import logging
from database import PsqlDB
import bcrypt

_logger = logging.getLogger(__name__)


class UserManagementSystem:
    def __init__(self):
        self.db = PsqlDB
        self.table = "lms_members"
        self.cur = self.db.conn.cursor()

    def member_login(self, email, password):
        try:
            cur = self.cur
            cur.execute(
                f"SELECT * FROM {self.table} WHERE email = %s",
                (email,),
            )
            member = cur.fetchone()
            return (
                member if member and self.check_password(member[3], password) else False
            )
        except Exception:
            _logger.exception(f"An error occurred while logging in:")
            return False

    def register_member(self, username, email, password) -> bool:
        try:
            cur = self.cur
            cur.execute(f"SELECT * FROM {self.table} WHERE email = %s", (email,))

            if cur.fetchone():
                return "An user with that email already exists."

            pw_hash = self.hash_password(password)
            cur.execute(
                f"INSERT INTO {self.table} (name, email, password) VALUES (%s, %s, %s) RETURNING *",
                (username, email, pw_hash),
            )
            if cur.rowcount > 0:
                _logger.info("Member registered successfully.")
                return True
            _logger.warning("Member registration failed.")
            return False
        except Exception:
            _logger.exception(f"An error occurred while registration:")
            return False

    def hash_password(self, pw):
        salt = bcrypt.gensalt()
        hash_bytes = bcrypt.hashpw(password=pw.encode("utf-8"), salt=salt)
        return hash_bytes.decode("utf-8")

    def check_password(self, stored_hash, pw):
        return bcrypt.checkpw(
            password=pw.encode("utf-8"), hashed_password=stored_hash.encode("utf-8")
        )

    def get_members(self) -> list:
        cur = self.cur
        cur.execute(f"SELECT * FROM {self.table}")
        return cur.fetchall()

    def add_member(self, vals: dict[str, str]):
        if vals:
            username = vals.get("username", "")
            email = vals.get("email", "")
            password = vals.get("password", "")
            register = self.register_member(username, email, password)
            return register

    def update_member(self, member_id: str, vals: dict[str, str]):
        if member_id and vals:
            cur = self.cur
            try:
                cur.execute(
                    f"UPDATE {self.table} SET name=%s, email=%s, type=%s, borrowed_books=%s WHERE id=%s",
                    (
                        vals.get("member_name", ""),
                        vals.get("email", ""),
                        vals.get("type", ""),
                        vals.get("borrowed_books", ""),
                        member_id,
                    ),
                )
                if cur.rowcount > 0:
                    _logger.info(
                        f"Successfully updated the member with ID: {member_id}."
                    )
                    return True
                _logger.error(f"Member update failed for member with ID: {member_id}.")
                return False
            except Exception:
                _logger.exception(
                    f"An error occurred while updating member with ID: {member_id}:"
                )
                return False

    def delete_member(self, member_id: str):
        if member_id:
            cur = self.cur
            try:
                cur.execute(f"DELETE FROM {self.table} WHERE id=%s", (member_id,))
                if cur.rowcount > 0:
                    _logger.info(
                        f"Successfully deleted the member with ID: {member_id}."
                    )
                    return True
                _logger.error(f"Failed to delete member with ID: {member_id}.")
                return False
            except Exception:
                _logger.exception(
                    f"An error occurred while deleting member with ID: {member_id}:"
                )
                return False

    def update_borrow_count(self, operation: str, member_id: str):
        if operation not in ["add", "subtract", "+", "-"]:
            _logger.error(
                "Invalid operation, it must either be 'add' or 'subtract' or their symbols ('+' or '-')"
            )
            raise ValueError(
                "Invalid operation, it must either be 'add' or 'subtract' or their symbols ('+' or '-')"
            )
        operator = "+" if operation in ["add", "+"] else "-"
        cur = self.cur
        try:
            cur.execute(
                f"SELECT borrowed_books FROM {self.table} WHERE id=%s", (member_id,)
            )
            result = cur.fetchone()
            if not result:
                _logger.error(f"Member with the ID: {member_id} doesn't exist.")
                return False
            if operator == "-":
                if result[0] <= 0:
                    _logger.error(
                        f"Cannot perform the operation, member with ID: {member_id} has not borrowed any books."
                    )
                    return False
            cur.execute(
                f"UPDATE lms_members SET borrowed_books = borrowed_books {operator} 1 where id=%s",
                (member_id,),
            )
            if cur.rowcount > 0:
                _logger.info(
                    f"Updated the borrow count of member with ID: {member_id}."
                )
                return True
            _logger.error(
                f"Failed to update the borrow count for the member with ID: {member_id}"
            )
            return False
        except Exception:
            _logger.exception(
                f"An error occurred while updating borrow count of member with ID: {member_id}"
            )
            return False


UserDAO = UserManagementSystem()
