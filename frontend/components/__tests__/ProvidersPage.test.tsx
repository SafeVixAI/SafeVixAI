/**
 * Comprehensive tests for the Providers page component.
 * Covers: render, empty/loading/error states, sync, form interactions,
 * edit/delete, test connection, drag-drop reorder, builtin templates.
 */

jest.mock('@/hooks/usePageEntry', function() {
  return {
    usePageEntry: jest.fn().mockReturnValue({ containerRef: { current: null } }),
  };
});

jest.mock('@/components/ui/TerminalHeader', function() {
  return {
    TerminalHeader: function TerminalHeaderMock() { return null; },
  };
});



var mockApi = {
  fetchBuiltinProviders: jest.fn(),
  fetchProviderConfigs: jest.fn(),
  createProviderConfig: jest.fn(),
  updateProviderConfig: jest.fn(),
  deleteProviderConfig: jest.fn(),
  testProviderConnection: jest.fn(),
  syncProvidersToChatbot: jest.fn(),
};

jest.mock('@/lib/provider-api', function() {
  return mockApi;
});

jest.mock('@/lib/store', function() {
  return {
    useAppStore: jest.fn(function(selector) {
      var state = { isDarkMode: false };
      return selector ? selector(state) : state;
    }),
  };
});

var ACTIVE = [
  { id: '1', providerName: 'groq', displayName: 'My Groq', apiKeyMasked: 'gsk_****', isActive: true, priority: 0, isCustom: false, baseUrl: null, defaultModel: 'llama-3.1-8b-instant' },
];

var WITH_INACTIVE = ACTIVE.concat([
  { id: '2', providerName: 'custom-ollama', displayName: 'Local Ollama', apiKeyMasked: '***', baseUrl: 'http://localhost:11434/v1/chat/completions', defaultModel: 'llama3.2', isActive: true, priority: 1, isCustom: true },
  { id: '3', providerName: 'gemini', displayName: 'My Gemini', apiKeyMasked: 'AI****', isActive: false, priority: 2, isCustom: false, baseUrl: null, defaultModel: 'gemini-2.0-flash' },
]);

var BUILTIN_RESP = [
  { name: 'groq', display: 'Groq', base_url: 'https://api.groq.com/openai/v1', models: ['llama-3.1-8b-instant'] },
  { name: 'openai', display: 'OpenAI', base_url: 'https://api.openai.com/v1', models: ['gpt-4o'] },
];

var React = require('react');
var rtl = require('@testing-library/react');
var screen = rtl.screen;
var waitFor = rtl.waitFor;
var fireEvent = rtl.fireEvent;
var ProvidersPage = require('@/app/providers/page').default;

function setupMocks(opts) {
  mockApi.fetchBuiltinProviders.mockResolvedValue(opts.builtins !== undefined ? opts.builtins : BUILTIN_RESP);
  mockApi.fetchProviderConfigs.mockResolvedValue(opts.configs !== undefined ? opts.configs : WITH_INACTIVE);
  mockApi.createProviderConfig.mockResolvedValue({ id: 'new-1' });
  mockApi.updateProviderConfig.mockResolvedValue({});
  mockApi.deleteProviderConfig.mockResolvedValue(undefined);
  mockApi.testProviderConnection.mockResolvedValue({ status: 'ok', message: 'Connected!' });
  mockApi.syncProvidersToChatbot.mockResolvedValue({ synced: 2, providers: ['groq', 'custom-ollama'] });
}

function renderPage() {
  return rtl.render(React.createElement(ProvidersPage));
}

/** Wait for loading to finish and provider cards to render */
async function waitForLoad() {
  await waitFor(function() {
    expect(screen.getAllByText(/Default endpoint|llama-3.1/).length).toBeGreaterThanOrEqual(1);
  });
}

/** Find the "Sync to Chat" / "Synced" / "Failed" button and click it */
function clickSyncBtn() {
  var buttons = screen.getAllByRole('button');
  var btn = buttons.find(function(b) {
    return b.textContent.includes('Sync') || b.textContent === 'Synced' || b.textContent === 'Failed';
  });
  if (btn) fireEvent.click(btn);
  return btn;
}

describe('ProvidersPage', function() {
  beforeEach(function() {
    jest.clearAllMocks();
  });

  // ═══════════════ Basic Render ═══════════════

  describe('basic render', function() {
    it('should show provider count', async function() {
      setupMocks({});
      renderPage();
      await waitFor(function() {
        expect(screen.getByText(/providers configured/)).toBeTruthy();
      });
    });

    it('should show builtin provider grid', async function() {
      setupMocks({});
      renderPage();
      await waitFor(function() {
        expect(screen.getByText('Groq')).toBeTruthy();
        expect(screen.getByText('OpenAI')).toBeTruthy();
      });
    });

    it('should show user provider configs', async function() {
      setupMocks({});
      renderPage();
      await waitFor(function() {
        expect(screen.getAllByText('My Groq').length).toBeGreaterThanOrEqual(1);
        expect(screen.getAllByText('Local Ollama').length).toBeGreaterThanOrEqual(1);
      });
    });

    it('should show fallback chain with multiple active providers', async function() {
      setupMocks({});
      renderPage();
      await waitFor(function() {
        expect(screen.getByText('Fallback Chain')).toBeTruthy();
        expect(screen.getByText('Primary')).toBeTruthy();
        expect(screen.getByText('Template (Fallback)')).toBeTruthy();
      });
    });

    it('should show add and quick add buttons', async function() {
      setupMocks({});
      renderPage();
      await waitFor(function() {
        expect(screen.getByText('Add Custom Provider')).toBeTruthy();
        expect(screen.getByText('Quick Add (Ollama/LocalAI)')).toBeTruthy();
      });
    });

    it('should show disabled badge for inactive providers', async function() {
      setupMocks({});
      renderPage();
      await waitFor(function() {
        expect(screen.getByText('Disabled')).toBeTruthy();
      });
    });

    it('should show masked API key', async function() {
      setupMocks({});
      renderPage();
      await waitFor(function() {
        expect(screen.getByText('gsk_****')).toBeTruthy();
      });
    });

    it('should show custom badge for custom providers', async function() {
      setupMocks({});
      renderPage();
      await waitFor(function() {
        var customLabels = screen.getAllByText('Custom');
        expect(customLabels.length).toBeGreaterThanOrEqual(1);
      });
    });

    it('should show provider name badge', async function() {
      setupMocks({});
      renderPage();
      await waitFor(function() {
        expect(screen.getAllByText('groq').length).toBeGreaterThanOrEqual(1);
      });
    });
  });

  // ═══════════════ Empty State ═══════════════

  describe('empty state', function() {
    it('should show empty message when no providers', async function() {
      setupMocks({ configs: [] });
      renderPage();
      await waitFor(function() {
        expect(screen.getByText('No providers configured')).toBeTruthy();
      });
    });

    it('should show subtitle in empty state', async function() {
      setupMocks({ configs: [] });
      renderPage();
      await waitFor(function() {
        expect(screen.getByText('Add your API keys below to enable AI providers')).toBeTruthy();
      });
    });
  });

  // ═══════════════ Error State ═══════════════

  describe('error state', function() {
    it('should gracefully degrade to empty state when individual fetches fail', async function() {
      setupMocks({ configs: [] });
      mockApi.fetchBuiltinProviders.mockImplementation(function() { return Promise.reject(new Error('Net err')); });
      mockApi.fetchProviderConfigs.mockImplementation(function() { return Promise.reject(new Error('Net err')); });
      renderPage();
      // Each fetch has .catch(() => []) so Promise.all resolves with [[], []]
      await waitFor(function() {
        expect(screen.getByText('No providers configured')).toBeTruthy();
      });
    });
  });

  // ═══════════════ Loading State ═══════════════

  describe('loading state', function() {
    it('should show spinner before data loads', async function() {
      mockApi.fetchProviderConfigs.mockReturnValue(new Promise(function() {}));
      mockApi.fetchBuiltinProviders.mockReturnValue(new Promise(function() {}));
      renderPage();
      await waitFor(function() {
        expect(document.querySelector('.lucide-refresh-cw.animate-spin')).toBeTruthy();
      });
    });
  });

  // ═══════════════ Sync Button ═══════════════

  describe('sync button', function() {
    it('should show Synced status after sync completes', async function() {
      setupMocks({});
      renderPage();
      await waitForLoad();
      clickSyncBtn();
      await waitFor(function() {
        expect(screen.getByText('Synced')).toBeTruthy();
      });
    });

    it('should show Failed status when sync errors', async function() {
      setupMocks({});
      mockApi.syncProvidersToChatbot.mockRejectedValue(new Error('Sync failed'));
      renderPage();
      await waitForLoad();
      clickSyncBtn();
      await waitFor(function() {
        expect(screen.getByText('Failed')).toBeTruthy();
      });
    });

    it('should call syncProvidersToChatbot on click', async function() {
      setupMocks({});
      renderPage();
      await waitForLoad();
      clickSyncBtn();
      await waitFor(function() {
        expect(mockApi.syncProvidersToChatbot).toHaveBeenCalledTimes(1);
      });
    });

    it('should show Syncing... with spinner while syncing', async function() {
      setupMocks({});
      mockApi.syncProvidersToChatbot.mockReturnValue(new Promise(function() {}));
      renderPage();
      await waitForLoad();
      clickSyncBtn();
      await waitFor(function() {
        expect(screen.getByText('Syncing...')).toBeTruthy();
      });
      var refreshIcon = document.querySelector('.lucide-refresh-cw');
      expect(refreshIcon.classList.contains('animate-spin')).toBe(true);
    });

    it('should disable sync button while syncing', async function() {
      setupMocks({});
      mockApi.syncProvidersToChatbot.mockReturnValue(new Promise(function() {}));
      renderPage();
      await waitForLoad();
      // Find the sync button (contains Sync text)
      var syncBtn = screen.getAllByRole('button').find(function(b) { return b.textContent.includes('Sync'); });
      expect(syncBtn).toBeTruthy();
      expect(syncBtn.hasAttribute('disabled')).toBe(false);
      fireEvent.click(syncBtn);
      await waitFor(function() {
        expect(syncBtn.hasAttribute('disabled')).toBe(true);
      });
    });
  });

  // ═══════════════ Add Form ═══════════════

  describe('add provider form', function() {
    it('should open add form when Add Custom Provider is clicked', async function() {
      setupMocks({});
      renderPage();
      await waitForLoad();
      fireEvent.click(screen.getByText('Add Custom Provider'));
      expect(await screen.findByText('Cancel')).toBeTruthy();
      expect((await screen.findAllByText('Add Provider')).length).toBeGreaterThanOrEqual(1);
    });

    it('should show form field labels', async function() {
      setupMocks({});
      renderPage();
      await waitForLoad();
      fireEvent.click(screen.getByText('Add Custom Provider'));
      expect(await screen.findByText('Provider Name')).toBeTruthy();
      expect(await screen.findByText('Display Name')).toBeTruthy();
      expect(await screen.findByText('API Key')).toBeTruthy();
      expect(await screen.findByText('Base URL')).toBeTruthy();
    });

    it('should open form on Quick Add click', async function() {
      setupMocks({});
      renderPage();
      await waitForLoad();
      fireEvent.click(screen.getByText('Quick Add (Ollama/LocalAI)'));
      expect(await screen.findByText('Cancel')).toBeTruthy();
    });

    it('should hide add buttons when form is open', async function() {
      setupMocks({});
      renderPage();
      await waitForLoad();
      fireEvent.click(screen.getByText('Add Custom Provider'));
      await waitFor(function() {
        expect(screen.queryByText('Add Custom Provider')).toBeNull();
      });
    });

    it('should cancel form on Cancel click', async function() {
      setupMocks({});
      renderPage();
      await waitForLoad();
      fireEvent.click(screen.getByText('Add Custom Provider'));
      expect(await screen.findByText('Cancel')).toBeTruthy();
      fireEvent.click(screen.getByText('Cancel'));
      await waitFor(function() {
        expect(screen.queryByText('Test Connection')).toBeNull();
      });
      expect(await screen.findByText('Add Custom Provider')).toBeTruthy();
    });

    it('should call createProviderConfig on save', async function() {
      setupMocks({});
      renderPage();
      await waitForLoad();
      fireEvent.click(screen.getByText('Add Custom Provider'));
      expect(await screen.findByDisplayValue(/^custom-/)).toBeTruthy();
      // Fill required fields
      var nameInput = screen.getByDisplayValue(/^custom-/);
      fireEvent.change(nameInput, { target: { value: 'my-provider' } });
      var displayInput = screen.getByPlaceholderText('My Groq Key');
      fireEvent.change(displayInput, { target: { value: 'My Provider' } });
      // "Add Provider" appears in both h3 title and save button — use getAllByText to click the button
      var saveBtns = screen.getAllByText('Add Provider');
      fireEvent.click(saveBtns[1]);
      await waitFor(function() {
        expect(mockApi.createProviderConfig).toHaveBeenCalled();
      });
    });

    it('should disable save button when provider name is empty', async function() {
      setupMocks({});
      renderPage();
      await waitForLoad();
      // Quick Add fills providerName and displayName
      fireEvent.click(screen.getByText('Quick Add (Ollama/LocalAI)'));
      expect(await screen.findByText('Cancel')).toBeTruthy();
      var saveBtns = screen.getAllByText('Add Provider');
      // Initially both fields filled — save not disabled
      expect(saveBtns[1].hasAttribute('disabled')).toBe(false);
      // Clear provider name
      var nameInput = screen.getByDisplayValue(/^custom-/);
      fireEvent.change(nameInput, { target: { value: '' } });
      await waitFor(function() {
        expect(saveBtns[1].hasAttribute('disabled')).toBe(true);
      });
    });
  });

  // ═══════════════ Edit Flow ═══════════════

  describe('edit provider', function() {
    it('should open form with existing values when edit clicked', async function() {
      // userConfigs key below is OVERRIDDEN by setupMocks's `opts.configs` mapping.
      // The actual data used is the default WITH_INACTIVE (3 providers).
      // My Groq is the first provider's displayName.
      setupMocks({ configs: [{ id: 'cfg-1', providerName: 'groq', displayName: 'My Groq', apiKey: 'enc-test', baseUrl: 'https://api.groq.com/openai/v1', defaultModel: 'llama-3.1-8b-instant', isActive: true, isCustom: false, priority: 1 }] });
      renderPage();
      await waitForLoad();
      // Find the edit button inside the provider card.
      var card = screen.getByText('My Groq').closest('.sv-card');
      var editBtn = card.querySelector('button');
      fireEvent.click(editBtn);
      await waitFor(function() {
        expect(screen.getByText('Edit Provider')).toBeTruthy();
      });
    });
  });

  // ═══════════════ Test Connection ═══════════════

  describe('test connection', function() {
    async function openFormAndFillKey() {
      renderPage();
      await waitForLoad();
      fireEvent.click(screen.getByText('Add Custom Provider'));
      await waitFor(function() {
        expect(screen.getByPlaceholderText('sk-...')).toBeTruthy();
      });
      fireEvent.change(screen.getByPlaceholderText('sk-...'), { target: { value: 'sk-test-key' } });
    }

    async function openForm() {
      renderPage();
      await waitForLoad();
      fireEvent.click(screen.getByText('Add Custom Provider'));
      await waitFor(function() {
        expect(screen.getByText('Cancel')).toBeTruthy();
      });
    }

    it('should disable test button when API key is empty', async function() {
      setupMocks({});
      await openForm();
      // API key input starts empty
      var testBtn = screen.getByText('Test Connection');
      expect(testBtn.hasAttribute('disabled')).toBe(true);
    });

    it('should show success message', async function() {
      setupMocks({});
      mockApi.testProviderConnection.mockResolvedValue({ status: 'ok', message: 'Connected!' });
      await openFormAndFillKey();
      expect(await screen.findByText('Test Connection')).toBeTruthy();
      fireEvent.click(screen.getByText('Test Connection'));
      await waitFor(function() {
        expect(screen.getByText('Connected!')).toBeTruthy();
      });
    });

    it('should show error message', async function() {
      setupMocks({});
      mockApi.testProviderConnection.mockResolvedValue({ status: 'error', message: 'Invalid API key' });
      await openFormAndFillKey();
      fireEvent.click(screen.getByText('Test Connection'));
      await waitFor(function() {
        expect(screen.getByText('Invalid API key')).toBeTruthy();
      });
    });
  });

  // ═══════════════ Delete ═══════════════

  describe('delete provider', function() {
    it('should call deleteProviderConfig when confirmed', async function() {
      window.confirm = jest.fn().mockReturnValue(true);
      setupMocks({ configs: ACTIVE });
      renderPage();
      await waitForLoad();
      var trash = document.querySelector('.lucide-trash-2');
      expect(trash).toBeTruthy();
      fireEvent.click(trash!.parentElement!);
      expect(mockApi.deleteProviderConfig).toHaveBeenCalledWith('1');
    });

    it('should NOT call deleteProviderConfig when cancelled', async function() {
      window.confirm = jest.fn().mockReturnValue(false);
      setupMocks({ configs: ACTIVE });
      renderPage();
      await waitForLoad();
      var trash = document.querySelector('.lucide-trash-2');
      fireEvent.click(trash);
      // Should not have called the API
      expect(mockApi.deleteProviderConfig).not.toHaveBeenCalled();
    });
  });

  // ═══════════════ Drag-Drop Fallback Chain ═══════════════

  describe('fallback chain drag-drop', function() {
    function makeDataTransfer(data) {
      return {
        getData: function(k) { return data[k] || ''; },
        setData: function(k, v) { data[k] = v; },
      };
    }

    it('should call updateProviderConfig on drop to reorder', async function() {
      setupMocks({ configs: ACTIVE.concat([
        { id: '2', providerName: 'custom-ollama', displayName: 'Local Ollama', apiKeyMasked: '***', baseUrl: 'http://localhost:11434/v1/chat/completions', defaultModel: 'llama3.2', isActive: true, priority: 1, isCustom: true },
      ]) });
      renderPage();
      await waitFor(function() {
        expect(screen.getByText('Fallback Chain')).toBeTruthy();
      });
      var items = document.querySelectorAll('[draggable="true"]');
      expect(items.length).toBe(2);
      // Drag item 1 onto item 2
      var dt = makeDataTransfer({});
      fireEvent.dragStart(items[0], { dataTransfer: dt });
      dt.setData('text/plain', '1');
      var dt2 = makeDataTransfer({ 'text/plain': '1' });
      fireEvent.drop(items[1], { dataTransfer: dt2, preventDefault: function() {} });
      await waitFor(function() {
        expect(mockApi.updateProviderConfig).toHaveBeenCalled();
      });
    });

    it('should be no-op when dragging invalid ID', async function() {
      setupMocks({ configs: ACTIVE.concat([
        { id: '2', providerName: 'custom-ollama', displayName: 'Local Ollama', apiKeyMasked: '***', baseUrl: 'http://localhost:11434/v1/chat/completions', defaultModel: 'llama3.2', isActive: true, priority: 1, isCustom: true },
      ]) });
      renderPage();
      await waitFor(function() {
        expect(screen.getByText('Fallback Chain')).toBeTruthy();
      });
      var items = document.querySelectorAll('[draggable="true"]');
      // Drag with non-existent ID
      var dt = { getData: function() { return 'nonexistent-id'; }, setData: function() {} };
      fireEvent.drop(items[0], { dataTransfer: dt, preventDefault: function() {} });
      expect(mockApi.updateProviderConfig).not.toHaveBeenCalled();
    });

    it('should be no-op when dropped on same item', async function() {
      setupMocks({ configs: ACTIVE.concat([
        { id: '2', providerName: 'custom-ollama', displayName: 'Local Ollama', apiKeyMasked: '***', baseUrl: 'http://localhost:11434/v1/chat/completions', defaultModel: 'llama3.2', isActive: true, priority: 1, isCustom: true },
      ]) });
      renderPage();
      await waitFor(function() {
        expect(screen.getByText('Fallback Chain')).toBeTruthy();
      });
      var items = document.querySelectorAll('[draggable="true"]');
      var dt = makeDataTransfer({});
      fireEvent.dragStart(items[0], { dataTransfer: dt });
      dt.setData('text/plain', '1');
      fireEvent.drop(items[0], {
        dataTransfer: makeDataTransfer({ 'text/plain': '1' }),
        preventDefault: function() {},
      });
      expect(mockApi.updateProviderConfig).not.toHaveBeenCalled();
    });
  });

  // ═══════════════ Builtin Templates Toggle ═══════════════

  describe('builtin templates toggle', function() {
    it('should collapse grid on click', async function() {
      setupMocks({});
      renderPage();
      await waitFor(function() {
        expect(screen.getByText('Groq')).toBeTruthy();
      });
      fireEvent.click(screen.getByText('Provider Templates'));
      await waitFor(function() {
        expect(screen.queryByText('Groq')).toBeNull();
      });
    });

    it('should show grid by default', async function() {
      setupMocks({});
      renderPage();
      await waitFor(function() {
        expect(screen.getByText('Groq')).toBeTruthy();
        expect(screen.getByText('OpenAI')).toBeTruthy();
      });
    });

    it('should open add form when a builtin template is clicked', async function() {
      setupMocks({ configs: [] });
      renderPage();
      await waitFor(function() {
        expect(screen.getByText('OpenAI')).toBeTruthy();
      });
      fireEvent.click(screen.getByText('OpenAI'));
      await waitFor(function() {
        // "Add Provider" appears in both h3 title and save button — check for at least one
        expect(screen.getAllByText('Add Provider').length).toBeGreaterThanOrEqual(1);
      });
    });
  });
});
