from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestDocsPresent(unittest.TestCase):
    def test_agents_is_a_map(self):
        text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertLessEqual(len(text.splitlines()), 130)
        self.assertIn("docs/INDEX.md", text)
        self.assertIn("python tools/check.py --all", text)

    def test_architecture_describes_layers(self):
        text = (ROOT / "ARCHITECTURE.md").read_text(encoding="utf-8")
        self.assertIn("bild/errors.py", text)
        self.assertIn("Content-Type", text)

    def test_agent_setup_does_not_invite_alternate_host_or_auth(self):
        text = (ROOT / "AGENT_SETUP.md").read_text(encoding="utf-8")
        lowered = text.lower()
        self.assertIn("https://api.getbild.com", text)
        self.assertIn("jwt", lowered)
        self.assertIn("do not invent", lowered)
        self.assertIn("ask about", lowered)
        for banned in ("custom host", "non-production", "their-host"):
            self.assertNotIn(banned, lowered)


if __name__ == "__main__":
    unittest.main()
