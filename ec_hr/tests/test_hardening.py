import ast
import importlib
import re
import unittest
from pathlib import Path

import ec_hr.hooks

try:
	from frappe.tests import UnitTestCase
except ImportError:  # pragma: no cover
	UnitTestCase = unittest.TestCase  # type: ignore[misc,assignment]

APP_ROOT = Path(__file__).resolve().parent.parent

#: Statutory provenance markers (or the explicit operational disclaimer).
SOURCE_RE = re.compile(
	r"Art\.|Codigo|Ley |LSS|MDT|SUT|Mandato|COPCI|LOD|SRI|CONA|IESS|BIESS|R\.O\.|no statutory formula"
)


class TestModuleProvenance(UnitTestCase):
	"""Every payroll module docstring names its legal source (or disclaims)."""

	def test_docstrings_cite_sources(self) -> None:
		bare = []
		for path in sorted((APP_ROOT / "payroll").glob("*.py")):
			if path.name == "__init__.py":
				continue
			tree = ast.parse(path.read_text(encoding="utf-8"))
			docstring = ast.get_docstring(tree) or ""
			if not SOURCE_RE.search(docstring):
				bare.append(path.name)
		self.assertEqual(bare, [])


class TestHooksWiring(UnitTestCase):
	"""Every doc_events handler imports in Ring 1 (guarded frappe pattern)."""

	def test_handlers_importable(self) -> None:
		for _doctype, handlers in ec_hr.hooks.doc_events.items():
			paths = [handlers] if isinstance(handlers, str) else list(handlers.values())
			for dotted in paths:
				for item in dotted if isinstance(dotted, list) else [dotted]:
					with self.subTest(handler=item):
						module_name, _, func = item.rpartition(".")
						module = importlib.import_module(module_name)
						self.assertTrue(callable(getattr(module, func)))
