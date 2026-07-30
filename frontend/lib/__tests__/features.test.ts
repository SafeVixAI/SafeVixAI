// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
describe('features', function () {
  it('exports FEATURES with expected keys', async function () {
    const mod = await import('../features')
    expect(mod.FEATURES).toHaveProperty('webllmOffline')
    expect(mod.FEATURES).toHaveProperty('crashDetection')
    expect(mod.FEATURES).toHaveProperty('familyTracking')
  })
})
