'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  Plus, Trash2, Check, X, RefreshCw, Wifi,
  Server, Key, Globe, Sliders, ChevronDown, ChevronUp,
  ExternalLink, AlertTriangle, Zap, Cpu, GripVertical, ArrowDown, ArrowUp,
} from 'lucide-react';
import { usePageEntry } from '@/hooks/usePageEntry';
import { TerminalHeader } from '@/components/ui/TerminalHeader';
import { SurfaceCard } from '@/components/ui/SurfaceCard';
import { useAppStore } from '@/lib/store';
import { useShallow } from 'zustand/react/shallow';
import type {
  ProviderConfig, BuiltinProvider,
} from '@/lib/provider-api';
import {
  fetchBuiltinProviders, fetchProviderConfigs,
  createProviderConfig, updateProviderConfig, deleteProviderConfig,
  testProviderConnection, syncProvidersToChatbot,
} from '@/lib/provider-api';

interface ProviderFormData {
  providerName: string;
  displayName: string;
  apiKey: string;
  baseUrl: string;
  defaultModel: string;
  isActive: boolean;
  priority: number;
  isCustom: boolean;
}

const INITIAL_FORM: ProviderFormData = {
  providerName: '', displayName: '', apiKey: '',
  baseUrl: '', defaultModel: '', isActive: true,
  priority: 0, isCustom: false,
};

type TestStatus = 'idle' | 'testing' | 'ok' | 'error';

export default function ProvidersPage() {
  const pageRef = usePageEntry();
  const { selectedProvider, setSelectedProvider } = useAppStore(
    useShallow((s) => ({
      selectedProvider: s.selectedProvider,
      setSelectedProvider: s.setSelectedProvider,
    }))
  );

  const [builtins, setBuiltins] = useState<BuiltinProvider[]>([]);
  const [userConfigs, setUserConfigs] = useState<ProviderConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState<ProviderFormData>(INITIAL_FORM);
  const [testStatus, setTestStatus] = useState<TestStatus>('idle');
  const [testMessage, setTestMessage] = useState('');
  const [syncStatus, setSyncStatus] = useState<'idle' | 'syncing' | 'ok' | 'error'>('idle');
  const [expandedProvider, setExpandedProvider] = useState<string | null>(null);
  const [showBuiltins, setShowBuiltins] = useState(true);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [b, c] = await Promise.all([
        fetchBuiltinProviders().catch(() => []),
        fetchProviderConfigs().catch(() => []),
      ]);
      setBuiltins(b);
      setUserConfigs(c);
    } catch (e) {
      setError('Failed to load providers. Check your connection.');
    }
    setLoading(false);
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const resetForm = () => {
    setFormData(INITIAL_FORM);
    setEditingId(null);
    setShowAddForm(false);
    setTestStatus('idle');
    setTestMessage('');
  };

  const handleSelectBuiltin = (b: BuiltinProvider) => {
    const existing = userConfigs.find((c) => c.providerName === b.name);
    if (existing) {
      setFormData({
        providerName: b.name,
        displayName: existing.displayName || b.display,
        apiKey: '',
        baseUrl: existing.baseUrl || b.base_url,
        defaultModel: existing.defaultModel || (b.models[0] || ''),
        isActive: existing.isActive,
        priority: existing.priority,
        isCustom: false,
      });
      setEditingId(existing.id!);
    } else {
      setFormData({
        providerName: b.name,
        displayName: b.display,
        apiKey: '',
        baseUrl: b.base_url,
        defaultModel: b.models[0] || '',
        isActive: true,
        priority: userConfigs.length,
        isCustom: false,
      });
      setEditingId(null);
    }
    setShowAddForm(true);
    setTestStatus('idle');
    setTestMessage('');
  };

  const handleAddCustom = () => {
    setFormData({
      providerName: 'custom-' + Date.now(),
      displayName: 'Custom Provider',
      apiKey: '',
      baseUrl: 'http://localhost:11434/v1/chat/completions',
      defaultModel: 'llama3.2',
      isActive: true,
      priority: userConfigs.length,
      isCustom: true,
    });
    setEditingId(null);
    setShowAddForm(true);
    setTestStatus('idle');
    setTestMessage('');
  };

  const handleTest = async () => {
    setTestStatus('testing');
    setTestMessage('');
    const result = await testProviderConnection({
      providerName: formData.providerName,
      apiKey: formData.apiKey,
      baseUrl: formData.baseUrl,
      model: formData.defaultModel,
    });
    setTestStatus(result.status === 'ok' ? 'ok' : 'error');
    setTestMessage(result.message);
  };

  const handleSave = async () => {
    if (!formData.providerName || !formData.displayName) return;
    try {
      if (editingId) {
        await updateProviderConfig(editingId, {
          displayName: formData.displayName,
          apiKey: formData.apiKey || undefined,
          baseUrl: formData.baseUrl || undefined,
          defaultModel: formData.defaultModel || undefined,
          isActive: formData.isActive,
          priority: formData.priority,
        });
      } else {
        await createProviderConfig(formData);
      }
      resetForm();
      await loadData();
    } catch (e: any) {
      setError(e.message);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this provider configuration?')) return;
    try {
      await deleteProviderConfig(id);
      await loadData();
    } catch (e: any) {
      setError(e.message);
    }
  };

  const handleSync = async () => {
    setSyncStatus('syncing');
    try {
      const result = await syncProvidersToChatbot();
      setSyncStatus('ok');
      setTimeout(() => setSyncStatus('idle'), 3000);
    } catch {
      setSyncStatus('error');
      setTimeout(() => setSyncStatus('idle'), 3000);
    }
  };

  return (
    <div ref={pageRef} className="sv-page relative flex flex-col transition-colors duration-500">
      <TerminalHeader title="AI Providers" subtitle="Configure your LLM API keys and custom endpoints" />

      <main className="sv-page-main max-w-4xl space-y-8 relative z-10">
        {/* Error banner */}
        {error && (
          <div className="flex items-center gap-3 p-4 rounded-card bg-red-500/10 border border-red-500/20">
            <AlertTriangle size={16} className="text-red-500 shrink-0" />
            <p className="text-xs font-medium text-red-500">{error}</p>
            <button onClick={() => setError(null)} className="ml-auto"><X size={14} /></button>
          </div>
        )}

        {/* Sync bar */}
        <div className="flex items-center justify-between">
          <p className="sv-micro text-text-3">
            {userConfigs.length} provider{userConfigs.length !== 1 ? 's' : ''} configured
          </p>
          <div className="flex gap-2">
            <button
              onClick={handleSync}
              disabled={syncStatus === 'syncing'}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand/10 border border-brand/20 text-[10px] font-semibold text-brand-light uppercase tracking-widest hover:bg-brand/20 transition-all disabled:opacity-50"
            >
              <RefreshCw size={12} className={syncStatus === 'syncing' ? 'animate-spin' : ''} />
              {syncStatus === 'syncing' ? 'Syncing...' : syncStatus === 'ok' ? 'Synced' : syncStatus === 'error' ? 'Failed' : 'Sync to Chat'}
            </button>
            <button
              onClick={loadData}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-3 border border-border text-[10px] font-semibold text-text-3 uppercase tracking-widest hover:bg-surface-2 transition-all"
            >
              <RefreshCw size={12} /> Refresh
            </button>
          </div>
        </div>

        {/* User-configured providers */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <RefreshCw size={20} className="animate-spin text-text-3" />
          </div>
        ) : (
          <>
            {/* Configured providers list */}
            {userConfigs.length === 0 && (
              <SurfaceCard padding="lg">
                <div className="text-center py-8">
                  <Cpu size={32} className="mx-auto mb-3 text-text-3" />
                  <p className="text-sm font-semibold text-text-2 mb-1">No providers configured</p>
                  <p className="text-[10px] text-text-3 mb-4">Add your API keys below to enable AI providers</p>
                </div>
              </SurfaceCard>
            )}

            <div className="flex flex-col gap-3">
              {userConfigs.map((cfg) => (
                <SurfaceCard key={cfg.id} padding="md">
                  <div className="flex items-center gap-4">
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${cfg.isActive ? 'bg-brand/10' : 'bg-surface-3'}`}>
                      {cfg.isCustom ? <Server size={18} className={cfg.isActive ? 'text-brand-light' : 'text-text-3'} /> : <Globe size={18} className={cfg.isActive ? 'text-brand-light' : 'text-text-3'} />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-semibold text-text-1 truncate">{cfg.displayName}</p>
                        <span className={`px-1.5 py-0.5 rounded text-[8px] font-bold uppercase tracking-wider ${cfg.isCustom ? 'bg-purple-500/10 text-purple-400' : 'bg-brand/10 text-brand-light'}`}>
                          {cfg.isCustom ? 'Custom' : cfg.providerName}
                        </span>
                        {!cfg.isActive && <span className="text-[8px] font-bold text-text-3 uppercase">Disabled</span>}
                      </div>
                      <p className="text-[10px] font-mono text-text-3 truncate mt-0.5">
                        {cfg.baseUrl || 'Default endpoint'}
                        {cfg.defaultModel ? ` → ${cfg.defaultModel}` : ''}
                      </p>
                      {cfg.apiKeyMasked && <p className="text-[9px] font-mono text-text-3 mt-0.5">{cfg.apiKeyMasked}</p>}
                    </div>
                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={() => {
                          setFormData({
                            providerName: cfg.providerName,
                            displayName: cfg.displayName,
                            apiKey: '',
                            baseUrl: cfg.baseUrl || '',
                            defaultModel: cfg.defaultModel || '',
                            isActive: cfg.isActive,
                            priority: cfg.priority,
                            isCustom: cfg.isCustom,
                          });
                          setEditingId(cfg.id!);
                          setShowAddForm(true);
                          setTestStatus('idle');
                          setTestMessage('');
                        }}
                        className="p-2 rounded-lg hover:bg-surface-3 transition-all text-text-3 hover:text-text-1"
                      >
                        <Sliders size={14} />
                      </button>
                      <button
                        onClick={() => handleDelete(cfg.id!)}
                        className="p-2 rounded-lg hover:bg-red-500/10 transition-all text-text-3 hover:text-red-500"
                      >
                        <Trash2 size={14} />
                      </button>
                      <button
                        onClick={() => setExpandedProvider(expandedProvider === cfg.id ? null : cfg.id!)}
                        className="p-2 rounded-lg hover:bg-surface-3 transition-all text-text-3"
                      >
                        {expandedProvider === cfg.id ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                      </button>
                    </div>
                  </div>
                </SurfaceCard>
              ))}
            </div>

            {/* Add provider form */}
            {showAddForm && (
              <SurfaceCard padding="lg">
                <div className="flex items-center justify-between mb-5">
                  <h3 className="text-sm font-semibold text-text-1 uppercase tracking-tight">
                    {editingId ? 'Edit Provider' : 'Add Provider'}
                  </h3>
                  <button onClick={resetForm} className="p-1.5 rounded-lg hover:bg-surface-3 transition-all">
                    <X size={14} className="text-text-3" />
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[10px] font-bold text-text-3 uppercase tracking-wider">Provider Name</label>
                    <input
                      value={formData.providerName}
                      onChange={(e) => setFormData({ ...formData, providerName: e.target.value })}
                      placeholder="groq, openai, ollama, ..."
                      className="w-full px-3 py-2 rounded-lg bg-surface-2 border border-border text-xs font-medium text-text-1 outline-none focus:border-brand-light"
                      disabled={!formData.isCustom}
                    />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[10px] font-bold text-text-3 uppercase tracking-wider">Display Name</label>
                    <input
                      value={formData.displayName}
                      onChange={(e) => setFormData({ ...formData, displayName: e.target.value })}
                      placeholder="My Groq Key"
                      className="w-full px-3 py-2 rounded-lg bg-surface-2 border border-border text-xs font-medium text-text-1 outline-none focus:border-brand-light"
                    />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[10px] font-bold text-text-3 uppercase tracking-wider">API Key</label>
                    <input
                      value={formData.apiKey}
                      onChange={(e) => setFormData({ ...formData, apiKey: e.target.value })}
                      placeholder="sk-..."
                      type="password"
                      className="w-full px-3 py-2 rounded-lg bg-surface-2 border border-border text-xs font-medium text-text-1 outline-none focus:border-brand-light"
                    />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[10px] font-bold text-text-3 uppercase tracking-wider">Model</label>
                    <input
                      value={formData.defaultModel}
                      onChange={(e) => setFormData({ ...formData, defaultModel: e.target.value })}
                      placeholder="llama-3.1-8b-instant"
                      className="w-full px-3 py-2 rounded-lg bg-surface-2 border border-border text-xs font-medium text-text-1 outline-none focus:border-brand-light"
                    />
                  </div>
                  <div className="flex flex-col gap-1.5 md:col-span-2">
                    <label className="text-[10px] font-bold text-text-3 uppercase tracking-wider">Base URL</label>
                    <input
                      value={formData.baseUrl}
                      onChange={(e) => setFormData({ ...formData, baseUrl: e.target.value })}
                      placeholder="https://api.groq.com/openai/v1/chat/completions"
                      className="w-full px-3 py-2 rounded-lg bg-surface-2 border border-border text-xs font-medium text-text-1 outline-none focus:border-brand-light font-mono"
                    />
                  </div>
                </div>

                {/* Test + Save buttons */}
                <div className="flex items-center gap-3 mt-5 pt-4 border-t border-border">
                  <button
                    onClick={handleTest}
                    disabled={testStatus === 'testing' || !formData.apiKey}
                    className="flex items-center gap-1.5 px-4 py-2 rounded-lg border border-border text-[10px] font-semibold text-text-3 uppercase tracking-widest hover:bg-surface-3 transition-all disabled:opacity-50"
                  >
                    {testStatus === 'testing' ? <RefreshCw size={12} className="animate-spin" /> : <Wifi size={12} />}
                    Test Connection
                  </button>
                  {testMessage && (
                    <span className={`text-[10px] font-medium ${testStatus === 'ok' ? 'text-green-500' : 'text-red-500'}`}>
                      {testMessage}
                    </span>
                  )}
                  <div className="ml-auto flex gap-2">
                    <button
                      onClick={resetForm}
                      className="px-4 py-2 rounded-lg border border-border text-[10px] font-semibold text-text-3 uppercase tracking-widest hover:bg-surface-3 transition-all"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleSave}
                      disabled={!formData.providerName || !formData.displayName}
                      className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-brand text-white text-[10px] font-semibold uppercase tracking-widest hover:bg-brand-dark transition-all disabled:opacity-50"
                    >
                      <Check size={12} />
                      {editingId ? 'Update' : 'Add Provider'}
                    </button>
                  </div>
                </div>
              </SurfaceCard>
            )}

            {/* Fallback Chain Visualizer */}
            {userConfigs.filter(c => c.isActive).length > 1 && (
              <SurfaceCard padding="lg">
                <div className="flex items-center gap-2 mb-4">
                  <ArrowDown size={14} className="text-brand-light" />
                  <h3 className="text-[10px] font-bold text-text-3 uppercase tracking-wider">Fallback Chain</h3>
                  <span className="text-[8px] font-mono text-text-4">Drag to reorder priority</span>
                </div>
                <div className="flex flex-col gap-1.5">
                  {userConfigs
                    .filter(c => c.isActive)
                    .sort((a, b) => a.priority - b.priority)
                    .map((cfg, idx) => (
                      <div
                        key={cfg.id}
                        draggable
                        onDragStart={(e) => {
                          e.dataTransfer.setData('text/plain', cfg.id!);
                          (e.currentTarget as HTMLElement).classList.add('opacity-40');
                        }}
                        onDragEnd={(e) => {
                          (e.currentTarget as HTMLElement).classList.remove('opacity-40');
                        }}
                        onDragOver={(e) => e.preventDefault()}
                        onDrop={async (e) => {
                          e.preventDefault();
                          const draggedId = e.dataTransfer.getData('text/plain');
                          if (draggedId === cfg.id) return;
                          const active = userConfigs.filter(c => c.isActive).sort((a, b) => a.priority - b.priority);
                          const fromIdx = active.findIndex(c => c.id === draggedId);
                          const toIdx = active.findIndex(c => c.id === cfg.id);
                          if (fromIdx === -1 || toIdx === -1) return;
                          const reordered = [...active];
                          const [moved] = reordered.splice(fromIdx, 1);
                          reordered.splice(toIdx, 0, moved);
                          for (let i = 0; i < reordered.length; i++) {
                            await updateProviderConfig(reordered[i].id!, { priority: i }).catch(() => {});
                          }
                          await loadData();
                        }}
                        className="flex items-center gap-3 p-3 rounded-xl bg-surface-2 border border-border hover:border-brand/30 transition-all cursor-grab active:cursor-grabbing"
                      >
                        <div className="flex items-center gap-2 text-text-3 shrink-0">
                          <GripVertical size={14} />
                          <span className="w-5 h-5 rounded-md bg-surface-3 flex items-center justify-center text-[9px] font-bold text-text-3 font-mono">{idx + 1}</span>
                        </div>
                        <div className={`w-2 h-2 rounded-full shrink-0 ${idx === 0 ? 'bg-green-500' : idx === 1 ? 'bg-brand-light' : 'bg-text-3'}`} />
                        <div className="flex-1 min-w-0">
                          <p className="text-xs font-semibold text-text-1 truncate">{cfg.displayName}</p>
                          <p className="text-[9px] font-mono text-text-4 truncate">{cfg.providerName} → {cfg.defaultModel || 'default'}</p>
                        </div>
                        {idx === 0 && <span className="px-2 py-0.5 rounded-full bg-green-500/10 text-green-500 text-[8px] font-bold uppercase tracking-wider">Primary</span>}
                      </div>
                    ))}
                  {/* Template fallback */}
                  <div className="flex items-center gap-3 p-3 rounded-xl bg-surface-3/50 border border-dashed border-border opacity-60">
                    <div className="flex items-center gap-2 text-text-4 shrink-0">
                      <GripVertical size={14} className="opacity-30" />
                      <span className="w-5 h-5 rounded-md bg-surface-3 flex items-center justify-center text-[9px] font-bold text-text-4 font-mono">{userConfigs.filter(c => c.isActive).length + 1}</span>
                    </div>
                    <div className="w-2 h-2 rounded-full shrink-0 bg-text-4" />
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-semibold text-text-4 truncate">Template (Fallback)</p>
                      <p className="text-[9px] font-mono text-text-5 truncate">deterministic-rag — always works, no API key</p>
                    </div>
                  </div>
                </div>
              </SurfaceCard>
            )}

            {/* Add buttons */}
            {!showAddForm && (
              <div className="flex gap-3">
                <button
                  onClick={() => { setShowAddForm(true); setFormData({ ...INITIAL_FORM, isCustom: true, providerName: 'custom-' + Date.now(), baseUrl: 'http://localhost:11434/v1/chat/completions', defaultModel: 'llama3.2', priority: userConfigs.length }); }}
                  className="flex items-center gap-1.5 px-4 py-2.5 rounded-lg border border-dashed border-border text-[10px] font-semibold text-text-3 uppercase tracking-widest hover:border-brand-light hover:text-brand-light transition-all"
                >
                  <Plus size={12} /> Add Custom Provider
                </button>
                <button
                  onClick={handleAddCustom}
                  className="flex items-center gap-1.5 px-4 py-2.5 rounded-lg border border-dashed border-border text-[10px] font-semibold text-text-3 uppercase tracking-widest hover:border-brand-light hover:text-brand-light transition-all"
                >
                  <Server size={12} /> Quick Add (Ollama/LocalAI)
                </button>
              </div>
            )}

            {/* Built-in provider templates */}
            <div className="pt-4">
              <button
                onClick={() => setShowBuiltins(!showBuiltins)}
                className="flex items-center gap-2 mb-4"
              >
                <Zap size={14} className="text-text-3" />
                <span className="text-[10px] font-bold text-text-3 uppercase tracking-wider">Provider Templates</span>
                {showBuiltins ? <ChevronUp size={12} className="text-text-3" /> : <ChevronDown size={12} className="text-text-3" />}
              </button>

              {showBuiltins && (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                  {builtins.map((b) => {
                    const isConfigured = userConfigs.some((c) => c.providerName === b.name);
                    return (
                      <button
                        key={b.name}
                        onClick={() => handleSelectBuiltin(b)}
                        className={`flex flex-col items-center gap-2 p-4 rounded-card border transition-all text-center ${isConfigured ? 'bg-brand-dim border-border-green' : 'bg-surface-1 border-border hover:border-brand-light'}`}
                      >
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${isConfigured ? 'bg-brand/20' : 'bg-surface-3'}`}>
                          <Globe size={14} className={isConfigured ? 'text-brand-light' : 'text-text-3'} />
                        </div>
                        <p className="text-[10px] font-bold text-text-1 truncate w-full">{b.display}</p>
                        <p className="text-[8px] font-mono text-text-3 truncate w-full">{b.name}</p>
                        {isConfigured && <Check size={10} className="text-green-500" />}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
