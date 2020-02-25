#!/usr/bin/env python3
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import argparse
from socketserver import ThreadingMixIn

name = 'noname'

class ThreadingSimpleServer(ThreadingMixIn, HTTPServer):
    pass

class SlowHandler(BaseHTTPRequestHandler):
    def _slowresponder(self, method):
        parsed_url = urlparse(self.path, 'http', allow_fragments=True)
        message = '\n'.join([
            'name={}'.format(name),
            'path={}'.format(self.path),
            'parsed_scheme={}'.format(parsed_url.scheme),
            'parsed_host={}'.format(parsed_url.netloc),
            'parsed_path={}'.format(parsed_url.path),
            'parsed_params={}'.format(parsed_url.params),
            'parsed_query={}'.format(parsed_url.query),
            'parsed_fragment={}'.format(parsed_url.fragment)
        ])
        message += '\n'
        for key, value in self.headers.items():
            message += 'header={}: {}\n'.format(key, value)

        qs=parse_qs(parsed_url.query)
        sleep=int(qs.get('sleep',[1])[0])

        ua=self.headers.get('user-agent','')
        if "haproxy" not in ua.lower():
            time.sleep(sleep)

        self.send_response(200)
        self.end_headers()
        self.wfile.write(message.encode())
        return

    def do_GET(self):
        return self._slowresponder('GET')

    def do_POST(self):
        return self._slowresponder('POST')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='HTTP echo server.')
    parser.add_argument('--port',
                        '-p',
                        type=int,
                        default=4242)
    parser.add_argument('--name',
                        '-n',
                        type=str,
                        default='HTTP echo server')
    args = parser.parse_args()
    if args.name:
        name = args.name
    print('Serving at port {}'.format(args.port))
    server = ThreadingSimpleServer(('', args.port), SlowHandler)
    server.serve_forever()
