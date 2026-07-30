'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Bug, Camera, Lightbulb, Loader2, MessageSquare, Send, Shield, Siren } from 'lucide-react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { logClientError } from '@/lib/client-logger';
import { useAppStore } from '@/lib/store';
import type { IssueType, IssueSeverity, IssuePriority } from '@/lib/api/types';
import { createIssue } from '@/lib/api/issues';

const ISSUE_TYPE_OPTIONS: Array<{ value: IssueType; label: string; icon: React.ReactNode }> = [
  { value: 'bug', label: 'Bug Report', icon: <Bug className="h-4 w-4" /> },
  { value: 'feature_request', label: 'Feature Request', icon: <Lightbulb className="h-4 w-4" /> },
  { value: 'feedback', label: 'General Feedback', icon: <MessageSquare className="h-4 w-4" /> },
  { value: 'performance', label: 'Performance Issue', icon: <Siren className="h-4 w-4" /> },
  { value: 'security', label: 'Security Report', icon: <Shield className="h-4 w-4" /> },
  { value: 'crash', label: 'Crash Report', icon: <Siren className="h-4 w-4" /> },
  { value: 'ai_feedback', label: 'AI Feedback', icon: <Lightbulb className="h-4 w-4" /> },
];

interface IssueFormProps {
  onSuccess?: (trackingNumber: string) => void;
  prefilledType?: IssueType;
}

export function IssueForm({ onSuccess, prefilledType }: IssueFormProps) {
  const router = useRouter();
  const [issueType, setIssueType] = useState<IssueType>(prefilledType || 'bug');
  const [severity, setSeverity] = useState<IssueSeverity>('medium');
  const [priority, setPriority] = useState<IssuePriority>('normal');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [stepsToReproduce, setStepsToReproduce] = useState('');
  const [expectedBehavior, setExpectedBehavior] = useState('');
  const [actualBehavior, setActualBehavior] = useState('');
  const [environment, setEnvironment] = useState('');
  const [labels, setLabels] = useState('');
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [reporterName, setReporterName] = useState('');
  const [reporterEmail, setReporterEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [screenshotUrls, setScreenshotUrls] = useState<string[]>([]);

  const user = useAppStore((s) => s.authToken);
  const userProfile = useAppStore((s) => s.userProfile);

  useEffect(() => {
    if (user && userProfile) {
      setReporterName(userProfile.displayName || userProfile.name || '');
      setReporterEmail(userProfile.email || '');
    }
  }, [user, userProfile]);

  const handleCaptureScreenshot = useCallback(() => {
    const canvas = document.createElement('canvas');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.fillStyle = '#1a1a2e';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#e0e0e0';
    ctx.font = '14px monospace';
    ctx.fillText(window.location.href, 20, 40);
    ctx.fillText(new Date().toISOString(), 20, 65);
    const dataUrl = canvas.toDataURL('image/png');
    setScreenshotUrls((prev) => [...prev, dataUrl]);
    toast.success('Screenshot captured');
  }, []);

  const handleSubmit = useCallback(async () => {
    if (!title.trim()) { toast.error('Title is required'); return; }
    if (!description.trim()) { toast.error('Description is required'); return; }

    setIsSubmitting(true);
    try {
      const result = await createIssue({
        issueType,
        severity,
        priority,
        title: title.trim(),
        description: description.trim(),
        stepsToReproduce: stepsToReproduce || undefined,
        expectedBehavior: expectedBehavior || undefined,
        actualBehavior: actualBehavior || undefined,
        environment: environment || undefined,
        labels: labels ? labels.split(',').map((l) => l.trim()).filter(Boolean) : undefined,
        screenshotUrls: screenshotUrls.length > 0 ? screenshotUrls : undefined,
        browserInfo: { userAgent: navigator.userAgent, url: window.location.href },
        isAnonymous: isAnonymous || !user,
        reporterName: isAnonymous ? undefined : reporterName || undefined,
        reporterEmail: isAnonymous ? undefined : reporterEmail || undefined,
      });

      toast.success(`Issue submitted! Tracking: ${result.trackingNumber}`);
      onSuccess?.(result.trackingNumber);
      router.push(`/issues/${result.uuid}`);
    } catch (error) {
      logClientError('Issue submission failed', error);
      toast.error('Failed to submit issue. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  }, [
    issueType, severity, priority, title, description,
    stepsToReproduce, expectedBehavior, actualBehavior, environment,
    labels, screenshotUrls, isAnonymous, user, reporterName, reporterEmail,
    onSuccess, router,
  ]);

  return (
    <div className="space-y-6">
      <div>
        <Label>Issue Type</Label>
        <RadioGroup
          value={issueType}
          onValueChange={(v) => setIssueType(v as IssueType)}
          className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-1"
        >
          {ISSUE_TYPE_OPTIONS.map((opt) => (
            <Label
              key={opt.value}
              className="flex items-center gap-2 rounded-lg border p-2 text-xs cursor-pointer has-[[data-state=checked]]:border-primary hover:bg-accent"
            >
              <RadioGroupItem value={opt.value} className="sr-only" />
              {opt.icon}
              {opt.label}
            </Label>
          ))}
        </RadioGroup>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="severity">Severity</Label>
          <Select value={severity} onValueChange={(v) => setSeverity(v as IssueSeverity)}>
            <SelectTrigger id="severity"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="critical">Critical</SelectItem>
              <SelectItem value="high">High</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
              <SelectItem value="low">Low</SelectItem>
              <SelectItem value="cosmetic">Cosmetic</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label htmlFor="priority">Priority</Label>
          <Select value={priority} onValueChange={(v) => setPriority(v as IssuePriority)}>
            <SelectTrigger id="priority"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="urgent">Urgent</SelectItem>
              <SelectItem value="high">High</SelectItem>
              <SelectItem value="normal">Normal</SelectItem>
              <SelectItem value="low">Low</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div>
        <Label htmlFor="title">Title</Label>
        <Input
          id="title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Brief summary of the issue"
        />
      </div>

      <div>
        <Label htmlFor="description">Description</Label>
        <Textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Detailed description of the issue..."
          rows={5}
        />
      </div>

      <div>
        <Label htmlFor="steps">Steps to Reproduce</Label>
        <Textarea
          id="steps"
          value={stepsToReproduce}
          onChange={(e) => setStepsToReproduce(e.target.value)}
          placeholder="1. Go to... 2. Click... 3. See error..."
          rows={3}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="expected">Expected Behavior</Label>
          <Textarea
            id="expected"
            value={expectedBehavior}
            onChange={(e) => setExpectedBehavior(e.target.value)}
            placeholder="What should happen?"
            rows={2}
          />
        </div>
        <div>
          <Label htmlFor="actual">Actual Behavior</Label>
          <Textarea
            id="actual"
            value={actualBehavior}
            onChange={(e) => setActualBehavior(e.target.value)}
            placeholder="What actually happened?"
            rows={2}
          />
        </div>
      </div>

      <div>
        <Label htmlFor="environment">Environment</Label>
        <Input
          id="environment"
          value={environment}
          onChange={(e) => setEnvironment(e.target.value)}
          placeholder="e.g., Chrome 120, Windows 11, app v2.1.0"
        />
      </div>

      <div>
        <Label htmlFor="labels">Labels (comma-separated)</Label>
        <Input
          id="labels"
          value={labels}
          onChange={(e) => setLabels(e.target.value)}
          placeholder="frontend, ui, mobile"
        />
      </div>

      <div className="flex items-center gap-4">
        <Button type="button" variant="outline" size="sm" onClick={handleCaptureScreenshot}>
          <Camera className="h-4 w-4 mr-1" /> Capture Screenshot
        </Button>
        {screenshotUrls.length > 0 && (
          <span className="text-xs text-muted-foreground">
            {screenshotUrls.length} screenshot{screenshotUrls.length > 1 ? 's' : ''} captured
          </span>
        )}
      </div>

      {!user && (
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="anonymous"
            checked={isAnonymous}
            onChange={(e) => setIsAnonymous(e.target.checked)}
            className="rounded border-gray-300"
          />
          <Label htmlFor="anonymous" className="text-sm">Submit anonymously</Label>
        </div>
      )}

      <div className="flex gap-2 justify-end">
        <Button variant="outline" onClick={() => router.back()}>Cancel</Button>
        <Button onClick={handleSubmit} disabled={isSubmitting}>
          {isSubmitting ? <Loader2 className="h-4 w-4 mr-1 animate-spin" /> : <Send className="h-4 w-4 mr-1" />}
          {isSubmitting ? 'Submitting...' : 'Submit Issue'}
        </Button>
      </div>
    </div>
  );
}
