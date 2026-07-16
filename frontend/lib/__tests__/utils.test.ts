// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { cn } from '../utils'

describe('cn', function() {
  it('merges class names', function() {
    expect(cn('px-4', 'py-2')).toBe('px-4 py-2')
  })

  it('handles conditional classes', function() {
    expect(cn('base', false && 'hidden', 'visible')).toBe('base visible')
  })

  it('resolves Tailwind conflicts (later wins)', function() {
    expect(cn('px-2', 'px-4')).toBe('px-4')
  })

  it('handles undefined inputs', function() {
    expect(cn('a', undefined, 'b')).toBe('a b')
  })

  it('handles null inputs', function() {
    expect(cn('a', null, 'b')).toBe('a b')
  })

  it('handles empty inputs', function() {
    expect(cn()).toBe('')
  })

  it('merges object syntax', function() {
    expect(cn({ foo: true, bar: false })).toBe('foo')
  })
})
