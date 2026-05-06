# Troubleshooting

## GitHub Pages muestra 404

**Causa:** El branch `gh-pages` no existe o no está configurado.

**Solución:**
```bash
cd ~/Projects/hermes-a2a-plugin
source .venv/bin/activate
mkdocs gh-deploy --force
```
Esto crea el branch y GitHub lo publica automáticamente.

## Plugin no aparece en `hermes plugins list`

**Causas posibles:**
1. No está symlinkeado en `~/.hermes/plugins/`
2. `plugin.yaml` falta o tiene error

**Verificación:**
```bash
ls -la ~/.hermes/plugins/hermes-a2a/    # Debe existir
cat ~/.hermes/plugins/hermes-a2a/plugin.yaml  # Debe tener name, version, etc.
```

## `delegate_task` da error 401 Authentication Fails

**Causa:** La API key en `delegation.api_key` expiró o es inválida.

**Solución:** Hacer las tareas secuencialmente (sin subagentes) o corregir la key en `~/.hermes/config.yaml`.

## Servidor A2A no responde

**Verificar:**
```bash
# ¿Está corriendo?
curl http://localhost:4097/health

# ¿Hay errores?
curl http://localhost:4097/tasks/send -X POST \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"params":{"id":"t","message":{"role":"user","parts":[{"text":"hi"}]}}}'

# ¿Puerto ocupado?
ss -tlnp | grep 4097
```

## OpenCode no ve las tools del MCP bridge

**Verificar:**
```bash
# Probar el bridge directamente:
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' \
  | python3 -m hermes_a2a_plugin.bridge_mcp

# Debería responder con las 3 tools
```

Si no funciona, revisar `~/.opencode/opencode.jsonc`:
```json
{
  "mcpServers": {
    "hermes-a2a": {
      "command": "python3",
      "args": ["-m", "hermes_a2a_plugin.bridge_mcp"]
    }
  }
}
```

## `mkdocs build --strict` falla con warnings

**Causas comunes:**
- `griffe: No type or annotation for parameter 'xxx'` → Agregar type hints
- `mkdocstrings: could not find module` → Verificar que el path en `api/reference.md` exista
- `Pages exist in docs but not in nav` → Agregar al nav en `mkdocs.yml`

## El `a2a` package de PyPI no es el SDK correcto

El paquete `a2a` en PyPI (v0.44) es un **web scraper** (depende de Scrapy). No lo uses.

El SDK real del protocolo A2A está en:
https://github.com/a2aproject/a2a-samples

Para nuestro plugin usamos Python built-in `http.server` — cero dependencias externas.
