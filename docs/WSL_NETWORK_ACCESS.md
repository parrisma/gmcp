# WSL Network Access Guide

## Docker Host IP Address

The WSL2 Docker host IP address for this environment is:
```
172.22.9.172
```

**Important**: Use this IP when accessing containers from Windows browser due to localhost IPv6 timeout issues.

---

## Service Access URLs

### OpenWebUI
- **From Windows Browser**: `http://172.22.9.172:9090`
- **From Containers (ai-net)**: `http://openwebui:8080`
- **From WSL Terminal**: `http://localhost:9090`

**Configuration**:
- Authentication: Disabled (`WEBUI_AUTH=false`)
- API Key Auth: Enabled (`ENABLE_API_KEY_AUTH=true`)
- Network: `ai-net`
- Volume: `openwebui_volume`
- Shared Directory: `~/openwebui_share` → `/data/openwebui_share`

**OpenRouter Configuration**:
```bash
export OPENROUTER_API_KEY="sk-or-v1-your-key-here"
./docker/run-openwebui.sh
```

**Adding MCPO as Tool**:
1. Go to **Settings** → **Tools** → **Add OpenAPI Server**
2. URL: `http://cd1389d37be0:8002` (or current dev container hostname)
3. API Key: Leave empty (no-auth mode)

---

### Web Server (REST API)
- **From Windows Browser**: `http://172.22.9.172:8000`
- **From Containers (ai-net)**: `http://cd1389d37be0:8000`
- **From WSL Terminal**: `http://localhost:8000`

**Key Endpoints**:
- API Docs: `http://172.22.9.172:8000/docs`
- Render Graph: `POST http://172.22.9.172:8000/render`
- Get Image: `GET http://172.22.9.172:8000/render/{guid}`
- Get HTML: `GET http://172.22.9.172:8000/render/{guid}/html`
- List Images: `GET http://172.22.9.172:8000/images`
- Ping: `GET http://172.22.9.172:8000/ping`

**Note**: The endpoint is `/render/{guid}`, not `/image/{guid}`

---

### MCP Server
- **From Windows Browser**: `http://172.22.9.172:8001`
- **From Containers (ai-net)**: `http://cd1389d37be0:8001`
- **From WSL Terminal**: `http://localhost:8001`

**Key Endpoints**:
- MCP Endpoint: `http://172.22.9.172:8001/mcp`
- SSE Messages: `http://172.22.9.172:8001/sse/messages`

---

### MCPO Proxy
- **From Windows Browser**: `http://172.22.9.172:8002`
- **From Containers (ai-net)**: `http://cd1389d37be0:8002`
- **From WSL Terminal**: `http://localhost:8002`

**Key Endpoints**:
- OpenAPI Schema: `http://172.22.9.172:8002/openapi.json`
- Ping: `POST http://172.22.9.172:8002/ping`
- Render Graph: `POST http://172.22.9.172:8002/render_graph`
- Get Image: `POST http://172.22.9.172:8002/get_image`

---

### n8n Workflow Automation
- **From Windows Browser**: `http://172.22.9.172:5678`
- **From Containers (ai-net)**: `http://n8n:5678`
- **From WSL Terminal**: `http://localhost:5678`

**Configuration**:
- Network: `ai-net`
- Volume: `gplot_volume`
- Shared Directory: `~/n8n_share` → `/data/n8n_share`

---

## Docker Network Configuration

All containers use the **`ai-net`** network for inter-container communication.

**Available Containers on ai-net**:
- `cd1389d37be0` - Dev container (gplot_dev)
- `openwebui` - OpenWebUI
- `n8n` - n8n automation

**Creating ai-net** (if needed):
```bash
docker network create ai-net
```

**Connecting Existing Container**:
```bash
docker network connect ai-net <container-name-or-id>
```

---

## Port Mappings

| Service | Host Port | Container Port | Protocol |
|---------|-----------|----------------|----------|
| Web API | 8000 | 8000 | HTTP |
| MCP Server | 8001 | 8001 | HTTP |
| MCPO Proxy | 8002 | 8002 | HTTP |
| n8n | 5678 | 5678 | HTTP |
| OpenWebUI | 9090 | 8080 | HTTP |

All services bind to `0.0.0.0` for accessibility from outside the container.

---

## Troubleshooting

### Chrome Hangs on localhost
**Problem**: Chrome hangs when accessing `http://localhost:PORT`

**Root Cause**: IPv6 connection timeout (Chrome tries `::1` first)

**Solutions**:
1. Use Docker host IP: `http://172.22.9.172:PORT` ✅ (Recommended)
2. Force IPv4: `http://127.0.0.1:PORT`
3. Edit `/etc/hosts` to comment out `::1` line
4. Disable IPv6 in Chrome: `chrome://flags/#enable-ipv6`

### Finding Docker Host IP
```bash
hostname -I | awk '{print $1}'
```

### Container Hostname
```bash
hostname
```
Current: `cd1389d37be0`

---

## No-Auth Mode

All services currently run in **no-auth mode** with the group name **`public`**:

**Starting Services**:
```bash
# Web Server
./scripts/run_web.sh

# MCP Server
./scripts/run_mcp.sh

# MCPO Proxy
./scripts/run_mcpo.sh

# OpenWebUI
./docker/run-openwebui.sh

# n8n
./docker/run-n8n.sh
```

**Verifying Group**:
```bash
# List all images and their groups
python scripts/storage_manager.py list

# Check metadata
cat data/storage/metadata.json | jq
```

---

## Quick Reference Commands

**Container Management**:
```bash
# List running containers
docker ps

# View logs
docker logs -f <container-name>

# Restart container
docker restart <container-name>

# Connect to ai-net
docker network connect ai-net <container-name>
```

**Service Health Checks**:
```bash
# Web API
curl http://localhost:8000/ping

# MCP Server  
curl http://localhost:8001/ping

# MCPO Proxy
curl -X POST http://localhost:8002/ping -H "Content-Type: application/json" -d '{}'

# OpenWebUI
curl http://localhost:9090/api/version
```

**Storage Management**:
```bash
# List all images
python scripts/storage_manager.py list

# Storage stats
python scripts/storage_manager.py stats

# Purge old images
python scripts/storage_manager.py purge --days 7
```
