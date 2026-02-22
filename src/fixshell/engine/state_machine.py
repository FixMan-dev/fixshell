import os
import sys
import subprocess
import platform
from .retry_engine import RetryEngine
from .executor import Executor
from ..ui.context_panel import ContextPanel
from typing import Dict, Any, Optional

class WorkflowStateMachine:
    """
    Orchestrates high-level system states and delegates 
    recovery execution to the RetryEngine.
    Tracks AUTH_STATE, REPO_STATE, etc.
    """

    def __init__(self, classifier, registry, dry_run: bool = False, mode: Optional[str] = None):
        self.executor = Executor(dry_run)
        self.retry_engine = RetryEngine(classifier, registry, self.executor, mode=mode)
        self.mode = mode
        self.state: Dict[str, Any] = {
            "AUTH_STATE": "Unknown",
            "REPO_STATE": "No",
            "BRANCH_STATE": "N/A",
            "NETWORK_STATE": "Online",
            "PERMISSION_STATE": "User",
            "WORKFLOW_STATE": "Idle",
            "OS_STATE": self._detect_os(),
            "DISTRO_STATE": self._detect_distro(),
            "ARCH_STATE": self._detect_arch(),
            "INSTALL_STATE": {"supported": False, "details": {}}
        }

    def _detect_os(self) -> str:
        return platform.system()

    def _detect_arch(self) -> str:
        machine = platform.machine().lower()
        if machine in ["x86_64", "amd64"]: return "amd64"
        if machine in ["arm64", "aarch64"]: return "arm64"
        return machine

    def _detect_distro(self) -> Dict[str, str]:
        os_name = self._detect_os()
        info = {
            "id": "unknown", 
            "version": "unknown", 
            "codename": "unknown", 
            "build": "0",
            "pretty_name": "unknown"
        }

        if os_name == "Linux":
            try:
                if os.path.exists("/etc/os-release"):
                    envs = {}
                    with open("/etc/os-release") as f:
                        for line in f:
                            if "=" in line:
                                k, v = line.rstrip().split("=", 1)
                                envs[k] = v.strip('"')
                    
                    info["id"] = envs.get("ID", "unknown")
                    info["version"] = envs.get("VERSION_ID", "unknown")
                    info["pretty_name"] = envs.get("PRETTY_NAME", "unknown")
                    
                    # Target Ubuntu specifics as per requirements
                    info["codename"] = envs.get("UBUNTU_CODENAME") or envs.get("VERSION_CODENAME") or "unknown"
                
                # lsb_release fallback
                if info["codename"] == "unknown":
                    res = subprocess.run(["lsb_release", "-cs"], capture_output=True, text=True)
                    if res.returncode == 0:
                        info["codename"] = res.stdout.strip()
                
                if info["pretty_name"] == "unknown":
                    res = subprocess.run(["lsb_release", "-ds"], capture_output=True, text=True)
                    if res.returncode == 0:
                        info["pretty_name"] = res.stdout.strip()

            except Exception:
                pass
        
        elif os_name == "Windows":
            v = sys.getwindowsversion()
            info["version"] = f"{v.major}.{v.minor}"
            info["build"] = str(v.build)
            info["pretty_name"] = f"Windows {v.major}"
            
        return info

    def update_state(self, key: str, value: Any):
        self.state[key] = value

    def refresh_context(self, context_manager=None):
        """
        Syncs state from the environment/context_manager 
        and renders the ContextPanel.
        """
        if context_manager:
            context_manager.refresh()
            # Map from context manager attributes to our formal state categories
            self.state["AUTH_STATE"] = getattr(context_manager, "user", "Not Logged In")
            self.state["REPO_STATE"] = "Yes" if getattr(context_manager, "is_repo", False) else "No"
            self.state["BRANCH_STATE"] = getattr(context_manager, "branch", "N/A")
            # Permission check
            import os
            self.state["PERMISSION_STATE"] = "Sudo/Root" if os.geteuid() == 0 else "User"

        ContextPanel.render(self.state)

    def execute_step(self, cmd_list: list, desc: str, context_manager=None, interactive: bool = False) -> bool:
        """
        Updates workflow state and delegates to RetryEngine.
        """
        self.state["WORKFLOW_STATE"] = f"Running: {desc}"
        
        # Ensure we categorize the error based on the current mode
        # The classifier.classify(output, mode=self.mode) is handled inside RetryEngine
        # (Assuming RetryEngine holds a reference to a classifier that supports mode-aware classification)
        
        success = self.retry_engine.execute_with_recovery(
            cmd_list, 
            desc, 
            context_manager=context_manager, 
            interactive=interactive,
            state=self.state
        )
        
        self.state["WORKFLOW_STATE"] = "Idle"
        return success
