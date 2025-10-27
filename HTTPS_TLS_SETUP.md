# HTTPS/TLS Configuration for Election System

## Overview
This document provides instructions for configuring HTTPS/TLS for the election system to ensure secure data transmission between clients and the server.

## Requirements
- SSL/TLS certificate (either from a Certificate Authority or self-signed for development)
- Python 3.6+ with Flask
- OpenSSL for certificate generation

## Steps to Configure HTTPS/TLS

### 1. Obtain SSL/TLS Certificate

#### For Production (Recommended)
Obtain a certificate from a trusted Certificate Authority (CA) like Let's Encrypt, DigiCert, or Comodo.

**Using Let's Encrypt (Free)**:
```bash
# Install certbot
pip install certbot

# Generate certificate (replace with your domain)
certbot certonly --standalone -d yourelectiondomain.com
```

#### For Development/Testing (Self-signed)
```bash
# Generate private key
openssl genrsa -out server.key 2048

# Generate Certificate Signing Request (CSR)
openssl req -new -key server.key -out server.csr

# Generate self-signed certificate (valid for 365 days)
openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt
```

### 2. Configure Flask Application

Update your Flask application to use HTTPS by adding the following code to your `app.py`:

```python
if __name__ == '__main__':
    # For development with self-signed certificate
    app.run(
        host='0.0.0.0',
        port=5000,
        ssl_context=('server.crt', 'server.key')
    )
    
    # For production with Let's Encrypt certificate
    # app.run(
    #     host='0.0.0.0',
    #     port=443,
    #     ssl_context=('/etc/letsencrypt/live/yourelectiondomain.com/fullchain.pem', 
    #                  '/etc/letsencrypt/live/yourelectiondomain.com/privkey.pem')
    # )
```

### 3. Configure HTTPS with a Production Server (Recommended)

For production, it's recommended to use a proper WSGI server like Gunicorn with Nginx:

#### Gunicorn Configuration
```bash
# Install Gunicorn
pip install gunicorn

# Run with SSL
gunicorn --certfile=server.crt --keyfile=server.key -b 0.0.0.0:5000 app:app
```

#### Nginx Configuration (as a reverse proxy)
```nginx
server {
    listen 443 ssl;
    server_name yourelectiondomain.com;

    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;
    
    # Strong SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305';
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_stapling on;
    ssl_stapling_verify on;
    
    # HSTS (optional but recommended)
    add_header Strict-Transport-Security "max-age=63072000" always;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourelectiondomain.com;
    return 301 https://$host$request_uri;
}
```

### 4. Security Headers

Ensure your application sets the following security headers:

```python
@app.after_request
def add_security_headers(response):
    # HSTS
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    # Content Security Policy
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'DENY'
    # XSS protection
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response
```

### 5. Certificate Renewal (for Let's Encrypt)

Set up automatic renewal for Let's Encrypt certificates:

```bash
# Create a cron job to run twice daily
echo "0 0,12 * * * root python -c 'import random; import time; time.sleep(random.random() * 3600)' && certbot renew -q" | sudo tee -a /etc/crontab > /dev/null
```

## Testing Your HTTPS Configuration

1. Verify your certificate is properly installed:
   ```bash
   openssl s_client -connect yourelectiondomain.com:443 -servername yourelectiondomain.com
   ```

2. Check your SSL/TLS configuration with online tools:
   - [SSL Labs Server Test](https://www.ssllabs.com/ssltest/)
   - [Security Headers](https://securityheaders.com/)

## Additional Security Recommendations

1. **HTTP Strict Transport Security (HSTS)**: Already included in the configuration above.

2. **Certificate Transparency Monitoring**: Monitor Certificate Transparency logs for certificates issued for your domain.

3. **OCSP Stapling**: Already enabled in the Nginx configuration.

4. **TLS Version**: Only allow TLSv1.2 and TLSv1.3 as configured above.

5. **Regular Updates**: Keep all software components (OpenSSL, Nginx, etc.) updated to patch security vulnerabilities.