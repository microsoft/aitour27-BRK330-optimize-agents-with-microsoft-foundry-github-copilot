const select = (selector) => document.querySelector(selector);
const selectAll = (selector) => Array.from(document.querySelectorAll(selector));

const form = select('#chat-form');
const message = select('#message');
const send = select('#send');
const status = select('#status');
const statusDetail = select('#status-detail');
const result = select('#result');
const runtime = select('#runtime');

function text(value) {
  return value === null || value === undefined || value === '' ? '—' : String(value);
}

function setStatus(mode, title, detail) {
  status.className = `status ${mode}`;
  status.querySelector('strong').textContent = title;
  statusDetail.textContent = detail;
}

function addDefinition(list, label, value) {
  const term = document.createElement('dt');
  term.textContent = label;
  const description = document.createElement('dd');
  description.textContent = text(value);
  list.append(term, description);
}

function renderRuntime(data) {
  runtime.replaceChildren();
  const mark = document.createElement('span');
  mark.className = `runtime-status ${data.status === 'ok' ? 'ok' : 'bad'}`;
  const copy = document.createElement('span');
  copy.textContent = data.status === 'ok'
    ? `${data.agent} · v${data.active_version} · ${data.model} · ${data.configuration}`
    : `${data.agent || 'Hosted Agent'} unavailable`;
  runtime.append(mark, copy);
}

async function refreshRuntime() {
  try {
    const response = await fetch('/api/health');
    renderRuntime(await response.json());
  } catch (error) {
    renderRuntime({ status: 'degraded', error: error.message });
  }
}

selectAll('.sample').forEach((button) => {
  button.addEventListener('click', () => {
    message.value = button.dataset.message;
    const attachments = JSON.parse(button.dataset.attachments || '[]');
    selectAll('input[name="attachments"]').forEach((input) => {
      input.checked = attachments.includes(input.value);
    });
    result.hidden = true;
    setStatus('idle', 'Ready', 'Travel request loaded.');
  });
});

function renderToolTimeline(steps) {
  const timeline = select('#timeline');
  timeline.replaceChildren();
  if (!steps.length) {
    const item = document.createElement('li');
    item.className = 'empty-evidence';
    item.textContent = 'No travel or policy checks were captured.';
    timeline.append(item);
    return;
  }
  steps.forEach((step, index) => {
    const item = document.createElement('li');
    const heading = document.createElement('div');
    heading.className = 'tool-heading';
    heading.textContent = `${String(index + 1).padStart(2, '0')}  ${step.tool}`;
    const details = document.createElement('details');
    const summary = document.createElement('summary');
    summary.textContent = 'Request and result';
    const payload = document.createElement('pre');
    payload.textContent = `${JSON.stringify(step.arguments, null, 2)}\n---\n${JSON.stringify(step.result, null, 2)}`;
    details.append(summary, payload);
    item.append(heading, details);
    timeline.append(item);
  });
}

function addPolicyItem(list, className, message) {
  const item = document.createElement('li');
  if (className) item.className = className;
  item.textContent = message;
  list.append(item);
}

function renderGaps(list, policy) {
  if (policy.booking_status && policy.booking_status !== 'dry_run_success') {
    addPolicyItem(list, 'evidence-gap', `Booking not completed: ${policy.booking_reason || policy.booking_status}`);
  }
  (policy.empty_searches || []).forEach((tool) => {
    addPolicyItem(list, 'evidence-gap', `No matching options found by ${tool}.`);
  });
  (policy.excluded_receipt_lines || []).forEach((line) => {
    addPolicyItem(list, 'blocked', `${line.rule_id}: ${line.reason}`);
  });
}

function renderPolicy(policy) {
  const list = select('#policy');
  list.replaceChildren();
  renderGaps(list, policy);
  if (policy.blocked_decisions?.length) {
    policy.blocked_decisions.forEach((decision) => {
      const item = document.createElement('li');
      item.className = 'blocked';
      item.textContent = `${decision.rule_id}: ${decision.reason}`;
      list.append(item);
    });
    return;
  }
  if (policy.errors?.length) {
    policy.errors.forEach((error) => {
      const item = document.createElement('li');
      item.className = 'evidence-gap';
      item.textContent = `Policy check incomplete: ${error}`;
      list.append(item);
    });
    return;
  }
  if (policy.cited_rule_ids?.length) {
    policy.cited_rule_ids.forEach((rule) => {
      const item = document.createElement('li');
      item.textContent = `${rule}: cited from tool evidence`;
      list.append(item);
    });
    return;
  }
  const item = document.createElement('li');
  if (!policy.checked) item.className = 'evidence-gap';
  item.textContent = policy.checked
    ? 'Policy checks passed; no blocking policy rule was triggered.'
    : 'Approval not confirmed: no policy-check result was captured.';
  list.append(item);
}

function renderResult(data) {
  result.hidden = false;
  const decision = select('#decision');
  const outcome = data.outcome || { tone: 'warning', label: 'Not confirmed — no outcome returned' };
  decision.className = `decision ${outcome.tone}`;
  decision.textContent = outcome.label;
  select('#assistant').textContent = data.assistant || '(No assistant text returned.)';
  renderToolTimeline(data.tool_timeline || []);
  renderPolicy(data.policy || {});

  const metadata = select('#metadata');
  metadata.replaceChildren();
  const active = data.runtime || {};
  const usage = data.usage || {};
  addDefinition(metadata, 'Agent', active.agent);
  addDefinition(metadata, 'Active version', active.active_version);
  addDefinition(metadata, 'Latest version', active.latest_version);
  addDefinition(metadata, 'Model', data.model || active.model);
  addDefinition(metadata, 'Configuration', active.configuration);
  addDefinition(metadata, 'Instruction SHA', active.instruction_sha);
  addDefinition(metadata, 'Response ID', data.response_id);
  addDefinition(metadata, 'Latency', data.latency_ms ? `${data.latency_ms} ms` : null);
  addDefinition(metadata, 'Input tokens', usage.input_tokens ?? usage.prompt_tokens);
  addDefinition(metadata, 'Output tokens', usage.output_tokens ?? usage.completion_tokens);
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const request = message.value.trim();
  if (!request) return;
  const attachments = selectAll('input[name="attachments"]:checked').map((input) => input.value);
  send.disabled = true;
  result.hidden = true;
  setStatus('busy', 'Reviewing', 'Checking travel options and Caldova policy…');
  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: request, attachments }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
    renderResult(data);
    setStatus('done', 'Trip reviewed', `Reference ${text(data.response_id)}`);
    renderRuntime({ status: 'ok', ...data.runtime });
  } catch (error) {
    setStatus('error', 'Invocation failed', error.message);
  } finally {
    send.disabled = false;
  }
});

refreshRuntime();
