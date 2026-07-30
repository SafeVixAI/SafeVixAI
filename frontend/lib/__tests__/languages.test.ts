// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
describe('languages', function () {
  it('exports SUPPORTED_LANGUAGES with 14 entries', async function () {
    const mod = await import('../languages')
    expect(mod.SUPPORTED_LANGUAGES).toHaveLength(14)
  })

  it('getLanguageByCode returns correct language', async function () {
    const mod = await import('../languages')
    const tamil = mod.getLanguageByCode('ta')
    expect(tamil).toBeDefined()
    expect(tamil!.name).toBe('Tamil')
    expect(tamil!.nativeName).toBe('தமிழ்')
    expect(tamil!.recognitionCode).toBe('ta-IN')
  })

  it('getLanguageByCode returns undefined for unknown', async function () {
    const mod = await import('../languages')
    expect(mod.getLanguageByCode('xx')).toBeUndefined()
  })

  it('each language has standard codes', async function () {
    const mod = await import('../languages')
    mod.SUPPORTED_LANGUAGES.forEach(function (l: any) {
      expect(l.code).toBeDefined()
      expect(l.recognitionCode).toBeDefined()
      expect(l.speechTargetCode).toBeDefined()
      expect(l.synthesisCode).toBeDefined()
    })
  })
})
