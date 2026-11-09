import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COVERAGE = ROOT / "skills" / "quality-bar" / "references" / "coverage.md"
SECURITY_COVERAGE = ROOT / "skills" / "quality-bar" / "references" / "security-and-engineering-coverage.md"
LIST_SIZES = {"A": 30, "B1": 13, "B2": 22, "C": 30, "D": 55, "E": 178}
STATUSES = {"Enforced", "Guided", "Partial", "Outside"}


def rows():
    out = []
    for line in COVERAGE.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 5 and cells[0].isdigit():
            out.append(cells)
    return out


class Coverage(unittest.TestCase):
    def test_all_59_points_present_once(self):
        self.assertEqual([int(r[0]) for r in rows()], list(range(1, 60)))

    def test_each_row_has_status_and_existing_paths(self):
        for number, _req, where, status, how in rows():
            self.assertIn(status, STATUSES, number)
            self.assertTrue(how, number)
            paths = re.findall(r"`([^`]+)`", where)
            self.assertTrue(paths, f"row {number} names no mechanism")
            for path in paths:
                self.assertTrue((ROOT / path).exists(), f"row {number}: {path} does not exist")

    def test_security_and_engineering_lists_fully_covered(self):
        seen = {name: [] for name in LIST_SIZES}
        for line in SECURITY_COVERAGE.read_text(encoding="utf-8").splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) != 6 or cells[0] not in LIST_SIZES:
                continue
            lst, items, _topic, where, status, how = cells
            self.assertIn(status, STATUSES, line)
            self.assertTrue(how, line)
            paths = re.findall(r"`([^`]+)`", where)
            self.assertTrue(paths, line)
            for path in paths:
                self.assertTrue((ROOT / path).exists(), f"{lst} {items}: {path} does not exist")
            for part in items.split(","):
                low, _, high = part.partition("-")
                seen[lst] += range(int(low), int(high or low) + 1)
        for name, size in LIST_SIZES.items():
            self.assertEqual(sorted(seen[name]), list(range(1, size + 1)), f"list {name} has gaps or duplicates")

    def test_every_skill_has_valid_frontmatter(self):
        for skill in (ROOT / "skills").glob("*/SKILL.md"):
            text = skill.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\nname: " + skill.parent.name + "\n"), skill)
            self.assertRegex(text, r"\ndescription: .{40,}\n(?:.*\n)*?---\n", skill)

    def test_research_skill_keeps_every_method_phase(self):
        text = (ROOT / "skills" / "research" / "SKILL.md").read_text(encoding="utf-8")
        for phase in ("## 0. Pick depth", "## 1. Plan", "## 2. Search loop", "## 3. Screen", "## 4. Extract",
                      "## 5. Triangulate", "## 6. Grade", "## 7. Synthesize", "## 8. Token discipline"):
            self.assertIn(phase, text)
        self.assertLess(len(text), 7000, "the research skill must stay small: move detail to references/")

    def test_every_skill_is_listed_in_the_workflow_or_readme(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for skill in (ROOT / "skills").iterdir():
            if skill.is_dir() and not skill.name.startswith("."):
                self.assertIn(f"`{skill.name}`", readme, f"{skill.name} missing from README")


if __name__ == "__main__":
    unittest.main()
