#!/usr/bin/env python3
import argparse
import functools
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler


class NoCacheHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=8790)
    p.add_argument("--bind", default="0.0.0.0")
    p.add_argument("--dir", default=".")
    args = p.parse_args()

    handler = functools.partial(NoCacheHandler, directory=args.dir)
    server = ThreadingHTTPServer((args.bind, args.port), handler)
    print(f"[chat-lite] serving {args.dir} on http://{args.bind}:{args.port} (no-cache)")
    server.serve_forever()


if __name__ == "__main__":
    main()
