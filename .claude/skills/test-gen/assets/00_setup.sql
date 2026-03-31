-- ==========================================================================
-- 00_helpers.sql — Shared test fixtures for Redoe OS pgTAP tests
-- ==========================================================================
-- Uses: supabase-test-helpers (usebasejump)
-- Run first: establishes test users + seed data for all subsequent tests
-- ==========================================================================

BEGIN;
SELECT plan(0);  -- helpers only, no assertions

-- ============================================================
-- TEST USERS — one per security tier, two plants
-- ============================================================

-- T1: Shop Floor (Windsor) — cnc_operator
SELECT tests.create_supabase_user(
  'shopfloor_windsor@test.redoe.local',
  '{"role": "cnc_operator", "plant": "windsor"}'::jsonb
);

-- T1: Shop Floor (Hunan) — moldmaker
SELECT tests.create_supabase_user(
  'shopfloor_hunan@test.redoe.local',
  '{"role": "moldmaker", "plant": "hunan"}'::jsonb
);

-- T2: PM (Windsor)
SELECT tests.create_supabase_user(
  'pm_windsor@test.redoe.local',
  '{"role": "pm", "plant": "windsor"}'::jsonb
);

-- T3: Finance (Windsor)
SELECT tests.create_supabase_user(
  'finance_windsor@test.redoe.local',
  '{"role": "finance", "plant": "windsor"}'::jsonb
);

-- T4: Management / VP (all plants)
SELECT tests.create_supabase_user(
  'vp@test.redoe.local',
  '{"role": "vp", "plant": "windsor"}'::jsonb
);

-- T4: GM (all plants)
SELECT tests.create_supabase_user(
  'gm@test.redoe.local',
  '{"role": "gm", "plant": "windsor"}'::jsonb
);

-- ============================================================
-- SEED DATA — minimal set for test assertions
-- IDs in 900+ range to avoid collision with production seed
-- ============================================================

-- Departments
INSERT INTO departments (id, name, plant_id, cost_center) OVERRIDING SYSTEM VALUE
VALUES
  (901, 'CNC', 'windsor', 'CNC'),
  (902, 'Finance', 'windsor', 'FIN'),
  (903, 'CNC', 'hunan', 'CNC');

-- People (linked to test auth users)
INSERT INTO people (id, first_name, last_name, email, role, department_id, plant_id, hourly_rate, supabase_user_id)
OVERRIDING SYSTEM VALUE VALUES
  (901, 'Test', 'Operator', 'shopfloor_windsor@test.redoe.local', 'cnc_operator', 901, 'windsor', 48.00,
    (SELECT id FROM auth.users WHERE email = 'shopfloor_windsor@test.redoe.local')),
  (902, 'Test', 'PM', 'pm_windsor@test.redoe.local', 'pm', 901, 'windsor', 55.00,
    (SELECT id FROM auth.users WHERE email = 'pm_windsor@test.redoe.local')),
  (903, 'Test', 'Finance', 'finance_windsor@test.redoe.local', 'finance', 902, 'windsor', 50.00,
    (SELECT id FROM auth.users WHERE email = 'finance_windsor@test.redoe.local')),
  (904, 'Test', 'VP', 'vp@test.redoe.local', 'vp', 902, 'windsor', 100.00,
    (SELECT id FROM auth.users WHERE email = 'vp@test.redoe.local')),
  (905, 'Test', 'HunanOp', 'shopfloor_hunan@test.redoe.local', 'moldmaker', 903, 'hunan', 30.00,
    (SELECT id FROM auth.users WHERE email = 'shopfloor_hunan@test.redoe.local')),
  (906, 'Test', 'GM', 'gm@test.redoe.local', 'gm', 902, 'windsor', 110.00,
    (SELECT id FROM auth.users WHERE email = 'gm@test.redoe.local'));

-- Customers
INSERT INTO customers (id, name, code, plant_id) OVERRIDING SYSTEM VALUE VALUES
  (901, 'Test FNG', 'FNG', 'windsor'),
  (902, 'Test Hunan Customer', 'THC', 'hunan');

-- Jobs (one per plant)
INSERT INTO jobs (id, job_id, job_type, plant_id, customer_id, lead_pm_id, status, quote_amount, order_amount)
OVERRIDING SYSTEM VALUE VALUES
  (901, 'R-2026-TEST-1', 'R', 'windsor', 901, 902, 'manufacturing', 100000.00, 120000.00),
  (902, 'G-2026-TEST-1', 'G', 'hunan', 902, NULL, 'design', 50000.00, 55000.00);

-- Job operations
INSERT INTO job_operations (id, job_id, department_id, description, planned_run_hrs)
OVERRIDING SYSTEM VALUE VALUES
  (901, 901, 901, 'Test CNC roughing', 40.00),
  (902, 902, 903, 'Test Hunan CNC roughing', 30.00);

-- Job costs (for cost visibility tests)
INSERT INTO job_costs (id, job_id, cost_type, description, quoted_amount, actual_amount)
OVERRIDING SYSTEM VALUE VALUES
  (901, 901, 'material', 'Steel P20', 30000.00, 28500.00),
  (902, 901, 'labour', 'CNC hours', 25000.00, 27000.00);

-- Machines
INSERT INTO machines (id, name, code, machine_type, department_id, plant_id)
OVERRIDING SYSTEM VALUE VALUES
  (901, 'Parpas 1', 'PAR1', 'cnc', 901, 'windsor');

INSERT INTO machine_monitoring_config (machine_id, idle_reason_input_sec)
VALUES (901, 1200);  -- 20 minutes

-- Notifications (for notif visibility tests)
INSERT INTO notifications (id, recipient_id, title, body) OVERRIDING SYSTEM VALUE VALUES
  (901, 901, 'Test Notif for Operator', 'You have a new task'),
  (902, 903, 'Test Notif for Finance', 'Invoice ready');

-- Purchase Requisitions (for PR visibility tests)
INSERT INTO purchase_requisitions (id, pr_number, job_id, requester_id, category, description, amount, status)
OVERRIDING SYSTEM VALUE VALUES
  (901, 'PR-TEST-001', 901, 901, 'mro', 'Test tooling supplies', 500.00, 'draft'),
  (902, 'PR-TEST-002', 901, 903, 'services', 'Test service PR', 2000.00, 'submitted');

-- Purchase Orders (for PO visibility tests)
INSERT INTO purchase_orders (id, po_number, pr_id, job_id, vendor_id, status, amount)
OVERRIDING SYSTEM VALUE VALUES
  (901, 'PO-TEST-001', 901, 901, NULL, 'draft', 500.00);

SELECT * FROM finish();
COMMIT;
