"""Jupyter Kernel Manager - Advanced implementation"""
import asyncio
import uuid
import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class KernelManager:
    """
    Manages Jupyter kernels for code execution.
    Supports kernel pooling, lifecycle management, and state tracking.
    """
    
    def __init__(self):
        self.kernels: Dict[str, Dict[str, Any]] = {}
        self.kernel_pool: List[str] = []
        self.max_pool_size = 5
        self.kernel_timeout = 600  # 10 minutes
    
    async def get_kernel(self, project_id: str) -> str:
        """
        Get or create a kernel for a project.
        """
        # Check if project already has a kernel
        if project_id in self.kernels:
            kernel_info = self.kernels[project_id]
            if kernel_info["status"] == "active":
                # Refresh timeout
                kernel_info["last_used"] = datetime.utcnow()
                return project_id
        
        # Try to get from pool
        if self.kernel_pool:
            kernel_id = self.kernel_pool.pop()
            self.kernels[project_id] = {
                "kernel_id": kernel_id,
                "status": "active",
                "created_at": datetime.utcnow(),
                "last_used": datetime.utcnow()
            }
            return project_id
        
        # Create new kernel
        kernel_id = await self._create_kernel()
        self.kernels[project            "kernel_id_id] = {
": kernel_id,
            "status": "active",
            "created_at": datetime.utcnow(),
            "last_used": datetime.utcnow()
        }
        
        return project_id
    
    async def _create_kernel(self) -> str:
        """
        Create a new Jupyter kernel.
        
        In production, this would use jupyter_client to create a real kernel.
        """
        # Simulated kernel ID
        return f"kernel-{uuid.uuid4().hex[:8]}"
    
    async def execute_code(
        self, 
        project_id: str, 
        code: str,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Execute code in the project's kernel.
        """
        # Get or create kernel
        await self.get_kernel(project_id)
        
        kernel_info = self.kernels.get(project_id)
        if not kernel_info:
            return {
                "success": False,
                "error": "Failed to get kernel"
            }
        
        try:
            # In production, this would execute in real kernel
            result = await self._execute_in_kernel(code, timeout)
            
            # Update last used
            kernel_info["last_used"] = datetime.utcnow()
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing code: {e}")
            return {
                "success": False,
                "error": str(e),
                "output": ""
            }
    
    async def _execute_in_kernel(
        self, 
        code: str, 
        timeout: int
    ) -> Dict[str, Any]:
        """
        Execute code in kernel (simulated for now).
        """
        # Simulated execution - in production use jupyter_client
        output = self._simulate_output(code)
        
        # Extract charts from code
        charts = []
        if "savefig" in code or "save" in code:
            charts = self._extract_chart_paths(code)
        
        return {
            "success": True,
            "output": output,
            "charts": charts,
            "execution_time": 1.5
        }
    
    def _simulate_output(self, code: str) -> str:
        """Simulate code output based on code content."""
        code_lower = code.lower()
        
        if "describe" in code_lower or "info" in code_lower:
            return """=== NUMERIC COLUMNS ===
         age   tenure  charges
count  1000.0  1000.0   1000.0
mean     45.0    2.5   1500.0
std      12.0    1.2    500.0
min      18.0    0.0    100.0
max      75.0    5.0   5000.0

=== SHAPE ===
Rows: 1000, Columns: 12"""
        
        if "train" in code_lower or "model" in code_lower:
            return """=== MODEL RESULTS ===
LogisticRegression: ROC-AUC = 0.8234
RandomForest: ROC-AUC = 0.8512
XGBoost: ROC-AUC = 0.8678

Best model: XGBoost with ROC-AUC: 0.8678"""
        
        if "import" in code_lower:
            return "Imports successful"
        
        if "read_csv" in code_lower:
            return "Data loaded successfully"
        
        return "Code executed successfully"
    
    def _extract_chart_paths(self, code: str) -> List[str]:
        """Extract chart paths from code."""
        charts = []
        if "savefig" in code or ".save" in code:
            # Extract filename from savefig('/path/to/chart.png')
            import re
            matches = re.findall(r"['\"](.*?\.(?:png|jpg|svg))['\"]", code)
            charts.extend(matches)
        return charts
    
    async def get_kernel_state(self, project_id: str) -> Dict[str, Any]:
        """
        Get current kernel state (variables, imports).
        """
        kernel_info = self.kernels.get(project_id)
        if not kernel_info:
            return {
                "exists": False,
                "variables": [],
                "imports": []
            }
        
        # In production, query kernel for actual state
        return {
            "exists": True,
            "kernel_id": kernel_info["kernel_id"],
            "created_at": kernel_info["created_at"].isoformat(),
            "last_used": kernel_info["last_used"].isoformat(),
            "variables": ["df", "model", "results"],
            "imports": ["pandas", "numpy", "sklearn"],
            "dataframes": ["df"]
        }
    
    async def reset_kernel(self, project_id: str) -> bool:
        """
        Reset kernel for project (clear all state).
        """
        if project_id in self.kernels:
            # Return old kernel to pool
            self.kernel_pool.append(
                self.kernels[project_id]["kernel_id"]
            )
            del self.kernels[project_id]
        
        return True
    
    async def release_kernel(self, project_id: str):
        """
        Release kernel back to pool.
        """
        if project_id in self.kernels:
            kernel_info = self.kernels[project_id]
            
            # Add to pool if not full
            if len(self.kernel_pool) < self.max_pool_size:
                self.kernel_pool.append(kernel_info["kernel_id"])
            
            # Remove from active
            del self.kernels[project_id]
    
    async def cleanup_idle_kernels(self):
        """
        Clean up idle kernels.
        """
        now = datetime.utcnow()
        idle_kernels = []
        
        for project_id, kernel_info in self.kernels.items():
            last_used = kernel_info["last_used"]
            if (now - last_used) > timedelta(seconds=self.kernel_timeout):
                idle_kernels.append(project_id)
        
        for project_id in idle_kernels:
            await self.release_kernel(project_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get kernel manager statistics.
        """
        return {
            "active_kernels": len(self.kernels),
            "pooled_kernels": len(self.kernel_pool),
            "projects": list(self.kernels.keys())
        }


# Global kernel manager instance
kernel_manager = KernelManager()
