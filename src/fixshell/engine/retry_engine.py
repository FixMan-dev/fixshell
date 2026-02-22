from .executor import Executor
from .classifier import ErrorCategory
from ..ui.renderer import Renderer
from typing import Optional, Callable, Dict, Any

class RetryEngine:
    """
    Universal recovery logic that implements the recursive 
    'Execute-Classify-Resolve' loop.
    """

    def __init__(self, classifier, registry, executor: Executor, mode: Optional[str] = None):
        self.classifier = classifier
        self.registry = registry
        self.executor = executor
        self.mode = mode

    def execute_with_recovery(self, cmd_list: list, desc: str, context_manager=None, interactive: bool = False, state: Dict[str, Any] = None) -> bool:
        max_retries = 3
        retry_count = 0
        tried_categories = set()

        while retry_count <= max_retries:
            result = self.executor.run(cmd_list, desc, interactive=interactive)

            if result.returncode == 0:
                Renderer.print_success()
                if context_manager: context_manager.refresh()
                return True

            # Diagnosis Phase
            output = result.stderr or result.stdout
            # Use the provided classifier to understand what happened
            # Note: We expect classifier to have a classify(output, mode) method
            diagnosis = self.classifier.classify(output, mode=self.mode)
            
            err_type = diagnosis.get("type", "FATAL")
            category = diagnosis.get("category", "UNKNOWN")

            if err_type == "INFORMATIONAL":
                Renderer.print_info("Informational message detected.")
                return True

            # State Shift Check
            if category in tried_categories:
                Renderer.print_error(f"Resolution for '{category}' failed to shift state.")
                Renderer.print_fatal(category, diagnosis.get("suggested_fix", ["None"])[0], output)
                return False

            if err_type == "RECOVERABLE":
                Renderer.print_resolution(category)
                
                # 1. Try Registry Resolver (Dynamic Logic)
                resolver = self.registry.get_resolver(category)
                if resolver:
                    tried_categories.add(category)
                    matches = diagnosis.get("matches", [])
                    if resolver(matches, dry_run=self.executor.dry_run, state=state):
                        Renderer.print_info("Resolution applied. Retrying original command...")
                        if context_manager: context_manager.refresh()
                        retry_count += 1
                        continue

                # 2. Try Template-Based Fixes (Deterministic Patterns)
                fix_commands = diagnosis.get("fix_commands")
                if fix_commands:
                    if self._apply_template_fix(fix_commands, diagnosis.get("matches", [])):
                        tried_categories.add(category)
                        retry_count += 1
                        continue

            # If we reach here, it's a fatal failure or unresolvable
            Renderer.print_error("Critical failure detected.")
            Renderer.print_fatal(category, diagnosis.get("suggested_fix", ["None"])[0], output)
            return False

        Renderer.print_error("Aborted: Max recovery attempts reached.")
        return False

    def _apply_template_fix(self, fix_templates: list, matches: list) -> bool:
        """
        Resolves {MATCH_n} placeholders and executes the suggested fix.
        """
        Renderer.print_info("Found Template-Based Fix")
        resolved_cmds = []
        for tmpl in fix_templates:
            rc = []
            for part in tmpl:
                if isinstance(part, str):
                    for i, m in enumerate(matches, 1):
                        part = part.replace(f"{{MATCH_{i}}}", str(m))
                    rc.append(part)
                else:
                    rc.append(part)
            resolved_cmds.append(rc)

        for rc in resolved_cmds:
            Renderer.print_info(f"→ Suggestion: {' '.join(rc)}")

        if self.executor.confirm("Apply this suggested fix?"):
            for rc in resolved_cmds:
                res = self.executor.run(rc, f"Applying fix: {' '.join(rc)}", capture=True)
                if res.returncode != 0:
                    Renderer.print_error(f"Fix failed: {res.stderr}")
                    return False
            return True
        return False
