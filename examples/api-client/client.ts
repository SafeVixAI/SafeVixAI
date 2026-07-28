/** SafeVixAI TypeScript API client example. */

interface EmergencyServices {
  hospitals: Array<{ name: string; lat: number; lon: number; phone?: string }>;
  police: Array<{ name: string; lat: number; lon: number }>;
  fire: Array<{ name: string; lat: number; lon: number }>;
}

interface ChallanResult {
  amount: number;
  section: string;
  description: string;
}

async function getNearbyEmergency(
  lat: number,
  lon: number,
  radius = 5000
): Promise<EmergencyServices> {
  const params = new URLSearchParams({
    lat: String(lat),
    lon: String(lon),
    radius: String(radius),
  });
  const resp = await fetch(
    `http://localhost:8000/api/v1/emergency/nearby?${params}`
  );
  if (!resp.ok) throw new Error(`API error: ${resp.status}`);
  return resp.json();
}

async function calculateChallan(
  violationCode: string,
  state = "tamil_nadu"
): Promise<ChallanResult> {
  const params = new URLSearchParams({
    violation_code: violationCode,
    state,
  });
  const resp = await fetch(
    `http://localhost:8000/api/v1/challan/calculate?${params}`
  );
  if (!resp.ok) throw new Error(`API error: ${resp.status}`);
  return resp.json();
}

// Usage
const services = await getNearbyEmergency(13.0827, 80.2707);
console.log(`Found ${services.hospitals.length} hospitals`);
