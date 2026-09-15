import socket
import threading
from itertools import count

from rawhttp.server import arguments, handle_connection


def handle_client(conn, address, products, ids, lock):
    with conn:
        conn.settimeout(5)
        handle_connection(conn, address, products, ids, lock)


def serve(host, port, backlog=128):
    products = {}
    ids = count(1)
    lock = threading.Lock()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen(backlog)
        print(f"Listening on {host}:{port}", flush=True)
        while True:
            conn, address = server.accept()
            worker = threading.Thread(
                target=handle_client, args=(conn, address, products, ids, lock), daemon=True
            )
            try:
                worker.start()
            except RuntimeError as exc:
                conn.close()
                print(f"Cannot start thread: {exc}", flush=True)


if __name__ == "__main__":
    args = arguments()
    try:
        serve(args.host, args.port, args.backlog)
    except KeyboardInterrupt:
        print("\nСервер остановлен")
