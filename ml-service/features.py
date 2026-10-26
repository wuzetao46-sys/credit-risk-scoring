"""
Shared definitions of the input features.

The UCI "Default of Credit Card Clients" dataset (Taiwan, 2005) has 23
input columns. We deliberately leave SEX out of the model: it is only used
afterwards to check whether the model treats groups fairly.
"""

# Columns the model is trained on, in this exact order.
FEATURES = [
    "LIMIT_BAL",   # credit limit (NT dollars)
    "EDUCATION",   # 1=graduate school, 2=university, 3=high school, 4=others
    "MARRIAGE",    # 1=married, 2=single, 3=others
    "AGE",
    "PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6",  # repayment status, Sep..Apr (-1=paid on time, 1..9=months late)
    "BILL_AMT1", "BILL_AMT2", "BILL_AMT3", "BILL_AMT4", "BILL_AMT5", "BILL_AMT6",  # bill amounts
    "PAY_AMT1", "PAY_AMT2", "PAY_AMT3", "PAY_AMT4", "PAY_AMT5", "PAY_AMT6",        # amounts paid
]

# Only used for the fairness audit, never as a model input.
PROTECTED_ATTRIBUTE = "SEX"  # 1=male, 2=female

TARGET = "default payment next month"

# Human-readable names shown in the web page next to each explanation.
FEATURE_LABELS = {
    "LIMIT_BAL": "Credit limit",
    "EDUCATION": "Education level",
    "MARRIAGE": "Marital status",
    "AGE": "Age",
    "PAY_0": "Repayment status (latest month)",
    "PAY_2": "Repayment status (2 months ago)",
    "PAY_3": "Repayment status (3 months ago)",
    "PAY_4": "Repayment status (4 months ago)",
    "PAY_5": "Repayment status (5 months ago)",
    "PAY_6": "Repayment status (6 months ago)",
    "BILL_AMT1": "Bill amount (latest month)",
    "BILL_AMT2": "Bill amount (2 months ago)",
    "BILL_AMT3": "Bill amount (3 months ago)",
    "BILL_AMT4": "Bill amount (4 months ago)",
    "BILL_AMT5": "Bill amount (5 months ago)",
    "BILL_AMT6": "Bill amount (6 months ago)",
    "PAY_AMT1": "Amount paid (latest month)",
    "PAY_AMT2": "Amount paid (2 months ago)",
    "PAY_AMT3": "Amount paid (3 months ago)",
    "PAY_AMT4": "Amount paid (4 months ago)",
    "PAY_AMT5": "Amount paid (5 months ago)",
    "PAY_AMT6": "Amount paid (6 months ago)",
}
