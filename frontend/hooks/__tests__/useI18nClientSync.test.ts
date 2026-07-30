jest.mock('@/lib/i18n', function() {
  return { __esModule: true, default: { language: 'en', changeLanguage: jest.fn(function() { return Promise.resolve() }) } }
})

import { render } from '@testing-library/react'
import React from 'react'

beforeEach(function() {
  window.history.pushState({}, '', '/')
  jest.clearAllMocks()
})

function TestCase({ lang }: { lang?: string }) {
  const hook = require('../useI18nClientSync')
  hook.useI18nClientSync(lang)
  return React.createElement('div')
}

describe('useI18nClientSync', function() {
  it('does nothing when language already matches', function() {
    render(React.createElement(TestCase))
    const i18n = require('@/lib/i18n').default
    expect(i18n.changeLanguage).not.toHaveBeenCalled()
  })

  it('uses path locale when supported', function() {
    window.history.pushState({}, '', '/hi/test')
    render(React.createElement(TestCase, { lang: 'en' }))
    const i18n = require('@/lib/i18n').default
    expect(i18n.changeLanguage).toHaveBeenCalledWith('hi')
  })

  it('uses preferredLanguage when path locale unsupported', function() {
    window.history.pushState({}, '', '/xx/test')
    render(React.createElement(TestCase, { lang: 'ta' }))
    const i18n = require('@/lib/i18n').default
    expect(i18n.changeLanguage).toHaveBeenCalledWith('ta')
  })

  it('sets RTL dir for Arabic', function() {
    window.history.pushState({}, '', '/ar/test')
    render(React.createElement(TestCase, { lang: 'ar' }))
    const i18n = require('@/lib/i18n').default
    expect(i18n.changeLanguage).toHaveBeenCalledWith('ar')
  })

  it('sets RTL dir for Urdu', function() {
    window.history.pushState({}, '', '/ur/test')
    render(React.createElement(TestCase, { lang: 'ur' }))
    const i18n = require('@/lib/i18n').default
    expect(i18n.changeLanguage).toHaveBeenCalledWith('ur')
  })
})
