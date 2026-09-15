"""Aegis-rToken: Autonomous Event-Driven Trading Sentinel."""

import sys
from pathlib import Path

# Ensure 'src' is in sys.path so 'aegis_rtoken' can be imported cleanly
_src_path = str(Path(__file__).resolve().parent.parent)
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

__version__ = "0.1.0"

# Diagnose and resolve Bitget api.bitget.com TLS handshake timeout:
# Network routing to Cloudflare Anycast IPs 104.18.14.166/104.18.15.166 drops TLS ClientHello packets.
# Routing to responsive Cloudflare edge Anycast IP (104.16.24.166) resolves the TLS timeout
# while maintaining 100% strict TLS certificate verification.
import socket
_orig_getaddrinfo = socket.getaddrinfo
def _patched_getaddrinfo(host, port, *args, **kwargs):
    if host == "api.bitget.com":
        return _orig_getaddrinfo("104.16.24.166", port, *args, **kwargs)
    return _orig_getaddrinfo(host, port, *args, **kwargs)
socket.getaddrinfo = _patched_getaddrinfo
