# Schema Quick Reference — Redoe OS v1.1

Use this to auto-suggest tables when a user describes a feature. Match their description to the relevant domain, then suggest the tables and their RLS tier.

## Tables by Domain

### Time & Labour
| Table | RLS | Tier | Description |
|-------|-----|------|-------------|
| labour_entries | YES | All read, own insert | Clock in/out, hours, job/op allocation |
| break_entries | NO | Open | Break tracking |
| shifts | NO | Open (lookup) | Shift definitions |
| indirect_codes | NO | Open (lookup) | Non-job time codes |

### Jobs & Operations
| Table | RLS | Tier | Description |
|-------|-----|------|-------------|
| jobs | YES | Plant-gated, mgmt all | Master job record (R/G/C/P/S types) |
| job_operations | YES | Plant-gated, mgmt all | Operations within a job |
| job_costs | YES | Finance/PM/mgmt only | Cost line items per job |
| job_cost_adjustments | NO | — | Cost corrections |
| job_notes | NO | — | Free-text notes on jobs |

### Purchasing
| Table | RLS | Tier | Description |
|-------|-----|------|-------------|
| purchase_requisitions | YES | Own + finance/buyer/mgmt | PR forms (OA equivalent) |
| purchase_orders | YES | Finance/buyer/mgmt | POs (SAP equivalent) |
| po_line_items | NO | — | PO detail lines |
| po_receipts | NO | — | Goods receipt |

### Quoting & Sales
| Table | RLS | Tier | Description |
|-------|-----|------|-------------|
| quotes | NO | — | Quote headers |
| quote_versions | NO | — | Quote revisions |
| quote_line_items | NO | — | Quote detail lines |
| customers | NO | — | Customer master |

### Engineering & Design
| Table | RLS | Tier | Description |
|-------|-----|------|-------------|
| requirement_forms | NO | — | F738 / Work Order forms |
| approval_checklist_items | NO | — | Checklist per F738 |
| approved_construction | NO | — | Approved construction records |
| eco_headers | NO | — | Engineering Change Orders |
| eco_line_items | NO | — | ECO detail lines |
| design_reviews | NO | — | Design review meetings |
| design_review_attendance | NO | — | Attendees |
| design_review_checklist | NO | — | Review checklist items |
| design_status_tasks | NO | — | Design milestone tracking |
| engineering_tracking | NO | — | Engineering progress |

### Machines & OEE
| Table | RLS | Tier | Description |
|-------|-----|------|-------------|
| machines | NO | — | Machine master data |
| machine_events | YES | Open read | Runtime/idle/setup events |
| machine_alerts | YES | Open read | Threshold breach alerts |
| machine_monitoring_config | NO | Open (config) | Alert thresholds |
| oee_snapshots | NO | — | OEE calculations |
| downtime_reasons | NO | Open (lookup) | Downtime reason codes |

### Quality & ISO
| Table | RLS | Tier | Description |
|-------|-----|------|-------------|
| quality_incidents | NO | — | NCRs, complaints, findings |
| iso_documents | NO | — | ISO document registry |
| iso_document_versions | NO | — | Document versions |
| best_practices | NO | — | Lessons learned |

### Finance & Revenue
| Table | RLS | Tier | Description |
|-------|-----|------|-------------|
| revenue_recognition | NO | — | Rev rec milestones |
| shipments | NO | — | Shipment records |
| kpi_snapshots | NO | — | Plant-level KPIs |

### System
| Table | RLS | Tier | Description |
|-------|-----|------|-------------|
| people | NO | — | Employee master (links to Supabase auth) |
| departments | NO | Open (lookup) | Department list |
| programs | NO | — | Customer programs |
| vendors | NO | — | Vendor master |
| notifications | YES | Own only | User notifications |
| audit_log | NO | Open (append-only) | All changes |
| sync_state | NO | Open (config) | SAP sync tracking |
| data_health_checks | NO | — | Data quality checks |
| data_receipt_log | NO | — | External data receipts |
| scrap_reasons | NO | Open (lookup) | Scrap codes |
| break_types | NO | Open (lookup) | Break type definitions |

## RLS Tier Summary

| Tier | Roles | Access Pattern |
|------|-------|---------------|
| Shop Floor | cnc_operator, moldmaker, edm_operator, inspector | Own plant jobs, own labour entries |
| PM | pm, scheduler | Own plant jobs, all labour (read) |
| Finance | finance, buyer | All financial data, purchasing |
| Management | gm, vp, plant_mgr, engineering_mgr, sales | All plants, all data |

## Key Enums

- **job_type:** R (Design & Build), G (Global/Hunan), C (Component), P (Production/PES), S (Service)
- **job_status:** quoted → po_received → design → engineering → manufacturing → tryout → tuning → shipped → invoiced → closed
- **person_role:** pm, designer, moldmaker, cnc_operator, edm_operator, inspector, finance, management, sales, engineering_mgr, plant_mgr, gm, vp, buyer, scheduler, it
- **cost_type:** labour, material, outsource, tariff, freight, tuning, financing, overhead, other
