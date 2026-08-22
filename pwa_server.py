"""Serve the local PWA shell while Streamlit runs on port 8501."""

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5500)
    args = parser.parse_args()

    shell_directory = Path(__file__).resolve().parent / "pwa"
    handler = partial(SimpleHTTPRequestHandler, directory=str(shell_directory))
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"Nutri Stacker PWA shell: http://127.0.0.1:{args.port}")
    print(f"Android/LAN URL: http://<computer-ip>:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping PWA shell server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
