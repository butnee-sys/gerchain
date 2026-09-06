"""
GerChain V81.2
TCP Network Transport.

Purpose:
- Witness Node хооронд бодит TCP холболт үүсгэх.
- Bundle-ийг JSON bytes хэлбэрээр дамжуулах.
- Хүлээн авагч талд бие даасан verification хийх боломж бүрдүүлэх.

V81.2:
- Бодит TCP transport.
- Consensus хараахан оруулаагүй.
- Authorization хараахан оруулаагүй.
- Cryptographic key protection хараахан оруулаагүй.
"""

from __future__ import annotations

import socket
from typing import Optional


class TCPTransport:
    """
    GerChain V81.2 TCP transport.

    Нэг transport:
        sender → TCP → receiver
    """

    VERSION = "V81.2"

    def __init__(
        self,
        host: str,
        port: int,
        timeout: float = 5.0,
    ):
        if not isinstance(host, str):
            raise TypeError(
                "host must be a string."
            )

        if not host:
            raise ValueError(
                "host cannot be empty."
            )

        if not isinstance(port, int):
            raise TypeError(
                "port must be an integer."
            )

        if port < 1 or port > 65535:
            raise ValueError(
                "port must be between 1 and 65535."
            )

        if timeout <= 0:
            raise ValueError(
                "timeout must be positive."
            )

        self.host = host
        self.port = port
        self.timeout = timeout

    def send(
        self,
        data: bytes,
    ) -> bytes:
        """
        TCP сервер рүү bytes илгээнэ.

        Серверээс буцаасан bytes-ийг
        response болгон буцаана.
        """

        if not isinstance(data, bytes):
            raise TypeError(
                "data must be bytes."
            )

        with socket.create_connection(
            (
                self.host,
                self.port,
            ),
            timeout=self.timeout,
        ) as sock:

            sock.sendall(data)

            chunks = []

            while True:
                chunk = sock.recv(4096)

                if not chunk:
                    break

                chunks.append(chunk)

            return b"".join(chunks)


class TCPServer:
    """
    GerChain V81.2 TCP серверийн
    хамгийн бага суурь бүтэц.

    Нэг client connection хүлээн авна.
    """

    VERSION = "V81.2"

    def __init__(
        self,
        host: str,
        port: int,
        timeout: float = 5.0,
    ):
        if not isinstance(host, str):
            raise TypeError(
                "host must be a string."
            )

        if not host:
            raise ValueError(
                "host cannot be empty."
            )

        if not isinstance(port, int):
            raise TypeError(
                "port must be an integer."
            )

        if port < 1 or port > 65535:
            raise ValueError(
                "port must be between 1 and 65535."
            )

        if timeout <= 0:
            raise ValueError(
                "timeout must be positive."
            )

        self.host = host
        self.port = port
        self.timeout = timeout

        self._server: Optional[
            socket.socket
        ] = None

    def start(self) -> None:
        """
        TCP серверийн socket үүсгэнэ.
        """

        if self._server is not None:
            raise RuntimeError(
                "Server is already running."
            )

        server = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
        )

        server.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1,
        )

        server.bind(
            (
                self.host,
                self.port,
            )
        )

        server.listen(5)

        self._server = server

    def accept_once(self) -> bytes:
        """
        Нэг client connection хүлээн авч,
        бүх bytes-ийг уншина.
        """

        if self._server is None:
            raise RuntimeError(
                "Server is not running."
            )

        connection, _address = (
            self._server.accept()
        )

        with connection:
            connection.settimeout(
                self.timeout
            )

            chunks = []

            while True:
                chunk = connection.recv(
                    4096
                )

                if not chunk:
                    break

                chunks.append(chunk)

            return b"".join(chunks)

    def close(self) -> None:
        """
        TCP серверийг хаана.
        """

        if self._server is not None:
            self._server.close()
            self._server = None


__all__ = [
    "TCPTransport",
    "TCPServer",
]