"""Leave durations and salary legs (pure Python, no frappe).

Maternity/paternity follow the Art. 152 ladder; combined paternity
extensions resolve by maximum per user decision (never summed). Sickness
pays 100% employer legs on days 1-3 and moves to the IESS rate from day 4
with no employer top-up per user decision — the IESS daily rate is an
explicit parameter because its percentage was not verified during research.
"""

try:
	from frappe import _
except ImportError:  # pragma: no cover - Ring 1 fallback, bench uses frappe._

	def _(message: str) -> str:
		return message


def maternity_days(*, multiple: bool = False) -> int:
	"""Return maternity leave days: 84, or 94 on multiple birth (Art. 152)."""
	return 94 if multiple else 84


def paternity_days(
	*,
	multiple: bool = False,
	cesarean: bool = False,
	premature_or_special: bool = False,
	severe_or_terminal: bool = False,
) -> int:
	"""Return paternity leave days by maximum applicable rung (Art. 152)."""
	days = 15
	if multiple or cesarean:
		days = max(days, 20)
	if premature_or_special:
		days = max(days, 23)
	if severe_or_terminal:
		days = max(days, 25)
	return days


def sickness_legs(day_index: int, daily_salary: float, iess_daily_rate: float) -> tuple[float, float]:
	"""Split a sickness day into (employer_leg, iess_leg).

	`day_index` is 1-based within the leave. Days 1-3 are fully employer-paid;
	from day 4 the IESS rate applies with no employer top-up.
	"""
	if day_index < 1:
		raise ValueError(_("Sickness day index starts at 1."))
	if day_index <= 3:
		return round(daily_salary, 2), 0.0
	return 0.0, round(iess_daily_rate, 2)


def mother_death_transfer(total_maternity: int, enjoyed: int) -> int:
	"""Return the remaining maternity days transferred to the father."""
	if not 0 <= enjoyed <= total_maternity:
		raise ValueError(_("Enjoyed days must fall within the total leave."))
	return total_maternity - enjoyed
