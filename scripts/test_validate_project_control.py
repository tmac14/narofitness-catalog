from unittest import TestCase, main

from validate_project_control import (
    Validation,
    parse_yaml_document,
    validate_runtime_fields,
    validate_task_runtime_protocol,
    validate_cursor_workspace,
)


class LoadYamlTests(TestCase):
    def test_accepts_unique_mapping_keys(self) -> None:
        validation = Validation()

        data = parse_yaml_document("first: 1\nsecond: 2\n", "registry.yaml", validation)

        self.assertEqual(data, {"first": 1, "second": 2})
        self.assertEqual(validation.errors, [])

    def test_rejects_duplicate_mapping_keys(self) -> None:
        validation = Validation()

        data = parse_yaml_document("duplicate: 1\nduplicate: 2\n", "registry.yaml", validation)

        self.assertEqual(data, {})
        self.assertEqual(len(validation.errors), 1)
        self.assertIn("found duplicate key 'duplicate'", validation.errors[0])


class RuntimeFieldTests(TestCase):
    def test_accepts_neutral_runtime_fields(self) -> None:
        validation = Validation()
        text = "\n".join(
            [
                "- control_plane_runtime: `ONLY_CODEX`",
                "- active_protocol: `ORCHESTRATION`",
                "- handoff_from: `NONE`",
                "- handoff_at: `NONE`",
                "- handoff_reason: `NONE`",
            ]
        )
        validate_runtime_fields(text, {"RUNTIME-D001"}, validation)
        self.assertEqual(validation.errors, [])

    def test_rejects_invalid_runtime(self) -> None:
        validation = Validation()
        text = "\n".join(
            [
                "- control_plane_runtime: `INVALID`",
                "- active_protocol: `ORCHESTRATION`",
                "- handoff_from: `NONE`",
                "- handoff_at: `NONE`",
                "- handoff_reason: `NONE`",
            ]
        )
        validate_runtime_fields(text, set(), validation)
        self.assertTrue(any("control_plane_runtime is invalid" in error for error in validation.errors))


class TaskRuntimeProtocolTests(TestCase):
    def test_accepts_valid_runtime_protocol_pair(self) -> None:
        validation = Validation()
        validate_task_runtime_protocol(
            "TEST-TASK",
            {"runtime": "ONLY_CODEX", "protocol": "IMPLEMENTATION"},
            validation,
        )
        self.assertEqual(validation.errors, [])

    def test_warns_on_legacy_protocol(self) -> None:
        validation = Validation()
        validate_task_runtime_protocol(
            "TEST-TASK",
            {"protocol": "CODEX_IMPLEMENTATION"},
            validation,
        )
        self.assertEqual(validation.errors, [])
        self.assertTrue(any("legacy protocol" in warning for warning in validation.warnings))

    def test_rejects_invalid_protocol(self) -> None:
        validation = Validation()
        validate_task_runtime_protocol(
            "TEST-TASK",
            {"runtime": "ONLY_CODEX", "protocol": "CODEX_ORCHESTRATION"},
            validation,
        )
        self.assertTrue(any("invalid protocol" in error for error in validation.errors))

    def test_rejects_missing_runtime(self) -> None:
        validation = Validation()
        validate_task_runtime_protocol(
            "TEST-TASK",
            {"protocol": "IMPLEMENTATION"},
            validation,
        )
        self.assertTrue(any("missing runtime field" in error for error in validation.errors))

    def test_allows_none_protocol_placeholder(self) -> None:
        validation = Validation()
        validate_task_runtime_protocol(
            "TEST-TASK",
            {"runtime": "ONLY_CODEX", "protocol": "NONE"},
            validation,
        )
        self.assertEqual(validation.errors, [])


class CursorWorkspaceTests(TestCase):
    def test_required_cursor_rules_and_hooks_exist(self) -> None:
        validation = Validation()
        validate_cursor_workspace(validation)
        self.assertEqual(validation.errors, [])


if __name__ == "__main__":
    main()
