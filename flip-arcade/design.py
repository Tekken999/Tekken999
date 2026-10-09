#!/usr/bin/env python3
"""Swap-style flip-up buffet arcade: geometry checks, cut list and drawings.

Closed, it is a double-door cabinet. The "doors" don't open: they are the back
of the display unit, which hangs upside down in a slot at the front. To play,
the display unit swings forward and up 180 degrees, then the fold-down control
deck on its front drops to horizontal. Storage sits behind the display unit
and is reached in arcade mode.

Usage:
    python3 design.py                                  # default 27" monitor
    python3 design.py --monitor-w 21.3 --monitor-h 12.6 --monitor-d 1.9

Everything is in inches. Side views use y = depth (0 = front face, grows toward
the wall) and z = height (0 = floor). Writes cabinet_mode.svg, arcade_mode.svg,
flip_sequence.svg and front_closed.svg next to this file and prints the checks
and cut list.
"""
import argparse
import math
import os

# --- Carcass -----------------------------------------------------------------
W = 29.0            # overall width
D = 13.5            # overall depth
H = 36.0            # closed height incl. glides
T = 0.75            # 3/4" plywood
GLIDE = 1.0         # leveling glide height -> carcass starts at z = 1
INNER_W = W - 2 * T  # 27.5 between side panels
TOP_Z = H - T

# --- Display unit (screen, speakers, marquee, fold-down deck) ----------------
UNIT_W = INNER_W - 0.25    # 1/8" each side for nylon washers
UNIT_D = 6.75
UNIT_L = 34.0
UNIT_Y0 = 0.125            # front face (screen side in arcade mode)
UNIT_WALL = 0.5
UNIT_BACK = 0.5            # 1/2" veneered back: it is the "double doors" when closed
PIVOT_FROM_END = 2.75
END_R = 2.25               # round-over on the pivot-end corners
FOOT_R = 0.5               # round-over on the other end
PIVOT = (UNIT_Y0 + UNIT_D / 2, H - PIVOT_FROM_END)
LOCK_OFFSET = 1.5          # index-plunger holes 1.5" either side of the pivot

# --- Fold-down control deck (Swap-style "front panel folds down") ------------
DECK_HINGE_Z = 35.0        # deck hinge on the unit front face (arcade orientation)
DECK_DEPTH = 8.0           # how far the deck reaches forward when down
DECK_THICK = 3.5           # 1/2" plate + 2-3/4" for stick/button bodies + 1/4" cover
STICK_Y_FROM_FRONT = 3.0
STICK_H = 2.5              # ball top above the control plate

# --- Storage behind the slot -------------------------------------------------
STORAGE_DOOR_Y = 7.375     # inset storage doors (front face)
SHELVES = 2

# --- Arcade-mode layout on the unit (z) --------------------------------------
MONITOR_BOTTOM = DECK_HINGE_Z + DECK_DEPTH + 0.5
MARQUEE_H = 5.0
TOPPER_H = 5.5             # optional lift-off topper to hit 70"

CLEARANCE = 0.25
UNIT_WEIGHT = 35.0         # lb: 27" monitor, speakers, deck, mini PC, wood


def rot(p, c, deg):
    """Rotate p about c by deg (counter-clockwise in the side view, front at left)."""
    a = math.radians(deg)
    dy, dz = p[0] - c[0], p[1] - c[1]
    return (c[0] + dy * math.cos(a) - dz * math.sin(a),
            c[1] + dy * math.sin(a) + dz * math.cos(a))


def rect(y0, z0, y1, z1):
    return [(y0, z0), (y1, z0), (y1, z1), (y0, z1)]


def densify(pts, step=0.25):
    out = []
    for a, b in zip(pts, pts[1:] + pts[:1]):
        n = max(1, int(math.dist(a, b) / step))
        out += [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n)]
    return out


# --- Moving parts, defined in ARCADE orientation -----------------------------
def unit_z():
    z0 = PIVOT[1] - PIVOT_FROM_END
    return z0, z0 + UNIT_L


def unit_shell():
    y0, y1 = UNIT_Y0, UNIT_Y0 + UNIT_D
    z0, z1 = unit_z()

    def corner(cy, cz, r, a0):
        return [(cy + r * math.cos(math.radians(a)), cz + r * math.sin(math.radians(a)))
                for a in range(a0, a0 + 91, 15)]
    r, f = END_R, FOOT_R
    return (corner(y1 - f, z1 - f, f, 0) + corner(y0 + f, z1 - f, f, 90)
            + corner(y0 + r, z0 + r, r, 180) + corner(y1 - r, z0 + r, r, 270))


def deck_parts(down):
    """Deck box and stick. Folded = stowed in a pocket in the unit's front face."""
    hinge = (UNIT_Y0, DECK_HINGE_Z)
    folded = rect(UNIT_Y0, DECK_HINGE_Z, UNIT_Y0 + DECK_THICK, DECK_HINGE_Z + DECK_DEPTH)
    sz = DECK_HINGE_Z + DECK_DEPTH - STICK_Y_FROM_FRONT
    stick = rect(UNIT_Y0 + DECK_THICK, sz - 0.6, UNIT_Y0 + DECK_THICK + STICK_H, sz + 0.6)
    if not down:
        return folded, stick
    return [rot(p, hinge, 90) for p in folded], [rot(p, hinge, 90) for p in stick]


def at_progress(pts, phi):
    """phi = 0 closed (buffet), 180 open (arcade). The unit's free end swings forward."""
    return [rot(p, PIVOT, -phi - 180) for p in pts]


# --- Fixed parts --------------------------------------------------------------
def door_top():
    """Storage doors stop below the unit's bottom in arcade mode so they can swing open."""
    return unit_z()[0] - T


def fixed_parts():
    parts = {
        "bottom": rect(STORAGE_DOOR_Y, GLIDE, D - T, GLIDE + T),
        "back": rect(D - T, GLIDE, D, TOP_Z),
        "top": rect(STORAGE_DOOR_Y, TOP_Z, D, H),
        "storage doors": rect(STORAGE_DOOR_Y, GLIDE + T, STORAGE_DOOR_Y + T, door_top()),
        "face rail": rect(STORAGE_DOOR_Y, door_top(), STORAGE_DOOR_Y + T, TOP_Z),
    }
    for i in range(SHELVES):
        z = GLIDE + T + (TOP_Z - GLIDE - T) * (i + 1) / (SHELVES + 1)
        parts[f"shelf {i + 1}"] = rect(STORAGE_DOOR_Y + T, z - T, D - T, z)
    return parts


def rect_dist(p, r):
    (y0, z0), (y1, z1) = r[0], r[2]
    inside = y0 < p[0] < y1 and z0 < p[1] < z1
    return -1.0 if inside else math.hypot(max(y0 - p[0], 0, p[0] - y1), max(z0 - p[1], 0, p[1] - z1))


def sweep():
    folded, stick = deck_parts(down=False)
    pts = densify(unit_shell()) + densify(folded) + densify(stick)
    fixed = fixed_parts()
    closest = {k: (math.inf, None) for k in fixed}
    reach_front = 0.0
    for phi in range(0, 181):
        moved = at_progress(pts, phi)
        reach_front = min(reach_front, min(p[0] for p in moved))
        for name, r in fixed.items():
            d = min(rect_dist(p, r) for p in moved)
            if d < closest[name][0]:
                closest[name] = (d, phi)
    return closest, reach_front


def geometry(args):
    z0, z1 = unit_z()
    inner_w = UNIT_W - 2 * UNIT_WALL
    _, stick = deck_parts(down=False)
    deck, _ = deck_parts(down=True)
    deck_top = max(p[1] for p in deck)
    monitor_top = MONITOR_BOTTOM + args.monitor_h
    marquee_top = z1 - 0.75
    marquee_bottom = marquee_top - MARQUEE_H
    closest, reach_front = sweep()
    stored_bottom = min(p[1] for p in at_progress(unit_shell(), 0))
    stick_back = max(p[0] for p in stick)
    back_inside = UNIT_Y0 + UNIT_D - UNIT_BACK

    checks = [
        ("Closed: unit clears the floor", stored_bottom >= GLIDE, f"unit bottom z {stored_bottom:.2f}"),
        ("Folded sticks fit inside the unit", stick_back <= back_inside - 0.125,
         f"stick tips at y {stick_back:.2f}, back panel at {back_inside:.2f}"),
    ]
    for name, (d, phi) in closest.items():
        checks.append((f"Flip clears {name}", d >= CLEARANCE, f"closest {d:.2f}\" at {phi} deg"))
    checks += [
        (f"Monitor width {args.monitor_w}\" fits the unit ({inner_w:.2f}\")", args.monitor_w <= inner_w - 0.25, ""),
        (f"Monitor depth {args.monitor_d}\" fits the unit", args.monitor_d <= UNIT_D - UNIT_BACK - 1.0, ""),
        (f"Monitor height {args.monitor_h}\" fits under the marquee", monitor_top <= marquee_bottom - 0.25,
         f"monitor top z {monitor_top:.2f}, marquee from {marquee_bottom:.2f}"),
    ]

    arm = (z0 + z1) / 2 - PIVOT[1] + 2.0   # monitor sits high: bias the centre of mass up
    return {
        "checks": checks,
        "front_clearance": -reach_front,
        "arcade_height": z1,
        "arcade_height_topper": z1 + TOPPER_H,
        "deck_top": deck_top,
        "deck_reach": -min(p[0] for p in deck),
        "monitor_top": monitor_top,
        "marquee": (marquee_bottom, marquee_top),
        "storage_depth": D - T - (STORAGE_DOOR_Y + T),
        "lift": UNIT_WEIGHT * arm / (z1 - PIVOT[1]),
    }


# --- Parts -------------------------------------------------------------------
def cut_list():
    door_w = (INNER_W - 3 * 0.0625) / 2
    door_h = door_top() - (GLIDE + T) - 0.125
    store_d = D - T - (STORAGE_DOOR_Y + T)
    deck_w = UNIT_W - 2 * UNIT_WALL - 1.0
    bezel_l = unit_z()[1] - (DECK_HINGE_Z + DECK_DEPTH)
    return [
        ("Side panel", 2, '3/4" ply', 35.0, D, "pivot + plunger holes"),
        ("Back", 1, '3/4" ply', INNER_W, TOP_Z - GLIDE, "structural"),
        ("Top", 1, '3/4" ply', INNER_W, D - STORAGE_DOOR_Y, "fixed buffet top behind the slot"),
        ("Bottom", 1, '3/4" ply', INNER_W, store_d, "storage floor; open under the slot"),
        ("Shelf", SHELVES, '3/4" ply', INNER_W, store_d, "fixed shelves in dadoes"),
        ("Face rail", 1, '3/4" ply', INNER_W, round(TOP_Z - door_top(), 3), "fixed, above the storage doors"),
        ("Storage door", 2, '3/4" ply', round(door_h, 3), round(door_w, 3), "inset; only seen in arcade mode"),
        ("Unit back ('double doors')", 1, '1/2" ply', UNIT_L, UNIT_W, "walnut veneer, center groove, 2 dummy pulls"),
        ("Unit side", 2, '1/2" ply', UNIT_L, UNIT_D, f"{END_R:g}\" radius at the pivot end, {FOOT_R:g}\" at the other"),
        ("Unit end cap", 2, '1/2" ply', UNIT_W - 1.0, UNIT_D - UNIT_BACK, ""),
        ("Unit pivot doubler", 2, '3/4" hardwood', 7.0, UNIT_D - UNIT_BACK, "inside each side at the pivot end"),
        ("Bezel (screen + marquee)", 1, '1/4" black MDF', bezel_l, UNIT_W, "from the deck pocket up"),
        ("Deck pocket back", 1, '1/2" ply', UNIT_W - 1.0, DECK_DEPTH, f"{DECK_THICK:g}\" behind the front; 2.5\" holes where the sticks pass"),
        ("Deck pocket floor", 1, '3/4" hardwood', UNIT_W - 1.0, DECK_THICK, "hinge rail for the deck"),
        ("Deck control plate", 1, '1/2" ply', deck_w, DECK_DEPTH, "+ optional 1/8\" acrylic overlay"),
        ("Deck side", 2, '1/2" ply', DECK_DEPTH, DECK_THICK - 0.75, ""),
        ("Deck end", 2, '1/2" ply', deck_w - 1.0, DECK_THICK - 0.75, "hinge end + front lip (finger pull)"),
        ("Deck cover", 1, '1/4" ply', deck_w, DECK_DEPTH, "screw-on; the unit's lower front face when folded"),
        ("Marquee acrylic", 1, '1/8" acrylic', UNIT_W - 9.0, MARQUEE_H, "a 3\" speaker grille either side"),
        ("Outrigger bar", 2, '3/4" hardwood', 16.0, 1.5, "slides 12\" forward before flipping"),
    ]


# --- SVG ---------------------------------------------------------------------
SCALE = 9.0
MARGIN = 40


class Svg:
    def __init__(self, width_in, height_in, y_min, title):
        self.w = width_in * SCALE + 2 * MARGIN
        self.h = height_in * SCALE + 2 * MARGIN + 30
        self.y_min = y_min
        self.height_in = height_in
        self.items = [f'<text x="{MARGIN}" y="24" font-size="16" font-weight="bold">{title}</text>']

    def pt(self, p):
        return ((p[0] - self.y_min) * SCALE + MARGIN, (self.height_in - p[1]) * SCALE + MARGIN + 30)

    def poly(self, pts, fill="#d9c3a0", stroke="#5a4020", dash=None, width=1.2, opacity=1.0):
        s = " ".join(f"{x:.1f},{y:.1f}" for x, y in map(self.pt, pts))
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.items.append(f'<polygon points="{s}" fill="{fill}" fill-opacity="{opacity}" stroke="{stroke}" stroke-width="{width}"{d}/>')

    def line(self, a, b, stroke="#333", dash=None, width=1):
        (x1, y1), (x2, y2) = self.pt(a), self.pt(b)
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.items.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}"{d}/>')

    def arc(self, c, r_in, a0, a1, stroke="#c0392b", dash="4 3"):
        pts = [self.pt((c[0] + r_in * math.cos(math.radians(a)), c[1] + r_in * math.sin(math.radians(a))))
               for a in range(a0, a1 + 1, 3)]
        s = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        self.items.append(f'<polyline points="{s}" fill="none" stroke="{stroke}" stroke-dasharray="{dash}"/>')

    def dot(self, c, color="#c0392b"):
        x, y = self.pt(c)
        self.items.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{color}"/>')

    def text(self, p, s, size=11, anchor="start", color="#222"):
        x, y = self.pt(p)
        self.items.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}" fill="{color}">{s}</text>')

    def save(self, path):
        body = "\n".join(self.items)
        with open(path, "w") as f:
            f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w:.0f}" height="{self.h:.0f}" '
                    f'viewBox="0 0 {self.w:.0f} {self.h:.0f}" font-family="Helvetica, Arial, sans-serif">\n'
                    f'<rect width="100%" height="100%" fill="#fff"/>\n{body}\n</svg>\n')


def draw_carcass(s, outrigger=False):
    s.line((-48, 0), (60, 0), stroke="#888", width=2)
    s.poly([(0, GLIDE), (D, GLIDE), (D, H), (0, H)], fill="#efe3cf", stroke="#b49a72", dash="6 3")
    for name, r in fixed_parts().items():
        s.poly(r, fill="#c8a978" if "door" in name else "#d9c3a0")
    for y in (1.0, D - 1.0):
        s.poly(rect(y - 0.4, 0, y + 0.4, GLIDE), fill="#555", stroke="#333")
    if outrigger:
        s.poly(rect(-12.0, 0.1, 4.0, 0.85), fill="#8e6e3c", stroke="#4d3a1c")


def draw_unit(s, args, geo, phi, deck_down=False, ghost=False):
    m = lambda pts: at_progress(pts, phi)
    op = 0.3 if ghost else 1.0
    z0, z1 = unit_z()
    s.poly(m(unit_shell()), fill="#9fb7d4", stroke="#2c4a70", opacity=op)
    s.poly(m(rect(UNIT_Y0 + UNIT_D - UNIT_BACK, z0 + 0.6, UNIT_Y0 + UNIT_D, z1 - 0.6)),
           fill="#6b4226", stroke="#3e2615", opacity=op)
    deck, stick = deck_parts(deck_down)
    if not ghost:
        mq0, mq1 = geo["marquee"]
        s.poly(m(rect(UNIT_Y0 + DECK_THICK, DECK_HINGE_Z, UNIT_Y0 + DECK_THICK + 0.5, DECK_HINGE_Z + DECK_DEPTH)))
        s.poly(m(rect(UNIT_Y0 + 0.25, MONITOR_BOTTOM, UNIT_Y0 + 0.25 + args.monitor_d, geo["monitor_top"])),
               fill="#222", stroke="#000")
        s.poly(m(rect(UNIT_Y0, mq0, UNIT_Y0 + 1.0, mq1)), fill="#f1c40f", stroke="#a67c00")
    s.poly(m(deck), fill="#e2b07a", stroke="#7a4a14", opacity=op)
    s.poly(m(stick), fill="#c0392b", stroke="#7b1d14", opacity=op)
    s.dot(PIVOT)


def draw_front(outdir):
    """Front elevation of the closed cabinet: the unit back reads as double doors."""
    s = Svg(W + 16, H + 6, -8, "Closed - front view")
    s.line((-8, 0), (W + 8, 0), stroke="#888", width=2)
    s.poly(rect(0, GLIDE, W, H), fill="#5c3a24", stroke="#3e2615")
    s.poly(rect(T, H - T, W - T, H), fill="#7a4a2a", stroke="#3e2615")
    z0 = H - UNIT_L
    half = UNIT_W / 2
    x0 = T + 0.125
    for i in range(2):
        s.poly(rect(x0 + i * half + 0.06, z0, x0 + (i + 1) * half - 0.06, H - T - 0.06), fill="#8b5a3c", stroke="#3e2615")
        s.poly(rect(x0 + i * half + 1.2, z0 + 1.2, x0 + (i + 1) * half - 1.2, H - T - 1.2), fill="none", stroke="#5c3a24")
    for x in (x0 + half - 1.0, x0 + half + 1.0):
        s.poly(rect(x - 0.15, 18, x + 0.15, 23), fill="#c9a24a", stroke="#7a5f1f")
    for x in (1.0, W - 1.0):
        s.poly(rect(x - 0.5, 0, x + 0.5, GLIDE), fill="#555", stroke="#333")
    s.text((W / 2, H + 1.5), f'{W:.0f}" wide x {H:.0f}" tall - the "doors" are the back of the display unit', 11, "middle", "#2c3e50")
    s.save(os.path.join(outdir, "front_closed.svg"))


def drawings(args, geo, outdir):
    s = Svg(60, 40, -28, "Cabinet / buffet mode - side section (front at left, wall at right)")
    draw_carcass(s)
    draw_unit(s, args, geo, 0)
    s.text((-1, 20), "back of the display unit =", 11, "end")
    s.text((-1, 18.6), "the 'double doors'", 11, "end")
    s.text((15, 31), "control deck folded into", 11)
    s.text((15, 29.6), "the unit, sticks inside", 11)
    s.text((15, 15), "storage: 2 shelves", 11)
    s.text((15, 13.6), "behind inset doors", 11)
    s.line((-22, H), (-22, 0), stroke="#2c3e50")
    s.text((-22.5, H / 2), f'{H:.0f}"', 13, "end", "#2c3e50")
    s.line((0, -0.6), (D, -0.6), stroke="#2c3e50")
    s.text((D / 2, -1.9), f'{D}" deep x {W:.0f}" wide', 12, "middle", "#2c3e50")
    s.save(os.path.join(outdir, "cabinet_mode.svg"))

    top = geo["arcade_height_topper"]
    s = Svg(58, top + 4, -30, "Arcade mode - side section (deck folded down)")
    draw_carcass(s, outrigger=True)
    draw_unit(s, args, geo, 180, deck_down=True)
    z1 = geo["arcade_height"]
    s.poly(rect(UNIT_Y0, z1, UNIT_Y0 + UNIT_D, z1 + TOPPER_H), fill="#f9e79f", stroke="#a67c00", dash="5 3")
    lx = UNIT_Y0 + UNIT_D + 1
    s.text((lx, z1 + 2), f'optional topper -> {top:.0f}"', 11)
    s.text((lx, sum(geo["marquee"]) / 2), "marquee + speakers either side", 11)
    s.text((lx, (MONITOR_BOTTOM + geo["monitor_top"]) / 2), "monitor", 11)
    s.text((D + 1, 20), "storage: doors open", 11)
    s.text((D + 1, 18.6), "under the deck", 11)
    s.text((-geo["deck_reach"] - 1, geo["deck_top"] + 1.5), f'control deck {geo["deck_top"]:.1f}"', 11, "end")
    s.text((-geo["deck_reach"] - 1, geo["deck_top"]), "(folds down)", 11, "end")
    s.text((-12, 1.6), "outrigger pulled out", 10, "start", "#4d3a1c")
    s.line((-24, z1), (-24, 0), stroke="#2c3e50")
    s.text((-24.5, z1 / 2), f'{z1:.1f}"', 13, "end", "#2c3e50")
    s.save(os.path.join(outdir, "arcade_mode.svg"))

    r = math.hypot(UNIT_D / 2, UNIT_L - PIVOT_FROM_END)
    s = Svg(64, geo["arcade_height"] + 6, -48, "Flip sequence - display unit swings up out of the FRONT, deck stays folded")
    draw_carcass(s, outrigger=True)
    for phi in (0, 45, 90, 135):
        draw_unit(s, args, geo, phi, ghost=True)
    draw_unit(s, args, geo, 180)
    s.arc(PIVOT, r, 90, 270)
    s.line((0, 3), (-geo["front_clearance"], 3), stroke="#c0392b", width=1.5)
    s.text((-geo["front_clearance"] / 2, 4), f'keep ~{math.ceil(geo["front_clearance"])}" clear in front while flipping',
           12, "middle", "#c0392b")
    s.save(os.path.join(outdir, "flip_sequence.svg"))

    draw_front(outdir)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--monitor-w", type=float, default=24.1, help="monitor width incl. bezel (27\" 16:9 ~ 24.1)")
    ap.add_argument("--monitor-h", type=float, default=14.3, help="monitor height incl. bezel, no stand (27\" ~ 14.3)")
    ap.add_argument("--monitor-d", type=float, default=2.2, help="monitor thickness, no stand")
    args = ap.parse_args()

    geo = geometry(args)
    outdir = os.path.dirname(os.path.abspath(__file__))

    print("== Key dimensions ==")
    print(f"Closed (buffet):  {W:.0f}\" W x {D}\" D x {H:.0f}\" H")
    print(f"Arcade:           {W:.0f}\" W x {D}\" D (+{geo['deck_reach']:.1f}\" deck) x "
          f"{geo['arcade_height']:.1f}\" H ({geo['arcade_height_topper']:.0f}\" with topper)")
    print(f"Control deck top: {geo['deck_top']:.1f}\" from floor")
    print(f"Storage behind the slot: {geo['storage_depth']:.2f}\" deep x {INNER_W}\" wide, {SHELVES} shelves")
    print(f"Clearance needed in front while flipping: ~{math.ceil(geo['front_clearance'])}\" (none behind)")
    print(f"Lift force at the end of the unit when horizontal: ~{geo['lift']:.0f} lb")
    print()
    print("== Clearance checks (whole flip sampled every 1 deg) ==")
    ok = True
    for name, passed, detail in geo["checks"]:
        ok &= passed
        print(f"[{'OK ' if passed else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))
    print()
    print("== Cut list ==")
    print("| Part | Qty | Material | Length | Width | Notes |")
    print("|---|---|---|---|---|---|")
    for part, qty, mat, length, width, notes in cut_list():
        print(f"| {part} | {qty} | {mat} | {length:g}\" | {width:g}\" | {notes} |")

    drawings(args, geo, outdir)
    print()
    print("Wrote cabinet_mode.svg, arcade_mode.svg, flip_sequence.svg, front_closed.svg")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
