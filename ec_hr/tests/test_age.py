import unittest
from datetime import date

from ec_hr.payroll.age import YouthCategory, age_on, is_prohibited_assignment, vacation_annual_days, youth_category

try:
	from frappe.tests import UnitTestCase
except ImportError:  # pragma: no cover
	UnitTestCase = unittest.TestCase  # type: ignore[misc,assignment]


class TestAgeOn(UnitTestCase):
	"""Completed years on the reference date (Guayaquil calendar dates in)."""

	def test_exact_birthday(self) -> None:
		self.assertEqual(age_on(date(2008, 10, 28), date(2026, 10, 28)), 18)

	def test_day_before_birthday(self) -> None:
		self.assertEqual(age_on(date(2008, 10, 28), date(2026, 10, 27)), 17)

	def test_leap_day_birthday(self) -> None:
		self.assertEqual(age_on(date(2020, 2, 29), date(2026, 2, 28)), 5)
		self.assertEqual(age_on(date(2020, 2, 29), date(2026, 3, 1)), 6)


class TestYouthCategory(UnitTestCase):
	"""Bands follow CT Art. 134 (<15 banned) and Art. 69 vacation ages."""

	def test_bands(self) -> None:
		as_of = date(2026, 10, 28)
		self.assertEqual(youth_category(date(2012, 1, 1), as_of), YouthCategory.UNDER_15)
		self.assertEqual(youth_category(date(2011, 10, 28), as_of), YouthCategory.AGE_15)
		self.assertEqual(youth_category(date(2010, 1, 1), as_of), YouthCategory.AGE_16_17)
		self.assertEqual(youth_category(date(2008, 10, 28), as_of), YouthCategory.ADULT)


class TestProhibitedAssignment(UnitTestCase):
	"""Under-15 always blocked (Art. 134); adolescents conservatively blocked
	for night/hazardous/overtime until the CONNA text is pinned in bench."""

	def test_under_15_always_blocked(self) -> None:
		self.assertTrue(is_prohibited_assignment(YouthCategory.UNDER_15))

	def test_adolescent_blocked_only_for_restricted_flags(self) -> None:
		self.assertFalse(is_prohibited_assignment(YouthCategory.AGE_15))
		self.assertTrue(is_prohibited_assignment(YouthCategory.AGE_15, night=True))
		self.assertTrue(is_prohibited_assignment(YouthCategory.AGE_16_17, hazardous=True))
		self.assertTrue(is_prohibited_assignment(YouthCategory.AGE_16_17, overtime=True))

	def test_adult_never_blocked(self) -> None:
		self.assertFalse(is_prohibited_assignment(YouthCategory.ADULT, night=True, hazardous=True))


class TestVacationAnnualDays(UnitTestCase):
	"""Art. 69: under-16 → 20 days, 16-17 → 18, adults 15 + seniority (+1/year
	after 5, capped at +15)."""

	def test_youth_bands(self) -> None:
		self.assertEqual(vacation_annual_days(YouthCategory.UNDER_15), 20)
		self.assertEqual(vacation_annual_days(YouthCategory.AGE_15), 20)
		self.assertEqual(vacation_annual_days(YouthCategory.AGE_16_17), 18)

	def test_adult_seniority_and_cap(self) -> None:
		self.assertEqual(vacation_annual_days(YouthCategory.ADULT), 15)
		self.assertEqual(vacation_annual_days(YouthCategory.ADULT, seniority_years=5), 15)
		self.assertEqual(vacation_annual_days(YouthCategory.ADULT, seniority_years=6), 16)
		self.assertEqual(vacation_annual_days(YouthCategory.ADULT, seniority_years=30), 30)
