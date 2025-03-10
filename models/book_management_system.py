import logging
from database import PsqlDB
import pdb

_logger = logging.getLogger(__name__)


class BookManagementSystem:
    def __init__(self):
        self.table = "lms_books"
        self.db = PsqlDB
        self.cur = self.db.conn.cursor()

    def get_books(self) -> list:
        cur = self.cur
        cur.execute(f"SELECT * FROM {self.table}")
        data = cur.fetchall()
        return data

    def find_book_by_id(self, book_id):
        cur = self.cur
        cur.execute(f"SELECT * FROM {self.table} WHERE id=%s", (book_id,))
        data = cur.fetchone()
        return data

    def add_book(self, vals):
        cur = self.cur
        try:
            cur.execute(
                f"INSERT INTO {self.table}(title, author, isbn, total_copies, available_copies) VALUES (%s, %s, %s, %s, %s) RETURNING *",
                (
                    vals["book_name"],
                    vals["author"],
                    vals["isbn"],
                    vals["total_copies"],
                    vals["available_copies"],
                ),
            )
            new_book = cur.fetchone()
            if new_book:
                return True
            return False
        except Exception as e:
            _logger.exception(
                f"An error occurred while adding the book {vals['book_name']}:"
            )
            return False

    def update_book(self, book_id: str, vals: dict):
        cur = self.cur
        try:
            cur.execute(
                f"UPDATE {self.table} SET title=%s, author=%s, isbn=%s, total_copies=%s, available_copies=%s WHERE id=%s",
                (
                    vals["book_name"],
                    vals["author"],
                    vals["isbn"],
                    vals["total_copies"],
                    vals["available_copies"],
                    book_id,
                ),
            )
            if cur.rowcount > 0:
                return True
            return False
        except Exception as e:
            _logger.exception(
                f"An error occurred while editing the book {vals['book_name']}:"
            )
            return False

    def remove_book(self, book_id: str):
        cur = self.cur
        try:
            cur.execute(f"DELETE FROM {self.table} WHERE id=%s RETURNING *", (book_id,))
            deleted_book = cur.fetchone()
            if deleted_book:
                return True
            return False
        except Exception as e:
            _logger.exception("An error occurred while removing book:")
            return False

    def search_book(self, book_name: str):
        cur = self.cur
        try:
            cur.execute(
                f"SELECT * FROM {self.table} WHERE title ILIKE '%%' || %s || '%%' OR author ILIKE '%%' || %s || '%%'",
                (book_name, book_name),
            )
            data = cur.fetchall()
            return data
        except Exception:
            _logger.exception("An error occurred while searching for book:")
            return []

    def update_book_count(self, book_id: str, method: str):
        if method not in ["add", "subtract", "+", "-"]:
            _logger.error(
                "Invalid operation, it must either be 'add' or 'subtract' or their symbols ('+' or '-')"
            )
            raise ValueError(
                "Invalid operation, it must either be 'add' or 'subtract' or their symbols ('+' or '-')"
            )
        operator = "+" if method in ["add", "+"] else "-"
        cur = self.cur
        try:
            cur.execute(
                f"SELECT available_copies, total_copies FROM {self.table} WHERE id=%s",
                (book_id,),
            )
            result = cur.fetchone()
            if not result:
                _logger.error(f"No book found with the id {book_id}")
                return False
            if operator == "-":
                if result[0] <= 0:
                    _logger.error(
                        f"Cannot perform the operation, book with the id {book_id} is unavailable."
                    )
                    return False
            else:
                if result[0] >= result[1]:
                    _logger.error(
                        f"Cannot perform the operation, book with the id {book_id} cannot be more than the total copies."
                    )
                    return False
            cur.execute(
                f"UPDATE {self.table} SET available_copies = available_copies {operator} 1 WHERE id=%s",
                (book_id,),
            )
            if cur.rowcount > 0:
                _logger.info(f"Updated book count of book with id {book_id}.")
                return True
            _logger.error(f"Book count update failed for book with id {book_id}.")
            return False
        except Exception as e:
            _logger.exception(
                f"An error occurred while updating book count of book id {book_id}:"
            )
            return False


BookDAO = BookManagementSystem()
