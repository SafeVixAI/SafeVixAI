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
  ],
  coverageThreshold: {
    global: {
    branches: 66,
    functions: 74,
    lines: 80,
    statements: 79,
    },
  },
}

module.exports = createJestConfig(customJestConfig)
