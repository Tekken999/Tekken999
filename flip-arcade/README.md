# Flip-Up Buffet Arcade Cabinet

A free-standing cabinet that looks like a small buffet/sideboard when closed and
flips up into a full-height arcade cabinet. **The screen and control panel are
one piece.** It swings up out of the front in a single motion, so the cabinet
can stay against the wall.

| Mode | Target (given) | This design |
|---|---|---|
| Cabinet / buffet (closed) | 36 × 29 × 13.5 in (91.4 × 73.7 × 34.3 cm) | **36 H × 29 W × 13.5 D in** |
| Arcade (open) | 70 × 28 × 14 in (177.8 × 71.1 × 35.6 cm) | **65 H** (70 with the lift-off topper) × 29 W × 13.5 D + 7.4 in control panel overhang |
| Weight | ~100 lb / 45 kg | ~90–100 lb with PC and ballast |

| Closed | Open | Flipping |
|---|---|---|
| ![cabinet mode](cabinet_mode.svg) | ![arcade mode](arcade_mode.svg) | ![flip sequence](flip_sequence.svg) |

All drawings are side sections: front on the left, wall on the right. The
dashed outline is the side panel.

---

## How it folds

**The flip unit** is the screen tower (monitor, speakers, marquee) with the
control panel fixed to its face.

- **Closed:** the tower hangs **upside down** in a 4-1/4 in slot at the
  **front** of the cabinet. Its back panel is the buffet's front face, and the
  screen faces into the cabinet where it's protected. The control panel sticks
  backward into the cabinet, upside down, with the sticks pointing at the floor
  and out of harm's way.
- **Flipping:** a 1/2 in pivot bolt sits 2.5 in below the top of the tower.
  You pull the bottom of the tower out toward you and walk it up over the top.
  It turns 180° and stands upright in the same slot. The control panel comes
  around with it and ends up in front of the screen, **39 in off the floor**,
  controls up.
- **Locking:** two spring index plungers per side lock the unit closed or open.
- **Outrigger feet:** two hardwood bars under the cabinet slide 10 in forward
  before you flip, and stay out while you play. The flip unit swings out the
  front, and players lean on the panel, so these keep the cabinet from tipping
  forward.

Behind the slot:

- **Lid:** the fixed top is piano-hinged at the back, so it doubles as a lid
  for reaching the storage.
- **Storage:** the bay below 22 in holds the PC, amp and power strip. Its inset
  doors are hidden behind the tower when closed and become the kick panel when
  open.
- **Flip zone:** the space between 22 in and the lid is where the control panel
  swings through. **Keep it empty.**

### Height

The tower has to fit inside the 36 in box when closed, and 2.5 in of it stays
inside the side panels when it's up for rigidity. That makes it 65 in tall
open. A 5 in lift-off marquee topper (it stores in the cabinet) brings it to
70 in.

### Things to know before you build

- **You need about 30 in clear in front of the cabinet** to flip it, and
  nothing behind it. Leave it against the wall.
- **Always pull the outriggers out before flipping.** When the unit is
  horizontal, its weight is about a foot in front of the cabinet.
- Lifting takes about **15 lb at the end of the tower** when it's horizontal.
  The flip unit weighs about 33 lb with a 27 in monitor and the controls.
  Do the first few flips with two people.
- **Max screen: 27 in 16:9.** The tower interior is 26.25 in wide and 3.25 in
  deep (including the VESA bracket).
- **Strap it to the wall** like any tall furniture. Put 15–20 lb of ballast low
  in the back of the storage bay.

---

## Your screen (fill in later)

Measure the monitor **without its stand**, then run:

```bash
python3 design.py --monitor-w <width incl. bezel> --monitor-h <height incl. bezel> --monitor-d <thickness>
```

The script:

- prints the key dimensions and the cut list;
- checks that the flip unit clears every fixed part at every degree of the
  swing (at least 1/4 in everywhere);
- redraws the three SVGs.

The defaults assume a typical 27 in monitor (24.1 × 14.3 × 2.2 in). Also
write down:

- [ ] Width × height × thickness (no stand): ____ × ____ × ____
- [ ] VESA pattern (75 / 100): ____
- [ ] Weight: ____
- [ ] Which side the ports exit (back-down is best): ____
- [ ] Power brick: internal / external

| Diagonal (16:9) | W × H (approx.) | Fits? |
|---|---|---|
| 22 in | 19.6 × 11.6 | yes |
| 24 in | 21.3 × 12.6 | yes |
| 27 in | 24.1 × 14.3 | yes (max) |
| 32 in | 28.5 × 16.8 | no |

---

## Key dimensions (inches)

Coordinates: **y** = distance back from the front face, **z** = height from
the floor.

| Item | Value |
|---|---|
| Leveling glides | 1 in (carcass sits at z = 1) |
| Side panels | 13.5 D × 35 H, 3/4 ply, 27.5 in apart |
| Tower slot | y 0 → 4.25, open at the front, top and bottom |
| **Tower pivot** | **y = 2.0, z = 33.5**, 1/2 in bolt through both side panels |
| Lock plungers | y = 2.0 at z = 32.0 and z = 35.0 (both sides) |
| Tower closed / open | z 2 → 36 / z 31 → 65 |
| Control panel (open) | top at z = 39, sticks out 7.4 in from the screen face |
| Control panel (closed) | upside down behind the tower, z 28 → 32, stick tips down to about z 25.5 |
| Lid | y 4.25 → 13.5, top at z = 36, piano-hinged on the back panel |
| Storage bay | y 5 → 12.75, floor at z = 1.75, top at z = 22 |
| Storage doors | inset at y 4.25, z 1.75 → 22 |
| Flip zone (keep clear) | everything above z = 22 behind the tower |
| Arcade layout on the tower | panel z 35–39, monitor from z 40, speakers above it, marquee z 58–64 |

The tightest spots during the flip:

- the tower's rounded top corner passes the lid's front edge with about 0.3 in
  to spare;
- the tower clears the storage doors by about 0.37 in.

**If you change any dimension, change it in `design.py` and re-run it.**

---

## Cut list

Generated by `design.py` for the default 27 in monitor.

### 3/4" plywood (one 4×8 sheet)
| Part | Qty | Size | Notes |
|---|---|---|---|
| Side panel | 2 | 35 × 13-1/2 | Drill as a clamped pair so the pivot and plunger holes line up |
| Back | 1 | 27-1/2 × 34-1/4 | Structural; 2" cable grommet |
| Bottom | 1 | 27-1/2 × 8-1/2 | Storage floor only; there's no floor under the tower slot |
| Top / lid | 1 | 27-1/2 × 9-1/4 | Buffet top, piano-hinged to the back panel |
| Storage top | 1 | 27-1/2 × 7-3/4 | Top surface at 22"; nothing goes above it |
| Storage door | 2 | 20-1/8 × 13-21/32 | Inset. Cut last, to fit the opening |

### 1/2" Baltic birch (one 5×5 sheet)
| Part | Qty | Size | Notes |
|---|---|---|---|
| Tower side | 2 | 34 × 3-3/4 | 1-1/2" radius on the two corners at the pivot end, 1/2" at the other end |
| Tower end cap | 2 | 26-1/4 × 3-1/4 | |
| Control plate | 1 | 27-1/4 × 7-1/2 | Buttons and sticks mount here |
| Control box bottom | 1 | 26-1/4 × 7 | Screw on so you can reach the wiring |
| Control box front | 1 | 26-1/4 × 3 | |
| Control box cheek | 2 | 7-1/2 × 7 | Box ends: 4" box with a 3" triangular gusset below (see `arcade_mode.svg`) |
| Topper (optional) | 1 set | 27-1/4 × 5 × 3-3/4 box | Lift-off, sits on 2 dowels |

### 1/4" sheet
| Part | Qty | Size | Notes |
|---|---|---|---|
| Tower back | 1 | 34 × 27-1/4 | **This is the buffet front when closed.** Use nice ply or veneer and add a finger pull near the bottom |
| Tower bezel | 1 | 34 × 27-1/4 | Black MDF; cutouts for screen, speakers and marquee |

### Hardwood and acrylic
| Part | Qty | Size | Notes |
|---|---|---|---|
| Panel mounting rail | 1 | 26-1/4 × 3 × 3/4 | Inside the tower behind the panel; the panel bolts through the bezel into it |
| Tower pivot doubler | 2 | 6 × 3-1/4 × 3/4 | Glued inside each tower side at the pivot end |
| Outrigger bar | 2 | 14 × 1-1/2 × 3/4 | Anti-tip feet |
| Marquee | 1 | 26-1/4 × 6 × 1/8 acrylic | |

**Before you cut:**
- **Measure your plywood.** "3/4" plywood is often 23/32".
- **Cut the tower parts and storage doors last,** sized from the real gap
  between the assembled side panels.
- **Check the control box against your control kit.** It's 3 in deep inside,
  which fits Sanwa JLF-style sticks. Check the below-panel depth on anything
  else.

---

## Hardware and parts list

**Pivot and locks**
- 2× 1/2 in-13 × 3 in hex bolts (tower pivot) + nylon-insert lock nuts + fender washers
- 4× 1/2 in ID flanged bronze bushings (2 in the side panels, 2 in the tower doublers)
- 4× 1/2 in UHMW or nylon washers (between the tower and the side panels)
- 4× 1/2 in spring index plungers with pull ring and rest position (2 per side)
- 4× 1/2 in ID steel sleeves for the plunger holes in the tower doublers
- 2× 3/16 in steel plates, about 2 × 6 in, on the outside of each side panel around the pivot and plungers
- 4× 1/4 in-20 carriage bolts + T-nuts (control panel to mounting rail)
- 2× 4 in steel corner braces inside the control box cheeks

**Carcass**
- 4× 1 in adjustable leveling glides + T-nuts
- 27 in piano hinge + lid stay (for the top)
- 4× inset Euro hinges + 2 magnetic catches (storage doors)
- 1 recessed finger pull (bottom of the tower back, to start the flip)
- UHMW tape for the outrigger channels, stop pins, felt pads
- Furniture anti-tip wall strap
- Wood glue, 1-1/4 in pocket screws, 1 in brads, edge banding

**Electronics**
- Monitor, 27 in max, VESA mount, with a low-profile flat VESA plate
- 2-player control kit: 2 sticks + 16–20 × 30 mm buttons + USB encoder(s)
- 2× 3 in full-range speakers + small 2×15 W amp
- 12 V LED strip + supply for the marquee
- Computer (your slim PC, mini PC, Pi 5 or console) in the storage bay
- Switched power strip, slim flexible HDMI cable (at least 6 ft), spiral wrap, 2 in grommet

---

## Cable routing through the flip

Everything on the flip unit (monitor, speakers, marquee, and the USB from the
control panel) leaves it in **one bundle, near the pivot**. That way the
bundle only twists instead of stretching.

1. The panel's USB goes straight back through a hole in the tower face behind
   the control box, into the tower.
2. The whole bundle leaves the tower through a 1.5 in hole in the tower face,
   **1 in below the pivot, between the panel gussets**. It's hidden under the
   panel when open.
3. Leave an **18 in slack loop** in spiral wrap, then pass it into the storage
   bay through a 2 in grommet at the front of the storage top.
4. Cycle the flip 10–20 times with the bundle in place before closing
   everything up. Make sure it never catches on the lid edge or the storage
   top.

---

## Build order

1. **Mock it up first.** Use cardboard or scrap MDF for the side panels and the
   tower-plus-panel unit. Check the swing and the 1/4–3/8 in gaps *before*
   cutting good plywood.
2. **Side panels.** Clamp them as a pair and drill the pivot hole and the two
   plunger holes. Fit the steel plates and bronze bushings.
3. **Carcass.** Glue and screw the back, bottom and storage top between
   the sides. Square it up. The back panel is what keeps it
   from racking, so glue it along its full height. Hinge on the lid.
4. **Outriggers.** Rout channels in the underside of the bottom (or screw on
   runners), line them with UHMW tape, and add stop pins so the bars pull out
   10 in and no further.
5. **Tower shell.** Glue the sides, end caps, pivot doublers and the panel
   mounting rail. Round the corners. Drill the pivot hole and the plunger holes
   1.5 in either side of it, then fit the bushings.
6. **Control box.** Build it with the cheeks and corner braces, then bolt it
   through the bezel into the mounting rail. It needs to be rigid: anyone
   leaning on the panel is leaning on these bolts.
7. **Hang the unit.** Fit it with the nylon washers and pivot bolts. Flip it
   slowly and check the gaps at the lid edge and the storage doors. Then fit
   the plungers.
8. **Doors.** Hang the storage doors.
9. **Electronics.** Mount the monitor, speakers and marquee. Wire the
   controls. Route the bundle and test it through 10–20 flips.
10. **Finish.** Sand, then paint or veneer. The tower back is the buffet front
    and the lid is the buffet top, so give both a furniture-grade finish. Add
    vinyl art on the bezel and marquee.

### Mode change checklist

**Buffet → Arcade:**
1. Clear the top of the cabinet.
2. Pull out both outriggers.
3. Pull both plunger rings and turn them to the rest position.
4. Grab the finger pull and swing the bottom of the tower out and up, walking
   it over.
5. Release the plungers so they click in.
6. Set the topper on (optional) and power on.

**Arcade → Buffet:** power off, then run those steps in reverse. Push the
outriggers in last.

---

## Open questions / assumptions

- **"I have a slim…"** got cut off. I assumed it's a slim PC or console that
  goes in the storage bay. If you meant a slim Arcade1Up to re-house, tell me
  and I'll adjust the panel and screen sizes.
- The control panel is at 39 in, which suits standing play or a bar stool.
  Lowering it is easy: change `PANEL_TOP` and re-run the checks.
- The monitor is mounted vertical (no tilt), like most slim/fold-flat cabs.
