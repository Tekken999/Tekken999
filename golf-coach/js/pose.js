// MediaPipe pose tracking + frame capture. Runs fully on-device in the browser.

// Loaded from the CDN on the web. The Android app bundles these files and sets
// window.RC_ASSETS (see android/build-apk.sh) so it works offline.
const CDN = 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14';
const MODEL_CDN = 'https://storage.googleapis.com/mediapipe-models/pose_landmarker';
const ASSETS = globalThis.RC_ASSETS || {
  bundle: `${CDN}/vision_bundle.mjs`,
  wasm: `${CDN}/wasm`,
  models: {
    lite: `${MODEL_CDN}/pose_landmarker_lite/float16/1/pose_landmarker_lite.task`,
    full: `${MODEL_CDN}/pose_landmarker_full/float16/1/pose_landmarker_full.task`,
  },
};

let cached = { key: null, landmarker: null };

export async function loadLandmarker(model = 'lite') {
  if (cached.key === model) return cached.landmarker;
  cached.landmarker?.close();
  const { PoseLandmarker, FilesetResolver } = await import(ASSETS.bundle);
  const vision = await FilesetResolver.forVisionTasks(ASSETS.wasm);
  const opts = (delegate) => ({
    baseOptions: { modelAssetPath: ASSETS.models[model], delegate },
    runningMode: 'VIDEO',
    numPoses: 1,
    minPoseDetectionConfidence: 0.5,
    minPosePresenceConfidence: 0.5,
    minTrackingConfidence: 0.5,
  });
  let landmarker;
  try {
    landmarker = await PoseLandmarker.createFromOptions(vision, opts('GPU'));
  } catch {
    landmarker = await PoseLandmarker.createFromOptions(vision, opts('CPU'));
  }
  cached = { key: model, landmarker };
  return landmarker;
}

// Tracks a <video> element frame by frame. Call step() once per new video frame.
export class PoseTracker {
  constructor(landmarker, video) {
    this.landmarker = landmarker;
    this.video = video;
    this.lastTs = 0;
    this.recording = false;
    this.frames = [];
    this.snaps = [];
    this.snapCanvas = document.createElement('canvas');
  }

  get aspect() { return this.video.videoWidth / this.video.videoHeight || 1; }

  // Returns raw landmarks (normalised 0..1) for the current frame, or null.
  step(mediaTimeMs) {
    const ts = Math.max(this.lastTs + 1, performance.now());
    this.lastTs = ts;
    const res = this.landmarker.detectForVideo(this.video, ts);
    const lm = res.landmarks?.[0] || null;
    if (this.recording && lm) {
      const a = this.aspect;
      this.frames.push({
        t: mediaTimeMs ?? ts,
        lm: lm.map((p) => ({ x: p.x * a, y: p.y, v: p.visibility ?? 1 })),
      });
      this.snapshot(this.frames.length - 1);
    }
    return lm;
  }

  // Store a small JPEG of each recorded frame for the slow-motion replay.
  snapshot(index) {
    const c = this.snapCanvas;
    const w = 360;
    c.width = w;
    c.height = Math.round(w / this.aspect);
    c.getContext('2d').drawImage(this.video, 0, 0, c.width, c.height);
    c.toBlob((b) => { if (b) this.snaps[index] = b; }, 'image/jpeg', 0.7);
  }

  start() { this.frames = []; this.snaps = []; this.recording = true; }
  stop() { this.recording = false; return { frames: this.frames, snaps: this.snaps, aspect: this.aspect }; }
}

// Checks the whole body is visible (head to feet) for the framing guide.
export function framingStatus(lm) {
  if (!lm) return { ok: false, msg: 'Step into the frame' };
  const vis = (i) => lm[i].visibility ?? 1;
  const inFrame = (i) => lm[i].x > 0.02 && lm[i].x < 0.98 && lm[i].y > 0.01 && lm[i].y < 0.99;
  const need = [0, 11, 12, 23, 24, 27, 28];
  if (need.every((i) => vis(i) > 0.5 && inFrame(i))) return { ok: true, msg: 'Full body in view — ready' };
  if (vis(27) < 0.5 || vis(28) < 0.5 || !inFrame(27) || !inFrame(28)) return { ok: false, msg: 'Move back — I need to see your feet' };
  if (!inFrame(0)) return { ok: false, msg: 'Move back — I need to see your head' };
  return { ok: false, msg: 'Get your whole body in the frame' };
}

export const CONNECTIONS = [
  [11, 12], [11, 13], [13, 15], [12, 14], [14, 16], [11, 23], [12, 24], [23, 24],
  [23, 25], [25, 27], [24, 26], [26, 28], [27, 29], [29, 31], [27, 31], [28, 30], [30, 32], [28, 32],
];

// Draws a skeleton. pts are {x,y} in 0..1 of the canvas.
export function drawSkeleton(ctx, pts, w, h, color = '#7CFFB2') {
  ctx.lineWidth = Math.max(2, w / 180);
  ctx.strokeStyle = color;
  ctx.lineCap = 'round';
  for (const [a, b] of CONNECTIONS) {
    if ((pts[a].v ?? pts[a].visibility ?? 1) < 0.3 || (pts[b].v ?? pts[b].visibility ?? 1) < 0.3) continue;
    ctx.beginPath();
    ctx.moveTo(pts[a].x * w, pts[a].y * h);
    ctx.lineTo(pts[b].x * w, pts[b].y * h);
    ctx.stroke();
  }
  ctx.fillStyle = '#ffffff';
  for (const i of [0, 11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]) {
    if ((pts[i].v ?? pts[i].visibility ?? 1) < 0.3) continue;
    ctx.beginPath();
    ctx.arc(pts[i].x * w, pts[i].y * h, Math.max(2.5, w / 140), 0, Math.PI * 2);
    ctx.fill();
  }
}
