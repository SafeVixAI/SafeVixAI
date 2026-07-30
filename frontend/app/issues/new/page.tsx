'use client';

import { IssueForm } from '@/components/issues/IssueForm';

export default function NewIssuePage() {
  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-3xl mx-auto p-4 sm:p-6 space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">New Issue Report</h1>
          <p className="text-muted-foreground text-sm">
            Submit a bug report, feature request, or general feedback
          </p>
        </div>
        <IssueForm />
      </div>
    </div>
  );
}
