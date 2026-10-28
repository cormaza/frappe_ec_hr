"""Ecuadorian custom fields for hrms documents (data only, no frappe import).

Returned in `create_custom_fields` format: `{doctype: [field, ...]}`. Labels
stay raw English (translated at display time; markers live in
`ec_hr/locale/i18n_markers.py`). No `insert_after` anchors: hrms core
fieldnames are pinned in bench, and a wrong anchor breaks install — order is
refined there, never assumed here.
"""

from ec_hr.payroll.contract import ContractKind


def _select(fieldname: str, label: str, options: list[str]) -> dict[str, object]:
	return {
		"fieldname": fieldname,
		"label": label,
		"fieldtype": "Select",
		"options": "\n".join(options),
		"reqd": 0,
	}


def get_custom_fields() -> dict[str, list[dict[str, object]]]:
	"""Return Ecuadorian custom fields keyed by target DocType."""
	id_types = ["Cedula", "RUC Natural", "RUC Private", "RUC Public", "Passport"]
	contract_kinds = [kind.value for kind in ContractKind]
	return {
		"Employee": [
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
		]
	}
