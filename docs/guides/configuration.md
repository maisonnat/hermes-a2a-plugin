# Configuration Reference

## Plugin Configuration

Configure the plugin via `~/.hermes/config.yaml`:

```yaml
plugins:
  enabled:
    - hermes-a2a

hermes_a2a:
  # Server configuration
  server:
    host: "127.0.0.1"      # Bind address
    port: 4097              # Listen port
    
  # Authentication
  auth:
    enabled: false          # Enable bearer token auth
    token: ""               # Secret token (set via env var preferred)
    
  # Agent Card customization
  agent_card:
    name: "Hermes Agent"
    description: "Self-improving AI agent with persistent memory"
    skills:
      - id: "hermes_general"
        name: "General Purpose"
        description: "Research, coding, automation"
        tags: ["research", "coding", "automation"]
        
  # Logging
  log_level: "info"         # debug, info, warn, error
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HERMES_A2A_PORT` | Server port | `4097` |
| `HERMES_A2A_HOST` | Bind address | `127.0.0.1` |
| `HERMES_A2A_TOKEN` | Auth token | (empty = no auth) |
| `HERMES_A2A_LOG_LEVEL` | Log level | `info` |

## CLI Reference

```bash
hermes a2a serve [OPTIONS]

Options:
  --port INT        Server port (default: 4097)
  --host TEXT       Bind address (default: 127.0.0.1)
  --token TEXT      Auth bearer token (optional)
  --verbose         Enable debug logging
  --help            Show this message
```
