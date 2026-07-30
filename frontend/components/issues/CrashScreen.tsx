'use client';

import { useCallback, useState } from 'react';
import { AlertTriangle, Bug, ChevronDown, ChevronUp, RefreshCw } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { logClientError } from '@/lib/client-logger';

interface CrashScreenProps {
  error: Error;
  errorInfo?: Record<string, unknown>;
  onRecover?: () => void;
}

export function CrashScreen({ error, errorInfo, onRecover }: CrashScreenProps) {
  const [showDetails, setShowDetails] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [description, setDescription] = useState('');

  const handleReport = useCallback(async () => {
    setIsSubmitting(true);
    try {
      const { createIssue } = await import('@/lib/api/issues');
      await createIssue({
        issueType: 'crash',
        severity: 'critical',
        title: `Crash: ${error?.message?.slice(0, 100) || 'Fatal error'}`,
        description: description || error?.message || 'Application crashed unexpectedly',
        stepsToReproduce: `Error: ${error?.message}\nStack: ${error?.stack}`,
        logs: {
          errorMessage: error?.message,
          errorName: error?.name,
          errorStack: error?.stack,
          errorInfo,
        },
        browserInfo: {
          userAgent: navigator.userAgent,
          url: window.location.href,
          timestamp: new Date().toISOString(),
          viewport: `${window.innerWidth}x${window.innerHeight}`,
          online: navigator.onLine,
        },
        systemInfo: {
          platform: (navigator as any).platform,
          language: navigator.language,
          cookiesEnabled: navigator.cookieEnabled,
        },
      });
      setSubmitted(true);
    } catch (reportError) {
      logClientError('Crash report submission failed', reportError);
      setSubmitted(true);
    } finally {
      setIsSubmitting(false);
    }
  }, [error, errorInfo, description]);

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-background p-4">
      <div className="max-w-lg w-full text-center space-y-6">
        <div className="flex justify-center">
          <div className="rounded-full bg-destructive/10 p-4">
            <AlertTriangle className="h-12 w-12 text-destructive" />
          </div>
        </div>

        <div className="space-y-2">
          <h1 className="text-2xl font-bold">Application Crashed</h1>
          <p className="text-muted-foreground">
            Sorry, the application encountered a critical error. Our team has been notified.
          </p>
        </div>

        {!submitted && (
          <div className="space-y-3 text-left">
            <label className="text-sm font-medium block">
              What were you doing? (optional)
            </label>
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Tell us what led to this crash..."
              rows={3}
            />
            <div className="flex gap-2 justify-center">
              <Button
                variant="outline"
                onClick={() => setShowDetails(!showDetails)}
                size="sm"
              >
                {showDetails ? <ChevronUp className="h-4 w-4 mr-1" /> : <ChevronDown className="h-4 w-4 mr-1" />}
                {showDetails ? 'Hide' : 'Show'} Technical Details
              </Button>
            </div>
            {showDetails && (
              <div className="rounded-md bg-muted p-3 font-mono text-xs overflow-auto max-h-32">
                {error?.stack || error?.message || 'No stack trace available'}
              </div>
            )}
          </div>
        )}

        <div className="flex gap-3 justify-center">
          {!submitted ? (
            <>
              <Button variant="outline" onClick={onRecover || (() => window.location.reload())}>
                <RefreshCw className="h-4 w-4 mr-1" /> Reload App
              </Button>
              <Button onClick={handleReport} disabled={isSubmitting}>
                <Bug className="h-4 w-4 mr-1" />
                {isSubmitting ? 'Submitting...' : 'Send Crash Report'}
              </Button>
            </>
          ) : (
            <Button onClick={onRecover || (() => window.location.reload())}>
              <RefreshCw className="h-4 w-4 mr-1" /> Reload App
            </Button>
          )}
        </div>

        {submitted && (
          <div className="rounded-md bg-green-50 dark:bg-green-950 p-3 text-sm text-green-700 dark:text-green-300">
            Crash report sent. Your tracking number has been saved locally.
          </div>
        )}
      </div>
    </div>
  );
}
