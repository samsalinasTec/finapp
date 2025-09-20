from .validators import safe_div
from ..models import Financials, Ratios

def compute(fin: Financials) -> Ratios:
    b, i = fin.balance, fin.income
    r = Ratios()

    # Liquidez
    r.current_ratio = safe_div(b.current_assets, b.current_liabilities)
    quick_assets = (b.cash or 0) + (b.accounts_receivable or 0)
    r.quick_ratio = safe_div(quick_assets, b.current_liabilities)
    if b.current_assets is not None and b.current_liabilities is not None:
        r.working_capital = (b.current_assets or 0) - (b.current_liabilities or 0)

    # Apalancamiento
    r.debt_to_equity = safe_div(b.total_liabilities, b.shareholders_equity)
    r.interest_coverage = safe_div((i.ebitda or i.operating_income), i.interest_expense)

    # Rentabilidad
    r.gross_margin = safe_div(i.gross_profit, i.revenue)
    r.operating_margin = safe_div(i.operating_income, i.revenue)
    r.net_margin = safe_div(i.net_income, i.revenue)
    r.roa = safe_div(i.net_income, b.total_assets)
    r.roe = safe_div(i.net_income, b.shareholders_equity)
    r.ebitda_margin = safe_div(i.ebitda, i.revenue)

    # Eficiencia
    r.asset_turnover = safe_div(i.revenue, b.total_assets)
    r.inventory_turnover = safe_div(i.cogs, b.inventory)
    return r
