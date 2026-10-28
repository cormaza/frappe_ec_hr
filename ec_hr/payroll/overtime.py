"""Day/night split and overtime valuation (pure Python, no frappe).

Night runs 19:00-06:00 (Art. 49, +25% over the equal-length day shift).
Overtime needs written agreement plus inspector authorization and caps at 4h
a day / 12h a week (Art. 55.1): daytime supplement +50%, night supplement
+100% on the day-hour base, Saturday/Sunday work +100% (Art. 55.2-55.4).

Night overtime stacks the full 225% (day base + 25% night premium + 100%
night supplement) per user decision — the stacking reading stays
bench-verifiable. Naive datetimes are assumed to share one zone (Guayaquil
observes no daylight saving, so wall-clock arithmetic is exact).
"""

from datetime import datetime, time, timedelta
from itertools import pairwise

try:
	from frappe import _
except ImportError:  # pragma: no cover - Ring 1 fallback, bench uses frappe._

	def _(message: str) -> str:
		return message


NIGHT_START = time(19, 0)
NIGHT_END = time(6, 0)

#: Overtime caps in minutes (Art. 55.1).
MAX_DAILY_OVERTIME_MIN = 4 * 60
MAX_WEEKLY_OVERTIME_MIN = 12 * 60


def _is_night(moment: time) -> bool:
	return moment >= NIGHT_START or moment < NIGHT_END


def split_day_night(start: datetime, end: datetime) -> tuple[int, int]:
	"""Split a shift into (day_minutes, night_minutes) at 06:00/19:00/midnight."""
	if end <= start:
		raise ValueError(_("Shift end must be after shift start."))
	boundaries = {start, end}
	cursor = start.replace(hour=0, minute=0, second=0, microsecond=0)
	while cursor <= end:
		for mark in (time(0, 0), NIGHT_END, NIGHT_START):
			point = cursor.replace(hour=mark.hour, minute=mark.minute)
			if start < point < end:
				boundaries.add(point)
		cursor += timedelta(days=1)
	ordered = sorted(boundaries)
	day = night = 0
	for first, second in pairwise(ordered):
		minutes = int((second - first).total_seconds() // 60)
		if _is_night(first.time()):
			night += minutes
		else:
			day += minutes
	return day, night


def _value(rate_per_hour: float, minutes: int, factor: float) -> float:
	return round(rate_per_hour * factor * minutes / 60, 2)


def night_premium_pay(rate_per_hour: float, night_minutes: int) -> float:
	"""Value the +25% night premium leg (Art. 49)."""
	return _value(rate_per_hour, night_minutes, 0.25)


def supplement_pay(rate_per_hour: float, minutes: int, *, night: bool) -> float:
	"""Value supplementary hours: +50% daytime, +100% night (Art. 55.2)."""
	return _value(rate_per_hour, minutes, 2.0 if night else 1.5)


def extraordinary_pay(rate_per_hour: float, minutes: int) -> float:
	"""Value Saturday/Sunday/holiday work at +100% (Art. 55.4)."""
	return _value(rate_per_hour, minutes, 2.0)


def night_overtime_pay(rate_per_hour: float, minutes: int) -> float:
	"""Value 24:00-06:00 overtime at the full 225% stack (user decision)."""
	return _value(rate_per_hour, minutes, 2.25)


def check_overtime_caps(daily_minutes: list[float], weekly_minutes: float) -> list[str]:
	"""Report Art. 55.1 cap breaches; empty list means compliant."""
	violations = []
	for index, minutes in enumerate(daily_minutes, start=1):
		if minutes > MAX_DAILY_OVERTIME_MIN:
			violations.append(_("Day {0} exceeds the 4-hour daily overtime cap.").format(index))
	if weekly_minutes > MAX_WEEKLY_OVERTIME_MIN:
		violations.append(_("Week exceeds the 12-hour weekly overtime cap."))
	return violations
