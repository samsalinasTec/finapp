from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field

# --- Pydantic domain models ---

class BalanceSheet(BaseModel):
    cash: Optional[float] = None
    accounts_receivable: Optional[float] = None
    inventory: Optional[float] = None
    current_assets: Optional[float] = None
    total_assets: Optional[float] = None
    accounts_payable: Optional[float] = None
    short_term_debt: Optional[float] = None
    current_liabilities: Optional[float] = None
    long_term_debt: Optional[float] = None
    total_liabilities: Optional[float] = None
    shareholders_equity: Optional[float] = None

class IncomeStatement(BaseModel):
    revenue: Optional[float] = None
    cogs: Optional[float] = None
    gross_profit: Optional[float] = None
    operating_income: Optional[float] = None
    ebitda: Optional[float] = None
    interest_expense: Optional[float] = None
    net_income: Optional[float] = None

class CashFlow(BaseModel):
    operating_cf: Optional[float] = None
    investing_cf: Optional[float] = None
    financing_cf: Optional[float] = None
    free_cf: Optional[float] = None

class ExtractionField(BaseModel):
    path: str
    label: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None
    confidence: float = 0.0
    source_hint: Optional[Dict[str, Any]] = None

class Financials(BaseModel):
    period: str
    currency: str = "MXN"
    scale: str = "UNIDAD"
    balance: BalanceSheet = BalanceSheet()
    income: IncomeStatement = IncomeStatement()
    cashflow: CashFlow = CashFlow()
    fields_raw: Dict[str, ExtractionField] = Field(default_factory=dict)

class Ratios(BaseModel):
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    working_capital: Optional[float] = None
    debt_to_equity: Optional[float] = None
    interest_coverage: Optional[float] = None
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    net_margin: Optional[float] = None
    roa: Optional[float] = None
    roe: Optional[float] = None
    ebitda_margin: Optional[float] = None
    asset_turnover: Optional[float] = None
    inventory_turnover: Optional[float] = None

# --- API payloads ---

class Issue(BaseModel):
    code: str
    message: str
    severity: str = "warn"
    fields: List[str] = Field(default_factory=list)

class ExtractPauseResponse(BaseModel):
    run_id: str
    doc_id: str
    status: str = "NEEDS_REVIEW"
    period: Optional[str] = None
    currency: Optional[str] = None
    scale_hint: Optional[str] = None
    issues: List[Issue] = Field(default_factory=list)
    fields: List[ExtractionField] = Field(default_factory=list)
    confidence_thresholds: Dict[str, float] = Field(default_factory=dict)

class ExtractReadyResponse(BaseModel):
    run_id: str
    doc_id: str
    status: str = "READY"
    financials: Financials
    ratios: Ratios
    audit: List[Dict[str, Any]] = Field(default_factory=list)

class ReviewRequest(BaseModel):
    run_id: str
    corrections: List[Dict[str, Any]]

class WhatIfRequest(BaseModel):
    financials_id: Optional[str] = None
    run_id: Optional[str] = None
    scenario_name: str
    changes: List[Dict[str, Any]]
