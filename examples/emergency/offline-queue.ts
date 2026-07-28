/** Offline SOS queue example. */
// Frontend: Queue SOS when offline
import { enqueueSOS } from "@/lib/offline-sos-queue";

async function sendSOSOffline(lat: number, lon: number): Promise<void> {
  if (!navigator.onLine) {
    await enqueueSOS({
      lat,
      lon,
      timestamp: Date.now(),
    });
    console.log("SOS queued for delivery when online");
  } else {
    // Online — send directly
    const resp = await fetch("http://localhost:8000/api/v1/live-tracking/trigger-sos", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lat, lon }),
    });
    if (!resp.ok) throw new Error(`SOS failed: ${resp.status}`);
    console.log("SOS sent");
  }
}
