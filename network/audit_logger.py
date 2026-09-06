class AuditLogger:
    def __init__(self):
        self.logs = []

    def record_event(self, event_type: str, details: str) -> bool:
        log_entry = {"event": event_type, "details": details}
        self.logs.append(log_entry)
        return True

    def get_log_count(self) -> int:
        return len(self.logs)