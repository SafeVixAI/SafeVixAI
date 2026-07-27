// SPDX-License-Identifier: MIT
// k6 stress test — ramp to 500 VU, identify breaking point
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 100 },
    { duration: '2m', target: 200 },
    { duration: '2m', target: 300 },
    { duration: '2m', target: 500 },
    { duration: '2m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<5000'],
    http_req_failed: ['rate<0.05'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
  const r = http.get(`${BASE_URL}/api/v1/emergency/nearby?lat=13.08&lon=80.27`, {
    headers: { 'Content-Type': 'application/json' },
  });
  check(r, { 'status ok': (res) => res.status < 500 });
  sleep(1);
}
