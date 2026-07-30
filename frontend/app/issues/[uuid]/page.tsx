'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Bug, Clock, Copy, ExternalLink, Flag, GitBranch, GitMerge, Loader2, MessageSquare, Shield, Siren, Trash2 } from 'lucide-react';
import { toast } from 'sonner';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { Textarea } from '@/components/ui/textarea';
import { fetchIssue, fetchTimeline, updateIssue, markSpam } from '@/lib/api/issues';
import { logClientError } from '@/lib/client-logger';
import type { IssueDetail, IssueStatus, TimelineEvent } from '@/lib/api/types';

const STATUS_OPTIONS: IssueStatus[] = [
  'new', 'triaged', 'acknowledged', 'in_progress', 'needs_info',
  'resolved', 'closed', 'wont_fix',
];

const STATUS_BADGE: Record<string, string> = {
  new: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
  triaged: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300',
  acknowledged: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
  in_progress: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300',
  needs_info: 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300',
  resolved: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
  closed: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
  wont_fix: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
  duplicate: 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300',
  spam: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
};

const EVENT_ICONS: Record<string, React.ReactNode> = {
  created: <Bug className="h-3 w-3" />,
  updated: <GitBranch className="h-3 w-3" />,
  marked_spam: <Flag className="h-3 w-3" />,
  marked_duplicate: <GitMerge className="h-3 w-3" />,
};

export default function IssueDetailPage() {
  const params = useParams();
  const router = useRouter();
  const uuid = params.uuid as string;

  const [issue, setIssue] = useState<IssueDetail | null>(null);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<IssueStatus>('new');
  const [updating, setUpdating] = useState(false);

  const loadIssue = useCallback(async () => {
    try {
      const [issueData, timelineData] = await Promise.all([
        fetchIssue(uuid),
        fetchTimeline(uuid),
      ]);
      setIssue(issueData);
      setTimeline(timelineData);
      setStatus(issueData.status as IssueStatus);
    } catch (error) {
      logClientError('Failed to load issue', error);
      toast.error('Issue not found');
      router.push('/issues');
    } finally {
      setLoading(false);
    }
  }, [uuid, router]);

  useEffect(() => { loadIssue(); }, [loadIssue]);

  const handleStatusChange = useCallback(async (newStatus: IssueStatus) => {
    setUpdating(true);
    try {
      const updated = await updateIssue(uuid, { status: newStatus });
      setStatus(updated.status as IssueStatus);
      setIssue(updated);
      toast.success(`Status changed to ${newStatus.replace(/_/g, ' ')}`);
      loadIssue();
    } catch (error) {
      logClientError('Status update failed', error);
      toast.error('Failed to update status');
    } finally {
      setUpdating(false);
    }
  }, [uuid, loadIssue]);

  const handleMarkSpam = useCallback(async () => {
    if (!confirm('Mark this issue as spam?')) return;
    setUpdating(true);
    try {
      await markSpam(uuid);
      toast.success('Marked as spam');
      loadIssue();
    } catch (error) {
      logClientError('Spam mark failed', error);
      toast.error('Failed to mark as spam');
    } finally {
      setUpdating(false);
    }
  }, [uuid, loadIssue]);

  if (loading) {
    return (
      <div className="min-h-screen bg-background p-6 max-w-4xl mx-auto space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-4 w-96" />
        <Skeleton className="h-64 rounded-lg" />
      </div>
    );
  }

  if (!issue) return null;

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-4xl mx-auto p-4 sm:p-6 space-y-6">
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" onClick={() => router.push('/issues')}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold">{issue.title}</h1>
              {issue.isSpam && <Badge variant="destructive">Spam</Badge>}
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <code className="text-xs bg-muted px-1 py-0.5 rounded">{issue.trackingNumber}</code>
              <Button
                variant="ghost"
                size="icon"
                className="h-4 w-4"
                onClick={() => {
                  navigator.clipboard.writeText(issue.trackingNumber);
                  toast.success('Copied');
                }}
              >
                <Copy className="h-3 w-3" />
              </Button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <Card>
              <CardHeader><CardTitle className="text-sm">Description</CardTitle></CardHeader>
              <CardContent>
                <p className="whitespace-pre-wrap text-sm">{issue.description}</p>
              </CardContent>
            </Card>

            {issue.stepsToReproduce && (
              <Card>
                <CardHeader><CardTitle className="text-sm">Steps to Reproduce</CardTitle></CardHeader>
                <CardContent>
                  <p className="whitespace-pre-wrap text-sm">{issue.stepsToReproduce}</p>
                </CardContent>
              </Card>
            )}

            {issue.aiSummary && (
              <Card>
                <CardHeader><CardTitle className="text-sm">AI Summary</CardTitle></CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">{issue.aiSummary}</p>
                  {issue.aiSuggestedFix && (
                    <div className="mt-2 rounded-md bg-green-50 dark:bg-green-950 p-3 text-sm">
                      <strong>Suggested Fix:</strong> {issue.aiSuggestedFix}
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            <Card>
              <CardHeader><CardTitle className="text-sm">Timeline</CardTitle></CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {timeline.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No timeline events</p>
                  ) : (
                    timeline.map((event, i) => (
                      <div key={i} className="flex gap-3 text-sm">
                        <div className="mt-0.5 text-muted-foreground">
                          {EVENT_ICONS[event.eventType] || <Clock className="h-3 w-3" />}
                        </div>
                        <div className="flex-1">
                          <p>{event.description}</p>
                          <p className="text-xs text-muted-foreground">
                            {event.actor && `by ${event.actor} · `}
                            {new Date(event.createdAt).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-4">
            <Card>
              <CardHeader><CardTitle className="text-sm">Details</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Type</span>
                  <Badge variant="outline" className="capitalize">{issue.issueType.replace(/_/g, ' ')}</Badge>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Severity</span>
                  <span className="capitalize font-medium">{issue.severity}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Priority</span>
                  <span className="capitalize font-medium">{issue.priority}</span>
                </div>
                <div className="flex justify-between text-sm items-center">
                  <span className="text-muted-foreground">Status</span>
                  <Select
                    value={status}
                    onValueChange={(v) => handleStatusChange(v as IssueStatus)}
                    disabled={updating || issue.isSpam}
                  >
                    <SelectTrigger className="w-full h-8 text-xs">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {STATUS_OPTIONS.map((s) => (
                        <SelectItem key={s} value={s} className="capitalize">
                          {s.replace(/_/g, ' ')}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {issue.assignee && (
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Assignee</span>
                    <span>{issue.assignee}</span>
                  </div>
                )}

                {issue.category && (
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Category</span>
                    <span className="capitalize">{issue.category}</span>
                  </div>
                )}
              </CardContent>
            </Card>

            {(issue.githubIssueUrl || issue.githubDiscussionUrl) && (
              <Card>
                <CardHeader><CardTitle className="text-sm">GitHub</CardTitle></CardHeader>
                <CardContent className="space-y-2">
                  {issue.githubIssueUrl && (
                    <a href={issue.githubIssueUrl} target="_blank" rel="noopener noreferrer"
                      className="flex items-center gap-2 text-sm text-blue-600 hover:underline">
                      <ExternalLink className="h-3 w-3" />
                      Issue #{issue.githubIssueNumber}
                    </a>
                  )}
                  {issue.githubDiscussionUrl && (
                    <a href={issue.githubDiscussionUrl} target="_blank" rel="noopener noreferrer"
                      className="flex items-center gap-2 text-sm text-blue-600 hover:underline">
                      <MessageSquare className="h-3 w-3" />
                      Discussion
                    </a>
                  )}
                </CardContent>
              </Card>
            )}

            {issue.slaResponseAt && (
              <Card>
                <CardHeader><CardTitle className="text-sm">SLA</CardTitle></CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Response by</span>
                    <span>{new Date(issue.slaResponseAt).toLocaleDateString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Resolution by</span>
                    <span>{new Date(issue.slaResolutionAt).toLocaleDateString()}</span>
                  </div>
                </CardContent>
              </Card>
            )}

            {!issue.isSpam && (
              <Button variant="outline" size="sm" className="w-full text-red-500" onClick={handleMarkSpam}>
                <Flag className="h-4 w-4 mr-1" /> Mark as Spam
              </Button>
            )}

            {issue.createdAt && (
              <p className="text-xs text-muted-foreground text-center">
                Created {new Date(issue.createdAt).toLocaleString()}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
