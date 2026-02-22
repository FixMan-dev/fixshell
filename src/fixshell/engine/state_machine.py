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
            "WORKFLOW_STATE": "Idle"
        }

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
            interactive=interactive
        )
        
        self.state["WORKFLOW_STATE"] = "Idle"
        return success
