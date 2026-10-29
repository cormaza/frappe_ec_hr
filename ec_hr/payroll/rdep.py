"""RDEP / Form 107 record datasets (pure Python, no frappe).

Builds validated per-worker annual dicts plus batch totals shared by the
RDEP annex and the Form 107 certificate. Serialization to the SRI XML/XSD
pins in bench against the live schema — this module never invents it.
"""

import re
from typing import Any

from ec_hr.payroll.company_currency import assert_single_company, assert_usd_only

try:
	from frappe import _
except ImportError:  # pragma: no cover - Ring 1 fallback, bench uses frappe._

	def _(message: str) -> str:
		return message


REQUIRED_KEYS = ("id_number", "full_name", "gross", "taxable", "tax_caused", "withheld")
MONEY_KEYS = ("gross", "taxable", "tax_caused", "withheld")


def _check_record(record: dict[str, Any]) -> None:
	for key in REQUIRED_KEYS:
		if key not in record:
			raise ValueError(_("RDEP record lacks required key: {0}.").format(key))
	for key in MONEY_KEYS:
		if float(record[key]) < 0:
			raise ValueError(_("RDEP record field cannot be negative: {0}.").format(key))


def build_record(**fields: Any) -> dict[str, Any]:
	"""Validate and return one worker's annual RDEP record."""
	record = dict(fields)
	_check_record(record)
	assert_usd_only(record.get("currency"), record.get("exchange_rate"))
	return record


def validate_batch(records: list[dict[str, Any]]) -> dict[str, float]:
	"""Validate every record and return batch totals."""
	for record in records:
		_check_record(record)
		assert_usd_only(record.get("currency"), record.get("exchange_rate"))
	assert_single_company((record.get("company") for record in records), what="company")
	return {
		"workers": len(records),
		"gross": round(sum(float(record["gross"]) for record in records), 2),
		"taxable": round(sum(float(record["taxable"]) for record in records), 2),
		"tax_caused": round(sum(float(record["tax_caused"]) for record in records), 2),
		"withheld": round(sum(float(record["withheld"]) for record in records), 2),
	}


#: Empleado block in exact XSD sequence (optional members marked).
_EMPLEADO_ORDER = (
	"benGalpg",
	"enfcatastro?",
	"numCargRebGastPers?",
	"tipIdRet",
	"idRet",
	"apellidoTrab",
	"nombreTrab",
	"estab",
	"residenciaTrab",
	"paisResidencia",
	"aplicaConvenio",
	"tipoTrabajDiscap",
	"porcentajeDiscap",
	"tipIdDiscap",
	"idDiscap?",
)

#: Ingresos block in exact XSD sequence (all required).
_INGRESOS_ORDER = (
	"suelSal",
	"sobSuelComRemu",
	"partUtil",
	"intGrabGen",
	"impRentEmpl",
	"decimTer",
	"decimCuar",
	"fondoReserva",
	"salarioDigno",
	"otrosIngRenGrav",
	"ingGravConEsteEmpl",
)

#: Gastos block in exact XSD sequence (optional members marked).
_GASTOS_ORDER = (
	"sisSalNet",
	"apoPerIess",
	"aporPerIessConOtrosEmpls",
	"deducVivienda",
	"deducSalud",
	"deducEduca?",
	"deducEducartcult",
	"deducAliement",
	"deducVestim",
	"deducArtycult?",
	"deduccionTurismo?",
	"exoDiscap",
	"exoTerEd",
)

#: Resumen block in exact XSD sequence (optional members marked).
_RESUMEN_ORDER = (
	"basImp",
	"impRentCaus",
	"rebajaGastosPersonales?",
	"impuestoRentaRebajaGastosPersonales?",
	"valRetAsuOtrosEmpls",
	"valImpAsuEsteEmpl",
	"valRet",
)

_NAME_RE = re.compile(r"[A-Za-z\s]{2,100}\Z")
_ID_RE = re.compile(r"[0-9a-zA-Z]{3,13}\Z")
_DIGITS3_RE = re.compile(r"[0-9]{3}\Z")

_ENUMS = {
	"tipIdRet": frozenset({"C", "P", "E"}),
	"tipIdDiscap": frozenset({"C", "P", "E", "N"}),
	"residenciaTrab": frozenset({"00", "01", "02"}),
	"aplicaConvenio": frozenset({"SI", "NO", "NA", "SD"}),
	"tipoTrabajDiscap": frozenset({"00", "01", "02", "03", "04"}),
	"benGalpg": frozenset({"SI", "NO"}),
	"enfcatastro": frozenset({"SI", "NO"}),
	"tipoEmpleador": frozenset({"PRIVADO_MIXTO", "PUBLICO"}),
	"enteSegSocial": frozenset({"IESS", "ISSFA_ISSPOL"}),
}


def xsd_worker(params: dict[str, Any]) -> dict[str, str]:
	"""Validate `params` against the RDEP XSD worker subset; return formatted fields.

	Required vs optional follows the XSD minOccurs; element order is owned by
	`rdep_xml`. Names must be ASCII letters/spaces (the XSD pattern rejects
	tildes); amounts format to two decimals.
	"""
	fields: dict[str, str] = {}
	for order in (_EMPLEADO_ORDER, _INGRESOS_ORDER, _GASTOS_ORDER, _RESUMEN_ORDER):
		for key in order:
			optional = key.endswith("?")
			tag = key.rstrip("?")
			if tag not in params:
				if optional:
					continue
				raise ValueError(_("RDEP worker lacks required field: {0}.").format(tag))
			value = params[tag]
			fields[tag] = _format_field(tag, value)
	extra = sorted(set(params) - set(fields))
	if extra:
		raise ValueError(_("RDEP worker has unknown fields: {0}.").format(extra))
	return fields


def _format_field(tag: str, value: Any) -> str:
	if tag in _ENUMS:
		text = str(value)
		if text not in _ENUMS[tag]:
			raise ValueError(_("RDEP field {0} has an invalid value: {1}.").format(tag, value))
		return text
	if tag in ("apellidoTrab", "nombreTrab"):
		text = str(value)
		if not _NAME_RE.match(text):
			raise ValueError(_("RDEP worker name is invalid: {0}.").format(value))
		return text
	if tag in ("idRet", "idDiscap"):
		text = str(value)
		if not _ID_RE.match(text):
			raise ValueError(_("RDEP worker id is invalid: {0}.").format(value))
		return text
	if tag in ("estab", "paisResidencia"):
		text = str(value)
		if not _DIGITS3_RE.match(text):
			raise ValueError(_("RDEP field {0} needs 3 digits: {1}.").format(tag, value))
		return text
	if tag == "sisSalNet":
		number = int(value)
		if number not in (1, 2):
			raise ValueError(_("RDEP sisSalNet must be 1 or 2: {0}.").format(value))
		return str(number)
	if tag == "porcentajeDiscap":
		number = int(value)
		if not 0 <= number <= 100:
			raise ValueError(_("RDEP disability percent out of range: {0}.").format(value))
		return str(number)
	if tag == "numCargRebGastPers":
		number = int(value)
		if not 0 <= number <= 5:
			raise ValueError(_("RDEP dependent count out of range: {0}.").format(value))
		return str(number)
	amount = float(value)
	if amount < 0:
		raise ValueError(_("RDEP amount cannot be negative: {0}.").format(tag))
	return f"{amount:.2f}"


def _order(keys: tuple[str, ...], fields: dict[str, str]) -> list[tuple[str, str]]:
	return [(key.rstrip("?"), fields[key.rstrip("?")]) for key in keys if key.rstrip("?") in fields]


def rdep_xml(
	num_ruc: str,
	anio: int,
	workers: list[dict[str, str]],
	*,
	tipo_empleador: str | None = None,
	ente_seg_social: str | None = None,
	schema: str = "2023",
	currency: str | None = None,
	exchange_rate: float | None = None,
) -> str:
	"""Build the RDEP annex XML document (element order per the XSD)."""
	assert_usd_only(currency, exchange_rate)
	if schema != "2023":
		raise ValueError(_("Unsupported RDEP schema pinned: {0}. Only 2023 is pinned.").format(schema))
	if len(num_ruc) != 13 or not num_ruc.isdigit():
		raise ValueError(_("Employer RUC must be exactly 13 digits."))
	if anio < 2004:
		raise ValueError(_("RDEP year is invalid: {0}.").format(anio))
	seen = set()
	for worker in workers:
		key = (worker["idRet"], worker["tipIdRet"])
		if key in seen:
			raise ValueError(_("Duplicate RDEP worker: {0}.").format(key))
		seen.add(key)
	lines = [
		'<?xml version="1.0" encoding="UTF-8"?>',
		"<rdep>",
		f"\t<numRuc>{num_ruc}</numRuc>",
		f"\t<anio>{anio}</anio>",
	]
	if tipo_empleador is not None:
		lines.append(f"\t<tipoEmpleador>{_format_field('tipoEmpleador', tipo_empleador)}</tipoEmpleador>")
	if ente_seg_social is not None:
		lines.append(f"\t<enteSegSocial>{_format_field('enteSegSocial', ente_seg_social)}</enteSegSocial>")
	if workers:
		lines.append("\t<retRelDep>")
		for worker in workers:
			lines.append("\t\t<datRetRelDep>")
			lines.append("\t\t\t<empleado>")
			for tag, text in _order(_EMPLEADO_ORDER, worker):
				lines.append(f"\t\t\t\t<{tag}>{text}</{tag}>")
			lines.append("\t\t\t</empleado>")
			for section in (_INGRESOS_ORDER, _GASTOS_ORDER, _RESUMEN_ORDER):
				for tag, text in _order(section, worker):
					lines.append(f"\t\t\t<{tag}>{text}</{tag}>")
			lines.append("\t\t</datRetRelDep>")
		lines.append("\t</retRelDep>")
	lines.append("</rdep>")
	return "\n".join(lines) + "\n"
