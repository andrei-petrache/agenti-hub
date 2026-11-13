"""Desenează mascota (bulgăraș portocaliu cu steluță) și o salvează ca agenti.ico — fără biblioteci externe."""
import math
import struct
import zlib
from pathlib import Path

ORANGE = (232, 135, 91)
DARK = (59, 47, 42)
PINK = (255, 143, 163)
WHITE = (255, 255, 255)


def star_pts(cx, cy, R, r):
    pts = []
    for i in range(8):
        ang = -math.pi / 2 + i * math.pi / 4
        rad = R if i % 2 == 0 else r
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    return pts


def in_poly(x, y, pts):
    ins = False
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            ins = not ins
        j = i
    return ins


STAR = star_pts(50, 17, 12, 3.2)


def sample(x, y):
    """Culoare (r,g,b,a) într-un punct din spațiul 100x100."""
    col = None
    # antena
    if abs(x - 50) < 1.6 and 24 <= y <= 33:
        col = ORANGE + (255,)
    if in_poly(x, y, STAR):
        col = ORANGE + (255,)
    # brațe
    for ax in (20, 80):
        if ((x - ax) / 5.5) ** 2 + ((y - 66) / 7.5) ** 2 <= 1:
            col = ORANGE + (255,)
    # corp
    if ((x - 50) / 32) ** 2 + ((y - 61) / 29) ** 2 <= 1:
        col = ORANGE + (255,)
        if ((x - 42) / 9) ** 2 + ((y - 41) / 5) ** 2 <= 1:
            col = tuple(int(c * 0.72 + 255 * 0.28) for c in ORANGE) + (255,)
        for bx in (31, 69):
            if (x - bx) ** 2 + (y - 63) ** 2 <= 30:
                col = tuple(int(c * 0.55 + p * 0.45) for c, p in zip(ORANGE, PINK)) + (255,)
        for ex in (39, 61):
            if (x - ex) ** 2 + (y - 55) ** 2 <= 5.2 ** 2:
                col = DARK + (255,)
            if (x - ex - 1.8) ** 2 + (y - 53) ** 2 <= 1.9 ** 2:
                col = WHITE + (255,)
        # zâmbet
        d = math.hypot(x - 50, y - 61)
        if 5.2 <= d <= 7.6 and y > 64:
            col = DARK + (255,)
    return col or (0, 0, 0, 0)


def render(size, ss=4):
    rows = []
    for py in range(size):
        row = bytearray()
        for px in range(size):
            acc = [0, 0, 0, 0]
            for sy in range(ss):
                for sx in range(ss):
                    x = (px + (sx + 0.5) / ss) * 100 / size
                    y = (py + (sy + 0.5) / ss) * 100 / size
                    r, g, b, a = sample(x, y)
                    acc[0] += r * a; acc[1] += g * a; acc[2] += b * a; acc[3] += a
            n = ss * ss
            a = acc[3] / n
            if acc[3]:
                row += bytes((int(acc[0] / acc[3]), int(acc[1] / acc[3]), int(acc[2] / acc[3]), int(a)))
            else:
                row += b"\0\0\0\0"
        rows.append(bytes(row))
    return rows


def png(rows, size):
    raw = b"".join(b"\0" + r for r in rows)
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def main():
    sizes = [16, 32, 48, 64, 128, 256]
    imgs = [png(render(s, 4 if s <= 64 else 2), s) for s in sizes]
    head = struct.pack("<HHH", 0, 1, len(imgs))
    off = 6 + 16 * len(imgs)
    dirs = b""
    for s, data in zip(sizes, imgs):
        dirs += struct.pack("<BBBBHHII", s % 256, s % 256, 0, 0, 1, 32, len(data), off)
        off += len(data)
    out = Path(__file__).with_name("agenti.ico")
    out.write_bytes(head + dirs + b"".join(imgs))
    Path(__file__).with_name("agenti.png").write_bytes(imgs[-1])
    print("scris", out)


if __name__ == "__main__":
    main()
