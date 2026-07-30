# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""HTML email templates with dark mode support for enterprise notification channels."""

from __future__ import annotations

from typing import Any

from models.notification import NotificationCategory, NotificationPriority

DARK_MODE_CSS = """
  @media (prefers-color-scheme: dark) {
    body { background: #0f172a !important; }
    .container { background: #1e293b !important; box-shadow: 0 1px 3px rgba(0,0,0,0.4) !important; }
    .body { color: #e2e8f0 !important; }
    .body p, .body li { color: #e2e8f0 !important; }
    .footer { background: #1a1a2e !important; border-top-color: #334155 !important; color: #94a3b8 !important; }
    .footer a { color: #60a5fa !important; }
    .badge-critical { background: #450a0a !important; color: #fca5a5 !important; }
    .badge-high { background: #431407 !important; color: #fdba74 !important; }
    .badge-normal { background: #172554 !important; color: #93c5fd !important; }
    .badge-low { background: #1e293b !important; color: #cbd5e1 !important; }
    .meta { border-top-color: #334155 !important; color: #94a3b8 !important; }
    .summary { background: #172554 !important; }
    .summary .count { color: #60a5fa !important; }
    .summary .label { color: #94a3b8 !important; }
    table th { color: #94a3b8 !important; border-bottom-color: #334155 !important; }
    table td { color: #e2e8f0 !important; border-bottom-color: #334155 !important; }
    .header .category { color: rgba(255,255,255,0.7) !important; }
  }
"""


def _base_style(priority_color: str) -> str:
    return f"""
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; background: #f3f4f6; }}
  .container {{ max-width: 600px; margin: 24px auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
  .header {{ background: {priority_color}; padding: 24px 32px; }}
  .header h1 {{ color: #ffffff; margin: 0; font-size: 20px; font-weight: 600; }}
  .header .category {{ color: rgba(255,255,255,0.8); font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin-top: 4px; }}
  .body {{ padding: 32px; color: #1f2937; line-height: 1.6; }}
  .body p {{ margin: 0 0 16px; }}
  .footer {{ padding: 16px 32px; background: #f9fafb; border-top: 1px solid #e5e7eb; font-size: 12px; color: #9ca3af; text-align: center; }}
  .footer a {{ color: #2563eb; text-decoration: none; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }}
  .badge-critical {{ background: #fef2f2; color: #dc2626; }}
  .badge-high {{ background: #fff7ed; color: #ea580c; }}
  .badge-normal {{ background: #eff6ff; color: #2563eb; }}
  .badge-low {{ background: #f9fafb; color: #6b7280; }}
  .meta {{ margin-top: 16px; padding-top: 16px; border-top: 1px solid #e5e7eb; font-size: 13px; color: #6b7280; }}
  .meta-item {{ margin-bottom: 4px; }}
{DARK_MODE_CSS}"""


def _digest_style() -> str:
    return f"""
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; background: #f3f4f6; }}
  .container {{ max-width: 600px; margin: 24px auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
  .header {{ background: #1e40af; padding: 24px 32px; }}
  .header h1 {{ color: #ffffff; margin: 0; font-size: 20px; }}
  .header .subtitle {{ color: rgba(255,255,255,0.8); font-size: 13px; margin-top: 4px; }}
  .body {{ padding: 32px; }}
  .summary {{ background: #eff6ff; border-radius: 8px; padding: 16px; text-align: center; margin-bottom: 24px; }}
  .summary .count {{ font-size: 36px; font-weight: 700; color: #1e40af; }}
  .summary .label {{ font-size: 13px; color: #6b7280; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th {{ padding: 8px 12px; text-align: left; font-size: 12px; text-transform: uppercase; color: #9ca3af; border-bottom: 2px solid #e5e7eb; }}
  td {{ padding: 8px 12px; border-bottom: 1px solid #e5e7eb; color: #374151; }}
  .footer {{ padding: 16px 32px; background: #f9fafb; border-top: 1px solid #e5e7eb; font-size: 12px; color: #9ca3af; text-align: center; }}
{DARK_MODE_CSS}"""


def render_email_html(
    title: str,
    body: str | None,
    category: NotificationCategory | None,
    priority: NotificationPriority | None,
    metadata: dict[str, Any] | None = None,
) -> str:
    cat_label = category.value.replace('_', ' ').title() if category else 'Notification'
    priority_color = {
        NotificationPriority.CRITICAL: '#DC2626',
        NotificationPriority.HIGH: '#EA580C',
        NotificationPriority.NORMAL: '#2563EB',
        NotificationPriority.LOW: '#6B7280',
    }.get(priority, '#2563EB') if priority else '#2563EB'

    body_html = _render_body(body or '', metadata or {})

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>{_base_style(priority_color)}</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="category">{cat_label}</div>
    <h1>{title}</h1>
  </div>
  <div class="body">
    {body_html}
  </div>
  <div class="footer">
    <p>SafeVixAI Notification System &mdash; IIT Madras Road Safety Hackathon 2026</p>
    <p><a href="{{unsubscribe_url}}">Unsubscribe</a> &middot; <a href="{{preferences_url}}">Notification Preferences</a></p>
  </div>
</div>
</body>
</html>"""


def _render_body(body: str, metadata: dict[str, Any]) -> str:
    lines = body.split('\n')
    html_parts = []
    for line in lines:
        line = line.strip()
        if not line:
            html_parts.append('<br>')
        elif line.startswith('- '):
            html_parts.append(f'<li>{line[2:]}</li>')
        elif ':' in line and len(line) < 80:
            key, val = line.split(':', 1)
            html_parts.append(f'<p><strong>{key.strip()}:</strong> {val.strip()}</p>')
        else:
            html_parts.append(f'<p>{line}</p>')

    meta_html = ''
    if metadata:
        items = []
        for k, v in metadata.items():
            if isinstance(v, (str, int, float, bool)):
                items.append(f'<div class="meta-item"><strong>{k}:</strong> {v}</div>')
        if items:
            meta_html = f'<div class="meta">{"".join(items)}</div>'

    return f'{"".join(html_parts)}{meta_html}'


def render_digest_html(
    title: str,
    categories: dict[str, int],
    period_start: str,
    period_end: str,
    total_count: int,
) -> str:
    category_rows = ''.join(
        f'<tr><td>{cat}</td><td style="text-align:right;color:#6b7280;">{cnt}</td></tr>'
        for cat, cnt in sorted(categories.items(), key=lambda x: -x[1])
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>{_digest_style()}</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="subtitle">{period_start} &mdash; {period_end}</div>
    <h1>{title}</h1>
  </div>
  <div class="body">
    <div class="summary">
      <div class="count">{total_count}</div>
      <div class="label">notifications in this period</div>
    </div>
    <table>
      <thead><tr><th>Category</th><th style="text-align:right">Count</th></tr></thead>
      <tbody>{category_rows}</tbody>
    </table>
  </div>
  <div class="footer">
    SafeVixAI Notification System &mdash; IIT Madras Road Safety Hackathon 2026
  </div>
</div>
</body>
</html>"""


SMS_TEMPLATES: dict[str, str] = {
    'sos': '🚨 SOS: {user_name} needs help at {location}. Respond immediately.',
    'sla_breach': '⚠️ SLA Breach: {complaint_ref} ({issue_type}) overdue by {overdue_hours:.1f}h.',
    'issue_update': '📋 Issue {tracking_number} updated to {status}: {title[:60]}',
    'deployment': '🚀 {service_name} deployed to {environment} ({version}). Status: {status}.',
    'system_health': '🔧 {component} — {status}. Metric: {metric} (threshold: {threshold}).',
    'security': '🔒 Security Alert: {event_type} detected. {details}',
    'billing': '💰 {message}',
}
