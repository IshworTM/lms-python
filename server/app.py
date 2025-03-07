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
            env.globals["member"] = self.is_logged_in()
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

    def is_logged_in(self):
        session_id = self.get_session_id()
        if session_id in sessions:
            return sessions[session_id]
        return None

    def get_session_id(self):
        session = cookie.get("session_id", False)
        if session:
            return session.value
        return False

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

    def send_custom_header(self, code: int, keyword: str, value: str):
        self.send_response(code)
        self.send_header(keyword, value)
        self.end_headers()

    def send_to_page(self, path: str = None):
        if path:
            self.send_response(303)
            self.send_header("Location", str(path))
            self.end_headers()

    def form_data_to_json(self):
        raw = self.rfile.read(int(self.headers["Content-Length"]))
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
        # pdb.set_trace()
        try:
            _server = SMTP(server, port)
            _server.starttls()
            _server.login(server_mail, server_password)
            _server.send_message(data)
            _server.quit()
            return True
        except SMTPException as e:
            _logger.exception("SMTP Error:")
            return False

    def do_POST(self):
        if self.path == "/login":
            data = self.form_data_to_json()
            member = ums.member_login(email=data["email"], password=data["password"])
            if member:
                session_id = self.create_session(member)
                self.set_session_cookie(session_id=session_id)
                self.send_to_page("/")
            else:
                content = f"""
                    <div class="modal fade" tabindex="-1" role="dialog" aria-hidden="true">
                        <div class="modal-dialog" role="document">
                            <div class="modal-content">
                                <div class="modal-header">
                                    <h4 class="modal-title">This site says:</h4>
                                    <button type="button" class="btn btn-light" data-dismiss="modal" data-bs-toggle="modal"
                                        aria-label="Close">&times;</button>
                                </div>
                                <div class="modal-body">
                                    <h6>Are you sure?</h6>
                                </div>
                                <div class="modal-footer">
                                    <button type="button" class="btn btn-secondary" data-dismiss="modal"
                                        data-bs-toggle="modal">Okay</button>
                                </div>
                            </div>
                        </div>
                    </div>
                """
                self.send_custom_header(
                    200,
                )
                self.send_json({"message": "Invalid Credentials"}, 500)

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
            if session_id in sessions:
                del sessions[session_id]
                return self.send_to_page("/")
            else:
                return self.send_json({"message": "No active sessions."})

        elif self.path == "/add_book":
            data = self.form_data_to_json()
            test = bms.add_book(data)
            if test:
                return self.send_to_page("/library")

        elif self.path.startswith("/remove_book"):
            book_id = self.get_id_from_query()
            if book_id:
                try:
                    bms.remove_book(book_id)
                    return self.send_to_page("/library")
                except Exception:
                    return _logger.exception(f"An unexpected error occurred:")
            return _logger.error("That book doesn't exist.")

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
            return _logger.error("That book doesn't exist.")

        elif self.path.startswith("/borrow"):
            book_id = self.get_id_from_query()
            session_id = self.get_session_id()
            member_id = sessions[session_id]["member_id"] or False
            if member_id and book_id:
                try:
                    lms.issue_book(book_id, member_id)
                    updated = bms.update_book_count(book_id, "-")
                    if updated:
                        return self.send_to_page("/loans")
                except ValueError:
                    return _logger.exception("Invalid value provided:")
                except Exception as e:
                    _logger.exception(
                        f"Cannot loan book at this moment, please try again later:",
                    )
                    return self.send_json(
                        {"error": f"Error while loaning a book: {e}"},
                        500,
                    )
            return self.send_to_page("/")

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
                    self.send_error(500, "Error while sending email.")
            else:
                self.send_error(500, "All fields are required.")

    def do_GET(self):
        if self.path.startswith("/static/"):
            file_path = self.path[1:]
            print(file_path)
            if os.path.exists(file_path):
                try:
                    with open(file_path, "rb") as file:
                        mime_type, _ = mime.guess_type(file_path)
                        self.send_custom_header(200, "Content-Type", mime_type)
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
            session_id = self.get_session_id()
            if session_id:
                member = sessions[session_id]
                member_id = member["member_id"]
                total_loans = len(lms.get_all_member_loans(member_id))
                returned_loans = len(lms.get_all_active_member_loans(member_id))
                self.serve_template(
                    "user_profile.html",
                    {
                        "member": member,
                        "total_loans": total_loans,
                        "total_returned": returned_loans,
                    },
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
            user = False
            session_id = self.get_session_id()
            if session_id:
                user = sessions[session_id]
            self.serve_template(
                "books.html",
                {
                    "books": books,
                    "datetime": datetime,
                    "timedelta": timedelta,
                    "user": user,
                },
            )
        elif self.path == "/loans":
            session_id = self.get_session_id()
            if session_id:
                current_session = sessions[session_id]
                role = current_session["role"]
                loans = []
                member_id = None

                if role != "admin":
                    member_id = current_session["member_id"]
                    data = lms.get_all_member_loans(member_id)
                else:
                    data = lms.get_all_loans()

                for loan in data:
                    book = bms.find_book_by_id(loan[1])
                    loans.append(
                        {
                            "id": loan[0],
                            "user_id": member_id or loan[2],
                            "isbn": book[3],
                            "book": book[1],
                            "loan_date": loan[3],
                            "due_date": loan[4],
                            "is_issued": loan[5],
                        }
                    )
                return self.serve_template("loans.html", {"loans": loans, "role": role})
            else:
                self.send_json(
                    {"error": "You must be logged in to perform this action."}, 401
                )
        elif self.path.startswith("/return"):
            loan_id = self.get_id_from_query()
            session_id = self.get_session_id()
            member_id = sessions[session_id]["member_id"] or False
            role = sessions[session_id]["role"] or False
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
