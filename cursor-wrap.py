#!/usr/bin/env python3
"""Wrap the cursor between the far-left and far-right edges in Hyprland."""
import json
import os
import socket
import time

SOCK = (f"{os.environ['XDG_RUNTIME_DIR']}/hypr/"
        f"{os.environ['HYPRLAND_INSTANCE_SIGNATURE']}/.socket.sock")

POLL = 0.02            # seconds between cursor checks
LAYOUT_REFRESH = 5.0   # seconds between monitor layout re-reads
EDGE = 3  # pixels of slack at each edge

def hypr(cmd: str) -> str:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.connect(SOCK)
        s.sendall(cmd.encode())
        chunks = []
        while data := s.recv(65536):
            chunks.append(data)
    return b"".join(chunks).decode()

def get_bounds() -> tuple[float, float]:
    mons = json.loads(hypr("j/monitors"))
    minx = min(m["x"] for m in mons)
    maxx = 0
    for m in mons:
        w = m["height"] if m["transform"] % 2 else m["width"]  # odd transforms are rotated 90/270
        maxx = max(maxx, m["x"] + w / m["scale"])
    return minx, maxx

def main() -> None:
    minx, maxx = get_bounds()
    last_refresh = time.monotonic()

    while True:
        try:
            now = time.monotonic()
            if now - last_refresh > LAYOUT_REFRESH:
                minx, maxx = get_bounds()
                last_refresh = now

            pos = json.loads(hypr("j/cursorpos"))
            x, y = pos["x"], int(pos["y"])

            if x >= maxx - EDGE:
                hypr(f"dispatch hl.dsp.cursor.move({{ x = {int(minx) + EDGE + 2}, y = {y} }})")
            elif x <= minx + 1:
                hypr(f"dispatch hl.dsp.cursor.move({{ x = {int(maxx) - EDGE - 2}, y = {y} }})")
        except (OSError, ValueError, KeyError):
            # If Hyprland is restarting or momentarily unavailable, retry
            time.sleep(1)
            continue

        time.sleep(POLL)

if __name__ == "__main__":
    main()