jest.mock('@huggingface/transformers', function() {
  return { pipeline: tfPipeline, env: {} }
});
jest.mock('../client-logger', function() { return { logClientError: jest.fn(), logClientWarning: jest.fn() } });
jest.mock('../features', function() { return { FEATURES: { webllmOffline: true } } });

var tfPipeline = jest.fn().mockRejectedValue(new Error('mock no tf'));

describe('offline-ai', function() {
  let mod: typeof import('../offline-ai');
  let logClientError: jest.Mock;
  let logClientWarning: jest.Mock;
  let FEATURES: { webllmOffline: boolean };

  beforeEach(async function() {
    jest.clearAllMocks();
    jest.resetModules();
    delete (window as any).ai;
    delete (navigator as any).deviceMemory;
    logClientError = require('../client-logger').logClientError;
    logClientWarning = require('../client-logger').logClientWarning;
    FEATURES = require('../features').FEATURES;
    mod = await import('../offline-ai');
  });

  describe('getOfflineAIStatus', function() {
    it('returns idle initially', function() {
      expect(mod.getOfflineAIStatus()).toBe('idle');
    });
  });

  describe('isOfflineAIReady', function() {
    it('returns false initially', function() {
      expect(mod.isOfflineAIReady()).toBe(false);
    });
  });

  describe('getOfflineAI', function() {
    it('returns fallback when no AI and transformers fails', async function() {
      const result = await mod.getOfflineAI();
      expect(result.type).toBe('fallback');
    });

    it('falls through to transformers when Chrome AI not readily available', async function() {
      (window as any).ai = {
        languageModel: {
          capabilities: jest.fn().mockResolvedValue({ available: 'after-download' }),
        },
      };
      const result = await mod.getOfflineAI();
      expect(result.type).toBe('fallback');
    });

    it('calls onProgress callback during flow', async function() {
      const onProgress = jest.fn();
      await mod.getOfflineAI(onProgress);
      expect(onProgress).toHaveBeenCalledWith(expect.objectContaining({ status: 'checking_system' }));
    });

    it('returns system when Chrome built-in AI available', async function() {
      const mockSession = { prompt: jest.fn().mockResolvedValue('hi') };
      (window as any).ai = {
        languageModel: {
          capabilities: jest.fn().mockResolvedValue({ available: 'readily' }),
          create: jest.fn().mockResolvedValue(mockSession),
        },
      };
      const result = await mod.getOfflineAI();
      expect(result.type).toBe('system');
    });

    it('early returns system on second call when Chrome AI ready', async function() {
      const mockSession = { prompt: jest.fn().mockResolvedValue('hi') };
      (window as any).ai = {
        languageModel: {
          capabilities: jest.fn().mockResolvedValue({ available: 'readily' }),
          create: jest.fn().mockResolvedValue(mockSession),
        },
      };
      await mod.getOfflineAI();
      const result = await mod.getOfflineAI();
      expect(result.type).toBe('system');
    });

    it('returns ready immediately on second call', async function() {
      await mod.getOfflineAI();
      const result = await mod.getOfflineAI();
      expect(result.type).toBe('fallback');
    });

    it('returns fallback when webllmOffline feature disabled', async function() {
      FEATURES.webllmOffline = false;
      const result = await mod.getOfflineAI();
      expect(result.type).toBe('fallback');
    });

    it('logs client error when transformers load fails', async function() {
      await mod.getOfflineAI();
      expect(logClientError).toHaveBeenCalled();
    });

    it('returns fallback on low memory device (< 4GB)', async function() {
      Object.defineProperty(navigator, 'deviceMemory', { value: 3.5, configurable: true });
      const result = await mod.getOfflineAI();
      expect(result.type).toBe('fallback');
    });

    it('early returns transformers on second call when ready', async function() {
      tfPipeline.mockResolvedValue(async function() {
        return [{ generated_text: 'ok' }];
      });
      await mod.getOfflineAI();
      const result = await mod.getOfflineAI();
      expect(result.type).toBe('transformers');
    });

    it('returns transformers when pipeline loads successfully', async function() {
      tfPipeline.mockResolvedValue(async function() {
        return [{ generated_text: 'test' }];
      });
      const onProgress = jest.fn();
      const result = await mod.getOfflineAI(onProgress);
      expect(result.type).toBe('transformers');
      expect(onProgress).toHaveBeenCalledWith(expect.objectContaining({ status: 'ready', percent: 100 }));
    });

    it('fires progress_callback during transformers download', async function() {
      tfPipeline.mockImplementation(async function(task: string, model: string, options: { progress_callback?: Function }) {
        options.progress_callback?.({ progress: 0.5, loaded: 5000000, total: 10000000 });
        options.progress_callback?.({ progress: 1.0, loaded: 10000000, total: 10000000 });
        return async function() {
          return [{ generated_text: 'ok' }];
        };
      });
      const onProgress = jest.fn();
      await mod.getOfflineAI(onProgress);
      expect(onProgress).toHaveBeenCalledWith(expect.objectContaining({ status: 'downloading', percent: 50 }));
      expect(onProgress).toHaveBeenCalledWith(expect.objectContaining({ status: 'downloading', percent: 100 }));
    });

    it('fires progress_callback with percent-only when total not provided', async function() {
      tfPipeline.mockImplementation(async function(task: string, model: string, options: { progress_callback?: Function }) {
        options.progress_callback?.({ progress: 0.3, loaded: 0, total: 0 });
        return async function() {
          return [{ generated_text: 'ok' }];
        };
      });
      const onProgress = jest.fn();
      await mod.getOfflineAI(onProgress);
      expect(onProgress).toHaveBeenCalledWith(expect.objectContaining({ status: 'downloading', percent: 30 }));
    });
  });

  describe('askOfflineAI', function() {
    it('returns keyword fallback for hospital', async function() {
      const response = await mod.askOfflineAI('What is the hospital number?');
      expect(response).toContain('Locator');
    });

    it('returns default message for unrecognized prompt', async function() {
      const response = await mod.askOfflineAI('the meaning of life');
      expect(response).toContain('offline mode');
    });

    it('uses Chrome AI session when available', async function() {
      const mockSession = { prompt: jest.fn().mockResolvedValue('Chrome AI response') };
      (window as any).ai = {
        languageModel: {
          capabilities: jest.fn().mockResolvedValue({ available: 'readily' }),
          create: jest.fn().mockResolvedValue(mockSession),
        },
      };
      await mod.getOfflineAI();
      const response = await mod.askOfflineAI('hello');
      expect(response).toBe('Chrome AI response');
    });

    it('falls back to keyword when session.prompt throws', async function() {
      const mockSession = { prompt: jest.fn().mockRejectedValue(new Error('AI error')) };
      (window as any).ai = {
        languageModel: {
          capabilities: jest.fn().mockResolvedValue({ available: 'readily' }),
          create: jest.fn().mockResolvedValue(mockSession),
        },
      };
      await mod.getOfflineAI();
      const response = await mod.askOfflineAI('hospital');
      expect(response).toContain('Locator');
      expect(logClientWarning).toHaveBeenCalled();
    });

    it('uses Transformers.js pipeline when loaded', async function() {
      tfPipeline.mockResolvedValue(async function() {
        return [{ generated_text: 'Gemma 4 response text' }];
      });
      await mod.getOfflineAI();
      const response = await mod.askOfflineAI('Tell me about road safety');
      expect(response).toBe('Gemma 4 response text');
    });

    it('handles audioBlob input via pipeline', async function() {
      tfPipeline.mockResolvedValue(async function(_messages: Array<{ role: string; content: unknown }>) {
        return [{ generated_text: 'audio processed' }];
      });
      await mod.getOfflineAI();
      const audioBlob = new Blob(['fake-audio'], { type: 'audio/webm' });
      const response = await mod.askOfflineAI('What is this sound?', audioBlob);
      expect(response).toBe('audio processed');
    });

    it('returns fallback string when pipeline returns null output', async function() {
      tfPipeline.mockResolvedValue(async function() {
        return [{ generated_text: null }];
      });
      await mod.getOfflineAI();
      const response = await mod.askOfflineAI('test');
      expect(response).toBe('No response generated.');
    });

    it('handles array output from pipeline', async function() {
      tfPipeline.mockResolvedValue(async function() {
        return [{ generated_text: [{ content: 'extracted content' }] }];
      });
      await mod.getOfflineAI();
      const response = await mod.askOfflineAI('test');
      expect(response).toBe('extracted content');
    });

    it('falls back to keyword when pipeline throws', async function() {
      tfPipeline.mockResolvedValue(async function() {
        throw new Error('pipeline error');
      });
      await mod.getOfflineAI();
      const response = await mod.askOfflineAI('police number');
      expect(response).toContain('100');
      expect(logClientWarning).toHaveBeenCalled();
    });

    it('matches prompt case-insensitively for accident', async function() {
      const response = await mod.askOfflineAI('ACCIDENT on highway');
      expect(response).toContain('Section 134');
    });

    it('returns fire response for fire keyword', async function() {
      const response = await mod.askOfflineAI('fire near my car');
      expect(response).toContain('101');
    });

    it('keyword matching for ambulance', async function() {
      const response = await mod.askOfflineAI('need an ambulance');
      expect(response).toContain('102');
    });

    it('keyword matching for police', async function() {
      const response = await mod.askOfflineAI('call police');
      expect(response).toContain('100');
    });

    it('keyword matching for pothole', async function() {
      const response = await mod.askOfflineAI('report pothole');
      expect(response).toContain('RoadWatch');
    });

    it('keyword matching for challan', async function() {
      const response = await mod.askOfflineAI('what is the challan for speeding');
      expect(response).toContain('Challan Calculator');
    });

    it('keyword matching for helmet', async function() {
      const response = await mod.askOfflineAI('helmet fine');
      expect(response).toContain('₹1,000');
    });

    it('keyword matching for seatbelt', async function() {
      const response = await mod.askOfflineAI('seatbelt rule');
      expect(response).toContain('₹1,000');
    });

    it('keyword matching for drunk driving', async function() {
      const response = await mod.askOfflineAI('drunk driving penalty');
      expect(response).toContain('₹10,000');
    });

    it('keyword matching for speed', async function() {
      const response = await mod.askOfflineAI('speeding fine');
      expect(response).toContain('₹1,000');
    });
  });
});
