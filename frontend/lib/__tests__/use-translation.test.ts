// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { useTranslation } from '../use-translation';

describe('useTranslation', function() {
  it('returns a t function and i18n instance', function() {
    const result = useTranslation();
    expect(result).toHaveProperty('t');
    expect(result).toHaveProperty('i18n');
    expect(typeof result.t).toBe('function');
    expect(typeof result.i18n.changeLanguage).toBe('function');
  });

  it('translates a known key', function() {
    const { t } = useTranslation();
    expect(t('nav.home')).toBe('Home');
    expect(t('nav.emergency')).toBe('Emergency');
    expect(t('nav.sos')).toBe('SOS');
  });

  it('returns key when key is unknown and no fallback provided', function() {
    const { t } = useTranslation();
    expect(t('nonexistent_key')).toBe('nonexistent_key');
  });

  it('returns string fallback when key is unknown and fallback is a string', function() {
    const { t } = useTranslation();
    expect(t('nonexistent_key', 'Fallback Text')).toBe('Fallback Text');
  });

  it('returns key when fallback is an object (not a string)', function() {
    const { t } = useTranslation();
    const opts = { defaultValue: 'should not appear' };
    expect(t('nonexistent_key', opts as any)).toBe('nonexistent_key');
  });

  it('translates keys with namespace prefix', function() {
    const { t } = useTranslation();
    expect(t('common.install_title')).toBe('Install SafeVixAI');
    expect(t('common.install_btn')).toBe('Install');
  });

  it('accepts a string namespace parameter', function() {
    const result = useTranslation('common');
    expect(typeof result.t).toBe('function');
    expect(result.i18n.language).toBe('en');
  });

  it('accepts an array of namespaces', function() {
    const { t } = useTranslation(['common', 'nav']);
    expect(typeof t).toBe('function');
  });

  it('i18n has language set to en by default', function() {
    const { i18n } = useTranslation();
    expect(i18n.language).toBe('en');
  });

  it('i18n.changeLanguage resolves successfully', async function() {
    const { i18n } = useTranslation();
    await expect(i18n.changeLanguage('hi')).resolves.toBeUndefined();
  });

  it('i18n.changeLanguage accepts different language codes', async function() {
    const { i18n } = useTranslation();
    await expect(i18n.changeLanguage('ta')).resolves.toBeUndefined();
    await expect(i18n.changeLanguage('te')).resolves.toBeUndefined();
    await expect(i18n.changeLanguage('kn')).resolves.toBeUndefined();
  });

  it('passes options parameter to underlying hook', function() {
    const options = { keyPrefix: 'nav' };
    const result = useTranslation(undefined, options);
    expect(typeof result.t).toBe('function');
    expect(result.i18n.language).toBe('en');
  });

  it('passes namespace and options together', function() {
    const result = useTranslation('common', { keyPrefix: 'install' });
    expect(typeof result.t).toBe('function');
  });
});
