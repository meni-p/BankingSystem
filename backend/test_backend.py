"""
CSCI 3060U – Phase #5: Back End Unit Testing
Group 21: Bushrat Zahan, Menhdi Patel, Sevara Omonova, Nabiha Shah

Method 1 (Statement Coverage):  apply_fee(account_number)
Method 2 (Decision + Loop Coverage): apply_all(account_numbers, transactions)
"""

import unittest
from unittest.mock import patch
import io
import sys

from transaction_processor import (
    apply_fee,
    apply_all,
    _apply_withdrawal,
    _apply_deposit,
    _apply_create,
    _apply_delete
)

# ===========================================================================
# Helper
# ===========================================================================

def make_account_number(number="10001", name="Test User", status="A",
                 balance=100.00, total_transactions=0, plan="NP"):
    return {
        "account_number": number,
        "name": name,
        "status": status,
        "balance": balance,
        "total_transactions": total_transactions,
        "plan": plan,
    }


# ===========================================================================
# METHOD 1 – apply_fee
# Coverage type: STATEMENT COVERAGE
#
# Source code decisions / branches
#   D1: account_number["plan"] == "SP"   (True -> fee=0.05 / False -> fee=0.10)
#   D2: account_number["balance"] - fee < 0  (True -> log error & return / False -> deduct)
#
# Statement coverage requires every executable line to be hit at least once.
# Minimum cases:
#   SC-1  NP plan, balance sufficient    -> hits D1-False, D2-False  (fee=0.10 deducted)
#   SC-2  SP plan, balance sufficient    -> hits D1-True,  D2-False  (fee=0.05 deducted)
#   SC-3  Any plan, balance insufficient -> hits D1-*, D2-True (error, no deduction)
# ===========================================================================

class TestApplyFeeStatementCoverage(unittest.TestCase):

    # ------------------------------------------------------------------
    # SC-1: Non-Student Plan, sufficient balance
    # Covers: D1-False branch (NP fee = 0.10), D2-False branch (deduct)
    # ------------------------------------------------------------------
    def test_sc1_np_plan_sufficient_balance(self):
        """SC-1: NP account_number with balance=100.00 should have fee of $0.10 deducted."""
        account_number = make_account_number(balance=100.00, plan="NP")
        apply_fee(account_number)
        self.assertAlmostEqual(account_number["balance"], 99.90)
        self.assertEqual(account_number["total_transactions"], 0)

    # ------------------------------------------------------------------
    # SC-2: Student Plan, sufficient balance
    # Covers: D1-True branch (SP fee = 0.05), D2-False branch (deduct)
    # ------------------------------------------------------------------
    def test_sc2_sp_plan_sufficient_balance(self):
        """SC-2: SP account_number with balance=50.00 should have fee of $0.05 deducted."""
        account_number = make_account_number(balance=50.00, plan="SP")
        apply_fee(account_number)
        self.assertAlmostEqual(account_number["balance"], 49.95)
        self.assertEqual(account_number["total_transactions"], 0)

    # ------------------------------------------------------------------
    # SC-3: Insufficient balance (NP) – error path
    # Covers: D2-True branch (log error, return without deducting)
    # ------------------------------------------------------------------
    def test_sc3_np_plan_insufficient_balance(self):
        """SC-3: NP account_number with balance=0.05 cannot cover $0.10 fee; balance unchanged."""
        account_number = make_account_number(balance=0.05, plan="NP")
        captured = io.StringIO()
        with patch("sys.stdout", captured):
            apply_fee(account_number)
        self.assertAlmostEqual(account_number["balance"], 0.05)   # unchanged
        self.assertEqual(account_number["total_transactions"], 0)  # not incremented
        self.assertIn("ERROR", captured.getvalue())

    # ------------------------------------------------------------------
    # SC-4 (extra): SP plan, balance exactly equals fee -> should succeed
    # ------------------------------------------------------------------
    def test_sc4_sp_plan_balance_equals_fee(self):
        """SC-4: SP account_number with balance exactly $0.05 should reach $0.00 (not negative)."""
        account_number = make_account_number(balance=0.05, plan="SP")
        apply_fee(account_number)
        self.assertAlmostEqual(account_number["balance"], 0.00)
        self.assertEqual(account_number["total_transactions"], 0)

    # ------------------------------------------------------------------
    # SC-5 (extra): SP plan, balance insufficient
    # ------------------------------------------------------------------
    def test_sc5_sp_plan_insufficient_balance(self):
        """SC-5: SP account_number with balance=0.01 cannot cover $0.05 fee; balance unchanged."""
        account_number = make_account_number(balance=0.01, plan="SP")
        captured = io.StringIO()
        with patch("sys.stdout", captured):
            apply_fee(account_number)
        self.assertAlmostEqual(account_number["balance"], 0.01)
        self.assertEqual(account_number["total_transactions"], 0)
        self.assertIn("ERROR", captured.getvalue())


# ===========================================================================
# METHOD 2 – apply_all
# Coverage type: DECISION + LOOP COVERAGE
#
# Decisions in apply_all:
#   D1: code == "00"  (skip end-of-session)
#   D2: code == "01"  (withdrawal)
#   D3: code == "02"  (transfer)
#   D4: code == "03"  (paybill)
#   D5: code == "04"  (deposit)
#   D6: code == "05"  (create)
#   D7: code == "06"  (delete)
#   D8: code == "07"  (disable)
#   D9: code == "08"  (changeplan)
#   D10: else         (unknown code)
#
# Loop coverage requires:
#   L-Zero:  loop body never executes  (empty transaction list)
#   L-Once:  loop body executes exactly once
#   L-Many:  loop body executes more than once
#
# Cases:
#   DL-1   Empty list                 -> L-Zero
#   DL-2   Single "00" record         -> L-Once, D1-True
#   DL-3   Single withdrawal          -> L-Once, D2-True
#   DL-4   Single deposit             -> L-Once, D5-True
#   DL-5   Single create              -> L-Once, D6-True
#   DL-6   Single delete              -> L-Once, D7-True
#   DL-7   Unknown code               -> L-Once, D10-True
#   DL-8   Mixed transactions (many)  -> L-Many
#   DL-9   Withdrawal error case      -> constraint violation (no balance change)
#   DL-10  Duplicate create           -> constraint path
#   DL-11  Transfer                   -> D3-True
#   DL-12  Paybill                    -> D4-True
#   DL-13  Disable                    -> D8-True
#   DL-14  Changeplan                 -> D9-True
# ===========================================================================

class TestApplyAllDecisionLoopCoverage(unittest.TestCase):

    # ------------------------------------------------------------------
    # DL-1: Empty transaction list -> loop body never executes
    # ------------------------------------------------------------------
    def test_dl1_empty_transactions(self):
        """DL-1 (L-Zero): No transactions; account_numbers unchanged."""
        account_numbers = {"10001": make_account_number("10001", balance=200.00)}
        result = apply_all(account_numbers, [])
        self.assertAlmostEqual(result["10001"]["balance"], 200.00)

    # ------------------------------------------------------------------
    # DL-2: Single end-of-session (code 00) -> loop runs once, D1 True, skip
    # ------------------------------------------------------------------
    def test_dl2_single_end_of_session(self):
        """DL-2 (L-Once, D1-True): EOS record skipped; account_numbers unchanged."""
        account_numbers = {"10001": make_account_number("10001", balance=200.00)}
        txns = [{"code": "00", "account_number": "00000", "amount": 0.00}]
        result = apply_all(account_numbers, txns)
        self.assertAlmostEqual(result["10001"]["balance"], 200.00)

    # ------------------------------------------------------------------
    # DL-3: Single withdrawal (code 01) -> loop once, D2-True
    # ------------------------------------------------------------------
    def test_dl3_single_withdrawal(self):
        """DL-3 (L-Once, D2-True): Withdrawal of $50 from $200 account_number -> $150."""
        account_numbers = {"10001": make_account_number("10001", balance=200.00)}
        txns = [{"code": "01", "account_number": "10001", "amount": 50.00}]
        result = apply_all(account_numbers, txns)
        self.assertAlmostEqual(result["10001"]["balance"], 149.90)

    # ------------------------------------------------------------------
    # DL-4: Single deposit (code 04) -> loop once, D3-True
    # ------------------------------------------------------------------
    def test_dl4_single_deposit(self):
        """DL-4 (L-Once, D3-True): Deposit of $75 into $200 account_number -> $275."""
        account_numbers = {"10001": make_account_number("10001", balance=200.00)}
        txns = [{"code": "04", "account_number": "10001", "amount": 75.00}]
        result = apply_all(account_numbers, txns)
        self.assertAlmostEqual(result["10001"]["balance"], 274.90)

    # ------------------------------------------------------------------
    # DL-5: Single create (code 05) -> loop once, D6-True
    # ------------------------------------------------------------------
    def test_dl5_single_create(self):
        """DL-5 (L-Once, D4-True): New account_number 20001 created with $500."""
        account_numbers = {}
        txns = [{"code": "05", "account_number": "20001", "name": "New User",
                 "amount": 500.00, "misc": "SP"}]
        result = apply_all(account_numbers, txns)
        self.assertIn("20001", result)
        self.assertAlmostEqual(result["20001"]["balance"], 500.00)

    # ------------------------------------------------------------------
    # DL-6: Single delete (code 06) -> loop once, D7-True
    # ------------------------------------------------------------------
    def test_dl6_single_delete(self):
        """DL-6 (L-Once, D5-True): account_number 10001 deleted from account_numbers."""
        account_numbers = {"10001": make_account_number("10001")}
        txns = [{"code": "06", "account_number": "10001", "amount": 0.00}]
        result = apply_all(account_numbers, txns)
        self.assertNotIn("10001", result)

    # ------------------------------------------------------------------
    # DL-7: Unknown transaction code -> loop once, D10-True (else branch)
    # ------------------------------------------------------------------
    def test_dl7_unknown_code(self):
        """DL-7 (L-Once, D6-True/else): Unknown code logs error, account_number unchanged."""
        account_numbers = {"10001": make_account_number("10001", balance=100.00)}
        txns = [{"code": "99", "account_number": "10001", "amount": 10.00}]
        captured = io.StringIO()
        with patch("sys.stdout", captured):
            result = apply_all(account_numbers, txns)
        self.assertAlmostEqual(result["10001"]["balance"], 100.00)
        self.assertIn("ERROR", captured.getvalue())

    # ------------------------------------------------------------------
    # DL-8: Multiple mixed transactions -> loop executes many times
    # Covers: L-Many; exercises D1, D2, D5, D7 in sequence
    # ------------------------------------------------------------------
    def test_dl8_multiple_mixed_transactions(self):
        """DL-8 (L-Many): EOS skip, withdrawal, deposit, delete in one pass."""
        account_numbers = {
            "10001": make_account_number("10001", balance=500.00),
            "10002": make_account_number("10002", balance=300.00),
        }
        txns = [
            {"code": "00", "account_number": "00000", "amount": 0.00},  # skip
            {"code": "01", "account_number": "10001", "amount": 100.00},  # withdraw
            {"code": "04", "account_number": "10002", "amount": 200.00},  # deposit
            {"code": "06", "account_number": "10002", "amount": 0.00},    # delete
        ]
        result = apply_all(account_numbers, txns)
        # 10001: 500 - 100 = 400
        self.assertAlmostEqual(result["10001"]["balance"], 399.90)
        # 10002 was deleted
        self.assertNotIn("10002", result)

    # ------------------------------------------------------------------
    # DL-9: Withdrawal causing negative balance -> constraint error, no deduct
    # ------------------------------------------------------------------
    def test_dl9_withdrawal_insufficient_funds(self):
        """DL-9: Withdrawal larger than balance logs error, balance unchanged."""
        account_numbers = {"10001": make_account_number("10001", balance=30.00)}
        txns = [{"code": "01", "account_number": "10001", "amount": 50.00}]
        captured = io.StringIO()
        with patch("sys.stdout", captured):
            result = apply_all(account_numbers, txns)
        self.assertAlmostEqual(result["10001"]["balance"], 30.00)
        self.assertIn("ERROR", captured.getvalue())

    # ------------------------------------------------------------------
    # DL-10: Create duplicate account_number -> constraint error, original unchanged
    # ------------------------------------------------------------------
    def test_dl10_create_duplicate_account_number(self):
        """DL-10: Creating an already-existing account_number logs error, balance unchanged."""
        account_numbers = {"10001": make_account_number("10001", balance=100.00)}
        txns = [{"code": "05", "account_number": "10001", "name": "Dup User",
                 "amount": 999.00, "misc": "NP"}]
        captured = io.StringIO()
        with patch("sys.stdout", captured):
            result = apply_all(account_numbers, txns)
        self.assertAlmostEqual(result["10001"]["balance"], 100.00)  # original unchanged
        self.assertIn("ERROR", captured.getvalue())

    # ------------------------------------------------------------------
    # DL-11: Transfer (code 02)
    # ------------------------------------------------------------------
    def test_dl11_transfer_valid(self):
        """DL-11: Transfer $50 from account 10001 to 10002."""
        account_numbers = {
            "10001": make_account_number("10001", balance=200.00),
            "10002": make_account_number("10002", balance=100.00),
        }
        txns = [{"code": "02", "account_number": "10001", "amount": 50.00, "misc": "10002"}]

        result = apply_all(account_numbers, txns)

        self.assertAlmostEqual(result["10001"]["balance"], 149.90)
        self.assertAlmostEqual(result["10002"]["balance"], 150.00)


    # ------------------------------------------------------------------
    # DL-12: Paybill (code 03)
    # ------------------------------------------------------------------
    def test_dl12_paybill_valid(self):
        """DL-12: Paybill of $40 from account 10001."""
        account_numbers = {
            "10001": make_account_number("10001", balance=100.00),
        }
        txns = [{"code": "03", "account_number": "10001", "amount": 40.00}]

        result = apply_all(account_numbers, txns)

        self.assertAlmostEqual(result["10001"]["balance"], 59.90)


    # ------------------------------------------------------------------
    # DL-13: Disable account (code 07)
    # ------------------------------------------------------------------
    def test_dl13_disable_account(self):
        """DL-13: Disable account 10001."""
        account_numbers = {
            "10001": make_account_number("10001", status="A"),
        }
        txns = [{"code": "07", "account_number": "10001", "amount": 0.00}]

        result = apply_all(account_numbers, txns)

        self.assertEqual(result["10001"]["status"], "D")


    # ------------------------------------------------------------------
    # DL-14: Change plan (code 08)
    # ------------------------------------------------------------------
    def test_dl14_changeplan(self):
        """DL-14: Change account plan from SP to NP."""
        account_numbers = {
            "10001": make_account_number("10001", plan="SP"),
        }
        txns = [{"code": "08", "account_number": "10001", "amount": 0.00}]

        result = apply_all(account_numbers, txns)

        self.assertEqual(result["10001"]["plan"], "NP")



if __name__ == "__main__":
    import traceback

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestApplyFeeStatementCoverage))
    suite.addTests(loader.loadTestsFromTestCase(TestApplyAllDecisionLoopCoverage))

    class VerboseResult(unittest.TextTestResult):
        def addSuccess(self, test):
            super().addSuccess(test)
            print(f"   PASS: {test.shortDescription()}")

        def addFailure(self, test, err):
            super().addFailure(test, err)
            print(f"   FAIL: {test.shortDescription()}")
            print(f"     {err[1]}")

        def addError(self, test, err):
            super().addError(test, err)
            print(f"   ERROR: {test.shortDescription()}")
            print(f"     {err[1]}")

    class VerboseRunner(unittest.TextTestRunner):
        resultclass = VerboseResult

    runner = VerboseRunner(verbosity=0, stream=sys.stdout)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
