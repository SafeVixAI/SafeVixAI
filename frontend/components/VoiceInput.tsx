'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

/**
 * SafeVixAI Enterprise Voice Input
 * Enterprise-grade voice recognition with semantic theme integration.
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import { Mic, MicOff, Loader2 } from 'lucide-react';
import { getLanguageByCode } from '@/lib/languages';
import { logClientWarning } from '@/lib/client-logger';

interface VoiceInputProps {
  onResult: (text: string) => void;
  className?: string;
  language?: string;
}

// Web Speech API types
interface IWindow extends Window {
  SpeechRecognition?: new () => ISpeechRecognition;
  webkitSpeechRecognition?: new () => ISpeechRecognition;
}

interface ISpeechRecognition extends EventTarget {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  maxAlternatives: number;
  start(): void;
  stop(): void;
  abort(): void;
  onstart: (() => void) | null;
  onend: (() => void) | null;
  onerror: ((event: SpeechRecognitionErrorEventLike) => void) | null;
  onresult: ((event: SpeechRecognitionResultEventLike) => void) | null;
}

interface SpeechRecognitionResultEventLike {
  results: {
    [index: number]: {
      [index: number]: {
        transcript: string;
      };
    };
  };
}

interface SpeechRecognitionErrorEventLike {
  error?: string;
}

export function VoiceInput({ onResult, className = '', language = 'en' }: VoiceInputProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const recognitionRef = useRef<ISpeechRecognition | null>(null);

  const handleResult = useCallback((text: string) => {
    onResult(text);
  }, [onResult]);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const win = window as IWindow;
    const SpeechAPI = win.SpeechRecognition ?? win.webkitSpeechRecognition;
    if (!SpeechAPI) return;

    const recognition = new SpeechAPI();
    const langObj = getLanguageByCode(language);
    recognition.lang = langObj?.recognitionCode || 'en-IN';
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      setIsLoading(false);
      setIsRecording(true);
    };

    recognition.onresult = (e) => {
      const transcript = e.results[0][0].transcript;
      handleResult(transcript);
      setIsRecording(false);
    };

    recognition.onerror = (event) => {
      logClientWarning('Speech recognition error', event.error);
      setIsRecording(false);
      setIsLoading(false);
    };

    recognition.onend = () => {
      setIsRecording(false);
      setIsLoading(false);
    };

    recognitionRef.current = recognition;
    return () => { recognition.abort(); };
  }, [handleResult, language]);

  const toggle = () => {
    if (!recognitionRef.current) {
      // Graceful fallback for demo if no API available
      handleResult('Reporting a road hazard at my current location.');
      return;
    }
    if (isRecording) {
      recognitionRef.current.stop();
    } else {
      setIsLoading(true);
      try {
        recognitionRef.current.start();
      } catch (error) {
        logClientWarning('Speech recognition start failed', error);
        setIsLoading(false);
      }
    }
  };

  return (
    <button
      onClick={toggle}
      disabled={isLoading}
      aria-label={isRecording ? 'Stop recording' : 'Start voice input'}
      className={`relative flex items-center justify-center rounded-full transition-all active:scale-90 border-2 shrink-0 ${
        isRecording 
          ? 'border-emergency bg-emergency/10 text-emergency shadow-[0_0_20px_rgba(220,38,38,0.3)]' 
          : 'border-border bg-surface-1 text-text-2 hover:border-border-md hover:text-text-1'
      } ${className}`}
      style={{
        width: '44px',
        height: '44px',
      }}
    >
      {isLoading ? (
        <Loader2 size={18} className="animate-spin text-brand" />
      ) : isRecording ? (
        <MicOff size={18} className="animate-pulse" />
      ) : (
        <Mic size={18} />
      )}
      
      {isRecording && (
        <span
          className="absolute inset-0 rounded-full animate-ping opacity-25 bg-emergency"
        />
      )}
    </button>
  );
}