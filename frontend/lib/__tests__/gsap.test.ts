// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
describe('gsap', function () {
  it('exports gsap and ScrollTrigger', async function () {
    var mod = await import('../gsap')
    expect(mod.gsap).toBeDefined()
    expect(mod.ScrollTrigger).toBeDefined()
  })

  it('registers plugins and sets defaults in browser', async function () {
    jest.resetModules()
    var registerSpy = jest.spyOn(require('gsap').gsap, 'registerPlugin').mockImplementation(function () {})
    var defaultsSpy = jest.spyOn(require('gsap').gsap, 'defaults').mockImplementation(function () {})
    await import('../gsap')
    expect(registerSpy).toHaveBeenCalled()
    expect(defaultsSpy).toHaveBeenCalled()
    registerSpy.mockRestore()
    defaultsSpy.mockRestore()
  })
})
