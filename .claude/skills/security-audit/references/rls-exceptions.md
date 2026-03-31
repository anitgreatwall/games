# RLS Exceptions — Tables Intentionally Without Row Level Security

These tables are public-read by design. They contain reference/configuration data with no user-specific or sensitive content.

| Table | Justification | Reviewed By | Date |
|-------|--------------|-------------|------|
| departments | Lookup table — all users need to see department list for forms/filters | Steve Pan | 2026-03-07 |
| shifts | Lookup table — shift definitions needed for time entry UI | Steve Pan | 2026-03-07 |
| indirect_codes | Lookup table — "500 job" subcategories for time entry dropdown | Steve Pan | 2026-03-07 |
| break_types | Lookup table — break options for time tracking | Steve Pan | 2026-03-07 |
| scrap_reasons | Lookup table — scrap reason codes for quality reporting | Steve Pan | 2026-03-07 |
| downtime_reasons | Lookup table — machine downtime reason codes | Steve Pan | 2026-03-07 |
| sync_state | System config — external system health status | Steve Pan | 2026-03-07 |
| machine_monitoring_config | Config — per-machine monitoring thresholds | Steve Pan | 2026-03-07 |
| audit_log | Read-restricted via application layer, not RLS. Only management dashboard queries this table. | Steve Pan | 2026-03-07 |

## Rules for Adding Exceptions

1. Table must contain ONLY reference/config data — no user-specific, financial, or operational records
2. Must be reviewed and approved by Steve or Andy
3. Must include justification explaining why RLS is unnecessary
4. Review annually — if table gains sensitive columns, add RLS

## Tables That MUST Have RLS (never exempt)

- jobs, job_operations, job_costs — core business data
- labour_entries — worker time records
- purchase_requisitions, purchase_orders, po_line_items, po_receipts — financial
- requirement_forms (Work Orders) — approval workflows
- eco_headers, eco_line_items — engineering changes
- quality_incidents — quality management
- notifications — user-scoped messages
- machine_events, machine_alerts — operational monitoring
- people — HR/employee data
- customers, vendors — business relationships
- quotes, quote_versions, quote_line_items — commercial
- revenue_recognition — financial
- iso_documents, iso_document_versions — controlled documents
