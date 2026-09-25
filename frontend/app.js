/**
 * OmniDoc AI — Intelligent Document Processing Platform Client
 * Frontend Application Controller
 */

// Global State
const state = {
  currentView: 'dashboard',
  documents: [],
  selectedDocId: null,
  currentDocData: null,
  activeFilter: 'all',
  currentUser: {
    name: 'Dr. Sarah Mitchell',
    role: 'Lead Compliance Officer',
    token: 'demo_token'
  }
};

// DOM Content Loaded Handler
document.addEventListener('DOMContentLoaded', () => {
  // Initialize Lucide icons
  if (window.lucide) {
    window.lucide.createIcons();
  }

  // Setup Event Listeners
  initNavigation();
  initThemeToggle();
  initUpload();
  initStudioTabs();
  initChat();
  initSearch();
  initDemoSelector();
  initAuth();

  // Load initial data
  loadDashboardData();
  loadDocuments();
  loadPortfolioData();
});

// ----------------- NAVIGATION -----------------
function initNavigation() {
  const navButtons = document.querySelectorAll('.nav-item');
  navButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const view = btn.getAttribute('data-view');
      switchView(view);
    });
  });

  document.getElementById('btnQuickUpload').addEventListener('click', () => {
    switchView('upload');
  });
}

function switchView(viewName) {
  state.currentView = viewName;

  // Update nav buttons
  document.querySelectorAll('.nav-item').forEach(b => {
    if (b.getAttribute('data-view') === viewName) {
      b.classList.add('active');
    } else {
      b.classList.remove('active');
    }
  });

  // Update panels
  document.querySelectorAll('.view-panel').forEach(p => p.classList.remove('active'));
  const targetPanel = document.getElementById(`view${capitalize(viewName)}`);
  if (targetPanel) {
    targetPanel.classList.add('active');
  }

  if (viewName === 'dashboard') {
    loadDashboardData();
  } else if (viewName === 'documents') {
    loadDocuments();
  } else if (viewName === 'portfolio') {
    loadPortfolioData();
  }

  // Re-render icons
  if (window.lucide) window.lucide.createIcons();
}

function capitalize(s) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

// ----------------- THEME TOGGLE -----------------
function initThemeToggle() {
  const toggleBtn = document.getElementById('btnThemeToggle');
  const icon = document.getElementById('themeIcon');
  
  toggleBtn.addEventListener('click', () => {
    document.body.classList.toggle('light-theme');
    document.body.classList.toggle('dark-theme');
    const isLight = document.body.classList.contains('light-theme');
    icon.setAttribute('data-lucide', isLight ? 'sun' : 'moon');
    if (window.lucide) window.lucide.createIcons();
  });
}

// ----------------- DASHBOARD & METRICS -----------------
async function loadDashboardData() {
  try {
    const res = await fetch('/api/dashboard/metrics');
    if (!res.ok) return;
    const data = await res.json();

    // Update KPI counters
    document.getElementById('kpiTotalDocs').textContent = data.total_documents;
    document.getElementById('kpiValidDocs').textContent = data.valid_documents;
    document.getElementById('kpiReviewDocs').textContent = data.needs_review;
    document.getElementById('kpiErrorDocs').textContent = data.high_risk_errors;
    document.getElementById('sidebarDocCount').textContent = data.total_documents;
    document.getElementById('topAccuracyText').textContent = `AI Accuracy: ${data.average_confidence}%`;

    // Render Recent Table
    const tbody = document.getElementById('dashboardTableBody');
    tbody.innerHTML = '';
    (data.recent_documents || []).forEach(doc => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>${escapeHtml(doc.title)}</strong></td>
        <td><span class="badge badge-category">${escapeHtml(doc.category)}</span></td>
        <td><span class="badge badge-conf">${doc.confidence}%</span></td>
        <td>${getStatusBadge(doc.status)}</td>
        <td>
          <button class="btn btn-xs btn-primary" onclick="openDocumentInStudio(${doc.id})">
            Inspect &rarr;
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });

    // Render Category Distribution Bars
    const catBars = document.getElementById('categoryBars');
    catBars.innerHTML = '';
    const total = data.total_documents || 1;
    (data.categories || []).forEach(cat => {
      const pct = Math.round((cat.count / total) * 100);
      const div = document.createElement('div');
      div.className = 'cat-bar-item';
      div.innerHTML = `
        <div class="cat-bar-meta">
          <span>${escapeHtml(cat.category)}</span>
          <span>${cat.count} doc (${pct}%)</span>
        </div>
        <div class="cat-bar-track">
          <div class="cat-bar-fill" style="width: ${pct}%; background: linear-gradient(90deg, #6366F1, #06B6D4);"></div>
        </div>
      `;
      catBars.appendChild(div);
    });

  } catch (err) {
    console.error('Failed to load dashboard metrics:', err);
  }
}

// ----------------- DOCUMENT QUEUE -----------------
async function loadDocuments() {
  try {
    const res = await fetch('/api/documents');
    if (!res.ok) return;
    state.documents = await res.json();
    renderDocumentsTable();
  } catch (err) {
    console.error('Failed to load documents:', err);
  }
}

function renderDocumentsTable() {
  const tbody = document.getElementById('fullDocsTableBody');
  if (!tbody) return;
  tbody.innerHTML = '';

  const filtered = state.documents.filter(d => {
    if (state.activeFilter === 'all') return true;
    if (state.activeFilter === 'valid') return d.validation_status === 'valid';
    if (state.activeFilter === 'warning') return d.validation_status === 'warning' || d.validation_status === 'needs_review';
    if (state.activeFilter === 'error') return d.validation_status === 'error';
    return true;
  });

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-muted); padding: 30px;">No documents match the selected filter.</td></tr>`;
    return;
  }

  filtered.forEach(d => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><span style="font-family: var(--font-mono); color: var(--text-muted);">#${d.id}</span></td>
      <td><strong>${escapeHtml(d.original_name)}</strong></td>
      <td><span class="badge badge-category">${escapeHtml(d.category)}</span></td>
      <td><span class="badge badge-conf">${Math.round(d.category_confidence * 100)}%</span></td>
      <td>${getStatusBadge(d.validation_status)}</td>
      <td>${d.page_count || 1} pg</td>
      <td><small style="color: var(--text-muted);">${formatTimestamp(d.created_at)}</small></td>
      <td>
        <button class="btn btn-xs btn-primary" onclick="openDocumentInStudio(${d.id})">
          Open Studio
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function getStatusBadge(status) {
  if (status === 'valid') {
    return `<span class="badge badge-valid"><i data-lucide="check-circle-2" style="width: 12px; height: 12px;"></i> VALID</span>`;
  } else if (status === 'warning' || status === 'needs_review') {
    return `<span class="badge badge-warning"><i data-lucide="alert-triangle" style="width: 12px; height: 12px;"></i> WARNING</span>`;
  } else {
    return `<span class="badge badge-error"><i data-lucide="alert-octagon" style="width: 12px; height: 12px;"></i> ACTION REQUIRED</span>`;
  }
}

// Status Filter Tabs
document.querySelectorAll('#statusFilterTabs .filter-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('#statusFilterTabs .filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    state.activeFilter = btn.getAttribute('data-status');
    renderDocumentsTable();
    if (window.lucide) window.lucide.createIcons();
  });
});

// ----------------- DOCUMENT INTELLIGENCE STUDIO -----------------
async function openDocumentInStudio(docId) {
  try {
    showToast('Loading document intelligence...', 'info');
    const res = await fetch(`/api/documents/${docId}`);
    if (!res.ok) {
      showToast('Document not found', 'error');
      return;
    }
    const doc = await res.json();
    state.selectedDocId = docId;
    state.currentDocData = doc;

    // Switch to studio view
    switchView('studio');

    // Populate Header Meta
    document.getElementById('studioDocTitle').textContent = doc.original_name;
    document.getElementById('studioCategoryBadge').textContent = `Category: ${doc.category}`;
    document.getElementById('studioConfidenceBadge').textContent = `AI Conf: ${Math.round(doc.category_confidence * 100)}%`;
    
    const statusBadge = document.getElementById('studioStatusBadge');
    statusBadge.className = `badge badge-${doc.validation_status === 'valid' ? 'valid' : doc.validation_status === 'warning' ? 'warning' : 'error'}`;
    statusBadge.textContent = `Status: ${doc.validation_status.toUpperCase()}`;

    // Load PDF Preview Frame
    const iframe = document.getElementById('pdfPreviewFrame');
    const textFallback = document.getElementById('textFallbackPreview');
    const btnDownload = document.getElementById('btnDownloadOriginal');

    btnDownload.href = `/api/documents/${docId}/file`;

    if (doc.filename.toLowerCase().endsWith('.pdf')) {
      iframe.style.display = 'block';
      textFallback.style.display = 'none';
      iframe.src = `/api/documents/${docId}/file`;
    } else {
      iframe.style.display = 'none';
      textFallback.style.display = 'block';
      textFallback.textContent = doc.raw_text;
    }

    // Populate Tab 1: Extracted Fields
    renderExtractedFields(doc.fields, doc.line_items);

    // Populate Tab 2: Validation
    renderValidationTab(doc.validation);

    // Populate Tab 3: Insights & Entities
    renderInsightsTab(doc.insights, doc.entities);

    // Populate Tab 4: Chat History
    loadChatHistory(docId);

    // Wire Export buttons
    document.getElementById('btnExportJson').onclick = () => {
      window.open(`/api/documents/${docId}/export/json`, '_blank');
    };
    document.getElementById('btnExportCsv').onclick = () => {
      window.open(`/api/documents/${docId}/export/csv`, '_blank');
    };
    document.getElementById('btnReprocess').onclick = () => {
      reprocessCurrentDocument(docId);
    };

    if (window.lucide) window.lucide.createIcons();
    showToast(`Loaded: ${doc.original_name}`, 'success');

  } catch (err) {
    console.error('Error opening studio:', err);
    showToast('Failed to load document studio', 'error');
  }
}

function renderExtractedFields(fields, lineItems) {
  const container = document.getElementById('extractedFieldsList');
  container.innerHTML = '';

  for (const [key, fieldData] of Object.entries(fields)) {
    const val = fieldData.value ?? '';
    const label = fieldData.label ?? key;
    const conf = Math.round((fieldData.confidence ?? 0.95) * 100);

    const row = document.createElement('div');
    row.className = 'field-item-row';
    row.innerHTML = `
      <div class="field-label">${escapeHtml(label)}</div>
      <div class="field-input-box">
        <input type="text" data-field-key="${key}" value="${escapeHtml(String(val))}" />
      </div>
      <div class="field-meta-pill">
        <span>${conf}% AI</span>
      </div>
    `;
    container.appendChild(row);
  }

  // Line items
  const lineSec = document.getElementById('lineItemsSection');
  const lineTbody = document.getElementById('lineItemsTableBody');
  if (lineItems && lineItems.length > 0) {
    lineSec.style.display = 'block';
    lineTbody.innerHTML = '';
    lineItems.forEach(item => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${escapeHtml(item.description || '')}</td>
        <td style="text-align: right;">${escapeHtml(item.quantity || '')}</td>
        <td style="text-align: right;">$${escapeHtml(item.unit_price || '')}</td>
        <td style="text-align: right; font-weight: 700;">$${escapeHtml(item.total || '')}</td>
      `;
      lineTbody.appendChild(tr);
    });
  } else {
    lineSec.style.display = 'none';
  }
}

// Live Save & Recalculate
document.getElementById('btnSaveFields').addEventListener('click', async () => {
  if (!state.selectedDocId || !state.currentDocData) return;

  const updatedFields = { ...state.currentDocData.fields };
  document.querySelectorAll('#extractedFieldsList input').forEach(input => {
    const key = input.getAttribute('data-field-key');
    if (updatedFields[key]) {
      updatedFields[key].value = input.value.trim();
    }
  });

  try {
    showToast('Recalculating validation rules...', 'info');
    const res = await fetch(`/api/documents/${state.selectedDocId}/fields`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fields: updatedFields })
    });
    const result = await res.json();
    if (result.status === 'success') {
      state.currentDocData.fields = updatedFields;
      state.currentDocData.validation = result.validation;
      state.currentDocData.insights = result.insights;

      // Update UI badges
      const statusBadge = document.getElementById('studioStatusBadge');
      statusBadge.className = `badge badge-${result.validation.status === 'valid' ? 'valid' : result.validation.status === 'warning' ? 'warning' : 'error'}`;
      statusBadge.textContent = `Status: ${result.validation.status.toUpperCase()}`;

      renderValidationTab(result.validation);
      renderInsightsTab(result.insights, state.currentDocData.entities);
      showToast('Fields updated & validation score recalculated!', 'success');
      loadDashboardData();
    }
  } catch (err) {
    console.error('Error saving fields:', err);
    showToast('Failed to update fields', 'error');
  }
});

function renderValidationTab(validation) {
  const issues = validation.issues || [];
  document.getElementById('studioIssuesCount').textContent = issues.length;

  const scoreNum = document.getElementById('valScoreNum');
  const scoreCircle = document.getElementById('valScoreCircle');
  const heading = document.getElementById('valStatusHeading');
  const desc = document.getElementById('valStatusDesc');

  const score = validation.validation_score ?? 100;
  scoreNum.textContent = score;

  if (validation.status === 'valid') {
    scoreCircle.style.borderColor = 'var(--color-success)';
    heading.textContent = 'All Compliance & Math Rules Passed';
    desc.textContent = 'No discrepancies, expiration risks, or high-liability anomalies were detected.';
  } else if (validation.status === 'warning') {
    scoreCircle.style.borderColor = 'var(--color-warning)';
    heading.textContent = 'Warning Flags Detected';
    desc.textContent = 'Non-critical issues or near-term expirations require secondary auditor confirmation.';
  } else {
    scoreCircle.style.borderColor = 'var(--color-danger)';
    heading.textContent = 'Critical Errors & Risk Violations';
    desc.textContent = 'Document violates financial arithmetic, compliance policies, or legal thresholds.';
  }

  const issuesList = document.getElementById('validationIssuesList');
  issuesList.innerHTML = '';

  if (issues.length === 0) {
    issuesList.innerHTML = `
      <div class="issue-card" style="border-color: var(--color-success-border); background: var(--color-success-bg);">
        <div class="issue-card-title" style="color: var(--color-success);"><i data-lucide="check-circle-2"></i> Verified Clean</div>
        <p class="issue-card-msg">All mathematical sums, date sequences, tax configurations, and legal clauses conform to enterprise policy.</p>
      </div>
    `;
  } else {
    issues.forEach(iss => {
      const card = document.createElement('div');
      card.className = `issue-card ${iss.severity}`;
      card.innerHTML = `
        <div class="issue-card-header">
          <div class="issue-card-title">
            <i data-lucide="${iss.severity === 'error' ? 'alert-octagon' : 'alert-triangle'}"></i>
            ${escapeHtml(iss.title)}
          </div>
          <span class="badge badge-${iss.severity === 'error' ? 'error' : 'warning'}">${iss.code}</span>
        </div>
        <p class="issue-card-msg">${escapeHtml(iss.message)}</p>
      `;
      issuesList.appendChild(card);
    });
  }

  if (window.lucide) window.lucide.createIcons();
}

function renderInsightsTab(insights, entities) {
  const container = document.getElementById('insightsList');
  container.innerHTML = '';

  (insights || []).forEach(ins => {
    const card = document.createElement('div');
    card.className = 'insight-card';
    card.innerHTML = `
      <span class="insight-badge">${escapeHtml(ins.badge || 'Insight')}</span>
      <h4>${escapeHtml(ins.title || '')}</h4>
      <p>${escapeHtml(ins.description || '')}</p>
      ${ins.action ? `<button class="insight-action-btn"><i data-lucide="arrow-right"></i> ${escapeHtml(ins.action)}</button>` : ''}
    `;
    container.appendChild(card);
  });

  const chipsBox = document.getElementById('entitiesChips');
  chipsBox.innerHTML = '';
  (entities || []).forEach(e => {
    const chip = document.createElement('div');
    chip.className = 'entity-chip';
    chip.innerHTML = `
      <span class="entity-chip-type">${escapeHtml(e.type)}</span>
      <span>${escapeHtml(e.value)}</span>
    `;
    chipsBox.appendChild(chip);
  });

  if (window.lucide) window.lucide.createIcons();
}

async function reprocessCurrentDocument(docId) {
  try {
    showToast('Re-processing with fresh AI layout extractor...', 'info');
    const res = await fetch(`/api/documents/${docId}/reprocess`, { method: 'POST' });
    if (res.ok) {
      showToast('Document successfully re-analyzed!', 'success');
      openDocumentInStudio(docId);
    }
  } catch (err) {
    showToast('Failed to reprocess document', 'error');
  }
}

// Studio Tabs Switching
function initStudioTabs() {
  document.querySelectorAll('.studio-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.studio-tab').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.studio-tab-content').forEach(c => c.classList.remove('active'));

      tab.classList.add('active');
      const target = tab.getAttribute('data-tab');
      const content = document.getElementById(`tabContent${capitalize(target)}`);
      if (content) content.classList.add('active');
      if (window.lucide) window.lucide.createIcons();
    });
  });
}

// ----------------- GROUNDED AI CHAT -----------------
function initChat() {
  const form = document.getElementById('chatForm');
  const input = document.getElementById('chatInput');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = input.value.trim();
    if (!query || !state.selectedDocId) return;

    input.value = '';
    appendChatMessage('user', query);

    try {
      const res = await fetch(`/api/documents/${state.selectedDocId}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });
      const data = await res.json();
      appendChatMessage('assistant', data.message, data.citations);
    } catch (err) {
      appendChatMessage('assistant', 'Sorry, I encountered an error analyzing that question against the document context.');
    }
  });
}

async function loadChatHistory(docId) {
  const stream = document.getElementById('chatMessagesStream');
  stream.innerHTML = '';
  try {
    const res = await fetch(`/api/documents/${docId}/chat`);
    const history = await res.json();
    if (history.length === 0) {
      appendChatMessage('assistant', `Hello! I am your **OmniDoc AI Assistant** for this document. Ask any question—I will provide answers grounded directly in the text with precise page and section citations.`);
    } else {
      history.forEach(msg => {
        appendChatMessage(msg.role, msg.message, msg.citations);
      });
    }
  } catch (err) {
    console.error('Error fetching chat history:', err);
  }
}

function appendChatMessage(role, text, citations = []) {
  const stream = document.getElementById('chatMessagesStream');
  const msgDiv = document.createElement('div');
  msgDiv.className = `chat-msg ${role}`;

  let citationsHtml = '';
  if (citations && citations.length > 0) {
    citationsHtml = `<div class="citation-box"><strong>Grounded Document Citations:</strong><br/>${citations.map(c => `📍 ${c.page || 'Page 1'} &bull; ${c.section || 'Document Body'}`).join('<br/>')}</div>`;
  }

  // Parse markdown-like bullets and bolding
  let formatted = escapeHtml(text)
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n\n/g, '<br/><br/>')
    .replace(/\n/g, '<br/>');

  msgDiv.innerHTML = `
    <div class="msg-avatar"><i data-lucide="${role === 'assistant' ? 'bot' : 'user'}"></i></div>
    <div class="msg-bubble">
      <div>${formatted}</div>
      ${citationsHtml}
    </div>
  `;

  stream.appendChild(msgDiv);
  stream.scrollTop = stream.scrollHeight;
  if (window.lucide) window.lucide.createIcons();
}

function askPreset(promptText) {
  document.getElementById('chatInput').value = promptText;
  document.getElementById('chatForm').dispatchEvent(new Event('submit'));
}

// ----------------- DRAG & DROP UPLOAD PIPELINE -----------------
function initUpload() {
  const dropzone = document.getElementById('fileDropzone');
  const fileInput = document.getElementById('fileInput');

  ['dragenter', 'dragover'].forEach(name => {
    dropzone.addEventListener(name, (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(name => {
    dropzone.addEventListener(name, (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
    });
  });

  dropzone.addEventListener('drop', (e) => {
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (fileInput.files.length > 0) {
      handleFileUpload(fileInput.files[0]);
    }
  });
}

async function handleFileUpload(file) {
  const procCard = document.getElementById('processingCard');
  procCard.style.display = 'block';

  document.getElementById('procFileName').textContent = file.name;
  document.getElementById('procFileSize').textContent = `${(file.size / 1024).toFixed(1)} KB &bull; Uploading to AI cluster`;

  resetStepper();

  // Step 1: Uploading
  setStageActive(1, 'Uploading document to secure processing pipeline...');
  const formData = new FormData();
  formData.append('file', file);

  try {
    await sleep(600);
    setStageCompleted(1);

    // Step 2: OCR & Layout
    setStageActive(2, 'Extracting layout primitives, character blocks, and table vectors...');
    await sleep(800);
    setStageCompleted(2);

    // Step 3: Classification
    setStageActive(3, 'Running deep taxonomy classifier against document tokens...');
    await sleep(700);
    setStageCompleted(3);

    // Step 4: Field Extraction
    setStageActive(4, 'Extracting structured schemas, line items, and named entities...');
    
    // Execute actual API upload call
    const res = await fetch('/api/documents/upload', {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Upload failed');
    }

    const data = await res.json();
    setStageCompleted(4);

    // Step 5: Validation
    setStageActive(5, 'Validating mathematical equations, expiry dates, and risk clauses...');
    await sleep(600);
    setStageCompleted(5);

    // Step 6: Insights
    setStageActive(6, 'Synthesizing executive insights and knowledge graphs...');
    await sleep(500);
    setStageCompleted(6);

    document.getElementById('stageStatusMessage').innerHTML = `
      <span style="color: var(--color-success); font-weight: 700;">
        🎉 Successfully processed! Classified as <u>${data.category}</u> (${Math.round(data.confidence * 100)}% confidence).
      </span>
    `;

    showToast(`Processed: ${file.name}`, 'success');

    // Auto open in Studio after brief moment
    await sleep(900);
    openDocumentInStudio(data.document_id);
    loadDashboardData();

  } catch (err) {
    console.error('Upload failed:', err);
    document.getElementById('stageStatusMessage').innerHTML = `
      <span style="color: var(--color-danger); font-weight: 700;">
        ❌ Processing Error: ${err.message}
      </span>
    `;
    showToast(`Error: ${err.message}`, 'error');
  }
}

function resetStepper() {
  for (let i = 1; i <= 6; i++) {
    const s = document.getElementById(`stage${i}`);
    if (s) {
      s.classList.remove('active', 'completed');
    }
    const l = document.getElementById(`line${i}`);
    if (l) {
      l.classList.remove('completed');
    }
  }
}

function setStageActive(stageNum, msg) {
  const s = document.getElementById(`stage${stageNum}`);
  if (s) s.classList.add('active');
  document.getElementById('stageStatusMessage').textContent = msg;
}

function setStageCompleted(stageNum) {
  const s = document.getElementById(`stage${stageNum}`);
  if (s) {
    s.classList.remove('active');
    s.classList.add('completed');
  }
  const l = document.getElementById(`line${stageNum}`);
  if (l) l.classList.add('completed');
}

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

// ----------------- DEMO SELECTOR -----------------
function initDemoSelector() {
  const select = document.getElementById('quickDemoSelect');
  select.addEventListener('change', (e) => {
    const val = e.target.value;
    if (val) {
      loadDemoScenario(val);
      select.value = '';
    }
  });
}

function loadDemoScenario(scenarioId) {
  openDocumentInStudio(scenarioId);
}

// ----------------- PORTFOLIO & CROSS-DOC INSIGHTS -----------------
async function loadPortfolioData() {
  try {
    const res = await fetch('/api/dashboard/cross-document-insights');
    if (!res.ok) return;
    const data = await res.json();

    // Render Suppliers List
    const vBox = document.getElementById('portfolioVendorsList');
    vBox.innerHTML = '';
    (data.active_entities || []).forEach(item => {
      const d = document.createElement('div');
      d.style.cssText = 'display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid var(--border-color); font-size: 0.84rem;';
      d.innerHTML = `<strong>${escapeHtml(item.name)}</strong><span class="badge badge-category">${item.frequency} documents</span>`;
      vBox.appendChild(d);
    });

    // Render Alerts
    const aBox = document.getElementById('portfolioAlertsList');
    aBox.innerHTML = '';
    (data.urgent_risk_alerts || []).forEach(alert => {
      const d = document.createElement('div');
      d.style.cssText = 'padding: 10px; background: var(--color-danger-bg); border-left: 3px solid var(--color-danger); border-radius: 4px; margin-bottom: 10px; font-size: 0.8rem;';
      d.innerHTML = `<strong>${escapeHtml(alert.issue)}</strong> &bull; <small>${escapeHtml(alert.doc_title)}</small><br/><span style="color: var(--text-secondary);">${escapeHtml(alert.message)}</span>`;
      aBox.appendChild(d);
    });

    // Render Deadlines
    const dBox = document.getElementById('portfolioDeadlinesList');
    dBox.innerHTML = '';
    (data.upcoming_deadlines || []).forEach(dl => {
      const d = document.createElement('div');
      d.style.cssText = 'display: inline-block; margin: 6px; padding: 10px 14px; background: rgba(255, 255, 255, 0.03); border: 1px solid var(--border-color); border-radius: var(--radius-sm); font-size: 0.8rem;';
      d.innerHTML = `<span style="color: var(--primary); font-weight: 700;">📅 ${escapeHtml(dl.date)}</span> &bull; <strong>${escapeHtml(dl.label)}</strong><br/><small style="color: var(--text-muted);">${escapeHtml(dl.doc_title)}</small>`;
      dBox.appendChild(d);
    });

  } catch (err) {
    console.error('Failed to load portfolio:', err);
  }
}

// ----------------- SEARCH -----------------
function initSearch() {
  const searchInput = document.getElementById('globalSearchInput');
  searchInput.addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase().trim();
    if (!q) {
      renderDocumentsTable();
      return;
    }
    const filtered = state.documents.filter(d => 
      d.original_name.toLowerCase().includes(q) ||
      d.category.toLowerCase().includes(q) ||
      d.validation_status.toLowerCase().includes(q)
    );
    
    // Switch to documents view to see search results
    if (state.currentView !== 'documents' && q.length > 2) {
      switchView('documents');
    }

    const tbody = document.getElementById('fullDocsTableBody');
    tbody.innerHTML = '';
    filtered.forEach(d => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>#${d.id}</td>
        <td><strong>${escapeHtml(d.original_name)}</strong></td>
        <td><span class="badge badge-category">${escapeHtml(d.category)}</span></td>
        <td>${Math.round(d.category_confidence * 100)}%</td>
        <td>${getStatusBadge(d.validation_status)}</td>
        <td>${d.page_count} pg</td>
        <td>${formatTimestamp(d.created_at)}</td>
        <td><button class="btn btn-xs btn-primary" onclick="openDocumentInStudio(${d.id})">Open</button></td>
      `;
      tbody.appendChild(tr);
    });
  });
}

// ----------------- AUTH MODAL -----------------
function initAuth() {
  document.getElementById('btnSwitchAuth').addEventListener('click', () => {
    document.getElementById('authModal').style.display = 'flex';
  });

  document.getElementById('formLogin').addEventListener('submit', async (e) => {
    e.preventDefault();
    const u = document.getElementById('loginUsername').value;
    const p = document.getElementById('loginPassword').value;
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: u, password: p })
      });
      const data = await res.json();
      if (res.ok) {
        setLoggedInUser(data.user);
        closeAuthModal();
        showToast(`Welcome back, ${data.user.full_name}!`, 'success');
      } else {
        showToast(data.detail || 'Login failed', 'error');
      }
    } catch (err) {
      showToast('Login connection error', 'error');
    }
  });

  document.getElementById('formRegister').addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      full_name: document.getElementById('regFullName').value,
      username: document.getElementById('regUsername').value,
      email: document.getElementById('regEmail').value,
      password: document.getElementById('regPassword').value,
      role: document.getElementById('regRole').value
    };
    try {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (res.ok) {
        setLoggedInUser(data.user);
        closeAuthModal();
        showToast(`Account created for ${data.user.full_name}!`, 'success');
      } else {
        showToast(data.detail || 'Registration failed', 'error');
      }
    } catch (err) {
      showToast('Registration error', 'error');
    }
  });
}

function closeAuthModal() {
  document.getElementById('authModal').style.display = 'none';
}

function switchAuthTab(tab) {
  const isLogin = tab === 'login';
  document.getElementById('tabBtnLogin').classList.toggle('active', isLogin);
  document.getElementById('tabBtnRegister').classList.toggle('active', !isLogin);
  document.getElementById('formLogin').style.display = isLogin ? 'flex' : 'none';
  document.getElementById('formRegister').style.display = isLogin ? 'none' : 'flex';
}

async function instantDemoLogin() {
  try {
    const res = await fetch('/api/auth/demo-login', { method: 'POST' });
    const data = await res.json();
    if (res.ok) {
      setLoggedInUser(data.user);
      closeAuthModal();
      showToast('Signed in with Demo Lead Auditor credentials', 'success');
    }
  } catch (err) {
    showToast('Demo login error', 'error');
  }
}

function setLoggedInUser(user) {
  state.currentUser = user;
  document.getElementById('userDisplayName').textContent = user.full_name;
  document.getElementById('userRole').textContent = user.role;
  document.getElementById('userInitial').textContent = user.full_name.charAt(0);
}

// ----------------- UTILS & TOAST -----------------
function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <i data-lucide="${type === 'success' ? 'check-circle' : type === 'error' ? 'alert-circle' : 'info'}"></i>
    <span>${escapeHtml(message)}</span>
  `;
  container.appendChild(toast);
  if (window.lucide) window.lucide.createIcons();

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function escapeHtml(text) {
  if (!text) return '';
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function formatTimestamp(ts) {
  if (!ts) return 'Just now';
  try {
    const d = new Date(ts);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  } catch (e) {
    return ts;
  }
}
