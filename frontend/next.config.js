// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
let withBundleAnalyzer = (cfg) => cfg;
try {
  withBundleAnalyzer = require('@next/bundle-analyzer')({
    enabled: process.env.ANALYZE === 'true',
  });
} catch (_) {
}

const nextConfig = {
  experimental: {
    optimizePackageImports: ['lucide-react', 'date-fns', '@radix-ui/react-icons', 'recharts'],
  },
  reactStrictMode: true,
  poweredByHeader: false,
  compress: true,
  generateEtags: true,
  httpAgentOptions: { keepAlive: true },
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },
  output: process.env.STANDALONE === 'true' ? 'standalone' : undefined,
  serverExternalPackages: ['@huggingface/transformers', 'onnxruntime-node', '@duckdb/duckdb-wasm'],
  outputFileTracingExcludes: {
    '*': [
      'node_modules/onnxruntime-node/**/*',
      'node_modules/@huggingface/transformers/**/*',
      'node_modules/@duckdb/duckdb-wasm/**/*',
    ],
  },
  images: {
    formats: ['image/avif', 'image/webp'],
    remotePatterns: [
      { protocol: 'https', hostname: 'images.unsplash.com' },
      { protocol: 'https', hostname: 'picsum.photos' },
      { protocol: 'https', hostname: 'source.unsplash.com' },
      { protocol: 'https', hostname: 'unpkg.com' },
      { protocol: 'https', hostname: 'nominatim.openstreetmap.org' },
      { protocol: 'https', hostname: 'lh3.googleusercontent.com' },
      { protocol: 'https', hostname: 'huggingface.co' },
    ],
  },
  // D6: ESLint now handled via CLI only in Next 16
  // No orphan redirects needed; /emergency and /settings routes now exist.
  async redirects() {
    return [];
  },
  async headers() {
    return [
      {
        source: '/static/(.*)',
        headers: [
          { key: 'Cache-Control', value: 'public, max-age=31536000, immutable' },
        ],
      },
      {
        source: '/icons/(.*)',
        headers: [
          { key: 'Cache-Control', value: 'public, max-age=31536000, immutable' },
        ],
      },
      {
        source: '/offline-data/(.*)',
        headers: [
          { key: 'Cache-Control', value: 'public, max-age=86400, stale-while-revalidate=604800' },
        ],
      },
      {
        source: '/manifest.json',
        headers: [
          { key: 'Cache-Control', value: 'public, max-age=3600' },
        ],
      },
      {
        source: '/sw.js',
        headers: [
          { key: 'Cache-Control', value: 'public, max-age=0, must-revalidate' },
          { key: 'Service-Worker-Allowed', value: '/' },
        ],
      },
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-XSS-Protection',
            value: '0',
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=31536000; includeSubDomains; preload',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(self), geolocation=(self), browsing-topics=()',
          },
          {
            key: 'Cross-Origin-Opener-Policy',
            value: 'same-origin',
          },
          {
            key: 'Cross-Origin-Resource-Policy',
            value: 'same-origin',
          },
          {
            key: 'Cross-Origin-Embedder-Policy',
            value: 'credentialless',
          },
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on',
          },
          {
            key: 'Content-Security-Policy',
            value: "default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline' https://eu.posthog.com https://us.posthog.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; img-src 'self' data: blob: https://images.unsplash.com https://picsum.photos https://source.unsplash.com https://unpkg.com https://nominatim.openstreetmap.org https://lh3.googleusercontent.com https://huggingface.co; font-src 'self' data: https://fonts.gstatic.com; connect-src 'self' wss: https:; worker-src 'self' blob:; frame-src 'self';",
          },
        ],
      },
      {
        source: '/emergency-card/:path*',
        headers: [
          {
            key: 'Referrer-Policy',
            value: 'no-referrer',
          },
          {
            key: 'X-Robots-Tag',
            value: 'noindex, nofollow',
          },
        ],
      },
      {
        source: '/track/:path*',
        headers: [
          {
            key: 'Referrer-Policy',
            value: 'no-referrer',
          },
          {
            key: 'X-Robots-Tag',
            value: 'noindex, nofollow',
          },
        ],
      },
    ];
  },
  webpack: (config, { isServer }) => {
    config.resolve.fallback = { fs: false, path: false };

    if (isServer) {
      config.resolve.alias = {
        ...config.resolve.alias,
        'onnxruntime-node': false,
        '@huggingface/transformers': false,
      };
    }

    // Transformers.js runs models via WebAssembly and offloads to Web Workers.
    // Without this, Next.js blocks both and the offline AI will not load.
    config.experiments = {
      ...config.experiments,
      asyncWebAssembly: true,
      layers: true,
    };

    // Next.js 15 + Webpack 5 handle web workers natively via
    // new Worker(new URL('./worker.js', import.meta.url))
    // No worker-loader needed.

    return config;
  },
};

module.exports = withBundleAnalyzer(nextConfig);
