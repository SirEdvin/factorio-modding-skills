"""Synthetic package fixtures; no published skills or runtime installation."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import validate_skills as validator


VALID_SKILL = """---
name: example-skill
description: Validate a synthetic example when testing the validator.
license: MIT
metadata:
  version: "1.0.0"
---
# Example

Use this synthetic fixture only in validator tests.
"""


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        self.skills = self.root / "skills"
        self.skills.mkdir()
        (self.skills / ".gitkeep").touch()

    def write_skill(self, content=VALID_SKILL, name="example-skill"):
        package = self.skills / name
        package.mkdir(exist_ok=True)
        (package / "SKILL.md").write_text(content, encoding="utf-8")
        return package

    def errors(self):
        return validator.validate_repository(self.root)[1]

    def assert_error(self, expected):
        errors = self.errors()
        self.assertTrue(any(expected in error for error in errors), errors)

    def test_empty_scaffold_passes(self):
        self.assertEqual(([], []), validator.validate_repository(self.root))

    def test_missing_skills_directory_fails(self):
        (self.skills / ".gitkeep").unlink()
        self.skills.rmdir()
        self.assert_error("missing skills directory")

    def test_valid_skill_with_and_without_gitkeep(self):
        self.write_skill()
        self.assertEqual((["example-skill"], []), validator.validate_repository(self.root))
        (self.skills / ".gitkeep").unlink()
        self.assertEqual([], self.errors())

    def test_all_packages_are_validated(self):
        self.write_skill()
        self.write_skill(VALID_SKILL.replace("example-skill", "another-skill"), "another-skill")
        self.assertEqual((["another-skill", "example-skill"], []), validator.validate_repository(self.root))
        (self.skills / "another-skill" / "SKILL.md").unlink()
        self.assert_error("missing SKILL.md")

    def test_unexpected_root_file_fails(self):
        (self.skills / "SKILL.md").write_text(VALID_SKILL, encoding="utf-8")
        self.assert_error("unexpected entry")

    def test_nonempty_gitkeep_fails(self):
        (self.skills / ".gitkeep").write_text("not a placeholder", encoding="utf-8")
        self.assert_error(".gitkeep must be empty")

    def test_directory_without_skill_fails(self):
        (self.skills / "unfinished").mkdir()
        self.assert_error("missing SKILL.md")

    def test_hidden_directory_is_not_silently_skipped(self):
        (self.skills / ".hidden").mkdir()
        self.assert_error("invalid package directory name")

    def test_name_mismatch_fails(self):
        self.write_skill(VALID_SKILL.replace("name: example-skill", "name: different"))
        self.assert_error("must exactly match")

    def test_invalid_directory_names_fail(self):
        for name in ("UPPER", "bad--name", "bad_name", "x" * 65):
            self.write_skill(VALID_SKILL.replace("example-skill", name), name)
        self.assert_error("invalid package directory name")

    def test_frontmatter_must_start_at_byte_zero(self):
        self.write_skill("\n" + VALID_SKILL)
        self.assert_error("frontmatter must start at byte zero")

    def test_frontmatter_requires_line_delimiters(self):
        self.write_skill(VALID_SKILL.replace("---\n# Example", "---suffix\n# Example"))
        self.assert_error("missing closing frontmatter delimiter")

    def test_duplicate_yaml_key_fails(self):
        self.write_skill(VALID_SKILL.replace("license: MIT", "license: MIT\nlicense: MIT"))
        self.assert_error("invalid YAML")

    def test_malformed_yaml_fails(self):
        self.write_skill(VALID_SKILL.replace("license: MIT", "license: [unclosed"))
        self.assert_error("invalid YAML")

    def test_non_mapping_frontmatter_fails(self):
        self.write_skill("---\n- item\n---\nBody.\n")
        self.assert_error("frontmatter must be a mapping")

    def test_nested_metadata_is_rejected_before_reference_coercion(self):
        for replacement in ("  nested:\n    key: value", "  tags:\n    - example"):
            with self.subTest(replacement=replacement):
                self.write_skill(VALID_SKILL.replace('  version: "1.0.0"', replacement))
                self.assert_error("metadata must map strings to strings")

    def test_optional_fields_must_be_nonempty_strings(self):
        for field in ("license", "compatibility", "allowed-tools"):
            with self.subTest(field=field):
                self.write_skill(VALID_SKILL.replace("license: MIT", f"{field}:\n  nested: value"))
                self.assert_error(f"{field} must be a nonempty string")

    def test_official_validator_rejects_invalid_frontmatter(self):
        for content in (
            VALID_SKILL.replace("description:", "unknown-field:"),
            VALID_SKILL.replace("Validate a synthetic example when testing the validator.", "x" * 1025),
            VALID_SKILL.replace("license: MIT", "unsupported: value"),
        ):
            with self.subTest(content=content):
                self.write_skill(content)
                self.assert_error("Agent Skills:")

    def test_reference_validator_is_really_called(self):
        package = self.write_skill()
        with patch.object(validator, "official_validate", return_value=["sentinel rejection"]) as official:
            self.assert_error("Agent Skills: sentinel rejection")
            official.assert_called_once_with(package)

    def test_empty_body_fails(self):
        self.write_skill(VALID_SKILL.split("# Example")[0])
        self.assert_error("instruction body must not be empty")

    def test_invalid_utf8_fails_cleanly(self):
        package = self.write_skill()
        (package / "SKILL.md").write_bytes(b"\xff")
        self.assert_error("cannot read UTF-8")

    def test_missing_markdown_link_fails(self):
        self.write_skill(VALID_SKILL + "\n[guide](references/missing.md)\n")
        self.assert_error("missing local link")

    def test_package_links_cannot_escape(self):
        (self.root / "outside.md").write_text("Outside", encoding="utf-8")
        for target in ("../../outside.md", "%2e%2e/%2e%2e/outside.md", str(self.root / "outside.md")):
            with self.subTest(target=target):
                self.write_skill(VALID_SKILL + f"\n[outside]({target})\n")
                self.assert_error("local link escapes package")

    def test_links_in_support_markdown_are_checked(self):
        package = self.write_skill(VALID_SKILL + "\n[guide](references/guide.md#topic)\n")
        (package / "references").mkdir()
        (package / "references" / "guide.md").write_text("[back](../SKILL.md)\n", encoding="utf-8")
        self.assertEqual([], self.errors())
        (package / "references" / "guide.md").write_text("[missing](missing.md)\n", encoding="utf-8")
        self.assert_error("missing local link")

    def test_reference_style_links_and_images_are_checked(self):
        self.write_skill(VALID_SKILL + "\n[guide][ref]\n\n[ref]: references/missing.md\n")
        self.assert_error("missing local link")
        self.write_skill(VALID_SKILL + "\n![image](assets/missing.png)\n")
        self.assert_error("missing local link")

    def test_external_links_anchors_and_code_examples_are_ignored(self):
        self.write_skill(VALID_SKILL + """
[web](https://example.com/doc) [mail](mailto:example@example.com) [anchor](#topic)
[cdn](//example.com/file) `[example](not-a-link.md)`

```markdown
[example](missing.md)
```
""")
        self.assertEqual([], self.errors())

    def test_symlink_skill_root_fails(self):
        (self.skills / ".gitkeep").unlink()
        self.skills.rmdir()
        (self.root / "outside").mkdir()
        self.skills.symlink_to(self.root / "outside", target_is_directory=True)
        self.assert_error("symlinks are not allowed")

    def test_symlink_package_and_support_file_fail(self):
        package = self.write_skill()
        (self.skills / "linked-skill").symlink_to(package, target_is_directory=True)
        self.assert_error("symlinks are not allowed")
        (self.skills / "linked-skill").unlink()
        (package / "linked.md").symlink_to(package / "SKILL.md")
        self.assert_error("symlinks are not allowed")

    def test_nested_skill_entrypoint_fails(self):
        package = self.write_skill()
        nested = package / "nested"
        nested.mkdir()
        (nested / "SKILL.md").write_text(VALID_SKILL, encoding="utf-8")
        self.assert_error("nested or alternate skill entrypoint")

    def test_cli_exit_status_and_empty_message(self):
        script = Path(__file__).with_name("validate_skills.py")
        result = subprocess.run([sys.executable, str(script), "--root", str(self.root)], capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("0 skill packages (empty scaffold)", result.stdout)
        self.write_skill("Not valid frontmatter.")
        result = subprocess.run([sys.executable, str(script), "--root", str(self.root)], capture_output=True, text=True)
        self.assertEqual(1, result.returncode)
        self.assertIn("Validation failed", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
