"""SHUUD domain separation helpers.

SHUUD events are application-domain records. They share GerChain's existing
WitnessChain, but their semantic domain is explicit in every payload. This
prevents an application event from being confused with an escrow transition.
"""

from typing import Any, Mapping

from .hashing import domain_hash

SHUUD_DOMAIN = "SHUUD"


def canonical_shuud_payload(
    event_type: str,
    incident_id: str,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    if not event_type or not event_type.strip():
        raise ValueError("event_type is required")
    if not incident_id or not incident_id.strip():
        raise ValueError("incident_id is required")
    return {
        "domain": SHUUD_DOMAIN,
        "event_type": event_type.strip(),
        "incident_id": incident_id.strip(),
        "payload": dict(payload),
    }


def shuud_event_hash(
    event_type: str,
    incident_id: str,
    payload: Mapping[str, Any],
) -> str:
    return domain_hash(
        "SHUUD_EVENT",
        canonical_shuud_payload(event_type, incident_id, payload),
    )


def is_shuud_payload(payload: Mapping[str, Any]) -> bool:
    return payload.get("domain") == SHUUD_DOMAIN
