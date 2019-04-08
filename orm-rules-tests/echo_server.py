#!/usr/bin/env python2
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from urlparse import urlparse
import argparse

name = 'noname'

class EchoHTTPServer(BaseHTTPRequestHandler):
    def do_GET(self):
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
        for header in self.headers.headers:
            message += 'header={}\n'.format(header)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(message.encode())

    def do_POST(self):
        message = 'Not implemented'
        self.send_response(500)
        self.end_headers()
        self.wfile.write(message.encode())

Handler = EchoHTTPServer

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='HTTP echo server.')
    parser.add_argument('--port',
                        '-p',
                        type=int,
                        default=7357)
    parser.add_argument('--name',
                        '-n',
                        type=str,
                        default='HTTP echo server')
    args = parser.parse_args()
    if args.name:
        name = args.name
    print('Serving at port {}'.format(args.port))
    server = HTTPServer(('', args.port), Handler)
    server.serve_forever()

