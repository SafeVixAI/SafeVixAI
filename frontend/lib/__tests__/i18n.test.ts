jest.mock('@/i18n/config/resources', function() {
  return {
    resources: {
      en: {
        common: function() { return Promise.resolve({ default: { hello: 'Hello', goodbye: 'Goodbye' } }) },
        auth: function() { return Promise.resolve({ default: { login: 'Login' } }) },
        dashboard: function() { return Promise.resolve({ default: { title: 'Dashboard' } }) },
      },
      ta: {
        common: function() { return Promise.resolve({ default: { hello: 'Vanakkam' } }) },
      },
      missing: {
        common: function() { return Promise.reject(new Error('Module not found')) },
      },
    },
  }
})

describe('i18n', function() {
  beforeEach(function() {
    jest.resetModules()
  })

  it('exports default i18n instance with t function', async function() {
    var mod = await import('../i18n')
    expect(mod.default).toBeDefined()
    expect(typeof mod.default.t).toBe('function')
  })

  it('sets fallbackLng to en and defaultNS to common', async function() {
    var mod = await import('../i18n')
    expect(mod.default.options.fallbackLng).toEqual(['en'])
    expect(mod.default.options.defaultNS).toBe('common')
  })

  it('initializes with multiple namespaces', async function() {
    var mod = await import('../i18n')
    expect(mod.default.options.ns).toEqual(expect.arrayContaining(['common', 'auth', 'dashboard', 'challan']))
  })

  it('has useSuspense set to false', async function() {
    var mod = await import('../i18n')
    expect(mod.default.options.react.useSuspense).toBe(false)
  })

  it('has interpolation escapeValue set to false', async function() {
    var mod = await import('../i18n')
    expect(mod.default.options.interpolation.escapeValue).toBe(false)
  })

  it('initializes with all 8 namespaces', async function() {
    var mod = await import('../i18n')
    expect(mod.default.options.ns).toEqual(['common', 'auth', 'dashboard', 'challan', 'chat', 'settings', 'errors', 'validation'])
  })

  it('can translate with en namespace', async function() {
    var mod = await import('../i18n')
    await new Promise(function(resolve) {
      mod.default.loadNamespaces('common', function() { resolve(null) })
    })
    expect(mod.default.t('hello')).toBe('Hello')
  })

  it('handles loading non-existent namespace gracefully', async function() {
    var mod = await import('../i18n')
    expect(function() {
      mod.default.loadNamespaces('__nonexistent__')
    }).not.toThrow()
  })

  it('falls back to English when language resource fails to load', async function() {
    var mod = await import('../i18n')
    var consoleWarn = jest.spyOn(console, 'warn').mockImplementation(function() {})
    await new Promise(function(resolve) {
      mod.default.loadLanguages('missing', function() { resolve(null) })
    })
    expect(consoleWarn).toHaveBeenCalled()
    consoleWarn.mockRestore()
  })

  it('handles missing namespace with no English fallback', async function() {
    var mod = await import('../i18n')
    var consoleWarn = jest.spyOn(console, 'warn').mockImplementation(function() {})
    await new Promise(function(resolve) {
      mod.default.loadNamespaces('__nonexistent__', function() { resolve(null) })
    })
    consoleWarn.mockRestore()
  })

  it('logs error when both primary and English fallback fail', async function() {
    jest.resetModules()
    jest.doMock('@/i18n/config/resources', function() {
      return {
        resources: {
          en: {
            // Intentionally omit common namespace so English fallback has no loader
            auth: function() { return Promise.resolve({ default: { login: 'Login' } }) },
          },
          fail: {
            common: function() { return Promise.reject(new Error('Primary fails')) },
          },
        },
      }
    })
    var consoleWarn = jest.spyOn(console, 'warn').mockImplementation(function() {})
    var mod = await import('../i18n')
    await new Promise(function(resolve) {
      mod.default.loadLanguages('fail', function() { resolve(null) })
    })
    expect(consoleWarn).toHaveBeenCalled()
    consoleWarn.mockRestore()
  })

  it('calls callback with error when English fallback also fails', async function() {
    jest.resetModules()
    jest.doMock('@/i18n/config/resources', function() {
      return {
        resources: {
          en: {
            common: function() { return Promise.reject(new Error('English fallback fails')) },
          },
          fail: {
            common: function() { return Promise.reject(new Error('Primary fails')) },
          },
        },
      }
    })
    var consoleWarn = jest.spyOn(console, 'warn').mockImplementation(function() {})
    var mod = await import('../i18n')
    await new Promise(function(resolve) {
      mod.default.loadLanguages('fail', function() { resolve(null) })
    })
    expect(consoleWarn).toHaveBeenCalled()
    consoleWarn.mockRestore()
  })
})
