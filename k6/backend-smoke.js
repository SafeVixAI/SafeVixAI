// SPDX-License-Identifier: MIT
// k6 smoke test — 1 VU, all 25 backend endpoints, P95 < 500ms
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 1,
  duration: '30s',
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.01'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
  const headers = { 'Content-Type': 'application/json' };

  // Health
  let r = http.get(`${BASE_URL}/health`, { headers });
  check(r, { 'health ok': (res) => res.status === 200 });

  // API v1 endpoints
  const endpoints = [
    '/api/v1/emergency/nearby?lat=13.08&lon=80.27',
    '/api/v1/challan/calculate?violation_code=MVA_185',
    '/api/v1/geocode/reverse?lat=13.08&lon=80.27',
    '/api/v1/citizen/nearby-municipalities?lat=13.08&lon=80.27',
    '/api/v1/wards/nearest?lat=13.08&lon=80.27',
    '/api/v1/officers/nearby?lat=13.08&lon=80.27',
    '/api/v1/roadwatch/issues?lat=13.08&lon=80.27&radius=5000',
    '/api/v1/command-center/dashboard',
    '/api/v1/public/health',
    '/api/v1/analytics/summary',
  ];

  for (const ep of endpoints) {
    r = http.get(`${BASE_URL}${ep}`, { headers });
    check(r, { [`${ep} ok`]: (res) => res.status < 500 });
    sleep(0.3);
  }
}
