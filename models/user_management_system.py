import logging
from database import PsqlDB
import bcrypt

_logger = logging.getLogger(__name__)


class UserManagementSystem:
    def __init__(self):
        self.db = PsqlDB
        self.cur = self.db.conn.cursor()

    def member_login(self, email, password):
        try:
            cur = self.cur
            cur.execute(
                "SELECT * FROM lms_members WHERE email = %s",
                (email,),
            )
            member = cur.fetchone()
            return (
                member if member and self.check_password(member[3], password) else False
            )
        except Exception:
            _logger.exception(f"An error occurred while logging in:")
            return False

    def register_member(self, username, email, password) -> str:
        try:
            cur = self.cur
            cur.execute("SELECT * FROM lms_members WHERE email = %s", (email,))

            if cur.fetchone():
                return "An user with that email already exists."

            pw_hash = self.hash_password(password)
            cur.execute(
                "INSERT INTO lms_members (name, email, password) VALUES (%s, %s, %s) RETURNING *",
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
        cur.execute("SELECT * FROM lms_members")
        return cur.fetchall()


UserDAO = UserManagementSystem()
