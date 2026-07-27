# Update Management — User Guide

## How Updates Work

SafeVixAI automatically checks for updates based on your configured schedule. When an update is found:
1. A banner appears at the top of the page
2. The dashboard widget shows the new version
3. You can choose to update now or dismiss (for non-mandatory updates)

## Release Channels

| Channel | Description | Use Case |
|---------|-------------|----------|
| Stable | Fully tested releases | Default for all users |
| Beta | Pre-release testing | Early adopters, testers |
| Nightly | Daily builds | Developers, contributors |
| Pre-release | Release candidates | QA team, staging |

## Installing Updates

### Via Web UI

1. Click **Update Now** on the banner or widget
2. Watch the progress bar fill as the download proceeds
3. Verification runs automatically (checksum + signature)
4. Click **Restart Now** to apply the update

### Via CLI

```bash
python scripts/safevixai_update.py check
python scripts/safevixai_update.py download 2.1.0
python scripts/safevixai_update.py install 2.1.0
```

## Understanding Badges

- **Mandatory** (red): You must install this update to continue using the app
- **Security** (amber): This update fixes a security vulnerability
- **Verified** (green, Shield icon): The update's checksum and signature passed verification

## Rollback

If an update causes issues:

1. Go to Settings -> Updates
2. Find the update in Recent Updates
3. The system auto-rolls back on failure
4. CLI: `python scripts/safevixai_update.py rollback`

## Offline Mode

1. Go to Settings -> Updates
2. Enable "Allow offline updates"
3. Download the bundle manually
4. The system applies it when connectivity is restored

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Update check fails | Check network connection, verify GitHub API access |
| Download fails | Auto-retry (3 attempts). Click Retry manually if needed |
| Install fails | Rollback to previous version automatically |
| Restart doesn't apply | Try manual restart via Settings page |
| Scheduler not running | Check `GET /api/v1/updates/scheduler/status` |

## FAQ

**Q: Will updates work offline?**
A: Updates are queued when offline and applied when connectivity returns.

**Q: Can I skip mandatory updates?**
A: No. Mandatory updates must be installed to continue using the app.

**Q: How do I change my update channel?**
A: Settings -> Updates -> Release Channel.

**Q: Is my data safe during updates?**
A: Yes. Updates only modify application code, not user data.
