from unittest import TestCase, main

from validate_project_control import Validation, parse_yaml_document, validate_runtime_fields


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


if __name__ == "__main__":
    main()
