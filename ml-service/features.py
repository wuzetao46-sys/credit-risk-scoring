"""
Shared definitions of the input features.

Dataset: Lending Club personal loans (USA), 163,987 loans, as prepared by H2O.ai.
Each row is one loan; bad_loan = 1 means the borrower defaulted or the loan was charged off.

The lender's interest rate (int_rate) is NOT a model input: Lending Club set it from
its own risk grade, so using it would copy their model instead of building ours.
We use it afterwards for the economic analysis (is the price right for the risk?).
"""

NUMERIC_FEATURES = [
    "loan_amnt",              # amount requested (USD)
    "term_months",            # 36 or 60
    "emp_length",             # years in current job (0-10)
    "annual_inc",             # annual income (USD)
    "dti",                    # debt-to-income ratio (%)
    "delinq_2yrs",            # number of 30+ day late payments in the last 2 years
    "revol_util",             # revolving credit utilisation (%)
    "total_acc",              # number of credit lines ever opened
    "longest_credit_length",  # years since first credit line
]

CATEGORICAL_FEATURES = [
    "home_ownership",         # RENT, MORTGAGE, OWN, OTHER
    "purpose",                # debt_consolidation, credit_card, car, ...
    "verification_status",    # was the income verified?
    "addr_state",             # US state
]

FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

TARGET = "bad_loan"
INTEREST_RATE = "int_rate"  # used for the economic analysis only

# Human-readable names shown in the web page next to each explanation.
FEATURE_LABELS = {
    "loan_amnt": "Loan amount",
    "term_months": "Term (months)",
    "emp_length": "Years in current job",
    "annual_inc": "Annual income",
    "dti": "Debt-to-income ratio",
    "delinq_2yrs": "Late payments (last 2 years)",
    "revol_util": "Credit card utilisation",
    "total_acc": "Number of credit lines",
    "longest_credit_length": "Credit history length",
    "home_ownership": "Home ownership",
    "purpose": "Loan purpose",
    "verification_status": "Income verified",
    "addr_state": "State",
}

# --- Economic assumptions (state them in the dissertation) ---
# Loss given default: share of the loan the lender loses when the borrower defaults.
LOSS_GIVEN_DEFAULT = 0.70
# For an amortising loan the average outstanding balance is about half the amount,
# so total interest earned ~= amount * rate * years * 0.5.
AVERAGE_BALANCE_FACTOR = 0.5
# Profit margin added on top of the break-even rate when suggesting a price.
TARGET_MARGIN = 0.02
