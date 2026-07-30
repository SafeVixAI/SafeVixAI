// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import { renderHook, act } from '@testing-library/react'

describe('useFormValidation', function () {
  const rules = [
    { key: 'name', label: 'Name', required: true, minLength: 2, maxLength: 50 },
    { key: 'email', label: 'Email', required: true, pattern: /^[^@]+@[^@]+\.[^@]+$/, patternMessage: 'Invalid email' },
    { key: 'phone', label: 'Phone', validate: function (v: string) { return v.length === 10 ? null : 'Must be 10 digits' } },
  ]

  it('returns initial state', async function () {
    const mod = await import('../use-form-validation')
    const { result } = renderHook(function () { return mod.useFormValidation(rules) })
    expect(result.current.errors).toEqual({})
    expect(result.current.submitting).toBe(false)
  })

  it('validates field - required', async function () {
    const mod = await import('../use-form-validation')
    const { result } = renderHook(function () { return mod.useFormValidation(rules) })
    const err = result.current.validateField('name', '')
    expect(err).toBe('Name is required')
  })

  it('validates field - minLength', async function () {
    const mod = await import('../use-form-validation')
    const { result } = renderHook(function () { return mod.useFormValidation(rules) })
    const err = result.current.validateField('name', 'A')
    expect(err).toBe('Name must be at least 2 characters')
  })

  it('validates field - maxLength', async function () {
    const mod = await import('../use-form-validation')
    const { result } = renderHook(function () { return mod.useFormValidation(rules) })
    const err = result.current.validateField('name', 'A'.repeat(51))
    expect(err).toBe('Name must be at most 50 characters')
  })

  it('validates field - pattern', async function () {
    const mod = await import('../use-form-validation')
    const { result } = renderHook(function () { return mod.useFormValidation(rules) })
    const err = result.current.validateField('email', 'invalid')
    expect(err).toBe('Invalid email')
  })

  it('validates field - custom validate', async function () {
    const mod = await import('../use-form-validation')
    const { result } = renderHook(function () { return mod.useFormValidation(rules) })
    const err = result.current.validateField('phone', '123')
    expect(err).toBe('Must be 10 digits')
  })

  it('validates field - valid value returns null', async function () {
    const mod = await import('../use-form-validation')
    const { result } = renderHook(function () { return mod.useFormValidation(rules) })
    const err = result.current.validateField('name', 'John')
    expect(err).toBeNull()
  })

  it('returns null for unknown rule', async function () {
    const mod = await import('../use-form-validation')
    const { result } = renderHook(function () { return mod.useFormValidation(rules) })
    const err = result.current.validateField('unknown', 'test')
    expect(err).toBeNull()
  })

  it('validateAll returns true when all valid', async function () {
    const mod = await import('../use-form-validation')
    const { result } = renderHook(function () { return mod.useFormValidation(rules) })
    const valid = result.current.validateAll({ name: 'John', email: 'john@test.com', phone: '1234567890' })
    expect(valid).toBe(true)
  })

  it('validateAll returns false with errors', async function () {
    const mod = await import('../use-form-validation')
    const { result } = renderHook(function () { return mod.useFormValidation(rules) })
    const valid = result.current.validateAll({ name: '', email: '', phone: '' })
    expect(valid).toBe(false)
  })

  it('handleBlur validates and touches field', async function () {
    const mod = await import('../use-form-validation')
    const { result } = renderHook(function () { return mod.useFormValidation(rules) })
    act(function () { result.current.handleBlur('name', '') })
    expect(result.current.touched.has('name')).toBe(true)
    expect(result.current.errors.name).toBe('Name is required')
  })

  it('handleChange only validates if touched', async function () {
    const mod = await import('../use-form-validation')
    const { result } = renderHook(function () { return mod.useFormValidation(rules) })
    act(function () { result.current.handleChange('name', '') })
    expect(result.current.errors.name).toBeUndefined()
  })

  it('handleSubmit returns false on validation failure', async function () {
    const mod = await import('../use-form-validation')
    const { result } = renderHook(function () { return mod.useFormValidation(rules) })
    const success = await result.current.handleSubmit({ name: '', email: '', phone: '' }, async function () {})
    expect(success).toBe(false)
  })

  it('handleSubmit runs submitFn on valid data', async function () {
    const mod = await import('../use-form-validation')
    const { result } = renderHook(function () { return mod.useFormValidation(rules) })
    const submitFn = jest.fn().mockResolvedValue(undefined)
    const success = await result.current.handleSubmit({ name: 'John', email: 'j@t.com', phone: '1234567890' }, submitFn)
    expect(success).toBe(true)
    expect(submitFn).toHaveBeenCalled()
  })

  it('handleSubmit prevents duplicate submission', async function () {
    const mod = await import('../use-form-validation')
    const { result } = renderHook(function () { return mod.useFormValidation(rules) })
    const submitFn = jest.fn().mockImplementation(function () { return new Promise(function (r) { setTimeout(r, 100) }) })
    const p1 = result.current.handleSubmit({ name: 'John', email: 'j@t.com', phone: '1234567890' }, submitFn)
    const p2 = result.current.handleSubmit({ name: 'John', email: 'j@t.com', phone: '1234567890' }, submitFn)
    await Promise.all([p1, p2])
    expect(submitFn).toHaveBeenCalledTimes(1)
  })

  it('reset clears all state', async function () {
    const mod = await import('../use-form-validation')
    const { result } = renderHook(function () { return mod.useFormValidation(rules) })
    act(function () { result.current.handleBlur('name', '') })
    act(function () { result.current.reset() })
    expect(result.current.errors).toEqual({})
    expect(result.current.touched.size).toBe(0)
    expect(result.current.submitting).toBe(false)
  })
})
