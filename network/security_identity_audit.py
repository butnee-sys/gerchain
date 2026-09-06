from __future__ import annotations

from typing import Any, Dict, Mapping, Set


class SecurityIdentityAudit:
    """
    GerChain V87.1 — Witness Identity Security Audit.

    Зорилго:
    - Зөвшөөрөгдсөн гэрчийг зөв таних.
    - Зөвшөөрөлгүй гэрчийг татгалзуулах.
    - Хуурамч гэрчийн таних тэмдгийг зөвшөөрөхгүй байх.
    - Давхар / зөрчилтэй гэрчийн таних тэмдгийг илрүүлэх.
    - Аудитын шийдвэрийг PASS / REJECTED / INCONCLUSIVE
      гэсэн гурван төлөвөөр гаргах.

    Үндсэн зарчим:

        AUTHORIZED + VALID ID  -> PASS
        UNAUTHORIZED           -> REJECTED
        UNKNOWN EVIDENCE       -> INCONCLUSIVE

    Энэ модуль нь V87.1-ийн аудитын логик юм.
    Үйлдвэрлэлийн сүлжээний тусгаарлалт гэж үзэхгүй.
    """

    VERSION = "V87.1"

    PASS = "PASS"
    REJECTED = "REJECTED"
    INCONCLUSIVE = "INCONCLUSIVE"

    @staticmethod
    def normalize_witness_id(
        witness_id: Any,
    ) -> str:
        if not isinstance(witness_id, str):
            raise TypeError(
                "witness_id must be a string."
            )

        normalized = witness_id.strip()

        if not normalized:
            raise ValueError(
                "witness_id cannot be empty."
            )

        return normalized

    @classmethod
    def verify_authorized_identity(
        cls,
        witness_id: Any,
        authorized_witnesses: Set[str],
    ) -> Dict[str, Any]:
        normalized_id = cls.normalize_witness_id(
            witness_id
        )

        if not isinstance(
            authorized_witnesses,
            (set, frozenset),
        ):
            raise TypeError(
                "authorized_witnesses must be a set."
            )

        normalized_authorized = {
            cls.normalize_witness_id(item)
            for item in authorized_witnesses
        }

        authorized = (
            normalized_id in normalized_authorized
        )

        return {
            "version": cls.VERSION,
            "operation": "VERIFY_AUTHORIZED_IDENTITY",
            "witness_id": normalized_id,
            "authorized": authorized,
            "status": (
                cls.PASS
                if authorized
                else cls.REJECTED
            ),
        }

    @classmethod
    def audit_witness_record(
        cls,
        record: Mapping[str, Any],
        authorized_witnesses: Set[str],
    ) -> Dict[str, Any]:
        if not isinstance(record, Mapping):
            raise TypeError(
                "record must be a mapping."
            )

        if "witness_id" not in record:
            return {
                "version": cls.VERSION,
                "operation": "AUDIT_WITNESS_RECORD",
                "status": cls.INCONCLUSIVE,
                "reason": "witness_id_missing",
            }

        witness_id = record["witness_id"]

        identity_result = cls.verify_authorized_identity(
            witness_id,
            authorized_witnesses,
        )

        if identity_result["status"] != cls.PASS:
            return {
                "version": cls.VERSION,
                "operation": "AUDIT_WITNESS_RECORD",
                "witness_id": identity_result["witness_id"],
                "authorized": False,
                "status": cls.REJECTED,
                "reason": "unauthorized_witness",
            }

        return {
            "version": cls.VERSION,
            "operation": "AUDIT_WITNESS_RECORD",
            "witness_id": identity_result["witness_id"],
            "authorized": True,
            "status": cls.PASS,
        }

    @classmethod
    def detect_duplicate_identities(
        cls,
        witness_ids: list[str],
    ) -> Dict[str, Any]:
        if not isinstance(witness_ids, list):
            raise TypeError(
                "witness_ids must be a list."
            )

        normalized = [
            cls.normalize_witness_id(item)
            for item in witness_ids
        ]

        seen = set()
        duplicates = set()

        for witness_id in normalized:
            if witness_id in seen:
                duplicates.add(witness_id)
            else:
                seen.add(witness_id)

        return {
            "version": cls.VERSION,
            "operation": "DUPLICATE_IDENTITY_CHECK",
            "total": len(normalized),
            "unique": len(seen),
            "duplicates": sorted(duplicates),
            "status": (
                cls.REJECTED
                if duplicates
                else cls.PASS
            ),
        }

    @classmethod
    def audit_network(
        cls,
        records: list[Mapping[str, Any]],
        authorized_witnesses: Set[str],
    ) -> Dict[str, Any]:
        if not isinstance(records, list):
            raise TypeError(
                "records must be a list."
            )

        audited = [
            cls.audit_witness_record(
                record,
                authorized_witnesses,
            )
            for record in records
        ]

        duplicate_result = cls.detect_duplicate_identities(
            [
                record["witness_id"]
                for record in records
                if "witness_id" in record
                and isinstance(record["witness_id"], str)
            ]
        )

        rejected_count = sum(
            1
            for result in audited
            if result["status"] == cls.REJECTED
        )

        inconclusive_count = sum(
            1
            for result in audited
            if result["status"] == cls.INCONCLUSIVE
        )

        if (
            rejected_count > 0
            or duplicate_result["status"] == cls.REJECTED
        ):
            overall_status = cls.REJECTED
        elif inconclusive_count > 0:
            overall_status = cls.INCONCLUSIVE
        else:
            overall_status = cls.PASS

        return {
            "version": cls.VERSION,
            "operation": "NETWORK_IDENTITY_AUDIT",
            "total_records": len(records),
            "rejected": rejected_count,
            "inconclusive": inconclusive_count,
            "duplicate_identity_check": duplicate_result,
            "records": audited,
            "status": overall_status,
        }


__all__ = [
    "SecurityIdentityAudit",
]