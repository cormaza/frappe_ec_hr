"""Bench install wiring: create Ecuadorian custom fields."""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from ec_hr.ecuador_hr.custom_fields import get_custom_fields
from ec_hr.ecuador_hr.salary_components import get_salary_components


def ensure_salary_components() -> None:
	for spec in get_salary_components():
		name = spec.get("name")
		if not frappe.db.exists("Salary Component", name):
			frappe.get_doc(spec).insert()


def after_install() -> None:
	create_custom_fields(get_custom_fields(), ignore_validate=True)
	ensure_salary_components()
