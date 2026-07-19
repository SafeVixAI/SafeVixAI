// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { gsap } from '@/lib/gsap';
import { useGSAP } from '@gsap/react';
import {
  ShieldCheck, BookOpen, Copy,
  HelpCircle, ThumbsUp, ThumbsDown, RotateCcw,
  Volume2, VolumeX, Wifi, WifiOff, Cpu, Zap
} from 'lucide-react';
import { useAppStore } from '@/lib/store';
import { useShallow } from 'zustand/react/shallow';
import { getOfflineAI, askOfflineAI, isOfflineAIReady } from '@/lib/offline-ai';
import { track } from '@/lib/analytics';
import TopSearch from '@/components/dashboard/TopSearch';
import { TerminalHeader } from '@/components/ui/TerminalHeader';
import { SurfaceCard } from '@/components/ui/SurfaceCard';
import { useGeolocation } from '@/lib/geolocation';
import { logClientError } from '@/lib/client-logger';
import { formatTime } from '@/lib/intl-formatters';
import { PUBLIC_CHATBOT_BASE_URL } from '@/lib/public-env';
import { getLanguageByCode } from '@/lib/languages';
import { appendChatLog, loadChatHistory } from '@/lib/chat-history';
import { fetchProviderConfigs, fetchBuiltinProviders } from '@/lib/provider-api';
import type { ProviderConfig, BuiltinProvider } from '@/lib/provider-api';
import { useTranslation } from 'react-i18next';

const TypingIndicator = dynamic(() => import('@/components/chat/TypingIndicator'), { ssr: false })
const SuggestedInquiries = dynamic(() => import('@/components/chat/SuggestedInquiries'), { ssr: false })
const PureMultimodalInput = dynamic(() => import('@/components/chat/multimodal-ai-chat-input'), { ssr: false })
const ModelLoader = dynamic(() => import('@/components/ModelLoader').then(mod => ({ default: mod.ModelLoader })), { ssr: false })


const CHATBOT_URL = PUBLIC_CHATBOT_BASE_URL;

async function* streamChat(
 message: string,
 session_id: string,
 lat?: number,
 lon?: number,
 provider_hint?: string,
 provider_model?: string,
): AsyncGenerator<{ type: string; text?: string; intent?: string; sources?: string[]; session_id?: string; message?: string; provider?: string; model?: string }> {
 const resp = await fetch(`${CHATBOT_URL}/api/v1/chat/stream`, {
 method: 'POST',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify({ message, session_id, lat, lon, provider_hint, provider_model }),
 });
 if (!resp.ok || !resp.body) throw new Error(`Chat error: ${resp.status}`);
 const reader = resp.body.getReader();
 const decoder = new TextDecoder();
 let buffer = '';
 while (true) {
 const { done, value } = await reader.read();
 if (done) break;
 buffer += decoder.decode(value, { stream: true });
 const lines = buffer.split('\n');
 buffer = lines.pop() ?? '';
 for (const line of lines) {
 if (line.startsWith('data: ')) {
 try { yield JSON.parse(line.slice(6)); } catch { /* skip */ }
 }
 }
 }
}
interface Message {
 id: string;
 role: 'user' | 'ai' | 'system';
 text: string;
 timestamp: string;
 citations?: string[];
 suggestedQueries?: string[];
 provider?: string;
}

import TypingText from '@/components/dashboard/TypingText';

export default function ChatPage() {
  const { t } = useTranslation();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const { aiMode, setAiMode, setModelLoadProgress, selectedProvider, setSelectedProvider } = useAppStore(
    useShallow((s) => ({
      aiMode: s.aiMode,
      setAiMode: s.setAiMode,
      setModelLoadProgress: s.setModelLoadProgress,
      selectedProvider: s.selectedProvider,
      setSelectedProvider: s.setSelectedProvider,
    }))
  );

  const [providerOptions, setProviderOptions] = useState<{ name: string; display: string; model: string }[]>([]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [userConfigs, builtins] = await Promise.all([
          fetchProviderConfigs().catch(() => [] as ProviderConfig[]),
          fetchBuiltinProviders().catch(() => [] as BuiltinProvider[]),
        ]);
        if (cancelled) return;
        const options: { name: string; display: string; model: string }[] = [];
        for (const p of builtins) {
          options.push({ name: p.name, display: p.display, model: p.models[0] ?? '' });
        }
        for (const p of userConfigs) {
          if (p.isActive && !options.some(o => o.name === p.providerName)) {
            options.push({ name: p.providerName, display: p.displayName, model: p.defaultModel ?? '' });
          }
        }
        setProviderOptions(options);
      } catch {
        // fallback — keep dropdown empty
      }
    }
    void load();
    return () => { cancelled = true; };
  }, []);

  const toggleAiMode = useCallback(async (mode: 'online' | 'offline') => {
    if (mode === 'online') {
      setAiMode('online');
    } else {
      const isAlreadyReady = isOfflineAIReady();
      if (!isAlreadyReady) {
        /* istanbul ignore next */const conn = typeof navigator !== 'undefined' ? (navigator as any).connection : null;
        const isCellular = conn && (conn.type === 'cellular' || conn.effectiveType === '2g' || conn.effectiveType === '3g' || conn.saveData);
        if (isCellular) {
          const confirmDownload = window.confirm(
            t('chat.mobile_data_warning', 'Warning: Enabling offline AI requires downloading a ~1.3GB model. You appear to be on a cellular connection or have Data Saver active. Do you want to proceed with the download?')
          );
          if (!confirmDownload) {
            setAiMode('online');
            return;
          }
        }
      }

      setAiMode('loading');
      try {
        await getOfflineAI((progress) => {
          if (progress.status === 'downloading') {
            setModelLoadProgress(progress.percent);
          } else if (progress.status === 'ready' || progress.status === 'system_available') {
            setModelLoadProgress(100);
            setAiMode('offline');
          }
        });
        setAiMode('offline');
      } catch (err) {
        logClientError('Failed to initialize offline AI:', err);
        setAiMode('online');
        setToastMessage(t('chat.offline_ai_failed', 'Offline AI failed to initialize. Using online mode.'));
      }
    }
  }, [setAiMode, setModelLoadProgress, t]);

 const { location } = useGeolocation();
  const [sessionId] = useState(() => {
    /* istanbul ignore next */if (typeof window === 'undefined') return `assistant-${Date.now()}`;
    const existing = window.localStorage.getItem('safevixai:assistant-session');
    if (existing) return existing;
    const uuid = typeof crypto !== 'undefined' && /* istanbul ignore next */crypto.randomUUID
      ? crypto.randomUUID()
      : Math.random().toString(36).substring(2, 15) + '-' + Date.now();
    const next = `assistant-${uuid}`;
    window.localStorage.setItem('safevixai:assistant-session', next);
    return next;
  });
 const [selectedLanguage, setSelectedLanguage] = useState('en');
  const pageRef = useRef<HTMLDivElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
 const welcomeAdded = useRef(false);
 const [autoRead, setAutoRead] = useState(false);

 const [isSpeaking, setIsSpeaking] = useState(false);

 const speakText = useCallback((text: string) => {
   /* istanbul ignore next */if (!('speechSynthesis' in window)) return;
   window.speechSynthesis.cancel();
   
   const utterance = new SpeechSynthesisUtterance(text);
   const langObj = getLanguageByCode(selectedLanguage);
   utterance.lang = langObj?.synthesisCode || 'en-IN';
   
   utterance.onstart = () => setIsSpeaking(true);
   utterance.onend = () => setIsSpeaking(false);
   utterance.onerror = () => setIsSpeaking(false);
   
   window.speechSynthesis.speak(utterance);
 }, [selectedLanguage]);

 const stopSpeaking = useCallback(() => {
   /* istanbul ignore next */if (!('speechSynthesis' in window)) return;
   window.speechSynthesis.cancel();
   setIsSpeaking(false);
 }, []);

  useEffect(() => {
  // Guard against React StrictMode double-mount
  if (welcomeAdded.current) return;
  welcomeAdded.current = true;
  document.title = `${t('nav.assistant', 'AI Assistant')} | SafeVixAI`;
 
  const hydrateChat = async () => {
    const initialSysMessage: Message = {
      id: 'sys-1',
      role: 'system',
      text: t('chat.session_encrypted', 'Session encrypted with SafeVixAI Protocol v2.4'),
      timestamp: '',
    };
    const history = await loadChatHistory(sessionId);
    if (history.length > 0) {
      setMessages([
        initialSysMessage,
        ...history.map((entry) => ({
          id: entry.id,
          role: entry.role,
          text: entry.text,
          timestamp: entry.timestamp,
          citations: entry.citations,
          provider: entry.provider,
        })),
      ]);
      return;
    }
 
    const welcomeMsg: Message = {
      id: 'ai-1',
      role: 'ai',
      text: t('chat.welcome_msg', 'SafeVixAI assistant online. I can answer questions about the Motor Vehicles Act, traffic penalties, your rights during a police stop, and road safety laws across India. What do you need?'),
      timestamp: formatTime(new Date()),
      provider: 'SafeVixAI Router',
    };
    setMessages([initialSysMessage, welcomeMsg]);
  };
 
  void hydrateChat();
  }, [sessionId, t]);

 useEffect(() => {
 if (scrollRef.current) {
 scrollRef.current.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
 }
 }, [messages, loading]);

 useEffect(() => {
 if (toastMessage) {
 const timer = setTimeout(() => setToastMessage(null), 3000);
 return () => clearTimeout(timer);
 }
 }, [toastMessage]);

 useEffect(() => {
 if (textareaRef.current) {
 textareaRef.current.style.height = 'auto';
 textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
 }
 }, [input]);

 const handleSend = useCallback(async (text: string) => {
   if (!text.trim()) return;

   const time = formatTime(new Date());
   const userMsg: Message = { id: Date.now().toString(), role: 'user', text, timestamp: time };
   setMessages(prev => [...prev, userMsg]);
   void appendChatLog({
     id: userMsg.id,
     sessionId,
     role: userMsg.role,
     text: userMsg.text,
     timestamp: userMsg.timestamp,
     createdAt: new Date().toISOString(),
   });
   setInput('');
   setLoading(true);

   // Streaming assistant placeholder
   const assistantId = `ai-${Date.now() + 1}`;
   setMessages(prev => [...prev, { id: assistantId, role: 'ai', text: '', timestamp: time }]);

   // Track chatbot query event
   track.chatbotQueried('chat_message', aiMode === 'offline' ? 'local_gemma' : 'backend_sse');

   try {
     if (aiMode === 'offline') {
       // Ensure offline AI is initialized
       await getOfflineAI();
       const offlineReply = await askOfflineAI(text);
       setMessages(prev =>
         prev.map(m =>
           m.id === assistantId
             ? { ...m, text: offlineReply, citations: ['Offline Knowledge Base'], provider: 'Local Gemma' }
             : m
         )
       );
       void appendChatLog({
         id: assistantId,
         sessionId,
         role: 'ai',
         text: offlineReply,
         timestamp: time,
         citations: ['Offline Knowledge Base'],
         provider: 'Local Gemma',
         createdAt: new Date().toISOString(),
       });
       if (autoRead && offlineReply) {
         speakText(offlineReply);
       }
     } else {
         const providerHint = selectedProvider?.providerName || undefined;
         const providerModel = selectedProvider?.model || undefined;
        let accumulated = '';
        for await (const event of streamChat(text, sessionId, location?.lat, location?.lon, providerHint, providerModel)) {
         if (event.type === 'token' && event.text) {
           accumulated += event.text;
           setMessages(prev =>
             prev.map(m => m.id === assistantId ? { ...m, text: accumulated } : m)
           );
       } else if (event.type === 'done') {
         const sources = event.sources ?? [];
         const provider = event.provider || event.model || 'SafeVixAI Router';
         setMessages(prev =>
           prev.map(m =>
             m.id === assistantId
               ? { ...m, text: accumulated || 'No response received.', citations: sources, provider }
               : m
           )
         );
         void appendChatLog({
           id: assistantId,
           sessionId,
           role: 'ai',
           text: accumulated || 'No response received.',
           timestamp: time,
           citations: sources,
           provider,
           createdAt: new Date().toISOString(),
         });
           if (autoRead && accumulated) {
             speakText(accumulated);
           }
         } else if (event.type === 'error') {
           throw new Error(event.message ?? 'Stream error');
         }
       }
     }
   } catch (err) {
     logClientError('Chat error:', err);
      setMessages(prev =>
        prev.map(m =>
          m.id === assistantId
            ? { ...m, text: t('chat.connection_interrupted', 'Neural link interrupted. Please verify connectivity and retry protocol.') }
            : m
        )
      );
   } finally {
     setLoading(false);
   }
  }, [sessionId, location, autoRead, speakText, aiMode, selectedProvider, t]);

  useGSAP(() => {
    gsap.from(pageRef.current, { opacity: 0, y: 16, duration: 0.35, ease: 'power2.out' });
  }, { scope: pageRef });

  return (
   <div ref={pageRef} className="sv-aurora w-full h-[var(--full-content-h)] md:h-[var(--full-content-h-desktop)] flex flex-col overflow-hidden bg-surface-1">
   <h1 className="sr-only">AI Assistant</h1>
   {/* Model Loading HUD overlay */}
  <ModelLoader />

  {/* ── Background Decorative Lines (SafeVixAI Pro Aesthetic) ── */}
  <div className="absolute inset-0 pointer-events-none z-0 overflow-hidden">

  {/* Ambient Glows */}
  <div className="absolute top-[-10%] right-[-10%] w-[60%] h-[60%] rounded-full bg-brand/5 dark:bg-brand/10 blur-[120px] hidden dark:block" />
  <div className="absolute bottom-[-5%] left-[-5%] w-[40%] h-[40%] rounded-full bg-brand-light/5 dark:bg-brand-light/10 blur-[100px] hidden dark:block" />
     {/* ── Unified Tactical Navigation Header ── */}
    <TerminalHeader title={t('chat.title', 'Assistant HUD')} subtitle={t('chat.subtitle', 'TACTICAL INTEL & LEGAL')} rightElement={
      <div className="flex items-center gap-3">
        {/* Mode Toggle */}
        <div className="flex items-center bg-surface-2 dark:bg-white/5 rounded-full p-0.5 border border-border-md dark:border-white/10">
          <button
            onClick={() => toggleAiMode('online')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[10px] font-semibold uppercase tracking-widest transition-all ${
              aiMode === 'online'
                ? 'bg-brand text-brand-foreground shadow-sm shadow-brand/10'
                : 'text-text-2 hover:text-text-1 dark:hover:text-text-3'
            }`}
            title={t('chat.switch_online', 'Switch to Online AI')}
          >
            <Wifi size={12} />
            {t('chat.online', 'Online')}
          </button>
          <button
            onClick={() => toggleAiMode('offline')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[10px] font-semibold uppercase tracking-widest transition-all ${
              aiMode === 'offline'
                ? 'bg-brand text-brand-foreground shadow-sm shadow-brand/10'
                : 'text-text-2 hover:text-text-1 dark:hover:text-text-3'
            }`}
            title={t('chat.switch_offline', 'Switch to Offline AI (Gemma)')}
          >
            <WifiOff size={12} />
            {t('chat.offline', 'Offline')}
          </button>
        </div>
 
        {/* Provider/Model Selector */}
        <div className="relative group">
          <button
            onClick={() => {
              const el = document.getElementById('provider-selector-dropdown');
              if (el) el.classList.toggle('hidden');
            }}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-surface-2 border border-border text-[9px] font-bold text-text-3 uppercase tracking-widest hover:border-brand-light hover:text-brand-light transition-all"
          >
            {selectedProvider ? <Cpu size={11} /> : <Zap size={11} className="text-amber-500" />}
            {selectedProvider ? selectedProvider.displayName.slice(0, 12) : 'Auto'}
          </button>
          <div id="provider-selector-dropdown" className="hidden absolute right-0 top-full mt-1 w-56 bg-surface-2 border border-border rounded-xl shadow-2xl z-50 overflow-hidden">
            <div className="p-2 border-b border-border">
              <button
                onClick={() => {
                  setSelectedProvider(null);
                  document.getElementById('provider-selector-dropdown')?.classList.add('hidden');
                }}
                className={`w-full text-left px-3 py-2 rounded-lg text-[10px] font-semibold transition-all ${!selectedProvider ? 'bg-brand/10 text-brand-light' : 'text-text-3 hover:bg-surface-3'}`}
              >
                Auto (Router)
              </button>
            </div>
            <div className="max-h-48 overflow-y-auto p-2 space-y-1">
              <p className="px-3 py-1 text-[8px] font-bold text-text-3 uppercase tracking-wider">Providers</p>
              {providerOptions.length === 0 ? (
                <p className="px-3 py-2 text-[9px] text-text-4 italic">Loading providers...</p>
              ) : providerOptions.map((p) => (
                <button
                  key={p.name}
                  onClick={() => {
                    setSelectedProvider({ providerName: p.name, model: p.model, displayName: p.display });
                    document.getElementById('provider-selector-dropdown')?.classList.add('hidden');
                  }}
                  className={`w-full text-left px-3 py-2 rounded-lg text-[10px] font-semibold transition-all ${selectedProvider?.providerName === p.name ? 'bg-brand/10 text-brand-light' : 'text-text-3 hover:bg-surface-3'}`}
                >
                  {p.display}
                  <span className="block text-[8px] font-mono text-text-4">{p.model}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {isSpeaking && (
          <button
            onClick={stopSpeaking}
            className="p-2 rounded-full transition-all bg-red-500/10 text-red-500 border border-red-500/30 animate-pulse"
            title={t('chat.stop_reading', 'Stop Reading')}
            aria-label={t('chat.stop_reading', 'Stop Reading')}
          >
            <VolumeX size={16} />
          </button>
        )}
        <button
          onClick={() => {
            setAutoRead(!autoRead);
            if (autoRead) stopSpeaking();
            setToastMessage(autoRead ? t('chat.audio_disabled', 'Audio disabled') : t('chat.audio_enabled', 'Audio enabled'));
          }}
          className={`p-2 rounded-full transition-colors border ${autoRead ? 'bg-brand/20 text-brand border-brand/30 shadow-[0_0_15px_rgba(0,200,150,0.2)]' : 'bg-surface-2 text-text-3 border-border hover:text-text-1'}`}
          title={autoRead ? t('chat.auto_read_disable', 'Disable Auto-read') : t('chat.auto_read_enable', 'Enable Auto-read')}
          aria-label={autoRead ? t('chat.auto_read_disable', 'Disable Auto-read') : t('chat.auto_read_enable', 'Enable Auto-read')}
        >
          {autoRead ? <Volume2 size={16} /> : <VolumeX size={16} />}
        </button>
      </div>
    } /> </div>

 <div className="lg:hidden relative z-40">
 <TopSearch isMapPage={false} forceShow={true} showBack={false} />
 </div>

 {/* ── Toast Notification ── */}
 
 {toastMessage && (
 <div style={{ animation: "fadeInDown 0.2s ease-out" }}
 className="fixed top-20 left-1/2 -translate-x-1/2 z-50 bg-surface-3 text-text-1 px-4 py-2 rounded-full shadow-lg text-sm font-medium"
 >
 {toastMessage}
 </div>
 )}
 

 {/* ── Chat Canvas ── */}
 <main ref={scrollRef} className="flex-1 min-h-0 overflow-y-auto px-4 sm:px-6 overflow-x-hidden pt-28 lg:pt-24 pb-48 lg:pb-36 flex flex-col max-w-4xl mx-auto w-full relative z-10 scroll-smooth [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
 <div className="space-y-8 flex flex-col w-full pb-8">
 
 {messages.map((msg) => {
 if (msg.role === 'system') {
 return (
 <div key={msg.id} className="self-center mt-2" style={{ animation: "fadeInUp 0.3s ease-out" }}
 >
 <div className="bg-white dark:bg-white/5 px-4 py-2 rounded-full border border-border shadow-sm backdrop-blur-md">
 <span className="text-brand dark:text-brand-light text-[10px] uppercase tracking-[0.15em] font-black font-space">
 {msg.text}
 </span>
 </div>
 </div>
 );
 }

  if (msg.role === 'user') {
  return (
  <div key={msg.id} style={{ animation: "slideInRight 0.3s ease-out" }} className="self-end max-w-[85%] sm:max-w-[75%] ml-12"
  >
  <div className="flex flex-col items-end gap-2">
  <div className="bg-[--brand-dim] rounded-t-2xl rounded-bl-2xl rounded-br-sm px-5 py-3.5 shadow-lg shadow-brand/10 border border-brand/20">
  <p className="text-text-1 text-[15px] leading-relaxed font-medium">{msg.text}</p>
  </div>
  <time dateTime={msg.timestamp} suppressHydrationWarning className="text-[10px] text-text-3 mr-2 font-medium tracking-wide shadow-sm">{msg.timestamp} • SafeVixAI</time>
  </div>
  </div>
  );
  }

  if (msg.role === 'ai') {
  const isOfflineMessage = msg.citations?.includes('Offline Knowledge Base') || aiMode === 'offline';
  const providerName = msg.provider || (isOfflineMessage ? 'Local Gemma' : 'SafeVixAI Router');

  return (
  <div key={msg.id} style={{ animation: "slideInLeft 0.3s ease-out" }} className="self-start max-w-[90%] sm:max-w-[85%] mr-12"
  >
  <div className="flex flex-col items-start gap-2 w-full">
  <SurfaceCard padding="lg" className="rounded-tl-2xl rounded-tr-2xl rounded-br-2xl rounded-bl-sm shadow-md shadow-black/10 bg-[--surface-2] border border-[--border] backdrop-blur-xl">
  <div className="flex items-center justify-between gap-2 mb-3 w-full">
    <div className="flex items-center gap-2">
      <div className="p-1.5 rounded-lg bg-brand/10 text-brand">
        <ShieldCheck size={16} />
      </div>
      <span className="text-brand text-[11px] font-bold uppercase tracking-[0.15em] font-mono">SafeVixAI</span>
    </div>
    <span className="text-[10px] font-semibold text-text-3 bg-surface-3 border border-border px-2 py-0.5 rounded-full font-mono">
      {providerName}
    </span>
  </div>
  <p className="text-text-1 text-[15px] leading-relaxed font-medium">
  <TypingText text={msg.text} />
  </p>

 {msg.citations && msg.citations.length > 0 && (
 <div className="mt-5 flex flex-wrap gap-2">
 {msg.citations.map((cite, i) => (
 <div key={i} className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full ${i === 0 ? 'bg-brand/10 border border-brand/20 text-brand' : 'bg-surface-3 border border-border text-text-2'}`}>
 {i === 0 && <BookOpen size={12} />}
 <span className={`text-[11px] font-semibold tracking-wide ${!i && 'uppercase'}`}>{cite}</span>
 </div>
 ))}
 </div>
 )}
 </SurfaceCard>

 <div className="flex items-center gap-4 ml-2 mb-1">
 <time dateTime={msg.timestamp} suppressHydrationWarning className="text-[10px] text-text-3 font-medium tracking-wide">{msg.timestamp} • SafeVixAI</time>
 <div className="flex gap-1.5 ml-1">
<button 
    onClick={async () => {
      try {
        /* istanbul ignore next */await navigator.clipboard.writeText(msg.text);
        setToastMessage(t('chat.copied', 'Copied to clipboard!'));
      } catch {
        setToastMessage(t('chat.clipboard_unavailable', 'Clipboard unavailable'));
      }
    }}
    className="text-text-3 hover:text-text-2 transition-colors p-1 rounded hover:bg-surface-2"
    title={t('chat.copy', 'Copy')}
    aria-label={t('chat.copy', 'Copy')}
    >
    <Copy size={13} strokeWidth={2} />
    </button>
<button 
    onClick={() => {
      speakText(msg.text);
      setToastMessage(t('chat.reading_aloud', 'Reading aloud...'));
    }}
    className="text-text-3 hover:text-text-2 transition-colors p-1 rounded hover:bg-surface-2"
    title={t('chat.read_aloud', 'Read Aloud')}
    aria-label={t('chat.read_aloud', 'Read Aloud')}
    >
    <Volume2 size={13} strokeWidth={2} />
    </button>
  <button 
  onClick={() => setToastMessage(t('chat.feedback_recorded', 'Feedback recorded'))}
  className="text-text-3 hover:text-text-2 transition-colors p-1 rounded hover:bg-surface-2"
  title={t('chat.thumbs_up', 'Thumbs Up')}
  aria-label={t('chat.thumbs_up', 'Thumbs Up')}
  >
  <ThumbsUp size={13} strokeWidth={2} />
  </button>
  <button 
  onClick={() => setToastMessage(t('chat.feedback_recorded', 'Feedback recorded'))}
  className="text-text-3 hover:text-text-2 transition-colors p-1 rounded hover:bg-surface-2"
  title={t('chat.thumbs_down', 'Thumbs Down')}
  aria-label={t('chat.thumbs_down', 'Thumbs Down')}
  >
  <ThumbsDown size={13} strokeWidth={2} />
  </button>
  <button 
  onClick={() => setToastMessage(t('chat.retrying', 'Retrying...'))}
  className="text-text-3 hover:text-text-2 transition-colors p-1 rounded hover:bg-surface-2 ml-1"
  title={t('chat.retry', 'Retry')}
  aria-label={t('chat.retry', 'Retry')}
  >
  <RotateCcw size={13} strokeWidth={2} />
  </button>
 </div>
 </div>

 {msg.suggestedQueries && (
 <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mt-2 w-full">
 {msg.suggestedQueries.map((q, i) => (
 <button
 key={i}
 onClick={() => handleSend(q)}
 className="group bg-surface-2 hover:bg-surface-3 backdrop-blur-md transition-all duration-200 p-4 rounded-xl flex items-start gap-3 text-left border border-border hover:border-brand/30 hover:shadow-sm"
 >
 <div className="mt-0.5 p-1 rounded bg-brand/10 text-brand group-hover:scale-110 transition-transform">
 <HelpCircle size={14} />
 </div>
 <span className="text-text-1 text-[13px] font-medium leading-snug">{q}</span>
 </button>
 ))}
 </div>
 )}
 </div>
 </div>
 );
 }
 })}

 {((messages.length <= 2) || showSuggestions) && !loading && (
   <div style={{ animation: "fadeInUp 0.3s ease-out" }}
   className="self-start w-full mt-2"
   >
   <p className="text-xs text-text-3 mb-3 font-semibold px-2 uppercase tracking-widest">{t('chat.suggested_inquiries', 'Suggested Inquiries')}</p>
   <SuggestedInquiries onSelect={handleSend} />
   {messages.length > 2 && (
   <button 
   onClick={() => setShowSuggestions(false)}
   className="mt-4 text-xs font-semibold text-text-3 hover:text-text-1 underline underline-offset-2 transition-colors mx-auto block"
   >
   {t('chat.hide_suggested', 'Hide Suggestions')}
   </button>
   )}
   </div>
  )}

 {messages.length > 2 && !showSuggestions && !loading && (
  <div style={{ animation: "fadeIn 0.3s ease-out" }} className="self-center">
  <button 
  onClick={() => setShowSuggestions(true)}
  className="px-4 py-2 rounded-full bg-white/50 dark:bg-white/5 border border-border text-xs font-semibold text-text-2 hover:bg-white dark:hover:bg-white/10 transition-colors shadow-sm"
  >
  {t('chat.show_suggested', 'Show Suggested Inquiries')}
  </button>
  </div>
 )}

  {/* Typing Indicator */}
  {loading && (
  <div style={{ animation: "slideInLeft 0.3s ease-out" }}
  className="self-start max-w-[90%] sm:max-w-[85%]"
  >
    <TypingIndicator />
  </div>
  )}

 
 </div>
 </main>

 {/* ── Bottom Input Shell ── */}
 <div className="absolute bottom-0 w-full z-50 flex justify-between items-end bg-gradient-to-t from-surface-1 via-surface-1/90 to-transparent pt-16 pb-28 lg:pb-6 px-4 sm:px-6 pointer-events-none">
 <div className="max-w-4xl mx-auto w-full flex flex-col relative items-end pointer-events-none">
 <div className="w-full flex items-end gap-2 sm:gap-3 pointer-events-auto">
  <PureMultimodalInput
  value={input}
  onChange={setInput}
  onSendMessage={({ input }) => handleSend(input)}
  isGenerating={loading}
  canSend={!loading}
  selectedLanguage={selectedLanguage}
  onLanguageChange={setSelectedLanguage}
  />
 </div>
 </div>
 </div>
 </div>
 );
}
