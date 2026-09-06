import json
from typing import Any

from core.canonical import canonicalize
from witness.chain import WitnessChain


def serialize_chain(chain: WitnessChain) -> bytes:
    """WitnessChain-ийг canonical байт хэлбэрт сериализрах."""

    bundle = {
        "manifest": chain.manifest,
        "manifest_hash": chain.manifest_hash,
        "witness_id": chain.witness_id,
        "initial_state": chain.initial_state,
        "entries": [
            {
                "record": {
                    "sequence": entry.record.sequence,
                    "event_id": entry.record.event_id,
                    "event_type": entry.record.event_type,
                    "timestamp": entry.record.timestamp,
                    "previous_state_hash": entry.record.previous_state_hash,
                    "event_hash": entry.record.event_hash,
                    "new_state_hash": entry.record.new_state_hash,
                    "evidence_hash": entry.record.evidence_hash,
                    "witness_id": entry.record.witness_id,
                    "manifest_hash": entry.record.manifest_hash,
                },
                "event_payload": entry.event_payload,
                "evidence": entry.evidence,
            }
            for entry in chain.entries
        ],
    }

    normalized = canonicalize(bundle)

    return __import__("json").dumps(
        normalized,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")