// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { searchLocalLawIndex } from '../offline-rag';

describe('offline-rag — searchLocalLawIndex', function() {
  beforeEach(function() {
    jest.useFakeTimers();
  });

  afterEach(function() {
    jest.useRealTimers();
  });

  it('should match laws by tag keyword', async function() {
    const promise = searchLocalLawIndex('helmet');
    jest.advanceTimersByTime(600);
    const results = await promise;
    expect(results).toHaveLength(1);
    expect(results[0].id).toBe('sec-194d');
  });

  it('should match laws by tag keyword among multiple words', async function() {
    const promise = searchLocalLawIndex('pothole danger');
    jest.advanceTimersByTime(600);
    const results = await promise;
    expect(results).toHaveLength(1);
    expect(results[0].id).toBe('sec-188');
  });

  it('should match laws by text content', async function() {
    const promise = searchLocalLawIndex('immediate medical attention');
    jest.advanceTimersByTime(600);
    const results = await promise;
    expect(results).toHaveLength(1);
    expect(results[0].id).toBe('sec-134');
  });

  it('should be case-insensitive', async function() {
    const promise = searchLocalLawIndex('HELMET');
    jest.advanceTimersByTime(600);
    const results = await promise;
    expect(results).toHaveLength(1);
    expect(results[0].id).toBe('sec-194d');
  });

  it('should return empty array for no match', async function() {
    const promise = searchLocalLawIndex('zzzznotfound');
    jest.advanceTimersByTime(600);
    const results = await promise;
    expect(results).toHaveLength(0);
  });

  it('should return all laws for empty query (text match on empty string)', async function() {
    const promise = searchLocalLawIndex('');
    jest.advanceTimersByTime(600);
    const results = await promise;
    expect(results).toHaveLength(3);
  });

  it('should return laws matching text even without tag match', async function() {
    const promise = searchLocalLawIndex('fine');
    jest.advanceTimersByTime(600);
    const results = await promise;
    expect(results).toHaveLength(1);
    expect(results[0].id).toBe('sec-194d');
  });

  it('should return multiple matches when query covers multiple docs', async function() {
    const promise = searchLocalLawIndex('neglect');
    jest.advanceTimersByTime(600);
    const results = await promise;
    expect(results).toHaveLength(1);
    expect(results[0].id).toBe('sec-188');
  });

  it('should return LawDoc objects with the correct shape', async function() {
    const promise = searchLocalLawIndex('helmet');
    jest.advanceTimersByTime(600);
    const results = await promise;
    expect(results.length).toBeGreaterThan(0);
    const doc = results[0];
    expect(doc).toHaveProperty('id');
    expect(doc).toHaveProperty('source');
    expect(doc).toHaveProperty('text');
    expect(typeof doc.id).toBe('string');
    expect(typeof doc.source).toBe('string');
    expect(typeof doc.text).toBe('string');
  });
});
