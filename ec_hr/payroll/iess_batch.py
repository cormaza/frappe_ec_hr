"""IESS batch ASCII layouts for historia-laboral updates (pure Python).

Field tables pinned from the official hl5 batch page: `;`-separated records,
`.` decimals, one record per affiliate, single yearly/monthly send per
movement. Movements: ENT (entry), SAL (exit), MSU (salary change), INS
(extras variation), PFR/PFM (reserve planillas). Single-character coded
fields (jornada, seguro, relation, causa, origin) reference annex code tables
the page does not publish — they pass through validated only for shape.
"""

from datetime import date

from ec_hr.payroll.company_currency import assert_single_company, require_company

try:
	from frappe import _
except ImportError:  # pragma: no cover - Ring 1 fallback, bench uses frappe._

	def _(message: str) -> str:
		return message


def assert_batch_header(
	lines: list[str], *, employer_ruc: str | None = None, branch: str | None = None
) -> str:
	"""Require every batch line to share one employer RUC (and branch when given)."""
	if not lines:
		return require_company(employer_ruc) if employer_ruc is not None else ""
	rucs = [line.split(";")[0] for line in lines]
	branches = [line.split(";")[1] for line in lines if ";" in line]
	rucc = assert_single_company(rucs, what="employer RUC")
	assert_single_company(branches, what="branch")
	if employer_ruc is not None and rucc != employer_ruc.strip():
		raise ValueError(_("Batch employer RUC {0} does not match expected {1}.").format(rucc, employer_ruc))
	if branch is not None:
		only = assert_single_company(branches, what="branch")
		if only != branch.strip():
			raise ValueError(_("Batch branch {0} does not match expected {1}.").format(only, branch))
	return rucc


def _head(employer_ruc: str, branch: str, year: int, month: int, movement: str) -> list[str]:
	if len(employer_ruc) != 13 or not employer_ruc.isdigit():
		raise ValueError(_("Employer RUC must be exactly 13 digits."))
	if len(branch) != 4 or not branch.isdigit():
		raise ValueError(_("Branch code must be exactly 4 digits."))
	if not 1 <= month <= 12:
		raise ValueError(_("Batch month must fall within 1-12."))
	return [employer_ruc, branch, str(year), f"{month:02d}", movement]


def _cedula(cedula: str) -> str:
	if len(cedula) != 10 or not cedula.isdigit():
		raise ValueError(_("Batch cedula must be exactly 10 digits."))
	return cedula


def _yyyymmdd(value: str) -> str:
	try:
		date(int(value[0:4]), int(value[4:6]), int(value[6:8]))
	except (ValueError, IndexError):
		raise ValueError(_("Batch date must be YYYYMMDD: {0}.").format(value)) from None
	if len(value) != 8 or not value.isdigit():
		raise ValueError(_("Batch date must be YYYYMMDD: {0}.").format(value))
	return value


def _amount(value: float) -> str:
	if value < 0:
		raise ValueError(_("Batch amount cannot be negative."))
	text = f"{value:.2f}".rstrip("0").rstrip(".")
	return text


def _one(char: str, what: str) -> str:
	if len(char) != 1:
		raise ValueError(_("Batch field {0} must be a single character.").format(what))
	return char


def ent_line(
	*,
	employer_ruc: str,
	branch: str,
	year: int,
	month: int,
	cedula: str,
	hired: str,
	registered: str,
	jornada: str,
	seguro: str,
	employer_code: str,
	relation: str,
	position: str,
	sector: str,
	salary: float,
	origin: str,
) -> str:
	"""Build an entry-notice (ENT) batch record."""
	if len(relation) != 2:
		raise ValueError(_("Batch relation must be 2 characters."))
	if len(position) > 64:
		raise ValueError(_("Batch position exceeds 64 characters."))
	if len(sector) != 13 or not sector.isdigit():
		raise ValueError(_("Batch sector must be exactly 13 digits."))
	return ";".join(
		[
			*_head(employer_ruc, branch, year, month, "ENT"),
			_cedula(cedula),
			_yyyymmdd(hired),
			_yyyymmdd(registered),
			_one(jornada, "jornada"),
			_one(seguro, "seguro"),
			employer_code,
			relation,
			position,
			sector,
			_amount(salary),
			_one(origin, "origin"),
		]
	)


def sal_line(
	*,
	employer_ruc: str,
	branch: str,
	year: int,
	month: int,
	cedula: str,
	exit_date: str,
	cause: str,
	death_date: str = "00000000",
) -> str:
	"""Build an exit-notice (SAL) batch record."""
	if death_date != "00000000":
		_yyyymmdd(death_date)
	return ";".join(
		[
			*_head(employer_ruc, branch, year, month, "SAL"),
			_cedula(cedula),
			_yyyymmdd(exit_date),
			_one(cause, "cause"),
			death_date,
		]
	)


def msu_line(*, employer_ruc: str, branch: str, year: int, month: int, cedula: str, new_salary: float) -> str:
	"""Build a salary-change (MSU) batch record."""
	return ";".join([*_head(employer_ruc, branch, year, month, "MSU"), _cedula(cedula), _amount(new_salary)])


def ins_line(
	*,
	employer_ruc: str,
	branch: str,
	year: int,
	month: int,
	cedula: str,
	extras: float,
	cause: str,
) -> str:
	"""Build an extras-variation (INS) batch record."""
	return ";".join(
		[
			*_head(employer_ruc, branch, year, month, "INS"),
			_cedula(cedula),
			_amount(extras),
			_one(cause, "cause"),
		]
	)


def _reserve_head(
	movement: str,
	*,
	employer_ruc: str,
	branch: str,
	year: int,
	month: int,
	cedula: str,
	total_salary: float,
	period: str,
	months: int,
) -> list[str]:
	if len(period) != 17:
		raise ValueError(_("Reserve period must read 'YYYY-MM A YYYY-MM' (17 chars)."))
	return [
		*_head(employer_ruc, branch, year, month, movement),
		_cedula(cedula),
		_amount(total_salary),
		period,
		f"{months:02d}",
	]


def pfr_line(
	*,
	employer_ruc: str,
	branch: str,
	year: int,
	month: int,
	cedula: str,
	total_salary: float,
	period: str,
	months: int,
) -> str:
	"""Build a reserve-planilla (PFR) batch record."""
	return ";".join(
		_reserve_head(
			"PFR",
			employer_ruc=employer_ruc,
			branch=branch,
			year=year,
			month=month,
			cedula=cedula,
			total_salary=total_salary,
			period=period,
			months=months,
		)
	)


def pfm_line(
	*,
	employer_ruc: str,
	branch: str,
	year: int,
	month: int,
	cedula: str,
	total_salary: float,
	period: str,
	months: int,
	period_type: str,
) -> str:
	"""Build a monthly-reserve (PFM) batch record."""
	return ";".join(
		[
			*_reserve_head(
				"PFM",
				employer_ruc=employer_ruc,
				branch=branch,
				year=year,
				month=month,
				cedula=cedula,
				total_salary=total_salary,
				period=period,
				months=months,
			),
			_one(period_type, "period_type"),
		]
	)
