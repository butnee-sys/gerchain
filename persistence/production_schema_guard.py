from __future__ import annotations

from sqlalchemy import inspect
from sqlalchemy.engine import Connection

REQUIRED_COLUMNS = {
    'gerchain_ledger_accounts': {'account_id','currency','balance','version','updated_at'},
    'gerchain_ledger_movements': {'id','transaction_id','source','destination','amount','currency','operation','escrow_id','integrity_hash','created_at'},
    'escrows': {'id','sender_address','receiver_address','amount','state','condition_desc','refund_destination','currency','version','created_at','updated_at'},
    'gerchain_transaction_witnesses': {'id','transaction_id','event_type','escrow_id','amount','created_at'},
    'gerchain_outbox_events': {'id','event_id','event_type','aggregate_id','payload_json','state','lease_until','attempts','created_at','updated_at'},
    'gerchain_idempotency_records': {'id','key','fingerprint','result_json','state','created_at','updated_at'},
}
REQUIRED_ESCROW_STATES = {'CREATED','FUNDED','LOCKED','RELEASED','REFUNDED','CANCELLED'}

def assert_canonical_production_schema(connection: Connection) -> None:
    if connection.dialect.name != 'postgresql':
        raise RuntimeError('canonical production schema requires PostgreSQL')
    inspector = inspect(connection)
    missing = []
    for table, columns in REQUIRED_COLUMNS.items():
        actual = {column['name'] for column in inspector.get_columns(table)}
        if not actual:
            missing.append(f'{table}: TABLE_MISSING')
            continue
        for column in sorted(columns - actual):
            missing.append(f'{table}: COLUMN_MISSING:{column}')
    if missing:
        raise RuntimeError('canonical production schema incomplete; migration required: ' + ', '.join(missing))
    constraints = inspector.get_check_constraints('escrows')
    state_sql = ' '.join(str(item.get('sqltext','')) for item in constraints).upper()
    for state in sorted(REQUIRED_ESCROW_STATES):
        if state not in state_sql:
            raise RuntimeError('canonical production schema escrow state constraint incomplete; required state ' + state)
    movement_constraints = inspector.get_check_constraints('gerchain_ledger_movements')
    movement_names = {str(item.get('name')) for item in movement_constraints}
    required_movement_constraints = {
        'gerchain_movement_operation_check',
        'gerchain_movement_integrity_hash_check',
        'gerchain_movement_escrow_binding_check',
    }
    missing_movement_constraints = sorted(required_movement_constraints - movement_names)
    if missing_movement_constraints:
        raise RuntimeError(
            'canonical production schema movement integrity constraints incomplete: '
            + ', '.join(missing_movement_constraints)
        )

    # SETTLEMENT is a direct Canonical Ledger movement, not an escrow
    # transition. Its escrow_id is therefore intentionally NULL; escrow-bound
    # operations FUND/RELEASE/REFUND/CANCEL must carry a non-empty escrow_id.
    binding_constraint = next(
        (item for item in movement_constraints if item.get('name') == 'gerchain_movement_escrow_binding_check'),
        None,
    )
    binding_sql = str((binding_constraint or {}).get('sqltext', '')).upper()
    if 'SETTLEMENT' not in binding_sql or 'ESCROW_ID IS NOT NULL' not in binding_sql:
        raise RuntimeError(
            'canonical production schema settlement/escrow binding contract is incomplete'
        )
