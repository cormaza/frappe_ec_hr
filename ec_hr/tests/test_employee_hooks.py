import unittest
from datetime import date
from types import SimpleNamespace

from ec_hr.ecuador_hr.employee_hooks import validate_employee

try:
	import frappe
	_RING_ERRORS = (ValueError, frappe.ValidationError)
except ImportError:  # pragma: no cover - Ring 1 has no frappe package.
	frappe = None  # type: ignore[assignment]
	_RING_ERRORS = (ValueError,)

try:
	from frappe.tests import UnitTestCase
except ImportError:  # pragma: no cover
	UnitTestCase = unittest.TestCase  # type: ignore[misc,assignment]


def _doc(**overrides):  # type: ignore[no-untyped-def]
	base = {
		"ec_id_type": None,
		"ec_id_number": None,
		"ec_id_validated": 0,
		"ec_contract_kind": None,
		"ec_disability_pct": 0.0,
		"date_of_birth": None,
	}
	base.update(overrides)
	return SimpleNamespace(**base)


class TestValidateEmployeePure(UnitTestCase):
	"""Hook logic over namespace docs: ValueError in Ring 1, ValidationError
	(frappe.throw) in bench — same failures, converted by the ring."""

	def test_valid_cedula_passes_and_flags(self) -> None:
		doc = _doc(ec_id_type="Cedula", ec_id_number="1710034065")
		validate_employee(doc)
		self.assertEqual(doc.ec_id_validated, 1)

	def test_invalid_cedula_fails_loud(self) -> None:
		with self.assertRaises(_RING_ERRORS):
			validate_employee(_doc(ec_id_type="Cedula", ec_id_number="1710034060"))

	def test_invalid_ruc_only_flags_and_allows_save(self) -> None:
		doc = _doc(ec_id_type="RUC Natural", ec_id_number="1710034060001")
		validate_employee(doc)
		self.assertEqual(doc.ec_id_validated, 0)

	def test_number_without_type_fails(self) -> None:
		with self.assertRaises(_RING_ERRORS):
			validate_employee(_doc(ec_id_number="1710034065"))

	def test_unknown_contract_kind_fails(self) -> None:
		with self.assertRaises(_RING_ERRORS):
			validate_employee(_doc(ec_contract_kind="hourly"))

	def test_known_contract_kind_passes(self) -> None:
		validate_employee(_doc(ec_contract_kind="indefinite"))

	def test_disability_pct_out_of_range_fails(self) -> None:
		with self.assertRaises(_RING_ERRORS):
			validate_employee(_doc(ec_disability_pct=120.0))

	def test_under_15_birthdate_fails(self) -> None:
		with self.assertRaises(_RING_ERRORS):
			validate_employee(_doc(date_of_birth=date(2015, 1, 1)))

	def test_adult_birthdate_passes(self) -> None:
		validate_employee(_doc(date_of_birth=date(1990, 6, 15)))

	def test_empty_doc_passes(self) -> None:
		validate_employee(_doc())


@unittest.skipUnless(frappe is not None, "bench-only: needs frappe.get_doc")
class TestValidateEmployeeBench(UnitTestCase):
	"""Bench wiring: the hook fails the same way on a real Employee doc."""

	def test_invalid_cedula_raises_validation_error(self) -> None:
		doc = frappe.get_doc(
			{
				"doctype": "Employee",
				"first_name": "Test",
				"date_of_birth": "1990-06-15",
				"ec_id_type": "Cedula",
				"ec_id_number": "1710034060",
			}
		)
		with self.assertRaises(frappe.ValidationError):
			validate_employee(doc)
