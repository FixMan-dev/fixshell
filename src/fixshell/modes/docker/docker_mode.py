
import click
import os
import subprocess
from .docker_templates import DOCKER_TEMPLATES
from .docker_validator import is_docker_installed, is_docker_running, is_port_free, container_exists
from ...engine.classifier import Classifier
from ...engine.resolver_registry import (
    ResolverRegistry, handle_docker_name_conflict, handle_docker_daemon_service,
    handle_docker_not_installed
)
from ...engine.state_machine import WorkflowStateMachine
from ...ui.renderer import Renderer

class DockerMode:
    """
    Controller for Docker guided workflow, synchronized with the FixShell Engine.
    """
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        
        # 1. Initialize Engine
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        dataset_dir = os.path.join(base_path, "dataset")
        self.classifier = Classifier(dataset_dir)
        
        # 2. Setup Registries
        self.registry = ResolverRegistry()
        self.registry.register("docker_name_conflict", handle_docker_name_conflict)
        self.registry.register("docker_daemon_service", handle_docker_daemon_service)
        self.registry.register("docker_not_installed", handle_docker_not_installed)
        
        # 3. Instantiate core components
        self.sm = WorkflowStateMachine(self.classifier, self.registry, dry_run, mode="docker")

    def run_guided_workflow(self):
        while True:
            click.clear()
            Renderer.print_banner("Docker Guided Workflow")
            
            # Use orchestrated StateMachine to refresh and render context
            self.sm.refresh_context()

            # Step 1: Template Selection
            click.secho("\n🎁 Available Templates:", fg="cyan", bold=True)
            options = [
                "Install Docker Engine (Guided)",
                "Create Node Web App Container",
                "Create Python Web App Container",
                "Run MySQL Database",
                "Run PostgreSQL Database",
                "Build Image from Current Folder",
                "Debug Running Container",
                "Stop/Remove Container Safely",
                "Exit Mode"
            ]
            
            for i, opt in enumerate(options, 1):
                click.echo(f"{i}. {opt}")
                
            choice = click.prompt("\nSelect an option", type=int, default=len(options))
            
            if choice >= len(options):
                break

            if choice == 1:
                self._install_docker_guided()
            elif choice <= 5:
                # choice 2->index 0, 3->index 1, 4->index 2, 5->index 3
                selected_key = list(DOCKER_TEMPLATES.keys())[choice-2]
                self._run_predefined_template(selected_key)
            elif choice == 6:
                self._build_current_folder()
            elif choice == 7:
                self._debug_container()
            elif choice == 8:
                self._stop_container()
            
            input("\nPress Enter to return to menu...")

    def _install_docker_guided(self):
        """Manually trigger the installation resolver logic."""
        handle_docker_not_installed([], dry_run=self.dry_run, state=self.sm.state)

    def _run_predefined_template(self, template_key):
        template = DOCKER_TEMPLATES[template_key]
        Renderer.print_step(f"Template: {template['name']}")
        
        # Inputs
        name = click.prompt("   Container name", default=template_key.replace("_", "-"))
        port_host = click.prompt("   Host port", type=int, default=template['steps'][1].get('port', 8080))
        
        # Basic validation (Manual for now, can be resolved by engine if it fails)
        if not is_port_free(port_host):
            Renderer.print_info(f"Port {port_host} is in use. Engine will attempt to resolve if it fails.")

        # Construct commands from template
        for step in template['steps']:
            if 'cmd' in step:
                cmd = step['cmd'].split()
                # Simple replacement for demonstration
                if "run" in cmd:
                    # In a real tool, we'd have a better template engine
                    for i, arg in enumerate(cmd):
                        if arg == "--name": cmd[i+1] = name
                        if arg == "-p":
                            container_port = cmd[i+1].split(':')[1]
                            cmd[i+1] = f"{port_host}:{container_port}"
                
                self.sm.execute_step(cmd, step['desc'])

    def _build_current_folder(self):
        if not os.path.exists("Dockerfile"):
            Renderer.print_error("No Dockerfile found in current directory.")
            return
        
        tag = click.prompt("   Image tag", default="myapp:latest")
        self.sm.execute_step(["docker", "build", "-t", tag, "."], f"Building Image: {tag}")

    def _debug_container(self):
        name = click.prompt("   Container name")
        self.sm.execute_step(["docker", "logs", "--tail", "20", name], f"Fetching Logs for {name}")

    def _stop_container(self):
        name = click.prompt("   Container name")
        if self.sm.execute_step(["docker", "stop", name], f"Stopping {name}"):
            if click.confirm("   Remove container permanently?", default=True):
                self.sm.execute_step(["docker", "rm", name], f"Removing {name}")
