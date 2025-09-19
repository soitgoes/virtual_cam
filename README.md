# Virtual Security Camera

A Python implementation of a virtual security camera that hosts an MJPEG stream on port 8080 with HTTPS support. This can be used to pipe content from a real security camera or run in simulation mode for testing purposes.

## Features

- **MJPEG Streaming**: Hosts a live video stream accessible via HTTPS (or HTTP)
- **SSL/TLS Support**: Uses self-signed certificates for secure connections
- **Real Camera Support**: Can use webcams or video files as input sources
- **Simulation Mode**: Generates synthetic frames for testing without hardware
- **Web Interface**: Built-in HTML page to view the stream with security indicators
- **Threaded Server**: Handles multiple concurrent connections
- **Configurable**: Command-line options for port, camera source, protocol, and mode

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip3 install -r requirements.txt
```

## Usage

### Basic Usage

Start the virtual camera server with default settings (HTTPS on port 8080, HTTP on port 8081, default webcam):

```bash
python3 virtual_camera.py
```

### Command Line Options

```bash
python3 virtual_camera.py [options]

Options:
  --https-port PORT   Port for HTTPS server (default: 8080)
  --http-port PORT    Port for HTTP server (default: 8081)
  --camera SOURCE     Camera source: 0 for default webcam, or path to video file
  --simulation        Run in simulation mode (generate synthetic frames)
  --https-only        Run only HTTPS server (disable HTTP)
  --http-only         Run only HTTP server (disable HTTPS)
  --auth TYPE         Enable authentication (basic or digest)
  --cert FILE         Path to SSL certificate file (auto-generated if not provided)
  --key FILE          Path to SSL private key file (auto-generated if not provided)
  --verbose, -v       Enable verbose logging
  --help, -h          Show help message
```

### Examples

**Use a specific webcam (camera index 1):**
```bash
python3 virtual_camera.py --camera 1
```

**Use a video file as input:**
```bash
python3 virtual_camera.py --camera /path/to/video.mp4
```

**Run in simulation mode (no camera required):**
```bash
python3 virtual_camera.py --simulation
```

**Run only HTTPS server (disable HTTP):**
```bash
python3 virtual_camera.py --https-only
```

**Run only HTTP server (disable HTTPS):**
```bash
python3 virtual_camera.py --http-only
```

**Use different ports:**
```bash
python3 virtual_camera.py --https-port 9090 --http-port 9091
```

**Use custom SSL certificate files:**
```bash
python3 virtual_camera.py --cert /path/to/cert.crt --key /path/to/key.key
```

**Use certificates from the certs directory:**
```bash
python3 virtual_camera.py --cert certs/my_cert.crt --key certs/my_key.key
```

**Enable Basic Authentication:**
```bash
python3 virtual_camera.py --auth basic
```

**Enable Digest Authentication:**
```bash
python3 virtual_camera.py --auth digest
```

**Enable verbose logging:**
```bash
python3 virtual_camera.py --verbose
```

## Accessing the Stream

Once the server is running, you can access the video stream in several ways:

### HTTPS Access (Default)
**Web Interface:**
```
https://localhost:8080/
```

**Direct Stream URL:**
```
https://localhost:8080/stream
```

**Note**: Since the server uses a self-signed certificate, your browser will show a security warning. This is normal for development/testing purposes. You can safely proceed by clicking "Advanced" and then "Proceed to localhost (unsafe)" or similar option.

### HTTP Access (Default)
**Web Interface:**
```
http://localhost:8081/
```

**Direct Stream URL:**
```
http://localhost:8081/stream
```

### Custom Ports
If you've specified different ports:
```
https://localhost:[HTTPS_PORT]/
http://localhost:[HTTP_PORT]/
```

### Authentication
When authentication is enabled, you'll be prompted for credentials:

**Default Credentials (for testing):**
- **Username**: `username`
- **Password**: `password`

**Basic Authentication:**
- Credentials are sent in base64 encoding
- Less secure but widely supported
- Use with HTTPS for better security

**Digest Authentication:**
- Credentials are hashed before transmission
- More secure than Basic Auth
- Still recommended to use with HTTPS

### Integration with Other Applications

The MJPEG stream can be integrated with:
- Security monitoring software
- Home automation systems
- Video recording applications
- Web applications that need live video feeds

## Technical Details

### MJPEG Stream Format
The server provides a standard MJPEG stream with:
- Content-Type: `multipart/x-mixed-replace; boundary=frame`
- JPEG quality: 85% (configurable in code)
- Target frame rate: ~30 FPS
- Resolution: 640x480 (configurable)

### Camera Support
- **Webcams**: Uses OpenCV's VideoCapture with camera indices (0, 1, 2, etc.)
- **Video Files**: Supports common video formats (MP4, AVI, MOV, etc.)
- **Simulation Mode**: Generates synthetic frames with timestamp and moving elements

### Server Architecture
- **Threaded HTTP Server**: Handles multiple concurrent connections
- **Thread-Safe Frame Access**: Uses locks to prevent race conditions
- **Graceful Shutdown**: Properly releases camera resources on exit

## Troubleshooting

### Camera Not Found
If the default camera (index 0) is not found:
1. Try different camera indices: `--camera 1`, `--camera 2`, etc.
2. Use simulation mode: `--simulation`
3. Check if the camera is being used by another application

### Port Already in Use
If port 8080 is already in use:
```bash
python3 virtual_camera.py --port 8081
```

### Permission Issues
On some systems, you may need to grant camera permissions to the terminal application.

### Performance Issues
- Reduce JPEG quality in the code (line with `cv2.IMWRITE_JPEG_QUALITY`)
- Lower the frame rate by increasing the sleep time in the stream loop
- Use a lower resolution camera or resize frames

## Certificate Management

### Automatic Certificate Generation
- **Default location**: Certificates are stored in the `certs/` directory
- **Auto-creation**: The `certs/` directory is created automatically if it doesn't exist
- **File names**: `certs/virtual_camera.crt` and `certs/virtual_camera.key`
- **Git ignore**: The `certs/` directory is excluded from version control for security

### Manual Certificate Generation
You can also generate certificates manually using the provided shell script:

```bash
# Generate certificates using the shell script
./initialize_certs.sh

# Force overwrite existing certificates
./initialize_certs.sh --force

# Show help
./initialize_certs.sh --help
```

The shell script provides:
- **OpenSSL validation** - checks if OpenSSL is installed
- **Interactive prompts** - asks before overwriting existing certificates
- **Certificate verification** - validates generated certificates
- **Detailed output** - shows certificate information and usage instructions

### Custom Certificates
You can use your own SSL certificates by specifying the paths:
```bash
python3 virtual_camera.py --cert certs/my_cert.crt --key certs/my_key.key
```

### Certificate Security
- **Never commit certificates** to version control
- **Self-signed certificates** are for development/testing only
- **Production use** requires certificates from a trusted Certificate Authority

## Security Considerations

- The server binds to `0.0.0.0` by default, making it accessible from any network interface
- **HTTPS is enabled by default** with self-signed certificates for secure connections
- Self-signed certificates will trigger browser security warnings - this is normal for development/testing
- **Authentication is available** with Basic and Digest auth for testing purposes
- **Default credentials** (username/password) are hardcoded for testing - change for production use
- For production use, consider using proper SSL certificates from a trusted Certificate Authority
- The current implementation is designed for local network use and testing purposes

## Dependencies

- **opencv-python**: Computer vision library for camera access and image processing
- **numpy**: Numerical computing library (required by OpenCV)
- **cryptography**: Library for SSL/TLS certificate generation and management
