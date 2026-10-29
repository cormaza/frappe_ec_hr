"""Bank payment layouts (pure Python, no frappe).

Operational module: bank column specs pin in bench against each bank's
manual (no statutory formula claimed). Layouts are caller-provided column
specs registered by name. Rows validate an identity plus a positive amount
before rendering.
"""

import csv
import io
from typing import Any

from ec_hr.payroll.company_currency import assert_single_company, assert_usd_only

try:
	from frappe import _
except ImportError:  # pragma: no cover - Ring 1 fallback, bench uses frappe._

	def _(message: str) -> str:
		return message


_LAYOUTS: dict[str, list[str]] = {}


def register_layout(name: str, columns: list[str]) -> None:
	"""Register a caller-provided bank column layout under `name`."""
	_LAYOUTS[name] = list(columns)


def _columns_of(layout: str | list[str]) -> list[str]:
	if isinstance(layout, str):
		if layout not in _LAYOUTS:
			raise ValueError(_("Unknown bank layout: {0}.").format(layout))
		return _LAYOUTS[layout]
	return list(layout)


def validate_row(row: dict[str, Any], *, id_key: str = "id_number", amount_key: str = "amount") -> None:
	"""Require a non-empty identity and a positive amount."""
	if not str(row.get(id_key) or "").strip():
		raise ValueError(_("Payment row lacks identity: {0}.").format(id_key))
	if float(row.get(amount_key) or 0.0) <= 0:
		raise ValueError(_("Payment row amount must be positive: {0}.").format(amount_key))
	if "currency" in row or "exchange_rate" in row:
		assert_usd_only(row.get("currency"), row.get("exchange_rate"))


def matches_layout(rows: list[dict[str, Any]], layout: str | list[str]) -> bool:
	"""Return True when every row carries every layout column."""
	columns = _columns_of(layout)
	return all(all(column in row for column in columns) for row in rows)


def render_csv(
	rows: list[dict[str, Any]],
	layout: str | list[str],
	*,
	delimiter: str = ",",
	header: bool = True,
) -> str:
	"""Render validated rows under the layout columns."""
	assert_single_company((row.get("company") for row in rows), what="company")
	for row in rows:
		if "currency" in row or "exchange_rate" in row:
			assert_usd_only(row.get("currency"), row.get("exchange_rate"))
	columns = _columns_of(layout)
	if not matches_layout(rows, columns):
		raise ValueError(_("Payment rows miss layout columns."))
	buffer = io.StringIO()
	writer = csv.writer(buffer, delimiter=delimiter, lineterminator="\r\n")
	if header:
		writer.writerow(columns)
	for row in rows:
		writer.writerow([row[column] for column in columns])
	return buffer.getvalue()


_TIPO_ID_MAP = {
	"C": "C",
	"R": "R",
	"P": "P",
	"CEDULA": "C",
	"RUC": "R",
	"PASSPORT": "P",
	"PASAPORTE": "P",
}

_TIPO_CTA = frozenset({"AHO", "CTE"})


def pichincha_row(
	*,
	contrapartida: str,
	amount: float,
	tipo_cta: str,
	numero_cta: str,
	tipo_id: str,
	numero_id: str,
	nombre: str,
	codigo_banco: str = "",
	currency: str | None = None,
	exchange_rate: float | None = None,
) -> dict[str, str]:
	"""Build one Banco Pichincha mass-payment row (bank's own PDF pin).

	Fixed TIPO=PA / MONEDA=USD / FORMA DE PAGO=CTA; VALOR as integer cents
	(123.90 -> "12390"); TIPO CTA AHO/CTE; TIPO ID single char C/R/P; bank
	code blank for Pichincha itself. MONEDA is fixed USD: any caller currency
	rate other than USD/1 is rejected fail-closed. Eleven documented fields: the PDF counts
	twelve columns but names only eleven, so the twelfth stays explicitly
	unpinned (no invented column). Emit tab-delimited without header via
	`render_csv(rows, layout, delimiter="\\t", header=False)`.
	"""
	assert_usd_only(currency, exchange_rate)
	if not contrapartida.strip():
		raise ValueError(_("Payment row lacks identity: contrapartida."))
	if amount <= 0:
		raise ValueError(_("Payment row amount must be positive: valor."))
	account_kind = tipo_cta.strip().upper()
	if account_kind not in _TIPO_CTA:
		raise ValueError(_("Unknown account kind: {0}.").format(tipo_cta))
	if not numero_cta.strip():
		raise ValueError(_("Payment row lacks identity: numero_cta."))
	id_kind = _TIPO_ID_MAP.get(tipo_id.strip().upper(), "")
	if not id_kind:
		raise ValueError(_("Unknown ID kind: {0}.").format(tipo_id))
	if not numero_id.strip():
		raise ValueError(_("Payment row lacks identity: numero_id."))
	if not nombre.strip():
		raise ValueError(_("Payment row lacks identity: nombre."))
	return {
		"tipo": "PA",
		"moneda": "USD",
		"forma_pago": "CTA",
		"contrapartida": contrapartida.strip(),
		"valor": str(round(amount * 100)),
		"tipo_cta": account_kind,
		"numero_cta": numero_cta.strip(),
		"tipo_id": id_kind,
		"numero_id": numero_id.strip(),
		"nombre": nombre.strip(),
		"codigo_banco": codigo_banco.strip(),
	}
