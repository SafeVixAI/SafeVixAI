// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

const COMPRESSION_ENABLED = true;

export async function loadGeoJSON(url: string): Promise<GeoJSON.GeoJSON> {
  /* istanbul ignore next */
  if (!COMPRESSION_ENABLED) {
    const resp = await fetch(url);
    return resp.json();
  }

  const supportsDecompression =
    typeof DecompressionStream !== 'undefined' && typeof fetch !== 'undefined';
  if (!supportsDecompression) {
    const resp = await fetch(url);
    return resp.json();
  }

  const gzUrl = `${url}.gz`;
  try {
    const resp = await fetch(gzUrl);
    if (!resp.ok) throw new Error('Gzip not available');
    const stream = resp.body?.pipeThrough(new DecompressionStream('gzip'));
    const decompressedResp = new Response(stream);
    return decompressedResp.json();
  } catch {
    const resp = await fetch(url);
    return resp.json();
  }
}

export { }
