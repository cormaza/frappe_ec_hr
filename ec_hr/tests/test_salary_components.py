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
				self.assertEqual(component["amount_based_on_formula"], 1)

	def test_formulas_pin_sandbox_safe_factors(self) -> None:
		# hrms evaluates formulas against bare slip-field names (no `doc`
		# prefix exists in the eval namespace); factors mirror overtime.py.
		expected = {
			"EC Overtime Daytime 50%": ("1.5", "ec_overtime_day_min"),
			"EC Overtime Night 100%": ("2.25", "ec_overtime_night_min"),
			"EC Extraordinary 100%": ("2.0", "ec_extraordinary_min"),
			"EC Night Premium 25%": ("0.25", "ec_night_min"),
			"EC Alimony Withholding": ("ec_alimony_order or 0", "ec_alimony_order"),
			"EC Salary Advance Deduction": (
				"ec_advance_deduction or 0",
				"ec_advance_deduction",
			),
		}
		formulas = {c["name"]: str(c["formula"]) for c in get_salary_components()}
		self.assertEqual(set(formulas), set(expected))
		for name, (factor, field) in expected.items():
			with self.subTest(component=name):
				self.assertIn(factor, formulas[name])
				self.assertIn(field, formulas[name])
				self.assertNotIn("doc.", formulas[name])
