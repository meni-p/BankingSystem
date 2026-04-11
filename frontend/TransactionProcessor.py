"""
TransactionProcessor Module

CLASS: TransactionProcessor
DESCRIPTION:
Handles all banking transactions by:
- Prompting for input
- Validating session and account rules
- Enforcing per-session limits
- Logging successful transactions to TransactionLog

This class does NOT manage session state itself.
It delegates session validation to SessionManager and
account operations to AccountManager.

"""


class TransactionProcessor:
    """
    TransactionProcessor

    Responsible for processing all supported transaction types:

    - Withdrawal
    - Transfer
    - Paybill
    - Deposit
    - Create (admin only)
    - Delete (admin only)
    - Disable (admin only)
    - Changeplan (admin only)
    - Logout

    """

    def __init__(self, session_manager, account_manager, transaction_log, transaction_file="daily_transaction.txt"):
        """
        Initialize TransactionProcessor.

        Args:
            session_manager: SessionManager instance
            account_manager: AccountManager instance
            transaction_log: TransactionLog instance
            transaction_file: Path to output transaction file

        """
        self.session = session_manager
        self.account_manager = account_manager
        self.transaction_log = transaction_log
        self.transaction_file = transaction_file
        self.scanner = input
        self.session_deposits = {}  # tracks deposits made this session

    def process_withdrawal(self):
        """
            Process withdrawal transaction (code 01).

            Validates:
            - User is logged in
            - Account exists and is active
            - Ownership (if standard mode) OR name verification (if admin mode)
            - Positive amount
            - Session withdrawal limit
            - Sufficient funds
        """
        if not self.session.is_logged_in():
            print("ERROR: Must be logged in first")
            return

        if self.session.is_admin():
            name = self.scanner("Enter account holder's name: ").strip()
            if not name:
                print("ERROR: Name cannot be empty")
                return

        acc_num = self.scanner("Enter account number: ").strip()
        account = self.account_manager.get_account(acc_num)

        if not account:
            print("ERROR: Account does not exist")
            return

        if account.status != 'A':
            print("ERROR: Account is disabled")
            return

        if self.session.is_admin():
            if account.holder_name.strip() != name.strip():
                print("ERROR: Account holder name does not match")
                return
        else:
            if not account.is_valid_for(self.session.get_current_user()):
                print("ERROR: Account does not belong to current user")
                return

        try:
            amount = float(self.scanner("Enter amount to withdraw: $"))
            if amount <= 0:
                print("ERROR: Amount must be positive")
                return
        except ValueError:
            print("ERROR: Invalid amount")
            return

        if not self.session.can_withdraw(amount):
            print(f"ERROR: Would exceed ${self.session.withdrawal_limit} session limit")
            return

        deposited = self.session_deposits.get(acc_num, 0)
        available = account.balance - deposited
        if amount > available:
            print("ERROR: Withdrawal limit reached - deposited funds cannot be used this session")
            return

        if account.withdraw(amount):
            self.session.record_withdrawal(amount)
            self.transaction_log.log_withdrawal(acc_num, amount)
            print(f"Withdrawal successful. New balance: ${account.balance:.2f}")
        else:
            print("ERROR: Insufficient funds")


    def process_transfer(self):
        """
        Process transfer transaction (code 02).

        Validates:
        - User is logged in
        - Source and destination accounts exist
        - Accounts are active
        - Ownership (if standard mode) OR name verification (if admin mode)
        - Positive amount
        - Session transfer limit
        - Sufficient funds

        NOTE:
        Transfer logging writes TWO records:
        - One for the source account
        - One for the destination account

        """

        if not self.session.is_logged_in():
            print("ERROR: Must be logged in first")
            return
        
        if self.session.is_admin():
            name = self.scanner("Enter source account holder's name: ").strip()
            if not name:
                print("ERROR: Name cannot be empty")
                return

        from_acc = self.scanner("Enter account number to transfer FROM: ").strip()
        account_from = self.account_manager.get_account(from_acc)

        if not account_from:
            print("ERROR: Source account does not exist")
            return

        if account_from.status != 'A':
            print("ERROR: Source account is disabled")
            return

        if self.session.is_admin():
            if account_from.holder_name.strip() != name.strip():
                print("ERROR: Source account holder name does not match")
                return
        else:
            if not account_from.is_valid_for(self.session.get_current_user()):
                print("ERROR: Source account does not belong to current user")
                return

        to_acc = self.scanner("Enter account number to transfer TO: ").strip()
        account_to = self.account_manager.get_account(to_acc)

        if not account_to:
            print("ERROR: Destination account does not exist")
            return

        if account_to.status != 'A':
            print("ERROR: Destination account is disabled")
            return

        try:
            amount = float(self.scanner("Enter amount to transfer: $"))
            if amount <= 0:
                print("ERROR: Amount must be positive")
                return
        except ValueError:
            print("ERROR: Invalid amount")
            return

        if not self.session.can_transfer(amount):
            print(f"ERROR: Would exceed ${self.session.transfer_limit} session limit")
            return

        if account_from.withdraw(amount):
            account_to.deposit(amount)
            self.session.record_transfer(amount)

            self.transaction_log.log_transfer(from_acc, amount)
            self.transaction_log.log_transfer(to_acc, amount)

            print("Transfer successful.")
            print(f"Source balance: ${account_from.balance:.2f}")
            print(f"Destination balance: ${account_to.balance:.2f}")
        else:
            print("ERROR: Insufficient funds in source account")

    def process_paybill(self):
        """
        Process paybill transaction (code 03).

        Validates:
        - User is logged in
        - Account exists and is active
        - Ownership (if standard mode) OR name verification (if admin mode)
        - Valid company code
        - Positive amount
        - Session paybill limit
        - Sufficient funds

        """

        if not self.session.is_logged_in():
            print("ERROR: Must be logged in first")
            return
        
        if self.session.is_admin():
            name = self.scanner("Enter account holder's name: ").strip()
            if not name:
                print("ERROR: Name cannot be empty")
                return

        valid_companies = {
            "EC": "The Bright Light Electric Company",
            "CQ": "Credit Card Company Q",
            "FI": "Fast Internet, Inc."
        }

        acc_num = self.scanner("Enter account number: ").strip()
        account = self.account_manager.get_account(acc_num)

        if not account:
            print("ERROR: Account does not exist")
            return

        if account.status != 'A':
            print("ERROR: Account is disabled")
            return

        if self.session.is_admin():
            if account.holder_name.strip() != name.strip():
                print("ERROR: Account holder name does not match")
                return
        else:
            if not account.is_valid_for(self.session.get_current_user()):
                print("ERROR: Account does not belong to current user")
                return

        company = self.scanner("Enter company code (EC, CQ, or FI): ").strip().upper()

        if company not in valid_companies:
            print("ERROR: Invalid company. Must be EC, CQ, or FI")
            return

        try:
            amount = float(self.scanner("Enter amount to pay: $"))
            if amount <= 0:
                print("ERROR: Amount must be positive")
                return
        except ValueError:
            print("ERROR: Invalid amount")
            return

        if not self.session.can_pay_bill(amount):
            print(f"ERROR: Would exceed ${self.session.paybill_limit} session limit")
            return

        if account.withdraw(amount):
            self.session.record_pay_bill(amount)
            self.transaction_log.log_paybill(acc_num, amount, company)
            print(f"Payment to {valid_companies[company]} successful.")
            print(f"New balance: ${account.balance:.2f}")
        else:
            print("ERROR: Insufficient funds")

    def process_deposit(self):
        """
        Process deposit transaction (code 04).

        Validates:
        - User is logged in
        - Account exists and is active
        - Positive amount
        - Name verification (if admin mode)

        Note:
        Deposited funds cannot be used for withdrawal in the same session.

        """

        if not self.session.is_logged_in():
            print("ERROR: Must be logged in first")
            return
        
        if self.session.is_admin():
            name = self.scanner("Enter account holder's name: ").strip()
            if not name:
                print("ERROR: Name cannot be empty")
                return

        acc_num = self.scanner("Enter account number: ").strip()
        account = self.account_manager.get_account(acc_num)

        if not account:
            print("ERROR: Account does not exist")
            return

        if account.status != 'A':
            print("ERROR: Account is disabled")
            return

        if self.session.is_admin():
            if account.holder_name.strip() != name.strip():
                print("ERROR: Account holder name does not match")
                return

        try:
            amount = float(self.scanner("Enter amount to deposit: $"))
            if amount <= 0:
                print("ERROR: Amount must be positive")
                return
        except ValueError:
            print("ERROR: Invalid amount")
            return

        account.deposit(amount)
        self.session_deposits[acc_num] = self.session_deposits.get(acc_num, 0) + amount
        self.transaction_log.log_deposit(acc_num, amount)

        print(f"Deposit successful. New balance: ${account.balance:.2f}")
        print("NOTE: Deposited funds are not available for withdrawal in current session.")

    def process_create(self):
        """
        Process account creation (code 05).
        Admin-only transaction.

        """

        if not self.session.is_logged_in():
            print("ERROR: Must be logged in first")
            return

        if not self.session.is_admin():
            print("ERROR: Create account is admin only")
            return

        name = self.scanner("Enter account holder name: ").strip()
        if not name:
            print("ERROR: Name cannot be empty")
            return

        MAX_NAME_LENGTH = 20
        if len(name) > MAX_NAME_LENGTH:
            print(f"ERROR: Name cannot exceed {MAX_NAME_LENGTH} characters")
            return

        try:
            balance = float(self.scanner("Enter initial balance: $"))
            if balance < 0:
                print("ERROR: Balance cannot be negative")
                return
        except ValueError:
            print("ERROR: Invalid amount")
            return

        account_num = self.account_manager.create_account(name, balance)

        if account_num:
            self.transaction_log.log_create(account_num, balance, name)
            print(f"Account created successfully. Account number: {account_num}")
        else:
            print("ERROR: Could not create account")
            

    def process_delete(self):
        """
        Process account deletion (code 06).
        Admin-only transaction.

        """

        if not self.session.is_logged_in():
            print("ERROR: Must be logged in first")
            return

        if not self.session.is_admin():
            print("ERROR: Delete account is admin only")
            return

        name = self.scanner("Enter account holder name: ").strip()
        if not name:
            print("ERROR: Name cannot be empty")
            return
        if len(name) > 20:
            print("ERROR: Name cannot exceed 20 characters")
            return

        acc_num = self.scanner("Enter account number: ").strip()

        account = self.account_manager.get_account(acc_num)
        if not account:
            print("ERROR: Account does not exist")
            return

        if account.holder_name.strip() != name.strip():
            print("ERROR: Account holder name does not match")
            return

        self.account_manager.delete_account(acc_num)
        self.transaction_log.log_delete(acc_num)

        print(f"Account {acc_num} deleted successfully.")

    def process_disable(self):
        """
        Process account disable (code 07).
        Admin-only transaction.
        """

        if not self.session.is_logged_in():
            print("ERROR: Must be logged in first")
            return

        if not self.session.is_admin():
            print("ERROR: Disable account is admin only")
            return

        name = self.scanner("Enter account holder name: ").strip()
        if not name:
            print("ERROR: Name cannot be empty")
            return
        if len(name) > 20:
            print("ERROR: Name cannot exceed 20 characters")
            return

        acc_num = self.scanner("Enter account number: ").strip()

        account = self.account_manager.get_account(acc_num)
        if not account:
            print("ERROR: Account does not exist")
            return

        if account.holder_name.strip() != name.strip():
            print("ERROR: Account holder name does not match")
            return

        self.account_manager.disable_account(acc_num)
        self.transaction_log.log_disable(acc_num)

        print(f"Account {acc_num} disabled successfully.")


    def process_change_plan(self):
        """
        Process change plan (code 08).
        Admin-only transaction.

        """

        if not self.session.is_logged_in():
            print("ERROR: Must be logged in first")
            return

        if not self.session.is_admin():
            print("ERROR: Change plan is admin only")
            return

        name = self.scanner("Enter account holder name: ").strip()
        if not name:
            print("ERROR: Name cannot be empty")
            return
        if len(name) > 20:
            print("ERROR: Name cannot exceed 20 characters")
            return

        acc_num = self.scanner("Enter account number: ").strip()

        account = self.account_manager.get_account(acc_num)
        if not account:
            print("ERROR: Account does not exist")
            return

        if account.holder_name.strip() != name.strip():
            print("ERROR: Account holder name does not match")
            return

        if account.plan != 'SP':
            print("ERROR: Account is not on student plan")
            return

        self.account_manager.change_plan(acc_num)
        self.transaction_log.log_change_plan(acc_num)

        print(f"Account {acc_num} plan changed from SP to NP successfully.")


    def process_logout(self):
        """
        Process logout (code 00).

        - Writes transaction file
        - Ends session

        """

        if not self.session.is_logged_in():
            print("ERROR: Not logged in")
            return

        self.transaction_log.write_to_file(self.transaction_file)
        self.session.logout()
        self.session_deposits = {}

        print(f"Session ended. Transactions written to {self.transaction_file}")
        print("Goodbye!")