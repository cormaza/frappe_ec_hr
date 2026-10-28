"""Ecuadorian Salary Component specs (pure data, no frappe import).

Each spec is a `frappe.get_doc` argument dict for the hrms Salary Component
DocType. Formulas use plain arithmetic on slip fields only: hrms evaluates
formulas in a sandbox without our payroll modules in scope, so the factors
below mirror `ec_hr.payroll.overtime` (1.5 / 2.25 / 2.0 / 0.25) and the
Ring 1 test pins each factor per component to stop drift.
"""


def get_salary_components() -> list[dict[str, object]]:
	"""Return the six Ecuadorian time-engine Salary Component specs."""
	return [
		{
			"doctype": "Salary Component",
			"name": "EC Overtime Daytime 50%",
			"salary_component": "EC Overtime Daytime 50%",
			"type": "Earning",
			"amount_based_on_formula": 1,
			"formula": "(ec_hourly_rate or 0) * 1.5 * (ec_overtime_day_min or 0) / 60",
		},
		{
			"doctype": "Salary Component",
			"name": "EC Overtime Night 100%",
			"salary_component": "EC Overtime Night 100%",
			"type": "Earning",
			"amount_based_on_formula": 1,
			"formula": "(ec_hourly_rate or 0) * 2.25 * (ec_overtime_night_min or 0) / 60",
		},
		{
			"doctype": "Salary Component",
			"name": "EC Extraordinary 100%",
			"salary_component": "EC Extraordinary 100%",
			"type": "Earning",
			"amount_based_on_formula": 1,
			"formula": "(ec_hourly_rate or 0) * 2.0 * (ec_extraordinary_min or 0) / 60",
		},
		{
			"doctype": "Salary Component",
			"name": "EC Night Premium 25%",
			"salary_component": "EC Night Premium 25%",
			"type": "Earning",
			"amount_based_on_formula": 1,
			"formula": "(ec_hourly_rate or 0) * 0.25 * (ec_night_min or 0) / 60",
		},
		{
			"doctype": "Salary Component",
			"name": "EC Alimony Withholding",
			"salary_component": "EC Alimony Withholding",
			"type": "Deduction",
			"amount_based_on_formula": 1,
			"formula": "(ec_alimony_order or 0) + (ec_alimony_carried or 0)",
		},
		{
			"doctype": "Salary Component",
			"name": "EC Salary Advance Deduction",
			"salary_component": "EC Salary Advance Deduction",
			"type": "Deduction",
			"amount_based_on_formula": 1,
			"formula": "(ec_advance_deduction or 0) + (ec_advance_carried or 0)",
		},
	]
