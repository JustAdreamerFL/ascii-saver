// Offline lifecycle regression. Mocks GNOME Shell/GJS API; no display required.
const fs = require('node:fs');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.resolve(__dirname, '../gnome-shell-extension/ascii-saver-cursor@ascii-saver.local/extension.js'), 'utf8')
    .replace(/^import .*;\s*$/gm, '')
    .replace('export default class AsciiSaverCursor extends Extension', 'class AsciiSaverCursor extends Extension')
    .concat('\nthis.AsciiSaverCursor = AsciiSaverCursor;\n');
const calls = [];
const ctx = {
  Gio: {
    BusType: {SESSION: 1},
    BusNameWatcherFlags: {NONE: 0},
    bus_watch_name: (...args) => { ctx.appeared = args[3]; ctx.vanished = args[4]; return 27; },
    bus_unwatch_name: id => calls.push(`unwatch:${id}`),
  },
  GLib: {
    PRIORITY_DEFAULT: 0,
    SOURCE_CONTINUE: true,
    timeout_add_seconds: (priority, interval, callback) => {ctx.timerCallback=callback;return 78;},
    Source: {remove: id => calls.push(`timer-remove:${id}`)},
  },
  Main: {screenShield:{locked:false}},
  global: {backend:{get_cursor_tracker: () => ({
    inhibit_cursor_visibility: () => calls.push('hide'),
    uninhibit_cursor_visibility: () => calls.push('show'),
  })}},
  Extension: class {},
};
vm.runInNewContext(source,ctx);
const extension = new ctx.AsciiSaverCursor();
extension.enable();
assert.equal(calls.length, 0);
ctx.appeared();
ctx.appeared();
assert.deepEqual(calls,['hide']);
ctx.Main.screenShield.locked = true;
ctx.timerCallback();
assert.deepEqual(calls,['hide','show']);
ctx.Main.screenShield.locked = false;
ctx.timerCallback();
assert.deepEqual(calls,['hide','show','hide']);
ctx.vanished();
assert.deepEqual(calls,['hide','show','hide','timer-remove:78','show']);
ctx.appeared();
extension.disable();
assert.deepEqual(calls.slice(-3),['unwatch:27','timer-remove:78','show']);
console.log('GNOME cursor extension mock lifecycle: PASS');
