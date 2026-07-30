// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
describe('user-profile', function () {
  describe('isProfileComplete', function () {
    it('returns false for null profile', async function () {
      const mod = await import('../user-profile')
      expect(mod.isProfileComplete(null)).toBe(false)
    })

    it('returns false for incomplete profile', async function () {
      const mod = await import('../user-profile')
      expect(mod.isProfileComplete({ name: '', bloodGroup: '', vehicleNumber: '' } as any)).toBe(false)
    })

    it('returns true for complete profile', async function () {
      const mod = await import('../user-profile')
      expect(mod.isProfileComplete({ name: 'John', bloodGroup: 'O+', vehicleNumber: 'TN01AB1234' } as any)).toBe(true)
    })
  })

  describe('getProfileStatus', function () {
    it('returns Critical for null', async function () {
      const mod = await import('../user-profile')
      expect(mod.getProfileStatus(null)).toBe('Critical')
    })

    it('returns Warning when missing name or blood', async function () {
      const mod = await import('../user-profile')
      expect(mod.getProfileStatus({ name: '', bloodGroup: 'O+', vehicleNumber: 'TN01' } as any)).toBe('Warning')
    })

    it('returns Safe when complete', async function () {
      const mod = await import('../user-profile')
      expect(mod.getProfileStatus({ name: 'John', bloodGroup: 'O+', vehicleNumber: 'TN01' } as any)).toBe('Safe')
    })
  })

  describe('getFirstName', function () {
    it('returns Sentinel for undefined', async function () {
      const mod = await import('../user-profile')
      expect(mod.getFirstName()).toBe('Sentinel')
    })

    it('returns first name', async function () {
      const mod = await import('../user-profile')
      expect(mod.getFirstName('John Doe')).toBe('John')
    })

    it('handles single name', async function () {
      const mod = await import('../user-profile')
      expect(mod.getFirstName('John')).toBe('John')
    })
  })
})
