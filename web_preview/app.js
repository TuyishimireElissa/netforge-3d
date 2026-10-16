'use strict';
let current = null;
let selected = '';
let cableStep = 0;
let busy = false;
const $ = (query) => document.querySelector(query);
const hints = {
  idle: 'Click the loose cable, PC B, then switch port 03 to repair the link.',
  cable: 'Cable picked up. Click PC B to choose eth0.',
  pc: 'PC B eth0 selected. Click the managed switch to use Fa0/3.'
};
function text(node, value) { node.textContent = String(value); }
function status(message) { text($('#selection-hint'), message); }
async function refresh() {
  const response = await fetch('/api/state', {cache: 'no-store'});
  if (!response.ok) throw new Error(`State request failed (${response.status})`);
  const data = await response.json();
  current = data.state;
  render();
}
async function action(payload) {
  if (busy) return;
  busy = true;
  try {
    const response = await fetch('/api/action', {
      method: 'POST',
      headers: {'Content-Type':'application/json', 'X-NetForge-Preview':'1'},
      body: JSON.stringify(payload)
    });
    const data = await response.json();
    if (data.state) { current = data.state; render(); }
    const result = data.error || (typeof data.result === 'string' ? data.result : JSON.stringify(data.result));
    status(`${response.ok ? 'SIMULATED' : 'NOT APPLIED'} · ${result}`);
    if (payload.action === 'command') appendTerminal(payload.line, result, response.ok);
  } catch (error) { status(`Connection error: ${error.message}`); }
  finally { busy = false; }
}
function appendTerminal(line, output, okay) {
  const history = $('#terminal-history');
  const input = document.createElement('div'); input.className = 'term-input'; text(input, `sw1> ${line}`);
  const reply = document.createElement('div'); reply.className = 'term-output'; text(reply, output);
  if (!okay) reply.classList.add('error');
  history.append(input, reply);
  while (history.children.length > 42) history.firstElementChild.remove();
  history.scrollTop = history.scrollHeight;
}
function renderMission(selector, report) {
  const card = $(selector);
  if (!report) return;
  card.classList.toggle('complete', Boolean(report.complete));
  // Fixed rubric weights: represent progress with CSS classes, not inline styles (CSP).
  for (let score = 0; score <= report.max_score; score++) card.classList.remove(`score-${score}`);
  card.classList.add(`score-${report.score}`);
  text(card.querySelector('.mission-score'), `${report.score} / ${report.max_score} POINTS · ${report.complete ? 'COMPLETE' : 'IN PROGRESS'}`);
  text(card.querySelector('.mission-icon'), report.complete ? '✓' : '○');
}
function render() {
  if (!current) return;
  const linked = Boolean(current.ports['pc-b:eth0'].linked);
  $('.scene').classList.toggle('connected', linked);
  const link = $('#link-state'); link.classList.toggle('up', linked);
  text(link, linked ? 'PC B LINKED · COPPER' : 'PC B DISCONNECTED');
  renderMission('#mission-a', current.assessment.mission_a);
  renderMission('#mission-b', current.assessment.mission_b);
  text($('#cli-mode'), `${current.cli_mode.toUpperCase()} MODE`);
  const entries = current.trace || [];
  const trace = $('#trace-content'); trace.replaceChildren();
  if (!entries.length) {
    const empty = document.createElement('div'); empty.className = 'empty-trace'; text(empty, 'No traffic yet. Repair the link and run a ping to see forwarding decisions.'); trace.append(empty);
  } else {
    for (const [index, entry] of entries.entries()) {
      const row = document.createElement('div'); row.className = 'trace-row' + (entry.startsWith('DROP') ? ' drop' : '');
      const marker = document.createElement('span'); text(marker, String(index + 1).padStart(2, '0'));
      const value = document.createElement('div'); text(value, entry); row.append(marker, value); trace.append(row);
    }
  }
  if (selected) inspect(selected);
}
function inspect(device) {
  selected = device;
  const display = $('#inspection-content');
  if (!current) return;
  const p = device === 'sw1' ? current.ports['sw1:fa0/3'] : current.ports[`${device}:eth0`];
  if (!p) return;
  // Device names and values from the fixed simulated model; no user HTML injection.
  display.replaceChildren();
  const title = document.createElement('b'); text(title, device === 'sw1' ? 'SW1 · FastEthernet 0/3' : device.toUpperCase() + ' · eth0');
  const detail = document.createElement('div'); text(detail, `MAC ${p.mac}  ·  ${p.linked ? 'CABLED' : 'NO CABLE'}  ·  ${p.up ? 'UP' : 'DOWN'}`);
  const extra = document.createElement('div'); text(extra, device === 'sw1' ? `VLAN ${p.vlan} · security ${p.security ? 'ON' : 'OFF'} · sticky ${p.sticky ? 'ON' : 'OFF'} · learned ${p.learned.join(', ') || 'none'}` : `IPv4 ${p.address}`);
  display.append(title, detail, extra);
}
function pick(device) {
  inspect(device);
  if (cableStep === 1 && device === 'pc-b') { cableStep = 2; status(hints.pc); return; }
  if (cableStep === 2 && device === 'sw1') {
    cableStep = 0;
    action({action:'connect', a:'pc-b:eth0', b:'sw1:fa0/3', media:'copper'});
    return;
  }
  if (cableStep) status('Select PC B, then SW1 to finish the cable connection.');
  else status(`Inspected ${device.toUpperCase()}. ${hints.idle}`);
}
for (const device of document.querySelectorAll('[data-device]')) device.addEventListener('click', () => pick(device.dataset.device));
$('#cable').addEventListener('click', () => { cableStep = 1; status(hints.cable); });
$('#ping').addEventListener('click', () => action({action:'ping', source:'pc-b:eth0', target:'pc-a:eth0'}));
$('#disconnect').addEventListener('click', () => action({action:'disconnect', port:'pc-b:eth0'}));
$('#assess').addEventListener('click', () => action({action:'assess'}));
$('#reset').addEventListener('click', () => { cableStep = 0; selected = ''; action({action:'reset'}); });
$('#cli-form').addEventListener('submit', (event) => {
  event.preventDefault(); const field = $('#cli-input'); const line = field.value.trim();
  if (!line) return; field.value = ''; action({action:'command', device:'sw1', line});
});
refresh().catch((error) => status(`Preview service unavailable: ${error.message}`));
