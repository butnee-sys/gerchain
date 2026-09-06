import json
import copy
from typing import Any, Dict, List, Set, Optional

from core.hashing import domain_hash
from core.state import apply_transition


class IndependentVerifier:
    """Creator Engine-ээс хараат бус бие даасан баталгаажуулагч."""

    def verify_bytes(self, data_bytes: bytes) -> bool:
        try:
            bundle = json.loads(
                data_bytes.decode("utf-8")
            )
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
        ):
            return False

        return self.verify_bundle(bundle)

    def _recompute_bundle(
        self,
        bundle: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Bundle-ийн төлөвийн бүх шилжилтийг эхнээс нь
        бие даан дахин тооцоолно.

        Буцаах утга:
        - final_state
        - final_state_hash
        - state_root
        - final_sequence
        """

        required_keys = {
            "manifest",
            "manifest_hash",
            "witness_id",
            "initial_state",
            "entries",
        }

        if not required_keys.issubset(bundle.keys()):
            return None

        manifest = bundle["manifest"]
        expected_manifest_hash = bundle["manifest_hash"]
        witness_id = bundle["witness_id"]
        initial_state = copy.deepcopy(
            bundle["initial_state"]
        )
        entries = bundle["entries"]

        if not isinstance(entries, list):
            return None

        recomputed_manifest_hash = domain_hash(
            "MANIFEST",
            manifest,
        )

        if (
            recomputed_manifest_hash
            != expected_manifest_hash
        ):
            return None

        recomputed_state = copy.deepcopy(
            initial_state
        )

        prev_state_hash = domain_hash(
            "STATE",
            recomputed_state,
        )

        # State Root-ийн эхний үндэс.
        state_root = domain_hash(
            "STATE_ROOT",
            {
                "sequence": 0,
                "state_hash": prev_state_hash,
                "previous_root": None,
                "event_hash": None,
            },
        )

        seen_event_ids: Set[str] = set()
        seen_event_hashes: Set[str] = set()
        seen_state_transitions: Set[tuple] = set()

        prev_sequence = 0

        for index, entry in enumerate(entries):

            if not isinstance(entry, dict):
                return None

            if "record" not in entry:
                return None

            record = entry["record"]

            seq = record.get("sequence")

            if seq != index + 1:
                return None

            if seq <= prev_sequence:
                return None

            prev_sequence = seq

            if record.get("witness_id") != witness_id:
                return None

            if (
                record.get("manifest_hash")
                != expected_manifest_hash
            ):
                return None

            event_id = record.get("event_id")

            if event_id in seen_event_ids:
                return None

            seen_event_ids.add(event_id)

            if "event_payload" not in entry:
                return None

            event_obj = {
                "sequence": seq,
                "event_id": event_id,
                "event_type": record.get(
                    "event_type"
                ),
                "timestamp": record.get(
                    "timestamp"
                ),
                "payload": entry["event_payload"],
            }

            recomputed_event_hash = domain_hash(
                "WITNESS_EVENT",
                event_obj,
            )

            if (
                recomputed_event_hash
                != record.get("event_hash")
            ):
                return None

            if (
                recomputed_event_hash
                in seen_event_hashes
            ):
                return None

            seen_event_hashes.add(
                recomputed_event_hash
            )

            if "evidence" not in entry:
                return None

            recomputed_evidence_hash = domain_hash(
                "EVIDENCE",
                entry["evidence"],
            )

            if (
                recomputed_evidence_hash
                != record.get("evidence_hash")
            ):
                return None

            if (
                record.get("previous_state_hash")
                != prev_state_hash
            ):
                return None

            transition_key = (
                prev_state_hash,
                seq,
            )

            if (
                transition_key
                in seen_state_transitions
            ):
                return None

            seen_state_transitions.add(
                transition_key
            )

            try:
                recomputed_state = apply_transition(
                    recomputed_state,
                    event_obj,
                )
            except (
                ValueError,
                TypeError,
                KeyError,
            ):
                return None

            recomputed_state_hash = domain_hash(
                "STATE",
                recomputed_state,
            )

            if (
                recomputed_state_hash
                != record.get("new_state_hash")
            ):
                return None

            # -----------------------------------------
            # V79.3 STATE ROOT
            #
            # Root бүр дараагийн root-тойгоо
            # криптографийн хувьд холбогдоно.
            #
            # Иймээс өмнөх түүх өөрчлөгдвөл
            # эцсийн State Root заавал өөрчлөгдөнө.
            # -----------------------------------------

            state_root = domain_hash(
                "STATE_ROOT",
                {
                    "sequence": seq,
                    "previous_root": state_root,
                    "event_hash": recomputed_event_hash,
                    "state_hash": recomputed_state_hash,
                },
            )

            prev_state_hash = (
                recomputed_state_hash
            )

        return {
            "final_state": recomputed_state,
            "final_state_hash": prev_state_hash,
            "state_root": state_root,
            "final_sequence": prev_sequence,
        }

    def compute_state_root(
        self,
        bundle: Dict[str, Any],
    ) -> Optional[str]:
        """
        Bundle-ийн State Root-ийг бүх түүхийг дахин
        тооцоолж гаргана.

        Stored hash-д шууд итгэхгүй.
        """

        result = self._recompute_bundle(bundle)

        if result is None:
            return None

        return result["state_root"]

    def verify_bundle(
        self,
        bundle: Dict[str, Any],
    ) -> bool:
        """Bundle-ийн бүрэн криптографийн баталгаажуулалт."""

        result = self._recompute_bundle(bundle)

        return result is not None

    def verify_no_fork(
        self,
        bundles: List[Dict[str, Any]],
    ) -> bool:

        transitions: Dict[
            tuple,
            tuple,
        ] = {}

        for bundle in bundles:

            if "entries" not in bundle:
                return False

            if not isinstance(
                bundle["entries"],
                list,
            ):
                return False

            if not self.verify_bundle(
                bundle
            ):
                return False

            recomputed = (
                self._recompute_bundle(
                    bundle
                )
            )

            if recomputed is None:
                return False

            initial_state = bundle[
                "initial_state"
            ]

            prev_state_hash = domain_hash(
                "STATE",
                initial_state,
            )

            for entry in bundle["entries"]:

                record = entry["record"]

                seq = record["sequence"]

                event_hash = record[
                    "event_hash"
                ]

                # Хадгалсан new_state_hash-ийг
                # fork шалгалтад ашиглах боловч
                # өмнө нь _recompute_bundle()
                # түүнийг бие даан баталгаажуулсан.
                new_state_hash = record[
                    "new_state_hash"
                ]

                key = (
                    prev_state_hash,
                    seq,
                )

                current_transition = (
                    event_hash,
                    new_state_hash,
                )

                if key in transitions:

                    if (
                        transitions[key]
                        != current_transition
                    ):
                        return False

                else:
                    transitions[key] = (
                        current_transition
                    )

                prev_state_hash = (
                    new_state_hash
                )

        return True