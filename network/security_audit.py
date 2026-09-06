from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Mapping


class SecurityAudit:
    """
    GerChain V87.0 — Security Audit Foundation.

    Зорилго:
    - Аюулгүй байдлын аудитын нэгдсэн суурь үүсгэх.
    - Зөрчлийг тодорхой ангиллаар бүртгэх.
    - Өгөгдлийн өөрчлөлтийг дахин тооцож шалгах.
    - Аюулгүй бус нөхцөлд PASS өгөхгүй байх.
    - PASS / REJECTED / INCONCLUSIVE төлөвийг ялгах.

    Үндсэн зарчим:
        VALID        -> PASS
        VIOLATION    -> REJECTED
        UNKNOWN      -> INCONCLUSIVE

    Энэ модуль нь үйлдвэрлэлийн түвшний халдлагын хамгаалалт
    гэж үзэхгүй. Энэ нь V87.x бодит аюулгүй байдлын тестүүдийн
    аудитын суурь юм.
    """

    VERSION = "V87.0"

    VALID_STATUS = "VALID"
    VIOLATION_STATUS = "VIOLATION"
    UNKNOWN_STATUS = "UNKNOWN"

    PASS = "PASS"
    REJECTED = "REJECTED"
    INCONCLUSIVE = "INCONCLUSIVE"

    SECURITY_CATEGORIES = (
        "IDENTITY",
        "AUTHORIZATION",
        "SIGNATURE",
        "REPLAY",
        "STATE_TAMPERING",
        "CHAIN_TIP",
        "ANCHOR",
        "QUORUM",
        "NETWORK",
    )

    @staticmethod
    def canonical_json(data: Mapping[str, Any]) -> str:
        if not isinstance(data, Mapping):
            raise TypeError("data must be a mapping.")

        return json.dumps(
            dict(data),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

    @classmethod
    def state_hash(
        cls,
        state: Mapping[str, Any],
    ) -> str:
        canonical = cls.canonical_json(state)

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

    @classmethod
    def verify_state_integrity(
        cls,
        state: Mapping[str, Any],
        expected_hash: str,
    ) -> Dict[str, Any]:
        if not isinstance(state, Mapping):
            raise TypeError("state must be a mapping.")

        if not isinstance(expected_hash, str):
            raise TypeError(
                "expected_hash must be a string."
            )

        actual_hash = cls.state_hash(state)

        matches = actual_hash == expected_hash

        return {
            "version": cls.VERSION,
            "operation": "STATE_INTEGRITY",
            "expected_hash": expected_hash,
            "actual_hash": actual_hash,
            "matches": matches,
            "status": (
                cls.PASS
                if matches
                else cls.REJECTED
            ),
        }

    @classmethod
    def audit_event(
        cls,
        category: str,
        status: str,
        evidence: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        if not isinstance(category, str):
            raise TypeError(
                "category must be a string."
            )

        if category not in cls.SECURITY_CATEGORIES:
            raise ValueError(
                f"Unknown security category: {category}"
            )

        if status not in (
            cls.VALID_STATUS,
            cls.VIOLATION_STATUS,
            cls.UNKNOWN_STATUS,
        ):
            raise ValueError(
                f"Unknown audit status: {status}"
            )

        if evidence is not None:
            if not isinstance(evidence, Mapping):
                raise TypeError(
                    "evidence must be a mapping."
                )
            evidence_data = dict(evidence)
        else:
            evidence_data = {}

        if status == cls.VALID_STATUS:
            decision = cls.PASS
        elif status == cls.VIOLATION_STATUS:
            decision = cls.REJECTED
        else:
            decision = cls.INCONCLUSIVE

        return {
            "version": cls.VERSION,
            "category": category,
            "input_status": status,
            "decision": decision,
            "evidence": evidence_data,
        }

    @classmethod
    def summarize(
        cls,
        events: list[Mapping[str, Any]],
    ) -> Dict[str, Any]:
        if not isinstance(events, list):
            raise TypeError(
                "events must be a list."
            )

        normalized = []

        for event in events:
            if not isinstance(event, Mapping):
                raise TypeError(
                    "each event must be a mapping."
                )

            decision = event.get("decision")

            if decision not in (
                cls.PASS,
                cls.REJECTED,
                cls.INCONCLUSIVE,
            ):
                raise ValueError(
                    "invalid event decision."
                )

            normalized.append(dict(event))

        rejected_count = sum(
            1
            for event in normalized
            if event["decision"] == cls.REJECTED
        )

        inconclusive_count = sum(
            1
            for event in normalized
            if event["decision"] == cls.INCONCLUSIVE
        )

        passed_count = sum(
            1
            for event in normalized
            if event["decision"] == cls.PASS
        )

        if rejected_count > 0:
            overall_status = cls.REJECTED
        elif inconclusive_count > 0:
            overall_status = cls.INCONCLUSIVE
        else:
            overall_status = cls.PASS

        return {
            "version": cls.VERSION,
            "operation": "SECURITY_AUDIT_SUMMARY",
            "total_events": len(normalized),
            "passed": passed_count,
            "rejected": rejected_count,
            "inconclusive": inconclusive_count,
            "status": overall_status,
            "events": normalized,
        }


__all__ = [
    "SecurityAudit",
]