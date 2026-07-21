'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { logClientError } from '@/lib/client-logger';

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  name?: string;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    logClientError(`ErrorBoundary${this.props.name ? `[${this.props.name}]` : ''} caught an error`, {
      message: error.message,
      componentStack: errorInfo.componentStack,
    });
    this.props.onError?.(error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      return (
        <div role="alert" className="flex flex-col items-center justify-center p-8 text-center border border-red-500/20 bg-red-950/10 rounded-xl">
          <AlertTriangle className="w-10 h-10 text-red-400 mb-3" />
          <h3 className="text-sm font-bold text-text-1 mb-1">Something went wrong</h3>
          <p className="text-xs text-text-2 mb-4 max-w-sm">
            {this.props.name ? `${this.props.name} failed to load. ` : ''}Try refreshing this section.
          </p>
          <button
            onClick={this.handleReset}
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-surface-3 hover:bg-surface-4 text-text-1 text-xs font-semibold rounded-lg transition-colors"
          >
            <RefreshCw size={14} />
            Retry
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}