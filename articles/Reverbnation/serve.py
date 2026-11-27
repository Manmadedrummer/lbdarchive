#!/usr/bin/env python3
"""Optional: run this to view the site at http://localhost:8000
YouTube only allows its video player on pages served over http(s), so the
video popups play reliably this way (opening index.html directly also works,
but YouTube may refuse to show the player inside the popup)."""
import http.server, socketserver, webbrowser, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
PORT = 8000
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
with socketserver.TCPServer(("127.0.0.1", PORT), Q) as srv:
    print("Serving at http://localhost:%d  (close this window to stop)" % PORT)
    webbrowser.open("http://localhost:%d/index.html" % PORT)
    srv.serve_forever()
