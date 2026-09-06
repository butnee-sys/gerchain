from __future__ import annotations

from typing import Any, Dict, Mapping


class SecuritySignatureAudit:
    """
    GerChain V87.2 — Witness Signature Security Audit.

    Зорилго:
    - Хүчинтэй гарын үсгийг PASS болгох.
    - Өгөгдөл өөрчлөгдсөн бол REJECTED болгох.
    - Буруу нийтийн түлхүүрээр шалгавал REJECTED болгох.
    - Буруу гарын үсгийг REJECTED болгох.
    - Гарчиг / агуулга / түлхүүрийн холбоос дутуу бол
      INCONCLUSIVE болгох.
    - Өмнөх V84.x хамгаалалтыг сулруулахгүй байх.

    Үндсэн зарчим:

        VALID SIGNATURE       -> PASS
        INVALID SIGNATURE     -> REJECTED
        MISSING EVIDENCE      -> INCONCLUSIVE

    Энэ модуль нь аудитын суурь бөгөөд үйлдвэрлэлийн
    түлхүүр хадгалалтын систем өөрөө биш.
    """

    VERSION = "V87.2"

    PASS = "PASS"
    REJECTED = "REJECTED"
    INCONCLUSIVE = "INCONCLUSIVE"

    @staticmethod
    def _require_bytes(
        value: Any,
        field_name: str,
    ) -> bytes:
        if not isinstance(value, bytes):
            raise TypeError(
                f"{field_name} must be bytes."
            )

        return value

    @classmethod
    def verify_signature(
        cls,
        message: Any,
        signature: Any,
        public_key: Any,
    ) -> Dict[str, Any]:
        if not isinstance(message, bytes):
            raise TypeError(
                "message must be bytes."
            )

        if not isinstance(signature, bytes):
            raise TypeError(
                "signature must be bytes."
            )

        if not isinstance(public_key, bytes):
            raise TypeError(
                "public_key must be bytes."
            )

        try:
            from cryptography.exceptions import (
                InvalidSignature,
            )
            from cryptography.hazmat.primitives.asymmetric import (
                ed25519,
            )

            key = ed25519.Ed25519PublicKey.from_public_bytes(
                public_key
            )

            key.verify(
                signature,
                message,
            )

            valid = True

        except InvalidSignature:
            valid = False

        except (ValueError, TypeError):
            valid = False

        except ImportError:
            return {
                "version": cls.VERSION,
                "operation": "VERIFY_SIGNATURE",
                "status": cls.INCONCLUSIVE,
                "reason": "ed25519_unavailable",
            }

        return {
            "version": cls.VERSION,
            "operation": "VERIFY_SIGNATURE",
            "valid": valid,
            "status": (
                cls.PASS
                if valid
                else cls.REJECTED
            ),
        }

    @classmethod
    def audit_record(
        cls,
        record: Mapping[str, Any],
    ) -> Dict[str, Any]:
        if not isinstance(record, Mapping):
            raise TypeError(
                "record must be a mapping."
            )

        required_fields = (
            "message",
            "signature",
            "public_key",
        )

        missing = [
            field
            for field in required_fields
            if field not in record
        ]

        if missing:
            return {
                "version": cls.VERSION,
                "operation": "AUDIT_SIGNATURE_RECORD",
                "status": cls.INCONCLUSIVE,
                "reason": "missing_evidence",
                "missing_fields": missing,
            }

        result = cls.verify_signature(
            message=record["message"],
            signature=record["signature"],
            public_key=record["public_key"],
        )

        return {
            "version": cls.VERSION,
            "operation": "AUDIT_SIGNATURE_RECORD",
            "valid": result.get("valid", False),
            "status": result["status"],
        }

    @classmethod
    def audit_witness_binding(
        cls,
        record: Mapping[str, Any],
        expected_public_keys: Mapping[str, bytes],
    ) -> Dict[str, Any]:
        if not isinstance(record, Mapping):
            raise TypeError(
                "record must be a mapping."
            )

        if not isinstance(expected_public_keys, Mapping):
            raise TypeError(
                "expected_public_keys must be a mapping."
            )

        if "witness_id" not in record:
            return {
                "version": cls.VERSION,
                "operation": "AUDIT_WITNESS_BINDING",
                "status": cls.INCONCLUSIVE,
                "reason": "witness_id_missing",
            }

        witness_id = record["witness_id"]

        if not isinstance(witness_id, str):
            raise TypeError(
                "witness_id must be a string."
            )

        if witness_id not in expected_public_keys:
            return {
                "version": cls.VERSION,
                "operation": "AUDIT_WITNESS_BINDING",
                "witness_id": witness_id,
                "status": cls.REJECTED,
                "reason": "unknown_witness",
            }

        if "public_key" not in record:
            return {
                "version": cls.VERSION,
                "operation": "AUDIT_WITNESS_BINDING",
                "witness_id": witness_id,
                "status": cls.INCONCLUSIVE,
                "reason": "public_key_missing",
            }

        expected_key = expected_public_keys[witness_id]

        if record["public_key"] != expected_key:
            return {
                "version": cls.VERSION,
                "operation": "AUDIT_WITNESS_BINDING",
                "witness_id": witness_id,
                "status": cls.REJECTED,
                "reason": "public_key_binding_mismatch",
            }

        return {
            "version": cls.VERSION,
            "operation": "AUDIT_WITNESS_BINDING",
            "witness_id": witness_id,
            "status": cls.PASS,
        }

    @classmethod
    def audit(
        cls,
        record: Mapping[str, Any],
        expected_public_keys: Mapping[str, bytes] | None = None,
    ) -> Dict[str, Any]:
        if not isinstance(record, Mapping):
            raise TypeError(
                "record must be a mapping."
            )

        signature_result = cls.audit_record(
            record
        )

        if signature_result["status"] != cls.PASS:
            return {
                "version": cls.VERSION,
                "operation": "FULL_SIGNATURE_AUDIT",
                "signature": signature_result,
                "binding": None,
                "status": signature_result["status"],
            }

        binding_result = None

        if expected_public_keys is not None:
            binding_result = cls.audit_witness_binding(
                record,
                expected_public_keys,
            )

            if binding_result["status"] != cls.PASS:
                return {
                    "version": cls.VERSION,
                    "operation": "FULL_SIGNATURE_AUDIT",
                    "signature": signature_result,
                    "binding": binding_result,
                    "status": binding_result["status"],
                }

        return {
            "version": cls.VERSION,
            "operation": "FULL_SIGNATURE_AUDIT",
            "signature": signature_result,
            "binding": binding_result,
            "status": cls.PASS,
        }


__all__ = [
    "SecuritySignatureAudit",
]