"""Load supplied rules literally; condition text is never executable code."""

from ..ingest.loader import InputError, read_records
from .models import Rule

ACTION_NAMES = frozenset({"DELETE", "REDACT", "ANONYMIZE", "RETAIN"})

# SCHEMA mappings from participant collection names, not resource-ID patterns.
COLLECTIONS = {
    "customer_profiles": "USER_PROFILE", "customer_profiles_primary": "USER_PROFILE",
    "customer_profiles_failover_replica": "USER_PROFILE", "profile_lookups": "USER_PROFILE",
    "customer_search_documents": "SEARCH_INDEX_ENTRY", "search_documents_primary": "SEARCH_INDEX_ENTRY",
    "index_queries": "SEARCH_INDEX_ENTRY", "customer_analytics_reports": "ANALYTICS_PROFILE",
    "customer_analytics_profiles": "ANALYTICS_PROFILE", "tickets": "SUPPORT_MESSAGE",
    "support_records": "SUPPORT_MESSAGE", "support_conversations": "SUPPORT_MESSAGE",
    "ticket_attachments": "SUPPORT_ATTACHMENT", "customer_exports": "USER_EXPORT",
    "customer_export_jobs": "USER_EXPORT", "exports": "USER_EXPORT",
    "security_audit_events": "SECURITY_AUDIT_LOG", "security_audit_records": "SECURITY_AUDIT_LOG",
    "audit_records": "SECURITY_AUDIT_LOG", "deleted_customer_references": "ACCOUNT_TOMBSTONE",
    "retained_order_records": "LEGAL_HOLD_RECORD", "backup_catalog": "BACKUP_ARCHIVE",
    "backup_restore_entries": "BACKUP_ARCHIVE", "restore_entries": "BACKUP_ARCHIVE",
    "connector_subscriptions": "DATA_FLOW", "connector_configurations": "DATA_FLOW", "connectors": "DATA_FLOW",
}
EVENT_CATEGORIES = {
    "profile_lookup_completed": "USER_PROFILE", "index_query_completed": "SEARCH_INDEX_ENTRY",
    "contact_query_completed": "SUPPORT_MESSAGE", "support_ticket_read_completed": "SUPPORT_MESSAGE",
    "message_read": "SUPPORT_MESSAGE", "message_pii_scan": "SUPPORT_MESSAGE",
    "attachment_pii_scan": "SUPPORT_ATTACHMENT", "analytics_identity_scan": "ANALYTICS_PROFILE",
    "analytics_profile_read": "ANALYTICS_PROFILE", "analytics_profile_read_completed": "ANALYTICS_PROFILE",
    "connector_config_loaded": "DATA_FLOW", "connector_heartbeat": "DATA_FLOW",
    "connector_config_read_completed": "DATA_FLOW", "restore_policy_read_completed": "BACKUP_ARCHIVE",
    "restore_candidate_evaluated": "BACKUP_ARCHIVE", "restore_authorization_completed": "BACKUP_ARCHIVE",
    "export_download_check_completed": "USER_EXPORT", "export_metadata_read_completed": "USER_EXPORT",
    "audit_record_read_completed": "SECURITY_AUDIT_LOG", "retained_order_loaded": "LEGAL_HOLD_RECORD",
}


class RuleBook:
    def __init__(self, rules):
        self.rules = tuple(rules)
        if len({r.rule_id for r in self.rules}) != len(self.rules) or len({r.category for r in self.rules}) != len(self.rules):
            raise InputError("duplicate rule ID or overlapping category; policy selection is ambiguous")
        if any(not r.rule_id.strip() or not r.category.strip() or not r.condition.strip() or r.action not in ACTION_NAMES for r in self.rules):
            raise InputError("invalid policy rule")
        self.by_category = {r.category: r for r in self.rules}

    @classmethod
    def load(cls, dataset_root):
        rows = read_records(dataset_root / "deletion_rules.csv", ("rule_id", "data_category", "condition", "required_action"))
        if not rows:
            raise InputError("policy rule table is empty")
        return cls(Rule(r["rule_id"], r["data_category"], r["condition"], r["required_action"]) for r in rows)

    def category(self, state, payloads):
        categories = set()
        for observation in state.timeline:
            if observation.claim_kind not in {"RECORD_SNAPSHOT", "SQL_RECORD", "LOG_EVENT"}:
                continue
            data = payloads[observation.observation_id]
            raw = observation.resource.category or data.get("record_type", "")
            if raw == "profiles":
                raw = {"account_service": "USER_PROFILE", "analytics_platform": "ANALYTICS_PROFILE"}.get(state.resource.system_id, "")
            canonical = raw if raw in self.by_category or raw == "DATA_FLOW" else COLLECTIONS.get(raw)
            event_category = EVENT_CATEGORIES.get(data.get("event"))
            if canonical:
                categories.add(canonical)
            if event_category:
                categories.add(event_category)
        return next(iter(categories)) if len(categories) == 1 else None
