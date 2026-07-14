"""
services/settlement_service.py — The Minimal Transactions Algorithm.

Problem: Given N people with net balances (positive = owed money, negative = owes money),
find the minimum number of transactions to settle all debts.

Algorithm (Two-Pointer Greedy):
  1. Separate people into creditors (net > 0) and debtors (net < 0).
  2. Sort both lists by absolute amount descending.
  3. At each step, pair the largest creditor with the largest debtor:
       - The smaller absolute value gets fully settled.
       - The remaining balance stays on the larger party.
  4. Repeat until all balances reach 0.

Complexity: O(n log n) for sorting + O(n) for the two-pointer pass = O(n log n) total.

Why is this optimal?
  Each transaction eliminates at least one person completely (either the creditor
  or debtor reaches 0). So at most N-1 transactions are needed, which is the
  theoretical minimum for any settlement problem.

Interview note: This is a classic "Simplify Debts" problem. The greedy approach
works because we're not concerned with WHO pays whom — only the minimum count.
"""
from __future__ import annotations


def compute_minimal_settlements(
    net: dict[int, float],
    names: dict[int, str] | None = None,
) -> list[dict]:
    """
    Compute the minimum transactions to fully settle a group.

    Args:
        net:   {friend_id: net_balance}
               Positive = this person is owed money (creditor).
               Negative = this person owes money (debtor).
        names: Optional {friend_id: name} for human-readable output.

    Returns:
        List of {"from": name/id, "to": name/id, "amount": float}
    """
    if names is None:
        names = {}

    def label(fid: int) -> str:
        return names.get(fid, f"Person#{fid}")

    # Round to 2 decimal places to avoid float noise
    balances = {fid: round(amt, 2) for fid, amt in net.items() if abs(amt) > 0.001}

    # Debtors: owe money (negative balance)
    # Creditors: are owed money (positive balance)
    debtors  = sorted([(fid, -amt) for fid, amt in balances.items() if amt < 0], key=lambda x: -x[1])
    creditors = sorted([(fid, amt) for fid, amt in balances.items() if amt > 0], key=lambda x: -x[1])

    transactions: list[dict] = []

    # Two-pointer greedy
    i, j = 0, 0
    # Work with mutable lists
    d = [list(x) for x in debtors]   # [fid, amount_owed]
    c = [list(x) for x in creditors] # [fid, amount_due]

    while i < len(d) and j < len(c):
        debtor_id,   debt   = d[i]
        creditor_id, credit = c[j]

        # The transaction amount is the minimum of what's owed and what's due
        amount = round(min(debt, credit), 2)

        transactions.append({
            "from":      label(debtor_id),
            "from_id":   debtor_id,
            "to":        label(creditor_id),
            "to_id":     creditor_id,
            "amount":    amount,
            "display":   f"{label(debtor_id)} → {label(creditor_id)}: ₹{amount}"
        })

        # Reduce balances
        d[i][1] = round(debt   - amount, 2)
        c[j][1] = round(credit - amount, 2)

        # Advance pointer(s) for whoever is fully settled
        if d[i][1] < 0.001:
            i += 1
        if c[j][1] < 0.001:
            j += 1

    return transactions


def explain_algorithm() -> str:
    """
    Return a human-readable explanation of the algorithm for educational use.
    You can expose this as an MCP tool for interview prep!
    """
    return """
    Minimal Debt Settlement — Two-Pointer Greedy Algorithm
    ======================================================

    Given N people with net balances:
      • Positive balance → person is OWED money (creditor)
      • Negative balance → person OWES money   (debtor)

    Steps:
    1. Split into creditors and debtors, sort by absolute amount.
    2. Pair the biggest debtor with the biggest creditor.
    3. Transfer min(debt, credit). Whoever hits 0 is done.
    4. Repeat until all balances are 0.

    Example:
      A owes 100, B owes 50, C is owed 150
      → Debtor list:   [(A, 100), (B, 50)]
      → Creditor list: [(C, 150)]

      Step 1: A→C: 100  (A done, C still needs 50)
      Step 2: B→C: 50   (B done, C done)
      Result: 2 transactions  ✅  (optimal, no middle-man)

    Complexity: O(n log n)
    """.strip()
