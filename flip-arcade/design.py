#!/usr/bin/env python3
"""Flip-up buffet arcade cabinet: geometry checks, cut list and side-view drawings.

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

DOOR_TOP = 31.25          # top of inset doors (1/4" reveal under control box)
PARTITION_Y = 8.75        # front face of partition (back of front compartment)
PARTITION_TOP = 28.5
DECK_TOP = 28.5           # fixed deck under the stored control box

# --- Tower (screen + speakers + marquee) -------------------------------------
TOWER_W = INNER_W - 0.25   # 1/8" each side for nylon washers
TOWER_D = 3.75
TOWER_L = 34.0
TOWER_Y0 = PARTITION_Y + T + 0.125     # 9.625, front face (screen side in arcade mode)
TOWER_PIVOT_FROM_END = 2.5             # pivot is 2.5" from the "short" end
TOWER_CORNER_R = 1.0                   # round-over on the 4 short-end corners
TOWER_WALL = 0.5                       # 1/2" Baltic birch
TOWER_BACK = 0.25
TOWER_BEZEL = 0.25
TOWER_PIVOT = (TOWER_Y0 + TOWER_D / 2, H - TOWER_PIVOT_FROM_END)  # (11.5, 33.5)
LOCK_OFFSET = 1.5          # index-plunger holes 1.5" either side of the pivot

# --- Control box -------------------------------------------------------------
BOX_DEPTH = 8.0
BOX_H = 4.5
BOX_W = INNER_W - 1.0      # 1/2" gap each side for the folding braces
BOX_PIVOT = (0.75, H - 0.75)  # (0.75, 35.25)
STICK_ABOVE_PLATE = 2.5    # ball-top height above the control plate
STICK_MAX_Y_STORED = 6.0   # keep sticks at least 2" from the box's back edge (stored)

# --- Arcade-mode layout on the tower (z, arcade orientation) ----------------
SPEAKER_BAND = (36.0, 40.5)
MONITOR_BOTTOM = 41.0
MARQUEE_H = 6.0
TOPPER_H = 5.0             # optional lift-off topper to hit 70"


def rot(p, c, deg):
    """Rotate point p about c by deg (positive = back part of the body goes up)."""
    a = math.radians(deg)
    dy, dz = p[0] - c[0], p[1] - c[1]
    return (c[0] + dy * math.cos(a) - dz * math.sin(a),
            c[1] + dy * math.sin(a) + dz * math.cos(a))


def rect(y0, z0, y1, z1):
    return [(y0, z0), (y1, z0), (y1, z1), (y0, z1)]


def tower_arcade_z():
    z0 = TOWER_PIVOT[1] - TOWER_PIVOT_FROM_END
    return z0, z0 + TOWER_L


def geometry(args):
    py, pz = TOWER_PIVOT
    tz0, tz1 = tower_arcade_z()
    half = TOWER_D / 2
    r_tower_end = math.hypot(half - TOWER_CORNER_R, TOWER_PIVOT_FROM_END - TOWER_CORNER_R) + TOWER_CORNER_R
    r_tower_long = math.hypot(half, TOWER_L - TOWER_PIVOT_FROM_END)

    by, bz = BOX_PIVOT
    box_far = math.hypot(BOX_DEPTH - by, bz - (H - BOX_H))
    box_front_corner = math.hypot(by, bz - (H - BOX_H))
    stick_tip_z = H - BOX_H - STICK_ABOVE_PLATE
    stick_r = math.hypot(STICK_MAX_Y_STORED - by, bz - stick_tip_z)

    inner_tw = TOWER_W - 2 * TOWER_WALL
    inner_td = TOWER_D - TOWER_BACK - TOWER_BEZEL
    monitor_top = MONITOR_BOTTOM + args.monitor_h
    marquee_top = tz1 - 1.0
    marquee_bottom = marquee_top - MARQUEE_H

    stored_tower_bottom = H - TOWER_L
    checks = [
        ("Tower clears stretcher when stored (bottom z > 1.75)",
         stored_tower_bottom > GLIDE + T, f"tower bottom at z={stored_tower_bottom:.2f}"),
        ("Tower end sweep clears partition top",
         PARTITION_TOP < pz - r_tower_end, f"sweep r={r_tower_end:.2f} -> lowest z {pz - r_tower_end:.2f}"),
        ("Tower end sweep clears stored control box",
         BOX_DEPTH < py - r_tower_end, f"box back y={BOX_DEPTH} vs sweep y {py - r_tower_end:.2f}"),
        ("Control box sweep clears stored tower",
         by + max(box_far, stick_r) < TOWER_Y0, f"reach y {by + max(box_far, stick_r):.2f} vs tower y {TOWER_Y0}"),
        ("Control box corner clears door tops",
         DOOR_TOP < bz - box_front_corner, f"corner dips to z {bz - box_front_corner:.2f}"),
        ("Stored stick tips clear deck",
         stick_tip_z >= DECK_TOP + 0.25, f"tips at z {stick_tip_z:.2f}, deck {DECK_TOP}"),
        (f"Monitor width {args.monitor_w}\" fits tower ({inner_tw:.2f}\")",
         args.monitor_w <= inner_tw - 0.25, ""),
        (f"Monitor depth {args.monitor_d}\" fits tower ({inner_td:.2f}\" incl. VESA plate)",
         args.monitor_d <= inner_td - 0.5, ""),
        (f"Monitor height {args.monitor_h}\" fits under marquee",
         monitor_top <= marquee_bottom - 0.5, f"monitor top z {monitor_top:.2f}, marquee from {marquee_bottom:.2f}"),
    ]
    return {
        "checks": checks,
        "r_tower_long": r_tower_long,
        "wall_clearance": py + r_tower_long - D,
        "arcade_height": tz1,
        "arcade_height_topper": tz1 + TOPPER_H,
        "panel_height": 2 * bz - (H - BOX_H),
        "panel_overhang": -(2 * by - BOX_DEPTH),
        "monitor_top": monitor_top,
        "marquee": (marquee_bottom, marquee_top),
    }


# --- Parts -------------------------------------------------------------------
def cut_list():
    door_w = (INNER_W - 3 * 0.0625) / 2
    door_h = DOOR_TOP - (GLIDE + 0.0625)
    return [
        # (part, qty, thickness, L, W, notes)
        ("Side panel", 2, '3/4" ply', 35.0, D, "pivot + lock holes, see drawing"),
        ("Bottom", 1, '3/4" ply', INNER_W, PARTITION_Y - T, "front compartment floor"),
        ("Partition", 1, '3/4" ply', INNER_W, PARTITION_TOP - (GLIDE + T), "structural back of compartment, 2\" cable grommet"),
        ("Deck", 1, '3/4" ply', INNER_W, PARTITION_Y - T, f"top at z={DECK_TOP}, vent holes"),
        ("Rear stretcher", 1, '3/4" ply', INNER_W, 3.5, "flat under the tower channel"),
        ("Door", 2, '3/4" ply', round(door_h, 3), round(door_w, 3), "inset, 1/16\" gaps"),
        ("Control box lid (buffet top)", 1, '3/4" ply', BOX_W, BOX_DEPTH, "show face; becomes panel underside"),
        ("Control plate", 1, '1/2" ply', BOX_W - 1.0, BOX_DEPTH - 1.0, "+ optional 1/8\" acrylic overlay"),
        ("Control box front/back", 2, '1/2" ply', BOX_W, BOX_H - T, "front is the 'drawer face'"),
        ("Control box ends", 2, '1/2" ply', BOX_DEPTH - 1.0, BOX_H - T, "3/8\" pivot bushing in left/right"),
        ("Tower side", 2, '1/2" ply', TOWER_L, TOWER_D, "1\" radius on short-end corners"),
        ("Tower end cap", 2, '1/2" ply', TOWER_W - 1.0, TOWER_D - 0.5, ""),
        ("Tower pivot doubler", 2, '3/4" hardwood', 6.0, TOWER_D - 0.5, "inside each tower side at the short end"),
        ("Tower back", 1, '1/4" ply', TOWER_L, TOWER_W, "vent slots behind monitor"),
        ("Tower bezel", 1, '1/4" black MDF/ply', TOWER_L, TOWER_W, "cutouts: speakers, screen, marquee"),
        ("Marquee acrylic", 1, '1/8" acrylic', TOWER_W - 1.0, MARQUEE_H, "print or vinyl behind"),
        ("Outrigger bar", 2, '3/4" hardwood', 12.0, 1.5, "slides 9\" forward in arcade mode"),
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


def tower_parts_arcade(args, geo):
    """Tower outline and front features in arcade orientation."""
    tz0, tz1 = tower_arcade_z()
    y0, y1 = TOWER_Y0, TOWER_Y0 + TOWER_D
    shell = rect(y0, tz0, y1, tz1)
    mon = rect(y0 + TOWER_BEZEL, MONITOR_BOTTOM, y0 + TOWER_BEZEL + args.monitor_d, geo["monitor_top"])
    spk = rect(y0 + TOWER_BEZEL, SPEAKER_BAND[0], y0 + 2.0, SPEAKER_BAND[1])
    mq0, mq1 = geo["marquee"]
    mq = rect(y0, mq0, y0 + 1.0, mq1)
    return shell, mon, spk, mq


def box_parts_stored():
    z0 = H - BOX_H
    shell = rect(0, z0, BOX_DEPTH, H)
    stick = [(4.0, z0), (4.0, z0 - STICK_ABOVE_PLATE + 0.6), (4.6, z0 - STICK_ABOVE_PLATE + 0.3),
             (4.0, z0 - STICK_ABOVE_PLATE), (3.4, z0 - STICK_ABOVE_PLATE + 0.3), (4.0, z0 - STICK_ABOVE_PLATE + 0.6)]
    return shell, stick


def draw_carcass(s):
    s.line((-12, 0), (60, 0), stroke="#888", width=2)
    side = [(0, GLIDE), (D, GLIDE), (D, H), (0, H)]
    s.poly(side, fill="#efe3cf", stroke="#b49a72", dash="6 3")
    s.poly(rect(0, GLIDE + 0.0625, T, DOOR_TOP), fill="#c8a978")
    s.poly(rect(T, GLIDE, PARTITION_Y, GLIDE + T))
    s.poly(rect(PARTITION_Y, GLIDE, PARTITION_Y + T, PARTITION_TOP))
    s.poly(rect(T, DECK_TOP - T, PARTITION_Y, DECK_TOP))
    s.poly(rect(PARTITION_Y + T + 0.25, GLIDE, PARTITION_Y + T + 3.75, GLIDE + T))
    for y in (1.0, D - 1.0):
        s.poly(rect(y - 0.4, 0, y + 0.4, GLIDE), fill="#555", stroke="#333")
    s.text((4.5, 14), "storage /", 10, "middle")
    s.text((4.5, 12.6), "PC + amp", 10, "middle")


def draw_tower(s, args, geo, deg, ghost=False):
    c = TOWER_PIVOT
    shell, mon, spk, mq = tower_parts_arcade(args, geo)
    k = 180 - deg  # parts are defined in arcade orientation; deg=0 is stored
    r = lambda pts: [rot(p, c, -k) for p in pts]
    op = 0.35 if ghost else 1.0
    s.poly(r(shell), fill="#9fb7d4", stroke="#2c4a70", opacity=op)
    if not ghost:
        s.poly(r(mon), fill="#222", stroke="#000")
        s.poly(r(spk), fill="#6c6c6c", stroke="#333")
        s.poly(r(mq), fill="#f1c40f", stroke="#a67c00")
    s.dot(c)


def draw_box(s, deg, ghost=False):
    c = BOX_PIVOT
    shell, stick = box_parts_stored()
    r = lambda pts: [rot(p, c, deg) for p in pts]
    op = 0.35 if ghost else 1.0
    s.poly(r(shell), fill="#e2b07a", stroke="#7a4a14", opacity=op)
    s.poly(r(stick), fill="#c0392b", stroke="#7b1d14", opacity=op)
    s.dot(c, "#7a4a14")


def drawings(args, geo, outdir):
    # Cabinet (buffet) mode
    s = Svg(56, 40, -18, "Cabinet / buffet mode - side section (front at left, wall at right)")
    draw_carcass(s)
    draw_tower(s, args, geo, 0)
    draw_box(s, 0)
    s.text((18.5, 20), "tower hangs upside-down", 11)
    s.text((18.5, 18.6), "in rear channel, screen", 11)
    s.text((18.5, 17.2), "faces the wall", 11)
    s.text((-1, 33.5), "control box =", 11, "end")
    s.text((-1, 32.1), "'drawer' + table top", 11, "end")
    s.text((-1, 16), "2 inset doors", 11, "end")
    s.line((-8, H), (-8, 0), stroke="#2c3e50")
    s.text((-8.5, H / 2), f'{H:.0f}"', 13, "end", "#2c3e50")
    s.line((0, -1.6 + GLIDE), (D, -1.6 + GLIDE), stroke="#2c3e50")
    s.text((D / 2, -2.9 + GLIDE), f'{D}" deep x {W:.0f}" wide', 12, "middle", "#2c3e50")
    s.save(os.path.join(outdir, "cabinet_mode.svg"))

    # Arcade mode
    top = geo["arcade_height_topper"]
    s = Svg(52, top + 4, -18, "Arcade mode - side section")
    draw_carcass(s)
    draw_tower(s, args, geo, 180)
    draw_box(s, 180)
    tz1 = geo["arcade_height"]
    s.poly(rect(TOWER_Y0, tz1, TOWER_Y0 + TOWER_D, tz1 + TOPPER_H), fill="#f9e79f", stroke="#a67c00", dash="5 3")
    s.text((TOWER_Y0 + TOWER_D + 1, tz1 + 2), f'optional topper -> {top:.0f}"', 11)
    s.text((TOWER_Y0 + TOWER_D + 1, (MONITOR_BOTTOM + geo["monitor_top"]) / 2), "monitor", 11)
    s.text((TOWER_Y0 + TOWER_D + 1, sum(geo["marquee"]) / 2), "marquee", 11)
    s.text((TOWER_Y0 + TOWER_D + 1, sum(SPEAKER_BAND) / 2), "speakers", 11)
    s.text((-geo["panel_overhang"], geo["panel_height"] + 1.2), f'control panel top {geo["panel_height"]:.1f}"', 11)
    # folding brace
    s.line((6.0, 30.0), (-3.0, 34.5), stroke="#16a085", width=3)
    s.text((-4, 31), "folding brace", 10, "end", "#16a085")
    # outrigger
    s.poly(rect(-9.25, 0.1, 2.75, 0.85), fill="#8e6e3c", stroke="#4d3a1c")
    s.text((-9.25, 1.6), "outrigger pulled out", 10, "start", "#4d3a1c")
    s.line((-13, tz1), (-13, 0), stroke="#2c3e50")
    s.text((-13.5, tz1 / 2), f'{tz1:.0f}"', 13, "end", "#2c3e50")
    s.save(os.path.join(outdir, "arcade_mode.svg"))

    # Flip sequence (tower swing envelope)
    reach = geo["r_tower_long"] + TOWER_PIVOT[0]
    s = Svg(reach + 18, geo["arcade_height"] + 6, -12, "Flip sequence - tower swings out the BACK, needs wall clearance")
    draw_carcass(s)
    draw_box(s, 0)
    for deg in (0, 45, 90, 135):
        draw_tower(s, args, geo, deg, ghost=True)
    draw_tower(s, args, geo, 180)
    s.arc(TOWER_PIVOT, geo["r_tower_long"], -90, 90)
    s.line((D, 3), (reach, 3), stroke="#c0392b", width=1.5)
    s.text(((D + reach) / 2, 4), f'keep ~{math.ceil(geo["wall_clearance"])}" clear behind cabinet while flipping', 12, "middle", "#c0392b")
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
    print(f"Control panel top: {geo['panel_height']:.1f}\" from floor")
    print(f"Wall clearance needed while flipping: ~{math.ceil(geo['wall_clearance'])}\"")
    print()
    print("== Clearance checks ==")
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
