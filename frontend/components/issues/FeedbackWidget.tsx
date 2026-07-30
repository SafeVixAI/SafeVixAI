'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { AlertTriangle, Bug, Camera, Lightbulb, MessageSquare, X } from 'lucide-react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Textarea } from '@/components/ui/textarea';
import { logClientError } from '@/lib/client-logger';

interface FeedbackWidgetProps {
  screenshotMode?: boolean;
  onScreenshotCapture?: (dataUrl: string) => void;
}

type FeedbackType = 'bug' | 'feature' | 'feedback' | 'performance';

const FEEDBACK_TYPES: Array<{ value: FeedbackType; label: string; icon: React.ReactNode }> = [
  { value: 'bug', label: 'Bug Report', icon: <Bug className="h-4 w-4" /> },
  { value: 'feature', label: 'Feature Request', icon: <Lightbulb className="h-4 w-4" /> },
  { value: 'feedback', label: 'General Feedback', icon: <MessageSquare className="h-4 w-4" /> },
  { value: 'performance', label: 'Performance Issue', icon: <AlertTriangle className="h-4 w-4" /> },
];

export function FeedbackWidget({ screenshotMode, onScreenshotCapture }: FeedbackWidgetProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [feedbackType, setFeedbackType] = useState<FeedbackType>('feedback');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [screenshot, setScreenshot] = useState<string | null>(null);
  const widgetRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (widgetRef.current && !widgetRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  const handleCaptureScreenshot = useCallback(() => {
    try {
      const canvas = document.createElement('canvas');
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      ctx.fillStyle = '#1a1a2e';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = '#e0e0e0';
      ctx.font = '16px monospace';
      ctx.fillText('Screenshot captured at ' + new Date().toLocaleTimeString(), 20, 40);
      ctx.fillText('URL: ' + window.location.href, 20, 70);

      const dataUrl = canvas.toDataURL('image/png');
      setScreenshot(dataUrl);
      onScreenshotCapture?.(dataUrl);
      toast.success('Screenshot captured');
    } catch (error) {
      logClientError('Screenshot capture failed', error);
      toast.error('Failed to capture screenshot');
    }
  }, [onScreenshotCapture]);

  const handleSubmit = useCallback(async () => {
    if (!description.trim()) {
      toast.error('Please provide a description');
      return;
    }
    setIsSubmitting(true);
    try {
      const { createIssue } = await import('@/lib/api/issues');
      await createIssue({
        issueType: feedbackType === 'feature' ? 'feature_request' : feedbackType === 'feedback' ? 'feedback' : feedbackType === 'performance' ? 'performance' : 'bug',
        title: title || `${feedbackType}: ${description.slice(0, 50)}...`,
        description,
        screenshotUrls: screenshot ? [screenshot] : undefined,
        browserInfo: {
          userAgent: navigator.userAgent,
          language: navigator.language,
          platform: (navigator as any).platform,
          url: window.location.href,
        },
      });
      toast.success('Thank you for your feedback!');
      setIsOpen(false);
      setTitle('');
      setDescription('');
      setScreenshot(null);
    } catch (error) {
      logClientError('Feedback submission failed', error);
      toast.error('Failed to submit feedback. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  }, [feedbackType, title, description, screenshot]);

  if (screenshotMode) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
        <Card className="w-full max-w-md mx-4">
          <CardHeader>
            <CardTitle>Report Issue</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Label>Type</Label>
            <RadioGroup
              value={feedbackType}
              onValueChange={(v) => setFeedbackType(v as FeedbackType)}
              className="grid grid-cols-2 gap-2"
            >
              {FEEDBACK_TYPES.map((ft) => (
                <Label
                  key={ft.value}
                  className="flex items-center gap-2 rounded-lg border p-3 cursor-pointer has-[[data-state=checked]]:border-primary"
                >
                  <RadioGroupItem value={ft.value} className="sr-only" />
                  {ft.icon}
                  {ft.label}
                </Label>
              ))}
            </RadioGroup>
            <div>
              <Label htmlFor="desc">Description</Label>
              <Textarea
                id="desc"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe the issue..."
                rows={4}
              />
            </div>
            <div className="flex gap-2">
              <Button onClick={handleCaptureScreenshot} variant="outline" size="sm">
                <Camera className="h-4 w-4 mr-1" />
                {screenshot ? 'Re-capture' : 'Capture Screenshot'}
              </Button>
              {screenshot && (
                <Button onClick={() => setScreenshot(null)} variant="ghost" size="sm">
                  <X className="h-4 w-4 mr-1" /> Remove
                </Button>
              )}
            </div>
            {screenshot && (
              <img src={screenshot} alt="Screenshot preview" className="rounded border max-h-32" />
            )}
            <div className="flex gap-2 justify-end">
              <Button variant="outline" onClick={() => setIsOpen(false)}>Cancel</Button>
              <Button onClick={handleSubmit} disabled={isSubmitting}>
                {isSubmitting ? 'Submitting...' : 'Submit'}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <>
      {isOpen && (
        <div className="fixed inset-0 z-40 bg-black/30" />
      )}
      <div ref={widgetRef} className="fixed bottom-4 right-4 z-50">
        {isOpen ? (
          <Card className="w-80 sm:w-96 shadow-xl">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Send Feedback</CardTitle>
              <Button variant="ghost" size="icon" onClick={() => setIsOpen(false)}>
                <X className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardContent className="space-y-3">
              <RadioGroup
                value={feedbackType}
                onValueChange={(v) => setFeedbackType(v as FeedbackType)}
                className="grid grid-cols-2 gap-2"
              >
                {FEEDBACK_TYPES.map((ft) => (
                  <Label
                    key={ft.value}
                    className="flex items-center gap-2 rounded-lg border p-2 text-xs cursor-pointer has-[[data-state=checked]]:border-primary"
                  >
                    <RadioGroupItem value={ft.value} className="sr-only" />
                    {ft.icon}
                    {ft.label}
                  </Label>
                ))}
              </RadioGroup>
              <div>
                <Label htmlFor="widget-desc" className="text-xs">Description</Label>
                <Textarea
                  id="widget-desc"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe your feedback..."
                  rows={3}
                  className="text-sm"
                />
              </div>
              <div className="flex gap-2 justify-end">
                <Button variant="outline" size="sm" onClick={handleCaptureScreenshot}>
                  <Camera className="h-3 w-3 mr-1" /> Screenshot
                </Button>
                <Button size="sm" onClick={handleSubmit} disabled={isSubmitting}>
                  {isSubmitting ? 'Sending...' : 'Send'}
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          <Button
            className="rounded-full h-12 w-12 shadow-lg"
            onClick={() => setIsOpen(true)}
            title="Send Feedback"
          >
            <MessageSquare className="h-5 w-5" />
          </Button>
        )}
      </div>
    </>
  );
}
