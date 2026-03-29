"""
Pure Python replacements for lark_decrypt.js functions.
No Node.js / execjs dependency required.
"""
import random
import string
import hashlib
import uuid


def generate_request_id():
    """Generate a 10-char base36 request ID (replaces JS generate_request_id)."""
    chars = string.digits + string.ascii_lowercase
    return "".join(random.choices(chars, k=10))


def generate_long_request_id():
    """Generate a UUID-v4 style request ID (replaces JS generate_long_request_id)."""
    return str(uuid.uuid4())


def generate_request_cid():
    """Generate a 10-char alphanumeric CID (replaces JS generate_request_cid)."""
    chars = string.digits + string.ascii_uppercase + string.ascii_lowercase
    return "".join(random.choices(chars, k=10))


def generate_access_key(text):
    """MD5 hex digest (replaces JS generate_access_key which is just MD5)."""
    return hashlib.md5(text.encode("utf-8")).hexdigest()
