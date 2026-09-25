import { analyzeSwing, SwingError, LM } from './analysis.js';
import { DRILLS, drillFor } from './drills.js';

const $ = (s) => document.querySelector(s);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// ---------- storage & settings ----------
const store = {
  get(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch { return d; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* private mode */ } },
};
const DEFAULTS = { handedness: 'right', view: 'auto', countdown: '5', duration: '8', voice: 'on', model: 'lite' };
const settings = { ...DEFAULTS, ...store.get('rc.settings', {}) };

document.querySelectorAll('.seg[data-setting]').forEach((seg) => {
  const key = seg.dataset.setting;
  const mark = () => seg.querySelectorAll('button').forEach((b) => b.classList.toggle('on', b.dataset.value === settings[key]));
  seg.addEventListener('click', (e) => {
    const b = e.target.closest('button');
    if (!b) return;
    settings[key] = b.dataset.value;
    store.set('rc.settings', settings);
    mark();
  });
  mark();
});

// ---------- navigation ----------
let current = 'home';
function show(name) {
  document.querySelectorAll('.screen').forEach((s) => s.classList.toggle('active', s.id === `screen-${name}`));
  $('#backBtn').hidden = name === 'home';
  current = name;
  window.scrollTo(0, 0);
}
function goHome() {
  stopCamera();
  stopReplay();
  renderHistory();
  show('home');
}
$('#backBtn').onclick = goHome;
$('#homeBtn').onclick = goHome;
$('#msgHome').onclick = goHome;

function showMessage(title, text, retry) {
  $('#msgTitle').textContent = title;
  $('#msgText').textContent = text;
  $('#msgRetry').onclick = retry || goHome;
  show('message');
}

// ---------- voice & sounds ----------
function speak(text) {
  if (settings.voice !== 'on' || !('speechSynthesis' in window)) return;
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.rate = 1;
  speechSynthesis.speak(u);
}
let audioCtx;
function beep(freq = 880, ms = 120) {
  try {
    audioCtx ||= new (window.AudioContext || window.webkitAudioContext)();
    const o = audioCtx.createOscillator(), g = audioCtx.createGain();
    o.frequency.value = freq;
    g.gain.setValueAtTime(0.25, audioCtx.currentTime);
    g.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + ms / 1000);
    o.connect(g).connect(audioCtx.destination);
    o.start();
    o.stop(audioCtx.currentTime + ms / 1000);
  } catch { /* no audio */ }
}

// ---------- pose module (lazy, so the app still works offline for drills) ----------
let poseMod;
async function getLandmarker(onMsg) {
  onMsg?.('Loading swing tracker… (first time can take a few seconds)');
  poseMod ||= await import('./pose.js');
  return poseMod.loadLandmarker(settings.model);
}

// ---------- camera capture ----------
const cam = { stream: null, facing: 'user', tracker: null, raf: 0, active: false, phase: 'idle', wakeLock: null, lastTime: -1 };
const video = $('#camVideo');
const overlay = $('#camOverlay');

async function openCapture() {
  show('capture');
  $('#startBtn').disabled = true;
  $('#startBtn').hidden = false;
  $('#stopBtn').hidden = true;
  $('#countdown').hidden = true;
  $('#recDot').hidden = true;
  cam.phase = 'idle';
  setPill('Starting camera…');
  if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
    showMessage('Camera not available', 'The camera only works when this page is opened over https:// (or localhost). See the README for how to host it.');
    return;
  }
  try {
    const landmarker = await getLandmarker(setPill);
    await startCamera();
    cam.tracker = new poseMod.PoseTracker(landmarker, video);
    cam.active = true;
    cam.lastTime = -1;
    loop();
    $('#startBtn').disabled = false;
    try { cam.wakeLock = await navigator.wakeLock?.request('screen'); } catch { /* optional */ }
  } catch (err) {
    console.error(err);
    stopCamera();
    if (err?.name === 'NotAllowedError') {
      showMessage('Camera blocked', 'Allow camera access for this site in your browser settings, then try again.', openCapture);
    } else if (err?.name === 'NotFoundError') {
      showMessage('No camera found', 'I could not find a camera on this device. You can still analyze a saved video from the home screen.');
    } else {
      showMessage('Could not start', 'The swing tracker failed to load. Check your internet connection (it is needed the first time) and try again.', openCapture);
    }
  }
}

async function startCamera() {
  cam.stream?.getTracks().forEach((t) => t.stop());
  cam.stream = await navigator.mediaDevices.getUserMedia({
    video: { facingMode: cam.facing, width: { ideal: 1280 }, height: { ideal: 720 }, frameRate: { ideal: 60 } },
    audio: false,
  });
  video.srcObject = cam.stream;
  await video.play();
  $('#captureStage').classList.toggle('mirror', cam.facing === 'user');
}

function stopCamera() {
  cam.active = false;
  cam.phase = 'idle';
  cancelAnimationFrame(cam.raf);
  clearTimeout(cam.timer);
  cam.stream?.getTracks().forEach((t) => t.stop());
  cam.stream = null;
  video.srcObject = null;
  cam.wakeLock?.release?.().catch(() => {});
  cam.wakeLock = null;
}

function setPill(msg, cls = '') {
  const p = $('#statusPill');
  p.textContent = msg;
  p.className = `pill ${cls}`;
}

function loop() {
  if (!cam.active) return;
  if (video.readyState >= 2 && video.currentTime !== cam.lastTime) {
    cam.lastTime = video.currentTime;
    const lm = cam.tracker.step(performance.now());
    overlay.width = video.videoWidth;
    overlay.height = video.videoHeight;
    const ctx = overlay.getContext('2d');
    ctx.clearRect(0, 0, overlay.width, overlay.height);
    if (lm) poseMod.drawSkeleton(ctx, lm, overlay.width, overlay.height);
    if (cam.phase === 'idle' || cam.phase === 'countdown') {
      const s = poseMod.framingStatus(lm);
      setPill(s.msg, s.ok ? 'ok' : 'bad');
    }
  }
  cam.raf = requestAnimationFrame(loop);
}

$('#recordBtn').onclick = openCapture;
$('#flipBtn').onclick = async () => {
  if (cam.phase !== 'idle') return;
  cam.facing = cam.facing === 'user' ? 'environment' : 'user';
  try { await startCamera(); } catch { showMessage('Could not switch camera', 'This device may only have one camera.', openCapture); }
};

$('#startBtn').onclick = async () => {
  if (cam.phase !== 'idle') return;
  cam.phase = 'countdown';
  $('#startBtn').hidden = true;
  $('#stopBtn').hidden = false;
  const cd = $('#countdown');
  cd.hidden = false;
  const n = Number(settings.countdown);
  speak(`Recording in ${n} seconds. Get set up.`);
  for (let i = n; i > 0; i--) {
    if (cam.phase !== 'countdown') return;
    cd.textContent = i;
    if (i <= 3) beep(660);
    await sleep(1000);
  }
  if (cam.phase !== 'countdown') return;
  cd.hidden = true;
  beep(1200, 250);
  cam.phase = 'recording';
  cam.tracker.start();
  setPill('Recording — swing away!', 'ok');
  $('#recDot').hidden = false;
  const started = performance.now();
  const dur = Number(settings.duration) * 1000;
  const tick = () => {
    if (cam.phase !== 'recording') return;
    const left = Math.max(0, dur - (performance.now() - started));
    $('#recTime').textContent = `${Math.ceil(left / 1000)}s`;
    if (left <= 0) return finishRecording();
    cam.timer = setTimeout(tick, 200);
  };
  tick();
};

$('#stopBtn').onclick = () => {
  if (cam.phase === 'recording') finishRecording();
  else if (cam.phase === 'countdown') {
    cam.phase = 'idle';
    $('#countdown').hidden = true;
    $('#startBtn').hidden = false;
    $('#stopBtn').hidden = true;
  }
};

async function finishRecording() {
  cam.phase = 'done';
  beep(900, 100); setTimeout(() => beep(900, 100), 160);
  const data = cam.tracker.stop();
  data.mirrored = cam.facing === 'user';
  stopCamera();
  await processCapture(data, openCapture);
}

// ---------- saved video ----------
$('#fileInput').onchange = async (e) => {
  const file = e.target.files?.[0];
  e.target.value = '';
  if (!file) return;
  show('analyzing');
  const bar = $('#analyzeBar');
  bar.style.width = '0%';
  $('#analyzeTitle').textContent = 'Reading your video…';
  const msg = (m) => { $('#analyzeMsg').textContent = m; };
  let landmarker;
  try {
    landmarker = await getLandmarker(msg);
  } catch (err) {
    console.error(err);
    showMessage('Could not start', 'The swing tracker failed to load. Check your internet connection and try again.');
    return;
  }
  const v = document.createElement('video');
  v.muted = true;
  v.playsInline = true;
  v.src = URL.createObjectURL(file);
  try {
    await new Promise((res, rej) => { v.onloadeddata = res; v.onerror = () => rej(new Error('decode')); });
  } catch {
    showMessage('Could not open video', 'That video format is not supported by this browser. Try an .mp4 or .mov recorded on your phone.');
    return;
  }
  const MAX_S = 20;
  const end = Math.min(v.duration || MAX_S, MAX_S);
  const tracker = new poseMod.PoseTracker(landmarker, v);
  tracker.start();
  msg('Tracking your body frame by frame…');
  v.playbackRate = 0.4;
  await new Promise((resolve) => {
    let last = -1;
    const done = () => { v.pause(); resolve(); };
    const onFrame = (mediaTime) => {
      if (mediaTime !== last) {
        last = mediaTime;
        tracker.step(mediaTime * 1000);
        bar.style.width = `${Math.min(100, (mediaTime / end) * 100)}%`;
      }
      if (v.ended || mediaTime >= end) return done();
      schedule();
    };
    const schedule = v.requestVideoFrameCallback
      ? () => v.requestVideoFrameCallback((_, meta) => onFrame(meta.mediaTime))
      : () => requestAnimationFrame(() => onFrame(v.currentTime));
    v.onended = done;
    v.play().then(schedule).catch(done);
  });
  URL.revokeObjectURL(v.src);
  const data = tracker.stop();
  data.mirrored = false;
  await processCapture(data, () => $('#fileInput').click());
};

// ---------- analysis ----------
let lastResult = null;
async function processCapture(data, retry) {
  show('analyzing');
  $('#analyzeTitle').textContent = 'Analyzing your swing…';
  $('#analyzeMsg').textContent = 'Finding address, top, impact and finish…';
  $('#analyzeBar').style.width = '100%';
  // Let the last JPEG snapshots finish encoding.
  for (let i = 0; i < 20 && data.snaps.filter(Boolean).length < data.frames.length; i++) await sleep(50);
  await sleep(300);
  let result;
  try {
    result = analyzeSwing(data.frames, { handedness: settings.handedness, view: settings.view });
  } catch (err) {
    console.error(err);
    const text = err instanceof SwingError ? err.message : 'Something went wrong analyzing that swing.';
    speak("I couldn't find a full swing. Let's try again.");
    showMessage("Let's try that again", text, retry);
    return;
  }
  result.snaps = data.snaps.slice(result.frameOffset, result.frameOffset + result.frames.length);
  result.aspect = data.aspect;
  result.mirrored = data.mirrored;
  lastResult = result;
  saveHistory(result);
  renderResults(result);
}

// ---------- results ----------
const STATUS_ICON = { good: '✅', warn: '⚠️', fault: '❌' };

function renderResults(r) {
  show('results');
  const ring = $('#scoreRing');
  ring.style.setProperty('--pct', r.score);
  ring.style.setProperty('--col', r.score >= 80 ? 'var(--accent)' : r.score >= 60 ? 'var(--warn)' : 'var(--fault)');
  $('#scoreNum').textContent = r.score;
  $('#viewLabel').textContent = `${r.view === 'face-on' ? 'Face-on' : 'Down-the-line'} view · ${settings.handedness}-handed`;
  $('#tempoLabel').textContent = `Backswing ${(r.timing.backswingMs / 1000).toFixed(2)}s · Downswing ${(r.timing.downswingMs / 1000).toFixed(2)}s`;
  $('#visWarn').hidden = !r.lowVisibility;

  renderFocus(r.focus, true);

  const list = $('#checklist');
  list.innerHTML = '';
  for (const f of r.findings) {
    const li = document.createElement('li');
    li.innerHTML = `<span class="ico">${STATUS_ICON[f.status]}</span><span>${f.label}</span><span class="val">${f.display}</span>`;
    if (f.status !== 'good' && f !== r.focus) {
      const b = document.createElement('button');
      b.className = 'drill-link';
      b.textContent = `Drill: ${drillFor(f).title} →`;
      b.onclick = () => { renderFocus(f, false); window.scrollTo({ top: 0, behavior: 'smooth' }); };
      li.appendChild(b);
    }
    list.appendChild(li);
  }

  setupReplay(r);
}

function drillHTML(d) {
  return `
    <p class="fault">${d.fault}</p>
    <div class="cue">“${d.cue}”</div>
    <ol class="steps">${d.steps.map((s) => `<li>${s}</li>`).join('')}</ol>
    <div class="plan"><b>Your bucket plan:</b> ${d.plan}</div>
    <p class="why"><b>Why it matters:</b> ${d.why}</p>
    <p class="meta">You need: ${d.equipment}</p>`;
}

function renderFocus(finding, auto) {
  const d = drillFor(finding);
  const card = $('#focusCard');
  const eyebrow = !finding ? 'Great swing — keep it up' : finding === lastResult?.focus ? "Today's focus" : 'Also worth working on';
  card.innerHTML = `
    <div class="eyebrow">${eyebrow}</div>
    <h2>${d.title}</h2>
    ${drillHTML(d)}
    <button class="btn ghost" id="speakBtn">🔊 Read it to me</button>`;
  const say = () => speak(`${finding ? 'Work on this' : 'Nice swing'}. ${d.title}. The feel is: ${d.cue}. ${d.steps.join(' ')} ${d.plan}`);
  card.querySelector('#speakBtn').onclick = () => { const v = settings.voice; settings.voice = 'on'; say(); settings.voice = v; };
  if (auto) speak(`${finding ? "Today's focus" : 'Nice swing'}: ${d.title}. The feel is: ${d.cue}`);
}

// ---------- replay ----------
const replay = { frames: [], imgs: [], idx: 0, playing: false, speed: 0.25, raf: 0 };
const rc = $('#replayCanvas');

function setupReplay(r) {
  stopReplay();
  replay.imgs.forEach((im) => im && URL.revokeObjectURL(im.src));
  replay.frames = r.frames;
  replay.result = r;
  replay.imgs = r.frames.map((_, i) => {
    const b = r.snaps[i];
    if (!b) return null;
    const im = new Image();
    im.src = URL.createObjectURL(b);
    im.onload = () => { if (i === replay.idx) drawReplay(); };
    return im;
  });
  rc.width = 360;
  rc.height = Math.round(360 / r.aspect);
  rc.parentElement.classList.toggle('mirror', !!r.mirrored);
  const scrub = $('#scrub');
  scrub.max = r.frames.length - 1;
  scrub.oninput = () => { stopReplay(); setFrame(Number(scrub.value)); };

  const phases = $('#phases');
  phases.innerHTML = '';
  for (const [key, label] of [['address', 'Setup'], ['top', 'Top'], ['impact', 'Impact'], ['finish', 'Finish']]) {
    const i = r.phases[key];
    const b = document.createElement('button');
    const c = document.createElement('canvas');
    c.width = 120; c.height = Math.round(120 / r.aspect);
    if (r.mirrored) c.style.transform = 'scaleX(-1)';
    b.append(c, label);
    b.onclick = () => { stopReplay(); setFrame(i); };
    phases.appendChild(b);
    const paint = () => drawFrame(c, i);
    if (replay.imgs[i]) replay.imgs[i].addEventListener('load', paint);
    paint();
  }
  setFrame(r.phases.address);
}

function setFrame(i) {
  replay.idx = Math.max(0, Math.min(replay.frames.length - 1, i));
  $('#scrub').value = replay.idx;
  drawReplay();
}

function drawReplay() { drawFrame(rc, replay.idx, true); }

function drawFrame(canvas, i, guides = false) {
  const ctx = canvas.getContext('2d');
  const { width: w, height: h } = canvas;
  const r = replay.result;
  const im = replay.imgs[i];
  ctx.fillStyle = '#000';
  ctx.fillRect(0, 0, w, h);
  if (im?.complete && im.naturalWidth) ctx.drawImage(im, 0, 0, w, h);
  const f = replay.frames[i];
  if (!f) return;
  const pts = f.lm.map((p) => ({ x: p.x / r.aspect, y: p.y, v: p.v }));
  if (guides) {
    const A = replay.frames[r.phases.address].lm;
    ctx.setLineDash([6, 6]);
    ctx.lineWidth = 2;
    const vline = (x, color) => { ctx.strokeStyle = color; ctx.beginPath(); ctx.moveTo(x * w, 0); ctx.lineTo(x * w, h); ctx.stroke(); };
    vline(A[LM.NOSE].x / r.aspect, 'rgba(255,209,102,.9)');
    vline((A[LM.L_HIP].x + A[LM.R_HIP].x) / 2 / r.aspect, 'rgba(120,200,255,.9)');
    if (r.view === 'down-the-line') {
      const hip = { x: (A[LM.L_HIP].x + A[LM.R_HIP].x) / 2 / r.aspect, y: (A[LM.L_HIP].y + A[LM.R_HIP].y) / 2 };
      const sh = { x: (A[LM.L_SHOULDER].x + A[LM.R_SHOULDER].x) / 2 / r.aspect, y: (A[LM.L_SHOULDER].y + A[LM.R_SHOULDER].y) / 2 };
      ctx.strokeStyle = 'rgba(255,255,255,.8)';
      ctx.beginPath();
      ctx.moveTo(hip.x * w, hip.y * h);
      ctx.lineTo((hip.x + (sh.x - hip.x) * 1.6) * w, (hip.y + (sh.y - hip.y) * 1.6) * h);
      ctx.stroke();
    }
    ctx.setLineDash([]);
  }
  poseMod.drawSkeleton(ctx, pts, w, h);
}

$('#speedSeg').onclick = (e) => {
  const b = e.target.closest('button');
  if (!b) return;
  replay.speed = Number(b.dataset.speed);
  $('#speedSeg').querySelectorAll('button').forEach((x) => x.classList.toggle('on', x === b));
};

$('#playBtn').onclick = () => (replay.playing ? stopReplay() : startReplay());

function startReplay() {
  if (!replay.frames.length) return;
  if (replay.idx >= replay.frames.length - 1) replay.idx = 0;
  replay.playing = true;
  $('#playBtn').textContent = '❚❚ Pause';
  const t0 = replay.frames[replay.idx].t;
  const wall0 = performance.now();
  const step = () => {
    if (!replay.playing) return;
    const target = t0 + (performance.now() - wall0) * replay.speed;
    let i = replay.idx;
    while (i < replay.frames.length - 1 && replay.frames[i + 1].t <= target) i++;
    if (i !== replay.idx) setFrame(i);
    if (i >= replay.frames.length - 1) return stopReplay();
    replay.raf = requestAnimationFrame(step);
  };
  replay.raf = requestAnimationFrame(step);
}

function stopReplay() {
  replay.playing = false;
  cancelAnimationFrame(replay.raf);
  $('#playBtn').textContent = '▶ Play';
}

$('#againBtn').onclick = () => { stopReplay(); openCapture(); };

// ---------- history ----------
function saveHistory(r) {
  const h = store.get('rc.history', []);
  h.unshift({ at: Date.now(), score: r.score, view: r.view, focus: drillFor(r.focus).title });
  store.set('rc.history', h.slice(0, 10));
}
function renderHistory() {
  const h = store.get('rc.history', []);
  $('#historyCard').hidden = !h.length;
  $('#historyList').innerHTML = h.map((e) => {
    const d = new Date(e.at);
    return `<li><span>${d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })} · ${e.focus}</span><b>${e.score}</b></li>`;
  }).join('');
}

// ---------- drill library ----------
$('#libraryBtn').onclick = () => {
  const seen = new Set();
  $('#libraryList').innerHTML = Object.values(DRILLS)
    .filter((d) => !seen.has(d.title) && seen.add(d.title))
    .map((d) => `
      <details class="card lib-item">
        <summary><h3>${d.title}</h3><p>Fixes: ${d.fault}</p></summary>
        ${drillHTML(d)}
      </details>`).join('');
  show('library');
};

renderHistory();
