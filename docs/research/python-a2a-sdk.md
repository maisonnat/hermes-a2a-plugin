# Research: python-a2a SDK

> Source: https://github.com/a2aproject/a2a-samples (A2A Protocol by Google → Linux Foundation)

## Overview

The A2A Python SDK is NOT the `a2a` package on PyPI (which is a web scraper). The real SDK lives in the [a2a-samples](https://github.com/a2aproject/a2a-samples) repo and is installed via `requirements.txt`.

## Architecture

```
AgentCard ──→ .well-known/agent-card.json (discovery)
AgentSkill ──→ Capability definition (id, name, description, tags)
AgentExecutor → Core logic (process tasks, return results)
DefaultRequestHandler → Routes A2A RPC calls to executor
TaskStore → Manages task lifecycle (InMemoryTaskStore)
```

## Core Components

### 1. Agent Card & Skills

```python
from a2a.types import AgentCard, AgentSkill, AgentCapabilities

skill = AgentSkill(
    id="hermes_coding",
    name="Code with OpenCode",
    description="Delegate coding tasks to OpenCode via A2A",
    tags=["coding", "development", "opencode"],
    examples=["Implement a REST API endpoint for user management"],
    input_modes=["text/plain"],
    output_modes=["text/plain", "application/json"],
)

agent_card = AgentCard(
    name="Hermes Agent",
    description="Self-improving AI agent with persistent memory",
    url="http://localhost:4097",
    version="1.0.0",
    capabilities=AgentCapabilities(streaming=True),
    skills=[skill],
)
```

### 2. Agent Executor

The core logic. Implements `AgentExecutor` abstract class:

```python
from a2a.server.agent_execution import AgentExecutor
from a2a.types import (
    RequestContext, EventQueue, Task, TaskState,
    TaskStatusUpdateEvent, TaskArtifactUpdateEvent,
    Artifact, Message, TextPart, Role,
)

class HermesAgentExecutor(AgentExecutor):
    async def execute(self, context: RequestContext, event_queue: EventQueue):
        # 1. Get or create task
        task = context.get_current_task()
        
        # 2. Signal working state
        await event_queue.push(TaskStatusUpdateEvent(
            state=TaskState.TASK_STATE_WORKING
        ))
        
        # 3. Execute business logic
        result = await self._run_hermes(context)
        
        # 4. Push result artifact
        await event_queue.push(TaskArtifactUpdateEvent(
            artifact=Artifact(
                parts=[TextPart(content=result)],
                name="hermes_response",
            )
        ))
        
        # 5. Signal completion
        await event_queue.push(TaskStatusUpdateEvent(
            state=TaskState.TASK_STATE_COMPLETED
        ))
    
    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        await event_queue.push(TaskStatusUpdateEvent(
            state=TaskState.TASK_STATE_CANCELLED
        ))
```

### 3. Server Setup (Starlette + Uvicorn)

```python
from starlette.applications import Starlette
from starlette.routing import Route
import uvicorn
from a2a.server import (
    DefaultRequestHandler, InMemoryTaskStore,
    create_agent_card_routes, create_jsonrpc_routes,
)

handler = DefaultRequestHandler(
    executor=HermesAgentExecutor(),
    task_store=InMemoryTaskStore(),
    agent_card=agent_card,
)

routes = []
routes.extend(create_agent_card_routes(agent_card))
routes.extend(create_jsonrpc_routes(handler, '/'))

app = Starlette(routes=routes)
uvicorn.run(app, host='127.0.0.1', port=4097)
```

### 4. Client Side (for OpenCode to connect)

```python
from a2a.client import create_client, A2ACardResolver
from a2a.types import ClientConfig, Message, Role

resolver = A2ACardResolver("http://localhost:4097")
agent_card = await resolver.get_agent_card()

client = await create_client(
    agent_card,
    ClientConfig(streaming=False)
)

message = Message.new_text_message("Implement auth endpoint", Role.ROLE_USER)
response = await client.send_message(message)
```

### 5. Streaming

```python
# Server-side: push events incrementally
await event_queue.push(TaskStatusUpdateEvent(state=TaskState.TASK_STATE_WORKING))
await event_queue.push(TaskArtifactUpdateEvent(artifact=Artifact(parts=[...])))

# Client-side
streaming_client = await create_client(agent_card, ClientConfig(streaming=True))
async for event in streaming_client.send_message(message):
    print(event)
```

## Key Differences from ACP

| Aspect | A2A | ACP (Zed/JetBrains) |
|--------|-----|---------------------|
| Purpose | Agent ↔ Agent | IDE ↔ Agent |
| Transport | HTTP/JSON-RPC 2.0 | stdio/JSON-RPC 2.0 |
| Discovery | Agent Card (`.well-known/`) | Capability negotiation |
| Task model | Stateful lifecycle | Request-response |
| Streaming | SSE events | Chunked responses |
| Auth | Bearer/OAuth/DIDComm | STDIO (trusted subprocess) |

## Installation

```bash
git clone https://github.com/a2aproject/a2a-samples.git --depth 1
cd a2a-samples
pip install -r samples/python/requirements.txt
```

Or for direct integration, we'll vendor the needed a2a package or add the samples repo as a dependency.
