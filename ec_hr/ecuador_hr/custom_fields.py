"""Ecuadorian custom fields for hrms documents (data only, no frappe import).

Returned in `create_custom_fields` format: `{doctype: [field, ...]}`. Labels
stay raw English (translated at display time; markers live in
`ec_hr/locale/i18n_markers.py`). Fields chain through `insert_after` inside
dedicated EC sections anchored on stable core fieldnames (verified against
the installed erpnext/hrms JSON in bench); Selects start with a blank option
so new docs never silently default to the first value.
"""

from ec_hr.payroll.contract import ContractKind


def _select(fieldname: str, label: str, options: list[str]) -> dict[str, object]:
	# Display values are Title Case for HR readability; stored values stay
	# lowercase identifiers (see payroll.contract.parse_contract_kind).
	display = [option.replace("_", " ").title() for option in options]
	return {
		"fieldname": fieldname,
		"label": label,
		"fieldtype": "Select",
		"options": "\n" + "\n".join(display),
		"reqd": 0,
	}


def _section(fieldname: str, label: str) -> dict[str, object]:
	return {"fieldname": fieldname, "label": label, "fieldtype": "Section Break"}


def _chain(fields: list[dict[str, object]], first_anchor: str) -> list[dict[str, object]]:
	"""Chain `insert_after` so every field lands inside its EC section."""
	previous = first_anchor
	for field in fields:
		field["insert_after"] = previous
		previous = str(field["fieldname"])
	return fields


def get_custom_fields() -> dict[str, list[dict[str, object]]]:
	"""Return Ecuadorian custom fields keyed by target DocType."""
	id_types = ["Cedula", "RUC Natural", "RUC Private", "RUC Public", "Passport"]
	contract_kinds = [kind.value for kind in ContractKind]
	employee = _chain(
		[
			_section("ec_details_section", "Ecuadorian Details"),
			_select("ec_id_type", "Ecuadorian ID Type", id_types),
			{
				"fieldname": "ec_id_number",
				"label": "Ecuadorian ID Number",
				"fieldtype": "Data",
				"reqd": 0,
			},
			{
				"fieldname": "ec_id_validated",
				"label": "Ecuadorian ID Validated",
				"fieldtype": "Check",
				"read_only": 1,
				"description": "Checksum result — review the ID number when unchecked.",
			},
			{
				"fieldname": "ec_nationality",
				"label": "Nationality",
				"fieldtype": "Data",
			},
			{
				"fieldname": "ec_visa_type",
				"label": "Visa Type",
				"fieldtype": "Data",
				"depends_on": "eval:doc.ec_id_type=='Passport'",
			},
			{
				"fieldname": "ec_work_permit_expiry",
				"label": "Work Permit Expiry",
				"fieldtype": "Date",
				"depends_on": "eval:doc.ec_id_type=='Passport'",
			},
			_select("ec_contract_kind", "Ecuadorian Contract Kind", contract_kinds),
			{
				"fieldname": "ec_sut_contract_id",
				"label": "SUT Contract ID",
				"fieldtype": "Data",
			},
			{
				"fieldname": "ec_probation_end",
				"label": "Probation End Date",
				"fieldtype": "Date",
			},
			{
				"fieldname": "ec_disability_pct",
				"label": "Disability Percentage",
				"fieldtype": "Percent",
			},
			{
				"fieldname": "ec_conadis_card",
				"label": "CONADIS Card Reference",
				"fieldtype": "Data",
				"depends_on": "eval:doc.ec_disability_pct>0",
			},
			{
				"fieldname": "ec_disability_card_expiry",
				"label": "Disability Card Expiry",
				"fieldtype": "Date",
				"depends_on": "eval:doc.ec_disability_pct>0",
			},
			{
				"fieldname": "ec_substitute",
				"label": "Disability Substitute",
				"fieldtype": "Check",
			},
			{
				"fieldname": "ec_family_charges",
				"label": "Family Charges",
				"fieldtype": "Table",
				"options": "EC Family Charge",
			},
			{
				"fieldname": "ec_xiii_accumulated",
				"label": "Accumulate Thirteenth Salary",
				"fieldtype": "Check",
			},
			{
				"fieldname": "ec_xiv_accumulated",
				"label": "Accumulate Fourteenth Salary",
				"fieldtype": "Check",
			},
			_select("ec_xiv_region", "Fourteenth Salary Region", ["costa", "sierra"]),
			{
				"fieldname": "ec_entry_notice_date",
				"label": "IESS Entry Notice Date",
				"fieldtype": "Date",
			},
			{
				"fieldname": "ec_exit_notice_date",
				"label": "IESS Exit Notice Date",
				"fieldtype": "Date",
			},
		],
		"create_user_automatically",
	)
	slip = _chain(
		[
			_section("ec_pay_section", "Ecuadorian Payroll Inputs"),
			{
				"fieldname": "ec_hourly_rate",
				"label": "Hourly Rate",
				"fieldtype": "Currency",
			},
			{
				"fieldname": "ec_overtime_day_min",
				"label": "Overtime Daytime Minutes",
				"fieldtype": "Int",
			},
			{
				"fieldname": "ec_overtime_night_min",
				"label": "Overtime Night Minutes",
				"fieldtype": "Int",
			},
			{
				"fieldname": "ec_extraordinary_min",
				"label": "Extraordinary Minutes",
				"fieldtype": "Int",
			},
			{
				"fieldname": "ec_night_min",
				"label": "Night Minutes",
				"fieldtype": "Int",
			},
			{
				"fieldname": "ec_overtime_daily_max_min",
				"label": "Overtime Daily Max Minutes",
				"fieldtype": "Int",
			},
			{
				"fieldname": "ec_overtime_weekly_min",
				"label": "Overtime Weekly Minutes",
				"fieldtype": "Int",
			},
			{
				"fieldname": "ec_alimony_order",
				"label": "Alimony Order Amount",
				"fieldtype": "Currency",
			},
			{
				"fieldname": "ec_advance_deduction",
				"label": "Salary Advance Deduction",
				"fieldtype": "Currency",
			},
		],
		"gross_pay",
	)
	leave = _chain(
		[
			{
				"fieldname": "ec_medical_certificate",
				"label": "Medical Certificate",
				"fieldtype": "Attach",
			},
		],
		"sb_other_details",
	)
	return {"Employee": employee, "Salary Slip": slip, "Leave Application": leave}
