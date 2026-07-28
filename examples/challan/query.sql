-- DuckDB query used internally for challan calculation
SELECT
  v.description,
  v.default_amount AS base_amount,
  COALESCE(s.override_amount, v.default_amount) AS final_amount,
  v.section,
  v.mva_category
FROM violations_seed v
LEFT JOIN state_overrides s
  ON v.violation_code = s.violation_code
  AND s.state = 'tamil_nadu'
WHERE v.violation_code = 'MVA_185';
