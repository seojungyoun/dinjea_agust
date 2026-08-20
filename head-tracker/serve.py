#!/usr/bin/env python3
"""Local HTTPS static server so a phone on the same Wi-Fi can open the app.

Camera access requires a secure context (HTTPS) on any origin other than
localhost, so this generates a self-signed certificate on first run and
serves the current directory over TLS.

Usage:
    python3 serve.py [port]   # default port 8443
"""
import http.server
import os
import socket
import ssl
import subprocess
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8443
DIR = os.path.dirname(os.path.abspath(__file__))
CERT_FILE = os.path.join(DIR, "cert.pem")
KEY_FILE = os.path.join(DIR, "key.pem")


def ensure_cert():
    if os.path.exists(CERT_FILE) and os.path.exists(KEY_FILE):
        return
    print("Generating self-signed certificate (one-time)...")
    subprocess.run(
        [
            "openssl", "req", "-x509", "-newkey", "rsa:2048",
            "-keyout", KEY_FILE, "-out", CERT_FILE,
            "-days", "365", "-nodes", "-subj", "/CN=localhost",
        ],
        check=True,
    )


def local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def main():
    ensure_cert()
    os.chdir(DIR)

    handler = http.server.SimpleHTTPRequestHandler
    httpd = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), handler)

    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(CERT_FILE, KEY_FILE)
    httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)

    ip = local_ip()
    print("=" * 52)
    print(f"  이 컴퓨터(모니터):  https://localhost:{PORT}")
    print(f"  휴대폰(같은 Wi-Fi): https://{ip}:{PORT}")
    print("  처음 접속 시 '고급 > 계속 진행' 등으로 보안 경고를")
    print("  넘겨야 합니다 (자체 서명 인증서라 발생하는 정상 경고).")
    print("=" * 52)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
