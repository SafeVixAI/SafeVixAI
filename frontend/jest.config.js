// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
const nextJest = require('next/jest')

const createJestConfig = nextJest({
  dir: './',
})

const customJestConfig = {
  setupFiles: ['<rootDir>/jest.env.js'],
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testEnvironment: 'jest-environment-jsdom',
  ...(process.env.CI === 'true' ? {
    maxWorkers: '50%',
    workerIdleMemoryLimit: '512MB',
  } : {}),
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
  },
  testPathIgnorePatterns: [
    '<rootDir>/e2e/',
    '<rootDir>/tests/a11y/',
    '<rootDir>/tests/api-contract.spec.ts',
    '<rootDir>/node_modules/',
    '<rootDir>/.next/',
    '<rootDir>/components/__tests__/test-utils.tsx',

  ],
  modulePathIgnorePatterns: ['<rootDir>/.next/'],
  coveragePathIgnorePatterns: [],
  collectCoverageFrom: [
    'components/**/*.{ts,tsx}',
    'lib/**/*.{ts,tsx}',
    'hooks/**/*.{ts,tsx}',
    'app/**/*.{ts,tsx}',
    '!components/**/*.stories.*',
    '!**/*.d.ts',
    '!**/__tests__/**',
    '!**/__mocks__/**',
    '!app/layout.tsx',
    '!app/global-error.tsx',
    '!**/route.ts',
    '!app/landing/hooks/**',
    '!app/landing/components/three/**',
    '!lib/api/update-api.ts',
    '!lib/sw/update-sw.ts',
    '!components/maps/index.ts',
    '!app/guide/**/layout.tsx',
    '!app/track/**/layout.tsx',
    '!app/emergency-card/**/page.tsx',
  ],
  coverageThreshold: {
    global: {
    branches: 69,
    functions: 75,
    lines: 82,
    statements: 80,
    },
  },
}

module.exports = createJestConfig(customJestConfig)
