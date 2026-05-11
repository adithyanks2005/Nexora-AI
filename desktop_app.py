from __future__ import annotations

import socket
import threading
import time
import webbrowser

import uvicorn

from backend.main import app


HOST = "127.0.0.1"
PORT = 8001


def wait_until_ready(timeout: float = 10.0) -> None:
    start = time.time()
    while time.time() - start < timeout:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.25)
            if sock.connect_ex((HOST, PORT)) == 0:
                return
        time.sleep(0.2)


def run_server() -> None:
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")


def main() -> None:
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    wait_until_ready()
    webbrowser.open(f"http://{HOST}:{PORT}")
    print("Nexora AI is running at http://127.0.0.1:8001")
    print("Close this window to stop the local app.")
    try:
        while thread.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
