"""
GerChain V81.2
TCP Transport Tests.

Purpose:
- Бодит TCP socket ашиглан bundle дамжуулах.
- Node A-аас Node B рүү bytes дамжуулах.
- Node B өөрийн Independent Verifier-ээр шалгах.
- Зөв bundle ACCEPT.
- Өөрчилсөн bundle REJECT.
- TCP transport-ийн үндсэн алдааны нөхцөлүүдийг шалгах.
"""

from __future__ import annotations

import json
import socket
import threading

from core.hashing import domain_hash
from network.node import WitnessNode
from network.transport import TCPServer, TCPTransport
from persistence.serializer import serialize_chain
from witness.chain import WitnessChain


def build_bundle():

    money_state = {
        "currency": "MNT",
        "balances": {
            "BUYER": 1000,
            "SELLER": 0,
        },
    }

    chain = WitnessChain(
        initial_state={
            "value": 0,
            "sequence_counter": 0,
            "initialized": False,
        },
        manifest={
            "system": "GerChain",
            "version": "V81.2",
            "purpose": "TCP Transport",
        },
        witness_id="NODE-A-V812",
        initial_money_state=money_state,
    )

    state_hash = domain_hash(
        "INITIAL_MONEY_STATE",
        money_state,
    )

    chain.append_event(
        event_id="V812-INITIAL-MONEY-001",
        event_type="INITIAL_MONEY_STATE",
        timestamp="2026-09-03T13:00:01",
        payload={
            "state": money_state,
            "state_hash": state_hash,
        },
        evidence={
            "type": "INITIAL_MONEY_COMMITMENT",
            "reference": "V812-001",
        },
    )

    return json.loads(
        serialize_chain(chain).decode("utf-8")
    )


def get_free_port():

    temp = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    )

    temp.bind(
        ("127.0.0.1", 0)
    )

    port = temp.getsockname()[1]

    temp.close()

    return port


def test_tcp_transport_round_trip():

    port = get_free_port()

    raw_server = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    )

    raw_server.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1,
    )

    raw_server.bind(
        ("127.0.0.1", port)
    )

    raw_server.listen(1)

    received = []

    def server_worker():

        connection, _address = (
            raw_server.accept()
        )

        with connection:

            data = connection.recv(
                65536
            )

            received.append(data)

            connection.sendall(
                b"V812-ACK"
            )

    thread = threading.Thread(
        target=server_worker,
        daemon=True,
    )

    thread.start()

    transport = TCPTransport(
        host="127.0.0.1",
        port=port,
    )

    payload = b"GERCHAIN-V812-TEST"

    response = transport.send(
        payload
    )

    thread.join(timeout=2)

    raw_server.close()

    assert received == [payload]

    assert response == b"V812-ACK"


def test_tcp_node_to_node_valid_bundle():

    bundle = build_bundle()

    serialized = json.dumps(
        bundle,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")

    port = get_free_port()

    raw_server = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    )

    raw_server.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1,
    )

    raw_server.bind(
        ("127.0.0.1", port)
    )

    raw_server.listen(1)

    node_b = WitnessNode(
        "NODE-B-V812"
    )

    result = []

    def node_b_server():

        connection, _address = (
            raw_server.accept()
        )

        with connection:

            data = connection.recv(
                65536
            )

            accepted = (
                node_b.receive_bytes(
                    data
                )
            )

            result.append(accepted)

            connection.sendall(
                b"ACCEPT"
                if accepted
                else b"REJECT"
            )

    thread = threading.Thread(
        target=node_b_server,
        daemon=True,
    )

    thread.start()

    transport = TCPTransport(
        host="127.0.0.1",
        port=port,
    )

    response = transport.send(
        serialized
    )

    thread.join(timeout=2)

    raw_server.close()

    assert result == [True]

    assert response == b"ACCEPT"

    assert (
        node_b.accepted_count()
        == 1
    )

    assert (
        node_b.rejected_count_total()
        == 0
    )


def test_tcp_node_to_node_tampered_bundle_rejected():

    bundle = build_bundle()

    bundle[
        "entries"
    ][0][
        "event_payload"
    ][
        "state"
    ][
        "balances"
    ][
        "BUYER"
    ] = 500

    serialized = json.dumps(
        bundle,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")

    port = get_free_port()

    raw_server = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    )

    raw_server.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1,
    )

    raw_server.bind(
        ("127.0.0.1", port)
    )

    raw_server.listen(1)

    node_b = WitnessNode(
        "NODE-B-V812-TAMPER"
    )

    result = []

    def node_b_server():

        connection, _address = (
            raw_server.accept()
        )

        with connection:

            data = connection.recv(
                65536
            )

            accepted = (
                node_b.receive_bytes(
                    data
                )
            )

            result.append(accepted)

            connection.sendall(
                b"ACCEPT"
                if accepted
                else b"REJECT"
            )

    thread = threading.Thread(
        target=node_b_server,
        daemon=True,
    )

    thread.start()

    transport = TCPTransport(
        host="127.0.0.1",
        port=port,
    )

    response = transport.send(
        serialized
    )

    thread.join(timeout=2)

    raw_server.close()

    assert result == [False]

    assert response == b"REJECT"

    assert (
        node_b.accepted_count()
        == 0
    )

    assert (
        node_b.rejected_count_total()
        == 1
    )


def test_tcp_transport_invalid_data_type():

    transport = TCPTransport(
        host="127.0.0.1",
        port=9999,
    )

    try:
        transport.send(
            "not-bytes"
        )
    except TypeError:
        return

    assert False, (
        "TCPTransport must reject "
        "non-bytes data."
    )


def test_tcp_server_requires_start():

    server = TCPServer(
        host="127.0.0.1",
        port=get_free_port(),
    )

    try:
        server.accept_once()
    except RuntimeError:
        return

    assert False, (
        "accept_once() must require "
        "a running server."
    )


def test_tcp_server_double_start_rejected():

    server = TCPServer(
        host="127.0.0.1",
        port=get_free_port(),
    )

    server.start()

    try:
        server.start()
    except RuntimeError:
        server.close()
        return

    server.close()

    assert False, (
        "Starting an already running "
        "server must fail."
    )