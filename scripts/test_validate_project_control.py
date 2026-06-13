from unittest import TestCase, main

from validate_project_control import Validation, parse_yaml_document


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


if __name__ == "__main__":
    main()
