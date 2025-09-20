from typing import List
from ..models import Financials, Issue

def safe_div(a, b):
    if a is None or b in (None, 0):
        return None
    try:
        return a / b
    except ZeroDivisionError:
        return None

def check_accounting_constraints(fin: Financials) -> List[Issue]:
    issues: List[Issue] = []
    b, i = fin.balance, fin.income

    # Ecuación contable
    if b.total_assets is not None and b.total_liabilities is not None and b.shareholders_equity is not None:
        diff = abs((b.total_liabilities or 0) + (b.shareholders_equity or 0) - (b.total_assets or 0))
        if diff > 1e-6:  # tolerancia básica
            issues.append(Issue(code="EQ_IMBALANCE",
                                message="Activos ≠ Pasivos + Capital",
                                severity="error",
                                fields=["balance.total_assets","balance.total_liabilities","balance.shareholders_equity"]))

    # Signos
    if i.interest_expense is not None and i.interest_expense < 0:
        issues.append(Issue(code="NEGATIVE_NOT_ALLOWED",
                            message="Gasto por intereses no debe ser negativo",
                            fields=["income.interest_expense"]))

    # Derivaciones básicas
    if i.gross_profit is None and i.revenue is not None and i.cogs is not None:
        # No es issue; se puede derivar más adelante
        pass

    # Faltantes críticos
    critical_missing = []
    for fpath in ["balance.total_assets","balance.total_liabilities","balance.shareholders_equity",
                  "income.revenue","income.net_income"]:
        # revisión ligera en fields_raw sería mejor; por simplicidad revisamos atributos
        obj, attr = fpath.split(".")
        if getattr(getattr(fin, obj), attr) is None:
            critical_missing.append(fpath)
    if critical_missing:
        issues.append(Issue(code="MISSING_REQUIRED",
                            message="Faltan campos críticos",
                            severity="error",
                            fields=critical_missing))
    return issues
