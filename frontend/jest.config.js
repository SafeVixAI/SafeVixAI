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
  coveragePathIgnorePatterns: [
    'MunicipalityCard\\.tsx$',
    'LocationPicker\\.tsx$',
  ],
  collectCoverageFrom: [
    'components/**/*.{ts,tsx}',
    'lib/**/*.{ts,tsx}',
    'hooks/**/*.{ts,tsx}',
    'app/providers/**/*.{ts,tsx}',
    '!components/**/*.stories.*',
    '!**/*.d.ts',
    '!**/__tests__/**',
    '!**/__mocks__/**',
    '!components/maps/**',
    '!components/chat/multimodal-ai-chat-input.tsx',
    '!hooks/useMapInstance.ts',
    '!lib/duckdb-challan.ts',
    '!lib/offline-ai.ts',
    '!components/EmergencyMap.tsx',
    '!components/LocationPicker.tsx',
    '!components/crash/ProgressRing.tsx',
    '!components/dashboard/DashboardMapBootstrap.tsx',
    '!lib/safe-spaces-layer.ts',
    '!components/EmergencyNumbers.tsx',
    '!components/EnterpriseClientAppHooks.tsx',
    '!components/ReportForm.tsx',
    '!components/ui/KeyboardShortcutsHelp.tsx',
    '!components/dashboard/SystemSidebar.tsx',
    '!lib/intl-formatters.ts',
    '!lib/navigation-launch.ts',
    '!lib/offline-sos-queue.ts',
    '!lib/useWebSocket.ts',
  ],
  coverageThreshold: {
    global: {
    branches: 79,
    functions: 85,
    lines: 94,
    statements: 90,
    },
  },
}

module.exports = createJestConfig(customJestConfig)
