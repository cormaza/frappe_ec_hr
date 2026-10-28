"""BIESS loan payroll legs (pure Python, no frappe).

The BIESS grants and amortizes; payroll only withholds the notified
installment each month and carries any arrears forward. No amortization math
lives here by design.
"""

try:
	from frappe import _
except ImportError:  # pragma: no cover - Ring 1 fallback, bench uses frappe._

	def _(message: str) -> str:
		return message


def withholding(notified_installment: float) -> float:
	"""Return the month's BIESS withholding: the notified installment."""
	if notified_installment < 0:
		raise ValueError(_("Notified installment cannot be negative."))
	return round(notified_installment, 2)


def carry_arrears(previous: float, notified: float, withheld: float) -> float:
	"""Roll arrears forward: previous + notified - withheld."""
	if previous < 0 or notified < 0 or withheld < 0:
		raise ValueError(_("Arrears inputs cannot be negative."))
	return round(previous + notified - withheld, 2)
