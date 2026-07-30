// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

if (typeof globalThis.Response === 'undefined') {
  (globalThis as Record<string, unknown>).Response = class {
    body: unknown;
    status: number;
    ok: boolean;
    constructor(body?: unknown, init?: Record<string, unknown>) {
      this.body = body;
      this.status = ((init?.status as number) ?? 200);
      this.ok = this.status >= 200 && this.status < 300;
    }
    async json(): Promise<unknown> {
      if (this.body == null) throw new SyntaxError('Unexpected end of JSON input');
      if (typeof this.body === 'string') return JSON.parse(this.body);
      if (this.body instanceof Uint8Array) return JSON.parse(new TextDecoder().decode(this.body));
      if (typeof (this.body as Record<string, unknown>).json === 'function') return (this.body as Record<string, unknown>).json;
      return JSON.parse(String(this.body));
    }
  };
}

import { loadGeoJSON } from '../load-geojson';

let mockValidGeoJSON: Record<string, unknown>;

function createMockResponse(data: unknown, overrides?: Record<string, unknown>): Response {
  return {
    ok: true,
    status: 200,
    json: jest.fn().mockResolvedValue(data),
    body: null,
    ...overrides,
  } as unknown as Response;
}

beforeEach(function() {
  mockValidGeoJSON = {
    type: 'FeatureCollection',
    features: [
      {
        type: 'Feature',
        geometry: { type: 'Point', coordinates: [80.2707, 13.0827] },
        properties: { name: 'Test Point' },
      },
    ],
  };
  globalThis.fetch = jest.fn();
  delete (globalThis as Record<string, unknown>).DecompressionStream;
});

describe('loadGeoJSON', function() {
  it('loads valid GeoJSON via direct fetch when DecompressionStream is unavailable', async function() {
    (globalThis.fetch as jest.Mock).mockResolvedValue(
      createMockResponse(mockValidGeoJSON)
    );

    const result = await loadGeoJSON('https://example.com/data.geojson');

    expect(result).toEqual(mockValidGeoJSON);
    expect(globalThis.fetch).toHaveBeenCalledTimes(1);
    expect(globalThis.fetch).toHaveBeenCalledWith('https://example.com/data.geojson');
  });

  it('loads valid GeoJSON via gzip decompression', async function() {
    (globalThis as Record<string, unknown>).DecompressionStream = jest.fn();

    const gzBody = {
      pipeThrough: jest.fn().mockReturnValue(JSON.stringify(mockValidGeoJSON)),
    };

    (globalThis.fetch as jest.Mock).mockImplementation(function(url: string) {
      if (url.endsWith('.gz')) {
        return Promise.resolve(createMockResponse(null, {
          ok: true,
          body: gzBody,
        }));
      }
      return Promise.resolve(createMockResponse(mockValidGeoJSON));
    });

    const result = await loadGeoJSON('https://example.com/data.geojson');

    expect(result).toEqual(mockValidGeoJSON);
    expect(globalThis.fetch).toHaveBeenCalledWith('https://example.com/data.geojson.gz');
    expect(globalThis.fetch).toHaveBeenCalledTimes(1);
  });

  it('falls back to direct fetch when gzip response is not ok', async function() {
    (globalThis as Record<string, unknown>).DecompressionStream = jest.fn();

    (globalThis.fetch as jest.Mock).mockImplementation(function(url: string) {
      if (url.endsWith('.gz')) {
        return Promise.resolve(createMockResponse(null, { ok: false, status: 404 }));
      }
      return Promise.resolve(createMockResponse(mockValidGeoJSON));
    });

    const result = await loadGeoJSON('https://example.com/data.geojson');

    expect(result).toEqual(mockValidGeoJSON);
    expect(globalThis.fetch).toHaveBeenCalledWith('https://example.com/data.geojson.gz');
    expect(globalThis.fetch).toHaveBeenCalledWith('https://example.com/data.geojson');
  });

  it('falls back to direct fetch when gzip fetch throws', async function() {
    (globalThis as Record<string, unknown>).DecompressionStream = jest.fn();

    (globalThis.fetch as jest.Mock).mockImplementation(function(url: string) {
      if (url.endsWith('.gz')) {
        return Promise.reject(new Error('Gzip network failure'));
      }
      return Promise.resolve(createMockResponse(mockValidGeoJSON));
    });

    const result = await loadGeoJSON('https://example.com/data.geojson');

    expect(result).toEqual(mockValidGeoJSON);
    expect(globalThis.fetch).toHaveBeenCalledWith('https://example.com/data.geojson.gz');
    expect(globalThis.fetch).toHaveBeenCalledWith('https://example.com/data.geojson');
    expect(globalThis.fetch).toHaveBeenCalledTimes(2);
  });

  it('rejects when direct fetch fails with network error (no decompression)', async function() {
    (globalThis.fetch as jest.Mock).mockRejectedValue(new Error('Network failure'));

    await expect(
      loadGeoJSON('https://example.com/data.geojson')
    ).rejects.toThrow('Network failure');
  });

  it('rejects when all paths fail (gzip throws, then direct throws)', async function() {
    (globalThis as Record<string, unknown>).DecompressionStream = jest.fn();
    (globalThis.fetch as jest.Mock).mockRejectedValue(new Error('Network unavailable'));

    await expect(
      loadGeoJSON('https://example.com/data.geojson')
    ).rejects.toThrow('Network unavailable');
  });

  it('loads from URLs with query parameters', async function() {
    (globalThis.fetch as jest.Mock).mockResolvedValue(
      createMockResponse(mockValidGeoJSON)
    );

    const result = await loadGeoJSON('https://example.com/data.geojson?token=abc&v=2');

    expect(result).toEqual(mockValidGeoJSON);
    expect(globalThis.fetch).toHaveBeenCalledWith('https://example.com/data.geojson?token=abc&v=2');
  });
});
