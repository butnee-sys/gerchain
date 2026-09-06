"""
GerChain V79.5
Canonical Chain Tip
Authorized Independent Multi-Witness Verification Engine.

Purpose:
- Сериалчилсан гэрчийн багцыг бие даан баталгаажуулах.
- Урьдчилан зөвшөөрөгдсөн гэрчийн бүрэлдэхүүнийг тогтоох.
- Танихгүй гэрчийг зөвшилцлөөс хасах.
- Нэг гэрчийн давхар багцыг хоёр санал гэж тооцохгүй байх.
- Stored hash-д сохроор итгэхгүй.
- Бүх түүхийг эх өгөгдлөөс дахин тооцоолох.
- STATE_ROOT дээр зөвшилцөл байгуулах.
- V79.4:
  manifest_hash + STATE_ROOT-ээр Chain Tip-ийн бүрэлдэхүүнийг ялгах.
- V79.5:
  manifest_hash + final_sequence + final_state_hash +
  state_root-оос нэг стандарт CHAIN_TIP хэш үүсгэх.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from core.hashing import domain_hash
from verifier.independent_verifier import IndependentVerifier


@dataclass(frozen=True)
class IndependentConsensusResult:
    """Тусгаарлагдсан олон гэрчийн зөвшилцлийн үр дүн."""

    status: str
    consensus_hash: Optional[str]
    votes: int
    quorum: int
    valid_witness_ids: List[str]
    invalid_witness_ids: List[str]
    dissenting_witness_ids: List[str]


class IndependentMultiWitnessEngine:
    """
    Зөвшөөрөгдсөн гэрчийн бүрэлдэхүүн дээр ажиллах
    Canonical Chain Tip бүхий бие даасан зөвшилцлийн хөдөлгүүр.

    V79.5 Chain Tip:

        CHAIN_TIP = SHA256(
            manifest_hash +
            final_sequence +
            final_state_hash +
            state_root
        )

    Бүх бүрэлдэхүүн нь canonical object хэлбэрээр
    domain_hash() ашиглан нэг стандарт хэш болно.
    """

    def __init__(
        self,
        quorum: int,
        authorized_witness_ids: Set[str],
    ):
        if quorum < 2:
            raise ValueError(
                "Quorum must be at least 2."
            )

        if not authorized_witness_ids:
            raise ValueError(
                "At least one authorized witness is required."
            )

        authorized_ids = set(
            authorized_witness_ids
        )

        if len(authorized_ids) < quorum:
            raise ValueError(
                "Authorized witness count cannot be smaller than quorum."
            )

        for witness_id in authorized_ids:
            if not isinstance(witness_id, str):
                raise ValueError(
                    "Authorized witness IDs must be strings."
                )

            if not witness_id:
                raise ValueError(
                    "Authorized witness IDs cannot be empty."
                )

        self.quorum = quorum

        self.authorized_witness_ids = frozenset(
            authorized_ids
        )

        self.verifier = IndependentVerifier()

    def _decode_bundle(
        self,
        data: bytes,
    ) -> Optional[Dict]:
        """Сериалчилсан багцыг JSON объект болгон задлах."""

        try:
            bundle = json.loads(
                data.decode("utf-8")
            )
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
        ):
            return None

        if not isinstance(bundle, dict):
            return None

        return bundle

    def _extract_witness_id(
        self,
        data: bytes,
    ) -> Optional[str]:
        """Багцаас гэрчийн таних дугаарыг авах."""

        bundle = self._decode_bundle(data)

        if bundle is None:
            return None

        witness_id = bundle.get(
            "witness_id"
        )

        if not isinstance(
            witness_id,
            str,
        ):
            return None

        if not witness_id:
            return None

        return witness_id

    def _extract_manifest_hash(
        self,
        bundle: Dict,
    ) -> Optional[str]:
        """
        Bundle-ийн manifest_hash-ийг авах.

        IndependentVerifier нь эх manifest-ээс энэ хэшийг
        бие даан дахин тооцоолж баталгаажуулсан байна.
        """

        manifest_hash = bundle.get(
            "manifest_hash"
        )

        if not isinstance(
            manifest_hash,
            str,
        ):
            return None

        if not manifest_hash:
            return None

        return manifest_hash

    def _build_chain_tip_key(
        self,
        manifest_hash: str,
        state_root: str,
    ) -> Tuple[str, str]:
        """
        V79.4-ийн дотоод Chain Tip түлхүүр.

        V79.5-д зөвшилцлийн үндсэн таних нэгж нь
        compute_chain_tip()-ээр үүссэн нэг хэш байна.
        """

        return (
            manifest_hash,
            state_root,
        )

    def compute_chain_tip(
        self,
        bundle: Dict,
    ) -> Optional[str]:
        """
        Bundle-ийн бүх түүхийг бие даан дахин тооцоолж,
        canonical CHAIN_TIP хэш үүсгэнэ.

        Chain Tip нь дараах дөрвөн бүрэлдэхүүнийг хамарна:

            manifest_hash
            final_sequence
            final_state_hash
            state_root

        Stored final hash-д шууд итгэхгүй.
        Бүх утгыг _recompute_bundle() дахин тооцоолно.
        """

        if not isinstance(
            bundle,
            dict,
        ):
            return None

        recomputed = (
            self.verifier._recompute_bundle(
                bundle
            )
        )

        if recomputed is None:
            return None

        manifest_hash = (
            self._extract_manifest_hash(
                bundle
            )
        )

        if manifest_hash is None:
            return None

        final_sequence = recomputed[
            "final_sequence"
        ]

        final_state_hash = recomputed[
            "final_state_hash"
        ]

        state_root = recomputed[
            "state_root"
        ]

        return domain_hash(
            "CHAIN_TIP",
            {
                "manifest_hash": manifest_hash,
                "final_sequence": final_sequence,
                "final_state_hash": final_state_hash,
                "state_root": state_root,
            },
        )

    def evaluate(
        self,
        bundles: List[bytes],
    ) -> IndependentConsensusResult:
        """
        Сериалчилсан гэрчийн багцуудыг:

        1. зөвшөөрөгдсөн эсэх,
        2. давхардсан эсэх,
        3. криптографийн хувьд хүчинтэй эсэх,
        4. бүх түүхээс STATE_ROOT дахин тооцоолох,
        5. manifest_hash-ийг баталгаажуулах,
        6. canonical CHAIN_TIP дахин тооцоолох,
        7. CHAIN_TIP-ээр зөвшилцөл тогтоох

        дарааллаар шалгана.
        """

        if not bundles:
            raise ValueError(
                "At least one witness bundle is required."
            )

        valid_witness_ids: List[str] = []
        invalid_witness_ids: List[str] = []

        valid_bundles: List[Dict] = []

        seen_witness_ids = set()

        for data in bundles:

            witness_id = self._extract_witness_id(
                data
            )

            if witness_id is None:
                invalid_witness_ids.append(
                    "<unknown>"
                )
                continue

            # -----------------------------------------
            # Authorized witness check
            # -----------------------------------------

            if (
                witness_id
                not in self.authorized_witness_ids
            ):
                invalid_witness_ids.append(
                    witness_id
                )
                continue

            # -----------------------------------------
            # Duplicate witness check
            # -----------------------------------------

            if witness_id in seen_witness_ids:
                invalid_witness_ids.append(
                    witness_id
                )
                continue

            seen_witness_ids.add(
                witness_id
            )

            # -----------------------------------------
            # Independent cryptographic verification
            # -----------------------------------------

            if not self.verifier.verify_bytes(
                data
            ):
                invalid_witness_ids.append(
                    witness_id
                )
                continue

            bundle = self._decode_bundle(
                data
            )

            if bundle is None:
                invalid_witness_ids.append(
                    witness_id
                )
                continue

            # -----------------------------------------
            # Independent STATE_ROOT verification
            # -----------------------------------------

            state_root = (
                self.verifier.compute_state_root(
                    bundle
                )
            )

            if state_root is None:
                invalid_witness_ids.append(
                    witness_id
                )
                continue

            # -----------------------------------------
            # Independently validated manifest_hash
            # -----------------------------------------

            manifest_hash = (
                self._extract_manifest_hash(
                    bundle
                )
            )

            if manifest_hash is None:
                invalid_witness_ids.append(
                    witness_id
                )
                continue

            # -----------------------------------------
            # V79.5 CANONICAL CHAIN TIP
            # -----------------------------------------

            chain_tip = self.compute_chain_tip(
                bundle
            )

            if chain_tip is None:
                invalid_witness_ids.append(
                    witness_id
                )
                continue

            valid_witness_ids.append(
                witness_id
            )

            valid_bundles.append(
                {
                    "bundle": bundle,
                    "manifest_hash": manifest_hash,
                    "state_root": state_root,
                    "chain_tip": chain_tip,
                    "witness_id": witness_id,
                }
            )

        # ---------------------------------------------
        # V79.5:
        #
        # Consensus MUST be based on the single
        # canonical CHAIN_TIP hash.
        #
        # CHAIN_TIP contains:
        #
        # manifest_hash
        # final_sequence
        # final_state_hash
        # state_root
        # ---------------------------------------------

        chain_tip_votes: Dict[
            str,
            List[str],
        ] = {}

        for item in valid_bundles:

            chain_tip = item[
                "chain_tip"
            ]

            witness_id = item[
                "witness_id"
            ]

            if chain_tip not in chain_tip_votes:
                chain_tip_votes[
                    chain_tip
                ] = []

            chain_tip_votes[
                chain_tip
            ].append(
                witness_id
            )

        winning_chain_tip: Optional[str] = None

        winning_witness_ids: List[str] = []

        for (
            chain_tip,
            witness_ids,
        ) in chain_tip_votes.items():

            if len(witness_ids) > len(
                winning_witness_ids
            ):
                winning_chain_tip = (
                    chain_tip
                )

                winning_witness_ids = (
                    witness_ids
                )

        votes = len(
            winning_witness_ids
        )

        if votes >= self.quorum:
            status = "CONSENSUS"
        else:
            status = "REJECTED"

        dissenting_witness_ids = [
            witness_id
            for witness_id in valid_witness_ids
            if witness_id
            not in winning_witness_ids
        ]

        for witness_id in invalid_witness_ids:

            if witness_id not in (
                dissenting_witness_ids
            ):
                dissenting_witness_ids.append(
                    witness_id
                )

        consensus_hash: Optional[str] = None

        if (
            status == "CONSENSUS"
            and winning_chain_tip is not None
        ):
            consensus_hash = (
                winning_chain_tip
            )

        return IndependentConsensusResult(
            status=status,
            consensus_hash=consensus_hash,
            votes=votes,
            quorum=self.quorum,
            valid_witness_ids=(
                valid_witness_ids
            ),
            invalid_witness_ids=(
                invalid_witness_ids
            ),
            dissenting_witness_ids=(
                dissenting_witness_ids
            ),
        )


__all__ = [
    "IndependentConsensusResult",
    "IndependentMultiWitnessEngine",
]