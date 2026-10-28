import unittest
from datetime import date
from types import SimpleNamespace

from ec_hr.ecuador_hr.notice_hooks import entry_warning, exit_warning, validate_employee_notices

try:
	from frappe.tests import UnitTestCase
except ImportError:  # pragma: no cover
	UnitTestCase = unittest.TestCase  # type: ignore[misc,assignment]

AS_OF = date(2026, 10, 28)


def _doc(**overrides):  # type: ignore[no-untyped-def]
	base = {
		"date_of_joining": None,
		"relieving_date": None,
		"ec_entry_notice_date": None,
		"ec_exit_notice_date": None,
	}
	base.update(overrides)
	return SimpleNamespace(**base)


class TestNoticeWarnings(UnitTestCase):
	"""LSS Art. 73 deadlines as warnings (user decision: never block saving)."""

	def test_on_time_entry_silent(self) -> None:
		doc = _doc(date_of_joining=date(2026, 10, 20), ec_entry_notice_date=date(2026, 10, 25))
		self.assertIsNone(entry_warning(doc, AS_OF))

	def test_late_entry_warns(self) -> None:
		doc = _doc(date_of_joining=date(2026, 9, 1), ec_entry_notice_date=date(2026, 10, 1))
		warning = entry_warning(doc, AS_OF)
		self.assertIsNotNone(warning)
		self.assertIn("15", str(warning))

	def test_missing_entry_warns_once_overdue(self) -> None:
		doc = _doc(date_of_joining=date(2026, 9, 1))
		self.assertIsNotNone(entry_warning(doc, AS_OF))
		fresh = _doc(date_of_joining=date(2026, 10, 20))
		self.assertIsNone(entry_warning(fresh, AS_OF))

	def test_exit_leg(self) -> None:
		doc = _doc(relieving_date=date(2026, 10, 20), ec_exit_notice_date=date(2026, 10, 22))
		self.assertIsNone(exit_warning(doc, AS_OF))
		late = _doc(relieving_date=date(2026, 10, 20), ec_exit_notice_date=date(2026, 10, 25))
		self.assertIsNotNone(exit_warning(late, AS_OF))
		self.assertIsNone(exit_warning(_doc(), AS_OF))

	def test_validate_never_raises(self) -> None:
		validate_employee_notices(_doc(date_of_joining=date(2026, 9, 1)))
		validate_employee_notices(_doc())
