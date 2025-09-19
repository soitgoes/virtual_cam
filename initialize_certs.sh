#!/bin/bash

# Virtual Security Camera - Certificate Initialization Script
# This script generates a self-signed SSL certificate and private key
# for use with the virtual security camera HTTPS server.

set -e  # Exit on any error

# Configuration
CERT_DIR="certs"
CERT_FILE="$CERT_DIR/virtual_camera.crt"
KEY_FILE="$CERT_DIR/virtual_camera.key"
DAYS=365
KEY_SIZE=2048
COUNTRY="US"
STATE="Virtual Camera"
CITY="Local"
ORG="Virtual Security Camera"
COMMON_NAME="localhost"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if OpenSSL is installed
check_openssl() {
    if ! command -v openssl &> /dev/null; then
        print_error "OpenSSL is not installed or not in PATH"
        print_info "Please install OpenSSL:"
        print_info "  - macOS: brew install openssl"
        print_info "  - Ubuntu/Debian: sudo apt-get install openssl"
        print_info "  - CentOS/RHEL: sudo yum install openssl"
        exit 1
    fi
}

# Function to create certificate directory
create_cert_dir() {
    if [ ! -d "$CERT_DIR" ]; then
        print_info "Creating certificate directory: $CERT_DIR"
        mkdir -p "$CERT_DIR"
        print_success "Certificate directory created"
    else
        print_info "Certificate directory already exists: $CERT_DIR"
    fi
}

# Function to check if certificates already exist
check_existing_certs() {
    if [ -f "$CERT_FILE" ] && [ -f "$KEY_FILE" ]; then
        print_warning "Certificates already exist:"
        print_info "  Certificate: $CERT_FILE"
        print_info "  Private Key: $KEY_FILE"
        echo
        read -p "Do you want to overwrite them? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Certificate generation cancelled"
            exit 0
        fi
        print_info "Overwriting existing certificates..."
    fi
}

# Function to generate private key
generate_private_key() {
    print_info "Generating private key ($KEY_SIZE bits)..."
    openssl genrsa -out "$KEY_FILE" $KEY_SIZE
    chmod 600 "$KEY_FILE"  # Restrict permissions to owner only
    print_success "Private key generated: $KEY_FILE"
}

# Function to generate certificate
generate_certificate() {
    print_info "Generating self-signed certificate (valid for $DAYS days)..."
    
    # Create certificate with Subject Alternative Names (SAN)
    openssl req -new -x509 -key "$KEY_FILE" -out "$CERT_FILE" -days $DAYS \
        -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/CN=$COMMON_NAME" \
        -addext "subjectAltName=DNS:localhost,DNS:127.0.0.1,IP:127.0.0.1"
    
    chmod 644 "$CERT_FILE"  # Readable by all, writable by owner
    print_success "Certificate generated: $CERT_FILE"
}

# Function to display certificate information
show_cert_info() {
    print_info "Certificate Information:"
    echo "  Subject: /C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/CN=$COMMON_NAME"
    echo "  Valid for: $DAYS days"
    echo "  Key size: $KEY_SIZE bits"
    echo "  Subject Alternative Names:"
    echo "    - DNS: localhost"
    echo "    - DNS: 127.0.0.1"
    echo "    - IP: 127.0.0.1"
    echo
    print_info "Certificate details:"
    openssl x509 -in "$CERT_FILE" -text -noout | grep -E "(Subject:|Not Before|Not After|Public Key)"
}

# Function to verify certificate
verify_certificate() {
    print_info "Verifying certificate..."
    if openssl x509 -in "$CERT_FILE" -text -noout > /dev/null 2>&1; then
        print_success "Certificate is valid"
    else
        print_error "Certificate verification failed"
        exit 1
    fi
    
    if openssl rsa -in "$KEY_FILE" -check -noout > /dev/null 2>&1; then
        print_success "Private key is valid"
    else
        print_error "Private key verification failed"
        exit 1
    fi
}

# Function to show usage instructions
show_usage() {
    print_info "Usage Instructions:"
    echo "  1. Run the virtual camera server:"
    echo "     python3 virtual_camera.py"
    echo
    echo "  2. Access the HTTPS stream:"
    echo "     https://localhost:8080/"
    echo
    echo "  3. Your browser will show a security warning (this is normal for self-signed certificates)"
    echo "     Click 'Advanced' and then 'Proceed to localhost (unsafe)'"
    echo
    print_warning "Security Notice:"
    echo "  - These are self-signed certificates for development/testing only"
    echo "  - Do not use in production environments"
    echo "  - The private key file has restricted permissions (600)"
}

# Main execution
main() {
    echo "=========================================="
    echo "Virtual Security Camera - Certificate Setup"
    echo "=========================================="
    echo
    
    # Check prerequisites
    check_openssl
    
    # Create directory and check existing certificates
    create_cert_dir
    check_existing_certs
    
    # Generate certificates
    generate_private_key
    generate_certificate
    
    # Verify and display information
    verify_certificate
    echo
    show_cert_info
    echo
    show_usage
    
    echo
    print_success "Certificate setup completed successfully!"
    echo "=========================================="
}

# Handle command line arguments
case "${1:-}" in
    -h|--help)
        echo "Virtual Security Camera - Certificate Initialization Script"
        echo
        echo "Usage: $0 [options]"
        echo
        echo "Options:"
        echo "  -h, --help     Show this help message"
        echo "  -f, --force    Force overwrite existing certificates"
        echo
        echo "This script generates a self-signed SSL certificate and private key"
        echo "for use with the virtual security camera HTTPS server."
        exit 0
        ;;
    -f|--force)
        # Force overwrite without prompting
        if [ -f "$CERT_FILE" ] && [ -f "$KEY_FILE" ]; then
            print_info "Force overwriting existing certificates..."
        fi
        main
        ;;
    "")
        # No arguments, run normally
        main
        ;;
    *)
        print_error "Unknown option: $1"
        print_info "Use -h or --help for usage information"
        exit 1
        ;;
esac
