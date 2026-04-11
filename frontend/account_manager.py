"""
Account Manager Module

CLASS: AccountManager
DESCRIPTION: Holds in-memory list of accounts, provides lookup by account number,
and applies account changes.

"""

from bank_account import BankAccount


class AccountManager:
    """
    AccountManager

    Stores all accounts in memory and provides operations to
    load, lookup, and modify accounts during a front end session.
    """

    def __init__(self):
        """Initialize storage for accounts and deleted accounts."""
        self.accounts = {}            
        self.deleted_set = set()      

    def load_from_file(self, filename):
        """
        Reads Current Bank Accounts file (37-char format) and populates accounts dictionary.

        Format:
        NNNNN AAAAAAAAAAAAAAAAAAAA S PPPPPPPP

        Stops when holder name is END_OF_FILE.
        """
        self.accounts.clear()
        self.deleted_set.clear()

        with open(filename, "r") as file:
            for line in file:
                line = line.rstrip("\n")

        
                if len(line) < 37: #for handling bad input to avoid crash
                    continue

                account_number = line[0:5]
                holder_name = line[6:26].strip()
                status = line[27:28]
                balance_str = line[29:37].strip()

                if holder_name == "END_OF_FILE":
                    break

                if not account_number.isdigit():
                    continue

                if status not in ["A", "D"]:
                    status = "A"

                try:
                    balance = float(balance_str)
                except ValueError:
                    continue

                
                self.accounts[account_number] = BankAccount(
                    account_number=account_number,
                    holder_name=holder_name,
                    balance=balance,
                    status=status,
                    plan="NP"
                )

    def user_exists(self, user_name):
        """
        Check if a user exists in any account.
        
        """
        for acc_num, account in self.accounts.items():
            if account.holder_name.strip().lower() == user_name.strip().lower():
                return True
        return False

    def get_account(self, account_number):
        """
        Returns BankAccount object for given account number, or None if not found.
        """
        normalized_number = str(account_number).strip().zfill(5)

        if normalized_number in self.deleted_set:
            return None

        return self.accounts.get(normalized_number)

    def create_account(self, holder_name, balance):
        """
        Generates new unique account number, creates BankAccount with status A and plan SP,
        adds to accounts dictionary.

        Returns the new account number.
        """
        holder_name = str(holder_name).strip()[:20]

        try:
            balance = float(balance)
        except ValueError:
            balance = 0.0

        
        balance = max(0.0, min(balance, 99999.99))

        new_number = self._generate_unique_account_number()

        self.accounts[new_number] = BankAccount(
            account_number=new_number,
            holder_name=holder_name,
            balance=balance,
            status="A",
            plan="SP"
        )

        return new_number

    def delete_account(self, account_number):
        """
        Marks account as deleted by adding to deleted set.
        Returns True if account existed, else False.
        """
        normalized_number = str(account_number).strip().zfill(5)

        if normalized_number in self.accounts:
            self.deleted_set.add(normalized_number)
            return True

        return False

    def disable_account(self, account_number):
        """
        Retrieves account and sets its status to disabled (D).
        Returns True if successful, else False.
        """
        account = self.get_account(account_number)
        if account is None:
            return False

        account.set_status("D")
        return True

    def change_plan(self, account_number):
        """
        Retrieves account and changes plan from SP to NP (no reverse).
        Returns True if successful, else False.
        """
        account = self.get_account(account_number)
        if account is None:
            return False

        if account.get_plan() == "SP":
            account.set_plan("NP")
            return True

        return False

    def _generate_unique_account_number(self):
        """
        Helper: generate a unique 5-digit account number not already in use.
        """
        for i in range(100000):
            candidate = str(i).zfill(5)
            if candidate not in self.accounts and candidate not in self.deleted_set:
                return candidate

        raise RuntimeError("No available account numbers remaining.")