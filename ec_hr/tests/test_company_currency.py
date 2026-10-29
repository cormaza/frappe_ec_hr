"""Multi-company / multi-currency pure guards (RED)."""

import unittest

try:
	from frappe.tests import UnitTestCase
except ImportError:  # pragma: no cover - Ring 1 fallback
	UnitTestCase = unittest.TestCase  # type: ignore[misc,assignment]

from ec_hr.payroll.company_currency import (
	assert_single_company,
	assert_usd_only,
	require_company,
)


class TestUsdOnly(UnitTestCase):
	def test_usd_accepted(self) -> None:
		self.assertEqual(assert_usd_only(currency="USD"), "USD")

	def test_usd_normalized(self) -> None:
		self.assertEqual(assert_usd_only(currency="  usd "), "USD")

	def test_missing_currency_defaults_usd(self) -> None:
		self.assertEqual(assert_usd_only(), "USD")

	def test_exchange_rate_one_accepted(self) -> None:
		self.assertEqual(assert_usd_only(currency="USD", exchange_rate=1), "USD")
		self.assertEqual(assert_usd_only(currency="USD", exchange_rate=1.0), "USD")

	def test_foreign_currency_rejected(self) -> None:
		with self.assertRaises(ValueError):
			assert_usd_only(currency="EUR")

	def test_non_unit_rate_rejected(self) -> None:
		with self.assertRaises(ValueError):
			assert_usd_only(currency="USD", exchange_rate=1.2)
		with self.assertRaises(ValueError):
			assert_usd_only(exchange_rate=0.98)


class TestSingleCompany(UnitTestCase):
	def test_single_company_returned(self) -> None:
		self.assertEqual(assert_single_company(["Acme"]), "Acme")

	def test_whitespace_stripped_and_empties_ignored(self) -> None:
		self.assertEqual(assert_single_company(["  Acme ", "", "Acme", None]), "Acme")

	def test_empty_returns_empty(self) -> None:
		self.assertEqual(assert_single_company([]), "")

	def test_mixed_companies_rejected(self) -> None:
		with self.assertRaises(ValueError):
			assert_single_company(["Acme", "Other"])

	def test_case_sensitive_names_are_distinct(self) -> None:
		with self.assertRaises(ValueError):
			assert_single_company(["Acme", "ACME"])

	def test_require_company_rejects_blank(self) -> None:
		with self.assertRaises(ValueError):
			require_company("")
		with self.assertRaises(ValueError):
			require_company("   ")
		with self.assertRaises(ValueError):
			require_company(None)
