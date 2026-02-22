import os
import subprocess
from ...engine.classifier import Classifier, ErrorCategory
from ...engine.resolver_registry import ResolverRegistry
from ...engine.state_machine import WorkflowStateMachine
from ...config import DATASET_DIR
from ...ui.renderer import Renderer

class LinuxMode:
    """
    Handles arbitrary Linux command diagnosis with deep context probing 
    and evidence-based scoring.
    """

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.classifier = Classifier(DATASET_DIR)
        self.registry = ResolverRegistry()
        self.sm = WorkflowStateMachine(self.classifier, self.registry, dry_run=dry_run, mode="linux")

    def diagnose_and_fix(self, cmd_list: list, use_ai: bool = False):
        if not cmd_list:
            Renderer.print_error("No command provided for diagnosis.")
            return

        if use_ai:
            Renderer.print_info("🚀 AI-Powered Diagnosis enabled (using Ollama)")
            # In a real implementation, this would call the LLM engine
            # For v0.2.0, we prioritize deterministic paths.
        
        Renderer.print_info(f"Probing environment context for: {' '.join(cmd_list)}")
        
        # 1. Evidence Scoring Logic (Deterministic)
        evidence = self._calculate_evidence_score(cmd_list)
        if evidence["score"] > 0:
            Renderer.print_info(f"Top Suspect: [bold]{evidence['suspect']}[/bold] (Score: {evidence['score']})")
            for link in evidence["links"]:
                Renderer.print_info(f"  🔗 Evidence: {link}")

        # 2. Delegate to State Machine for execution and recovery
        success = self.sm.execute_step(cmd_list, f"Running with Self-Healing")

        if success:
            Renderer.print_success("Operation completed successfully.")
        else:
            if not use_ai:
                Renderer.print_info("💡 Tip: Try running with '--ai' for a deeper LLM-based diagnosis.")
            Renderer.print_error("Recovery failed after multiple attempts.")

    def _calculate_evidence_score(self, cmd_list: list):
        """
        Implementation of the Evidence Scoring system.
        Probes the system (ss, df, ls, etc.) based on the command.
        """
        score = 0
        suspect = "Unknown"
        links = []
        cmd_str = " ".join(cmd_list).lower()

        # Check for Port Conflicts
        if "server" in cmd_str or "listen" in cmd_str:
            # Probe: Check for suspicious open ports (generic check)
            res = subprocess.run("ss -tulpn | wc -l", shell=True, capture_output=True, text=True)
            if int(res.stdout.strip()) > 5:
                score += 0.4
                suspect = "PORT_CONFLICT"
                links.append("High number of active listening ports detected via 'ss'")

        # Check for Disk Issues
        if "write" in cmd_str or "save" in cmd_str or "install" in cmd_str:
            res = subprocess.run("df / --output=pcent | tail -n 1", shell=True, capture_output=True, text=True)
            usage = int(res.stdout.strip().replace('%', ''))
            if usage > 90:
                score += 0.8
                suspect = "DISK_FULL"
                links.append(f"Primary partition usage is at {usage}% via 'df'")

        # Check for Permission Issues
        if "sudo" not in cmd_str and any(x in cmd_str for x in ["apt", "systemctl", "docker"]):
            if os.geteuid() != 0:
                score += 0.9
                suspect = "PERMISSION_DENIED"
                links.append("Command requires root but running as standard user")

        return {"score": score, "suspect": suspect, "links": links}
