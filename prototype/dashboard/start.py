import http.server
import socketserver
import os

PORT = 8001
DIRECTORY = os.getcwd()

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-type")
        self.send_header("Content-Security-Policy", "frame-ancestors *")
        super().end_headers()

handler = CORSRequestHandler
handler.directory = DIRECTORY

with socketserver.TCPServer(("", PORT), handler) as httpd:
    httpd.serve_forever()