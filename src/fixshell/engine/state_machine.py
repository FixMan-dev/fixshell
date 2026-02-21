
import subprocess
import click
import os
from .error_classifier import ErrorClassifierEngine

class ErrorCategory:
    FATAL = "FATAL"
    RECOVERABLE = "RECOVERABLE"
    RETRYABLE = "RETRYABLE"
    INFORMATIONAL = "INFORMATIONAL"

class WorkflowStateMachine:
    def __init__(self, classifier, registry, dry_run=False, mode=None):
        self.classifier = classifier
        self.registry = registry
        self.dry_run = dry_run
        self.mode = mode

    def execute_step(self, cmd_list: list, step_desc: str, context_manager=None, interactive=False) -> bool:
        """
        Runs a step in a Layered Recovery Loop.
        """
        max_retries = 3
        retry_count = 0
        tried_categories = set()

        while retry_count <= max_retries:
            cmd_str = " ".join(cmd_list)
            click.echo(f"\n🚀 {click.style(step_desc, bold=True)}")
            
            # Show the command prominently
            click.echo(click.style("   COMMAND: ", fg="bright_black") + click.style(f" {cmd_str} ", bg="bright_black", fg="white", bold=True))
            
            if self.dry_run:
                click.secho("   ✔ [DRY-RUN] Success", fg="blue", italic=True)
                return True

            env = os.environ.copy()
            env["GIT_TERMINAL_PROMPT"] = "0" 

            if interactive:
                click.secho("   (Switching to Interactive Mode...)", fg="yellow", dim=True)
                result = subprocess.run(cmd_list, env=env)
                if result.returncode == 0:
                    click.secho("   ✔ Execution Successful", fg="green", bold=True)
                    if context_manager: context_manager.refresh()
                    return True
                else:
                    click.secho(f"   ❌ Command failed with exit code {result.returncode}", fg="red", bold=True)
                    return False

            result = subprocess.run(cmd_list, capture_output=True, text=True, env=env)
            
            if result.returncode == 0:
                if result.stdout:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) < 5:
                        for line in lines: click.echo(f"   {line}")
                    else:
                        click.echo(f"   {lines[0]} ... (+{len(lines)-1} lines)")
                
                click.secho("   ✔ Success", fg="green", bold=True)
                if context_manager: context_manager.refresh()
                return True

            # Diagnosis Phase
            output = result.stderr or result.stdout
            diagnosis = self.classifier.classify(output, mode=self.mode)
            err_type = diagnosis.get("type", ErrorCategory.FATAL)
            category = diagnosis.get("category", "UNKNOWN")

            if err_type == ErrorCategory.INFORMATIONAL:
                click.secho("   ✔ (Info)", fg="blue")
                return True

            # Check if this failure is actually a "post-fix artifact" 
            # (e.g., branch already deleted by the fix)
            if retry_count > 0 and category == "UNKNOWN":
                if "not found" in output.lower() or "already exists" in output.lower():
                    click.secho("   ✔ (Assuming Success: Operation likely finalized by previous fix)", fg="green")
                    return True

            if category in tried_categories:
                click.secho(f"\n   ❌ Resolution for '{category}' failed to shift state.", fg="red", bold=True)
                self._on_fatal(diagnosis, output)
                return False

            if err_type == ErrorCategory.RECOVERABLE:
                click.secho(f"   💊 Needs Resolution: {category}", fg="yellow")
                
                # 1. Try Registry Resolver
                resolver = self.registry.get_resolver(category)
                if resolver:
                    tried_categories.add(category)
                    matches = diagnosis.get("matches", [])
                    if resolver(matches, dry_run=self.dry_run):
                        click.secho("   ♻ Resolution applied. Retrying...", fg="cyan")
                        if context_manager: context_manager.refresh()
                        retry_count += 1
                        continue 
                
                # 2. Try Template-based Fixes
                fix_templates = diagnosis.get("fix_commands")
                if fix_templates:
                    click.secho("\n   💡 Suggested Fix (Template-based):", fg="cyan", bold=True)
                    matches = list(diagnosis.get("matches", []))
                    resolved_cmds = []
                    for tmpl in fix_templates:
                        rc = []
                        for part in tmpl:
                            if isinstance(part, str):
                                for i, m in enumerate(matches, 1):
                                    part = part.replace(f"{{MATCH_{i}}}", str(m))
                                rc.append(part)
                            else: rc.append(part)
                        resolved_cmds.append(rc)
                    
                    for rc in resolved_cmds:
                        click.secho(f"     → {' '.join(rc)}", fg="white", italic=True)
                    
                    if click.confirm(click.style("\n   Apply this fix?", fg="cyan", bold=True), default=True):
                        fix_success = True
                        for rc in resolved_cmds:
                            click.echo(f"   Applying: {' '.join(rc)}...", nl=False)
                            if not self.dry_run:
                                f_res = subprocess.run(rc, capture_output=True, text=True)
                                if f_res.returncode == 0: click.secho(" ✔", fg="green")
                                else:
                                    click.secho(" ❌", fg="red")
                                    click.echo(f"     Error: {f_res.stderr.strip()}")
                                    fix_success = False; break
                            else: click.secho(" ✔ [DRY-RUN]", fg="blue")
                        
                        if fix_success:
                            click.secho("   ♻ Fix applied. Retrying...", fg="cyan")
                            if context_manager: context_manager.refresh()
                            tried_categories.add(category)
                            retry_count += 1
                            continue

            # Escalate to Fatal
            click.secho("   ❌ Critical failure detected.", fg="red")
            self._on_fatal(diagnosis, output)
            return False

        click.secho(f"\n❌ Aborted: Max attempts reached.", fg="red", bold=True)
        return False

    def _on_fatal(self, diagnosis, raw_stderr):
        click.secho("\n--- FATAL ERROR: UNRECOVERABLE ---", fg="red", bold=True)
        click.echo(f"Category: {diagnosis.get('category')}")
        click.echo(f"Suggestion: {diagnosis.get('suggested_fix', ['None'])[0]}")
        click.secho("\nRaw Stderr:", fg="white", dim=True)
        click.secho(raw_stderr, fg="red", dim=True)
        click.echo("-" * 40)
