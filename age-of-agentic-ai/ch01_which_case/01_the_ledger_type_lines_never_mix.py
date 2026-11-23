# Strategic HR in the Age of Agentic AI, Chapter 1: Which Case
# Listing: The Ledger Type: Lines Never Mix (Under the Hood)
# The two closing lines are the whole point. The first returns minus $32k; the second fails loudly instead of producing the $40k win.

from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class Qty:
    amount: Decimal
    unit: str        # "USD", "INR" or "hours"
    line: str        # "cash", "capacity", "risk" or "growth"

    def __add__(self, other: "Qty") -> "Qty":
        if (self.unit, self.line) != (other.unit, other.line):
            raise TypeError(f"{other.line} in {other.unit} cannot "
                            f"join {self.line} in {self.unit}")
        return Qty(self.amount + other.amount, self.unit, self.line)

def total(items, line, unit):
    zero = Qty(Decimal(0), unit, line)
    return sum((q for q in items if (q.line, q.unit) == (line, unit)), zero)

case_a = [Qty(Decimal(-20000), "USD", "cash"),     # build
          Qty(Decimal(-12000), "USD", "cash"),     # run
          Qty(Decimal(1440), "hours", "capacity")]

total(case_a, "cash", "USD").amount        # Decimal('-32000')
case_a[0] + case_a[2]                      # TypeError: by design
