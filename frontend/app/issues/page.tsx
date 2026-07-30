'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { AlertTriangle, BarChart3, Bug, CheckCircle2, Clock, Copy, Filter, Plus, Search, Shield, Siren, SlidersHorizontal } from 'lucide-react';
import { toast } from 'sonner';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { fetchIssueStats, fetchIssues } from '@/lib/api/issues';
import { logClientError } from '@/lib/client-logger';
import type { IssueListItem, IssueStatsResponse, IssueStatus } from '@/lib/api/types';

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

const SEVERITY_ICON: Record<string, React.ReactNode> = {
  critical: <Siren className="h-4 w-4 text-red-500" />,
  high: <AlertTriangle className="h-4 w-4 text-orange-500" />,
  medium: <AlertTriangle className="h-4 w-4 text-yellow-500" />,
  low: <CheckCircle2 className="h-4 w-4 text-green-500" />,
  cosmetic: <CheckCircle2 className="h-4 w-4 text-gray-400" />,
};

export default function IssuesDashboardPage() {
  const [issues, setIssues] = useState<IssueListItem[]>([]);
  const [stats, setStats] = useState<IssueStatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [typeFilter, setTypeFilter] = useState<string>('');

  const loadIssues = useCallback(async () => {
    setLoading(true);
    try {
      const [issuesData, statsData] = await Promise.all([
        fetchIssues({
          page,
          pageSize: 20,
          status: statusFilter || undefined,
          issueType: typeFilter || undefined,
          search: search || undefined,
        }),
        fetchIssueStats(),
      ]);
      setIssues(issuesData.items);
      setTotalPages(issuesData.totalPages);
      setStats(statsData);
    } catch (error) {
      logClientError('Failed to load issues', error);
      toast.error('Failed to load issues');
    } finally {
      setLoading(false);
    }
  }, [page, statusFilter, typeFilter, search]);

  useEffect(() => { loadIssues(); }, [loadIssues]);

  const copyTracking = (tn: string) => {
    navigator.clipboard.writeText(tn);
    toast.success('Tracking number copied');
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto p-4 sm:p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Issue Reports</h1>
            <p className="text-muted-foreground text-sm">Manage bug reports, feature requests, and feedback</p>
          </div>
          <Link href="/issues/new">
            <Button>
              <Plus className="h-4 w-4 mr-1" /> New Issue
            </Button>
          </Link>
        </div>

        <Tabs defaultValue="dashboard">
          <TabsList>
            <TabsTrigger value="dashboard"><BarChart3 className="h-4 w-4 mr-1" /> Dashboard</TabsTrigger>
            <TabsTrigger value="list"><Filter className="h-4 w-4 mr-1" /> All Issues</TabsTrigger>
          </TabsList>

          <TabsContent value="dashboard" className="space-y-4 mt-4">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {stats ? (
                <>
                  <StatCard title="Total Issues" value={stats.total} icon={<Bug className="h-4 w-4" />} />
                  <StatCard title="Open" value={stats.openCount} icon={<Clock className="h-4 w-4" />} />
                  <StatCard title="Resolved" value={stats.resolvedCount} icon={<CheckCircle2 className="h-4 w-4" />} />
                  <StatCard title="SLA Breaches" value={stats.slaBreachCount} icon={<AlertTriangle className="h-4 w-4" />} />
                </>
              ) : (
                Array.from({ length: 4 }).map((_, i) => (
                  <Skeleton key={i} className="h-24 rounded-lg" />
                ))
              )}
            </div>

            {stats && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Card>
                  <CardHeader><CardTitle className="text-sm">By Type</CardTitle></CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {Object.entries(stats.byType).map(([type, count]) => (
                        <div key={type} className="flex justify-between text-sm">
                          <span className="capitalize">{type.replace(/_/g, ' ')}</span>
                          <span className="font-medium">{count}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader><CardTitle className="text-sm">By Severity</CardTitle></CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {Object.entries(stats.bySeverity).map(([sev, count]) => (
                        <div key={sev} className="flex justify-between text-sm">
                          <span className="flex items-center gap-1 capitalize">
                            {SEVERITY_ICON[sev] || null} {sev}
                          </span>
                          <span className="font-medium">{count}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </TabsContent>

          <TabsContent value="list" className="space-y-4 mt-4">
            <div className="flex flex-wrap gap-3">
              <div className="relative flex-1 min-w-[200px]">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search issues..."
                  value={search}
                  onChange={(e) => { setSearch(e.target.value); setPage(1); }}
                  className="pl-9"
                />
              </div>
              <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v); setPage(1); }}>
                <SelectTrigger className="w-[140px]">
                  <SlidersHorizontal className="h-4 w-4 mr-1" />
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Statuses</SelectItem>
                  <SelectItem value="new">New</SelectItem>
                  <SelectItem value="triaged">Triaged</SelectItem>
                  <SelectItem value="in_progress">In Progress</SelectItem>
                  <SelectItem value="resolved">Resolved</SelectItem>
                  <SelectItem value="closed">Closed</SelectItem>
                </SelectContent>
              </Select>
              <Select value={typeFilter} onValueChange={(v) => { setTypeFilter(v); setPage(1); }}>
                <SelectTrigger className="w-[140px]">
                  <SelectValue placeholder="Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Types</SelectItem>
                  <SelectItem value="bug">Bug</SelectItem>
                  <SelectItem value="feature_request">Feature</SelectItem>
                  <SelectItem value="feedback">Feedback</SelectItem>
                  <SelectItem value="crash">Crash</SelectItem>
                  <SelectItem value="security">Security</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Tracking</TableHead>
                      <TableHead>Title</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Severity</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Assignee</TableHead>
                      <TableHead>Created</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {loading ? (
                      Array.from({ length: 5 }).map((_, i) => (
                        <TableRow key={i}>
                          {Array.from({ length: 7 }).map((_, j) => (
                            <TableCell key={j}><Skeleton className="h-4 w-full" /></TableCell>
                          ))}
                        </TableRow>
                      ))
                    ) : issues.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                          No issues found. <Link href="/issues/new" className="underline">Create one</Link>
                        </TableCell>
                      </TableRow>
                    ) : (
                      issues.map((issue) => (
                        <TableRow key={issue.uuid}>
                          <TableCell>
                            <code className="text-xs flex items-center gap-1">
                              {issue.trackingNumber}
                              <button onClick={() => copyTracking(issue.trackingNumber)} className="hover:text-primary">
                                <Copy className="h-3 w-3" />
                              </button>
                            </code>
                          </TableCell>
                          <TableCell>
                            <Link href={`/issues/${issue.uuid}`} className="hover:underline font-medium">
                              {issue.title}
                            </Link>
                          </TableCell>
                          <TableCell className="capitalize text-sm">{issue.issueType.replace(/_/g, ' ')}</TableCell>
                          <TableCell>
                            <span className="flex items-center gap-1 text-sm">
                              {SEVERITY_ICON[issue.severity] || null}
                              {issue.severity}
                            </span>
                          </TableCell>
                          <TableCell>
                            <Badge className={`text-xs ${STATUS_BADGE[issue.status] || ''}`}>
                              {issue.status.replace(/_/g, ' ')}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-sm">{issue.assignee || '-'}</TableCell>
                          <TableCell className="text-sm text-muted-foreground">
                            {new Date(issue.createdAt).toLocaleDateString()}
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>

            {totalPages > 1 && (
              <div className="flex justify-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                >
                  Previous
                </Button>
                <span className="text-sm text-muted-foreground py-1">
                  Page {page} of {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                </Button>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

function StatCard({ title, value, icon }: { title: string; value: number; icon: React.ReactNode }) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">{title}</p>
            <p className="text-2xl font-bold">{value}</p>
          </div>
          <div className="rounded-full bg-muted p-2">{icon}</div>
        </div>
      </CardContent>
    </Card>
  );
}
