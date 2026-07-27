# Challan Calculation Examples

> **Fine calculation with state overrides and offline mode.**

---

## Online Calculation

```python
import httpx

BASE = "http://localhost:8000"

# Basic fine calculation
resp = httpx.get(f"{BASE}/api/v1/challan/calculate", params={
    "violation_code": "MVA_185",  # Drunk driving
    "state": "tamil_nadu",
})
print(resp.json())
# {'amount': 10000, 'section': '185 MV Act', 'description': 'Driving under influence of alcohol'}

# With vehicle class override
resp = httpx.get(f"{BASE}/api/v1/challan/calculate", params={
    "violation_code": "MVA_194D",  # No helmet
    "state": "karnataka",
    "vehicle_class": "motorcycle",
})
print(f"Fine: ₹{resp.json()['amount']}")
```

## Offline Calculation (Browser)

```typescript
// Frontend: DuckDB-Wasm offline challan calculator
import { calculateChallanOffline } from '@/lib/duckdb-challan';

const result = await calculateChallanOffline({
  violationCode: 'MVA_185',
  state: 'tamil_nadu',
});
console.log(`Offline fine: ₹${result.amount}`);
```

## SQL Direct (for advanced use)

```sql
-- DuckDB query used internally
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
```
