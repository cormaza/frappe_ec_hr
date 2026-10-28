import ast
import json
import re
import unittest
from pathlib import Path

try:
	from frappe.tests import UnitTestCase
except ImportError:  # pragma: no cover
	UnitTestCase = unittest.TestCase  # type: ignore[misc,assignment]

APP_ROOT = Path(__file__).resolve().parent.parent
LOCALE = APP_ROOT / "locale"
MARKERS = LOCALE / "i18n_markers.py"

_LITERAL_RE = re.compile(r'_\(\s*"((?:[^"\\]|\\.)*)"')


def _markers_msgids() -> set[str]:
	tree = ast.parse(MARKERS.read_text(encoding="utf-8"))
	found = set()
	for node in ast.walk(tree):
		if (
			isinstance(node, ast.Expr)
			and isinstance(node.value, ast.Call)
			and getattr(node.value.func, "id", "") == "_"
			and node.value.args
			and isinstance(node.value.args[0], ast.Constant)
		):
			found.add(str(node.value.args[0].value))
	return found


def _code_msgids() -> set[str]:
	found = set()
	for path in (*APP_ROOT.glob("payroll/*.py"), *APP_ROOT.glob("ecuador_hr/**/*.py")):
		found.update(_LITERAL_RE.findall(path.read_text(encoding="utf-8")))
	return found


def _doctype_msgids() -> set[str]:
	# Bare numeric codes (169.1, 172...) are identifiers, not UI strings: the
	# bench scanner will not keep them all, so they stay untranslated here.
	found = set()
	for path in APP_ROOT.glob("ecuador_hr/doctype/*/*.json"):
		try:
			definition = json.loads(path.read_text(encoding="utf-8"))
		except json.JSONDecodeError:
			continue
		found.add(str(definition.get("name", "")))
		for field in definition.get("fields", []):
			if field.get("label"):
				found.add(str(field["label"]))
			for option in str(field.get("options", "")).split("\n"):
				text = option.strip()
				# Skip bare numeric codes (169.1, 172...) and ec_ field identifiers:
				# identifiers by design, never UI strings.
				if text and not re.fullmatch(r"[\d.]+", text) and not text.startswith("ec_"):
					found.add(text)
	found.discard("")
	return found


def _po_msgids() -> set[str]:
	msgids = set()
	current = None
	for line in (LOCALE / "es.po").read_text(encoding="utf-8").splitlines():
		if line.startswith("msgid "):
			current = ast.literal_eval(line[len("msgid ") :].strip())
			if current:
				msgids.add(current)
	return msgids


class TestMarkersGuard(UnitTestCase):
	"""Markers exist for extraction but never run (AGENTS.md i18n contract)."""

	def test_markers_file_parses_with_literals_only(self) -> None:
		self.assertTrue(_markers_msgids())

	def test_no_runtime_import_of_markers(self) -> None:
		pattern = re.compile(r"^\s*(import|from)\s+[\w.]*i18n_markers", re.MULTILINE)
		offenders = [
			path.name
			for path in (*APP_ROOT.glob("payroll/*.py"), *APP_ROOT.glob("ecuador_hr/**/*.py"))
			if pattern.search(path.read_text(encoding="utf-8"))
		]
		self.assertEqual(offenders, [])


class TestCatalogCoverage(UnitTestCase):
	"""Every markers/code msgid ships in es.po until bench owns extraction."""

	def test_markers_covered(self) -> None:
		po = _po_msgids()
		missing = sorted(m for m in _markers_msgids() if m not in po)
		self.assertEqual(missing, [])

	def test_code_literals_covered(self) -> None:
		po = _po_msgids()
		missing = sorted(m for m in _code_msgids() | _doctype_msgids() if m not in po)
		self.assertEqual(missing, [])

	def test_po_headers_valid(self) -> None:
		header = (LOCALE / "es.po").read_text(encoding="utf-8")
		self.assertIn('"Language: es\\n"', header)
		match = re.search(r"PO-Revision-Date: (\d{4}-\d{2}-\d{2} \d{2}:\d{2})", header)
		self.assertIsNotNone(match)
