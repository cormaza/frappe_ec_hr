"""Age computation for youth-work and vacation rules (pure Python, no frappe).

Bands follow CT Art. 134 (under-15 work ban with double-pay penalty) and
Art. 69 para. 3 (20 vacation days under 16, 18 days at 16-17) plus the Art. 69
seniority uplift (+1 day per year beyond 5, capped at +15). The 15-18
night/hazardous/overtime block is a conservative default: the exact CONNA
Title V wording is still `to-verify-in-bench`.
"""

from datetime import date
from enum import Enum


class YouthCategory(str, Enum):
	"""Age bands with distinct statutory treatment."""

	UNDER_15 = "under_15"
	AGE_15 = "age_15"
	AGE_16_17 = "age_16_17"
	ADULT = "adult"


def age_on(birthdate: date, as_of: date) -> int:
	"""Return completed years of age on `as_of`."""
	years = as_of.year - birthdate.year
	if (as_of.month, as_of.day) < (birthdate.month, birthdate.day):
		years -= 1
	return years


def youth_category(birthdate: date, as_of: date) -> YouthCategory:
	"""Classify `birthdate` into a statutory band on `as_of`."""
	years = age_on(birthdate, as_of)
	if years < 15:
		return YouthCategory.UNDER_15
	if years < 16:
		return YouthCategory.AGE_15
	if years < 18:
		return YouthCategory.AGE_16_17
	return YouthCategory.ADULT


def is_prohibited_assignment(
	category: YouthCategory,
	*,
	night: bool = False,
	hazardous: bool = False,
	overtime: bool = False,
) -> bool:
	"""Return True when assigning `category` to such work is barred."""
	if category == YouthCategory.UNDER_15:
		return True
	if category == YouthCategory.ADULT:
		return False
	return night or hazardous or overtime


def vacation_annual_days(category: YouthCategory, seniority_years: int = 0) -> int:
	"""Return statutory annual vacation days (Art. 69)."""
	if category in (YouthCategory.UNDER_15, YouthCategory.AGE_15):
		return 20
	if category == YouthCategory.AGE_16_17:
		return 18
	return 15 + min(max(seniority_years - 5, 0), 15)
