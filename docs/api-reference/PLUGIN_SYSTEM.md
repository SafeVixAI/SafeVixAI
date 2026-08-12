# Plugin System

> **Version:** 1.0 (Design)  
> **Last updated:** 2026-07-26  
> **Cross-references:** [Architecture.md](../architecture/Architecture.md), [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)

---

## Overview

SafeVixAI supports a plugin system for extending functionality across all three services. Plugins can add new API endpoints, LLM providers, chatbot tools, middleware, and UI components.

```mermaid
flowchart TB
    subgraph Plugin[" Plugin Manifest - plugin.json "]
        M["Name, Version, Description"]
    end

    subgraph Backend[" Backend Plugins "]
        BP1["Middleware - Request/Response"]
        BP2["Storage - Custom Backend"]
    end

    subgraph Chatbot[" Chatbot Plugins "]
        CP1["Provider - New LLM"]
        CP2["Tool - API Integration"]
    end

    subgraph Frontend[" Frontend Plugins "]
        FP1["UI - Custom Components"]
        FP2["Pages - New Routes"]
    end

    Plugin --> Backend
    Plugin --> Chatbot
    Plugin --> Frontend

    style Plugin fill:#9e6a03,color:#fff
    style Backend fill:#238636,color:#fff
    style Chatbot fill:#1f6feb,color:#fff
    style Frontend fill:#6e5494,color:#fff


    classDef edge fill:#dbeafe,stroke:#3b82f6,stroke-width:2px,color:#1e3a5f
    classDef control fill:#dcfce7,stroke:#22c55e,stroke-width:2px,color:#14532d
    classDef ai fill:#f3e8ff,stroke:#a855f7,stroke-width:2px,color:#581c87
    classDef data fill:#fef3c7,stroke:#f59e0b,stroke-width:2px,color:#78350f
    classDef security fill:#fee2e2,stroke:#ef4444,stroke-width:2px,color:#7f1d1d
    classDef external fill:#f1f5f9,stroke:#94a3b8,stroke-width:2px,stroke-dasharray:5 5,color:#334155
    classDef decision fill:#e0e7ff,stroke:#6366f1,stroke-width:2px,color:#312e81
    classDef success fill:#d1fae5,stroke:#10b981,stroke-width:2px,color:#064e3b
    classDef action fill:#fff7ed,stroke:#f97316,stroke-width:2px,color:#7c2d12
    classDef neutral fill:#f8fafc,stroke:#64748b,stroke-width:2px,color:#1e293b

    class Plugin neutral
    class M neutral
    class Backend control
    class BP1 neutral
    class BP2 data
    class Chatbot ai
    class CP1 ai
    class CP2 edge
    class Frontend edge
    class FP1 edge
    class FP2 neutral```

---

## Plugin Types

| Type | Service | Description |
|------|---------|-------------|
| Middleware | Backend | Add request/response processing (auth, logging, rate limiting) |
| Provider | Chatbot | Add new LLM provider to the fallback chain |
| Tool | Chatbot | Add new agent tool (API integration, data lookup) |
| Storage | Backend | Custom storage backend (S3, GCS, Azure Blob) |
| UI | Frontend | Custom React components, pages, menu items |

---

## Plugin Manifest

Plugins are declared via a `plugin.json` manifest:

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "Description of my plugin",
  "type": "tool",
  "entry": "plugin.py",
  "dependencies": {
    "python": ["requests>=2.28"],
    "node": []  // For UI plugins
  },
  "hooks": ["on_message", "on_tool_call"],
  "config_schema": {
    "type": "object",
    "properties": {
      "api_key": { "type": "string" }
    }
  }
}
```

---

## Lifecycle Hooks

| Hook | Stage | Description |
|------|-------|-------------|
| `on_load` | Startup | Plugin loaded and registered |
| `on_unload` | Shutdown | Plugin unregistered, cleanup |
| `on_request` | Per-request | Intercept incoming request (middleware) |
| `on_response` | Per-request | Intercept outgoing response (middleware) |
| `on_message` | Per-chat | Intercept chatbot message |
| `on_tool_call` | Per-tool | Intercept tool execution |

---

## Creating a Plugin

### Step 1: Create Plugin Directory
```
my-plugin/
├── plugin.json
├── plugin.py
└── README.md
```

### Step 2: Implement Plugin Interface
```python
# plugin.py
from core.plugins import BasePlugin, PluginContext

class MyPlugin(BasePlugin):
    name = "my-plugin"
    version = "1.0.0"

    async def on_load(self, ctx: PluginContext):
        self.api_key = ctx.config.get("api_key")
        ctx.logger.info(f"Loaded: {self.name}")

    async def on_message(self, message: str, ctx: PluginContext) -> str | None:
        """Modify or respond to chatbot messages."""
        if "hello" in message.lower():
            return "Hello from MyPlugin! 🚀"
        return None

    async def on_unload(self, ctx: PluginContext):
        ctx.logger.info(f"Unloaded: {self.name}")
```

### Step 3: Register Plugin
```python
# In your app setup
from core.plugins import PluginManager

manager = PluginManager()
manager.load_plugin("path/to/my-plugin")
```

---

## Configuration

Plugins access configuration through the plugin context:

```python
# plugin.json defines:
# "config_schema": { "api_key": { "type": "string" } }

# Accessed in plugin:
api_key = ctx.config.get("api_key")
```

Configuration is set at plugin load time via environment variables or a config file.

---

## Publishing & Discovery

Plugins are discovered from a configured directory:

```python
# backend/core/plugins.py
PLUGIN_DIRS = [
    "plugins/",
    "custom/plugins/",
]
```

For community plugins, a future plugin registry at `plugins.safevixai.dev` will host public plugins.

---

## Security Considerations

- **Sandboxing**: Plugins run in the same process — use with caution
- **Permissions**: Plugins can only access resources they declare in `plugin.json`
- **Validation**: Plugin manifests are validated against a schema
- **Rate limiting**: Plugin-initiated API calls respect global rate limits
- **Audit**: All plugin actions are logged

---

## Examples

### Custom LLM Provider
```python
# providers/custom_provider.py
from providers.base import BaseLLMProvider

class CustomProvider(BaseLLMProvider):
    async def generate(self, messages, **kwargs):
        # Call your custom API
        response = await httpx.post("https://api.custom.com/v1/chat", json={
            "messages": messages,
            "model": self.model,
        })
        return response.json()["choices"][0]["message"]["content"]
```

### Custom Middleware
```python
# middleware/custom_middleware.py
from starlette.middleware.base import BaseHTTPMiddleware

class RequestTimerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        response.headers["X-Duration-Ms"] = str(int(duration * 1000))
        return response
```

---

## API Reference

### `BasePlugin` Methods
| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `on_load` | `ctx: PluginContext` | `None` | Called on plugin load |
| `on_unload` | `ctx: PluginContext` | `None` | Called on plugin unload |
| `on_request` | `request: Request` | `Response | None` | Intercept request |
| `on_response` | `request, response` | `Response` | Intercept response |
| `on_message` | `message: str, ctx` | `str | None` | Intercept chatbot message |
| `on_tool_call` | `tool, args, ctx` | `str | None` | Intercept tool call |

### `PluginContext` Properties
| Property | Type | Description |
|----------|------|-------------|
| `config` | `dict` | Plugin configuration |
| `logger` | `Logger` | Plugin-specific logger |
| `redis` | `Redis | None` | Shared Redis client |
| `db` | `AsyncSession | None` | Database session |
