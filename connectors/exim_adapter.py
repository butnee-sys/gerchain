"""EXIM Port connector adapter.

This is the only connector-layer module that imports the EXIM Port package.
Application code and the open multi-connector gateway stay independent of
NEF–GerChain and of the concrete Port package layout.
"""

from typing import Any, Mapping

from nef_gerchain_port import ExternalPortExport, ExternalPortImport


class EXIMConnectorAdapter:
    """Translate connector operations to the versioned EXIM Port boundary."""

    connector_id = "EXIM"

    def __init__(self) -> None:
        self._port_import = ExternalPortImport()
        self._port_export = ExternalPortExport()

    def create_witness_chain(self, *, initial_state: dict[str, Any], manifest: dict[str, Any], witness_id: str, initial_money_state: dict[str, Any] | None = None) -> Any:
        return self._port_import.create_witness_chain(initial_state=initial_state, manifest=manifest, witness_id=witness_id, initial_money_state=initial_money_state)

    def release_escrow(self, escrow: Any, *, authorization_hash: str, incident_id: str, rule_version: str, timestamp: str, evidence: Any | None = None) -> Any:
        return self._port_import.release_escrow(escrow, authorization_hash=authorization_hash, incident_id=incident_id, rule_version=rule_version, timestamp=timestamp, evidence=evidence)

    def release_escrow_authorized(self, escrow: Any, **kwargs: Any) -> Any:
        return self._port_import.release_escrow_authorized(escrow, **kwargs)

    def export_status(self, *, status: str, reference_id: str | None = None, data: Mapping[str, Any] | None = None) -> Any:
        return self._port_export.status(status=status, reference_id=reference_id, data=dict(data or {}))

    def export_escrow_status(self, *, escrow: Any) -> Any:
        return self._port_export.escrow_status(escrow)

    def export_settlement_status(self, *, escrow: Any) -> Any:
        return self._port_export.settlement_status(escrow)

    def export_evidence_status(self, *, evidence_id: str, case_id: str, evidence_hash: str | None = None, status: str = "VERIFIED", data: Mapping[str, Any] | None = None) -> Any:
        return self._port_export.evidence_status(evidence_id=evidence_id, case_id=case_id, evidence_hash=evidence_hash, status=status, data=dict(data or {}))

    def export_audit_event(self, *, reference_id: str, event_type: str, timestamp: str, evidence_hash: str | None = None, data: Mapping[str, Any] | None = None) -> Any:
        return self._port_export.audit_event(reference_id=reference_id, event_type=event_type, timestamp=timestamp, evidence_hash=evidence_hash, data=dict(data or {}))


__all__ = ["EXIMConnectorAdapter"]
