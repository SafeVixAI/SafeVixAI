// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
describe('emergency-numbers', function () {
  it('exports EMERGENCY_NUMBER_LIST with 13 entries', async function () {
    const mod = await import('../emergency-numbers')
    expect(mod.EMERGENCY_NUMBER_LIST).toHaveLength(13)
  })

  it('PRIMARY_EMERGENCY_BAR contains 112, 102, 100, 1033', async function () {
    const mod = await import('../emergency-numbers')
    expect(mod.PRIMARY_EMERGENCY_BAR).toHaveLength(4)
    expect(mod.PRIMARY_EMERGENCY_BAR.map(function (e: any) { return e.service })).toEqual(expect.arrayContaining(['112', '102', '100', '1033']))
  })

  it('EMERGENCY_NUMBER_MAP is keyed by id', async function () {
    const mod = await import('../emergency-numbers')
    expect(mod.EMERGENCY_NUMBER_MAP.national_emergency).toBeDefined()
    expect(mod.EMERGENCY_NUMBER_MAP.ambulance.service).toBe('102')
    expect(mod.EMERGENCY_NUMBER_MAP.police.label).toBe('Police')
  })
})
