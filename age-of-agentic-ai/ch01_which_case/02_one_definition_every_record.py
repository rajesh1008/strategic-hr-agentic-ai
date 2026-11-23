# Strategic HR in the Age of Agentic AI, Chapter 1: Which Case
# Listing: One Definition, Every Record (Under the Hood)
# Illustrative pay of 100: excluded allowances of 60 exceed half by 10, so wages for the statute are 50, not 40. Counsel confirms the excluded list.

from decimal import Decimal

def statutory_wages(pay: dict[str, Decimal], excluded: set[str]) -> Decimal:
    """Code on Wages, 2019, s.2(y) proviso: when excluded payments exceed
    one half of all remuneration, the excess is treated as wages."""
    total = sum(pay.values(), Decimal(0))
    base = sum((v for k, v in pay.items() if k not in excluded), Decimal(0))
    excess = max(Decimal(0), (total - base) - total / 2)
    return base + excess

pay = {"basic": Decimal(40), "da": Decimal(0),
       "hra": Decimal(30), "special_allowance": Decimal(30)}
statutory_wages(pay, excluded={"hra", "special_allowance"})   # Decimal('50')
