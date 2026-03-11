# DSAgent UI Integration Guide

## Overview

This document describes how to integrate the DSAgent API with frontend applications.

## Using the Python Client

```python
import asyncio
from dsagent.client import DSAgentClient

async def main():
    async with DSAgentClient("http://localhost:8000") as client:
        # Create project
        project = await client.create_project(
            name="Customer Churn Prediction",
            target_column="churn",
            success_metric="roc_auc",
            metric_threshold=0.85
        )
        project_id = project["id"]
        
        # Chat with agent
        response = await client.chat(
            project_id=project_id,
            message="I want to predict customer churn"
        )
        print(response["response"])
        
        # Check for HITL
        pending = await client.get_pending_hitl(project_id)
        for hitl in pending:
            print(f"HITL: {hitl['question']}")
            # Approve or reject
            await client.approve_hitl(hitl["id"])

asyncio.run(main())
```

## SSE Streaming Events

The API uses Server-Sent Events for streaming. Here's how to parse them:

```javascript
const eventSource = new EventSource(
  `/api/v1/chat/${projectId}/stream`,
  { method: 'POST', body: JSON.stringify({ message: text }) }
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch (event.type) {
    case 'thinking':
      // Show thinking indicator
      showThinking(data.thinking);
      break;
      
    case 'llm_response':
      // Show response
      appendMessage(data.content);
      break;
      
    case 'code_executing':
      // Show code being executed
      showCode(data.code);
      break;
      
    case 'code_result':
      // Show execution result
      showResult(data.stdout, data.images);
      break;
      
    case 'done':
      // Conversation complete
      eventSource.close();
      break;
      
    case 'error':
      // Show error
      showError(data.error);
      break;
  }
};
```

## HITL Workflow

### 1. Check for Pending HITL

```javascript
async function checkHITL(projectId) {
  const response = await fetch(
    `/api/v1/hitl/pending?project_id=${projectId}`
  );
  const pending = await response.json();
  
  if (pending.length > 0) {
    showHITLPanel(pending[0]);
  }
}
```

### 2. Display HITL Request

```javascript
function showHITLPanel(hitl) {
  const panel = document.getElementById('hitl-panel');
  panel.innerHTML = `
    <h3>${hitl.type.replace('_', ' ').toUpperCase()}</h3>
    <p>${hitl.question}</p>
    <div class="options">
      <button onclick="approveHITL('${hitl.id}')">Approve</button>
      <button onclick="rejectHITL('${hitl.id}')">Reject</button>
      <button onclick="modifyHITL('${hitl.id}')">Modify</button>
    </div>
  `;
  panel.show();
}
```

### 3. Handle Response

```javascript
async function approveHITL(hitlId) {
  await fetch(`/api/v1/hitl/${hitlId}/approve`, {
    method: 'POST'
  });
  hideHITLPanel();
  // Continue conversation
}

async function rejectHITL(hitlId) {
  await fetch(`/api/v1/hitl/${hitlId}/reject`, {
    method: 'POST'
  });
  hideHITLPanel();
}
```

## UI Components

### Chat Interface

```
┌─────────────────────────────────────────┐
│  DSAgent Ralph                         │
├─────────────────────────────────────────┤
│                                         │
│  [User] I want to predict churn         │
│                                         │
│  [Agent] I'll help you build a          │
│  prediction model. Let me start by      │
│  analyzing your data...                │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Thinking: Loading data...       │   │
│  └─────────────────────────────────┘   │
│                                         │
├─────────────────────────────────────────┤
│  ┌─────────────────────────────────┐   │
│  │ Type message...              [↗] │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

### HITL Panel

```
┌─────────────────────────────────────────┐
│  ⚠️ Approval Required                   │
├─────────────────────────────────────────┤
│                                         │
│  Plan Approval                          │
│                                         │
│  Generated plan:                        │
│  1. Load data                          │
│  2. EDA analysis                       │
│  3. Train models                       │
│  4. Evaluate results                   │
│                                         │
│  [Approve] [Modify] [Reject]          │
│                                         │
└─────────────────────────────────────────┘
```

### Project Status Dashboard

```
┌─────────────────────────────────────────┐
│  Project: Customer Churn               │
│  Status: Running                       │
│  Iteration: 2/3                        │
├─────────────────────────────────────────┤
│  Items: 8/12 ✓                         │
│  ████████████░░░░░░░░░░ 66%           │
│                                         │
│  Current: Training RandomForest         │
└─────────────────────────────────────────┘
```

## API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/projects` | Create project |
| GET | `/api/v1/projects` | List projects |
| GET | `/api/v1/projects/{id}` | Get project |
| GET | `/api/v1/projects/{id}/status` | Get status |
| POST | `/api/v1/chat/{id}/stream` | Chat with SSE |
| GET | `/api/v1/hitl/pending` | Pending approvals |
| POST | `/api/v1/hitl/{id}/approve` | Approve |
| POST | `/api/v1/hitl/{id}/reject` | Reject |
| POST | `/api/v1/kernel/{id}/execute` | Execute code |
| GET | `/api/v1/kernel/{id}/state` | Kernel state |

## Environment Variables

For production, configure:

```env
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
DEFAULT_MODEL=claude-sonnet-4-20250514
```
