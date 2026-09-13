import argparse
import json
import socket
from contextlib import suppress
from itertools import count

PHRASES = {
    200: "OK",
    201: "Created",
    204: "No Content",
    400: "Bad Request",
    404: "Not Found",
    405: "Method Not Allowed",
}


def make_response(status, data=None, headers=None):
    lines = [f"HTTP/1.1 {status} {PHRASES[status]}", "Connection: close"]
    body = b""
    if status != 204:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        lines.extend(
            ["Content-Type: application/json; charset=utf-8", f"Content-Length: {len(body)}"]
        )
    for name, value in (headers or {}).items():
        lines.append(f"{name}: {value}")
    return ("\r\n".join(lines) + "\r\n\r\n").encode("iso-8859-1") + body


def parse_head(head):
    request_line, *lines = head.decode("iso-8859-1").split("\r\n")
    method, path, version = request_line.split()
    if version not in ("HTTP/1.0", "HTTP/1.1") or not path.startswith("/"):
        raise ValueError("Invalid request line")
    headers = {}
    for line in lines:
        name, value = line.split(":", 1)
        name = name.strip().lower()
        if not name or name in headers:
            raise ValueError("Invalid or duplicate header")
        headers[name] = value.strip()
    if "transfer-encoding" in headers:
        raise ValueError("Only Content-Length is supported")
    length = headers.get("content-length", "0")
    if not length.isascii() or not length.isdecimal():
        raise ValueError("Invalid Content-Length")
    return method, path, int(length)


def route(method, path, body, products, ids):
    path = path.split("?", 1)[0]
    if path == "/health":
        allowed = "GET"
    elif path == "/products":
        allowed = "POST"
    elif (
        path.startswith("/products/")
        and path.removeprefix("/products/").isascii()
        and path.removeprefix("/products/").isdecimal()
    ):
        allowed = "DELETE"
    else:
        return 404, {"error": "Not found"}, {}
    if method != allowed:
        return 405, {"error": "Method not allowed"}, {"Allow": allowed}
    if method == "GET":
        return 200, {"status": "ok", "service": "product-catalog", "version": "0.1.0"}, {}
    if method == "POST":
        product = json.loads(body.decode("utf-8"))
        if not isinstance(product, dict):
            raise ValueError("Expected a JSON object")
        product_id = next(ids)
        product["id"] = product_id
        products[product_id] = product
        return 201, product, {"Location": f"/products/{product_id}"}
    product_id = int(path.removeprefix("/products/"))
    if product_id not in products:
        return 404, {"error": "Product not found"}, {}
    del products[product_id]
    return 204, None, {}


def handle_connection(conn, address, products, ids):
    method, path = "-", "-"
    recv_count = 0
    try:
        raw = b""
        while b"\r\n\r\n" not in raw:
            chunk = conn.recv(4096)
            recv_count += 1
            if not chunk:
                if not raw:
                    return
                raise ValueError("Incomplete headers")
            raw += chunk
        head, _, body = raw.partition(b"\r\n\r\n")
        method, path, length = parse_head(head)
        body = body[:length]
        while len(body) < length:
            chunk = conn.recv(min(4096, length - len(body)))
            recv_count += 1
            if not chunk:
                raise ValueError("Incomplete body")
            body += chunk
        status, data, headers = route(method, path, body, products, ids)
        response = make_response(status, data, headers)
    except (ValueError, RecursionError):
        status = 400
        response = make_response(status, {"error": "Bad request"})
    except OSError:
        return
    # Клиент мог отключиться до отправки ответа.
    with suppress(OSError):
        conn.sendall(response)
    print(f"{address[0]}:{address[1]} {method} {path} {status} recv={recv_count}", flush=True)


def serve(host, port):
    products = {}
    ids = count(1)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen()
        print(f"Listening on {host}:{port}", flush=True)
        while True:
            conn, address = server.accept()
            with conn:
                conn.settimeout(5)
                handle_connection(conn, address, products, ids)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HTTP-сервер каталога товаров")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    try:
        serve(args.host, args.port)
    except KeyboardInterrupt:
        print("\nСервер остановлен")
