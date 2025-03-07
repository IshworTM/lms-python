from app import LMSHandler, httpserver
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(process)d %(levelname)s %(name)s: %(message)s",
)


def run(port=8090):
    live = httpserver.HTTPServer(("localhost", port), LMSHandler)
    print(f"Server running on: http://localhost:{port}")
    live.serve_forever()


if __name__ == "__main__":
    run()
