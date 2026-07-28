// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
//
// CLI Update Command - SafeVixAI update management from the terminal
// Usage: node scripts/update.mjs <command> [options]
//
// Commands:
//   status              Show current version, latest, channel, last checked
//   check               Force check for updates
//   history [--limit N] Show installation history
//   channels            List available channels with version counts
//   apply <version>     Trigger download + install (if backend supports)

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

function die(msg, code) {
  console.error('Error:', msg);
  process.exit(code || 1);
}

async function fetchJson(url, options) {
  const resp = await fetch(url, {
    headers: { 'Accept': 'application/json' },
    ...options,
    signal: AbortSignal.timeout(10000),
  });
  if (!resp.ok) {
    const body = await resp.text().catch(() => '');
    die(`HTTP ${resp.status} ${resp.statusText}: ${body.substring(0, 200)}`);
  }
  return await resp.json();
}

async function cmdStatus() {
  const [version, releases] = await Promise.all([
    fetchJson(`${BACKEND_URL}/api/v1/updates/version`).catch(() => ({ version: 'unknown' })),
    fetchJson(`${BACKEND_URL}/api/v1/updates/releases?limit=1`).catch(() => ({ releases: [] })),
  ]);
  const latest = releases.releases?.[0];
  console.log('SafeVixAI Update Status');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━');
  console.log(`Current version: ${version.version || 'unknown'}`);
  console.log(`Latest version:  ${latest?.version || 'N/A'}`);
  console.log(`Channel:         ${version.channel || 'stable'}`);
  console.log(`Update available: ${latest?.version && latest.version !== version.version ? 'YES' : 'No'}`);
  console.log(`Last checked:    ${version.last_checked_at || 'never'}`);
}

async function cmdCheck() {
  const result = await fetchJson(`${BACKEND_URL}/api/v1/updates/check`, { method: 'POST' });
  console.log('Update Check Result');
  console.log('━━━━━━━━━━━━━━━━━━━');
  console.log(`Latest version:   ${result.latest_version}`);
  console.log(`Update available: ${result.update_available ? 'YES' : 'No'}`);
  console.log(`Mandatory:        ${result.is_mandatory ? 'Yes' : 'No'}`);
  console.log(`Security update:  ${result.is_security ? 'Yes' : 'No'}`);
  console.log(`Current version:  ${result.current_version}`);
  if (result.update_available) {
    console.log(`\nRun: node scripts/update.mjs apply ${result.latest_version}`);
  }
}

async function cmdHistory(args) {
  const limitIdx = args.indexOf('--limit');
  const limit = limitIdx >= 0 ? parseInt(args[limitIdx + 1], 10) || 10 : 10;
  const data = await fetchJson(`${BACKEND_URL}/api/v1/updates/history?limit=${limit}`);
  console.log(`Installation History (last ${limit})`);
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  if (!data.installations?.length) {
    console.log('No installation history found.');
    return;
  }
  for (const inst of data.installations) {
    console.log(`${inst.version}  ${inst.status}  ${inst.installed_at || ''}  ${inst.channel || ''}`);
  }
}

async function cmdChannels() {
  const data = await fetchJson(`${BACKEND_URL}/api/v1/updates/channels`);
  console.log('Available Channels');
  console.log('━━━━━━━━━━━━━━━━━━━');
  if (!data.channels?.length) {
    console.log('No channels configured.');
    return;
  }
  for (const ch of data.channels) {
    const versions = ch.version_count !== undefined ? ` (${ch.version_count} versions)` : '';
    console.log(`  ${ch.name.padEnd(12)} ${ch.description || ''}${versions}`);
  }
}

async function cmdApply(version) {
  if (!version) die('Usage: node scripts/update.mjs apply <version>');
  console.log(`Triggering download + install for version ${version}...`);
  const result = await fetchJson(`${BACKEND_URL}/api/v1/updates/apply`, {
    method: 'POST',
    body: JSON.stringify({ version }),
    headers: { 'Content-Type': 'application/json' },
  });
  console.log('Update initiated:', result.status || 'OK');
  console.log('Check status with: node scripts/update.mjs status');
}

async function main() {
  const args = process.argv.slice(2);
  const cmd = args[0];

  switch (cmd) {
    case 'status':   return await cmdStatus();
    case 'check':    return await cmdCheck();
    case 'history':  return await cmdHistory(args.slice(1));
    case 'channels': return await cmdChannels();
    case 'apply':    return await cmdApply(args[1]);
    default:
      console.log('SafeVixAI Update CLI');
      console.log('');
      console.log('Commands:');
      console.log('  status              Show current version + latest available');
      console.log('  check               Force check for updates');
      console.log('  history [--limit N] Show installation history');
      console.log('  channels            List available channels');
      console.log('  apply <version>     Trigger download + install');
      console.log('');
      console.log('Environment:');
      console.log('  BACKEND_URL   Backend API base URL (default: http://localhost:8000)');
      process.exit(1);
  }
}

main().catch((err) => die(err.message, 1));
