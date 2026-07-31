'use client';

import { Component, ErrorInfo, ReactNode } from 'react';
import { ErrorDialog, ErrorInfo as ErrorInfoType } from './ErrorDialog';
import { CrashScreen } from './CrashScreen';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: 'dialog' | 'screen';
}

interface ErrorBoundaryState {
  error: ErrorInfoType | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { error: { error } };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({
      error: {
        error,
        componentStack: errorInfo.componentStack || undefined,
      },
    });
  }

  handleRecover = () => {
    this.setState({ error: null });
  };

  render() {
    if (this.state.error) {
      if (this.props.fallback === 'screen') {
        return (
          <CrashScreen
            error={this.state.error.error}
            errorInfo={{ componentStack: this.state.error.componentStack }}
            onRecover={this.handleRecover}
          />
        );
      }
      return (
        <ErrorDialog
          errorInfo={this.state.error}
          onClose={this.handleRecover}
          onRecover={this.handleRecover}
        />
      );
    }
    return this.props.children;
  }
}
