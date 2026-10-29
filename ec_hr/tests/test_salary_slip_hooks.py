import unittest
from types import SimpleNamespace

from ec_hr.ecuador_hr.salary_slip_hooks import validate_salary_slip

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


def _doc(**overrides):  # type: ignore[no-untyped-def]
	base = {
		"company": "Acme",
		"ec_overtime_daily_max_min": 0,
		"ec_overtime_weekly_min": 0,
		"net_pay": 0,
	}
	base.update(overrides)
	return SimpleNamespace(**base)


class TestValidateSalarySlipPure(UnitTestCase):
	"""Hook logic over namespace docs: ValueError in Ring 1, ValidationError
	(frappe.throw) in bench — same failures, converted by the ring."""

	def test_caps_breach_fails(self) -> None:
		with self.assertRaises(_RING_ERRORS):
			validate_salary_slip(_doc(ec_overtime_daily_max_min=300, ec_overtime_weekly_min=0))

	def test_weekly_caps_breach_fails(self) -> None:
		with self.assertRaises(_RING_ERRORS):
			validate_salary_slip(_doc(ec_overtime_daily_max_min=0, ec_overtime_weekly_min=800))

	def test_negative_net_pay_fails(self) -> None:
		with self.assertRaises(_RING_ERRORS):
			validate_salary_slip(_doc(net_pay=-1))

	def test_clean_doc_passes(self) -> None:
		validate_salary_slip(_doc(ec_overtime_daily_max_min=60, ec_overtime_weekly_min=120, net_pay=100))


class TestValidateSalarySlipIsolation(UnitTestCase):
	"""Multi-company / multi-currency hardening: one company, USD only."""

	def test_missing_company_fails(self) -> None:
		doc = _doc()
		del doc.company
		with self.assertRaises(_RING_ERRORS):
			validate_salary_slip(doc)

	def test_foreign_currency_fails(self) -> None:
		with self.assertRaises(_RING_ERRORS):
			validate_salary_slip(_doc(currency="EUR", exchange_rate=1.2))

	def test_non_unit_rate_fails(self) -> None:
		with self.assertRaises(_RING_ERRORS):
			validate_salary_slip(_doc(currency="USD", exchange_rate=25000.0))

	def test_employee_company_mismatch_fails(self) -> None:
		with self.assertRaises(_RING_ERRORS):
			validate_salary_slip(_doc(employee="EMP-001", employee_company="Other"))

	def test_employee_company_match_passes(self) -> None:
		validate_salary_slip(_doc(employee="EMP-001", employee_company="Acme"))


@unittest.skipUnless(frappe is not None, "bench-only: needs frappe.get_doc")
class TestValidateSalarySlipBench(UnitTestCase):
	"""Bench wiring: the hook fails the same way on a real Salary Slip doc."""

	def test_caps_breach_raises_validation_error(self) -> None:
		doc = frappe.get_doc(
			{
				"doctype": "Salary Slip",
				"ec_overtime_daily_max_min": 300,
				"ec_overtime_weekly_min": 0,
				"net_pay": 100,
			}
		)
		with self.assertRaises(frappe.ValidationError):
			validate_salary_slip(doc)
