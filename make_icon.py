"""Draws the BuzzzHub bee and saves it as buzzzhub.ico / buzzzhub.png, with no external libraries."""
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


YELLOW = (255, 196, 61)
WING = (205, 232, 255)


def seg_dist(x, y, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    t = max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
    return math.hypot(x - x1 - t * dx, y - y1 - t * dy)


def sample(x, y):
    """The BuzzzHub bee: (r,g,b,a) colour at a point of the 100x100 space."""
    col = None
    # wings (behind)
    for wx, rot in ((29, 0.5), (71, -0.5)):
        c, s_ = math.cos(rot), math.sin(rot)
        u, v = (x - wx) * c + (y - 30) * s_, -(x - wx) * s_ + (y - 30) * c
        if (u / 15) ** 2 + (v / 10) ** 2 <= 1:
            col = WING + (235,)
    # antennae
    for (x1, y1, x2, y2) in ((42, 34, 35, 15), (58, 34, 65, 15)):
        if seg_dist(x, y, x1, y1, x2, y2) < 1.7:
            col = DARK + (255,)
        if math.hypot(x - x2, y - y2) < 4:
            col = DARK + (255,)
    # body
    if ((x - 50) / 33) ** 2 + ((y - 60) / 31) ** 2 <= 1:
        col = YELLOW + (255,)
        if 73 <= y <= 79 or 84.5 <= y <= 90:
            col = DARK + (255,)
        if ((x - 41) / 9) ** 2 + ((y - 39) / 4.5) ** 2 <= 1:
            col = tuple(int(c * 0.7 + 255 * 0.3) for c in YELLOW) + (255,)
        for bx in (30, 70):
            if (x - bx) ** 2 + (y - 60) ** 2 <= 30:
                col = tuple(int(c * 0.55 + p * 0.45) for c, p in zip(YELLOW, PINK)) + (255,)
        for ex in (39, 61):
            if (x - ex) ** 2 + (y - 52) ** 2 <= 5.2 ** 2:
                col = DARK + (255,)
            if (x - ex - 1.8) ** 2 + (y - 50) ** 2 <= 1.9 ** 2:
                col = WHITE + (255,)
        d = math.hypot(x - 50, y - 58)
        if 5.2 <= d <= 7.6 and y > 61:
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
    out = Path(__file__).with_name("buzzzhub.ico")
    out.write_bytes(head + dirs + b"".join(imgs))
    Path(__file__).with_name("buzzzhub.png").write_bytes(imgs[-1])
    print("wrote", out)


if __name__ == "__main__":
    main()
