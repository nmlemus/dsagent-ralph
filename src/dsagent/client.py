"""DSAgent API Client - For connecting to frontend applications"""

import asyncio
import json
from typing import Dict, Any, Optional, List, AsyncIterator
import aiohttp


class DSAgentClient:
    """
    Python client for DSAgent API.
    Can be used by frontend applications or external services.
    """

    def __init__(
        self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self._get_headers())
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    # === Projects ===

    async def create_project(
        self,
        name: str,
        description: str = "",
        target_column: str = "",
        success_metric: str = "roc_auc",
        metric_threshold: float = 0.8,
    ) -> Dict[str, Any]:
        """Create a new project"""
        async with self.session.post(
            f"{self.base_url}/api/v1/projects",
            json={
                "name": name,
                "description": description,
                "target_column": target_column,
                "success_metric": success_metric,
                "metric_threshold": metric_threshold,
            },
        ) as resp:
            return await resp.json()

    async def get_project(self, project_id: str) -> Dict[str, Any]:
        """Get project details"""
        async with self.session.get(
            f"{self.base_url}/api/v1/projects/{project_id}"
        ) as resp:
            return await resp.json()

    async def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects"""
        async with self.session.get(f"{self.base_url}/api/v1/projects") as resp:
            return await resp.json()

    async def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """Get project status"""
        async with self.session.get(
            f"{self.base_url}/api/v1/projects/{project_id}/status"
        ) as resp:
            return await resp.json()

    # === Chat ===

    async def chat(self, project_id: str, message: str) -> Dict[str, Any]:
        """Send chat message (sync)"""
        async with self.session.post(
            f"{self.base_url}/api/v1/chat/{project_id}", json={"message": message}
        ) as resp:
            return await resp.json()

    async def chat_stream(self, project_id: str, message: str) -> AsyncIterator[str]:
        """Send chat message with streaming response"""
        async with self.session.post(
            f"{self.base_url}/api/v1/chat/{project_id}/stream",
            json={"message": message},
        ) as resp:
            async for line in resp.content:
                if line:
                    yield line.decode("utf-8")

    # === HITL ===

    async def get_pending_hitl(
        self, project_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get pending HITL requests"""
        url = f"{self.base_url}/api/v1/hitl/pending"
        if project_id:
            url += f"?project_id={project_id}"
        async with self.session.get(url) as resp:
            return await resp.json()

    async def approve_hitl(
        self, hitl_id: str, response: str = "Approved"
    ) -> Dict[str, Any]:
        """Approve HITL request"""
        async with self.session.post(
            f"{self.base_url}/api/v1/hitl/{hitl_id}/approve",
            json={"response": response},
        ) as resp:
            return await resp.json()

    async def reject_hitl(
        self, hitl_id: str, response: str = "Rejected"
    ) -> Dict[str, Any]:
        """Reject HITL request"""
        async with self.session.post(
            f"{self.base_url}/api/v1/hitl/{hitl_id}/reject", json={"response": response}
        ) as resp:
            return await resp.json()

    async def respond_hitl(
        self, hitl_id: str, response: str, status: str = "approved"
    ) -> Dict[str, Any]:
        """Respond to HITL request"""
        async with self.session.post(
            f"{self.base_url}/api/v1/hitl/{hitl_id}/respond",
            json={"response": response, "status": status},
        ) as resp:
            return await resp.json()

    # === Kernel ===

    async def execute_code(
        self, project_id: str, code: str, timeout: int = 300
    ) -> Dict[str, Any]:
        """Execute code in kernel"""
        async with self.session.post(
            f"{self.base_url}/api/v1/kernel/{project_id}/execute",
            json={"code": code, "timeout": timeout},
        ) as resp:
            return await resp.json()

    async def get_kernel_state(self, project_id: str) -> Dict[str, Any]:
        """Get kernel state"""
        async with self.session.get(
            f"{self.base_url}/api/v1/kernel/{project_id}/state"
        ) as resp:
            return await resp.json()

    async def reset_kernel(self, project_id: str) -> Dict[str, Any]:
        """Reset kernel"""
        async with self.session.post(
            f"{self.base_url}/api/v1/kernel/{project_id}/reset"
        ) as resp:
            return await resp.json()

    # === Items & Experiments ===

    async def get_items(self, project_id: str) -> List[Dict[str, Any]]:
        """Get project items"""
        async with self.session.get(
            f"{self.base_url}/api/v1/projects/{project_id}/items"
        ) as resp:
            return await resp.json()

    async def get_experiments(self, project_id: str) -> List[Dict[str, Any]]:
        """Get project experiments"""
        async with self.session.get(
            f"{self.base_url}/api/v1/projects/{project_id}/experiments"
        ) as resp:
            return await resp.json()


# Convenience function for sync usage
def create_client(
    base_url: str = "http://localhost:8000", api_key: Optional[str] = None
) -> DSAgentClient:
    """Create a DSAgent client"""
    return DSAgentClient(base_url, api_key)
