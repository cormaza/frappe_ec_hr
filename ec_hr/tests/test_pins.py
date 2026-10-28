import unittest
from datetime import date

from ec_hr.payroll.iess_batch import ent_line, ins_line, msu_line, pfm_line, pfr_line, sal_line
from ec_hr.payroll.rdep import rdep_xml, xsd_worker
from ec_hr.payroll.sut import payment_deadline, sut_checklist

try:
	from frappe.tests import UnitTestCase
except ImportError:  # pragma: no cover
	UnitTestCase = unittest.TestCase  # type: ignore[misc,assignment]


class TestIessBatchLines(UnitTestCase):
	"""hl5 batch layouts: `;`-separated ASCII, `.` decimals, golden vectors
	adapted from the official page examples."""

	def test_sal_golden_vector(self) -> None:
		self.assertEqual(
			sal_line(
				employer_ruc="1090075744001",
				branch="0001",
				year=2003,
				month=3,
				cedula="1001915212",
				exit_date="20030131",
				cause="A",
			),
			"1090075744001;0001;2003;03;SAL;1001915212;20030131;A;00000000",
		)

	def test_msu_golden_vector(self) -> None:
		self.assertEqual(
			msu_line(
				employer_ruc="1090075744001",
				branch="0001",
				year=2003,
				month=3,
				cedula="1001915212",
				new_salary=222.22,
			),
			"1090075744001;0001;2003;03;MSU;1001915212;222.22",
		)

	def test_ent_line(self) -> None:
		self.assertEqual(
			ent_line(
				employer_ruc="1090075744001",
				branch="0001",
				year=2003,
				month=3,
				cedula="1001915212",
				hired="19950101",
				registered="20030101",
				jornada="1",
				seguro="R",
				employer_code="2",
				relation="06",
				position="Cargo",
				sector="1608551004148",
				salary=111.11,
				origin="P",
			),
			"1090075744001;0001;2003;03;ENT;1001915212;19950101;20030101;1;R;2;06;Cargo;1608551004148;111.11;P",
		)

	def test_ins_and_reserve_lines(self) -> None:
		self.assertEqual(
			ins_line(
				employer_ruc="1090075744001",
				branch="0001",
				year=2003,
				month=3,
				cedula="1001915212",
				extras=12.34,
				cause="X",
			),
			"1090075744001;0001;2003;03;INS;1001915212;12.34;X",
		)
		self.assertEqual(
			pfr_line(
				employer_ruc="0160010070001",
				branch="0001",
				year=2002,
				month=7,
				cedula="0102981931",
				total_salary=105.2,
				period="2002-07 A 2003-06",
				months=12,
			),
			"0160010070001;0001;2002;07;PFR;0102981931;105.2;2002-07 A 2003-06;12",
		)
		self.assertEqual(
			pfm_line(
				employer_ruc="0160010070001",
				branch="0001",
				year=2009,
				month=7,
				cedula="0102981931",
				total_salary=105.2,
				period="2009-07 A 2009-07",
				months=1,
				period_type="G",
			),
			"0160010070001;0001;2009;07;PFM;0102981931;105.2;2009-07 A 2009-07;01;G",
		)

	def test_bad_fields_fail(self) -> None:
		with self.assertRaises(ValueError):
			sal_line(
				employer_ruc="123",
				branch="0001",
				year=2003,
				month=3,
				cedula="1001915212",
				exit_date="20030131",
				cause="A",
			)
		with self.assertRaises(ValueError):
			msu_line(
				employer_ruc="1090075744001",
				branch="0001",
				year=2003,
				month=13,
				cedula="1001915212",
				new_salary=222.22,
			)
		with self.assertRaises(ValueError):
			sal_line(
				employer_ruc="1090075744001",
				branch="0001",
				year=2003,
				month=3,
				cedula="1001915212",
				exit_date="2003-01-31",
				cause="A",
			)


class TestRdepSchemaVersion(UnitTestCase):
	"""Builders version by schema year; only 2023 is pinned (no public 2026 XSD)."""

	def test_default_schema_is_2023(self) -> None:
		document = rdep_xml("1790000028001", 2025, [], schema="2023")
		self.assertIn("<anio>2025</anio>", document)

	def test_unknown_schema_fails(self) -> None:
		with self.assertRaises(ValueError):
			rdep_xml("1790000028001", 2025, [], schema="2026")


class TestSutChecklist(UnitTestCase):
	"""SUT manual filing: worker data + liquidation + signed acta PDF +
	payment proof PDF, payable within 30 days (MDT-2017-0135)."""

	def _act(self, **overrides):  # type: ignore[no-untyped-def]
		act = {
			"id_number": "1710034065",
			"full_name": "Test Worker",
			"hire_date": "2020-01-15",
			"exit_date": "2026-10-01",
			"cause": "169.9",
			"lines": [{"concept": "desahucio", "amount": 1000.0}],
			"total": 1000.0,
			"signed_acta": "/files/acta.pdf",
			"payment_proof": "/files/pago.pdf",
		}
		act.update(overrides)
		return act

	def test_ready_act_has_no_issues(self) -> None:
		self.assertEqual(sut_checklist(self._act()), [])

	def test_missing_fields_and_mismatch_reported(self) -> None:
		issues = sut_checklist(self._act(signed_acta=None, total=900.0))
		self.assertIn("missing:signed_acta", issues)
		self.assertIn("total-mismatch", issues)

	def test_payment_deadline_thirty_days(self) -> None:
		self.assertEqual(payment_deadline(date(2026, 10, 1)), date(2026, 10, 31))
