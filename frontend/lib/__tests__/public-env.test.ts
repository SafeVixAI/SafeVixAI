// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import {
  PUBLIC_API_BASE_URL,
  PUBLIC_CHATBOT_BASE_URL,
  publicApiWebSocketUrl,
} from '../public-env';

describe('public-env', function() {
  describe('PUBLIC_API_BASE_URL', function() {
    it('reads from NEXT_PUBLIC_API_URL', function() {
      expect(PUBLIC_API_BASE_URL).toBe('http://localhost:8000');
    });

    it('does not have trailing slash', function() {
      expect(PUBLIC_API_BASE_URL).not.toMatch(/\/$/);
    });
  });

  describe('PUBLIC_CHATBOT_BASE_URL', function() {
    it('reads from NEXT_PUBLIC_CHATBOT_URL', function() {
      expect(PUBLIC_CHATBOT_BASE_URL).toBe('http://localhost:8010');
    });
  });

  describe('publicApiWebSocketUrl', function() {
    it('converts http to ws', function() {
      expect(publicApiWebSocketUrl('/test')).toBe('ws://localhost:8000/test');
    });

    it('handles path without leading slash', function() {
      expect(publicApiWebSocketUrl('chat/stream')).toBe(
        'ws://localhost:8000/chat/stream',
      );
    });

    it('preserves query parameters', function() {
      const url = publicApiWebSocketUrl('/tracking?group=abc');
      expect(url).toBe('ws://localhost:8000/tracking?group=abc');
    });

    it('removes hash fragment', function() {
      const url = publicApiWebSocketUrl('/path#section');
      expect(url).toBe('ws://localhost:8000/path');
    });
  });

  describe('fallback behavior', function() {
    it('uses fallback defaults when env vars are missing', function() {
      const OLD_API = process.env.NEXT_PUBLIC_API_URL;
      const OLD_BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL;
      const OLD_CHAT = process.env.NEXT_PUBLIC_CHATBOT_URL;
      delete process.env.NEXT_PUBLIC_API_URL;
      delete process.env.NEXT_PUBLIC_BACKEND_URL;
      delete process.env.NEXT_PUBLIC_CHATBOT_URL;

      let mod: typeof import('../public-env');
      jest.isolateModules(() => {
        mod = require('../public-env');
      });

      expect(mod!.PUBLIC_API_BASE_URL).toBe('https://safevixai-api.onrender.com');
      expect(mod!.PUBLIC_CHATBOT_BASE_URL).toBe('https://safevixai-chatbot.onrender.com');

      process.env.NEXT_PUBLIC_API_URL = OLD_API;
      process.env.NEXT_PUBLIC_BACKEND_URL = OLD_BACKEND;
      process.env.NEXT_PUBLIC_CHATBOT_URL = OLD_CHAT;
    });

    it('logs warning when env vars missing and not in test mode', function() {
      const OLD_API = process.env.NEXT_PUBLIC_API_URL;
      const OLD_BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL;
      const OLD_CHAT = process.env.NEXT_PUBLIC_CHATBOT_URL;
      const OLD_NODE_ENV = process.env.NODE_ENV;
      delete process.env.NEXT_PUBLIC_API_URL;
      delete process.env.NEXT_PUBLIC_BACKEND_URL;
      delete process.env.NEXT_PUBLIC_CHATBOT_URL;
      process.env.NODE_ENV = 'development';
      const warnSpy = jest.spyOn(console, 'warn').mockImplementation(() => {});
      jest.isolateModules(() => {
        require('../public-env');
      });
      expect(warnSpy).toHaveBeenCalled();
      warnSpy.mockRestore();
      process.env.NEXT_PUBLIC_API_URL = OLD_API;
      process.env.NEXT_PUBLIC_BACKEND_URL = OLD_BACKEND;
      process.env.NEXT_PUBLIC_CHATBOT_URL = OLD_CHAT;
      process.env.NODE_ENV = OLD_NODE_ENV;
    });

    it('does not log warning in test mode when env vars missing', function() {
      const OLD_API = process.env.NEXT_PUBLIC_API_URL;
      const OLD_BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL;
      const OLD_CHAT = process.env.NEXT_PUBLIC_CHATBOT_URL;
      delete process.env.NEXT_PUBLIC_API_URL;
      delete process.env.NEXT_PUBLIC_BACKEND_URL;
      delete process.env.NEXT_PUBLIC_CHATBOT_URL;
      const warnSpy = jest.spyOn(console, 'warn').mockImplementation(() => {});
      jest.isolateModules(() => {
        require('../public-env');
      });
      expect(warnSpy).not.toHaveBeenCalled();
      warnSpy.mockRestore();
      process.env.NEXT_PUBLIC_API_URL = OLD_API;
      process.env.NEXT_PUBLIC_BACKEND_URL = OLD_BACKEND;
      process.env.NEXT_PUBLIC_CHATBOT_URL = OLD_CHAT;
    });
  });
});


