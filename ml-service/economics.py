"""
The economics of a single loan, used by both train.py and app.py.

Simplified one-period model of a lender's profit:
  - borrower repays:   lender earns interest = amount * rate * years * AVERAGE_BALANCE_FACTOR
  - borrower defaults: lender loses           amount * LOSS_GIVEN_DEFAULT
Expected profit = (1 - PD) * interest - PD * loss
"""
import numpy as np

from features import AVERAGE_BALANCE_FACTOR, LOSS_GIVEN_DEFAULT


def interest_earned(amount, rate_percent, term_months):
    years = np.asarray(term_months) / 12
    return np.asarray(amount) * np.asarray(rate_percent) / 100 * years * AVERAGE_BALANCE_FACTOR


def loss_if_default(amount):
    return np.asarray(amount) * LOSS_GIVEN_DEFAULT


def realised_profit(amount, rate_percent, term_months, defaulted):
    """What the lender actually made on loans it approved (used to evaluate decisions)."""
    defaulted = np.asarray(defaulted).astype(bool)
    return np.where(defaulted,
                    -loss_if_default(amount),
                    interest_earned(amount, rate_percent, term_months))


def expected_loss(probability_of_default, amount):
    return probability_of_default * loss_if_default(amount)


def break_even_rate(probability_of_default, term_months):
    """
    Interest rate (in %) at which expected profit is zero:
      (1 - PD) * rate * years * f = PD * LGD   =>   rate = PD * LGD / ((1 - PD) * years * f)
    """
    years = term_months / 12
    pd_ = min(probability_of_default, 0.999)
    return 100 * pd_ * LOSS_GIVEN_DEFAULT / ((1 - pd_) * years * AVERAGE_BALANCE_FACTOR)
