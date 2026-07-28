# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
"""MkDocs hook: conditionally enable Plausible analytics when env var set.

Usage: set PLAUSIBLE_DOMAIN env var to enable Plausible analytics.
Optional: PLAUSIBLE_SRC for custom script path (e.g., self-hosted).
"""

import os


def on_config(config):
    domain = os.environ.get("PLAUSIBLE_DOMAIN", "")
    if not domain:
        return config

    src = os.environ.get("PLAUSIBLE_SRC", "")
    plausible_config = {"domain": domain}
    if src:
        plausible_config["src"] = src

    config.plugins.append(("material-plausible", plausible_config))
    config.extra.setdefault("analytics", {})
    config.extra["analytics"]["provider"] = "plausible"
    config.extra["analytics"]["domain"] = domain
    if src:
        config.extra["analytics"]["src"] = src
    return config
