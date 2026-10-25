"""Find this computer's Wi-Fi address and draw QR codes for the phone."""

from __future__ import annotations

import socket


def lan_ips() -> list[str]:
    """Best-effort list of private IPv4 addresses other devices on the network can reach."""
    ips: list[str] = []
    # The UDP "connect" trick picks the interface used for the default route; no packet is sent.
    for probe in ("10.255.255.255", "192.168.255.255", "172.31.255.255"):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect((probe, 1))
                ip = s.getsockname()[0]
                if ip and not ip.startswith("127.") and ip not in ips:
                    ips.append(ip)
        except OSError:
            continue
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if not ip.startswith("127.") and ip not in ips:
                ips.append(ip)
    except OSError:
        pass
    return [ip for ip in ips if is_private(ip)] or ips


def is_private(ip: str) -> bool:
    parts = [int(p) for p in ip.split(".")]
    return (
        parts[0] == 10
        or (parts[0] == 172 and 16 <= parts[1] <= 31)
        or (parts[0] == 192 and parts[1] == 168)
    )


def terminal_qr(text: str) -> str:
    import io

    import segno

    buf = io.StringIO()
    segno.make(text, error="m").terminal(out=buf, compact=True, border=2)
    return buf.getvalue()


def svg_qr(text: str) -> str:
    import io

    import segno

    buf = io.BytesIO()
    segno.make(text, error="m").save(buf, kind="svg", scale=6, border=2, dark="#111", light="#fff")
    return buf.getvalue().decode()
