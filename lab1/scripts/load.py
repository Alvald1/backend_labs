import argparse
import asyncio
import json
import math
import statistics
import time
from collections import Counter
from contextlib import suppress


async def read_response(reader, expected):
    head = await reader.readuntil(b"\r\n\r\n")
    lines = head.decode("iso-8859-1").split("\r\n")
    status = int(lines[0].split()[1])
    if status != expected:
        raise ValueError(f"HTTP {status}, expected {expected}")
    headers = dict(line.lower().split(":", 1) for line in lines[1:] if line)
    body = await reader.readexactly(int(headers.get("content-length", "0")))
    if expected == 200 and json.loads(body).get("status") != "ok":
        raise ValueError("Invalid health response")
    if expected == 201 and not isinstance(json.loads(body).get("id"), int):
        raise ValueError("Missing product id")


async def one_request(args):
    started = time.perf_counter()
    writer = None
    try:
        async with asyncio.timeout(args.timeout):
            reader, writer = await asyncio.open_connection(args.host, args.port)
            if args.delay:
                body = b'{"name": "Load product"}'
                writer.write(
                    (
                        f"POST /products HTTP/1.1\r\nHost: {args.host}:{args.port}\r\n"
                        f"Content-Length: {len(body)}\r\n"
                        "Content-Type: application/json\r\nExpect: 100-continue\r\n\r\n"
                    ).encode()
                )
                await writer.drain()
                await read_response(reader, 100)
                await asyncio.sleep(args.delay)
                writer.write(body)
                expected = 201
            else:
                writer.write(
                    f"GET /health HTTP/1.1\r\nHost: {args.host}:{args.port}\r\n\r\n".encode()
                )
                expected = 200
            await writer.drain()
            await read_response(reader, expected)
            return time.perf_counter() - started, None
    except (OSError, ValueError, asyncio.IncompleteReadError, asyncio.LimitOverrunError) as exc:
        return None, type(exc).__name__
    finally:
        if writer is not None:
            writer.close()
            with suppress(OSError):
                await writer.wait_closed()


async def main(args):
    started = time.perf_counter()
    results = await asyncio.gather(*(one_request(args) for _ in range(args.n)))
    elapsed = time.perf_counter() - started
    timings = sorted(duration for duration, error in results if error is None)
    errors = Counter(error for _, error in results if error is not None)
    print(
        json.dumps(
            {
                "n": args.n,
                "delay": args.delay,
                "total_seconds": round(elapsed, 6),
                "median_ms": round(statistics.median(timings) * 1000, 3) if timings else None,
                "p95_ms": round(timings[math.ceil(0.95 * len(timings)) - 1] * 1000, 3)
                if timings
                else None,
                "errors": sum(errors.values()),
                "error_types": dict(errors),
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Одновременные запросы к HTTP-серверу")
    parser.add_argument("n", type=int, help="Число одновременных соединений")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--delay", type=float, default=0)
    args = parser.parse_args()
    if args.n < 1 or args.timeout <= 0 or args.delay < 0:
        parser.error("Нужны N > 0, timeout > 0 и delay >= 0")
    asyncio.run(main(args))
