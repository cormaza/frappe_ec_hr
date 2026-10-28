import shutil
import subprocess
import unittest
from pathlib import Path
from typing import ClassVar

from ec_hr.payroll.accounting import provision_lines
from ec_hr.payroll.payments import (
	matches_layout,
	pichincha_row,
	register_layout,
	render_csv,
	validate_row,
)
from ec_hr.payroll.rdep import build_record, rdep_xml, validate_batch, xsd_worker

try:
	from frappe.tests import UnitTestCase
except ImportError:  # pragma: no cover
	UnitTestCase = unittest.TestCase  # type: ignore[misc,assignment]

SAMPLE_BANK = "Test Bank Layout"


def _worker(**overrides):  # type: ignore[no-untyped-def]
	record = {
		"id_number": "1710034065",
		"full_name": "Test Worker",
		"gross": 12000.0,
		"taxable": 12000.0,
		"tax_caused": 95.95,
		"withheld": 95.95,
	}
	record.update(overrides)
	return record


class TestRdepRecords(UnitTestCase):
	"""Annual per-worker RDEP/Form-107 dataset: validated dicts + totals.
	XML/XSD serialization pins in bench against the live SRI schema."""

	def test_valid_record_builds(self) -> None:
		record = build_record(**_worker())
		self.assertEqual(record["id_number"], "1710034065")

	def test_missing_key_and_negatives_fail(self) -> None:
		broken = _worker()
		del broken["taxable"]
		with self.assertRaises(ValueError):
			build_record(**broken)
		with self.assertRaises(ValueError):
			build_record(**_worker(gross=-1.0))

	def test_batch_totals(self) -> None:
		totals = validate_batch([_worker(), _worker(gross=6000.0, taxable=6000.0)])
		self.assertEqual(totals["workers"], 2)
		self.assertEqual(totals["gross"], 18000.0)
		self.assertEqual(totals["withheld"], 191.9)


class TestBankLayouts(UnitTestCase):
	"""Layouts are caller-provided specs (no invented bank columns); the
	sample layout below lives in tests only until bench pins real ones."""

	def test_register_render_and_validate(self) -> None:
		register_layout(SAMPLE_BANK, ["id_number", "full_name", "amount"])
		rows = [{"id_number": "1710034065", "full_name": "Test Worker", "amount": 950.0}]
		for row in rows:
			validate_row(row)
		self.assertTrue(matches_layout(rows, SAMPLE_BANK))
		rendered = render_csv(rows, SAMPLE_BANK)
		self.assertEqual(rendered, "id_number,full_name,amount\r\n1710034065,Test Worker,950.0\r\n")

	def test_bad_rows_fail(self) -> None:
		with self.assertRaises(ValueError):
			validate_row({"id_number": "", "amount": 10.0})
		with self.assertRaises(ValueError):
			validate_row({"id_number": "1710034065", "amount": 0.0})
		with self.assertRaises(ValueError):
			render_csv([{"id_number": "x"}], SAMPLE_BANK)


class TestPichinchaRow(UnitTestCase):
	"""Banco Pichincha mass-payment pin (bank's own PDF): fixed PA/USD/CTA,
	integer cents, AHO/CTE, single-char C/R/P, blank code for Pichincha."""

	def _row(self, **overrides):  # type: ignore[no-untyped-def]
		base = {
			"contrapartida": "001",
			"amount": 123.90,
			"tipo_cta": "AHO",
			"numero_cta": "2200123456",
			"tipo_id": "C",
			"numero_id": "1710034065",
			"nombre": "Test Worker",
		}
		base.update(overrides)
		return pichincha_row(**base)

	def test_documented_transforms(self) -> None:
		row = self._row()
		self.assertEqual(
			row,
			{
				"tipo": "PA",
				"moneda": "USD",
				"forma_pago": "CTA",
				"contrapartida": "001",
				"valor": "12390",
				"tipo_cta": "AHO",
				"numero_cta": "2200123456",
				"tipo_id": "C",
				"numero_id": "1710034065",
				"nombre": "Test Worker",
				"codigo_banco": "",
			},
		)

	def test_id_and_account_variants(self) -> None:
		self.assertEqual(self._row(tipo_id="ruc")["tipo_id"], "R")
		self.assertEqual(self._row(tipo_id="pasaporte")["tipo_id"], "P")
		self.assertEqual(self._row(tipo_cta="cte")["tipo_cta"], "CTE")

	def test_invalid_rows_fail(self) -> None:
		with self.assertRaises(ValueError):
			self._row(tipo_cta="XXX")
		with self.assertRaises(ValueError):
			self._row(tipo_id="X")
		with self.assertRaises(ValueError):
			self._row(amount=0.0)
		with self.assertRaises(ValueError):
			self._row(nombre="  ")

	def test_tab_file_without_header(self) -> None:
		layout = list(self._row())
		rendered = render_csv([self._row()], layout, delimiter="\t", header=False)
		self.assertEqual(
			rendered,
			"PA\tUSD\tCTA\t001\t12390\tAHO\t2200123456\tC\t1710034065\tTest Worker\t\r\n",
		)


class TestProvisionLines(UnitTestCase):
	"""Double-entry provision stubs: the chart of accounts always arrives as
	an explicit map (it varies per company)."""

	ACCOUNT_MAP: ClassVar[dict[str, dict[str, str]]] = {
		"thirteenth": {"expense": "5101", "liability": "2110"}
	}

	def test_lines_balance(self) -> None:
		lines = provision_lines([{"concept": "thirteenth", "amount": 100.0}], self.ACCOUNT_MAP)
		self.assertEqual(
			lines,
			[
				{"account": "5101", "debit": 100.0, "credit": 0.0},
				{"account": "2110", "debit": 0.0, "credit": 100.0},
			],
		)

	def test_missing_mapping_fails_loud(self) -> None:
		with self.assertRaises(ValueError):
			provision_lines([{"concept": "mystery", "amount": 10.0}], self.ACCOUNT_MAP)


def _xsd_params(**overrides):  # type: ignore[no-untyped-def]
	params = {
		"benGalpg": "NO",
		"tipIdRet": "C",
		"idRet": "1710034065",
		"apellidoTrab": "Perez",
		"nombreTrab": "Juan",
		"estab": "001",
		"residenciaTrab": "01",
		"paisResidencia": "593",
		"aplicaConvenio": "NA",
		"tipoTrabajDiscap": "04",
		"porcentajeDiscap": 0,
		"tipIdDiscap": "N",
		"suelSal": 12000.0,
		"sobSuelComRemu": 0.0,
		"partUtil": 500.0,
		"intGrabGen": 0.0,
		"impRentEmpl": 0.0,
		"decimTer": 1000.0,
		"decimCuar": 550.0,
		"fondoReserva": 1000.0,
		"salarioDigno": 0.0,
		"otrosIngRenGrav": 0.0,
		"ingGravConEsteEmpl": 14550.0,
		"sisSalNet": 1,
		"apoPerIess": 1134.0,
		"aporPerIessConOtrosEmpls": 0.0,
		"deducVivienda": 0.0,
		"deducSalud": 0.0,
		"deducEducartcult": 0.0,
		"deducAliement": 0.0,
		"deducVestim": 0.0,
		"exoDiscap": 0.0,
		"exoTerEd": 0.0,
		"basImp": 13416.0,
		"impRentCaus": 95.95,
		"valRetAsuOtrosEmpls": 0.0,
		"valImpAsuEsteEmpl": 0.0,
		"valRet": 95.95,
	}
	params.update(overrides)
	return params


class TestXsdWorker(UnitTestCase):
	"""XSD worker subset: required presence, enums, patterns, 2-decimals."""

	def test_amounts_format_two_decimals(self) -> None:
		fields = xsd_worker(_xsd_params())
		self.assertEqual(fields["suelSal"], "12000.00")
		self.assertEqual(fields["valRet"], "95.95")

	def test_missing_required_fails(self) -> None:
		params = _xsd_params()
		del params["suelSal"]
		with self.assertRaises(ValueError):
			xsd_worker(params)

	def test_invalid_enum_pattern_and_negative_fail(self) -> None:
		with self.assertRaises(ValueError):
			xsd_worker(_xsd_params(tipIdRet="X"))
		with self.assertRaises(ValueError):
			xsd_worker(_xsd_params(nombreTrab="José123"))
		with self.assertRaises(ValueError):
			xsd_worker(_xsd_params(suelSal=-1.0))
		with self.assertRaises(ValueError):
			xsd_worker(_xsd_params(extra_key=1.0))

	def test_optional_members_accepted(self) -> None:
		fields = xsd_worker(_xsd_params(deducEduca=100.0, rebajaGastosPersonales=50.0))
		self.assertEqual(fields["deducEduca"], "100.00")
		self.assertEqual(fields["rebajaGastosPersonales"], "50.00")


class TestRdepXml(UnitTestCase):
	"""Document assembly keeps XSD element order and unique workers."""

	XSD_PATH = Path(__file__).resolve().parent.parent / "payroll" / "schemas" / "rdep-2023.xsd"

	def test_element_order(self) -> None:
		document = rdep_xml("1790000028001", 2025, [xsd_worker(_xsd_params())])
		order = [
			line.strip().split(">")[0][1:]
			for line in document.splitlines()
			if line.strip().startswith("<")
			and not line.strip().startswith("</")
			and not line.strip().startswith("<?")
		]
		sequence = [
			"rdep",
			"numRuc",
			"anio",
			"retRelDep",
			"datRetRelDep",
			"empleado",
			"benGalpg",
			"tipIdRet",
			"suelSal",
			"sisSalNet",
			"basImp",
			"valRet",
		]
		positions = [order.index(tag) for tag in sequence]
		self.assertEqual(positions, sorted(positions))

	def test_duplicate_and_employer_validation(self) -> None:
		worker = xsd_worker(_xsd_params())
		with self.assertRaises(ValueError):
			rdep_xml("1790000028001", 2025, [worker, dict(worker)])
		with self.assertRaises(ValueError):
			rdep_xml("123", 2025, [worker])
		with self.assertRaises(ValueError):
			rdep_xml("1790000028001", 2003, [worker])

	@unittest.skipUnless(XSD_PATH.is_file() and shutil.which("xmllint"), "needs vendored XSD and xmllint")
	def test_validates_against_official_xsd(self) -> None:
		document = rdep_xml(
			"1790000028001",
			2025,
			[xsd_worker(_xsd_params())],
			tipo_empleador="PRIVADO_MIXTO",
			ente_seg_social="IESS",
		)
		result = subprocess.run(
			["xmllint", "--noout", "--schema", str(self.XSD_PATH), "-"],
			input=document.encode("utf-8"),
			capture_output=True,
			timeout=60,
		)
		self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8"))
