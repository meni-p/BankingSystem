"""
TransactionLog Module

CLASS: TransactionLog
DESCRIPTION:
Builds and stores 40-character fixed-format transaction records
and writes them to the daily transaction file at logout.

Transaction Record Format (Fixed Width):
CC (2) +
AAAAAAAAAAAAAAAAAAAA (20) +
NNNNN (5) +
PPPPPPPP (8) +
MM (2)
Total: 40 characters per line (including padding)

"""


class TransactionLog:
    """
    TransactionLog

    Responsible for:
    - Formatting all transaction records
    - Enforcing 40-character fixed-width format
    - Storing transactions in memory during session
    - Writing transactions to file on logout

    """

    RECORD_LEN = 40  
    def __init__(self):
        """
        Initialize a new TransactionLog.

        Creates an empty list to store formatted transaction records
        during the current session.

        """
        self.transactions = []

    def _build_record(self, code, name, account_number, amount, misc):
        """
        Build a properly formatted 40-character transaction record.

        Args:
            code (str): 2-character transaction code
            name (str): Account holder name (max 20 chars)
            account_number (str/int): 5-digit account number
            amount (float): Transaction amount
            misc (str): 2-character miscellaneous field

        Returns:
            str: 40-character formatted transaction record

        """
        code = (code or "").ljust(2)[:2]
        name = (name or "").ljust(20)[:20]
        acc = self._format_account(account_number)   
        amt = self._format_amount(amount)            
        misc = (misc or "").ljust(2)[:2]             

        record = f"{code}{name}{acc}{amt}{misc}"

        return record.ljust(self.RECORD_LEN)[:self.RECORD_LEN]

    def log_withdrawal(self, account_number, amount):
        """
        Record withdrawal transaction (code 01).

        Args:
            account_number (str): Account number
            amount (float): Amount withdrawn

        """
        record = self._build_record("01", "", account_number, amount, "")
        self.transactions.append(record)

    def log_transfer(self, account_number, amount):
        """
        Record transfer transaction (code 02).

        Logs one record for the account involved.

        Args:
            account_number (str): Account involved in transfer
            amount (float): Amount transferred

        """
        record = self._build_record("02", "", account_number, amount, "")
        self.transactions.append(record)

    def log_paybill(self, account_number, amount, company_code):
        """
        Record paybill transaction (code 03).

        Args:
            account_number (str): Account paying the bill
            amount (float): Amount paid
            company_code (str): Company code (EC, CQ, FI)

        """
        record = self._build_record("03", "", account_number, amount, company_code)
        self.transactions.append(record)

    def log_deposit(self, account_number, amount):
        """
        Record deposit transaction (code 04).

        Args:
            account_number (str): Account receiving deposit
            amount (float): Amount deposited

        """
        record = self._build_record("04", "", account_number, amount, "")
        self.transactions.append(record)

    def log_create(self, account_number, amount, name=""):
        """
        Record account creation transaction (code 05).

        Args:
            account_number (str): New account number
            amount (float): Initial balance

        """
        record = self._build_record("05", name, account_number, amount, "SP")
        self.transactions.append(record)

    def log_delete(self, account_number):
        """
        Record account deletion transaction (code 06).

        Args:
            account_number (str): Account being deleted

        """
        record = self._build_record("06", "", account_number, 0.0, "")
        self.transactions.append(record)

    def log_disable(self, account_number):
        """
        Record account disable transaction (code 07).

        Args:
            account_number (str): Account being disabled

        """
        record = self._build_record("07", "", account_number, 0.0, "")
        self.transactions.append(record)

    def log_change_plan(self, account_number):
        """
        Record change plan transaction (code 08).

        Args:
            account_number (str): Account changing from SP to NP

        """
        record = self._build_record("08", "", account_number, 0.0, "NP")
        self.transactions.append(record)

    def write_to_file(self, filename):
        """
        Write all stored transactions to file and append end-of-session marker.

        Args:
            filename (str): Output file name

        """
        try:
            with open(filename, "w") as file:

                for transaction in self.transactions:
                    file.write(transaction + "\n")

                end_marker = "00".ljust(self.RECORD_LEN)[:self.RECORD_LEN]
                file.write(end_marker + "\n")

            print(f"Successfully wrote {len(self.transactions)} transactions to {filename}")

        except Exception as e:
            print(f"ERROR: Could not write to file {filename}: {e}")

    def get_transaction_count(self):
        """
        Return number of transactions logged in the current session.

        Returns:
            int: Number of transactions

        """
        return len(self.transactions)

    def _format_account(self, account_number):
        """
        Format account number as 5-digit zero-filled string.

        Args:
            account_number (str/int): Raw account number

        Returns:
            str: 5-digit zero-filled account number

        """
        if isinstance(account_number, str):
            digits = "".join(filter(str.isdigit, account_number))
            num = int(digits) if digits else 0
        else:
            num = int(account_number)

        return f"{num:05d}"

    def _format_amount(self, amount):
        """
        Format amount as 8-character string with two decimal places.

        Example:
            110 → "00110.00"

        Args:
            amount (float/int): Dollar amount

        Returns:
            str: 8-character formatted amount
            
        """
        amt_float = float(amount)
        dollars = int(amt_float)
        cents = int(round((amt_float - dollars) * 100))

        if cents >= 100:
            dollars += 1
            cents -= 100

        return f"{dollars:05d}.{cents:02d}"