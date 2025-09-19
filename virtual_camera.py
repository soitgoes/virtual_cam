#!/usr/bin/env python3
"""
Virtual Security Camera Implementation
Hosts an MJPEG stream on port 8080 that can pipe content from a security camera
"""

import cv2
import threading
import time
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import argparse
import sys
import os
import ssl
import socket
import ipaddress
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
    daemon_threads = True
    allow_reuse_address = True


class SSLContext:
    """Helper class for SSL certificate generation and management."""
    
    @staticmethod
    def generate_self_signed_cert(cert_file, key_file, hostname='localhost'):
        """Generate a self-signed SSL certificate."""
        try:
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            
            # Create certificate
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Virtual Camera"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "Local"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Virtual Security Camera"),
                x509.NameAttribute(NameOID.COMMON_NAME, hostname),
            ])
            
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + timedelta(days=365)
            ).add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName(hostname),
                    x509.DNSName("localhost"),
                    x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
                ]),
                critical=False,
            ).sign(private_key, hashes.SHA256(), default_backend())
            
            # Write certificate to file
            with open(cert_file, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            
            # Write private key to file
            with open(key_file, "wb") as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            logger.info(f"Generated self-signed certificate: {cert_file}")
            logger.info(f"Generated private key: {key_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate self-signed certificate: {e}")
            return False
    
    @staticmethod
    def setup_ssl_context(cert_file, key_file):
        """Setup SSL context for HTTPS server."""
        try:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(cert_file, key_file)
            context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
            return context
        except Exception as e:
            logger.error(f"Failed to setup SSL context: {e}")
            return None


class MJPEGHandler(BaseHTTPRequestHandler):
    """HTTP handler for MJPEG streaming."""
    
    def do_GET(self):
        """Handle GET requests for the MJPEG stream."""
        if self.path == '/stream':
            self.send_response(200)
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()
            
            try:
                while True:
                    # Get frame from the virtual camera
                    frame = self.server.virtual_camera.get_frame()
                    if frame is not None:
                        # Encode frame as JPEG
                        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                        if ret:
                            # Send frame
                            self.wfile.write(b'--frame\r\n')
                            self.send_header('Content-Type', 'image/jpeg')
                            self.send_header('Content-Length', str(len(buffer)))
                            self.end_headers()
                            self.wfile.write(buffer)
                            self.wfile.write(b'\r\n')
                    time.sleep(0.033)  # ~30 FPS
            except (ConnectionResetError, BrokenPipeError):
                logger.info("Client disconnected from stream")
        elif self.path == '/':
            # Serve a simple HTML page to view the stream
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            # Determine protocol based on server type
            protocol = "https" if hasattr(self.server, 'ssl_context') and self.server.ssl_context else "http"
            port = self.server.server_address[1]
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Virtual Security Camera</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                    .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .stream {{ border: 2px solid #333; border-radius: 8px; }}
                    .info {{ background: #f0f0f0; padding: 15px; border-radius: 4px; margin-bottom: 20px; }}
                    .security-badge {{ background: #4CAF50; color: white; padding: 5px 10px; border-radius: 4px; font-size: 12px; display: inline-block; margin-left: 10px; }}
                    .warning {{ background: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 10px; border-radius: 4px; margin-bottom: 15px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Virtual Security Camera Stream <span class="security-badge">HTTPS</span></h1>
                    <div class="warning">
                        <strong>Security Notice:</strong> This connection uses a self-signed certificate. 
                        Your browser may show a security warning - this is normal for development/testing purposes.
                    </div>
                    <div class="info">
                        <p><strong>Stream URL:</strong> <a href="/stream">{protocol}://localhost:{port}/stream</a></p>
                        <p><strong>Protocol:</strong> {protocol.upper()}</p>
                        <p><strong>Status:</strong> <span id="status">Connecting...</span></p>
                    </div>
                    <img src="/stream" alt="Camera Stream" class="stream" style="width: 100%; max-width: 640px;">
                </div>
                <script>
                    const img = document.querySelector('img');
                    const status = document.getElementById('status');
                    
                    img.onload = () => status.textContent = 'Connected';
                    img.onerror = () => status.textContent = 'Connection Error';
                </script>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')

    def log_message(self, format, *args):
        """Override to use our logger instead of stderr."""
        logger.info(f"{self.address_string()} - {format % args}")


class VirtualCamera:
    """Virtual camera that can simulate or use real camera input."""
    
    def __init__(self, camera_source=0, simulation_mode=False):
        """
        Initialize the virtual camera.
        
        Args:
            camera_source: Camera source (0 for default webcam, or path to video file)
            simulation_mode: If True, generates synthetic frames instead of using real camera
        """
        self.camera_source = camera_source
        self.simulation_mode = simulation_mode
        self.cap = None
        self.frame_count = 0
        self.lock = threading.Lock()
        
        if not simulation_mode:
            self._initialize_camera()
    
    def _initialize_camera(self):
        """Initialize the camera capture."""
        try:
            self.cap = cv2.VideoCapture(self.camera_source)
            if not self.cap.isOpened():
                logger.error(f"Failed to open camera source: {self.camera_source}")
                logger.info("Falling back to simulation mode")
                self.simulation_mode = True
            else:
                # Set camera properties for better performance
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.cap.set(cv2.CAP_PROP_FPS, 30)
                logger.info(f"Camera initialized successfully: {self.camera_source}")
        except Exception as e:
            logger.error(f"Error initializing camera: {e}")
            logger.info("Falling back to simulation mode")
            self.simulation_mode = True
    
    def _generate_synthetic_frame(self):
        """Generate a synthetic frame for simulation mode."""
        import numpy as np
        
        # Create a frame with timestamp and moving elements
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Add a gradient background
        for y in range(480):
            for x in range(640):
                frame[y, x] = [int(50 + (y/480) * 50), int(50 + (x/640) * 50), 100]
        
        # Add timestamp
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, timestamp, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Add moving circle
        center_x = int(320 + 200 * np.sin(self.frame_count * 0.05))
        center_y = int(240 + 100 * np.cos(self.frame_count * 0.03))
        cv2.circle(frame, (center_x, center_y), 20, (0, 255, 0), -1)
        
        # Add some text
        cv2.putText(frame, "VIRTUAL SECURITY CAMERA", (10, 450), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
        cv2.putText(frame, "SIMULATION MODE", (10, 420), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        self.frame_count += 1
        return frame
    
    def get_frame(self):
        """Get the next frame from the camera."""
        with self.lock:
            if self.simulation_mode:
                return self._generate_synthetic_frame()
            else:
                if self.cap and self.cap.isOpened():
                    ret, frame = self.cap.read()
                    if ret:
                        return frame
                    else:
                        logger.warning("Failed to read frame from camera")
                        return None
                else:
                    return None
    
    def release(self):
        """Release camera resources."""
        if self.cap:
            self.cap.release()
            logger.info("Camera resources released")


class VirtualCameraServer:
    """Main server class for the virtual security camera."""
    
    def __init__(self, https_port=8080, http_port=8081, camera_source=0, simulation_mode=False, 
                 use_https=True, use_http=True, cert_file=None, key_file=None):
        """
        Initialize the virtual camera server.
        
        Args:
            https_port: Port for HTTPS server
            http_port: Port for HTTP server
            camera_source: Camera source (0 for default webcam, or path to video file)
            simulation_mode: If True, generates synthetic frames instead of using real camera
            use_https: If True, start HTTPS server
            use_http: If True, start HTTP server
            cert_file: Path to SSL certificate file (auto-generated if None)
            key_file: Path to SSL private key file (auto-generated if None)
        """
        self.https_port = https_port
        self.http_port = http_port
        self.use_https = use_https
        self.use_http = use_http
        self.cert_file = cert_file or 'certs/virtual_camera.crt'
        self.key_file = key_file or 'certs/virtual_camera.key'
        self.virtual_camera = VirtualCamera(camera_source, simulation_mode)
        self.https_server = None
        self.http_server = None
        self.https_thread = None
        self.http_thread = None
    
    def start(self):
        """Start the virtual camera server(s)."""
        try:
            # Setup SSL if HTTPS is enabled
            ssl_context = None
            if self.use_https:
                # Ensure certs directory exists
                cert_dir = os.path.dirname(self.cert_file)
                if cert_dir and not os.path.exists(cert_dir):
                    os.makedirs(cert_dir, exist_ok=True)
                    logger.info(f"Created certificate directory: {cert_dir}")
                
                # Generate self-signed certificate if files don't exist
                if not os.path.exists(self.cert_file) or not os.path.exists(self.key_file):
                    logger.info("Generating self-signed SSL certificate...")
                    if not SSLContext.generate_self_signed_cert(self.cert_file, self.key_file):
                        logger.error("Failed to generate SSL certificate. Disabling HTTPS.")
                        self.use_https = False
                
                if self.use_https:
                    ssl_context = SSLContext.setup_ssl_context(self.cert_file, self.key_file)
                    if not ssl_context:
                        logger.error("Failed to setup SSL context. Disabling HTTPS.")
                        self.use_https = False
            
            # Start HTTPS server if enabled
            if self.use_https and ssl_context:
                self.https_server = ThreadedHTTPServer(('0.0.0.0', self.https_port), MJPEGHandler)
                self.https_server.virtual_camera = self.virtual_camera
                self.https_server.ssl_context = ssl_context
                self.https_server.socket = ssl_context.wrap_socket(self.https_server.socket, server_side=True)
                
                self.https_thread = threading.Thread(target=self.https_server.serve_forever)
                self.https_thread.daemon = True
                self.https_thread.start()
                
                logger.info(f"HTTPS server started on port {self.https_port}")
                logger.info(f"HTTPS Stream URL: https://localhost:{self.https_port}/stream")
                logger.info(f"HTTPS Web interface: https://localhost:{self.https_port}/")
            
            # Start HTTP server if enabled
            if self.use_http:
                self.http_server = ThreadedHTTPServer(('0.0.0.0', self.http_port), MJPEGHandler)
                self.http_server.virtual_camera = self.virtual_camera
                
                self.http_thread = threading.Thread(target=self.http_server.serve_forever)
                self.http_thread.daemon = True
                self.http_thread.start()
                
                logger.info(f"HTTP server started on port {self.http_port}")
                logger.info(f"HTTP Stream URL: http://localhost:{self.http_port}/stream")
                logger.info(f"HTTP Web interface: http://localhost:{self.http_port}/")
            
            # Log server information
            logger.info("=" * 60)
            logger.info("Virtual Security Camera Server Started")
            logger.info("=" * 60)
            logger.info(f"Camera source: {self.virtual_camera.camera_source}")
            logger.info(f"Simulation mode: {self.virtual_camera.simulation_mode}")
            
            if self.use_https and ssl_context:
                logger.info("Using self-signed certificate - browser may show security warning")
                logger.info(f"Certificate file: {self.cert_file}")
                logger.info(f"Private key file: {self.key_file}")
            
            logger.info("Press Ctrl+C to stop the server(s)")
            logger.info("=" * 60)
            
            # Keep main thread alive
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Shutting down server(s)...")
                self.stop()
                
        except Exception as e:
            logger.error(f"Error starting server: {e}")
            sys.exit(1)
    
    def stop(self):
        """Stop the virtual camera server(s)."""
        if self.https_server:
            self.https_server.shutdown()
            self.https_server.server_close()
            logger.info("HTTPS server stopped")
        
        if self.http_server:
            self.http_server.shutdown()
            self.http_server.server_close()
            logger.info("HTTP server stopped")
        
        self.virtual_camera.release()
        logger.info("All servers stopped")


def main():
    """Main function to run the virtual camera server."""
    parser = argparse.ArgumentParser(description='Virtual Security Camera Server with Dual HTTP/HTTPS Support')
    parser.add_argument('--https-port', type=int, default=8080, help='Port for HTTPS server (default: 8080)')
    parser.add_argument('--http-port', type=int, default=8081, help='Port for HTTP server (default: 8081)')
    parser.add_argument('--camera', type=str, default='0', help='Camera source: 0 for default webcam, or path to video file')
    parser.add_argument('--simulation', action='store_true', help='Run in simulation mode (generate synthetic frames)')
    parser.add_argument('--https-only', action='store_true', help='Run only HTTPS server (disable HTTP)')
    parser.add_argument('--http-only', action='store_true', help='Run only HTTP server (disable HTTPS)')
    parser.add_argument('--cert', type=str, help='Path to SSL certificate file (auto-generated if not provided)')
    parser.add_argument('--key', type=str, help='Path to SSL private key file (auto-generated if not provided)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Convert camera argument to appropriate type
    camera_source = args.camera
    if camera_source.isdigit():
        camera_source = int(camera_source)
    
    # Determine which servers to start
    use_https = not args.http_only
    use_http = not args.https_only
    
    # Create and start server
    server = VirtualCameraServer(
        https_port=args.https_port,
        http_port=args.http_port,
        camera_source=camera_source,
        simulation_mode=args.simulation,
        use_https=use_https,
        use_http=use_http,
        cert_file=args.cert,
        key_file=args.key
    )
    
    server.start()


if __name__ == '__main__':
    main()
