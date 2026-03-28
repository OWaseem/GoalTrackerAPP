#!/usr/bin/env python3
"""
Run once to generate VAPID keys for Web Push.
Copy the output into your Render environment variables.
"""
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import base64

private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
public_key  = private_key.public_key()

# Public key: uncompressed EC point, urlsafe base64 (no padding) — sent to browser
pub = base64.urlsafe_b64encode(
    public_key.public_bytes(
        serialization.Encoding.X962,
        serialization.PublicFormat.UncompressedPoint,
    )
).rstrip(b"=").decode()

# Private key: raw 32-byte scalar, urlsafe base64 (no padding) — used server-side
priv = base64.urlsafe_b64encode(
    private_key.private_numbers().private_value.to_bytes(32, "big")
).rstrip(b"=").decode()

print("Add these to your Render dashboard (Environment → Add Variable):\n")
print(f"VAPID_PUBLIC_KEY  = {pub}")
print(f"VAPID_PRIVATE_KEY = {priv}")
