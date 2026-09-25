// Run with: node --test golf-coach/tests
import test from 'node:test';
import assert from 'node:assert/strict';
import { analyzeSwing, SwingError } from '../js/analysis.js';
import { makeSwing } from './synthetic.mjs';
import { drillFor } from '../js/drills.js';

const status = (r, id) => r.findings.find((f) => f.id === id)?.status;

test('good face-on swing has no faults', () => {
  const r = analyzeSwing(makeSwing(), { handedness: 'right' });
  assert.equal(r.view, 'face-on');
  const faults = r.findings.filter((f) => f.status !== 'good');
  assert.deepEqual(faults.map((f) => f.id), []);
  assert.equal(r.focus, null);
  assert.equal(drillFor(r.focus).title, 'Groove It: Ladder Drill');
  assert.ok(r.score >= 95);
});

test('phases are found in order at the right moments', () => {
  const frames = makeSwing();
  const r = analyzeSwing(frames);
  const { address, top, impact, finish } = r.phases;
  assert.ok(address < top && top < impact && impact < finish);
  assert.ok(Math.abs(frames[top].t - 1900) <= 70, `top at ${frames[top].t}`);
  assert.ok(Math.abs(frames[impact].t - 2200) <= 70, `impact at ${frames[impact].t}`);
  assert.ok(Math.abs(frames[address].t - 1000) <= 170, `address at ${frames[address].t}`);
});

test('hip slide in backswing becomes the focus', () => {
  const r = analyzeSwing(makeSwing({ hipSway: 0.45 }));
  assert.equal(status(r, 'hip_sway'), 'fault');
  assert.equal(r.focus.id, 'hip_sway');
  assert.equal(drillFor(r.focus).title, 'Stick Outside the Trail Hip');
});

test('head sway is detected', () => {
  const r = analyzeSwing(makeSwing({ headSway: 0.5 }));
  assert.equal(status(r, 'head_sway'), 'fault');
});

test('reverse pivot is detected', () => {
  const r = analyzeSwing(makeSwing({ headSway: -0.3 }));
  assert.equal(status(r, 'reverse_pivot'), 'fault');
});

test('rushed backswing gives the tempo drill', () => {
  const r = analyzeSwing(makeSwing({ backMs: 420, downMs: 300 }));
  assert.equal(status(r, 'tempo'), 'fault');
  assert.equal(drillFor(r.focus).title, '"One-Two-Three" Tempo');
});

test('hanging back at the finish is detected', () => {
  const r = analyzeSwing(makeSwing({ weightShift: -0.05 }));
  assert.equal(status(r, 'weight_shift'), 'fault');
});

test('bent lead arm at the top is detected', () => {
  const r = analyzeSwing(makeSwing({ leadElbowBend: 0.08 }));
  assert.equal(status(r, 'lead_arm'), 'fault');
});

test('left-handed golfer is analysed with mirrored rules', () => {
  const r = analyzeSwing(makeSwing({ mirror: true, hipSway: 0.45 }), { handedness: 'left' });
  assert.equal(r.view, 'face-on');
  assert.equal(status(r, 'hip_sway'), 'fault');
  assert.equal(status(r, 'weight_shift'), 'good');
});

test('down-the-line view is auto-detected with good posture', () => {
  const r = analyzeSwing(makeSwing({ view: 'down-the-line' }));
  assert.equal(r.view, 'down-the-line');
  assert.equal(status(r, 'setup_posture'), 'good');
  assert.equal(status(r, 'early_extension'), 'good');
});

test('early extension is detected down-the-line', () => {
  const r = analyzeSwing(makeSwing({ view: 'down-the-line', earlyExt: 0.25 }));
  assert.equal(status(r, 'early_extension'), 'fault');
  assert.equal(drillFor(r.focus).title, 'Butt to the Bag');
});

test('works at a low 15fps tracking rate', () => {
  const r = analyzeSwing(makeSwing({ fps: 15 }));
  assert.equal(status(r, 'tempo'), 'good');
});

test('standing still is rejected with a friendly message', () => {
  const frames = makeSwing().slice(0, 25).map((f, i) => ({ ...f, t: i * 33 }));
  assert.throws(() => analyzeSwing(frames), SwingError);
});

test('back-to-back swings with a tracking jump still find the right phases', () => {
  const one = makeSwing({ hipSway: 0.45 });
  const len = one[one.length - 1].t + 33;
  const frames = [...one, ...one.map((f) => ({ ...f, t: f.t + len }))].filter((f) => f.t > 1500);
  const r = analyzeSwing(frames);
  assert.ok(r.timing.backswingMs > 700 && r.timing.backswingMs < 1100, `backswing ${r.timing.backswingMs}`);
  assert.ok(r.timing.downswingMs > 200 && r.timing.downswingMs < 400, `downswing ${r.timing.downswingMs}`);
  assert.equal(r.focus.id, 'hip_sway');
});

test('a clip that stops right after impact does not judge the finish', () => {
  const frames = makeSwing({ weightShift: -0.05 }).filter((f) => f.t < 2400);
  const r = analyzeSwing(frames);
  assert.equal(status(r, 'finish'), undefined);
  assert.equal(status(r, 'weight_shift'), undefined);
});
