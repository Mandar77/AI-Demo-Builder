#!/usr/bin/env python3
"""
Simple webhook receiver for testing notifications
Run this locally to receive webhook notifications
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from datetime import datetime

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            print("\n" + "=" * 60)
            print(f"🎉 WEBHOOK NOTIFICATION RECEIVED - {datetime.now()}")
            print("=" * 60)
            print(json.dumps(data, indent=2))
            print("=" * 60 + "\n")
        except Exception as e:
            print(f"Error parsing JSON: {e}")
            print(f"Raw data: {post_data}")
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'status': 'received'}).encode())
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(b"""
        <html>
        <head><title>Webhook Receiver</title></head>
        <body>
            <h1>Webhook Receiver is Running</h1>
            <p>This server is ready to receive webhook notifications.</p>
            <p>POST requests will be logged to the console.</p>
        </body>
        </html>
        """)
    
    def log_message(self, format, *args):
        # Suppress default logging, we print our own
        pass

def run(port=8000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, WebhookHandler)
    print(f"🚀 Webhook receiver started on http://localhost:{port}")
    print(f"📡 Ready to receive notifications...")
    print(f"💡 Configure HTTP_WEBHOOK_URL=http://localhost:{port} in Lambda")
    print(f"   (For local testing, use ngrok or similar to expose this port)")
    print("\nPress Ctrl+C to stop\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Webhook receiver stopped")
        httpd.server_close()

if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    run(port)

