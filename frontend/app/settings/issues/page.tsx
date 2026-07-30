'use client';

import { useCallback, useEffect, useState } from 'react';
import { Bell, Bug, ExternalLink, Globe, Mail, Save, Shield, Trash2 } from 'lucide-react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { logClientError } from '@/lib/client-logger';
import { useAppStore } from '@/lib/store';

interface IssueSettings {
  autoSubmitErrors: boolean;
  includeScreenshots: boolean;
  includeLogs: boolean;
  includeSystemInfo: boolean;
  anonymousByDefault: boolean;
  slackWebhook: string;
  discordWebhook: string;
  webhookUrl: string;
}

export default function IssuesSettingsPage() {
  const [settings, setSettings] = useState<IssueSettings>({
    autoSubmitErrors: true,
    includeScreenshots: true,
    includeLogs: true,
    includeSystemInfo: true,
    anonymousByDefault: false,
    slackWebhook: '',
    discordWebhook: '',
    webhookUrl: '',
  });
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    try {
      const stored = localStorage.getItem('issue-settings');
      if (stored) setSettings({ ...settings, ...JSON.parse(stored) });
    } catch { /* ignore */ }
  }, []);

  const saveSettings = useCallback(() => {
    try {
      localStorage.setItem('issue-settings', JSON.stringify(settings));
      setSaved(true);
      toast.success('Issue reporting settings saved');
      setTimeout(() => setSaved(false), 2000);
    } catch (error) {
      logClientError('Failed to save settings', error);
      toast.error('Failed to save settings');
    }
  }, [settings]);

  const clearCache = useCallback(() => {
    try {
      localStorage.removeItem('issue-settings');
      localStorage.removeItem('issue-drafts');
      setSettings({
        autoSubmitErrors: true,
        includeScreenshots: true,
        includeLogs: true,
        includeSystemInfo: true,
        anonymousByDefault: false,
        slackWebhook: '',
        discordWebhook: '',
        webhookUrl: '',
      });
      toast.success('Issue cache cleared');
    } catch (error) {
      logClientError('Failed to clear cache', error);
    }
  }, []);

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-3xl mx-auto p-4 sm:p-6 space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Issue Reporting Settings</h1>
          <p className="text-muted-foreground text-sm">
            Configure how issues and feedback are collected and reported
          </p>
        </div>

        <Tabs defaultValue="general">
          <TabsList>
            <TabsTrigger value="general"><Bug className="h-4 w-4 mr-1" /> General</TabsTrigger>
            <TabsTrigger value="notifications"><Bell className="h-4 w-4 mr-1" /> Notifications</TabsTrigger>
            <TabsTrigger value="privacy"><Shield className="h-4 w-4 mr-1" /> Privacy</TabsTrigger>
          </TabsList>

          <TabsContent value="general" className="space-y-4 mt-4">
            <Card>
              <CardHeader><CardTitle className="text-sm">Error Reporting</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Auto-submit Errors</Label>
                    <CardDescription>Automatically submit unhandled errors</CardDescription>
                  </div>
                  <Switch
                    checked={settings.autoSubmitErrors}
                    onCheckedChange={(v) => setSettings({ ...settings, autoSubmitErrors: v })}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Include Screenshots</Label>
                    <CardDescription>Capture screenshot with error reports</CardDescription>
                  </div>
                  <Switch
                    checked={settings.includeScreenshots}
                    onCheckedChange={(v) => setSettings({ ...settings, includeScreenshots: v })}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Include Logs</Label>
                    <CardDescription>Include console logs with reports</CardDescription>
                  </div>
                  <Switch
                    checked={settings.includeLogs}
                    onCheckedChange={(v) => setSettings({ ...settings, includeLogs: v })}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Include System Info</Label>
                    <CardDescription>Include browser and device information</CardDescription>
                  </div>
                  <Switch
                    checked={settings.includeSystemInfo}
                    onCheckedChange={(v) => setSettings({ ...settings, includeSystemInfo: v })}
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="notifications" className="space-y-4 mt-4">
            <Card>
              <CardHeader><CardTitle className="text-sm">Webhook Integration</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="slack">Slack Webhook URL</Label>
                  <Input
                    id="slack"
                    value={settings.slackWebhook}
                    onChange={(e) => setSettings({ ...settings, slackWebhook: e.target.value })}
                    placeholder="https://hooks.slack.com/services/..."
                  />
                </div>
                <div>
                  <Label htmlFor="discord">Discord Webhook URL</Label>
                  <Input
                    id="discord"
                    value={settings.discordWebhook}
                    onChange={(e) => setSettings({ ...settings, discordWebhook: e.target.value })}
                    placeholder="https://discord.com/api/webhooks/..."
                  />
                </div>
                <div>
                  <Label htmlFor="webhook">Custom Webhook URL</Label>
                  <Input
                    id="webhook"
                    value={settings.webhookUrl}
                    onChange={(e) => setSettings({ ...settings, webhookUrl: e.target.value })}
                    placeholder="https://example.com/webhook/issues"
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="privacy" className="space-y-4 mt-4">
            <Card>
              <CardHeader><CardTitle className="text-sm">Privacy Settings</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Anonymous by Default</Label>
                    <CardDescription>Submit issues anonymously unless you choose otherwise</CardDescription>
                  </div>
                  <Switch
                    checked={settings.anonymousByDefault}
                    onCheckedChange={(v) => setSettings({ ...settings, anonymousByDefault: v })}
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle className="text-sm">Data Management</CardTitle></CardHeader>
              <CardContent className="space-y-2">
                <Button variant="outline" size="sm" onClick={clearCache}>
                  <Trash2 className="h-4 w-4 mr-1" /> Clear Issue Cache & Drafts
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        <div className="flex justify-end">
          <Button onClick={saveSettings}>
            <Save className="h-4 w-4 mr-1" /> {saved ? 'Saved!' : 'Save Settings'}
          </Button>
        </div>
      </div>
    </div>
  );
}
