/** Offline challan calculation using DuckDB-Wasm. */
import { calculateChallanOffline } from "@/lib/duckdb-challan";

interface ChallanParams {
  violationCode: string;
  state: string;
  vehicleClass?: string;
}

async function getFineOffline(params: ChallanParams): Promise<number> {
  const result = await calculateChallanOffline({
    violationCode: params.violationCode,
    state: params.state,
  });
  console.log(`Offline fine: ₹${result.amount}`);
  return result.amount;
}
