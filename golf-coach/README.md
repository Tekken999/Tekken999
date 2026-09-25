# ⛳ Range Coach — golf swing coach in your phone

Record one swing with your phone's camera and get **one easy drill** to work on
with your next bucket of balls.

Everything runs in the browser, on your device. Your video is never uploaded.

## How it works

1. Prop your phone on your bag, facing you (**face-on**) or behind you looking down the target line (**down-the-line**).
2. Tap **Record my swing**. A countdown gives you time to walk to the ball.
3. Set up and swing, then hold your finish.
4. The app tracks 33 body points ([MediaPipe Pose](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker)),
   finds your **setup, top, impact and finish**, and checks:

| Face-on view | Down-the-line view | Both |
|---|---|---|
| Hip slide (sway) | Spine tilt at setup | Tempo (backswing : downswing, ideal ≈ 3 : 1) |
| Head movement | Knee flex at setup | Full, balanced finish |
| Reverse pivot | Early extension (hips toward ball) | |
| Bent lead arm at the top | Standing up out of posture | |
| Head lifting / dipping | Head lifting | |
| Weight shift to lead side | | |

5. You get a swing score, a **"Today's focus"** drill with a feel cue, three steps and a bucket plan.
   You also get a slow-motion replay with your skeleton drawn on it, and a full checklist.
   The voice coach can read the drill out loud so you don't need to walk back to your phone.

You can also analyze a video you already recorded (e.g. slow-mo from your camera app) with **Analyze a saved video**.

## Running it

The camera only works on `https://` or `localhost`.

**Easiest — GitHub Pages:** in the repo on GitHub go to *Settings → Pages*, choose
*Deploy from a branch*, pick the branch and `/ (root)`, and save. Then open
`https://<your-username>.github.io/<repo>/golf-coach/` on your phone. Use *Add to Home Screen* for an app icon.

**On your computer:**

```bash
cd golf-coach
npx serve .        # then open http://localhost:3000
```

The first run needs internet to download the tracking model (~5–10 MB). After that it's cached by your browser.

## Tips for good results

- Whole body, head to feet, must be in frame. The status pill turns green when it is.
- Put the phone at about hip height, 3–4 steps away.
- Avoid having the sun directly behind you.
- Use **Tracking: Precise** on a newer phone for better accuracy. **Fast** works better on older phones.

## Development

```
golf-coach/
├── index.html        UI screens
├── css/styles.css
├── js/app.js         screens, camera, recording, results, replay
├── js/pose.js        MediaPipe loader, frame capture, skeleton drawing
├── js/analysis.js    swing phase detection + checks (pure functions)
├── js/drills.js      drill library
└── tests/            unit tests with synthetic swings
```

Run the tests (Node 20+):

```bash
cd golf-coach && npm test
```

The coaching is for practice guidance, not a replacement for a lesson with a PGA pro.
The measurements come from a single 2D camera, so treat them as helpful hints, not lab data.
