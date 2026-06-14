#!/usr/bin/env python3
"""Ordia CLI — init, validate, doctor, help, commands."""

from __future__ import annotations

import argparse
import json
import shlex
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

from ordia.bootstrap import repo_root_from_core
from ordia.config import load_ordia_config, templates_root, validate_ordia_manifest
from ordia.protocols import protocols_root


def _repo_root() -> Path:
    return repo_root_from_core() or Path.cwd().resolve()


def _cursor_bundle() -> Path:
    root = _repo_root()
    return root / "packages" / "ordia-cursor" / "templates"


def _today() -> str:
    return date.today().isoformat()


def _render(text: str, profile: str, product_root: str) -> str:
    return (
        text.replace("{{PROFILE}}", profile)
        .replace("{{PRODUCT_ROOT}}", product_root.rstrip("/") + "/")
        .replace("{{DATE}}", _today())
    )


def _copy_template_tree(template_dir: Path, target_root: Path, profile: str, product_root: str) -> list[Path]:
    written: list[Path] = []
    for path in sorted(template_dir.rglob("*")):
        if path.is_dir():
            continue
        relative = path.relative_to(template_dir)
        if relative.name == "ordia.yaml":
            continue
        dest = target_root / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        content = _render(path.read_text(encoding="utf-8"), profile, product_root)
        dest.write_text(content, encoding="utf-8")
        written.append(dest)
    return written


def _install_protocol_templates(target: Path, profile: str, product_root: str) -> list[Path]:
    src = protocols_root()
    if not src.is_dir():
        return []
    dest = target / "docs" / "control" / "protocols"
    dest.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for path in sorted(src.glob("*.md")):
        content = _render(path.read_text(encoding="utf-8"), profile, product_root)
        out = dest / path.name
        out.write_text(content, encoding="utf-8")
        written.append(out)
    return written


def _install_cursor_bundle(target: Path) -> None:
    bundle = _cursor_bundle()
    if not bundle.is_dir():
        raise FileNotFoundError("Ordia Cursor template bundle missing (packages/ordia-cursor/templates)")
    dest = target / ".cursor"
    dest.mkdir(parents=True, exist_ok=True)
    python_exe = sys.executable
    python_token = f'"{python_exe}"' if " " in python_exe else python_exe
    python_token = python_token.replace("\\", "/")
    hooks_json = bundle / "hooks.json"
    if hooks_json.is_file():
        hooks_text = hooks_json.read_text(encoding="utf-8").replace("{PYTHON}", python_token)
        (dest / "hooks.json").write_text(hooks_text, encoding="utf-8")
    hooks_src = bundle / "hooks"
    hooks_dest = dest / "hooks"
    if hooks_src.is_dir():
        if hooks_dest.exists():
            shutil.rmtree(hooks_dest)
        shutil.copytree(hooks_src, hooks_dest)
    rules_src = bundle / "rules"
    rules_dest = dest / "rules"
    if rules_src.is_dir():
        rules_dest.mkdir(parents=True, exist_ok=True)
        for rule in rules_src.glob("*.mdc"):
            shutil.copy2(rule, rules_dest / rule.name)


def _package_docs_root() -> Path:
    return Path(__file__).resolve().parent.parent / "docs"


def _bundled_product_docs_root() -> Path | None:
    bundled = Path(__file__).resolve().parent / "product_docs"
    return bundled if bundled.is_dir() else None


def _product_docs_root(from_repo_docs: bool = False) -> Path | None:
    if from_repo_docs:
        repo = _repo_root()
        repo_ordia = repo / "docs" / "ordia"
        if repo_ordia.is_dir() and (repo_ordia / "README.md").is_file():
            return repo_ordia
    return _bundled_product_docs_root()


PRODUCT_DOC_NAMES = (
    "README.md",
    "DAILY_USAGE.md",
    "SPEC_v0.2.md",
    "SPEC_v0.6.md",
    "SPEC_v0.7.md",
    "SPEC_v0.8.md",
)


def _install_product_docs(target: Path, *, from_repo_docs: bool = False) -> list[Path]:
    src_root = _product_docs_root(from_repo_docs=from_repo_docs)
    if src_root is None:
        return []
    dest = target / "docs" / "ordia"
    dest.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name in PRODUCT_DOC_NAMES:
        src = src_root / name
        if not src.is_file():
            continue
        out = dest / name
        if not out.exists() or src.stat().st_mtime >= out.stat().st_mtime:
            shutil.copy2(src, out)
        written.append(out)
    return written


def _install_package_docs(target: Path) -> list[Path]:
    src = _package_docs_root()
    if not src.is_dir():
        return []
    dest = target / "docs" / "ordia" / "package"
    dest.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for path in sorted(src.glob("*.md")):
        out = dest / path.name
        shutil.copy2(path, out)
        written.append(out)
    return written


def cmd_init(args: argparse.Namespace) -> int:
    target = Path(args.directory).resolve()
    target.mkdir(parents=True, exist_ok=True)
    manifest = target / "ordia.yaml"
    if manifest.exists() and not args.force:
        print(f"ERROR: {manifest} already exists (use --force to overwrite scaffold only)", file=sys.stderr)
        return 1

    template_name = args.template
    template_dir = templates_root() / template_name
    if not template_dir.is_dir():
        print(f"ERROR: unknown template {template_name!r}", file=sys.stderr)
        return 1

    profile = args.profile
    product_root = args.product_root
    if template_name == "monorepo" and args.product_root == "src/":
        product_root = "apps/"

    ordia_template = template_dir / "ordia.yaml"
    manifest.write_text(
        _render(ordia_template.read_text(encoding="utf-8"), profile, product_root),
        encoding="utf-8",
    )
    written = _copy_template_tree(template_dir, target, profile, product_root)
    protocol_written = _install_protocol_templates(target, profile, product_root)
    written.extend(protocol_written)

    product_written = _install_product_docs(target, from_repo_docs=getattr(args, "from_repo_docs", False))
    written.extend(product_written)

    if args.with_cursor:
        _install_cursor_bundle(target)
    if getattr(args, "with_docs", False):
        doc_written = _install_package_docs(target)
        written.extend(doc_written)

    print(f"Ordia init complete — profile={profile!r} template={template_name!r}")
    print(f"- wrote {manifest.relative_to(target)}")
    for path in written:
        print(f"- wrote {path.relative_to(target)}")
    if product_written:
        source = "repo docs/ordia/" if getattr(args, "from_repo_docs", False) else "bundled product_docs/"
        print(f"- installed portable product documentation under docs/ordia/ (from {source})")
    if args.with_cursor:
        print("- installed .cursor hooks and ordia rules")
    if getattr(args, "with_docs", False):
        print("- installed package documentation under docs/ordia/package/")
    if protocol_written:
        print(f"- installed {len(protocol_written)} protocol templates under docs/control/protocols/")
    print("Next: npm run ordia:validate")
    return 0


def _session_declared_profile(root: Path) -> str | None:
    session_file = root / ".cursor" / "session-protocol.json"
    if not session_file.is_file():
        return None
    try:
        data = json.loads(session_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if isinstance(data, dict) and data.get("ordia_profile"):
        return str(data["ordia_profile"])
    return None


def cmd_validate(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    config = load_ordia_config(root)
    if config is None:
        print("ERROR: ordia.yaml missing or invalid", file=sys.stderr)
        return 1

    errors: list[str] = []
    warnings: list[str] = []
    validate_ordia_manifest(config, errors, warnings)
    for warning in warnings:
        print(f"WARNING: {warning}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print("RESULT: FAIL")
        return 1

    print("Ordia manifest validation")
    print(f"- profile: {config.profile}")
    print(f"- version: {config.version}")
    print(f"- control root: {config.control_root.relative_to(root)}")
    print(f"- warnings: {len(warnings)}")
    print(f"- errors: 0")

    if args.project:
        from ordia.validator.project import ProjectValidationOptions, validate_project

        opts = ProjectValidationOptions(
            require_cursor_workspace=(root / ".cursor" / "hooks.json").is_file(),
            strict_profile=bool(getattr(args, "strict_profile", False)),
            strict_closure=bool(getattr(args, "strict_closure", False)),
            strict_model_report=bool(getattr(args, "strict_model_report", False)),
            session_profile=_session_declared_profile(root),
        )
        if config.profile == "narofitness":
            opts.profile_cursor_rules = [".cursor/rules/narofitness-permanent-guardrails.mdc"]
            opts.validate_inventory = True
            opts.inventory_path = str(config.control_root / "DOCUMENTATION_INVENTORY.md")
        result = validate_project(root, config, opts)
        for warning in result.warnings:
            print(f"WARNING: {warning}")
        if result.errors:
            for error in result.errors:
                print(f"ERROR: {error}", file=sys.stderr)
            print("RESULT: FAIL")
            return 1
        print("Project validation")
        print(f"- warnings: {len(result.warnings)}")
        print(f"- errors: 0")

    print("RESULT: PASS")
    return 0


def _find_ordia_core(root: Path) -> Path | None:
    for candidate in (
        root / "packages" / "ordia-core",
        root / "vendor" / "ordia-core",
    ):
        if (candidate / "ordia" / "config.py").is_file():
            return candidate
    repo = _repo_root()
    if repo and repo != root:
        monorepo_core = repo / "packages" / "ordia-core"
        if (monorepo_core / "ordia" / "config.py").is_file():
            return monorepo_core
    return None


def _verify_hook_commands(root: Path) -> list[str]:
    issues: list[str] = []
    hooks_json = root / ".cursor" / "hooks.json"
    if not hooks_json.is_file():
        return issues
    try:
        data = json.loads(hooks_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        issues.append("Could not parse .cursor/hooks.json")
        return issues
    hooks = data.get("hooks") if isinstance(data, dict) else None
    if not isinstance(hooks, dict):
        return issues
    for event_hooks in hooks.values():
        if not isinstance(event_hooks, list):
            continue
        for entry in event_hooks:
            if not isinstance(entry, dict):
                continue
            command = str(entry.get("command", "")).strip()
            if not command or "{PYTHON}" in command:
                issues.append("Hook command missing or still contains {PYTHON} placeholder")
                continue
            try:
                parts = shlex.split(command, posix=False)
            except ValueError as exc:
                issues.append(f"Hook command could not be parsed: {exc}")
                continue
            if len(parts) < 2:
                issues.append(f"Hook command incomplete: {command!r}")
                continue
            python_exe = parts[0]
            script_rel = parts[1]
            exe_path = Path(python_exe)
            if not exe_path.is_file() and shutil.which(python_exe) is None:
                issues.append(f"Hook Python executable not invocable: {python_exe}")
            script_path = (root / script_rel).resolve()
            try:
                script_path.relative_to(root.resolve())
            except ValueError:
                issues.append(f"Hook script escapes project root: {script_rel}")
                continue
            if not script_path.is_file():
                issues.append(f"Hook script missing: {script_rel}")
                continue
            try:
                probe = subprocess.run(
                    [python_exe, "-m", "py_compile", str(script_path)],
                    cwd=root,
                    capture_output=True,
                    text=True,
                    timeout=15,
                    check=False,
                )
            except (OSError, subprocess.SubprocessError) as exc:
                issues.append(f"Hook script probe failed for {script_rel}: {exc}")
                continue
            if probe.returncode != 0:
                detail = (probe.stderr or probe.stdout or "").strip()[-200:]
                issues.append(f"Hook script failed py_compile ({script_rel}): {detail or 'syntax error'}")
    return issues


def _commands_paths(args: argparse.Namespace) -> tuple[Path, Path, Path]:
    root = Path(args.directory).resolve()
    config = load_ordia_config(root)
    from ordia.commands.catalog import resolve_catalog_paths

    catalog_path, package_path = resolve_catalog_paths(root, config)
    return root, catalog_path, package_path


def cmd_help(args: argparse.Namespace) -> int:
    from ordia.commands.catalog import load_catalog, load_package_scripts
    from ordia.commands.help_text import format_command_detail, format_help_list, format_help_overview

    root, catalog_path, package_path = _commands_paths(args)
    if not catalog_path.is_file():
        print(f"ERROR: commands catalog missing: {catalog_path.relative_to(root)}", file=sys.stderr)
        return 1

    try:
        catalog = load_catalog(catalog_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: could not load catalog: {exc}", file=sys.stderr)
        return 1

    if args.list:
        print(format_help_list(catalog))
        return 0

    if args.command_name:
        scripts = load_package_scripts(package_path) if package_path.is_file() else {}
        text, code = format_command_detail(args.command_name, catalog, scripts)
        print(text)
        return code

    print(format_help_overview(catalog))
    return 0


def cmd_commands_validate(args: argparse.Namespace) -> int:
    from ordia.commands.catalog import validate_catalog_sync

    root, catalog_path, package_path = _commands_paths(args)
    errors, count = validate_catalog_sync(root, catalog_path, package_path)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print("RESULT: FAIL")
        return 1
    print(f"OK: catalog in sync ({count} root commands).")
    print("RESULT: PASS")
    return 0


def cmd_model_recommend(args: argparse.Namespace) -> int:
    from ordia.model_routing import default_registry_path, recommend_for_task

    root = Path(args.directory).resolve()
    task_id = args.task.strip()
    if not task_id:
        print("ERROR: --task is required", file=sys.stderr)
        return 1

    packet_text: str | None = None
    task_entry: dict[str, Any] | None = None
    config = load_ordia_config(root)
    if config is not None:
        packet_path = config.task_packets_dir / f"{task_id}.md"
        if packet_path.is_file():
            packet_text = packet_path.read_text(encoding="utf-8")
        if config.task_registry_path.is_file():
            try:
                import yaml

                reg_data = yaml.safe_load(config.task_registry_path.read_text(encoding="utf-8"))
                tasks = reg_data.get("tasks", []) if isinstance(reg_data, dict) else []
                if isinstance(tasks, list):
                    for entry in tasks:
                        if isinstance(entry, dict) and str(entry.get("id")) == task_id:
                            task_entry = entry
                            break
            except Exception:  # noqa: BLE001
                pass

    runtime = args.runtime or "ONLY_CURSOR"
    config_default_tier = config.models_default_tier if config is not None else None
    recommendation = recommend_for_task(
        task_id,
        root=root,
        registry_path=default_registry_path(root),
        packet_text=packet_text,
        task_entry=task_entry,
        runtime=runtime,
        prompt=args.prompt,
        config_default_tier=config_default_tier,
    )
    if args.json:
        print(
            json.dumps(
                {
                    "tier": recommendation.tier,
                    "rationale": recommendation.rationale,
                    "runtime": recommendation.runtime,
                    "cursor_primary": recommendation.cursor_primary,
                    "codex_primary": recommendation.codex_primary,
                    "cost_band": recommendation.cost_band,
                    "economic_rating": recommendation.economic_rating,
                    "track_minimum": recommendation.track_minimum,
                },
                indent=2,
            )
        )
    else:
        print(recommendation.format_block())
    return 0


def cmd_model_usage_template(args: argparse.Namespace) -> int:
    from ordia.model_routing import usage_section_template

    print(usage_section_template())
    return 0


def cmd_workflow_list(args: argparse.Namespace) -> int:
    from ordia.workflows import list_intents

    root = Path(args.directory).resolve()
    items = list_intents(root, category=args.category)
    if args.json:
        payload = [
            {
                "id": item.id,
                "category": item.category,
                "title": item.title,
                "runtime": item.runtime,
                "protocol": item.protocol,
                "requires_task": item.requires_task,
            }
            for item in items
        ]
        print(json.dumps(payload, indent=2))
        return 0
    for item in items:
        print(f"{item.id:22} [{item.category:8}] {item.title}")
    print(f"\nTotal: {len(items)} intents")
    return 0


def cmd_workflow_describe(args: argparse.Namespace) -> int:
    from ordia.workflows import describe_intent

    root = Path(args.directory).resolve()
    print(describe_intent(root, args.intent_id))
    return 0


def cmd_prompt_emit(args: argparse.Namespace) -> int:
    from ordia.workflows import emit_prompt

    root = Path(args.directory).resolve()
    try:
        block = emit_prompt(
            root,
            args.intent,
            task_id=args.task,
            agent=args.agent,
            runtime=args.runtime,
            protocol=args.protocol,
            mode=args.mode,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps({"prompt": block}, indent=2))
    else:
        print(block)
    return 0


def cmd_prompt_header(args: argparse.Namespace) -> int:
    from ordia.workflows import emit_header

    root = Path(args.directory).resolve()
    try:
        block = emit_header(
            root,
            args.intent,
            task_id=args.task,
            agent=args.agent,
            runtime=args.runtime,
            protocol=args.protocol,
            mode=args.mode,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps({"header": block}, indent=2))
    else:
        print(block)
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    issues: list[str] = []
    hints: list[str] = []

    manifest = root / "ordia.yaml"
    if not manifest.is_file():
        issues.append("ordia.yaml is missing — run: npm run ordia:init")
    else:
        hints.append(f"manifest: {manifest.relative_to(root)}")

    config = load_ordia_config(root)
    if config is None and manifest.is_file():
        issues.append("ordia.yaml could not be loaded (install PyYAML: npm run control:install)")
    elif config is not None:
        errors: list[str] = []
        warnings: list[str] = []
        validate_ordia_manifest(config, errors, warnings)
        issues.extend(errors)
        for warning in warnings:
            hints.append(f"warning: {warning}")

    hooks_json = root / ".cursor" / "hooks.json"
    rules_dir = root / ".cursor" / "rules"
    manifest_loader = root / ".cursor" / "hooks" / "lib" / "ordia_manifest.py"
    if hooks_json.is_file():
        hints.append("Cursor hooks: installed")
        issues.extend(_verify_hook_commands(root))
    else:
        hints.append("Cursor hooks: not installed (optional: ordia init --with-cursor)")
    if manifest_loader.is_file():
        hints.append("Inline manifest loader: installed")
    else:
        hints.append("Inline manifest loader: not installed (use --with-cursor on init)")
    if rules_dir.is_dir() and any(rules_dir.glob("ordia-*.mdc")):
        hints.append("Ordia Cursor rules: installed")
    else:
        hints.append("Ordia Cursor rules: not installed (use --with-cursor on init)")

    if config is not None and hasattr(config, "models_telemetry_root"):
        telemetry = config.models_telemetry_root
        try:
            telemetry.mkdir(parents=True, exist_ok=True)
            hints.append(f"Model telemetry root: {telemetry.relative_to(root)} (writable)")
        except OSError as exc:
            issues.append(f"Model telemetry root not writable: {exc}")

    core = _find_ordia_core(root)
    if core is not None:
        try:
            hints.append(f"ordia-core package: {core.relative_to(root)}")
        except ValueError:
            hints.append(f"ordia-core package: {core}")
    else:
        hints.append("ordia-core package: not in target (optional for CLI; hooks use inline loader)")

    try:
        import yaml  # noqa: F401
    except ImportError:
        issues.append("PyYAML not installed — run: npm run control:install")

    print("Ordia doctor")
    for hint in hints:
        print(f"- {hint}")
    if issues:
        print(f"- issues: {len(issues)}")
        for issue in issues:
            print(f"  ERROR: {issue}", file=sys.stderr)
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ordia", description="Ordia control-plane CLI")
    root_parent = argparse.ArgumentParser(add_help=False)
    root_parent.add_argument("--directory", "-C", default=".", help="Repository root (default: .)")
    sub = parser.add_subparsers(dest="command", required=True)

    init_parser = sub.add_parser("init", help="Scaffold ordia.yaml and control store", parents=[root_parent])
    init_parser.add_argument("--profile", default="default", help="Project profile id")
    init_parser.add_argument(
        "--template",
        choices=("minimal", "monorepo"),
        default="minimal",
        help="Scaffold template (monorepo defaults product root to apps/)",
    )
    init_parser.add_argument("--product-root", default="src/", help="Product code root for enforcement")
    init_parser.add_argument("--with-cursor", action="store_true", help="Install Cursor hooks and ordia rules")
    init_parser.add_argument(
        "--with-docs",
        action="store_true",
        help="Copy ordia-core package manuals to docs/ordia/package/ (technical docs)",
    )
    init_parser.add_argument(
        "--from-repo-docs",
        action="store_true",
        help="Copy live docs/ordia/ from reference repo instead of bundled portable product_docs (reference only)",
    )
    init_parser.add_argument("--force", action="store_true", help="Allow init when ordia.yaml exists")
    init_parser.set_defaults(func=cmd_init)

    validate_parser = sub.add_parser("validate", help="Validate ordia.yaml and control paths", parents=[root_parent])
    validate_parser.add_argument(
        "--project",
        action="store_true",
        help="Also run manifest-driven project registry/state validation",
    )
    validate_parser.add_argument(
        "--strict-profile",
        action="store_true",
        help="Fail when Ordia profile header does not match ordia.yaml",
    )
    validate_parser.add_argument(
        "--strict-closure",
        action="store_true",
        help="Fail when VALIDATED tasks miss RUNTIME-D006 closure evidence",
    )
    validate_parser.add_argument(
        "--strict-model-report",
        action="store_true",
        help="Warn when VALIDATED tasks lack Model usage evidence",
    )
    validate_parser.set_defaults(func=cmd_validate)

    model_parser = sub.add_parser("model", help="Model tier routing utilities", parents=[root_parent])
    model_sub = model_parser.add_subparsers(dest="model_cmd", required=True)
    recommend_parser = model_sub.add_parser(
        "recommend",
        help="Recommend model tier for a task",
        parents=[root_parent],
    )
    recommend_parser.add_argument("--task", required=True, help="Task ID")
    recommend_parser.add_argument(
        "--runtime",
        choices=("ONLY_CURSOR", "ONLY_CODEX", "CODEX_PLUS_CURSOR"),
        help="Runtime for recommendation display",
    )
    recommend_parser.add_argument("--prompt", help="Optional prompt text for read-only detection")
    recommend_parser.add_argument("--json", action="store_true", help="Emit JSON instead of prompt block")
    recommend_parser.set_defaults(func=cmd_model_recommend)

    usage_template_parser = model_sub.add_parser(
        "usage-template",
        help="Print canonical Model usage section for executor deliverables",
        parents=[root_parent],
    )
    usage_template_parser.set_defaults(func=cmd_model_usage_template)

    workflow_parser = sub.add_parser("workflow", help="Workflow intent catalog", parents=[root_parent])
    workflow_sub = workflow_parser.add_subparsers(dest="workflow_cmd", required=True)
    workflow_list = workflow_sub.add_parser("list", help="List workflow intents", parents=[root_parent])
    workflow_list.add_argument(
        "--category",
        choices=("control", "planning", "work", "quality", "domain"),
        help="Filter by category",
    )
    workflow_list.add_argument("--json", action="store_true", help="Emit JSON")
    workflow_list.set_defaults(func=cmd_workflow_list)
    workflow_describe = workflow_sub.add_parser("describe", help="Describe one intent", parents=[root_parent])
    workflow_describe.add_argument("intent_id", help="Intent id (e.g. implement_feature)")
    workflow_describe.set_defaults(func=cmd_workflow_describe)

    prompt_parser = sub.add_parser("prompt", help="Emit standardized prompt blocks", parents=[root_parent])
    prompt_sub = prompt_parser.add_subparsers(dest="prompt_cmd", required=True)
    prompt_emit = prompt_sub.add_parser("emit", help="Full prompt block", parents=[root_parent])
    prompt_emit.add_argument("--intent", required=True, help="Workflow intent id")
    prompt_emit.add_argument("--task", help="Task ID")
    prompt_emit.add_argument("--agent", help="Agent identity override")
    prompt_emit.add_argument(
        "--runtime",
        choices=("ONLY_CURSOR", "ONLY_CODEX", "CODEX_PLUS_CURSOR"),
        help="Override default runtime",
    )
    prompt_emit.add_argument(
        "--protocol",
        choices=("ORCHESTRATION", "IMPLEMENTATION"),
        help="Override default protocol",
    )
    prompt_emit.add_argument("--mode", help="Override mode (Agent, Plan, QA, Audit)")
    prompt_emit.add_argument("--json", action="store_true", help="Emit JSON wrapper")
    prompt_emit.set_defaults(func=cmd_prompt_emit)
    prompt_header = prompt_sub.add_parser("header", help="Session header only", parents=[root_parent])
    prompt_header.add_argument("--intent", required=True, help="Workflow intent id")
    prompt_header.add_argument("--task", help="Task ID")
    prompt_header.add_argument("--agent", help="Agent identity override")
    prompt_header.add_argument(
        "--runtime",
        choices=("ONLY_CURSOR", "ONLY_CODEX", "CODEX_PLUS_CURSOR"),
    )
    prompt_header.add_argument(
        "--protocol",
        choices=("ORCHESTRATION", "IMPLEMENTATION"),
    )
    prompt_header.add_argument("--mode", help="Override mode")
    prompt_header.add_argument("--json", action="store_true")
    prompt_header.set_defaults(func=cmd_prompt_header)

    doctor_parser = sub.add_parser("doctor", help="Check Ordia setup and dependencies", parents=[root_parent])
    doctor_parser.set_defaults(func=cmd_doctor)

    help_parser = sub.add_parser("help", help="Command catalog overview, list, or detail", parents=[root_parent])
    help_parser.add_argument(
        "command_name",
        nargs="?",
        help="Command name for detail view (e.g. ordia:validate)",
    )
    help_parser.add_argument("--list", action="store_true", help="Print flat command list")
    help_parser.set_defaults(func=cmd_help)

    commands_parser = sub.add_parser("commands", help="Command catalog utilities", parents=[root_parent])
    commands_sub = commands_parser.add_subparsers(dest="commands_cmd", required=True)
    validate_catalog = commands_sub.add_parser(
        "validate",
        help="Validate catalog sync with package.json",
        parents=[root_parent],
    )
    validate_catalog.set_defaults(func=cmd_commands_validate)

    return parser


def _configure_stdout() -> None:
    """Use UTF-8 on Windows consoles so emitted prompts can print em-dashes."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass


def main() -> int:
    _configure_stdout()
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
