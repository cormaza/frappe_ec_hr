import unittest

from ec_hr.ecuador_hr.salary_components import get_salary_components

try:
	from frappe.tests import UnitTestCase
except ImportError:  # pragma: no cover
	UnitTestCase = unittest.TestCase  # type: ignore[misc,assignment]


class TestSalaryComponents(UnitTestCase):
	"""Salary Component specs stay valid without a bench."""

	def test_names_unique_and_non_empty(self) -> None:
		components = get_salary_components()
		self.assertEqual(len(components), 6)
		names = [c["name"] for c in components]
		self.assertTrue(all(name for name in names))
		self.assertEqual(len(set(names)), len(names))

	def test_types_are_earning_or_deduction(self) -> None:
		for component in get_salary_components():
			with self.subTest(component=component.get("name")):
				self.assertIn(component["type"], ("Earning", "Deduction"))
				self.assertEqual(component["doctype"], "Salary Component")
				self.assertTrue(component["salary_component"])
				self.assertTrue(component["formula"])

	def test_formulas_pin_sandbox_safe_factors(self) -> None:
		# hrms evaluates formulas in a sandbox without our modules in scope,
		# so earning formulas mirror overtime.py factors as plain arithmetic.
		expected = {
			"EC Overtime Daytime 50%": ("1.5", "doc.ec_overtime_day_min"),
			"EC Overtime Night 100%": ("2.25", "doc.ec_overtime_night_min"),
			"EC Extraordinary 100%": ("2.0", "doc.ec_extraordinary_min"),
			"EC Night Premium 25%": ("0.25", "doc.ec_night_min"),
			"EC Alimony Withholding": ("doc.ec_alimony_order or 0", "doc.ec_alimony_order"),
			"EC Salary Advance Deduction": (
				"doc.ec_advance_deduction or 0",
				"doc.ec_advance_deduction",
			),
		}
		formulas = {c["name"]: str(c["formula"]) for c in get_salary_components()}
		self.assertEqual(set(formulas), set(expected))
		for name, (factor, field) in expected.items():
			with self.subTest(component=name):
				self.assertIn(factor, formulas[name])
				self.assertIn(field, formulas[name])
