// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
describe('gsap', function () {
  it('exports gsap and ScrollTrigger', async function () {
    const mod = await import('../gsap')
    expect(mod.gsap).toBeDefined()
    expect(mod.ScrollTrigger).toBeDefined()
  })

  it('registers plugins and sets defaults in browser', async function () {
    jest.resetModules()
    const registerSpy = jest.spyOn(require('gsap').gsap, 'registerPlugin').mockImplementation(function () {})
    const defaultsSpy = jest.spyOn(require('gsap').gsap, 'defaults').mockImplementation(function () {})
    await import('../gsap')
    expect(registerSpy).toHaveBeenCalled()
    expect(defaultsSpy).toHaveBeenCalled()
    registerSpy.mockRestore()
    defaultsSpy.mockRestore()
  })
})
