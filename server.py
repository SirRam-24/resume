import http.server
import socketserver
import urllib.request
import urllib.error
import json
import os

DB_FILE = 'database.json'

class ProxyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, DELETE, PUT')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        if self.path == '/api/students':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            if os.path.exists(DB_FILE):
                with open(DB_FILE, 'r') as f:
                    self.wfile.write(f.read().encode())
            else:
                self.wfile.write(b'[]')
        else:
            # Serve regular static files
            super().do_GET()

    def do_POST(self):
        if self.path == '/api/students':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            with open(DB_FILE, 'wb') as f:
                f.write(post_data)
                
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode())

        elif self.path == '/api/chat':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            req = urllib.request.Request('https://integrate.api.nvidia.com/v1/chat/completions', data=post_data, headers={
                'Content-Type': 'application/json',
                'Authorization': self.headers.get('Authorization', '')
            })
            
            try:
                response = urllib.request.urlopen(req)
                self.send_response(response.status)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(response.read())
            except urllib.error.HTTPError as e:
                self.send_response(e.code)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(e.read())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(str(e).encode('utf-8'))
        else:
            self.send_error(404)

PORT = 8000
with socketserver.TCPServer(("", PORT), ProxyHTTPRequestHandler) as httpd:
    print(f"HAPIS Proxy Server running at http://localhost:{PORT}")
    httpd.serve_forever()
