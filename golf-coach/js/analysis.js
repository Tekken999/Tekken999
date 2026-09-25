// Swing analysis: turns a sequence of pose frames into swing phases, measurements
// and coaching findings. Pure functions only (no DOM) so it can be unit tested.
//
// A frame is { t: milliseconds, lm: [{ x, y, v }] } with 33 MediaPipe pose
// landmarks. x is pre-multiplied by the video aspect ratio so x and y share the
// same unit (fraction of video height). y grows downwards.

export const LM = {
  NOSE: 0, L_EAR: 7, R_EAR: 8,
  L_SHOULDER: 11, R_SHOULDER: 12, L_ELBOW: 13, R_ELBOW: 14, L_WRIST: 15, R_WRIST: 16,
  L_HIP: 23, R_HIP: 24, L_KNEE: 25, R_KNEE: 26, L_ANKLE: 27, R_ANKLE: 28,
  L_HEEL: 29, R_HEEL: 30, L_FOOT: 31, R_FOOT: 32,
};

// ---------- geometry helpers ----------
const mid = (a, b) => ({ x: (a.x + b.x) / 2, y: (a.y + b.y) / 2, v: Math.min(a.v ?? 1, b.v ?? 1) });
const dist = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);
const median = (arr) => {
  const s = [...arr].sort((a, b) => a - b);
  const m = Math.floor(s.length / 2);
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
};
// Angle at b (degrees) formed by a-b-c.
export function angle(a, b, c) {
  const v1 = { x: a.x - b.x, y: a.y - b.y };
  const v2 = { x: c.x - b.x, y: c.y - b.y };
  const cos = (v1.x * v2.x + v1.y * v2.y) / (Math.hypot(v1.x, v1.y) * Math.hypot(v2.x, v2.y) || 1);
  return (Math.acos(Math.max(-1, Math.min(1, cos))) * 180) / Math.PI;
}
// Forward lean of the spine: angle between hip->shoulder line and vertical.
function spineTilt(f) {
  const hip = mid(f.lm[LM.L_HIP], f.lm[LM.R_HIP]);
  const sh = mid(f.lm[LM.L_SHOULDER], f.lm[LM.R_SHOULDER]);
  return (Math.atan2(Math.abs(sh.x - hip.x), hip.y - sh.y) * 180) / Math.PI;
}
const hands = (f) => mid(f.lm[LM.L_WRIST], f.lm[LM.R_WRIST]);
const hipMid = (f) => mid(f.lm[LM.L_HIP], f.lm[LM.R_HIP]);
const shoulderMid = (f) => mid(f.lm[LM.L_SHOULDER], f.lm[LM.R_SHOULDER]);
const torsoLen = (f) => dist(shoulderMid(f), hipMid(f));

// ---------- smoothing ----------
export function smoothFrames(frames, radius = 1) {
  return frames.map((f, i) => {
    const lo = Math.max(0, i - radius);
    const hi = Math.min(frames.length - 1, i + radius);
    const lm = f.lm.map((p, j) => {
      let sx = 0, sy = 0;
      for (let k = lo; k <= hi; k++) { sx += frames[k].lm[j].x; sy += frames[k].lm[j].y; }
      const n = hi - lo + 1;
      return { x: sx / n, y: sy / n, v: p.v };
    });
    return { ...f, lm };
  });
}

// ---------- phase detection ----------
// Returns { address, top, impact, finish } frame indexes, or throws with a
// friendly message if no full swing can be found.
export function detectPhases(frames) {
  if (frames.length < 15) throw new SwingError('Not enough video of you was captured. Make sure your whole body is in the frame.');
  const T = median(frames.map(torsoLen));
  const hp = frames.map(hands);
  const speed = frames.map((f, i) => {
    if (i === 0) return 0;
    const dt = (f.t - frames[i - 1].t) / 1000 || 1 / 30;
    return dist(hp[i], hp[i - 1]) / dt / T; // torso lengths per second
  });

  const argBy = (lo, hi, score) => {
    let best = -1, bestScore = -Infinity;
    for (let i = Math.max(0, lo); i <= Math.min(frames.length - 1, hi); i++) {
      const s = score(i);
      if (s > bestScore) { bestScore = s; best = i; }
    }
    return best;
  };
  const idxAtTime = (ms, from, dir) => {
    let i = from;
    while (i + dir >= 0 && i + dir < frames.length && Math.abs(frames[i + dir].t - frames[from].t) <= ms) i += dir;
    return i;
  };

  // The fastest hand movement happens in the downswing / early follow-through.
  const peak = argBy(1, frames.length - 1, (i) => speed[i]);
  // Walk backwards from the peak. If the peak is in the follow-through, first
  // step back down to the impact low point.
  let i = peak;
  while (i > 0 && hp[i - 1].y >= hp[i].y - 0.02 * T) i--;
  // Top of backswing: highest hands going back in time, stopping once the hands
  // have dropped well below that (we are then in the early backswing), so an
  // earlier swing's finish is never mistaken for the top.
  let top = i;
  for (const stop = idxAtTime(2500, i, -1); i > stop; ) {
    i--;
    if (hp[i].y < hp[top].y) top = i;
    else if (hp[i].y > hp[top].y + 0.5 * T) break;
  }
  // Address: lowest hands going back from the top (latest one wins ties),
  // stopping if the hands rise again (a previous swing or waggle).
  let low = -1;
  for (let j = top - 1, stop = idxAtTime(4000, top, -1); j >= stop; j--) {
    if (low < 0 || hp[j].y > hp[low].y) low = j;
    else if (hp[j].y < hp[low].y - 0.5 * T) break;
  }
  if (low < 0) throw new SwingError('I could not see your address position. Start recording before you set up to the ball.');
  // Then walk forward to the last still frame before the takeaway starts.
  let address = low;
  while (address + 1 < top && dist(hp[address + 1], hp[low]) < 0.12 * T) address++;
  // Impact: hands return to their lowest point shortly after the top.
  const impact = argBy(top + 1, idxAtTime(800, top, 1), (i) => hp[i].y);
  // Finish: hands highest in the 1.5s after impact.
  const finish = argBy(impact + 1, idxAtTime(1500, impact, 1), (i) => -hp[i].y);

  const rise = (hp[address].y - hp[top].y) / T;
  if (rise < 0.6 || impact <= top || finish <= impact) {
    throw new SwingError("I couldn't find a full swing in that clip. Make sure your whole body and hands stay in view from setup to finish.");
  }
  if (frames[top].t - frames[address].t < 250) {
    throw new SwingError('The recording seems to start mid-swing. Start recording, then set up to the ball.');
  }
  return { address, top, impact, finish, peakSpeed: speed[peak] };
}

// Splits raw frames wherever tracking jumps (hands teleport more than ~1.6
// torso lengths in one frame, e.g. the tracker switched to another person) or
// there is a gap in the video. Returns [{ start, frames }].
export function splitSegments(frames) {
  if (!frames.length) return [];
  const T = median(frames.map(torsoLen));
  const segs = [{ start: 0, frames: [frames[0]] }];
  for (let i = 1; i < frames.length; i++) {
    const jump = dist(hands(frames[i]), hands(frames[i - 1])) > 1.6 * T;
    const gap = frames[i].t - frames[i - 1].t > 500;
    if (jump || gap) segs.push({ start: i, frames: [] });
    segs[segs.length - 1].frames.push(frames[i]);
  }
  return segs;
}

export class SwingError extends Error {}

// ---------- view detection ----------
export function detectView(frame) {
  const sw = Math.abs(frame.lm[LM.L_SHOULDER].x - frame.lm[LM.R_SHOULDER].x);
  return sw / torsoLen(frame) > 0.45 ? 'face-on' : 'down-the-line';
}

// ---------- grading ----------
// Each check produces a finding: { id, label, value, status: good|warn|fault }
// Lower bound / upper bound rules keep threshold logic in one place.
function grade(value, { warnBelow, faultBelow, warnAbove, faultAbove }) {
  if (faultBelow !== undefined && value < faultBelow) return 'fault';
  if (faultAbove !== undefined && value > faultAbove) return 'fault';
  if (warnBelow !== undefined && value < warnBelow) return 'warn';
  if (warnAbove !== undefined && value > warnAbove) return 'warn';
  return 'good';
}

// Order in which faults are worth fixing (fundamentals first).
export const PRIORITY = [
  'setup_posture', 'knee_flex', 'hip_sway', 'head_sway', 'reverse_pivot', 'lead_arm',
  'early_extension', 'lost_posture', 'head_lift', 'head_dip', 'weight_shift', 'tempo', 'finish',
];

// ---------- main entry ----------
// rawFrames must all contain 33 landmarks.
// options: { handedness: 'right'|'left', view: 'auto'|'face-on'|'down-the-line' }
export function analyzeSwing(rawFrames, options = {}) {
  // Analyse each clean segment and keep the fastest full swing (so a slow
  // practice swing or a tracking glitch does not win).
  let best = null, firstError = null;
  for (const seg of splitSegments(rawFrames)) {
    if (seg.frames.length < 15) continue;
    const segFrames = smoothFrames(seg.frames);
    try {
      const ph = detectPhases(segFrames);
      if (!best || ph.peakSpeed > best.phases.peakSpeed) best = { frames: segFrames, phases: ph, start: seg.start };
    } catch (err) {
      firstError ||= err;
    }
  }
  if (!best) throw firstError || new SwingError('Not enough video of you was captured. Make sure your whole body is in the frame.');
  const { frames, phases, start: frameOffset } = best;
  const A = frames[phases.address], Tp = frames[phases.top], I = frames[phases.impact], F = frames[phases.finish];
  const view = !options.view || options.view === 'auto' ? detectView(A) : options.view;
  const right = options.handedness !== 'left';
  const T = torsoLen(A);
  const findings = [];
  const add = (id, label, value, display, rule) => findings.push({ id, label, value, display, status: grade(value, rule) });

  // Tempo (both views). Tour average backswing:downswing is roughly 3:1.
  const back = Tp.t - A.t, down = I.t - Tp.t;
  const tempo = back / Math.max(down, 1);
  add('tempo', 'Tempo (backswing : downswing)', tempo, `${tempo.toFixed(1)} : 1`,
    { faultBelow: 1.8, warnBelow: 2.4, warnAbove: 4.2, faultAbove: 5.5 });

  // Finish: hands should finish above the shoulders.
  const finishHeight = (shoulderMid(F).y - hands(F).y) / T;
  add('finish', 'Full, balanced finish', finishHeight, finishHeight > 0.3 ? 'Full' : finishHeight > 0 ? 'Short' : 'Very short',
    { faultBelow: 0, warnBelow: 0.3 });

  if (view === 'face-on') {
    const lead = right ? { sh: LM.L_SHOULDER, el: LM.L_ELBOW, wr: LM.L_WRIST } : { sh: LM.R_SHOULDER, el: LM.R_ELBOW, wr: LM.R_WRIST };
    const trailSh = right ? LM.R_SHOULDER : LM.L_SHOULDER;
    const SW = Math.abs(A.lm[LM.L_SHOULDER].x - A.lm[LM.R_SHOULDER].x) || T * 0.8;
    const dir = Math.sign(A.lm[lead.sh].x - A.lm[trailSh].x) || 1; // +1 = target is +x
    const toward = (p0, p1) => ((p1.x - p0.x) * dir) / SW; // positive = moved toward target

    const headTop = toward(A.lm[LM.NOSE], Tp.lm[LM.NOSE]);
    const hipTop = toward(hipMid(A), hipMid(Tp));
    const hipFinish = toward(hipMid(A), hipMid(F));
    const headRise = (A.lm[LM.NOSE].y - I.lm[LM.NOSE].y) / T;
    const leadArm = angle(Tp.lm[lead.sh], Tp.lm[lead.el], Tp.lm[lead.wr]);
    const pct = (v) => `${Math.round(Math.abs(v) * 100)}% of shoulder width`;

    add('hip_sway', 'Hips turn (no slide) in backswing', -hipTop, hipTop < 0 ? `Slid ${pct(hipTop)} away` : 'Stayed centred',
      { warnAbove: 0.18, faultAbove: 0.3 });
    add('head_sway', 'Head steady in backswing', -headTop, headTop < 0 ? `Moved ${pct(headTop)} away` : 'Steady',
      { warnAbove: 0.22, faultAbove: 0.35 });
    add('reverse_pivot', 'Weight loads to trail side', headTop, headTop > 0.05 ? `Head leaned ${pct(headTop)} toward target` : 'Loaded correctly',
      { warnAbove: 0.12, faultAbove: 0.2 });
    add('lead_arm', 'Lead arm extended at the top', leadArm, `${Math.round(leadArm)}°`,
      { faultBelow: 135, warnBelow: 150 });
    add('head_lift', 'Posture held through impact', headRise, headRise > 0.03 ? `Head rose ${Math.round(headRise * 100)}% of torso` : 'Held',
      { warnAbove: 0.07, faultAbove: 0.12 });
    add('head_dip', 'No dipping into impact', -headRise, headRise < -0.03 ? `Head dropped ${Math.round(-headRise * 100)}% of torso` : 'Held',
      { warnAbove: 0.08, faultAbove: 0.13 });
    add('weight_shift', 'Weight shifts to lead side', hipFinish, hipFinish > 0 ? `Hips moved ${pct(hipFinish)} forward` : 'Stayed back',
      { faultBelow: 0.1, warnBelow: 0.2 });
  } else {
    // Which way is the golfer facing (toward the ball)? Toes point that way.
    const toes = mid(A.lm[LM.L_FOOT], A.lm[LM.R_FOOT]);
    const heels = mid(A.lm[LM.L_HEEL], A.lm[LM.R_HEEL]);
    let face = Math.sign(toes.x - heels.x);
    if (!face || Math.min(toes.v, heels.v) < 0.4) {
      face = Math.sign(A.lm[LM.NOSE].x - mid(A.lm[LM.L_EAR], A.lm[LM.R_EAR]).x) || 1;
    }
    const tiltA = spineTilt(A), tiltI = spineTilt(I);
    // Knee flex from whichever leg the camera sees better.
    const lVis = Math.min(A.lm[LM.L_HIP].v, A.lm[LM.L_KNEE].v, A.lm[LM.L_ANKLE].v);
    const rVis = Math.min(A.lm[LM.R_HIP].v, A.lm[LM.R_KNEE].v, A.lm[LM.R_ANKLE].v);
    const knee = lVis >= rVis
      ? angle(A.lm[LM.L_HIP], A.lm[LM.L_KNEE], A.lm[LM.L_ANKLE])
      : angle(A.lm[LM.R_HIP], A.lm[LM.R_KNEE], A.lm[LM.R_ANKLE]);
    const hipToBall = ((hipMid(I).x - hipMid(A).x) * face) / T;
    const headRise = (A.lm[LM.NOSE].y - I.lm[LM.NOSE].y) / T;

    add('setup_posture', 'Athletic spine tilt at address', tiltA, `${Math.round(tiltA)}° forward`,
      { faultBelow: 18, warnBelow: 25, warnAbove: 50, faultAbove: 58 });
    add('knee_flex', 'Soft knee flex at address', knee, `${Math.round(knee)}° at the knee`,
      { faultBelow: 125, warnBelow: 137, warnAbove: 170, faultAbove: 176 });
    add('early_extension', 'Hips stay back through impact', hipToBall, hipToBall > 0.02 ? `Hips moved ${Math.round(hipToBall * 100)}% of torso toward ball` : 'Stayed back',
      { warnAbove: 0.07, faultAbove: 0.12 });
    add('lost_posture', 'Spine angle kept through impact', tiltA - tiltI, tiltA - tiltI > 2 ? `Stood up ${Math.round(tiltA - tiltI)}°` : 'Kept',
      { warnAbove: 6, faultAbove: 10 });
    add('head_lift', 'Head height held through impact', headRise, headRise > 0.03 ? `Head rose ${Math.round(headRise * 100)}% of torso` : 'Held',
      { warnAbove: 0.07, faultAbove: 0.12 });
  }

  // Split tempo into a direction so the right drill is picked.
  const tempoFinding = findings.find((f) => f.id === 'tempo');
  if (tempoFinding.status !== 'good') tempoFinding.drill = tempo < 2.4 ? 'tempo_fast' : 'tempo_slow';

  // If the clip ends right after impact we never saw the finish: don't judge it.
  if (frames[frames.length - 1].t - I.t < 700) {
    for (const id of ['finish', 'weight_shift']) {
      const k = findings.findIndex((f) => f.id === id);
      if (k >= 0) findings.splice(k, 1);
    }
  }

  const penalty = { good: 0, warn: 6, fault: 15 };
  const score = Math.max(30, 100 - findings.reduce((s, f) => s + penalty[f.status], 0));
  const rank = (f) => PRIORITY.indexOf(f.id);
  const byPriority = [...findings].sort((a, b) => rank(a) - rank(b));
  const focus = byPriority.find((f) => f.status === 'fault') || byPriority.find((f) => f.status === 'warn') || null;

  // Visibility warning: feet not seen well means posture numbers are shaky.
  const feetVis = median(frames.map((f) => Math.min(f.lm[LM.L_ANKLE].v ?? 1, f.lm[LM.R_ANKLE].v ?? 1)));

  return {
    view, score, phases, focus, findings: byPriority,
    frames, // smoothed frames of the analysed swing (used for replay)
    frameOffset, // index of frames[0] in the input array
    timing: { backswingMs: back, downswingMs: down },
    lowVisibility: feetVis < 0.5,
  };
}
