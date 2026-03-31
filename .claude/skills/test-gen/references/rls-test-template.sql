-- ==========================================================================
-- RLS Test Template — Redoe OS
-- Replace: <TABLE>, <POLICY>, <COLUMN>, <VALUE>, <ALLOWED_ROLE>, <BLOCKED_ROLE>
-- ==========================================================================

BEGIN;
SELECT plan(6);  -- adjust count

-- ============================================================
-- POSITIVE: Allowed role sees expected data
-- ============================================================
SELECT tests.authenticate_as('<ALLOWED_ROLE>@test.redoe.local');

SELECT is(
  (SELECT COUNT(*)::int FROM <TABLE> WHERE <COLUMN> = '<VALUE>'),
  1,
  '<ALLOWED_ROLE> CAN see <TABLE> row'
);

-- ============================================================
-- POSITIVE: Management sees cross-plant data
-- ============================================================
SELECT tests.authenticate_as('vp@test.redoe.local');

SELECT is(
  (SELECT COUNT(*)::int FROM <TABLE>),
  2,  -- both plants
  'VP sees all <TABLE> rows across plants'
);

-- ============================================================
-- NEGATIVE: Blocked role sees nothing
-- ============================================================
SELECT tests.authenticate_as('<BLOCKED_ROLE>@test.redoe.local');

SELECT is(
  (SELECT COUNT(*)::int FROM <TABLE>),
  0,
  '<BLOCKED_ROLE> CANNOT see <TABLE>'
);

-- ============================================================
-- NEGATIVE: Cross-plant access blocked
-- ============================================================
SELECT tests.authenticate_as('shopfloor_windsor@test.redoe.local');

SELECT is(
  (SELECT COUNT(*)::int FROM <TABLE> WHERE plant_id = 'hunan'),
  0,
  'Windsor user CANNOT see Hunan <TABLE> data'
);

-- ============================================================
-- NEGATIVE: Unauthenticated sees nothing
-- ============================================================
SELECT tests.clear_authentication();

SELECT is(
  (SELECT COUNT(*)::int FROM <TABLE>),
  0,
  'Unauthenticated sees NO <TABLE> rows'
);

-- ============================================================
-- POSITIVE: GM also has cross-plant access
-- ============================================================
SELECT tests.authenticate_as('gm@test.redoe.local');

SELECT is(
  (SELECT COUNT(*)::int FROM <TABLE>),
  2,
  'GM sees all <TABLE> rows across plants'
);

SELECT * FROM finish();
ROLLBACK;
