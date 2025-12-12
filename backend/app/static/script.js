// --- Constants & Config ---
const STORAGE_KEY = 'ai-grader-pro-config';

// --- DOM Elements ---
const navItems = document.querySelectorAll('.nav-item');
const views = document.querySelectorAll('.view-section');

// Workspace
const fileInput = document.getElementById('fileInput');
const dropZone = document.getElementById('dropZone');
const browseBtn = document.getElementById('browseBtn'); // New button
const fileStatusBar = document.getElementById('fileStatusBar');
const fileInfo = document.getElementById('fileInfo');
const startBtn = document.getElementById('startBtn');
const statusText = document.getElementById('statusText');
const progress = document.getElementById('progress');
const progressBar = document.getElementById('progressBar');
const summaryCard = document.getElementById('summaryCard');
const summary = document.getElementById('summary');
const avgScoreDisplay = document.getElementById('avgScoreDisplay');
const resultLink = document.getElementById('resultLink');
const errorLink = document.getElementById('errorLink');

// Settings
const apiUrl = document.getElementById('apiUrl');
const apiKey = document.getElementById('apiKey');
const modelName = document.getElementById('modelName');
const template = document.getElementById('template');
const skipFormatCheck = document.getElementById('skipFormatCheck');
const mockMode = document.getElementById('mockMode');

// Rules Editor
const promptCategory = document.getElementById('promptCategory');
const sectionsContainer = document.getElementById('sectionsContainer');
const addSectionBtn = document.getElementById('addSectionBtn');
const savePromptConfigBtn = document.getElementById('savePromptConfig');
const refreshRulesBtn = document.getElementById('refreshRulesBtn');
const promptSaveStatus = document.getElementById('promptSaveStatus');

let promptConfigCache = null;
let currentPromptCategoryKey = null;

// --- 1. Navigation & View Manager ---

function switchView(viewId) {
  // Update Nav
  navItems.forEach(nav => {
    if (nav.dataset.view === viewId) nav.classList.add('active');
    else nav.classList.remove('active');
  });

  // Update View
  views.forEach(view => {
    if (view.id === viewId) view.classList.add('active');
    else view.classList.remove('active');
  });
  
  // Lazy Load Logic
  if (viewId === 'view-rules' && !promptConfigCache) {
    loadPromptRules();
  }
}

navItems.forEach(btn => {
  btn.addEventListener('click', () => {
    const targetView = btn.dataset.view;
    if(targetView) switchView(targetView);
  });
});

// --- 2. Configuration Persistence ---

function loadConfig() {
  const cache = localStorage.getItem(STORAGE_KEY);
  if (!cache) return;
  try {
    const cfg = JSON.parse(cache);
    if(apiUrl) apiUrl.value = cfg.apiUrl || '';
    if(apiKey) apiKey.value = cfg.apiKey || '';
    if(modelName) modelName.value = cfg.modelName || '';
    if(template) template.value = cfg.template || '职业规划书与专业分析报告的自动分类';
    if(skipFormatCheck) skipFormatCheck.checked = cfg.skipFormatCheck !== false;
    if(mockMode) mockMode.checked = Boolean(cfg.mockMode);
  } catch (e) {
    console.warn('Config Load Error', e);
  }
}

function saveConfig() {
  const cfg = {
    apiUrl: apiUrl.value,
    apiKey: apiKey.value,
    modelName: modelName.value,
    template: template.value,
    skipFormatCheck: skipFormatCheck.checked,
    mockMode: mockMode.checked,
  };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(cfg));
}

// Auto-save settings on change
[apiUrl, apiKey, modelName, template, skipFormatCheck, mockMode].forEach(el => {
  if(el) el.addEventListener('change', saveConfig);
});

// --- 3. File Handling ---

function updateFileStatus() {
  const files = fileInput.files;
  if (!files || files.length === 0) {
    fileInfo.innerHTML = '等待文件导入...';
    dropZone.classList.remove('has-file');
    return;
  }
  const count = files.length;
  const sizeMB = (Array.from(files).reduce((a, f) => a + f.size, 0) / 1024 / 1024).toFixed(2);
  
  fileInfo.innerHTML = `<span style="color:var(--signal-success);font-weight:600">✓ 已就绪 ${count} 个文件</span> <span style="margin:0 8px;opacity:0.3">|</span> ${sizeMB} MB`;
  dropZone.classList.add('has-file');
}

if(dropZone) {
    dropZone.addEventListener('click', () => fileInput.click());
    dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('drag-over'); });
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropZone.classList.remove('drag-over');
      fileInput.files = e.dataTransfer.files;
      updateFileStatus();
    });
}

if(browseBtn) browseBtn.addEventListener('click', (e) => {
    e.stopPropagation(); // prevent double trigger
    fileInput.click();
});

if(fileInput) fileInput.addEventListener('change', updateFileStatus);

// --- 4. Grading Logic (Workspace) ---

startBtn.addEventListener('click', async () => {
  const files = fileInput.files;
  if (!files || files.length === 0) {
    alert('请先上传作业文件');
    return;
  }
  if (!mockMode.checked && !apiUrl.value) {
    alert('请前往 [参数配置] 设置 API 信息');
    switchView('view-settings');
    return;
  }

  // UI State: Processing
  startBtn.disabled = true;
  startBtn.innerHTML = '<span class="spin">⟳</span> 处理中...';
  statusText.className = 'status-badge processing';
  statusText.textContent = 'PROCESSING';
  progress.classList.remove('hidden');
  progressBar.style.width = '5%';
  summaryCard.classList.add('hidden');

  const formData = new FormData();
  Array.from(files).forEach(f => formData.append('files', f));
  formData.append('api_url', apiUrl.value);
  formData.append('api_key', apiKey.value);
  formData.append('model_name', modelName.value);
  formData.append('template', template.value);
  formData.append('skip_format_check', skipFormatCheck.checked);
  formData.append('mock', mockMode.checked);

  // Fake Progress
  let progressVal = 5;
  const timer = setInterval(() => {
    if (progressVal < 90) {
      progressVal += Math.random() * 5;
      progressBar.style.width = progressVal + '%';
    }
  }, 500);

  try {
    const resp = await fetch('/api/grade', { method: 'POST', body: formData });
    clearInterval(timer);
    
    if (!resp.ok) {
        const errJson = await resp.json();
        throw new Error(errJson.detail || 'API Error');
    }

    const data = await resp.json();
    progressBar.style.width = '100%';
    
    setTimeout(() => {
      renderResult(data);
      statusText.className = 'status-badge ready';
      statusText.textContent = 'COMPLETED';
    }, 600);

  } catch (err) {
    clearInterval(timer);
    console.error(err);
    statusText.className = 'status-badge error';
    statusText.textContent = 'FAILED';
    alert('批改失败: ' + err.message);
  } finally {
    startBtn.disabled = false;
    startBtn.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg> 开始批改';
    setTimeout(() => {
        progress.classList.add('hidden');
        progressBar.style.width = '0';
    }, 2000);
  }
});

function renderResult(data) {
  summaryCard.classList.remove('hidden');
  avgScoreDisplay.textContent = data.average_score ?? 'N/A';
  
  summary.innerHTML = `
    <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:16px; margin-bottom:24px;">
      <div><small>总文件</small><div style="font-size:20px;font-weight:700">${data.total_files}</div></div>
      <div><small>成功</small><div style="font-size:20px;font-weight:700;color:var(--signal-success)">${data.success_count}</div></div>
      <div><small>异常</small><div style="font-size:20px;font-weight:700;color:${data.error_count > 0 ? 'var(--signal-error)' : 'inherit'}">${data.error_count}</div></div>
    </div>
  `;
  
  resultLink.href = data.download_result_url;
  errorLink.href = data.download_error_url;
}

// --- 5. Rules Editor (Embedded) ---

async function loadPromptRules() {
  try {
    const resp = await fetch('/api/prompt-config');
    const data = await resp.json();
    promptConfigCache = data.config;
    renderPromptUI();
  } catch (e) {
    console.error('Failed to load rules', e);
  }
}

function renderPromptUI() {
  if (!promptConfigCache) return;
  
  // Category Select
  promptCategory.innerHTML = '';
  Object.keys(promptConfigCache.categories).forEach(k => {
    const opt = document.createElement('option');
    opt.value = k;
    opt.textContent = promptConfigCache.categories[k].display_name;
    promptCategory.appendChild(opt);
  });
  
  if (currentPromptCategoryKey) promptCategory.value = currentPromptCategoryKey;
  else currentPromptCategoryKey = promptCategory.value;

  renderSections();
}

function renderSections() {
  sectionsContainer.innerHTML = '';
  const category = promptConfigCache.categories[currentPromptCategoryKey];
  if (!category) return;

  category.sections.forEach((sec, sIdx) => {
    const el = document.createElement('div');
    el.className = 'section-item';
    el.innerHTML = `
      <div class="section-header-row">
        <div style="flex:1">
           <label style="font-size:11px;color:#9CA3AF;text-transform:uppercase;">评分大项名称</label>
           <input type="text" class="section-title-input" value="${sec.key}" data-s="${sIdx}" data-f="key" placeholder="例如：逻辑结构">
        </div>
        <div>
           <label style="font-size:11px;color:#9CA3AF;text-transform:uppercase;display:block;text-align:center;">满分</label>
           <input type="number" class="section-score-input" value="${sec.max_score}" data-s="${sIdx}" data-f="max_score" placeholder="分">
        </div>
        <button class="btn-icon-danger" data-action="del-sec" data-s="${sIdx}" title="删除此大项">
           <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
        </button>
      </div>
      
      <div class="rule-items-grid items-list-${sIdx}"></div>
      
      <button class="btn-ghost primary" data-action="add-item" data-s="${sIdx}" style="font-size:13px; margin-top:16px; width:100%; border-style:dashed;">
        + 添加一条评分细则
      </button>
    `;
    
    const list = el.querySelector(`.items-list-${sIdx}`);
    sec.items.forEach((item, iIdx) => {
      const row = document.createElement('div');
      row.className = 'rule-item-row';
      row.innerHTML = `
         <div>
            <input type="text" value="${item.key}" data-s="${sIdx}" data-i="${iIdx}" data-f="key" placeholder="细则名称">
         </div>
         <div>
            <input type="number" step="0.5" value="${item.max_score}" data-s="${sIdx}" data-i="${iIdx}" data-f="max_score" placeholder="分值" style="text-align:center">
         </div>
         <div>
            <textarea rows="1" data-s="${sIdx}" data-i="${iIdx}" data-f="description" placeholder="评分说明（Prompt提示词）" style="resize:vertical;min-height:38px">${item.description || ''}</textarea>
         </div>
         <button class="btn-icon-danger" data-action="del-item" data-s="${sIdx}" data-i="${iIdx}" style="width:28px;height:28px;background:transparent;">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
         </button>
      `;
      list.appendChild(row);
    });
    
    sectionsContainer.appendChild(el);
  });
}

// Editor Event Delegation (Fixed)
sectionsContainer.addEventListener('click', (e) => {
  const t = e.target.closest('[data-action]'); // 关键修复：查找最近的带 action 的父元素
  if(!t) return;
  
  const act = t.dataset.action;
  const s = Number(t.dataset.s);
  // dataset.i 可能是 undefined，需要小心处理
  const i = t.dataset.i !== undefined ? Number(t.dataset.i) : null;
  const cat = promptConfigCache.categories[currentPromptCategoryKey];
  
  if (act === 'del-sec') {
    cat.sections.splice(s, 1);
  } else if (act === 'add-item') {
    cat.sections[s].items.push({key:'新细则', max_score:1, description:''});
  } else if (act === 'del-item' && i !== null) {
    cat.sections[s].items.splice(i, 1);
  }
  
  renderSections();
});

addSectionBtn.addEventListener('click', () => {
   if(!promptConfigCache || !currentPromptCategoryKey) return;
   promptConfigCache.categories[currentPromptCategoryKey].sections.push({
     key: '新评分大项', max_score: 10, items: []
   });
   renderSections();
});

savePromptConfigBtn.addEventListener('click', async () => {
  try {
     savePromptConfigBtn.disabled = true;
     savePromptConfigBtn.textContent = '保存中...';
     
     const resp = await fetch('/api/prompt-config', {
       method: 'POST', 
       headers: {'Content-Type': 'application/json'},
       body: JSON.stringify(promptConfigCache)
     });
     
     if(resp.ok) {
       promptSaveStatus.textContent = '配置已保存';
       promptSaveStatus.style.color = 'var(--signal-success)';
       setTimeout(() => promptSaveStatus.textContent = '', 2000);
       
       // 同步更新主界面的模板选择
       renderPromptUI();
     } else {
       throw new Error('Save failed');
     }
  } catch(e) {
    alert('保存失败，请检查网络');
    promptSaveStatus.textContent = '保存失败';
    promptSaveStatus.style.color = 'var(--signal-error)';
  } finally {
    savePromptConfigBtn.disabled = false;
    savePromptConfigBtn.textContent = '保存变更';
  }
});

function renderPromptUI() {
  if (!promptConfigCache) return;
  
  // 1. Update Rules Editor Category Select
  const oldVal = promptCategory.value;
  promptCategory.innerHTML = '';
  
  // 2. Update Main Settings Template Select
  const oldTemplateVal = template.value;
  template.innerHTML = ''; // Clear existing hardcoded options
  
  Object.keys(promptConfigCache.categories).forEach(k => {
    const display = promptConfigCache.categories[k].display_name || k;
    
    // For Rules Editor
    const opt1 = document.createElement('option');
    opt1.value = k;
    opt1.textContent = display;
    promptCategory.appendChild(opt1);
    
    // For Main Settings
    const opt2 = document.createElement('option');
    opt2.value = display; // Note: Backend likely expects display name or key depending on logic.
    // Based on original HTML, it used the display name value. 
    // Ideally we should verify if backend expects 'key' or 'display_name'. 
    // Assuming display name for now as per original code.
    opt2.textContent = display;
    template.appendChild(opt2);
  });
  
  // Restore selections
  if (currentPromptCategoryKey && promptConfigCache.categories[currentPromptCategoryKey]) {
    promptCategory.value = currentPromptCategoryKey;
  } else {
    currentPromptCategoryKey = promptCategory.value;
  }
  
  // Attempt to keep template selection
  if (oldTemplateVal) {
     // Check if old value exists in new options to avoid invalid selection
     const exists = Array.from(template.options).some(o => o.value === oldTemplateVal);
     if(exists) template.value = oldTemplateVal;
  }

  renderSections();
}

promptCategory.addEventListener('change', () => {
  currentPromptCategoryKey = promptCategory.value;
  renderSections();
});

if(refreshRulesBtn) refreshRulesBtn.addEventListener('click', loadPromptRules);

// --- Init ---
loadConfig();
// Pre-load prompt rules so template dropdown is populated immediately
loadPromptRules();

// Add spin animation
const style = document.createElement('style');
style.textContent = `.spin { display:inline-block; animation: spin 1s linear infinite; } @keyframes spin { 100% {transform: rotate(360deg);} }`;
document.head.appendChild(style);
