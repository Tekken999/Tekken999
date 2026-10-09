#!/usr/bin/env python3
"""Flip-up buffet arcade cabinet (front-flip): geometry checks, cut list and side-view drawings.

The screen tower and the control panel are one rigid unit. Closed, it hangs
upside down in a slot at the FRONT of the cabinet with the panel tucked inside;
it swings forward and up 180 degrees into arcade mode.

Usage:
    python3 design.py                                  # default 27" monitor
    python3 design.py --monitor-w 21.3 --monitor-h 12.6 --monitor-d 1.9

Everything is in inches. Side views use y = depth (0 = front face, grows toward
the wall) and z = height (0 = floor). Writes cabinet_mode.svg, arcade_mode.svg
and flip_sequence.svg next to this file and prints the checks and cut list.
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

SLOT_D = 4.25              # open tower slot at the front, y 0 -> 4.25
TOP_Z = H - T              # underside of the fixed top / lid (35.25)
STORAGE_TOP = 22.0         # top of the lower storage bay; the flip zone is above it

# --- Tower + control panel (one rigid unit) ----------------------------------
TOWER_W = INNER_W - 0.25   # 1/8" each side for nylon washers
TOWER_D = 3.75
TOWER_L = 34.0
TOWER_Y0 = 0.125           # front face (screen side in arcade mode)
TOWER_PIVOT_FROM_END = 2.5
TOWER_CORNER_R = 1.5       # round-over on the short-end corners (clears the lid edge)
TOWER_FOOT_R = 0.5         # round-over on the long-end corners (clears the bottom panel)
TOWER_WALL = 0.5
TOWER_BACK = 0.25
TOWER_BEZEL = 0.25
TOWER_PIVOT = (TOWER_Y0 + TOWER_D / 2, H - TOWER_PIVOT_FROM_END)  # (2.0, 33.5)
LOCK_OFFSET = 1.5          # index-plunger holes 1.5" either side of the pivot

PANEL_DEPTH = 7.5          # how far the control panel sticks out from the screen face
PANEL_H = 4.0              # control box height
PANEL_TOP = 39.0           # control surface height in arcade mode
GUSSET_H = 3.0             # end cheeks extend this far below the box (stiffness)
STICK_Y_FROM_FRONT = 3.0
STICK_H = 2.5              # ball top above the control plate

# --- Arcade-mode layout on the tower (z) -------------------------------------
MONITOR_BOTTOM = PANEL_TOP + 1.0
MARQUEE_H = 6.0
SPEAKER_MIN_H = 3.25       # 3" speakers between monitor and marquee
TOPPER_H = 5.0             # optional lift-off topper to hit 70"

CLEARANCE = 0.25           # minimum gap anywhere during the flip
TOWER_WEIGHT = 25.0        # lb with a 27" monitor, speakers, marquee
PANEL_WEIGHT = 8.0         # lb with controls


def rot(p, c, deg):
    """Rotate p about c by deg (positive = counter-clockwise in the side view: back goes up)."""
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


# --- Moving unit, defined in ARCADE orientation -------------------------------
def tower_z():
    z0 = TOWER_PIVOT[1] - TOWER_PIVOT_FROM_END
    return z0, z0 + TOWER_L


def tower_shell():
    """Tower outline with the short (bottom, in arcade mode) end corners rounded."""
    y0, y1 = TOWER_Y0, TOWER_Y0 + TOWER_D
    z0, z1 = tower_z()
    def corner(cy, cz, r, a0):
        return [(cy + r * math.cos(math.radians(a)), cz + r * math.sin(math.radians(a)))
                for a in range(a0, a0 + 91, 15)]
    r, f = TOWER_CORNER_R, TOWER_FOOT_R
    return (corner(y1 - f, z1 - f, f, 0) + corner(y0 + f, z1 - f, f, 90)
            + corner(y0 + r, z0 + r, r, 180) + corner(y1 - r, z0 + r, r, 270))


def panel_parts():
    y_front = TOWER_Y0 - PANEL_DEPTH
    box = rect(y_front, PANEL_TOP - PANEL_H, TOWER_Y0, PANEL_TOP)
    cheek = [(TOWER_Y0, PANEL_TOP - PANEL_H - GUSSET_H), (TOWER_Y0, PANEL_TOP - PANEL_H),
             (y_front + 1.0, PANEL_TOP - PANEL_H)]
    sy = y_front + STICK_Y_FROM_FRONT
    stick = rect(sy - 0.6, PANEL_TOP, sy + 0.6, PANEL_TOP + STICK_H)
    return box, cheek, stick


def moving_bodies():
    box, cheek, stick = panel_parts()
    return {"tower": tower_shell(), "panel": box, "cheek": cheek, "stick": stick}


def at_progress(pts, phi):
    """phi = 0 closed (buffet), 180 open (arcade). The tower's bottom swings forward."""
    return [rot(p, TOWER_PIVOT, -phi - 180) for p in pts]


# --- Fixed parts --------------------------------------------------------------
def fixed_parts():
    return {
        "bottom": rect(SLOT_D, GLIDE, D - T, GLIDE + T),
        "back": rect(D - T, GLIDE, D, TOP_Z),
        "top / lid": rect(SLOT_D, TOP_Z, D, H),
        "storage door": rect(SLOT_D, GLIDE + T, SLOT_D + T, STORAGE_TOP),
        "storage top": rect(SLOT_D + T, STORAGE_TOP - T, D - T, STORAGE_TOP),
    }


def rect_dist(p, r):
    (y0, z0), (y1, z1) = r[0], r[2]
    dy = max(y0 - p[0], 0, p[0] - y1)
    dz = max(z0 - p[1], 0, p[1] - z1)
    inside = y0 < p[0] < y1 and z0 < p[1] < z1
    return -1.0 if inside else math.hypot(dy, dz)


def sweep():
    """Closest approach of the moving unit to each fixed part over the whole flip."""
    pts = [p for body in moving_bodies().values() for p in densify(body)]
    fixed = fixed_parts()
    closest = {k: (math.inf, None) for k in fixed}
    reach_front, top_z = 0.0, 0.0
    for phi in range(0, 181):
        moved = at_progress(pts, phi)
        reach_front = min(reach_front, min(p[0] for p in moved))
        top_z = max(top_z, max(p[1] for p in moved))
        for name, r in fixed.items():
            d = min(rect_dist(p, r) for p in moved)
            if d < closest[name][0]:
                closest[name] = (d, phi)
    return closest, reach_front, top_z


def geometry(args):
    tz0, tz1 = tower_z()
    inner_tw = TOWER_W - 2 * TOWER_WALL
    inner_td = TOWER_D - TOWER_BACK - TOWER_BEZEL
    monitor_top = MONITOR_BOTTOM + args.monitor_h
    marquee_top = tz1 - 0.75
    marquee_bottom = marquee_top - MARQUEE_H
    closest, reach_front, top_z = sweep()

    stored = {k: at_progress(v, 0) for k, v in moving_bodies().items()}
    stored_bottom = min(p[1] for p in stored["tower"])
    stored_top = max(p[1] for v in stored.values() for p in v)
    stored_back = max(p[0] for v in stored.values() for p in v)

    checks = [
        ("Closed: unit fits under the top", stored_top <= TOP_Z - CLEARANCE or
         max(p[1] for p in stored["tower"]) <= H, f"highest panel point z {max(p[1] for k, v in stored.items() if k != 'tower' for p in v):.2f}"),
        ("Closed: tower clears the floor", stored_bottom >= GLIDE, f"tower bottom z {stored_bottom:.2f}"),
        ("Closed: panel clears the back", stored_back <= D - T - CLEARANCE, f"panel reaches y {stored_back:.2f}"),
    ]
    for name, (d, phi) in closest.items():
        checks.append((f"Flip clears {name}", d >= CLEARANCE, f"closest {d:.2f}\" at {phi} deg"))
    speaker_h = marquee_bottom - monitor_top
    checks += [
        (f"Monitor width {args.monitor_w}\" fits tower ({inner_tw:.2f}\")", args.monitor_w <= inner_tw - 0.25, ""),
        (f"Monitor depth {args.monitor_d}\" fits tower ({inner_td:.2f}\" incl. VESA plate)",
         args.monitor_d <= inner_td - 0.5, ""),
        (f"Monitor height {args.monitor_h}\" leaves room for speakers under the marquee",
         speaker_h >= SPEAKER_MIN_H, f"monitor top z {monitor_top:.2f}, {speaker_h:.2f}\" speaker band"),
    ]

    # Lift effort with the unit horizontal, lifting at the far end of the tower.
    arm_tower = (tz0 + tz1) / 2 - TOWER_PIVOT[1] + 3.0      # monitor sits high: bias COG up
    arm_panel = PANEL_TOP - PANEL_H / 2 - TOWER_PIVOT[1]       # panel is close to the pivot
    lift = (TOWER_WEIGHT * arm_tower + PANEL_WEIGHT * arm_panel) / (tz1 - TOWER_PIVOT[1])
    return {
        "checks": checks,
        "front_clearance": -reach_front,
        "sweep_top": top_z,
        "arcade_height": tz1,
        "arcade_height_topper": tz1 + TOPPER_H,
        "panel_overhang": PANEL_DEPTH - TOWER_Y0,
        "monitor_top": monitor_top,
        "speakers": (monitor_top, marquee_bottom),
        "marquee": (marquee_bottom, marquee_top),
        "lift": lift,
    }


# --- Parts -------------------------------------------------------------------
def cut_list():
    door_w = (INNER_W - 3 * 0.0625) / 2
    door_h = STORAGE_TOP - (GLIDE + T) - 0.125
    return [
        # (part, qty, thickness, L, W, notes)
        ("Side panel", 2, '3/4" ply', 35.0, D, "pivot + lock holes, see drawing"),
        ("Bottom", 1, '3/4" ply', INNER_W, D - T - SLOT_D, "storage floor; open under the tower slot"),
        ("Back", 1, '3/4" ply', INNER_W, TOP_Z - GLIDE, "structural, 2\" cable grommet"),
        ("Top / lid", 1, '3/4" ply', INNER_W, D - SLOT_D, "buffet top; piano-hinged at the back for storage access"),
        ("Storage top", 1, '3/4" ply', INNER_W, D - SLOT_D - 2 * T, f"top at z={STORAGE_TOP}; nothing above this line"),
        ("Storage door", 2, '3/4" ply', round(door_h, 3), round(door_w, 3), "inset; hidden when closed, kick panel when open"),
        ("Control plate", 1, '1/2" ply', TOWER_W, PANEL_DEPTH, "+ optional 1/8\" acrylic overlay"),
        ("Control box bottom", 1, '1/2" ply', TOWER_W - 1.0, PANEL_DEPTH - 0.5, "screw-on access panel"),
        ("Control box front", 1, '1/2" ply', TOWER_W - 1.0, PANEL_H - 1.0, ""),
        ("Control box cheek", 2, '1/2" ply', PANEL_DEPTH, PANEL_H + GUSSET_H, "ends: 4\" box + 3\" triangular gusset below, see drawing"),
        ("Panel mounting rail", 1, '3/4" hardwood', TOWER_W - 2 * TOWER_WALL, 3.0, "inside tower behind the panel; panel bolts through to it"),
        ("Tower side", 2, '1/2" ply', TOWER_L, TOWER_D, "1-1/2\" radius on short-end corners, 1/2\" on long end"),
        ("Tower end cap", 2, '1/2" ply', TOWER_W - 1.0, TOWER_D - 0.5, ""),
        ("Tower pivot doubler", 2, '3/4" hardwood', 6.0, TOWER_D - 0.5, "inside each tower side at the short end"),
        ("Tower back", 1, '1/4" ply', TOWER_L, TOWER_W, "buffet front face when closed; finish it nicely"),
        ("Tower bezel", 1, '1/4" black MDF/ply', TOWER_L, TOWER_W, "cutouts: screen, speakers, marquee"),
        ("Marquee acrylic", 1, '1/8" acrylic', TOWER_W - 1.0, MARQUEE_H, "print or vinyl behind"),
        ("Outrigger bar", 2, '3/4" hardwood', 14.0, 1.5, "slides 10\" forward before flipping"),
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
    s.line((-40, 0), (60, 0), stroke="#888", width=2)
    s.poly([(0, GLIDE), (D, GLIDE), (D, H), (0, H)], fill="#efe3cf", stroke="#b49a72", dash="6 3")
    for name, r in fixed_parts().items():
        s.poly(r, fill="#c8a978" if "door" in name else "#d9c3a0")
    for y in (1.0, D - 1.0):
        s.poly(rect(y - 0.4, 0, y + 0.4, GLIDE), fill="#555", stroke="#333")
    s.text((9, 12), "storage", 10, "middle")
    s.text((9, 10.6), "PC + amp", 10, "middle")
    if outrigger:
        s.poly(rect(-10.0, 0.1, 4.0, 0.85), fill="#8e6e3c", stroke="#4d3a1c")


def draw_unit(s, args, geo, phi, ghost=False):
    tz0, tz1 = tower_z()
    y0 = TOWER_Y0
    mq0, mq1 = geo["marquee"]
    sp0, sp1 = geo["speakers"]
    m = lambda pts: at_progress(pts, phi)
    op = 0.3 if ghost else 1.0
    box, cheek, stick = panel_parts()
    s.poly(m(tower_shell()), fill="#9fb7d4", stroke="#2c4a70", opacity=op)
    s.poly(m(cheek), fill="#e2b07a", stroke="#7a4a14", opacity=op)
    s.poly(m(box), fill="#e2b07a", stroke="#7a4a14", opacity=op)
    s.poly(m(stick), fill="#c0392b", stroke="#7b1d14", opacity=op)
    if not ghost:
        s.poly(m(rect(y0 + TOWER_BEZEL, MONITOR_BOTTOM, y0 + TOWER_BEZEL + args.monitor_d, geo["monitor_top"])), fill="#222", stroke="#000")
        s.poly(m(rect(y0 + TOWER_BEZEL, sp0 + 0.1, y0 + 2.0, sp1 - 0.1)), fill="#6c6c6c", stroke="#333")
        s.poly(m(rect(y0, mq0, y0 + 1.0, mq1)), fill="#f1c40f", stroke="#a67c00")
    s.dot(TOWER_PIVOT)


def drawings(args, geo, outdir):
    s = Svg(56, 40, -24, "Cabinet / buffet mode - side section (front at left, wall at right)")
    draw_carcass(s)
    draw_unit(s, args, geo, 0)
    s.text((-1, 20), "back of the tower =", 11, "end")
    s.text((-1, 18.6), "buffet front face", 11, "end")
    s.text((15, 30), "control panel rides", 11)
    s.text((15, 28.6), "upside down inside,", 11)
    s.text((15, 27.2), "sticks pointing down", 11)
    s.text((15, 33.5), "top lid", 11)
    s.line((-18, H), (-18, 0), stroke="#2c3e50")
    s.text((-18.5, H / 2), f'{H:.0f}"', 13, "end", "#2c3e50")
    s.line((0, -0.6), (D, -0.6), stroke="#2c3e50")
    s.text((D / 2, -1.9), f'{D}" deep x {W:.0f}" wide', 12, "middle", "#2c3e50")
    s.save(os.path.join(outdir, "cabinet_mode.svg"))

    top = geo["arcade_height_topper"]
    s = Svg(52, top + 4, -24, "Arcade mode - side section")
    draw_carcass(s, outrigger=True)
    draw_unit(s, args, geo, 180)
    tz1 = geo["arcade_height"]
    s.poly(rect(TOWER_Y0, tz1, TOWER_Y0 + TOWER_D, tz1 + TOPPER_H), fill="#f9e79f", stroke="#a67c00", dash="5 3")
    lx = TOWER_Y0 + TOWER_D + 1
    s.text((lx, tz1 + 2), f'optional topper -> {top:.0f}"', 11)
    s.text((lx, sum(geo["marquee"]) / 2), "marquee", 11)
    s.text((lx, sum(geo["speakers"]) / 2), "speakers", 11)
    s.text((lx, (MONITOR_BOTTOM + geo["monitor_top"]) / 2), "monitor", 11)
    s.text((-PANEL_DEPTH - 1, PANEL_TOP + 1.5), f'control panel {PANEL_TOP:.0f}"', 11, "end")
    s.text((-PANEL_DEPTH - 1, PANEL_TOP), "(fixed to tower)", 11, "end")
    s.text((-10, 1.6), "outrigger pulled out", 10, "start", "#4d3a1c")
    s.line((-18, tz1), (-18, 0), stroke="#2c3e50")
    s.text((-18.5, tz1 / 2), f'{tz1:.0f}"', 13, "end", "#2c3e50")
    s.save(os.path.join(outdir, "arcade_mode.svg"))

    r = math.hypot(TOWER_D / 2, TOWER_L - TOWER_PIVOT_FROM_END)
    s = Svg(60, geo["sweep_top"] + 6, -44, "Flip sequence - screen + panel swing up out the FRONT (wall side stays put)")
    draw_carcass(s, outrigger=True)
    for phi in (0, 45, 90, 135):
        draw_unit(s, args, geo, phi, ghost=True)
    draw_unit(s, args, geo, 180)
    s.arc(TOWER_PIVOT, r, 90, 270)
    s.line((0, 3), (-geo["front_clearance"], 3), stroke="#c0392b", width=1.5)
    s.text((-geo["front_clearance"] / 2, 4), f'keep ~{math.ceil(geo["front_clearance"])}" clear in front while flipping', 12, "middle", "#c0392b")
    s.save(os.path.join(outdir, "flip_sequence.svg"))


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
    print(f"Arcade:           {W:.0f}\" W x {D}\" D (+{geo['panel_overhang']:.1f}\" control panel) x "
          f"{geo['arcade_height']:.0f}\" H ({geo['arcade_height_topper']:.0f}\" with topper)")
    print(f"Control panel top: {PANEL_TOP:.1f}\" from floor")
    print(f"Clearance needed in front while flipping: ~{math.ceil(geo['front_clearance'])}\" "
          f"(nothing behind - it can stay against the wall)")
    print(f"Lift force at the end of the tower when horizontal: ~{geo['lift']:.0f} lb")
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
    print("Wrote cabinet_mode.svg, arcade_mode.svg, flip_sequence.svg")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
