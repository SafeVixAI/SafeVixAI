/**
 * Tests for the provider API client module.
 */

var BUILTIN_RESP = [
  { name: 'groq', display: 'Groq', base_url: 'https://api.groq.com/openai/v1/chat/completions', models: ['llama-3.1-8b-instant'] },
  { name: 'openai', display: 'OpenAI', base_url: 'https://api.openai.com/v1/chat/completions', models: ['gpt-4o'] },
  { name: 'gemini', display: 'Gemini', base_url: 'https://generativelanguage.googleapis.com/v1beta/models', models: ['gemini-2.0-flash'] },
];

var CONFIG_RESP = [
  { id: '1', providerName: 'groq', displayName: 'My Groq', apiKeyMasked: 'gsk_****', isActive: true, priority: 0, isCustom: false },
  { id: '2', providerName: 'custom-ollama', displayName: 'Local Ollama', apiKeyMasked: '***', baseUrl: 'http://localhost:11434/v1/chat/completions', defaultModel: 'llama3.2', isActive: true, priority: 1, isCustom: true },
];

jest.mock('@/lib/public-env', function() {
  return {
    PUBLIC_API_BASE_URL: 'http://test.local',
  };
});

var providerApi = require('@/lib/provider-api');

describe('provider-api', function() {
  var originalFetch;

  beforeAll(function() {
    originalFetch = global.fetch;
  });

  afterAll(function() {
    global.fetch = originalFetch;
  });

  afterEach(function() {
    jest.restoreAllMocks();
  });

  describe('fetchBuiltinProviders', function() {
    it('should return list of builtin providers', async function() {
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: function() { return Promise.resolve(BUILTIN_RESP); },
      });
      var result = await providerApi.fetchBuiltinProviders();
      expect(result).toHaveLength(3);
      expect(result[0].name).toBe('groq');
      expect(fetch).toHaveBeenCalledWith('http://test.local/api/v1/providers/builtins');
    });

    it('should throw on HTTP error', async function() {
      global.fetch = jest.fn().mockResolvedValue({
        ok: false,
        status: 500,
        text: function() { return Promise.resolve('Server error'); },
      });
      await expect(providerApi.fetchBuiltinProviders()).rejects.toThrow('HTTP 500');
    });
  });

  describe('fetchProviderConfigs', function() {
    it('should return list of user provider configs', async function() {
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: function() { return Promise.resolve(CONFIG_RESP); },
      });
      var result = await providerApi.fetchProviderConfigs();
      expect(result).toHaveLength(2);
      expect(result[0].providerName).toBe('groq');
    });
  });

  describe('createProviderConfig', function() {
    it('should POST provider config and return created record', async function() {
      var newConfig = {
        providerName: 'test-groq',
        displayName: 'Test Groq',
        apiKey: 'sk-test',
        isActive: true,
        priority: 0,
        isCustom: false,
      };
      var expected = { id: '3', ...newConfig, apiKeyMasked: 'sk-****', apiKey: undefined };
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        status: 201,
        json: function() { return Promise.resolve(expected); },
      });
      var result = await providerApi.createProviderConfig(newConfig);
      expect(result.displayName).toBe('Test Groq');
      expect(fetch).toHaveBeenCalledWith(
        'http://test.local/api/v1/providers',
        expect.objectContaining({ method: 'POST' }),
      );
    });

    it('should POST provider config without API key', async function() {
      var newConfig = {
        providerName: 'test-groq',
        displayName: 'Test Groq',
        apiKey: '',
        isActive: true,
        priority: 0,
        isCustom: false,
      };
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        status: 201,
        json: function() { return Promise.resolve({ id: '4', ...newConfig, apiKeyMasked: '' }); },
      });
      var result = await providerApi.createProviderConfig(newConfig);
      var callBody = JSON.parse((fetch as any).mock.calls[0][1].body);
      expect(callBody.api_key).toBeUndefined()
      expect(result.providerName).toBe('test-groq');
    });
  });

  describe('updateProviderConfig', function() {
    it('should PUT provider config', async function() {
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: function() { return Promise.resolve({ id: '1', displayName: 'Updated' }); },
      });
      var result = await providerApi.updateProviderConfig('1', { displayName: 'Updated' });
      expect(result.displayName).toBe('Updated');
      expect(fetch).toHaveBeenCalledWith(
        'http://test.local/api/v1/providers/1',
        expect.objectContaining({
          method: 'PUT',
          body: expect.stringContaining('Updated'),
        }),
      );
    });

    it('should toggle isActive to false', async function() {  // A1
      jest.spyOn(globalThis, 'fetch').mockResolvedValue({
        ok: true,
        status: 200,
        json: function() { return Promise.resolve({ id: '1', isActive: false, provider_name: 'groq', display_name: 'Groq' }); },
      } as any);
      var result = await providerApi.updateProviderConfig('1', { isActive: false });
      expect(result).toBeTruthy();
      expect(result.isActive).toBe(false);
    });
  });

  describe('deleteProviderConfig', function() {
    it('should DELETE provider config', async function() {
      global.fetch = jest.fn().mockResolvedValue({ ok: true, status: 204 });
      await providerApi.deleteProviderConfig('1');
      expect(fetch).toHaveBeenCalledWith(
        'http://test.local/api/v1/providers/1',
        expect.objectContaining({ method: 'DELETE' }),
      );
    });

    it('should throw on delete error', async function() {
      global.fetch = jest.fn().mockResolvedValue({
        ok: false,
        status: 404,
        text: function() { return Promise.resolve('Not found'); },
      });
      await expect(providerApi.deleteProviderConfig('99')).rejects.toThrow('HTTP 404');
    });
  });

  describe('testProviderConnection', function() {
    it('should POST test connection and return result', async function() {
      var testResult = { status: 'ok', message: 'Connected', provider: 'groq', model: 'test' };
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: function() { return Promise.resolve(testResult); },
      });
      var result = await providerApi.testProviderConnection({
        providerName: 'groq',
        apiKey: 'sk-test',
        model: 'test',
      });
      expect(result.status).toBe('ok');
    });

    it('should work with empty model and baseUrl fields', async function() {  // A2
      var testResult = { status: 'ok', message: 'Connected' };
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: function() { return Promise.resolve(testResult); },
      });
      var result = await providerApi.testProviderConnection({
        providerName: 'groq',
        apiKey: 'sk-test',
        model: '',
        baseUrl: '',
      });
      expect(result.status).toBe('ok');
    });
  });

  describe('syncProvidersToChatbot', function() {
    it('should POST sync and return result', async function() {
      var syncResult = { synced: 3, providers: ['groq', 'openai'] };
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: function() { return Promise.resolve(syncResult); },
      });
      var result = await providerApi.syncProvidersToChatbot();
      expect(result.synced).toBe(3);
      expect(result.providers).toContain('groq');
    });

    it('should throw on sync error', async function() {
      global.fetch = jest.fn().mockResolvedValue({
        ok: false,
        status: 500,
        text: function() { return Promise.resolve('Sync failed'); },
      });
      await expect(providerApi.syncProvidersToChatbot()).rejects.toThrow('HTTP 500');
    });
  });
});
