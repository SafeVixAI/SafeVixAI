'use client';

import { useCallback, useState } from 'react';
import { AlertTriangle, Bug, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { logClientError } from '@/lib/client-logger';

export interface ErrorInfo {
  error: Error;
  errorInfo?: Record<string, unknown>;
  componentStack?: string;
}

interface ErrorDialogProps {
  errorInfo: ErrorInfo | null;
  onClose: () => void;
  onRecover?: () => void;
}

export function ErrorDialog({ errorInfo, onClose, onRecover }: ErrorDialogProps) {
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleReport = useCallback(async () => {
    setIsSubmitting(true);
    try {
      const { createIssue } = await import('@/lib/api/issues');
      const browserInfo = {
        userAgent: navigator.userAgent,
        url: window.location.href,
        timestamp: new Date().toISOString(),
        viewport: `${window.innerWidth}x${window.innerHeight}`,
      };

      await createIssue({
        issueType: 'crash',
        severity: errorInfo?.error?.message?.includes('timeout') ? 'medium' : 'high',
        title: `Error: ${errorInfo?.error?.message?.slice(0, 100) || 'Unknown error'}`,
        description: description || errorInfo?.error?.message || 'No details provided',
        stepsToReproduce: errorInfo?.componentStack
          ? `Component stack:\n${errorInfo.componentStack}`
          : null,
        logs: {
          errorMessage: errorInfo?.error?.message,
          errorName: errorInfo?.error?.name,
          errorStack: errorInfo?.error?.stack,
        },
        browserInfo,
      });
      setSubmitted(true);
      toast.success('Error report submitted');
    } catch (error) {
      logClientError('Error report submission failed', error);
      toast.error('Could not submit report. Logged locally.');
    } finally {
      setIsSubmitting(false);
    }
  }, [errorInfo, description]);

  const handleRefresh = useCallback(() => {
    onRecover?.();
    window.location.reload();
  }, [onRecover]);

  if (!errorInfo) return null;

  return (
    <Dialog open={!!errorInfo} onOpenChange={() => onClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-destructive" />
            Something went wrong
          </DialogTitle>
          <DialogDescription>
            An unexpected error occurred. You can help us fix it by reporting the details below.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="rounded-md bg-muted p-3 font-mono text-xs overflow-auto max-h-24">
            {errorInfo.error?.message || 'Unknown error'}
          </div>

          {!submitted && (
            <div>
              <label className="text-sm font-medium mb-1 block">
                What were you doing? (optional)
              </label>
              <Textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Tell us what happened..."
                rows={2}
              />
            </div>
          )}

          {submitted && (
            <div className="rounded-md bg-green-50 dark:bg-green-950 p-3 text-sm text-green-700 dark:text-green-300">
              Thank you! Your report has been submitted. Our team will investigate.
            </div>
          )}
        </div>

        <DialogFooter className="gap-2">
          {!submitted && (
            <Button variant="outline" onClick={handleRefresh}>
              <RefreshCw className="h-4 w-4 mr-1" /> Reload Page
            </Button>
          )}
          {!submitted && (
            <Button onClick={handleReport} disabled={isSubmitting}>
              <Bug className="h-4 w-4 mr-1" />
              {isSubmitting ? 'Submitting...' : 'Report Issue'}
            </Button>
          )}
          {submitted && (
            <Button onClick={handleRefresh}>
              <RefreshCw className="h-4 w-4 mr-1" /> Reload Page
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
