#!/usr/bin/env python3

"""beforeSubmitPrompt hook: warn when active model tier is below approved tier."""



from __future__ import annotations



import sys

from pathlib import Path



ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(ROOT / ".cursor" / "hooks"))



from lib.control_context import (  # noqa: E402

    detect_model_tier_approval,

    emit_json,

    is_change_capable_prompt,

    load_full_session,

    load_model_registry,

    model_slug_to_tier,

    models_require_approval_above,

    persist_session_from_prompt,

    read_state_fields,

    read_stdin_json,

    save_session,

    task_model_tier_min,

    tier_at_least,

    workspace_root_from_input,

)

from lib.model_routing_lite import (  # noqa: E402

    CODEX_RATE_LIMIT_NOTE,

    CURSOR_RATE_LIMIT_NOTE,

    is_cursor_auto_model,

)

from lib.workflow_intents_lite import validate_intent_in_prompt  # noqa: E402


def _allow(*, message: str | None = None, intent_warning: str | None = None) -> None:
    parts = [part for part in (intent_warning, message) if part]
    payload: dict[str, str] = {"permission": "allow"}
    if parts:
        payload["agent_message"] = " ".join(parts)
    emit_json(payload)





def main() -> int:

    try:

        return _main()

    except Exception as exc:  # noqa: BLE001

        emit_json({"permission": "allow", "agent_message": f"check_model_tier warning: {exc}"})

        return 0





def _main() -> int:

    payload = read_stdin_json()

    root = workspace_root_from_input(payload, __file__)

    prompt = str(payload.get("prompt") or "")

    active_model = str(payload.get("model") or "")

    intent_warning = validate_intent_in_prompt(root, prompt)



    approved_tier = detect_model_tier_approval(prompt)

    if approved_tier:

        existing = load_full_session(root) or {}

        task_id = existing.get("active_task_id") or read_state_fields(root).get("active_task_id")

        min_tier = task_model_tier_min(root, str(task_id) if task_id else None)

        if existing:

            save_session(

                root,

                existing["runtime"],

                existing["protocol"],

                "model_tier_approval",

                session_mode=existing.get("session_mode"),

                implementation_approved=existing.get("implementation_approved"),

                approved_model_tier=approved_tier,

                model_tier_approved=True,

            )

        if min_tier and not tier_at_least(approved_tier, min_tier):

            _allow(

                intent_warning=intent_warning,

                message=(

                    f"Model tier warning: APPROVE MODEL {approved_tier} is below task minimum {min_tier}"

                    f"{f' for {task_id}' if task_id else ''}. "

                    f"Use APPROVE MODEL {min_tier} or confirm override intentionally."

                ),

            )

            return 0

        _allow(intent_warning=intent_warning)

        return 0



    if prompt.strip():

        persist_session_from_prompt(root, prompt, "beforeSubmitPrompt")



    session = load_full_session(root)

    if not session:

        _allow(intent_warning=intent_warning)

        return 0



    runtime = str(session.get("runtime") or "")

    codex_runtime = runtime in {"ONLY_CODEX", "CODEX_PLUS_CURSOR"}



    if (

        session.get("protocol") == "IMPLEMENTATION"

        and not session.get("model_tier_approved")

        and is_change_capable_prompt(prompt)

    ):

        require_above = models_require_approval_above(root)

        if require_above and require_above != "T0":

            message = (

                f"Model tier approval required (policy: above {require_above}). "

                f"Run `npm run ordia -- model recommend --task <ID>` and reply APPROVE MODEL T* "

                "before change-capable implementation work."

            )

            if codex_runtime:

                message = f"{message} {CODEX_RATE_LIMIT_NOTE}"

            _allow(intent_warning=intent_warning, message=message)

            return 0



    if not session.get("model_tier_approved"):

        _allow(intent_warning=intent_warning)

        return 0



    approved = str(session.get("approved_model_tier") or "")

    if not approved or not active_model:

        _allow(intent_warning=intent_warning)

        return 0



    registry = load_model_registry(root)

    if not registry:

        _allow(

            intent_warning=intent_warning,

            message=(

                "Model registry unavailable; tier mismatch checks skipped. "

                "Ensure MODEL_REGISTRY.yaml exists and PyYAML is installed."

            ),

        )

        return 0



    active_tier = model_slug_to_tier(registry, active_model)

    if is_cursor_auto_model(active_model):

        auto_tier = active_tier or "T1"

        if not tier_at_least(auto_tier, approved):

            _allow(

                intent_warning=intent_warning,

                message=(

                    f"Cursor Auto Mode active (maps to {auto_tier}, approved {approved}). "

                    f"{CURSOR_RATE_LIMIT_NOTE}"

                ),

            )

        else:

            _allow(intent_warning=intent_warning)

        return 0



    if active_tier and not tier_at_least(active_tier, approved):

        _allow(

            intent_warning=intent_warning,

            message=(

                f"Model tier warning: active model {active_model!r} maps to {active_tier}, "

                f"below approved tier {approved}. Switch model or reply APPROVE MODEL {approved} "

                "with an override tier if intentional."

            ),

        )

        return 0



    _allow(intent_warning=intent_warning)

    return 0





if __name__ == "__main__":

    raise SystemExit(main())

