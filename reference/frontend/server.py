#!/usr/bin/env python3
"""
Simple HTTP server for testing the frontend
"""

import http.server
import socketserver
import os

# Change to the frontend directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Create handler with CORS support
class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

# Create server
PORT = 8000
Handler = CORSRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving at http://localhost:{PORT}")
    print("Press Ctrl+C to stop")
    httpd.serve_forever()