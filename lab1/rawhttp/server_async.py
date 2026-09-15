import asyncio
from contextlib import suppress
from itertools import count

from rawhttp.server import RequestParser, arguments, make_response, route


async def handle_client(reader, writer, products, ids):
    request = RequestParser()
    reads = 0
    address = writer.get_extra_info("peername")
    try:
        try:
            while True:
                chunk = await asyncio.wait_for(reader.read(4096), 5)
                reads += 1
                if not chunk:
                    if request.headers is None and not request.buffer:
                        return
                    raise ValueError("Incomplete request")
                complete = request.feed(chunk)
                if request.expect_continue:
                    writer.write(b"HTTP/1.1 100 Continue\r\n\r\n")
                    await writer.drain()
                    request.expect_continue = False
                if complete:
                    break
            status, data, headers = route(request.method, request.path, request.body, products, ids)
            response = make_response(status, data, headers)
        except (ValueError, RecursionError):
            status = 400
            response = make_response(status, {"error": "Bad request"})
        writer.write(response)
        await writer.drain()
        print(
            f"{address[0]}:{address[1]} {request.method} {request.path} {status} reads={reads}",
            flush=True,
        )
    except OSError:
        return
    finally:
        writer.close()
        with suppress(OSError):
            await writer.wait_closed()


async def serve(host, port, backlog=128):
    products = {}
    ids = count(1)
    server = await asyncio.start_server(
        lambda reader, writer: handle_client(reader, writer, products, ids),
        host,
        port,
        backlog=backlog,
    )
    async with server:
        print(f"Listening on {host}:{port}", flush=True)
        await server.serve_forever()


if __name__ == "__main__":
    args = arguments()
    try:
        asyncio.run(serve(args.host, args.port, args.backlog))
    except KeyboardInterrupt:
        print("\nСервер остановлен")
