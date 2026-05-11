/* ── Nexora AI — Frontend App ─────────────────────────────────────────────── */
const API = '';   // same origin

/* ── State ───────────────────────────────────────────────────────────────── */
let currentSessionId = null;
let messageHistory   = [];
let selectedIcon     = '💊';
let symptoms         = [];
let isRecording      = false;
let recognition      = null;
let deferredInstallPrompt = null;

/* ── DOM refs ────────────────────────────────────────────────────────────── */
const chatMessages  = document.getElementById('chatMessages');
const chatInput     = document.getElementById('chatInput');
const sendBtn       = document.getElementById('sendBtn');
const voiceBtn      = document.getElementById('voiceBtn');
const sessionList   = document.getElementById('sessionList');
const chatTitle     = document.getElementById('chatTitle');
const toast         = document.getElementById('toast');
const installAppBtn = document.getElementById('installAppBtn');
const offlineBanner = document.getElementById('offlineBanner');

window.addEventListener('beforeinstallprompt', event => {
  event.preventDefault();
  deferredInstallPrompt = event;
  if (!isStandaloneApp() && installAppBtn) installAppBtn.hidden = false;
});

window.addEventListener('appinstalled', () => {
  deferredInstallPrompt = null;
  if (installAppBtn) installAppBtn.hidden = true;
  showToast('Nexora AI installed');
});

/* ── Init ────────────────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  registerAppShell();
  setupInstallPrompt();
  syncOnlineStatus();
  openInitialPage();
  loadSessions();
  loadReminders();
  loadRecords();
  setupVoice();

  // Nav
  document.querySelectorAll('.nav-item').forEach(btn => {
    btn.addEventListener('click', () => {
      const page = btn.dataset.page;
      switchPage(page);
      btn.closest('.sidebar-nav').querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    });
  });

  // New chat
  document.getElementById('newChatBtn').addEventListener('click', newChat);

  // Send
  sendBtn.addEventListener('click', sendMessage);
  chatInput.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  });
  chatInput.addEventListener('input', () => {
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 160) + 'px';
  });

  // Quick prompts
  document.querySelectorAll('.quick-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      chatInput.value = btn.dataset.prompt;
      sendMessage();
    });
  });

  // Theme toggle
  document.getElementById('themeToggle').addEventListener('click', () => {
    const html = document.documentElement;
    const isDark = html.dataset.theme === 'dark';
    html.dataset.theme = isDark ? 'light' : 'dark';
    document.getElementById('themeToggle').textContent = isDark ? '☀️' : '🌙';
  });

  // Sidebar toggle (mobile)
  document.getElementById('sidebarToggle').addEventListener('click', () => {
    document.getElementById('sidebar').classList.toggle('open');
  });

  // Voice
  voiceBtn.addEventListener('click', toggleVoice);

  // Symptom checker
  document.getElementById('symptomInput').addEventListener('keydown', e => {
    if (e.key === 'Enter' && e.target.value.trim()) {
      addSymptom(e.target.value.trim());
      e.target.value = '';
    }
  });
  document.querySelectorAll('.chip').forEach(chip => {
    chip.addEventListener('click', () => addSymptom(chip.dataset.symptom));
  });
  document.getElementById('analyzeBtn').addEventListener('click', analyzeSymptoms);

  // Calc tabs
  document.querySelectorAll('.calc-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.calc-tab').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.calc-panel').forEach(p => p.classList.remove('active'));
      tab.classList.add('active');
      document.getElementById('calc-' + tab.dataset.calc).classList.add('active');
    });
  });

  // Reminders
  document.getElementById('addReminderBtn').addEventListener('click', addReminder);
  document.getElementById('clearDoneBtn').addEventListener('click', clearDoneReminders);
  document.querySelectorAll('.icon-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.icon-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      selectedIcon = btn.dataset.icon;
    });
  });

  // Records
  document.getElementById('addRecordBtn').addEventListener('click', addRecord);
});

window.addEventListener('online', () => {
  syncOnlineStatus();
  showToast('Back online');
});

window.addEventListener('offline', () => {
  syncOnlineStatus();
  showToast('Offline mode enabled', 'error');
});

function registerAppShell() {
  if (!('serviceWorker' in navigator)) return;
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/service-worker.js').catch(() => {});
  });
}

function setupInstallPrompt() {
  if (!installAppBtn) return;
  if (isStandaloneApp()) {
    installAppBtn.hidden = true;
    return;
  }
  installAppBtn.addEventListener('click', async () => {
    if (!deferredInstallPrompt) {
      showToast('Use your browser menu to install Nexora AI');
      return;
    }
    deferredInstallPrompt.prompt();
    await deferredInstallPrompt.userChoice.catch(() => null);
    deferredInstallPrompt = null;
    installAppBtn.hidden = true;
  });
}

function isStandaloneApp() {
  return window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true;
}

function syncOnlineStatus() {
  if (!offlineBanner) return;
  offlineBanner.hidden = navigator.onLine;
}

function openInitialPage() {
  const requested = new URLSearchParams(window.location.search).get('page');
  const allowed = ['chat', 'symptoms', 'calculators', 'reminders', 'records'];
  if (!allowed.includes(requested)) return;
  switchPage(requested);
  document.querySelectorAll('.nav-item').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.page === requested);
  });
}

/* ── Page switching ──────────────────────────────────────────────────────── */
function switchPage(page) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById('page-' + page).classList.add('active');
  if (history.replaceState) {
    const url = page === 'chat' ? '/' : `/?page=${encodeURIComponent(page)}`;
    history.replaceState(null, '', url);
  }
}

/* ── Toast ───────────────────────────────────────────────────────────────── */
function showToast(msg, type = 'success') {
  toast.textContent = msg;
  toast.className = `toast show ${type}`;
  setTimeout(() => toast.classList.remove('show'), 3000);
}

/* ── Sessions ────────────────────────────────────────────────────────────── */
async function loadSessions() {
  try {
    const sessions = await apiFetch('/api/sessions');
    sessionList.innerHTML = '';
    sessions.forEach(s => {
      const el = document.createElement('div');
      el.className = 'session-item' + (s.id === currentSessionId ? ' active' : '');
      el.innerHTML = `
        <span class="session-title">💬 ${escHtml(s.title)}</span>
        <button class="session-del" data-id="${s.id}">✕</button>
      `;
      el.addEventListener('click', e => {
        if (!e.target.classList.contains('session-del')) loadSession(s.id, s.title);
      });
      el.querySelector('.session-del').addEventListener('click', e => {
        e.stopPropagation();
        deleteSession(s.id);
      });
      sessionList.appendChild(el);
    });
  } catch {}
}

async function loadSession(id, title) {
  currentSessionId = id;
  chatTitle.textContent = title;
  messageHistory = [];
  chatMessages.innerHTML = '';
  try {
    const msgs = await apiFetch(`/api/sessions/${id}/messages`);
    msgs.forEach(m => {
      messageHistory.push({ role: m.role, content: m.content });
      appendMessage(m.role, m.content);
    });
  } catch {}
  loadSessions();
  switchPage('chat');
  document.querySelectorAll('.nav-item').forEach(b => {
    b.classList.toggle('active', b.dataset.page === 'chat');
  });
}

async function deleteSession(id) {
  await apiFetch(`/api/sessions/${id}`, 'DELETE');
  if (currentSessionId === id) newChat();
  else loadSessions();
}

function newChat() {
  currentSessionId = crypto.randomUUID();
  messageHistory   = [];
  chatTitle.textContent = 'Nexora AI';
  chatMessages.innerHTML = `
    <div class="welcome-card">
      <div class="welcome-icon">🧬</div>
      <h3>Hello! I'm Nexora AI</h3>
      <p>Your intelligent healthcare companion. Ask me anything about health, wellness, symptoms, nutrition, or mental wellbeing.</p>
      <div class="quick-prompts">
        <button class="quick-btn" data-prompt="What are the symptoms of diabetes?">🩸 Diabetes symptoms</button>
        <button class="quick-btn" data-prompt="How can I improve my sleep quality?">😴 Better sleep tips</button>
        <button class="quick-btn" data-prompt="What foods boost the immune system?">🥦 Immune boosting foods</button>
        <button class="quick-btn" data-prompt="How do I manage stress and anxiety?">🧘 Stress management</button>
        <button class="quick-btn" data-prompt="What is a healthy daily routine?">📅 Healthy daily routine</button>
        <button class="quick-btn" data-prompt="How much water should I drink daily?">💧 Daily water intake</button>
      </div>
    </div>`;
  document.querySelectorAll('.quick-btn').forEach(btn => {
    btn.addEventListener('click', () => { chatInput.value = btn.dataset.prompt; sendMessage(); });
  });
  loadSessions();
}

/* ── Chat ────────────────────────────────────────────────────────────────── */
async function sendMessage() {
  const text = chatInput.value.trim();
  if (!text) return;

  if (!currentSessionId) currentSessionId = crypto.randomUUID();

  chatInput.value = '';
  chatInput.style.height = 'auto';

  // Remove welcome card
  const welcome = chatMessages.querySelector('.welcome-card');
  if (welcome) welcome.remove();

  appendMessage('user', text);
  messageHistory.push({ role: 'user', content: text });

  const typingEl = appendTyping();
  sendBtn.disabled = true;

  try {
    const data = await apiFetch('/api/chat', 'POST', {
      session_id: currentSessionId,
      messages:   messageHistory,
    });
    typingEl.remove();
    appendMessage('assistant', data.reply);
    messageHistory.push({ role: 'assistant', content: data.reply });
    chatTitle.textContent = messageHistory[0]?.content?.slice(0, 40) || 'Chat';
    loadSessions();
  } catch (err) {
    typingEl.remove();
    appendMessage('assistant', '⚠️ ' + (err.message || 'Something went wrong. Please check your API key.'));
  } finally {
    sendBtn.disabled = false;
  }
}

function appendMessage(role, content) {
  const div = document.createElement('div');
  div.className = `message ${role}`;
  div.innerHTML = `
    <div class="msg-avatar">${role === 'user' ? '👤' : '🧬'}</div>
    <div class="msg-bubble">${formatMessage(content)}</div>`;
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return div;
}

function appendTyping() {
  const div = document.createElement('div');
  div.className = 'message assistant';
  div.innerHTML = `
    <div class="msg-avatar">🧬</div>
    <div class="msg-bubble">
      <div class="typing-indicator">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
      </div>
    </div>`;
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return div;
}

function formatMessage(text) {
  return text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/^### (.+)$/gm, '<strong>$1</strong>')
    .replace(/^## (.+)$/gm, '<strong>$1</strong>')
    .replace(/^# (.+)$/gm, '<strong>$1</strong>')
    .replace(/^[-•] (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>')
    .replace(/^(.+)$/, '<p>$1</p>');
}

/* ── Voice Input ─────────────────────────────────────────────────────────── */
function setupVoice() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) { voiceBtn.style.display = 'none'; return; }
  recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.onresult = e => {
    chatInput.value = e.results[0][0].transcript;
    chatInput.dispatchEvent(new Event('input'));
  };
  recognition.onend = () => {
    isRecording = false;
    voiceBtn.classList.remove('recording');
    voiceBtn.textContent = '🎤';
  };
}

function toggleVoice() {
  if (!recognition) return;
  if (isRecording) {
    recognition.stop();
  } else {
    recognition.start();
    isRecording = true;
    voiceBtn.classList.add('recording');
    voiceBtn.textContent = '🔴';
  }
}

/* ── Symptom Checker ─────────────────────────────────────────────────────── */
function addSymptom(s) {
  if (!s || symptoms.includes(s)) return;
  symptoms.push(s);
  renderSymptomTags();
}

function removeSymptom(s) {
  symptoms = symptoms.filter(x => x !== s);
  renderSymptomTags();
}

function renderSymptomTags() {
  const container = document.getElementById('symptomTags');
  container.innerHTML = symptoms.map(s => `
    <span class="tag">${escHtml(s)}<span class="tag-remove" onclick="removeSymptom('${escHtml(s)}')">×</span></span>
  `).join('');
}

async function analyzeSymptoms() {
  if (!symptoms.length) { showToast('Add at least one symptom', 'error'); return; }
  const btn = document.getElementById('analyzeBtn');
  btn.disabled = true;
  btn.textContent = '⏳ Analyzing...';
  try {
    const data = await apiFetch('/api/symptoms', 'POST', {
      symptoms,
      body_area: document.getElementById('bodyArea').value,
      severity:  document.getElementById('severity').value,
      duration:  document.getElementById('duration').value,
    });
    const result = document.getElementById('symptomResult');
    document.getElementById('symptomResultContent').innerHTML = formatMessage(data.reply);
    result.classList.remove('hidden');
    result.scrollIntoView({ behavior: 'smooth' });
  } catch (err) {
    showToast(err.message || 'Analysis failed', 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = '🔍 Analyze Symptoms';
  }
}

/* ── Calculators ─────────────────────────────────────────────────────────── */
async function calcBMI() {
  const weight = parseFloat(document.getElementById('bmiWeight').value);
  const height = parseFloat(document.getElementById('bmiHeight').value);
  const unit   = document.getElementById('bmiUnit').value;
  if (!weight || !height) { showToast('Enter weight and height', 'error'); return; }
  const data = await apiFetch('/api/calc/bmi', 'POST', { weight, height, unit });
  const el = document.getElementById('bmiResult');
  el.classList.remove('hidden');
  el.innerHTML = `
    <div class="bmi-gauge">
      <div class="bmi-value" style="color:${data.color}">${data.bmi}</div>
      <div class="bmi-cat" style="color:${data.color}">${data.category}</div>
      <div class="bmi-bar"><div class="bmi-needle" style="left:${data.needle_pct}%"></div></div>
      <div style="display:flex;justify-content:space-between;font-size:11px;color:var(--text2)">
        <span>Underweight</span><span>Normal</span><span>Overweight</span><span>Obese</span>
      </div>
    </div>
    <p class="bmi-advice">${data.advice}</p>`;
}

async function calcCalories() {
  const age      = parseFloat(document.getElementById('calAge').value);
  const weight   = parseFloat(document.getElementById('calWeight').value);
  const height   = parseFloat(document.getElementById('calHeight').value);
  const gender   = document.getElementById('calGender').value;
  const activity = parseFloat(document.getElementById('calActivity').value);
  const goal     = document.getElementById('calGoal').value;
  if (!age || !weight || !height) { showToast('Fill all fields', 'error'); return; }
  const data = await apiFetch('/api/calc/calories', 'POST', { age, gender, weight, height, activity, goal });
  const el = document.getElementById('caloriesResult');
  el.classList.remove('hidden');
  el.innerHTML = `
    <div class="macro-grid">
      <div class="macro-card"><div class="macro-val">${data.bmr}</div><div class="macro-lbl">BMR (kcal)</div></div>
      <div class="macro-card"><div class="macro-val">${data.tdee}</div><div class="macro-lbl">TDEE (kcal)</div></div>
      <div class="macro-card"><div class="macro-val" style="color:var(--green)">${data.target}</div><div class="macro-lbl">Target (kcal)</div></div>
      <div class="macro-card"><div class="macro-val">${data.protein_g}g</div><div class="macro-lbl">Protein</div></div>
      <div class="macro-card"><div class="macro-val">${data.carbs_g}g</div><div class="macro-lbl">Carbs</div></div>
      <div class="macro-card"><div class="macro-val">${data.fat_g}g</div><div class="macro-lbl">Fat</div></div>
    </div>`;
}

async function calcWater() {
  const weight   = parseFloat(document.getElementById('waterWeight').value);
  const activity = parseFloat(document.getElementById('waterActivity').value);
  const climate  = parseFloat(document.getElementById('waterClimate').value);
  if (!weight) { showToast('Enter your weight', 'error'); return; }
  const data = await apiFetch('/api/calc/water', 'POST', { weight, activity, climate });
  const el = document.getElementById('waterResult');
  el.classList.remove('hidden');
  el.innerHTML = `
    <div class="water-result">
      <div class="water-big">${data.litres}</div>
      <div class="water-unit">litres / day</div>
      <div class="water-sub">
        <span>🥤 ${data.cups} cups</span>
        <span>💧 ${data.ml} ml</span>
      </div>
    </div>`;
}

async function calcIdeal() {
  const height = parseFloat(document.getElementById('idealHeight').value);
  const gender = document.getElementById('idealGender').value;
  if (!height) { showToast('Enter your height', 'error'); return; }
  const data = await apiFetch('/api/calc/ideal-weight', 'POST', { height, gender });
  const el = document.getElementById('idealResult');
  el.classList.remove('hidden');
  el.innerHTML = `
    <div class="ideal-result">
      <div class="ideal-range">${data.low} – ${data.high} kg</div>
      <div class="ideal-sub">Ideal: <strong>${data.ideal} kg</strong> for ${data.gender} at ${data.height_cm} cm</div>
      <p class="bmi-advice" style="margin-top:12px">Based on the Devine formula. Individual healthy weight varies — consult your doctor for personalised guidance.</p>
    </div>`;
}

/* ── Reminders ───────────────────────────────────────────────────────────── */
async function loadReminders() {
  try {
    const reminders = await apiFetch('/api/reminders');
    renderReminders(reminders);
  } catch {}
}

function renderReminders(reminders) {
  const list = document.getElementById('remindersList');
  if (!reminders.length) {
    list.innerHTML = '<p style="color:var(--text2);text-align:center;padding:24px">No reminders yet. Add one!</p>';
    return;
  }
  list.innerHTML = reminders.map(r => `
    <div class="reminder-card ${r.done ? 'done' : ''}" id="rem-${r.id}">
      <div class="reminder-icon">${r.icon}</div>
      <div class="reminder-info">
        <div class="reminder-title">${escHtml(r.title)}</div>
        <div class="reminder-meta">⏰ ${r.time} · 🔁 ${r.repeat}${r.notes ? ' · ' + escHtml(r.notes) : ''}</div>
      </div>
      <div class="reminder-actions">
        <button class="rem-check ${r.done ? 'done' : ''}" onclick="toggleReminder(${r.id})">${r.done ? '✓' : ''}</button>
        <button class="rem-del" onclick="deleteReminder(${r.id})">🗑</button>
      </div>
    </div>`).join('');
}

async function addReminder() {
  const title = document.getElementById('remTitle').value.trim();
  const time  = document.getElementById('remTime').value;
  if (!title) { showToast('Enter a title', 'error'); return; }
  try {
    await apiFetch('/api/reminders', 'POST', {
      title, time,
      repeat: document.getElementById('remRepeat').value,
      notes:  document.getElementById('remNotes').value.trim(),
      icon:   selectedIcon,
      color:  '#E6F1FB',
    });
    document.getElementById('remTitle').value = '';
    document.getElementById('remNotes').value = '';
    showToast('Reminder added ✓');
    loadReminders();
  } catch (err) {
    showToast(err.message || 'Failed to add reminder', 'error');
  }
}

async function toggleReminder(id) {
  await apiFetch(`/api/reminders/${id}/toggle`, 'PATCH');
  loadReminders();
}

async function deleteReminder(id) {
  await apiFetch(`/api/reminders/${id}`, 'DELETE');
  showToast('Reminder deleted');
  loadReminders();
}

async function clearDoneReminders() {
  await apiFetch('/api/reminders/done/clear', 'DELETE');
  showToast('Cleared done reminders');
  loadReminders();
}

/* ── Health Records ──────────────────────────────────────────────────────── */
async function loadRecords() {
  try {
    const records = await apiFetch('/api/records');
    renderRecords(records);
  } catch {}
}

function renderRecords(records) {
  const list = document.getElementById('recordsList');
  if (!records.length) {
    list.innerHTML = '<p style="color:var(--text2);text-align:center;padding:24px">No records yet. Log your first health data!</p>';
    return;
  }
  list.innerHTML = records.map(r => `
    <div class="record-card">
      <span class="record-type-badge">${escHtml(r.type)}</span>
      <div>
        <div class="record-data">${escHtml(r.data)}</div>
        ${r.notes ? `<div class="record-meta">${escHtml(r.notes)}</div>` : ''}
        <div class="record-meta">${formatDate(r.recorded_at)}</div>
      </div>
      <button class="record-del" onclick="deleteRecord(${r.id})">🗑</button>
    </div>`).join('');
}

async function addRecord() {
  const data = document.getElementById('recData').value.trim();
  if (!data) { showToast('Enter a value', 'error'); return; }
  try {
    await apiFetch('/api/records', 'POST', {
      type:  document.getElementById('recType').value,
      data,
      notes: document.getElementById('recNotes').value.trim(),
    });
    document.getElementById('recData').value = '';
    document.getElementById('recNotes').value = '';
    showToast('Record logged ✓');
    loadRecords();
  } catch (err) {
    showToast(err.message || 'Failed to log record', 'error');
  }
}

async function deleteRecord(id) {
  await apiFetch(`/api/records/${id}`, 'DELETE');
  showToast('Record deleted');
  loadRecords();
}

/* ── API helper ──────────────────────────────────────────────────────────── */
async function apiFetch(path, method = 'GET', body = null) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body) opts.body = JSON.stringify(body);
  let res;
  try {
    res = await fetch(API + path, opts);
  } catch {
    throw new Error('You are offline. Connect to the internet to use AI and saved data.');
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  if (res.status === 204) return null;
  return res.json();
}

/* ── Utils ───────────────────────────────────────────────────────────────── */
function escHtml(str) {
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function formatDate(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}
