/** Family tracking WebSocket integration example. */
const WS_URL = `ws://localhost:8000/api/v1/tracking/${groupId}`;
const ws = new WebSocket(WS_URL);

interface LocationUpdate {
  type: "location_update";
  lat: number;
  lon: number;
  speed: number;
  battery: number;
}

interface FamilyLocation {
  lat: number;
  lon: number;
  memberId: string;
  timestamp: number;
}

ws.onopen = () => {
  const update: LocationUpdate = {
    type: "location_update",
    lat: 13.0827,
    lon: 80.2707,
    speed: 0,
    battery: 85,
  };
  ws.send(JSON.stringify(update));
};

ws.onmessage = (event: MessageEvent) => {
  const data: FamilyLocation = JSON.parse(event.data);
  console.log("Family member location:", data.lat, data.lon);
};

ws.onerror = (error: Event) => {
  console.error("WebSocket error:", error);
};

export { ws };
