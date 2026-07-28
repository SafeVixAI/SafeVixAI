# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

# Tutorial: Integrate the Challan Calculator

**Time required:** 10 minutes
**Prerequisites:** Running SafeVixAI instance, API access

## Step 1: Calculate a Fine via API

```bash
curl -X POST "http://localhost:8000/api/v1/challan/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "violation_code": "MVA_185",
    "vehicle_class": "motorcycle",
    "state": "Karnataka",
    "is_repeat_offender": false
  }'
```

Expected response:
```json
{
  "fine_amount": 1000,
  "section": "MVA 185 - Drunk Driving",
  "description": "First offense: INR 1,000 fine",
  "source": "Motor Vehicles Act, 1988"
}
```

## Step 2: Use the Frontend UI

Navigate to `http://localhost:3000/challan`:
1. Select a violation from the dropdown (e.g., Drunk Driving, No Helmet, Red Light)
2. Choose your vehicle class (Motorcycle, Car, Truck, etc.)
3. Select your state (Karnataka, Uttar Pradesh, Tamil Nadu, etc.)
4. Toggle "Repeat Offender" if applicable
5. Click "Calculate"

## Step 3: Use Offline Calculation

The challan calculator works offline using client-side DuckDB-Wasm:

```javascript
import { calculateChallanOffline } from '@/lib/duckdb-challan';

var result = await calculateChallanOffline({
  violation_code: 'MVA_185',
  vehicle_class: 'motorcycle',
  state: 'Karnataka',
  is_repeat_offender: false,
});
```

The offline engine uses the same violation data stored in the PWA cache and DuckDB-Wasm for deterministic SQL-based calculation.

## Verification

- API returns HTTP 200 with fine amount
- UI shows the calculated amount with section reference
- Offline calculation returns the same result as the API
- Repeat offender toggle increases the fine amount

## Troubleshooting

| Issue | Solution |
|-------|----------|
| DuckDB-Wasm fails to load | Ensure WASM files are in `public/` directory |
| API returns 422 | Check violation code against [supported codes](../API.md#challan) |
| State override not applying | Verify `state_overrides.csv` contains the state |
| Offline calc different from API | Ensure offline data is up-to-date (check PWA cache version) |
