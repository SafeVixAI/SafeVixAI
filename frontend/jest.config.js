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
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
  },
  testPathIgnorePatterns: [
    '<rootDir>/e2e/',
    '<rootDir>/tests/a11y/',
    '<rootDir>/tests/api-contract.spec.ts',
    '<rootDir>/hooks/__tests__/useSOS.test.ts',
    '<rootDir>/node_modules/',
    '<rootDir>/.next/',
    '<rootDir>/components/__tests__/test-utils.tsx',
    '<rootDir>/components/__tests__/ProvidersPage.test.tsx',
    '<rootDir>/components/chat/__tests__/multimodal-ai-chat-input.test.tsx',
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
    '!app/landing/components/**',
    '!app/landing/hooks/**',
    '!app/landing/components/three/**',
    '!components/maps/index.ts',
    '!app/guide/**/layout.tsx',
    '!app/track/**/layout.tsx',
    '!app/first-aid/FirstAidClient.tsx',
    '!app/emergency-card/**/page.tsx',
  ],
  coverageThreshold: {
    global: {
    branches: 67,
    functions: 76,
    lines: 83,
    statements: 81,
    },
  },
}

module.exports = createJestConfig(customJestConfig)
