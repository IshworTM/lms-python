import logging
from smtplib import SMTP, SMTPException
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import http.server as httpserver
from http.cookies import SimpleCookie as CookieBaker
import json, pdb, uuid, os, mimetypes as mime
import urllib.parse as parse
from jinja2 import Environment, PackageLoader, select_autoescape
from models import BookDAO as bms, UserDAO as ums, LmsDAO as lms
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv(".env")

sessions = {}
cookie = CookieBaker()

env = Environment(
    loader=PackageLoader(package_name="project_lms", package_path="templates")
)
_logger = logging.getLogger(__name__)


class LMSHandler(httpserver.SimpleHTTPRequestHandler):
    def serve_template(self, template_name: str, context=None):
        if context is None:
            context = {}
        try:
            env.globals["member"] = self.get_session()
            template = env.get_template(template_name)
            content = template.render(context)
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content.encode("UTF-8"))
        except Exception as e:
            _logger.exception(f"An exception occured:")
            return self.send_error(
                500, f"An error occurred while serving the template: {e}"
            )

    def send_html(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def send_json(self, data, code: int = None, headers=None):
        self.send_response(code or 200)
        self.send_header("Content-type", "application/json")
        if headers:
            for keyword, value in headers.items():
                self.send_header(keyword, value)
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def send_custom_header(self, code: int, headers: dict[str, str]):
        self.send_response(code)
        if headers:
            for keyword, value in headers.items():
                self.send_header(keyword, value)
        self.end_headers()

    def send_to_page(self, path: str = None):
        if path:
            self.send_response(303)
            self.send_header("Location", str(path))
            self.end_headers()

    def form_data_to_json(self):
        raw = self.rfile.read(int(self.headers["Content-Length"]))
        if self.headers.get("Content-Type") == "application/json":
            return json.loads(raw.decode("UTF-8"))
        parsed_data = parse.parse_qs(raw.decode("utf-8"))
        data = {key: value[0] for key, value in parsed_data.items()}
        return data

    def create_session(self, member):
        session_id = str(uuid.uuid4())
        sessions[session_id] = {
            "member_id": member[0],
            "username": member[1],
            "email": member[2],
            "role": member[4],
        }
        return session_id

    def get_session_id(self):
        session_id = cookie.get("session_id", False)
        return session_id.value if session_id else False

    def get_session(self):
        session_id = self.get_session_id()
        return sessions.get(session_id, False)

    def set_session_cookie(self, session_id):
        cookie["session_id"] = session_id
        cookie["session_id"]["max-age"] = 3600

    def parse_path_query(self):
        query = parse.urlparse(self.path).query
        return parse.parse_qs(query)

    def get_id_from_query(self):
        vals = self.parse_path_query()
        return vals.get("id", [None])[0]

    def send_email(self, name, email, msg):
        server = "smtp.gmail.com"
        port = 587
        server_mail = os.getenv("EMAIL_NAME")
        server_password = os.getenv("PASSWORD")

        data = MIMEMultipart()
        data["From"] = server_mail
        data["To"] = os.getenv("MAIL")
        data["Subject"] = f"New Contact Message from {name}"

        body = f"Name: {name}\nEmail: {email}\nMessage:\n{msg}"
        data.attach(MIMEText(body, "plain"))
        try:
            _server = SMTP(server, port)
            _server.starttls()
            _server.login(server_mail, server_password)
            _server.send_message(data)
            _server.quit()
            return True
        except SMTPException as e:
            _logger.exception("SMTP Error:")
            self.send_json(
                {"error": f"Internal Server Error: {e}"},
                500,
            )
            return False

    def do_POST(self):
        if self.path == "/login":
            data = self.form_data_to_json()
            member = ums.member_login(email=data["email"], password=data["password"])
            if member:
                session_id = self.create_session(member)
                self.set_session_cookie(session_id=session_id)
                self.send_json({"success": "Login Successful"}, 200)
            else:
                fetch_mode = self.headers.get("Sec-Fetch-Mode")
                if fetch_mode == "cors":
                    self.send_json({"error": "Invalid Credentials"}, 401)
                else:
                    self.send_to_page("/")

        elif self.path == "/signup":
            data = self.form_data_to_json()
            ums.register_member(
                username=data["username"],
                email=data["email"],
                password=data["password"],
            )
            self.send_to_page("/")

        elif self.path == "/logout":
            session_id = self.get_session_id()
            session = sessions.get(session_id, False)
            if session:
                del sessions[session_id]
                return self.send_to_page("/")
            else:
                return self.send_json({"message": "No active sessions."})

        elif self.path == "/add_book":
            data = self.form_data_to_json()
            if data:
                try:
                    bms.add_book(data)
                    return self.send_to_page("/library")
                except Exception:
                    _logger.exception(f"Error while adding a book:")
                    self.send_json(f"Error while adding a book: {e}", 500)

        elif self.path.startswith("/remove_book"):
            book_id = self.get_id_from_query()
            if book_id:
                try:
                    bms.remove_book(book_id)
                    return self.send_to_page("/library")
                except Exception:
                    return _logger.exception(f"An unexpected error occurred:")
            _logger.warning(
                "Tried to delete book directly from the URL, redirecting to root page..."
            )
            return self.send_to_page("/")

        elif self.path.startswith("/edit_book"):
            book_id = self.get_id_from_query()
            if book_id:
                try:
                    data = self.form_data_to_json()
                    bms.update_book(book_id, data)
                    return self.send_to_page("/library")
                except Exception as e:
                    _logger.exception(f"An unexpected error occurred:")
                    return self.send_json(
                        {"error": f"Internal Server Error: {e}"},
                        500,
                    )
            _logger.warning(
                "Tried to edit book directly from the URL, redirecting to root page..."
            )
            return self.send_to_page("/")

        elif self.path.startswith("/request"):
            book_id = self.get_id_from_query()
            session = self.get_session()
            if session:
                member_id = session["member_id"]
                if member_id and book_id:
                    try:
                        request_multiple = lms.validate_multiple_request(
                            book_id, member_id
                        )
                        if request_multiple:
                            return self.send_json(
                                {"error": "You can only request one book at a time"},
                                400,
                            )
                        already_borrowed = lms.validate_existing_borrow(
                            book_id, member_id
                        )
                        if already_borrowed:
                            return self.send_json(
                                {"error": "You have already borrowed this book"},
                                400,
                            )
                        lms.request_book(book_id, member_id)
                        return self.send_to_page("/loans")
                    except Exception as e:
                        _logger.exception(
                            f"Cannot request book at this moment, please try again later:",
                        )
                        return self.send_json(
                            {"error": f"Error while requesting a book borrow: {e}"},
                            500,
                        )

        elif self.path.startswith("/approve"):
            loan_id = self.get_id_from_query()
            session = self.get_session()
            if session:
                role = session["role"]
                if role == "admin" and loan_id:
                    try:
                        loan = lms.get_loan_by_id(loan_id)
                        if loan and loan[5] == "pending":
                            lms.approve_book_issue(loan_id)
                            bms.update_book_count(loan[1], "-")
                            ums.update_borrow_count("+", loan[2])
                            return self.send_to_page("/loans")
                    except ValueError:
                        _logger.exception("Invalid value provided:")
                        return self.send_json({"error": "Invalid Value Provided."}, 400)
                    except Exception as e:
                        _logger.exception(
                            f"Cannot approve book at this moment, please try again later:",
                        )
                        return self.send_json(
                            {"error": f"Error while approving a book: {e}"},
                            500,
                        )
            return self.send_json({"error": "Unauthorized"}, 403)

        elif self.path.startswith("/search"):
            data = self.form_data_to_json()
            book_name = data.get("bookName", "").lower()
            results = bms.search_book(book_name)
            self.serve_template(
                "search.html",
                {
                    "results": results,
                    "item": book_name,
                    "datetime": datetime,
                    "timedelta": timedelta,
                },
            )
        elif self.path == "/send_message":
            data = self.form_data_to_json()
            name = data.get("contactName", "")
            email = data.get("contactEmail", "")
            message = data.get("contactMessage", "")
            if name and email and message:
                sent = self.send_email(name, email, message)
                if sent:
                    self.send_to_page("/thank_you")
                else:
                    self.send_json(f"Error while sending email: {e}", 500)
            else:
                self.send_json("All fields are required.", 400)

        elif self.path == "/add_member":
            data = self.form_data_to_json()
            if data:
                try:
                    ums.add_member(data)
                    self.send_to_page("/members")
                except Exception:
                    _logger.exception("Error while adding new member:", stack_info=True)
                    self.send_json(
                        f"An error occurred while adding new member: {e}", 500
                    )

        elif self.path.startswith("/edit_member"):
            session = self.get_session()
            role = session.get("role", "")
            if role == "admin":
                member_id = self.get_id_from_query()
                if member_id:
                    data = self.form_data_to_json()
                    try:
                        ums.update_member(member_id, data)
                        return self.send_to_page("/members")
                    except Exception:
                        _logger.exception(
                            "An error occurred while editing member:", stack_info=True
                        )
                        return self.send_json(
                            f"An error occurred while editing this member: {e}", 500
                        )
            _logger.warning(
                f"Tried to edit member directly from the URL, redirecting to home."
            )
            return self.send_to_page("/")

        elif self.path.startswith("/delete_member"):
            session = self.get_session()
            role = session.get("role", "")
            if role == "admin":
                member_id = self.get_id_from_query()
                if member_id:
                    try:
                        ums.delete_member(member_id)
                        return self.send_to_page("/members")
                    except Exception:
                        _logger.exception(
                            f"An error occurred while deleting the member with ID: {member_id}"
                        )
                        return self.send_json(
                            f"An error occurred while deleting the member with ID: {member_id}",
                            500,
                        )
                _logger.warning(
                    f"Attempted to delete member from a forbidden method.",
                    stack_info=True,
                )
            return self.send_to_page("/")

    def do_GET(self):
        if self.path.startswith("/static/"):
            file_path = self.path[1:]
            print(f"Attempting to serve file: {file_path}")
            if os.path.exists(file_path):
                try:
                    with open(file_path, "rb") as file:
                        mime_type, _ = mime.guess_type(file_path)
                        self.send_custom_header(200, {"Content-Type": mime_type})
                        self.wfile.write(file.read())
                except Exception as e:
                    _logger.exception(
                        "Internal Server Error while serving static files:"
                    )
                    return self.send_json(
                        {"error": f"Internal Server Error: {e}"},
                        500,
                    )
            else:
                return _logger.error(f"File not found: {file_path}")
        if self.path == "/":
            self.serve_template("index.html")
        elif self.path == "/profile":
            session = self.get_session()
            if session:
                member_id = session.get("member_id")
                total_loans = len(lms.get_all_member_loans(member_id))
                returned_loans = len(lms.get_all_active_member_returns(member_id))
                return self.serve_template(
                    "user_profile.html",
                    {
                        "total_loans": total_loans,
                        "total_returned": returned_loans,
                    },
                )
            _logger.warning(
                f"Attempted to access profile directly from URL or without logging in."
            )
            return self.send_to_page("/")
        elif self.path == "/about_us":
            self.serve_template("about_us.html")
        elif self.path == "/contact_us":
            self.serve_template("contact_us.html")
        elif self.path == "/thank_you":
            self.serve_template("thank_you.html")
        elif self.path == "/library":
            books = bms.get_books()
            return self.serve_template(
                "books.html",
                {
                    "books": books,
                    "datetime": datetime,
                    "timedelta": timedelta,
                },
            )
        elif self.path == "/members":
            members = ums.get_members()
            session = self.get_session()
            role = session["role"] if session else None
            if role == "admin":
                ctx = []
                for member in members:
                    ctx.append(
                        {
                            "id": member[0],
                            "name": member[1],
                            "email": member[2],
                            "type": member[4],
                            "borrowed_books": member[5],
                        }
                    )
                return self.serve_template("users.html", {"members": ctx})
            return self.send_to_page("/")
        elif self.path == "/loans":
            session = self.get_session()
            if session:
                role = session.get("role", "")
                loans = []
                member_id = None
                if role != "admin":
                    member_id = session.get("member_id", False)
                    data = lms.get_all_member_loans(member_id)
                else:
                    data = lms.get_all_loans()

                for loan in data:
                    if loan[5] != "returned":
                        book = bms.find_book_by_id(loan[1])
                        loans.append(
                            {
                                "id": loan[0],
                                "user_id": member_id or loan[2],
                                "isbn": book[3],
                                "book": book[1],
                                "loan_date": loan[3],
                                "return_date": loan[4],
                                "status": loan[5],
                            }
                        )
                return self.serve_template("loans.html", {"loans": loans, "role": role})
            else:
                fetch_mode = self.headers.get("Sec-Fetch-Mode")
                if fetch_mode == "cors":
                    self.send_json(
                        {"error": "You must be logged in to perform this action."}, 401
                    )
                else:
                    _logger.warning(
                        "Attempted to access loans directly from URL navigation, redirecting to homepage.",
                    )
                    return self.send_to_page("/")
        elif self.path == "/returns":
            session = self.get_session()
            if session:
                role = session.get("role", "")
                returns = []
                member_id = None
                if role != "admin":
                    member_id = session.get("member_id", False)
                    data = lms.get_all_member_returns(member_id)
                else:
                    data = lms.get_all_returns()

                for returned_book in data:
                    if returned_book[5] == "returned":
                        book = bms.find_book_by_id(returned_book[1])
                        returns.append(
                            {
                                "id": returned_book[0],
                                "user_id": member_id or returned_book[2],
                                "isbn": book[3],
                                "book": book[1],
                                "loan_date": returned_book[3],
                                "return_date": returned_book[4],
                                "status": returned_book[5],
                            }
                        )
                return self.serve_template(
                    "returns.html",
                    {"returns": returns},
                )
            else:
                fetch_mode = self.headers.get("Sec-Fetch-Mode")
                if fetch_mode == "cors":
                    self.send_json(
                        {"error": "You must be logged in to perform this action."}, 401
                    )
                else:
                    _logger.warning(
                        "Attempted to access loans directly from URL navigation, redirecting to homepage.",
                    )
                    return self.send_to_page("/")
        elif self.path.startswith("/return"):
            loan_id = self.get_id_from_query()
            session = self.get_session()
            member_id = session.get("member_id", False)
            role = session.get("role", "")
            if member_id and loan_id:
                try:
                    loan_data = lms.get_loan_by_id(loan_id)
                    if not loan_data:
                        _logger.error(f"No loan record with the ID: {loan_id}.")
                        return self.send_error(404, "Loan record not found.")
                    if role != "admin" and loan_data[2] != member_id:
                        _logger.error(
                            f"Member ID: {member_id} attempted to return a book which was not borrowed by them."
                        )
                        return self.send_json(
                            {
                                "error": "You can only return books that you have borrowed!"
                            },
                            403,
                        )
                    returned = lms.return_book(
                        loan_id, member_id if role != "admin" else None
                    )
                    book_id = loan_data[1]
                    if returned:
                        updated = bms.update_book_count(book_id, "+")
                        if updated:
                            ums.update_borrow_count("-", loan_data[2])
                            _logger.info("Book successfully returned!")
                            return self.send_to_page("/loans")
                        _logger.error(f"Failed to update inventory for book {book_id}")
                        return self.send_json(
                            {"error": "Failed to update inventory."}, 500
                        )
                    _logger.error(
                        f"Book return failed for book with id: {book_id} and loan id: {loan_id}."
                    )
                    return self.send_json(
                        {"error": "Failed to process book return. Please try again!"},
                        500,
                    )
                except Exception as e:
                    _logger.exception(
                        f"Cannot return this book at this moment, please try again later:",
                    )
                    return self.send_json(
                        {
                            "error": f"An error occurred while processing the return: {e}"
                        },
                        500,
                    )
