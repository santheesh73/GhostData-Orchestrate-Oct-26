"""Nested record/snapshot/service-export adapters, independent of filenames."""

from .normalization import (MAX_UNITS, ParseDiagnostic, finish,
                            make_observation, observation_time, strict_json)

# Schema adapters, not subject/policy classifiers. Explicit system fields win.
COLLECTION_SYSTEM = {
    "customer_profiles": "account_service", "customer_analytics_reports": "analytics_platform",
    "customer_analytics_profiles": "analytics_platform", "customer_search_documents": "search_service",
    "customer_export_jobs": "export_service", "customer_exports": "export_service",
    "support_records": "support_platform", "connector_subscriptions": "integration_service",
    "backup_restore_entries": "backup_service", "security_audit_records": "security_service",
    "search_documents_primary": "search_service", "customer_profiles_primary": "account_service",
    "customer_profiles_failover_replica": "account_service",
}


def pointer(parent, key):
    return parent + "/" + str(key).replace("~", "~0").replace("/", "~1")


def parse_json_document(text, source, digest):
    data = strict_json(text)
    if not isinstance(data, (dict, list)):
        raise ValueError("JSON evidence must contain an object or array")
    observations, diagnostics = [], []
    seen = parsed = 0
    if isinstance(data, dict) and "resource_id" not in data:
        metadata = {k: v for k, v in data.items() if not isinstance(v, (dict, list))}
        if metadata:
            observations.append(make_observation(source, digest, "/@metadata", metadata,
                observed_at=source.available_at, time_basis="file_capture" if source.available_at else "unknown",
                claim_kind="FILE_METADATA"))
            seen += 1
            parsed += 1

    def visit(node, location, system="", collection="", clock=None, basis="unknown", expected=False):
        nonlocal seen, parsed
        if seen > MAX_UNITS:
            raise ValueError("JSON record budget exceeded")
        if isinstance(node, list):
            for index, child in enumerate(node):
                visit(child, pointer(location, index), system, collection, clock, basis, expected)
            return
        if not isinstance(node, dict):
            if expected:
                seen += 1
                diagnostics.append(ParseDiagnostic("INVALID_RECORD", location, "record must be an object", "ERROR"))
            return
        system = node.get("origin_system", node.get("system_id", node.get("system", node.get("data_store", system))))
        collection = node.get("collection_name", node.get("collection", collection))
        if not isinstance(system, str) or not isinstance(collection, str):
            diagnostics.append(ParseDiagnostic("INVALID_CONTEXT", location, "system/collection metadata must be strings", "ERROR"))
            system, collection = "", ""
        system = system or COLLECTION_SYSTEM.get(collection, "")
        clock, basis = observation_time(node, clock, basis, diagnostics, location)
        if "resource_id" in node or expected:
            seen += 1
            resource = node.get("resource_id", "")
            valid = isinstance(resource, str) and bool(resource.strip())
            if not valid:
                diagnostics.append(ParseDiagnostic("MISSING_RESOURCE_ID", location, "record has no nonempty resource identifier", "ERROR"))
            observations.append(make_observation(
                source, digest, location or "/", node, system=system, resource=resource if valid else "",
                category=str(node.get("record_type", collection)), physical_copy=collection,
                observed_at=clock, time_basis=basis, claim_kind="RECORD_SNAPSHOT" if valid else "RAW_UNPARSED"))
            parsed += int(valid)
        containers = {"records", "snapshots", "service_exports"}
        if "records" in node:
            records = node["records"]
            if not isinstance(records, list):
                diagnostics.append(ParseDiagnostic("INVALID_CONTAINER", pointer(location, "records"), "records must be an array", "ERROR"))
            else:
                seen += 1
                parsed += 1
                metadata = {k: v for k, v in node.items() if k not in containers}
                metadata["record_count_observed"] = len(records)
                metadata["completeness"] = "NOT_ESTABLISHED"
                observations.append(make_observation(source, digest, location + "/@scope", metadata,
                    system=system, category="COLLECTION_SCOPE", physical_copy=collection,
                    observed_at=clock, time_basis=basis, claim_kind="SCOPE_METADATA"))
                if "record_count" in node and node["record_count"] != len(records):
                    diagnostics.append(ParseDiagnostic("COUNT_MISMATCH", location, "declared and observed record counts differ"))
                visit(records, pointer(location, "records"), system, collection, clock, basis, True)
        if "service_exports" in node:
            services = node["service_exports"]
            if not isinstance(services, dict):
                diagnostics.append(ParseDiagnostic("INVALID_CONTAINER", location, "service_exports must be an object", "ERROR"))
            else:
                for service, groups in services.items():
                    if not isinstance(groups, dict):
                        diagnostics.append(ParseDiagnostic("INVALID_CONTAINER", location, "service export groups must be objects", "ERROR"))
                        continue
                    for group, records in groups.items():
                        group_path = pointer(pointer(pointer(location, "service_exports"), service), group)
                        if not isinstance(records, list):
                            diagnostics.append(ParseDiagnostic("INVALID_CONTAINER", group_path, "service collection must be an array", "ERROR"))
                        else:
                            seen += 1
                            parsed += 1
                            observations.append(make_observation(source, digest, group_path + "/@scope",
                                {"service": service, "collection": group, "record_count_observed": len(records),
                                 "completeness": "NOT_ESTABLISHED"}, system=service, category="COLLECTION_SCOPE",
                                physical_copy=group, observed_at=clock, time_basis=basis, claim_kind="SCOPE_METADATA"))
                            visit(records, group_path, service, group, clock, basis, True)
        for key, value in node.items():
            if key not in {"records", "service_exports"} and isinstance(value, (dict, list)):
                visit(value, pointer(location, key), system, collection, clock, basis)

    visit(data, "", clock=source.available_at,
          basis="file_capture" if source.available_at is not None else "unknown")
    if not any(o.claim_kind != "FILE_METADATA" for o in observations):
        diagnostics.append(ParseDiagnostic("UNSUPPORTED_JSON_SHAPE", "/", "no resource records or declared collection scope found"))
    return finish(source, "json", digest, observations, diagnostics, seen, parsed)
