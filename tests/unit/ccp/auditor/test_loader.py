"""Tests for the RulesLoader."""

from __future__ import annotations

from pathlib import Path

import pytest

from ccp.auditor.loader import RulesLoader
from ccp.auditor.types import RuleDefinition


class TestRulesLoader:
    """Tests for RulesLoader class."""

    @pytest.fixture
    def mock_rules_dir(self, tmp_path: Path) -> Path:
        """Create a mock rules directory structure."""
        rules_dir = tmp_path / ".claude" / "rules"
        standard_dir = rules_dir / "standard"
        custom_dir = rules_dir / "custom"
        standard_dir.mkdir(parents=True)
        custom_dir.mkdir(parents=True)

        (standard_dir / "tdd-enforcement.md").write_text("# TDD Rules\nAlways write tests first.")
        (standard_dir / "coding-standards.md").write_text("# Coding Standards\nFollow DRY principle.")
        (custom_dir / "project.md").write_text("# Project Rules\nCustom project rules.")

        return tmp_path

    def test_load_rules_returns_list(self, mock_rules_dir: Path) -> None:
        """Should return a list of RuleDefinition objects."""
        loader = RulesLoader(project_root=mock_rules_dir)
        rules = loader.load_rules()

        assert isinstance(rules, list)
        assert len(rules) == 3
        assert all(isinstance(r, RuleDefinition) for r in rules)

    def test_load_rules_includes_standard_and_custom(self, mock_rules_dir: Path) -> None:
        """Should load from both standard and custom directories."""
        loader = RulesLoader(project_root=mock_rules_dir)
        rules = loader.load_rules()

        sources = {r.source for r in rules}
        assert "standard" in sources
        assert "custom" in sources

    def test_load_all_returns_only_rules(self, tmp_path: Path) -> None:
        """load_all() only loads rules for efficiency."""
        rules_dir = tmp_path / ".claude" / "rules" / "standard"
        rules_dir.mkdir(parents=True)
        (rules_dir / "rule.md").write_text("# Rule")

        loader = RulesLoader(project_root=tmp_path)
        all_items = loader.load_all()

        assert len(all_items) == 1
        assert all_items[0].source == "standard"

    def test_build_system_prompt_not_empty(self, mock_rules_dir: Path) -> None:
        """Should build a non-empty system prompt."""
        loader = RulesLoader(project_root=mock_rules_dir)
        prompt = loader.build_system_prompt()

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "TDD" in prompt or "tdd" in prompt.lower()

    def test_handles_missing_directories(self, tmp_path: Path) -> None:
        """Should handle missing directories gracefully."""
        loader = RulesLoader(project_root=tmp_path)
        rules = loader.load_rules()

        assert rules == []

    def test_rule_definition_has_correct_fields(self, mock_rules_dir: Path) -> None:
        """Should populate all RuleDefinition fields."""
        loader = RulesLoader(project_root=mock_rules_dir)
        rules = loader.load_rules()

        rule = rules[0]
        assert rule.name
        assert rule.path.exists()
        assert rule.content
        assert rule.source in ("standard", "custom")

    def test_rules_are_cached(self, mock_rules_dir: Path) -> None:
        """Rules should be cached after first load."""
        loader = RulesLoader(project_root=mock_rules_dir)

        rules1 = loader.load_rules()
        rules2 = loader.load_rules()

        assert rules1 is rules2  # Same object (cached)

    def test_build_system_prompt_includes_json_format(self, mock_rules_dir: Path) -> None:
        """System prompt should include JSON response format instructions."""
        loader = RulesLoader(project_root=mock_rules_dir)
        prompt = loader.build_system_prompt()

        assert "JSON" in prompt
        assert "violations" in prompt
