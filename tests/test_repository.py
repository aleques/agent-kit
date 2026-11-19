"""The kit itself: skill headers are valid for every tool, links resolve, and every file passes the
generic detectors of its own guard."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

from helpers import KIT_ROOT, FAKE_TERMS, load_scan_module

scan = load_scan_module()
LINK = re.compile(r"\]\(([^)#\s]+)(?:#[^)]*)?\)")


def kit_files():
    return sorted(p for p in KIT_ROOT.rglob("*") if p.is_file()
                  and not {".git", "__pycache__"} & set(p.relative_to(KIT_ROOT).parts))


def front_matter(text: str) -> dict:
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        return {}
    fields = {}
    for line in match.group(1).splitlines():
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip().strip("'\"")
    return fields


class SkillHeaderTest(unittest.TestCase):
    def test_every_skill_has_name_equal_to_folder_and_a_short_description(self):
        skills = sorted((KIT_ROOT / "skills").glob("*/SKILL.md"))
        self.assertGreater(len(skills), 0)
        for skill in skills:
            with self.subTest(skill=skill.parent.name):
                fields = front_matter(skill.read_text(encoding="utf-8"))
                self.assertEqual(fields.get("name"), skill.parent.name)
                description = fields.get("description", "")
                self.assertTrue(description)
                self.assertLessEqual(len(description), 250)


def prose_outside_code_blocks(text: str) -> str:
    """Markdown without fenced code blocks: links inside ``` examples are illustrations."""
    kept, inside = [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            inside = not inside
            continue
        if not inside:
            kept.append(line)
    return "\n".join(kept)


class LinkTest(unittest.TestCase):
    def test_links_inside_code_blocks_are_ignored(self):
        text = "see [a](real.md)\n```markdown\n[b](example-only.md)\n```\n"
        self.assertEqual(LINK.findall(prose_outside_code_blocks(text)), ["real.md"])

    def test_relative_links_in_markdown_point_to_existing_files(self):
        checked = 0
        for path in kit_files():
            if path.suffix != ".md":
                continue
            prose = prose_outside_code_blocks(path.read_text(encoding="utf-8"))
            for target in LINK.findall(prose):
                if "://" in target or target.startswith("mailto:"):
                    continue
                checked += 1
                with self.subTest(file=str(path.relative_to(KIT_ROOT)), link=target):
                    self.assertTrue((path.parent / target).exists())
        print(f"\nlinks checked: {checked}")


class SelfScanTest(unittest.TestCase):
    def test_every_file_passes_the_generic_detectors(self):
        terms = scan.parse_terms("fake.txt", "\n".join(FAKE_TERMS))
        allow = scan.load_allow()
        files = kit_files()
        findings = []
        for path in files:
            name = str(path.relative_to(KIT_ROOT))
            for finding in scan.scan_bytes(name, path.read_bytes(), terms, allow):
                if not finding.detector.startswith("deny:"):
                    findings.append(str(finding))
        print(f"\nself-scan: {len(files)} files, {len(findings)} findings")
        self.assertGreater(len(files), 0)
        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
