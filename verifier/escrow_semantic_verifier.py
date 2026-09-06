"""
GerChain V80.2
Independent Escrow Semantic Verifier.

Purpose:
- Witness-ийн криптографийн бүтэн байдлаас тусад нь
  Escrow-ийн утгын дүрмийг шалгах.
- ATOMIC_SETTLEMENT болон ESCROW_TRANSITION
  хоорондын логик уялдааг шалгах.
- Хэшийг дахин зөв тооцоолсон байсан ч
  утгын хувьд буруу settlement-ийг REJECT хийх.
- Settlement-ийн өмнөх LOCKED transition-тэй
  escrow_id, amount, currency-г тулгаж шалгах.
- Settlement-ийн дараах RELEASED/REFUNDED transition-тэй
  логик уялдааг шалгах.
- V80.2:
  LOCKED -> ATOMIC_SETTLEMENT -> RELEASED/REFUNDED
  гэсэн яг дараалсан Witness sequence-г шаардах.
"""

from __future__ import annotations

from typing import Any, Dict, List


class EscrowSemanticVerifier:
    """
    Witness bundle доторх Escrow-тэй холбоотой
    үйл явдлуудын утгын бүрэн бүтэн байдлыг
    бие даан шалгагч.
    """

    VERSION = "V80.2"

    SETTLEMENT_TYPE = "ATOMIC_SETTLEMENT"
    TRANSITION_TYPE = "ESCROW_TRANSITION"

    VALID_SETTLEMENT_TARGETS = {
        "RELEASED",
        "REFUNDED",
    }

    VALID_TRANSITION_STATES = {
        "FUNDED",
        "LOCKED",
        "RELEASED",
        "REFUNDED",
        "CANCELLED",
    }

    def verify(
        self,
        bundle: Dict[str, Any],
    ) -> bool:
        """
        Bundle-ийн Escrow semantic integrity-г шалгана.

        Шалгалтын дараалал:

        1. Settlement-ийн дотоод утга
        2. Escrow transition-ийн дотоод утга
        3. Settlement -> дараах transition холбоо
        4. LOCKED -> settlement өмнөх холбоо
        5. V80.2 strict sequence adjacency
        """

        if not isinstance(bundle, dict):
            return False

        entries = bundle.get("entries")

        if not isinstance(entries, list):
            return False

        settlement_entries = []
        transition_entries = []

        for entry in entries:
            if not isinstance(entry, dict):
                return False

            record = entry.get("record")

            if not isinstance(record, dict):
                return False

            event_type = record.get("event_type")

            if event_type == self.SETTLEMENT_TYPE:
                settlement_entries.append(entry)

            elif event_type == self.TRANSITION_TYPE:
                transition_entries.append(entry)

        for settlement in settlement_entries:
            if not self._verify_settlement(
                settlement,
                entries,
            ):
                return False

        for transition in transition_entries:
            if not self._verify_transition(
                transition
            ):
                return False

        if settlement_entries:
            if not self._verify_settlement_transition_links(
                settlement_entries,
                transition_entries,
            ):
                return False

            if not self._verify_locked_settlement_links(
                settlement_entries,
                transition_entries,
            ):
                return False

        return True

    def _verify_settlement(
        self,
        entry: Dict[str, Any],
        entries: List[Dict[str, Any]],
    ) -> bool:
        record = entry["record"]
        payload = entry.get("event_payload")

        if not isinstance(payload, dict):
            return False

        required_fields = {
            "transaction_id",
            "sequence",
            "source",
            "destination",
            "amount",
            "currency",
            "escrow_id",
            "previous_escrow_state",
            "new_escrow_state",
            "previous_source_balance",
            "new_source_balance",
            "previous_destination_balance",
            "new_destination_balance",
        }

        if not required_fields.issubset(
            payload.keys()
        ):
            return False

        if record.get("event_type") != self.SETTLEMENT_TYPE:
            return False

        escrow_id = payload.get("escrow_id")

        if not isinstance(escrow_id, str):
            return False

        if not escrow_id:
            return False

        amount = payload.get("amount")

        if not isinstance(amount, int):
            return False

        if amount <= 0:
            return False

        currency = payload.get("currency")

        if not isinstance(currency, str):
            return False

        if not currency:
            return False

        previous_state = payload.get(
            "previous_escrow_state"
        )

        new_state = payload.get(
            "new_escrow_state"
        )

        if previous_state != "LOCKED":
            return False

        if new_state not in self.VALID_SETTLEMENT_TARGETS:
            return False

        source = payload.get("source")
        destination = payload.get("destination")

        if not isinstance(source, str):
            return False

        if not isinstance(destination, str):
            return False

        if not source or not destination:
            return False

        if source == destination:
            return False

        previous_source_balance = payload.get(
            "previous_source_balance"
        )

        new_source_balance = payload.get(
            "new_source_balance"
        )

        previous_destination_balance = payload.get(
            "previous_destination_balance"
        )

        new_destination_balance = payload.get(
            "new_destination_balance"
        )

        if not all(
            isinstance(value, int)
            for value in (
                previous_source_balance,
                new_source_balance,
                previous_destination_balance,
                new_destination_balance,
            )
        ):
            return False

        if (
            previous_source_balance - amount
            != new_source_balance
        ):
            return False

        if (
            previous_destination_balance + amount
            != new_destination_balance
        ):
            return False

        return True

    def _verify_transition(
        self,
        entry: Dict[str, Any],
    ) -> bool:
        record = entry["record"]
        payload = entry.get("event_payload")

        if not isinstance(payload, dict):
            return False

        required_fields = {
            "escrow_id",
            "sequence",
            "previous_state",
            "new_state",
            "amount",
            "currency",
        }

        if not required_fields.issubset(
            payload.keys()
        ):
            return False

        if record.get("event_type") != self.TRANSITION_TYPE:
            return False

        previous_state = payload.get(
            "previous_state"
        )

        new_state = payload.get(
            "new_state"
        )

        if previous_state not in {
            "CREATED",
            "FUNDED",
            "LOCKED",
        }:
            return False

        if new_state not in self.VALID_TRANSITION_STATES:
            return False

        amount = payload.get("amount")

        if not isinstance(amount, int):
            return False

        if amount <= 0:
            return False

        currency = payload.get("currency")

        if not isinstance(currency, str):
            return False

        if not currency:
            return False

        escrow_id = payload.get("escrow_id")

        if not isinstance(escrow_id, str):
            return False

        if not escrow_id:
            return False

        return True

    def _verify_locked_settlement_links(
        self,
        settlement_entries: List[Dict[str, Any]],
        transition_entries: List[Dict[str, Any]],
    ) -> bool:
        """
        V80.2:

        ATOMIC_SETTLEMENT-ийн яг өмнөх Witness sequence
        LOCKED transition байх ёстой.

        Нэмэлтээр:
        - escrow_id
        - amount
        - currency
        - previous_escrow_state
        - new_state

        бүгд нийцсэн байна.
        """

        for settlement in settlement_entries:
            settlement_payload = settlement[
                "event_payload"
            ]

            settlement_record = settlement["record"]
            settlement_sequence = settlement_record[
                "sequence"
            ]

            locked_transition = None

            for transition in transition_entries:
                transition_record = transition["record"]
                transition_payload = transition[
                    "event_payload"
                ]

                # V80.2:
                # LOCKED нь settlement-ийн яг өмнөх
                # Witness sequence байх ёстой.
                if (
                    transition_record["sequence"]
                    != settlement_sequence - 1
                ):
                    continue

                if (
                    transition_payload.get("new_state")
                    != "LOCKED"
                ):
                    continue

                locked_transition = transition
                break

            if locked_transition is None:
                return False

            locked_payload = locked_transition[
                "event_payload"
            ]

            # Exact sequence adjacency
            if (
                locked_transition["record"]["sequence"]
                != settlement_sequence - 1
            ):
                return False

            # Escrow identity
            if (
                locked_payload.get("escrow_id")
                != settlement_payload.get("escrow_id")
            ):
                return False

            # Escrow amount
            if (
                locked_payload.get("amount")
                != settlement_payload.get("amount")
            ):
                return False

            # Currency
            if (
                locked_payload.get("currency")
                != settlement_payload.get("currency")
            ):
                return False

            # Settlement must explicitly start from LOCKED
            if (
                settlement_payload.get(
                    "previous_escrow_state"
                )
                != "LOCKED"
            ):
                return False

            # Selected transition must produce LOCKED
            if (
                locked_payload.get("new_state")
                != "LOCKED"
            ):
                return False

        return True

    def _verify_settlement_transition_links(
        self,
        settlement_entries: List[Dict[str, Any]],
        transition_entries: List[Dict[str, Any]],
    ) -> bool:
        """
        V80.2:

        ATOMIC_SETTLEMENT-ийн яг дараагийн Witness sequence
        RELEASED эсвэл REFUNDED transition байх ёстой.

        Нэмэлтээр:
        - escrow_id
        - amount
        - currency
        - previous_state
        - target state

        бүгд нийцсэн байна.
        """

        for settlement in settlement_entries:
            settlement_payload = settlement[
                "event_payload"
            ]

            escrow_id = settlement_payload[
                "escrow_id"
            ]

            settlement_target = settlement_payload[
                "new_escrow_state"
            ]

            settlement_amount = settlement_payload[
                "amount"
            ]

            settlement_currency = settlement_payload[
                "currency"
            ]

            settlement_record = settlement["record"]
            settlement_sequence = settlement_record[
                "sequence"
            ]

            matching_transition = None

            for transition in transition_entries:
                transition_record = transition[
                    "record"
                ]

                transition_payload = transition[
                    "event_payload"
                ]

                # V80.2:
                # Зөвхөн settlement-ийн яг дараагийн
                # Witness sequence-г зөвшөөрнө.
                if (
                    transition_record["sequence"]
                    != settlement_sequence + 1
                ):
                    continue

                if (
                    transition_payload.get("escrow_id")
                    != escrow_id
                ):
                    continue

                matching_transition = transition
                break

            if matching_transition is None:
                return False

            transition_payload = (
                matching_transition["event_payload"]
            )

            # Exact sequence adjacency
            if (
                matching_transition["record"]["sequence"]
                != settlement_sequence + 1
            ):
                return False

            # Must transition from LOCKED
            if (
                transition_payload.get(
                    "previous_state"
                )
                != "LOCKED"
            ):
                return False

            # Must reach settlement target
            if (
                transition_payload.get("new_state")
                != settlement_target
            ):
                return False

            # Target must be terminal settlement state
            if (
                settlement_target
                not in self.VALID_SETTLEMENT_TARGETS
            ):
                return False

            # Amount must match
            if (
                transition_payload.get("amount")
                != settlement_amount
            ):
                return False

            # Currency must match
            if (
                transition_payload.get("currency")
                != settlement_currency
            ):
                return False

        return True


__all__ = [
    "EscrowSemanticVerifier",
]