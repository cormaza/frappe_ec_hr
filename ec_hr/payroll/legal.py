"""Ecuadorian statutory payroll constants and helpers (pure Python, no frappe).

Day-0 scaffold: only the IESS contribution rates every later computation
needs. Sector-specific rates and SBU-indexed amounts arrive with the roadmap
phases; the SBU itself is never hardcoded (see AGENTS.md).
"""


def _pct(base: float, rate_pct: float) -> float:
	return round(base * rate_pct / 100.0, 2)


#: Employee personal contribution to IESS (aporte personal), percent.
IESS_PERSONAL_RATE_PCT = 9.45

#: Employer contribution to IESS (aporte patronal), percent.
IESS_EMPLOYER_RATE_PCT = 11.15


def iess_contributions(base: float) -> dict[str, float]:
	"""Split a contribution base into personal and employer IESS amounts.

	Both legs round to cents independently; ``total`` is the rounded sum of
	the rounded legs, matching planilla presentation.
	"""
	personal = _pct(base, IESS_PERSONAL_RATE_PCT)
	employer = _pct(base, IESS_EMPLOYER_RATE_PCT)
	return {"personal": personal, "employer": employer, "total": round(personal + employer, 2)}
