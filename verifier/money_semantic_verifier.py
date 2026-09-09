"""
GerChain V80.4.3
Independent Money Semantic Verifier.

Purpose:
- Мөнгөний шилжилтийн утгын бүрэн бүтэн байдлыг шалгах.
- source болон destination дансны үлдэгдлийг
  дахин тооцоолох.
- amount, currency, өмнөх/дараах үлдэгдлийн
  арифметик уялдааг шалгах.
- MONEY_TRANSFER болон ATOMIC_SETTLEMENT
  хоёрын мөнгөний утгыг бие даан шалгах.
- Дараалсан мөнгөн үйл явдлуудын
  үлдэгдлийн залгамж чанарыг шалгах.
- Нийт мөнгөний эхний болон эцсийн
  үлдэгдлийн хадгалалтын инвариантыг шалгах.
- INITIAL_MONEY_STATE-ийн commitment-ийг
  бие даан дахин тооцож шалгах.
- Хэш зөв байсан ч мөнгөний утга буруу бол
  REJECT хийх.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from core.hashing import domain_hash


class MoneySemanticVerifier:

    VERSION = "V80.3.1"

    MONEY_TRANSFER_TYPE = "MONEY_TRANSFER"
    ATOMIC_SETTLEMENT_TYPE = "ATOMIC_SETTLEMENT"
    INITIAL_MONEY_STATE_TYPE = "INITIAL_MONEY_STATE"

    def verify(
        self,
        bundle: Dict[str, Any],
    ) -> bool:
        """
        Bundle-ийн мөнгөний semantic integrity-г
        бие даан шалгана.

        Шалгалтын дараалал:

        1. INITIAL_MONEY_STATE commitment
        2. Нэг мөнгөн үйл явдлын арифметик
        3. Үлдэгдлийн залгамж чанар
        4. Нийт мөнгөний хадгалалтын инвариант
        """

        if not isinstance(bundle, dict):
            return False

        entries = bundle.get("entries")

        if not isinstance(entries, list):
            return False

        money_entries: List[Dict[str, Any]] = []
        initial_money_entries: List[Dict[str, Any]] = []

        for entry in entries:

            if not isinstance(entry, dict):
                return False

            record = entry.get("record")

            if not isinstance(record, dict):
                return False

            event_type = record.get("event_type")

            if event_type == self.INITIAL_MONEY_STATE_TYPE:

                initial_money_entries.append(entry)

            elif event_type in {
                self.MONEY_TRANSFER_TYPE,
                self.ATOMIC_SETTLEMENT_TYPE,
            }:

                money_entries.append(entry)

        # -------------------------------------------------
        # V80.4.3
        # INITIAL_MONEY_STATE semantic verification
        # -------------------------------------------------

        for entry in initial_money_entries:

            if not self._verify_initial_money_state(
                entry
            ):
                return False

        # -------------------------------------------------
        # Money movement semantic verification
        # -------------------------------------------------

        for entry in money_entries:

            event_type = entry[
                "record"
            ].get(
                "event_type"
            )

            if event_type == self.MONEY_TRANSFER_TYPE:

                if not self._verify_money_transfer(
                    entry
                ):
                    return False

            elif event_type == self.ATOMIC_SETTLEMENT_TYPE:

                if not self._verify_atomic_settlement(
                    entry
                ):
                    return False

        # -------------------------------------------------
        # Balance continuity
        # -------------------------------------------------

        if not self._verify_balance_continuity(
            money_entries
        ):
            return False

        # -------------------------------------------------
        # Money conservation
        # -------------------------------------------------

        if not self._verify_money_conservation(
            initial_money_entries,
            money_entries,
        ):
            return False

        return True

    # =====================================================
    # V80.4.3
    # INITIAL MONEY STATE
    # =====================================================

    def _verify_initial_money_state(
        self,
        entry: Dict[str, Any],
    ) -> bool:
        """
        INITIAL_MONEY_STATE-ийн commitment-ийг
        бие даан дахин тооцож шалгана.

        Шалгалт:

        state байгаа эсэх
        ↓
        currency зөв эсэх
        ↓
        balances зөв бүтэцтэй эсэх
        ↓
        бүх үлдэгдэл integer/non-negative эсэх
        ↓
        INITIAL_MONEY_STATE hash дахин тооцох
        ↓
        stored hash-тэй таарч байгаа эсэх
        """

        record = entry.get("record")

        if not isinstance(record, dict):
            return False

        if record.get(
            "event_type"
        ) != self.INITIAL_MONEY_STATE_TYPE:
            return False

        payload = entry.get(
            "event_payload"
        )

        if not isinstance(payload, dict):
            return False

        state = payload.get(
            "state"
        )

        stored_hash = payload.get(
            "state_hash"
        )

        if not isinstance(state, dict):
            return False

        if not isinstance(
            stored_hash,
            str,
        ):
            return False

        currency = state.get(
            "currency"
        )

        balances = state.get(
            "balances"
        )

        if not isinstance(
            currency,
            str,
        ):
            return False

        if not currency:
            return False

        if not isinstance(
            balances,
            dict,
        ):
            return False

        for account_id, balance in balances.items():

            if not isinstance(
                account_id,
                str,
            ):
                return False

            if not account_id:
                return False

            # bool нь int-ийн дэд төрөл тул
            # тусад нь хориглоно.
            if not isinstance(
                balance,
                int,
            ):
                return False

            if isinstance(
                balance,
                bool,
            ):
                return False

            if balance < 0:
                return False

        recalculated_hash = domain_hash(
            "INITIAL_MONEY_STATE",
            state,
        )

        return (
            recalculated_hash
            == stored_hash
        )

    # =====================================================
    # MONEY TRANSFER
    # =====================================================

    def _verify_money_transfer(
        self,
        entry: Dict[str, Any],
    ) -> bool:
        """
        MONEY_TRANSFER-ийн арифметик утгыг шалгана.
        """

        fields = self._extract_money_fields(
            entry
        )

        if fields is None:
            return False

        (
            source,
            destination,
            amount,
            currency,
            previous_source_balance,
            new_source_balance,
            previous_destination_balance,
            new_destination_balance,
        ) = fields

        if amount <= 0:
            return False

        if (
            new_source_balance
            != previous_source_balance - amount
        ):
            return False

        if (
            new_destination_balance
            != previous_destination_balance + amount
        ):
            return False

        if (
            previous_source_balance < 0
            or previous_destination_balance < 0
            or new_source_balance < 0
            or new_destination_balance < 0
        ):
            return False

        if source == destination:
            return False

        return True

    # =====================================================
    # ATOMIC SETTLEMENT
    # =====================================================

    def _verify_atomic_settlement(
        self,
        entry: Dict[str, Any],
    ) -> bool:
        """
        ATOMIC_SETTLEMENT-ийн мөнгөний
        арифметик уялдааг шалгана.
        """

        fields = self._extract_money_fields(
            entry
        )

        if fields is None:
            return False

        (
            source,
            destination,
            amount,
            currency,
            previous_source_balance,
            new_source_balance,
            previous_destination_balance,
            new_destination_balance,
        ) = fields

        if amount <= 0:
            return False

        if (
            new_source_balance
            != previous_source_balance - amount
        ):
            return False

        if (
            new_destination_balance
            != previous_destination_balance + amount
        ):
            return False

        if (
            previous_source_balance < 0
            or previous_destination_balance < 0
            or new_source_balance < 0
            or new_destination_balance < 0
        ):
            return False

        if source == destination:
            return False

        record = entry.get(
            "record"
        )

        if not isinstance(
            record,
            dict,
        ):
            return False

        payload = entry.get(
            "event_payload"
        )

        if not isinstance(
            payload,
            dict,
        ):
            return False

        previous_escrow_state = payload.get(
            "previous_escrow_state"
        )

        new_escrow_state = payload.get(
            "new_escrow_state"
        )

        if previous_escrow_state != "LOCKED":
            return False

        if new_escrow_state not in {
            "RELEASED",
            "REFUNDED",
        }:
            return False

        escrow_id = payload.get(
            "escrow_id"
        )

        if not isinstance(
            escrow_id,
            str,
        ):
            return False

        if not escrow_id:
            return False

        return True

    # =====================================================
    # FIELD EXTRACTION
    # =====================================================

    def _extract_money_fields(
        self,
        entry: Dict[str, Any],
    ) -> (
        Tuple[
            str,
            str,
            int,
            str,
            int,
            int,
            int,
            int,
        ]
        | None
    ):
        """
        Мөнгөний үйл явдлын нийтлэг талбаруудыг
        нэг хэлбэрээр гаргаж авна.
        """

        payload = entry.get(
            "event_payload"
        )

        if not isinstance(
            payload,
            dict,
        ):
            return None

        source = payload.get(
            "source"
        )

        destination = payload.get(
            "destination"
        )

        amount = payload.get(
            "amount"
        )

        currency = payload.get(
            "currency"
        )

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

        if not isinstance(
            source,
            str,
        ):
            return None

        if not source:
            return None

        if not isinstance(
            destination,
            str,
        ):
            return None

        if not destination:
            return None

        if not isinstance(
            amount,
            int,
        ):
            return None

        if isinstance(
            amount,
            bool,
        ):
            return None

        if not isinstance(
            currency,
            str,
        ):
            return None

        if not currency:
            return None

        balances = [
            previous_source_balance,
            new_source_balance,
            previous_destination_balance,
            new_destination_balance,
        ]

        for balance in balances:

            if not isinstance(
                balance,
                int,
            ):
                return None

            if isinstance(
                balance,
                bool,
            ):
                return None

        return (
            source,
            destination,
            amount,
            currency,
            previous_source_balance,
            new_source_balance,
            previous_destination_balance,
            new_destination_balance,
        )

    # =====================================================
    # BALANCE CONTINUITY
    # =====================================================

    def _verify_balance_continuity(
        self,
        money_entries: List[Dict[str, Any]],
    ) -> bool:
        """
        Нэг дансны дараагийн үйл явдлын өмнөх үлдэгдэл
        өмнөх үйл явдлын дараах үлдэгдэлтэй таарч
        байгаа эсэхийг шалгана.
        """

        last_balances: Dict[
            Tuple[str, str],
            int,
        ] = {}

        for entry in money_entries:

            fields = self._extract_money_fields(
                entry
            )

            if fields is None:
                return False

            (
                source,
                destination,
                amount,
                currency,
                previous_source_balance,
                new_source_balance,
                previous_destination_balance,
                new_destination_balance,
            ) = fields

            source_key = (
                source,
                currency,
            )

            destination_key = (
                destination,
                currency,
            )

            if source_key in last_balances:

                if (
                    previous_source_balance
                    != last_balances[source_key]
                ):
                    return False

            if destination_key in last_balances:

                if (
                    previous_destination_balance
                    != last_balances[destination_key]
                ):
                    return False

            last_balances[
                source_key
            ] = new_source_balance

            last_balances[
                destination_key
            ] = new_destination_balance

        return True

    # =====================================================
    # MONEY CONSERVATION
    # =====================================================

    def _verify_money_conservation(
        self,
        initial_money_entries: List[Dict[str, Any]],
        money_entries: List[Dict[str, Any]],
    ) -> bool:
        """
        Мөнгөний нийт хадгалалтын инвариантыг шалгана.

        Дүрэм:

            INITIAL_MONEY_STATE
                    ↓
            бүх money event
                    ↓
            эцсийн дансны үлдэгдэл

        Эхний бүх дансны нийт мөнгө
        эцсийн бүх дансны нийт мөнгөтэй
        тэнцүү байх ёстой.

        Зөвхөн тухайн гүйлгээний source/destination
        хоёр дансыг хооронд нь харьцуулахгүй.
        """

        if not money_entries:
            return True

        # -------------------------------------------------
        # 1. INITIAL_MONEY_STATE-оос authoritative
        #    эхний дансны төлөвийг авна.
        # -------------------------------------------------

        if not initial_money_entries:
            return False

        if len(initial_money_entries) != 1:
            return False

        initial_entry = initial_money_entries[0]

        payload = initial_entry.get(
            "event_payload"
        )

        if not isinstance(
            payload,
            dict,
        ):
            return False

        initial_state = payload.get(
            "state"
        )

        if not isinstance(
            initial_state,
            dict,
        ):
            return False

        currency = initial_state.get(
            "currency"
        )

        initial_balances = initial_state.get(
            "balances"
        )

        if not isinstance(
            currency,
            str,
        ):
            return False

        if not currency:
            return False

        if not isinstance(
            initial_balances,
            dict,
        ):
            return False

        # -------------------------------------------------
        # 2. Эхний нийт мөнгө
        # -------------------------------------------------

        initial_total = 0

        for account_id, balance in initial_balances.items():

            if not isinstance(
                account_id,
                str,
            ):
                return False

            if not account_id:
                return False

            if not isinstance(
                balance,
                int,
            ):
                return False

            if isinstance(
                balance,
                bool,
            ):
                return False

            if balance < 0:
                return False

            initial_total += balance

        # -------------------------------------------------
        # 3. Эцсийн дансны төлөвийг эхний төлөвөөс
        #    сэргээнэ.
        # -------------------------------------------------

        final_balances = dict(
            initial_balances
        )

        for entry in money_entries:

            fields = self._extract_money_fields(
                entry
            )

            if fields is None:
                return False

            (
                source,
                destination,
                amount,
                event_currency,
                previous_source_balance,
                new_source_balance,
                previous_destination_balance,
                new_destination_balance,
            ) = fields

            if event_currency != currency:
                return False

            # Event-ийн previous balance нь
            # бидний сэргээсэн төлөвтэй яг таарах ёстой.

            if source not in final_balances:
                return False

            if destination not in final_balances:
                return False

            if (
                final_balances[source]
                != previous_source_balance
            ):
                return False

            if (
                final_balances[destination]
                != previous_destination_balance
            ):
                return False

            final_balances[source] = (
                new_source_balance
            )

            final_balances[destination] = (
                new_destination_balance
            )

        # -------------------------------------------------
        # 4. Эцсийн нийт мөнгө
        # -------------------------------------------------

        final_total = sum(
            final_balances.values()
        )

        # -------------------------------------------------
        # 5. Conservation invariant
        # -------------------------------------------------

        return (
            final_total
            == initial_total
        )



__all__ = [
    "MoneySemanticVerifier",
]