// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import {
  EMAIL_RULE,
  PASSWORD_RULE,
  NAME_RULE,
  LOGIN_RULES,
  SIGNUP_RULES,
  RESET_RULES,
} from '../validation-schemas';
import { ValidationRule } from '../use-form-validation';

describe('EMAIL_RULE', function() {
  it('should have correct key, label, and required fields', function() {
    expect(EMAIL_RULE.key).toBe('email');
    expect(EMAIL_RULE.label).toBe('Email');
    expect(EMAIL_RULE.required).toBe(true);
  });

  it('should accept valid email addresses', function() {
    const valid = ['user@example.com', 'a@b.co', 'test.user@domain.org', 'name+tag@company.in', '123@xyz.ai'];
    valid.forEach(function(email) {
      expect(EMAIL_RULE.pattern!.test(email)).toBe(true);
    });
  });

  it('should reject invalid email addresses', function() {
    const invalid = ['', '   ', 'notanemail', '@nodomain', 'nouser@', 'space in@test.com', 'a@b', 'a@.com'];
    invalid.forEach(function(email) {
      expect(EMAIL_RULE.pattern!.test(email)).toBe(false);
    });
  });

  it('should have correct patternMessage', function() {
    expect(EMAIL_RULE.patternMessage).toBe('Invalid email address');
  });
});

describe('PASSWORD_RULE', function() {
  it('should have correct key, label, and required fields', function() {
    expect(PASSWORD_RULE.key).toBe('password');
    expect(PASSWORD_RULE.label).toBe('Password');
    expect(PASSWORD_RULE.required).toBe(true);
    expect(PASSWORD_RULE.minLength).toBe(8);
  });

  it('should have minLength of 8', function() {
    expect(PASSWORD_RULE.minLength).toBe(8);
  });

  it('should have correct patternMessage', function() {
    expect(PASSWORD_RULE.patternMessage).toBe('Minimum 8 characters');
  });
});

describe('NAME_RULE', function() {
  it('should have correct key, label, required, and minLength', function() {
    expect(NAME_RULE.key).toBe('name');
    expect(NAME_RULE.label).toBe('Full Name');
    expect(NAME_RULE.required).toBe(true);
    expect(NAME_RULE.minLength).toBe(2);
  });
});

describe('LOGIN_RULES', function() {
  it('should be an array with 2 rules', function() {
    expect(Array.isArray(LOGIN_RULES)).toBe(true);
    expect(LOGIN_RULES.length).toBe(2);
  });

  it('should include EMAIL_RULE as first rule', function() {
    expect(LOGIN_RULES[0]).toBe(EMAIL_RULE);
  });

  it('should include PASSWORD_RULE with minLength 1 as second rule', function() {
    expect(LOGIN_RULES[1].key).toBe('password');
    expect(LOGIN_RULES[1].label).toBe('Password');
    expect(LOGIN_RULES[1].required).toBe(true);
    expect(LOGIN_RULES[1].minLength).toBe(1);
  });

  it('should not mutate the original PASSWORD_RULE', function() {
    expect(PASSWORD_RULE.minLength).toBe(8);
  });
});

describe('SIGNUP_RULES', function() {
  const password = 'securePass123';
  let rules: ValidationRule[];

  beforeEach(function() {
    rules = SIGNUP_RULES(password);
  });

  it('should return an array with 4 rules', function() {
    expect(Array.isArray(rules)).toBe(true);
    expect(rules.length).toBe(4);
  });

  it('should include NAME_RULE as first rule', function() {
    expect(rules[0]).toBe(NAME_RULE);
  });

  it('should include EMAIL_RULE as second rule', function() {
    expect(rules[1]).toBe(EMAIL_RULE);
  });

  it('should include PASSWORD_RULE as third rule', function() {
    expect(rules[2]).toBe(PASSWORD_RULE);
  });

  it('should have confirmPassword as fourth rule', function() {
    expect(rules[3].key).toBe('confirmPassword');
    expect(rules[3].label).toBe('Confirm Password');
    expect(rules[3].required).toBe(true);
  });

  it('should have validate function on confirmPassword', function() {
    expect(typeof rules[3].validate).toBe('function');
  });

  it('confirmPassword validate should return null when passwords match', function() {
    const err = rules[3].validate!(password);
    expect(err).toBeNull();
  });

  it('confirmPassword validate should return error when passwords do not match', function() {
    const err = rules[3].validate!('differentPassword');
    expect(err).toBe('Passwords do not match');
  });

  it('confirmPassword validate should return error when confirm is empty', function() {
    const err = rules[3].validate!('');
    expect(err).toBe('Passwords do not match');
  });

  it('should return separate instances per call', function() {
    const rules2 = SIGNUP_RULES('otherPass');
    expect(rules2[3].validate!('securePass123')).toBe('Passwords do not match');
    expect(rules2[3].validate!('otherPass')).toBeNull();
  });

  it('should handle empty password parameter', function() {
    const emptyRules = SIGNUP_RULES('');
    expect(emptyRules[3].validate!('')).toBeNull();
    expect(emptyRules[3].validate!('x')).toBe('Passwords do not match');
  });

  it('should handle special characters in password', function() {
    const specialRules = SIGNUP_RULES('p@$$w0rd!');
    expect(specialRules[3].validate!('p@$$w0rd!')).toBeNull();
    expect(specialRules[3].validate!('p@$$w0rd')).toBe('Passwords do not match');
  });
});

describe('RESET_RULES', function() {
  it('should be an array with 1 rule', function() {
    expect(Array.isArray(RESET_RULES)).toBe(true);
    expect(RESET_RULES.length).toBe(1);
  });

  it('should include EMAIL_RULE', function() {
    expect(RESET_RULES[0]).toBe(EMAIL_RULE);
  });
});

describe('SIGNUP_RULES with empty string edge cases', function() {
  it('confirmPassword validate should handle null-ish matching', function() {
    const rules = SIGNUP_RULES('');
    expect(rules[3].validate!('')).toBeNull();
  });

  it('confirmPassword validate should handle whitespace', function() {
    const rules = SIGNUP_RULES('  ');
    expect(rules[3].validate!('  ')).toBeNull();
    expect(rules[3].validate!('')).toBe('Passwords do not match');
  });
});

describe('Rule immutability', function() {
  it('should not mutate original constants when spreading in LOGIN_RULES', function() {
    expect(PASSWORD_RULE.minLength).toBe(8);
  });
});
