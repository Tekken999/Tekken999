// Synthetic swing generator shared by the unit tests and browser smoke test.
import { LM } from '../js/analysis.js';

const rad = (d) => (d * Math.PI) / 180;

// Builds a synthetic swing. Face-on: right-handed golfer facing the camera, so
// the lead (left) side and the target are toward +x.
export function makeSwing({
  view = 'face-on', backMs = 900, downMs = 300, hipSway = 0, headSway = 0,
  weightShift = 0.35, leadElbowBend = 0, earlyExt = 0, fps = 30, mirror = false,
} = {}) {
  const frames = [];
  const total = 1000 + backMs + downMs + 450 + 800;
  for (let t = 0; t <= total; t += 1000 / fps) {
    let theta, back = 0, fin = 0;
    if (t < 1000) theta = 0;
    else if (t < 1000 + backMs) { const p = (t - 1000) / backMs; back = p; theta = -170 * (1 - Math.cos(p * Math.PI)) / 2; }
    else if (t < 1000 + backMs + downMs) { const p = (t - 1000 - backMs) / downMs; back = 1 - p; theta = -170 * (1 - p * p); }
    else if (t < 1000 + backMs + downMs + 450) { const p = (t - 1000 - backMs - downMs) / 450; fin = p; theta = 170 * Math.sin((p * Math.PI) / 2); }
    else { fin = 1; theta = 170; }

    const lm = Array.from({ length: 33 }, () => ({ x: 0.4, y: 0.5, v: 0.99 }));
    const set = (i, x, y) => { lm[i] = { x, y, v: 0.99 }; };

    if (view === 'face-on') {
      const SW = 0.14;
      const hipDx = -hipSway * SW * back + weightShift * SW * fin;
      const headDx = -headSway * SW * back;
      set(LM.NOSE, 0.4 + headDx, 0.25);
      set(LM.L_EAR, 0.42 + headDx, 0.25); set(LM.R_EAR, 0.38 + headDx, 0.25);
      set(LM.L_SHOULDER, 0.47 + hipDx / 2, 0.35); set(LM.R_SHOULDER, 0.33 + hipDx / 2, 0.35);
      set(LM.L_HIP, 0.44 + hipDx, 0.55); set(LM.R_HIP, 0.36 + hipDx, 0.55);
      set(LM.L_KNEE, 0.45, 0.72); set(LM.R_KNEE, 0.35, 0.72);
      set(LM.L_ANKLE, 0.46, 0.88); set(LM.R_ANKLE, 0.34, 0.88);
      set(LM.L_HEEL, 0.46, 0.9); set(LM.R_HEEL, 0.34, 0.9);
      set(LM.L_FOOT, 0.47, 0.91); set(LM.R_FOOT, 0.33, 0.91);
      const smx = 0.4 + hipDx / 2, smy = 0.35, R = 0.27;
      const hx = smx + R * Math.sin(rad(theta)), hy = smy + R * Math.cos(rad(theta));
      set(LM.L_WRIST, hx, hy); set(LM.R_WRIST, hx, hy);
      // Lead elbow: midpoint of shoulder->hands, pushed sideways to bend the arm at the top.
      const ls = lm[LM.L_SHOULDER];
      const len = Math.hypot(hx - ls.x, hy - ls.y) || 1;
      const bend = leadElbowBend * back;
      set(LM.L_ELBOW, (ls.x + hx) / 2 + ((hy - ls.y) / len) * bend, (ls.y + hy) / 2 - ((hx - ls.x) / len) * bend);
      set(LM.R_ELBOW, (lm[LM.R_SHOULDER].x + hx) / 2, (lm[LM.R_SHOULDER].y + hy) / 2);
    } else {
      // Down-the-line: golfer faces +x (toward the ball).
      const T = 0.2;
      const hipDx = earlyExt * T * (t >= 1000 + backMs ? Math.min(1, (t - 1000 - backMs) / downMs) : 0);
      set(LM.NOSE, 0.55, 0.3); set(LM.L_EAR, 0.52, 0.29); set(LM.R_EAR, 0.51, 0.29);
      set(LM.L_SHOULDER, 0.5, 0.39); set(LM.R_SHOULDER, 0.49, 0.39);
      set(LM.L_HIP, 0.38 + hipDx, 0.55); set(LM.R_HIP, 0.37 + hipDx, 0.55);
      set(LM.L_KNEE, 0.44, 0.71); set(LM.R_KNEE, 0.43, 0.71);
      set(LM.L_ANKLE, 0.41, 0.88); set(LM.R_ANKLE, 0.4, 0.88);
      set(LM.L_HEEL, 0.39, 0.9); set(LM.R_HEEL, 0.38, 0.9);
      set(LM.L_FOOT, 0.46, 0.9); set(LM.R_FOOT, 0.45, 0.9);
      const R = 0.27;
      const hx = 0.5 + R * Math.sin(rad(theta)) * 0.6 + 0.05, hy = 0.39 + R * Math.cos(rad(theta));
      set(LM.L_WRIST, hx, hy); set(LM.R_WRIST, hx, hy);
      set(LM.L_ELBOW, (0.5 + hx) / 2, (0.39 + hy) / 2); set(LM.R_ELBOW, (0.49 + hx) / 2, (0.39 + hy) / 2);
    }
    if (mirror) {
      // Mirror image of a right-hander = a left-hander. Swap anatomical sides too.
      const m = lm.map((p) => ({ ...p, x: 0.8 - p.x }));
      for (const [a, b] of [[7, 8], [11, 12], [13, 14], [15, 16], [23, 24], [25, 26], [27, 28], [29, 30], [31, 32]]) {
        [m[a], m[b]] = [m[b], m[a]];
      }
      frames.push({ t, lm: m });
    } else frames.push({ t, lm });
  }
  return frames;
}
