
import click
import os
from .docker_templates import DOCKER_TEMPLATES
from .docker_validator import is_docker_installed, is_docker_running, is_port_free, container_exists
from .docker_executor import DockerExecutor
from ...engine.error_classifier import ErrorClassifierEngine

class DockerMode:
    """
    Controller for Docker guided workflow.
    """
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        dataset_dir = os.path.join(base_path, "dataset")
        self.classifier = ErrorClassifierEngine(dataset_dir)
        self.executor = DockerExecutor(self.classifier, dry_run=dry_run)

    def run_guided_workflow(self):
        click.clear()
        click.secho("=== Docker Guided Workflow Mode ===", fg="blue", bold=True)
        
        # Step 1: Environment Validation
        click.secho("\n[1] Validating Docker Environment...", fg="yellow")
        checks = [
            (is_docker_installed(), "Docker installed"),
            (is_docker_running(), "Docker daemon running")
        ]
        
        fatal = False
        for success, msg in checks:
            icon = "✔" if success else "❌"
            color = "green" if success else "red"
            click.secho(f"  {icon} {msg}", fg=color)
            if not success:
                fatal = True
        
        if fatal:
            click.secho("\nFatal: Docker environment not ready.", fg="red", bold=True)
            return

        # Step 2: Template Selection
        click.secho("\n[2] Select Template", fg="yellow")
        options = [
            "Create Node Web App Container",
            "Create Python Web App Container",
            "Run MySQL Database",
            "Run PostgreSQL Database",
            "Build Image from Current Folder",
            "Debug Running Container",
            "Stop Container Safely",
            "Exit"
        ]
        
        for i, opt in enumerate(options, 1):
            click.echo(f"{i}. {opt}")
            
        choice = click.prompt("\nSelect an option", type=int, default=len(options))
        
        if choice >= len(options):
            return

        selected_key = list(DOCKER_TEMPLATES.keys())[choice-1] if choice <= 4 else None
        
        if choice <= 4:
            self._run_predefined_template(selected_key)
        elif choice == 5:
            self._build_current_folder()
        elif choice == 6:
            self._debug_container()
        elif choice == 7:
            self._stop_container()

    def _run_predefined_template(self, template_key):
        template = DOCKER_TEMPLATES[template_key]
        click.secho(f"\n--- {template['name']} ---", fg="cyan")
        
        # Structured Inputs
        c_name = click.prompt("Container name", default=template_key.replace("_", "-"))
        port = click.prompt("Host port mapping (Host:Container)", default=f"{template['steps'][1].get('port', 8080)}:{template['steps'][1].get('port', 8080)}")
        env_vars = click.prompt("Environment variables (KEY=VAL, separated by comma)", default="", show_default=False)
        volumes = click.prompt("Volume mapping (Host:Container, optional)", default="", show_default=False)
        
        # Validate Inputs
        port_host = int(port.split(':')[0])
        if not is_port_free(port_host):
            click.secho(f"❌ Port {port_host} is already in use!", fg="red")
            return
        if container_exists(c_name):
            click.secho(f"❌ Container named '{c_name}' already exists!", fg="red")
            return

        # Execution
        click.secho("\n[3] Executing Workflow...", fg="yellow")
        for step in template['steps']:
            if 'cmd' in step:
                cmd = step['cmd'].split()
                # Inject user inputs into the 'run' command
                if "run" in cmd:
                    # Insert name and port
                    for i, arg in enumerate(cmd):
                        if arg == "--name": cmd[i+1] = c_name
                        if arg == "-p": cmd[i+1] = port
                    
                    # Insert Envs
                    if env_vars:
                        for ev in env_vars.split(','):
                            cmd.insert(cmd.index("run") + 1, f"{ev.strip()}")
                            cmd.insert(cmd.index("run") + 1, "-e")
                            
                    # Insert Volumes
                    if volumes:
                        for vol in volumes.split(','):
                            cmd.insert(cmd.index("run") + 1, f"{vol.strip()}")
                            cmd.insert(cmd.index("run") + 1, "-v")
                
                if not self.executor.execute(cmd, step['desc']):
                    return
        
        click.secho("\n✔ SUCCESS: Container is running!", fg="green", bold=True)
        click.echo(template['summary'])

    def _build_current_folder(self):
        if not os.path.exists("Dockerfile"):
            click.secho("❌ No Dockerfile found in current directory.", fg="red")
            return
        
        tag = click.prompt("Image tag", default="myapp:latest")
        self.executor.execute(["docker", "build", "-t", tag, "."], f"Building image {tag}")

    def _debug_container(self):
        c_name = click.prompt("Enter container name to debug")
        if not container_exists(c_name):
            click.secho(f"❌ Container '{c_name}' not found.", fg="red")
            return
        
        click.echo("Running 'docker logs' and 'docker stats'...")
        self.executor.execute(["docker", "logs", "--tail", "20", c_name], "Fetching logs")
        self.executor.execute(["docker", "inspect", "-f", "{{.State.Status}}", c_name], "Checking status")

    def _stop_container(self):
        c_name = click.prompt("Enter container name to stop")
        if not container_exists(c_name):
             click.secho(f"❌ Container '{c_name}' not found.", fg="red")
             return
             
        self.executor.execute(["docker", "stop", c_name], f"Stopping {c_name}")
        if click.confirm(f"Remove container {c_name}?", default=False):
            self.executor.execute(["docker", "rm", c_name], f"Removing {c_name}")
