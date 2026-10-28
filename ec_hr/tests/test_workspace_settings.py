import json
import unittest
from pathlib import Path

try:
	import frappe

	_RING_ERRORS = (ValueError, frappe.ValidationError)
except ImportError:  # pragma: no cover - Ring 1 has no frappe package.
	frappe = None  # type: ignore[assignment]
	_RING_ERRORS = (ValueError,)

try:
	from frappe.tests import UnitTestCase
except ImportError:  # pragma: no cover
	UnitTestCase = unittest.TestCase  # type: ignore[misc,assignment]

from ec_hr.ecuador_hr.doctype.ec_hr_settings.ec_hr_settings import ECHRSettings

APP_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE = APP_ROOT / "ecuador_hr" / "workspace" / "ecuador_hr" / "ecuador_hr.json"

KNOWN_LINK_TARGETS = frozenset(
	{
		"Employee",
		"Salary Slip",
		"Salary Structure",
		"Salary Component",
		"Employee Advance",
		"Leave Application",
		"EC Settlement Act",
		"EC HR Settings",
	}
)


class TestWorkspace(UnitTestCase):
	"""Workspace JSON parses with known link targets; bench build owns the rest."""

	def test_workspace_shape(self) -> None:
		definition = json.loads(WORKSPACE.read_text(encoding="utf-8"))
		self.assertEqual(definition["doctype"], "Workspace")
		self.assertEqual(definition["module"], "Ecuador HR")
		self.assertEqual(definition["name"], "Ecuador HR")
		breaks = {link["label"] for link in definition["links"] if link.get("type") == "Card Break"}
		for link in definition["links"]:
			if link.get("type") == "Link":
				with self.subTest(link=link.get("label")):
					self.assertIn(link["link_to"], KNOWN_LINK_TARGETS)
		cards = {block["data"]["card_name"] for block in json.loads(definition["content"])}
		self.assertTrue(cards <= breaks)


class TestSettingsJson(UnitTestCase):
	SETTINGS = APP_ROOT / "ecuador_hr" / "doctype" / "ec_hr_settings" / "ec_hr_settings.json"
	RATE = APP_ROOT / "ecuador_hr" / "doctype" / "ec_sbu_rate" / "ec_sbu_rate.json"

	def test_settings_is_single_with_rate_table(self) -> None:
		definition = json.loads(self.SETTINGS.read_text(encoding="utf-8"))
		self.assertEqual(definition["name"], "EC HR Settings")
		self.assertEqual(definition["issingle"], 1)
		names = [f["fieldname"] for f in definition["fields"]]
		self.assertEqual(definition["field_order"], names)
		for expected in ("sbu_rates", "cona_table_year", "sri_table_year", "rdep_schema_version"):
			self.assertIn(expected, names)

	def test_rate_is_child_table(self) -> None:
		definition = json.loads(self.RATE.read_text(encoding="utf-8"))
		self.assertEqual(definition["name"], "EC SBU Rate")
		self.assertEqual(definition["istable"], 1)
		self.assertGreaterEqual(len(definition.get("permissions", [])), 1)


def _settings(rows):  # type: ignore[no-untyped-def]
	# __new__ bypasses Document.__init__ so one path serves both rings (see
	# test_settlement._act for why).
	doc = ECHRSettings.__new__(ECHRSettings)
	doc.sbu_rates = rows  # type: ignore[attr-defined]
	return doc


class TestSettingsValidation(UnitTestCase):
	"""Controller rules run in Ring 1 via the stub base."""

	def test_valid_table_passes(self) -> None:
		doc = _settings([{"year": 2024, "amount": 460.0}, {"year": 2025, "amount": 550.0}])
		doc.validate()
		self.assertEqual(doc.get_sbu(2025), 550.0)

	def test_duplicate_zero_and_missing_fail(self) -> None:
		with self.assertRaises(_RING_ERRORS):
			_settings([{"year": 2025, "amount": 550.0}, {"year": 2025, "amount": 560.0}]).validate()
		with self.assertRaises(_RING_ERRORS):
			_settings([{"year": 2025, "amount": 0.0}]).validate()
		with self.assertRaises(_RING_ERRORS):
			_settings([{"year": 2025, "amount": 550.0}]).get_sbu(2026)


@unittest.skipUnless(frappe is not None, "bench-only: needs the installed Single")
class TestSettingsBench(UnitTestCase):
	def test_single_validates(self) -> None:
		doc = frappe.get_doc("EC HR Settings")
		doc.validate()
