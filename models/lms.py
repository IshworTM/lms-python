import logging
from database import PsqlDB
from datetime import date, datetime, timedelta
import pdb

_logger = logging.getLogger(__name__)

FINE_PER_DAY = 5


class LibraryManagementSystem:
    def __init__(self):
        self.table = "lms_book_issue"
        self.db = PsqlDB
        self.cur = self.db.conn.cursor()

    def get_all_loans(self):
        cur = self.cur
        cur.execute(f"SELECT * FROM {self.table}")
        return cur.fetchall()

    def get_loan_by_id(self, loan_id: str):
        cur = self.cur
        cur.execute(f"SELECT * FROM {self.table} WHERE id=%s", (loan_id,))
        return cur.fetchone()

    def get_member_loan(self, loan_id: str, member_id: str):
        cur = self.cur
        cur.execute(
            f"SELECT * FROM {self.table} WHERE id=%s AND member_id=%s",
            (loan_id, member_id),
        )
        return cur.fetchone()

    def get_all_member_loans(self, member_id: int):
        cur = self.cur
        cur.execute(f"SELECT * FROM {self.table} WHERE member_id=%s", (member_id,))
        return cur.fetchall()

    def get_all_active_member_returns(self, member_id: int):
        cur = self.cur
        cur.execute(
            f"SELECT * FROM {self.table} WHERE member_id=%s and status = 'returned'",
            (member_id,),
        )
        return cur.fetchall()

    def get_all_returns(self):
        cur = self.cur
        cur.execute(f"SELECT * FROM {self.table} WHERE status = 'returned'")
        return cur.fetchall()

    def get_all_member_returns(self, member_id: int):
        cur = self.cur
        cur.execute(
            f"SELECT * FROM {self.table} WHERE member_id=%s and status = 'returned'",
            (member_id,),
        )
        return cur.fetchall()

    def approve_book_issue(self, loan_id: str):
        cur = self.cur
        loan = self.get_loan_by_id(loan_id)
        if loan and loan[7] == "pending":
            cur.execute(
                f"UPDATE {self.table} SET status='approved' WHERE id=%s", (loan_id,)
            )
            if cur.rowcount > 0:
                return True
            return False

    def validate_multiple_request(self, book_id: str, member_id: str):
        cur = self.cur
        cur.execute(
            f"SELECT * FROM {self.table} WHERE book_id=%s AND member_id=%s AND status='pending'",
            (book_id, member_id),
        )
        return cur.fetchall()

    def validate_existing_borrow(self, book_id: str, member_id: str):
        cur = self.cur
        cur.execute(
            f"SELECT * FROM {self.table} WHERE book_id=%s AND member_id=%s AND status='approved'",
            (book_id, member_id),
        )
        return cur.fetchall()

    def get_all_pending_books(self):
        cur = self.cur
        cur.execute(f"SELECT * FROM {self.table} WHERE status = 'pending'")

    def get_member_pending_books(self, member_id: str):
        cur = self.cur
        cur.execute(
            f"SELECT * FROM {self.table} WHERE status = 'pending' AND member_id=%s",
            (member_id,),
        )
        return cur.fetchall()

    def request_book(self, book_id: str, member_id: str):
        cur = self.cur
        issue_date = date.today().strftime("%Y-%m-%d")
        due_date = (date.today() + timedelta(weeks=1)).strftime("%Y-%m-%d")
        try:
            cur.execute(
                f"INSERT INTO {self.table}(book_id, member_id, issue_date, due_date, status) VALUES(%s,%s,%s,%s,%s)",
                (
                    book_id,
                    member_id,
                    issue_date,
                    due_date,
                    "pending",
                ),
            )
            if cur.rowcount > 0:
                return True
            return False
        except Exception:
            _logger.exception(
                f"Error occurred while issuing the book with id {book_id}:"
            )
            return False

    def return_book(self, loan_id: str, member_id: str = None):
        cur = self.cur
        try:
            result = False
            # fine = 0
            if member_id:
                result = self.get_member_loan(loan_id, member_id)
            else:
                result = self.get_loan_by_id(loan_id)
            if not result:
                _logger.error(
                    f"No loan record found with the id: {loan_id} for member id: {member_id}"
                )
                return False
            book_id = result[1]
            status = result[7]
            if not book_id or status != "approved":
                _logger.error(
                    f"Book with book_id: {book_id} and loan_id: {loan_id} is not currently issued."
                )
                return False
            # if result[5] > result[4]:
            #     overdue_days = (result[5] - result[4]).days
            #     fine = FINE_PER_DAY * overdue_days
            cur.execute(
                f"UPDATE {self.table} SET return_date=CURRENT_DATE, status='returned' WHERE id=%s",
                (loan_id,),
            )
            if not cur.rowcount > 0:
                _logger.error(f"Failed to update loan record with id: {loan_id}")
                return False
            _logger.info(
                f"The book with id: {book_id} and loan id: {loan_id} has been successfully returned."
            )
            return True
        except Exception:
            _logger.exception(
                "An error occured while returning the book, try again later:"
            )
            return False


LmsDAO = LibraryManagementSystem()
