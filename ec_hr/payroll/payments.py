"""Bank payment layouts (pure Python, no frappe).

Operational module: bank column specs pin in bench against each bank's
manual (no statutory formula claimed). Layouts are caller-provided column
specs registered by name. Rows validate an identity plus a positive amount
before rendering.
"""

import csv
import io
from typing import Any

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


def matches_layout(rows: list[dict[str, Any]], layout: str | list[str]) -> bool:
	"""Return True when every row carries every layout column."""
	columns = _columns_of(layout)
	return all(all(column in row for column in columns) for row in rows)


def render_csv(rows: list[dict[str, Any]], layout: str | list[str]) -> str:
	"""Render validated rows as CSV under the layout columns."""
	columns = _columns_of(layout)
	if not matches_layout(rows, columns):
		raise ValueError(_("Payment rows miss layout columns."))
	buffer = io.StringIO()
	writer = csv.writer(buffer)
	writer.writerow(columns)
	for row in rows:
		writer.writerow([row[column] for column in columns])
	return buffer.getvalue().rstrip("\r\n") + "\r\n" if rows else ",".join(columns) + "\r\n"
