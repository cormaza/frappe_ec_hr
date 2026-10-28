"""Bench install wiring: create Ecuadorian custom fields."""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from ec_hr.ecuador_hr.custom_fields import get_custom_fields


def after_install() -> None:
    create_custom_fields(get_custom_fields(), ignore_validate=True)
