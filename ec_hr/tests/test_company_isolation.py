"""Multi-company / multi-currency batch hardening (RED — T2)."""

import unittest

try:
	from frappe.tests import UnitTestCase
except ImportError:  # pragma: no cover - Ring 1 fallback
	UnitTestCase = unittest.TestCase  # type: ignore[misc,assignment]

from ec_hr.payroll import accounting, iess_batch, payments, rdep


def _rdep_record(**overrides):
	base = {
		"id_number": "1710034065",
		"full_name": "Test Worker",
		"gross": 1000.0,
		"taxable": 1000.0,
		"tax_caused": 50.0,
		"withheld": 50.0,
	}
	base.update(overrides)
	return base


class TestRdepIsolation(UnitTestCase):
	def test_batch_without_company_passes(self) -> None:
		totals = rdep.validate_batch([_rdep_record()])
		self.assertEqual(totals["workers"], 1)

	def test_batch_mixed_company_rejected(self) -> None:
		with self.assertRaises(ValueError):
			rdep.validate_batch(
				[
					_rdep_record(company="Acme"),
					_rdep_record(company="Other"),
				]
			)

	def test_batch_foreign_currency_rejected(self) -> None:
		with self.assertRaises(ValueError):
			rdep.validate_batch([_rdep_record(currency="EUR")])

	def test_xml_non_unit_rate_rejected(self) -> None:
		with self.assertRaises(ValueError):
			rdep.rdep_xml("1790012345001", 2024, [], exchange_rate=1.2)


class TestIessBatchIsolation(UnitTestCase):
	def _ent(self, ruc="1790012345001", branch="0001"):
		return iess_batch.ent_line(
			employer_ruc=ruc,
			branch=branch,
			year=2024,
			month=1,
			cedula="1710034065",
			hired="20240105",
			registered="20240110",
			jornada="A",
			seguro="B",
			employer_code="EC",
			relation="01",
			position="Worker",
			sector="1790012345001",
			salary=460.0,
			origin="C",
		)

	def test_single_ruc_batch_passes(self) -> None:
		lines = [self._ent(), self._ent()]
		self.assertEqual(iess_batch.assert_batch_header(lines, employer_ruc="1790012345001"), "1790012345001")

	def test_mixed_ruc_batch_rejected(self) -> None:
		lines = [self._ent(ruc="1790012345001"), self._ent(ruc="1790012345002")]
		with self.assertRaises(ValueError):
			iess_batch.assert_batch_header(lines)

	def test_wrong_expected_ruc_rejected(self) -> None:
		with self.assertRaises(ValueError):
			iess_batch.assert_batch_header([self._ent()], employer_ruc="1790012345002")


class TestAccountingIsolation(UnitTestCase):
	def _map(self):
		return {"thirteenth": {"expense": "5101", "liability": "2101"}}

	def _item(self, **overrides):
		base = {"concept": "thirteenth", "amount": 100.0}
		base.update(overrides)
		return base

	def test_items_without_company_pass(self) -> None:
		lines = accounting.provision_lines([self._item()], self._map())
		self.assertEqual(len(lines), 2)

	def test_mixed_company_rejected(self) -> None:
		with self.assertRaises(ValueError):
			accounting.provision_lines([self._item(company="Acme"), self._item(company="Other")], self._map())

	def test_explicit_company_mismatch_rejected(self) -> None:
		with self.assertRaises(ValueError):
			accounting.provision_lines([self._item(company="Acme")], self._map(), company="Other")

	def test_foreign_currency_item_rejected(self) -> None:
		with self.assertRaises(ValueError):
			accounting.provision_lines([self._item(currency="EUR")], self._map())


class TestPaymentsIsolation(UnitTestCase):
	def test_row_foreign_currency_rejected(self) -> None:
		with self.assertRaises(ValueError):
			payments.validate_row({"id_number": "1710034065", "amount": 100.0, "currency": "EUR"})

	def test_csv_mixed_company_rejected(self) -> None:
		rows = [
			{"id_number": "A", "amount": 10.0, "company": "Acme"},
			{"id_number": "B", "amount": 10.0, "company": "Other"},
		]
		with self.assertRaises(ValueError):
			payments.render_csv(rows, ["id_number", "amount", "company"])

	def test_pichincha_foreign_currency_rejected(self) -> None:
		with self.assertRaises(ValueError):
			payments.pichincha_row(
				contrapartida="X",
				amount=100.0,
				tipo_cta="AHO",
				numero_cta="123",
				tipo_id="C",
				numero_id="1710034065",
				nombre="Test",
				currency="EUR",
			)
