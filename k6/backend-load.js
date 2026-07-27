// SPDX-License-Identifier: MIT
// k6 load test — 100 VU, 5 min, P95 < 2s, error < 1%
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '1m', target: 100 },
    { duration: '3m', target: 100 },
    { duration: '1m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'],
    http_req_failed: ['rate<0.01'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

const ENDPOINTS = [
  '/api/v1/emergency/nearby?lat=13.08&lon=80.27',
  '/api/v1/challan/calculate?violation_code=MVA_185',
  '/api/v1/geocode/reverse?lat=13.08&lon=80.27',
  '/api/v1/wards/nearest?lat=13.08&lon=80.27',
  '/api/v1/command-center/dashboard',
];

export default function () {
  const ep = ENDPOINTS[Math.floor(Math.random() * ENDPOINTS.length)];
  const r = http.get(`${BASE_URL}${ep}`, {
    headers: { 'Content-Type': 'application/json' },
  });
  check(r, { 'status ok': (res) => res.status < 500 });
  sleep(Math.random() * 2 + 1);
}
