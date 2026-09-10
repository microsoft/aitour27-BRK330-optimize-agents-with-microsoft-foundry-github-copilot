const $ = (s) => document.querySelector(s);
const $$ = (s) => Array.from(document.querySelectorAll(s));

const samples = $$('.sample');
const form = $('#chat-form');
const messageEl = $('#message');
const statusEl = $('#status');
const statusTextEl = $('#status .text');
const hintEl = $('#hint');
const result = $('#result');
const banner = $('#banner');
const assistantEl = $('#assistant');
const timelineEl = $('#timeline');
const policyEl = $('#policy');
const metaEl = $('#meta');
const sendBtn = $('#send');

let elapsedTimer = null;

function setStatus(mode, text) {
  statusEl.className = 'status ' + mode;
  statusTextEl.textContent = text;
}

function startElapsed() {
  const start = Date.now();
  elapsedTimer = setInterval(() => {
    const s = ((Date.now() - start) / 1000).toFixed(0);
    hintEl.textContent = `${s}s elapsed · gpt-5 baseline · multi-tool call`;
  }, 500);
}

function stopElapsed() {
  if (elapsedTimer) clearInterval(elapsedTimer);
  elapsedTimer = null;
}

function clearResult() {
  result.classList.add('hidden');
  banner.className = '';
  banner.textContent = '';
  assistantEl.textContent = '';
  timelineEl.innerHTML = '';
  policyEl.innerHTML = '';
  metaEl.innerHTML = '';
  hintEl.textContent = '';
  setStatus('idle', 'Idle');
}

samples.forEach(btn => btn.addEventListener('click', () => {
  messageEl.value = btn.dataset.message;
  const atts = JSON.parse(btn.dataset.attachments || '[]');
  $$('input[name=attachments]').forEach(cb => cb.checked = atts.includes(cb.value));
  clearResult();
}));

messageEl.addEventListener('input', () => {
  if (!result.classList.contains('hidden')) clearResult();
});

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const message = messageEl.value.trim();
  if (!message) return;
  const attachments = $$('input[name=attachments]:checked').map(cb => cb.value);

  sendBtn.disabled = true;
  setStatus('busy', 'Contoso concierge is working…');
  startElapsed();
  result.classList.add('hidden');

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, attachments }),
    });
    const data = await res.json();
    if (data.error) {
      setStatus('error', `Agent error (HTTP ${data.status_code || res.status})`);
      hintEl.textContent = (data.error || '').slice(0, 120);
    } else {
      render(data);
      setStatus(data.policy?.hard_gate_blocked ? 'error' : 'done',
        data.policy?.hard_gate_blocked
          ? 'Blocked by Caldova policy (hard gate).'
          : 'Concierge completed.');
      hintEl.textContent = '';
    }
  } catch (err) {
    setStatus('error', 'Error: ' + err.message);
  } finally {
    stopElapsed();
    sendBtn.disabled = false;
  }
});

function render(data) {
  result.classList.remove('hidden');

  const blocked = !!(data.policy && data.policy.hard_gate_blocked);
  banner.className = blocked ? 'blocked' : 'ok';
  banner.textContent = blocked
    ? 'BLOCKED — Caldova policy hard gate stopped this action. Cited rules: ' + (data.policy.cited_rule_ids || []).join(', ')
    : 'Compliant — cited rules: ' + ((data.policy && data.policy.cited_rule_ids) || []).join(', ');

  assistantEl.textContent = data.assistant || '(no assistant text)';

  timelineEl.innerHTML = '';
  for (const step of (data.tool_timeline || [])) {
    const li = document.createElement('li');
    li.innerHTML = `<div><span class="tool">${step.tool}</span></div>
                    <details><summary>arguments &amp; result</summary>
                    <pre>${escape_(JSON.stringify(step.arguments, null, 2))}\n---\n${escape_(JSON.stringify(step.result, null, 2))}</pre>
                    </details>`;
    timelineEl.appendChild(li);
  }

  policyEl.innerHTML = '';
  const blocked_decisions = (data.policy && data.policy.blocked_decisions) || [];
  if (blocked_decisions.length === 0) {
    const cited = (data.policy && data.policy.cited_rule_ids) || [];
    if (cited.length === 0) {
      const li = document.createElement('li');
      li.textContent = 'No policy citations produced.';
      policyEl.appendChild(li);
    } else {
      cited.forEach(r => {
        const li = document.createElement('li');
        li.innerHTML = `<span class="rid">${r}</span> Cited and passed.`;
        policyEl.appendChild(li);
      });
    }
  } else {
    blocked_decisions.forEach(d => {
      const li = document.createElement('li');
      li.className = 'block';
      li.innerHTML = `<span class="rid">${d.rule_id}</span><b>${d.title}</b> — ${d.reason}<br><em>${d.remediation || ''}</em>`;
      policyEl.appendChild(li);
    });
  }

  const u = data.usage || {};
  const prompt = u.prompt_tokens ?? u.input_tokens ?? '-';
  const completion = u.completion_tokens ?? u.output_tokens ?? '-';
  const total = u.total_tokens ?? '-';
  const cached = u.input_tokens_details?.cached_tokens ?? '-';
  metaEl.innerHTML = `
    <div><div class="k">Variant</div><div class="v">${data.variant || '-'}</div></div>
    <div><div class="k">Model</div><div class="v">${data.model || '-'}</div></div>
    <div><div class="k">Prompt tok</div><div class="v">${prompt}</div></div>
    <div><div class="k">Completion tok</div><div class="v">${completion}</div></div>
    <div><div class="k">Total tok</div><div class="v">${total}</div></div>
    <div><div class="k">Cached tok</div><div class="v">${cached}</div></div>
  `;
}

function escape_(s) { return s.replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'})[c]); }
