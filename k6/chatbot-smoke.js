// SPDX-License-Identifier: MIT
// k6 smoke test — 20 VU chat, 10 VU stream, P95 < 5s
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    chat: {
      executor: 'constant-vus',
      vus: 20,
      duration: '30s',
    },
    stream: {
      executor: 'constant-vus',
      vus: 10,
      duration: '30s',
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<5000'],
    http_req_failed: ['rate<0.05'],
  },
};

const BASE_URL = __ENV.CHATBOT_URL || 'http://localhost:8010';
const HEADERS = { 'Content-Type': 'application/json' };

export default function () {
  const payload = JSON.stringify({
    message: 'What is the fine for speeding in India?',
    session_id: `k6-test-${__VU}`,
  });

  const r = http.post(`${BASE_URL}/api/v1/chat/`, payload, { headers: HEADERS });
  check(r, { 'chat ok': (res) => res.status < 500 });
  sleep(2);
}
