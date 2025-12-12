const fileInput = document.getElementById('fileInput');
const dropZone = document.getElementById('dropZone');
const fileInfo = document.getElementById('fileInfo');
const apiUrl = document.getElementById('apiUrl');
const apiKey = document.getElementById('apiKey');
const modelName = document.getElementById('modelName');
const template = document.getElementById('template');
const skipFormatCheck = document.getElementById('skipFormatCheck');
const mockMode = document.getElementById('mockMode');
const openPromptEditor = document.getElementById('openPromptEditor');
const closePromptEditor = document.getElementById('closePromptEditor');
const promptModal = document.getElementById('promptModal');
const promptCategory = document.getElementById('promptCategory');
const sectionsContainer = document.getElementById('sectionsContainer');
const addSectionBtn = document.getElementById('addSectionBtn');
const savePromptConfigBtn = document.getElementById('savePromptConfig');
const promptSaveStatus = document.getElementById('promptSaveStatus');
const startBtn = document.getElementById('startBtn');
const statusText = document.getElementById('statusText');
const progress = document.getElementById('progress');
const progressBar = document.getElementById('progressBar');
const summary = document.getElementById('summary');
const summaryCard = document.getElementById('summaryCard'); // New container
const downloadLinks = document.getElementById('downloadLinks');
const resultLink = document.getElementById('resultLink');
const errorLink = document.getElementById('errorLink');

const STORAGE_KEY = 'ai-homework-config';

let promptConfigCache = null;
let currentPromptCategoryKey = null;

// --- Initialization ---

function loadConfig() {
  const cache = localStorage.getItem(STORAGE_KEY);
  if (!cache) return;
  try {
    const cfg = JSON.parse(cache);
    apiUrl.value = cfg.apiUrl || '';
    apiKey.value = cfg.apiKey || '';
    modelName.value = cfg.modelName || '';
    template.value = cfg.template || '职业规划书与专业分析报告的自动分类';
    skipFormatCheck.checked = cfg.skipFormatCheck !== false;
    mockMode.checked = Boolean(cfg.mockMode);
  } catch (e) {
    console.warn('读取缓存失败', e);
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

// --- File Handling (Drag & Drop + Input) ---

function updateFileInfo() {
  const files = fileInput.files;
  if (!files || files.length === 0) {
    fileInfo.innerHTML = '支持 .docx 格式';
    dropZone.classList.remove('has-file');
    return;
  }
  const count = files.length;
  const totalSize = Array.from(files).reduce((acc, f) => acc + f.size, 0);
  const sizeStr = (totalSize / 1024 / 1024).toFixed(2);
  
  fileInfo.innerHTML = `<span style="color:var(--brand-primary);font-weight:600;">已就绪 ${count} 个文件</span> (${sizeStr} MB)`;
  dropZone.classList.add('has-file');
}

// Click to upload
dropZone.addEventListener('click', () => fileInput.click());

// Drag & Drop visual effects
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
  dropZone.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
  e.preventDefault();
  e.stopPropagation();
}

['dragenter', 'dragover'].forEach(eventName => {
  dropZone.addEventListener(eventName, () => dropZone.classList.add('drag-over'), false);
});

['dragleave', 'drop'].forEach(eventName => {
  dropZone.addEventListener(eventName, () => dropZone.classList.remove('drag-over'), false);
});

dropZone.addEventListener('drop', handleDrop, false);

function handleDrop(e) {
  const dt = e.dataTransfer;
  const files = dt.files;
  
  // Filter for docx only if possible, or let backend handle it.
  // Ideally, we should check file.type or name extension here.
  
  fileInput.files = files; // Assign dropped files to input
  updateFileInfo();
}

fileInput.addEventListener('change', updateFileInfo);

// --- Core Logic ---

startBtn.addEventListener('click', async () => {
  const files = fileInput.files;
  if (!files || files.length === 0) {
    shakeElement(dropZone);
    return;
  }
  if (!mockMode.checked && !apiUrl.value) {
    shakeElement(document.querySelector('.config-card'));
    statusText.textContent = '请先配置 API Endpoint';
    return;
  }

  saveConfig();
  
  // UI State: Loading
  startBtn.disabled = true;
  startBtn.innerHTML = '<svg class="spin" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 1 1-6.219-8.56"></path></svg> 处理中...';
  statusText.textContent = '正在连接模型进行批改...';
  
  progress.classList.remove('hidden');
  progress.classList.add('active'); // Fade in
  progressBar.style.width = '5%'; // Start slightly
  
  // Hide results if re-running
  if(summaryCard) summaryCard.classList.add('hidden');

  const formData = new FormData();
  Array.from(files).forEach((f) => formData.append('files', f));
  formData.append('api_url', apiUrl.value);
  formData.append('api_key', apiKey.value);
  formData.append('model_name', modelName.value);
  formData.append('template', template.value);
  formData.append('skip_format_check', skipFormatCheck.checked);
  formData.append('mock', mockMode.checked);

  // Fake progress simulation to make it feel responsive
  let progressInterval = setInterval(() => {
    const currentW = parseFloat(progressBar.style.width) || 0;
    if (currentW < 90) {
      progressBar.style.width = (currentW + (Math.random() * 5)) + '%';
    }
  }, 800);

  try {
    const resp = await fetch('/api/grade', {
      method: 'POST',
      body: formData,
    });
    
    clearInterval(progressInterval);
    
    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.detail || '服务异常');
    }

    progressBar.style.width = '100%';
    const data = await resp.json();
    
    setTimeout(() => {
      renderSummary(data);
      statusText.textContent = '批改完成';
    }, 500); // Small delay for smooth 100% bar visual

  } catch (err) {
    clearInterval(progressInterval);
    progressBar.style.backgroundColor = 'var(--accent-error)';
    console.error(err);
    alert(err.message || '批改失败');
    statusText.textContent = '任务终止：' + (err.message || '未知错误');
  } finally {
    startBtn.disabled = false;
    startBtn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg> 初始化批改任务';
    
    // Hide progress bar after a while
    setTimeout(() => {
        progress.classList.remove('active');
        setTimeout(() => {
            progress.classList.add('hidden');
            progressBar.style.width = '0';
            progressBar.style.backgroundColor = 'var(--brand-primary)'; // Reset color
        }, 300);
    }, 2000);
  }
});

function renderSummary(data) {
  if(summaryCard) summaryCard.classList.remove('hidden');
  
  // High-end stat display
  summary.innerHTML = `
    <div class="stat-item">
      <h3>处理文件数</h3>
      <p>${data.total_files}</p>
    </div>
    <div class="stat-item">
      <h3>成功</h3>
      <p style="color:var(--accent-success)">${data.success_count}</p>
    </div>
    <div class="stat-item">
      <h3>失败</h3>
      <p style="${data.error_count > 0 ? 'color:var(--accent-error)' : ''}">${data.error_count}</p>
    </div>
    <div class="stat-item">
      <h3>平均分</h3>
      <p>${data.average_score ?? '-'}</p>
    </div>
  `;
  
  downloadLinks.classList.remove('hidden');
  resultLink.href = data.download_result_url;
  errorLink.href = data.download_error_url;
  
  // Smooth scroll to result
  summaryCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function shakeElement(el) {
  el.style.transform = 'translateX(-4px)';
  setTimeout(() => el.style.transform = 'translateX(4px)', 100);
  setTimeout(() => el.style.transform = 'translateX(-4px)', 200);
  setTimeout(() => el.style.transform = 'none', 300);
}

// Add CSS spin animation dynamically
const styleSheet = document.createElement("style");
styleSheet.innerText = `
@keyframes spin { 100% { transform: rotate(360deg); } }
.spin { animation: spin 1s linear infinite; }
`;
document.head.appendChild(styleSheet);

loadConfig();
updateFileInfo();

// --- 评分标准低代码编辑 ---

async function fetchPromptConfig() {
  const resp = await fetch('/api/prompt-config');
  if (!resp.ok) {
    throw new Error('获取提示词配置失败');
  }
  const data = await resp.json();
  if (!data.config) {
    throw new Error('提示词配置不存在，请联系管理员');
  }
  promptConfigCache = data.config;
  return promptConfigCache;
}

function openModal() {
  promptModal.classList.remove('hidden');
}

function closeModal() {
  promptModal.classList.add('hidden');
}

function renderCategorySelector() {
  promptCategory.innerHTML = '';
  const categories = promptConfigCache.categories || {};
  Object.keys(categories).forEach((key) => {
    const option = document.createElement('option');
    option.value = key;
    option.textContent = categories[key].display_name || key;
    promptCategory.appendChild(option);
  });
  if (!currentPromptCategoryKey) {
    currentPromptCategoryKey = promptCategory.value;
  } else {
    promptCategory.value = currentPromptCategoryKey;
  }
}

function renderSections() {
  sectionsContainer.innerHTML = '';
  const category = promptConfigCache.categories[currentPromptCategoryKey];
  if (!category) return;

  category.sections.forEach((section, secIndex) => {
    const secDiv = document.createElement('div');
    secDiv.className = 'section-card';

    secDiv.innerHTML = `
      <div class="section-header">
        <input type="text" value="${section.key}" data-sec-index="${secIndex}" data-field="key" placeholder="大项名称" />
        <input type="number" min="1" step="1" value="${section.max_score}" data-sec-index="${secIndex}" data-field="max_score" placeholder="分值" />
        <button class="btn-ghost small-btn" data-sec-index="${secIndex}" data-action="delete-section" type="button">删除大项</button>
      </div>
      <div data-sec-items="${secIndex}"></div>
      <button class="btn-ghost small-btn" data-sec-index="${secIndex}" data-action="add-item" type="button">添加小项</button>
    `;

    const itemsContainer = secDiv.querySelector(`[data-sec-items="${secIndex}"]`);
    section.items.forEach((item, itemIndex) => {
      const itemRow = document.createElement('div');
      itemRow.className = 'item-row';
      itemRow.innerHTML = `
        <input type="text" value="${item.key}" data-sec-index="${secIndex}" data-item-index="${itemIndex}" data-field="key" placeholder="小项名称" />
        <input type="number" min="1" step="0.5" value="${item.max_score}" data-sec-index="${secIndex}" data-item-index="${itemIndex}" data-field="max_score" placeholder="分值" />
        <textarea data-sec-index="${secIndex}" data-item-index="${itemIndex}" data-field="description" placeholder="评分说明">${item.description}</textarea>
        <button class="btn-ghost small-btn" data-sec-index="${secIndex}" data-item-index="${itemIndex}" data-action="delete-item" type="button">删除</button>
      `;
      itemsContainer.appendChild(itemRow);
    });

    sectionsContainer.appendChild(secDiv);
  });
}

function bindSectionEvents() {
  sectionsContainer.addEventListener('input', (e) => {
    const target = e.target;
    const secIndex = target.getAttribute('data-sec-index');
    const itemIndex = target.getAttribute('data-item-index');
    const field = target.getAttribute('data-field');
    if (secIndex === null || !field) return;

    const category = promptConfigCache.categories[currentPromptCategoryKey];
    const section = category.sections[Number(secIndex)];
    if (itemIndex !== null) {
      section.items[Number(itemIndex)][field] = field === 'max_score' ? Number(target.value) : target.value;
    } else {
      section[field] = field === 'max_score' ? Number(target.value) : target.value;
    }
  });

  sectionsContainer.addEventListener('click', (e) => {
    const target = e.target;
    const action = target.getAttribute('data-action');
    if (!action) return;
    const secIndex = Number(target.getAttribute('data-sec-index'));
    const category = promptConfigCache.categories[currentPromptCategoryKey];

    if (action === 'delete-section') {
      category.sections.splice(secIndex, 1);
      renderSections();
      return;
    }
    if (action === 'add-item') {
      category.sections[secIndex].items.push({ key: '新小项', max_score: 5, description: '请填写评分说明' });
      renderSections();
      return;
    }
    if (action === 'delete-item') {
      const itemIndex = Number(target.getAttribute('data-item-index'));
      category.sections[secIndex].items.splice(itemIndex, 1);
      renderSections();
    }
  });
}

addSectionBtn?.addEventListener('click', () => {
  const category = promptConfigCache.categories[currentPromptCategoryKey];
  category.sections.push({
    key: '新评分大项',
    max_score: 10,
    items: [{ key: '新小项', max_score: 5, description: '请填写评分说明' }],
  });
  renderSections();
});

savePromptConfigBtn?.addEventListener('click', async () => {
  promptSaveStatus.textContent = '正在保存...';
  try {
    const resp = await fetch('/api/prompt-config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(promptConfigCache),
    });
    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.detail || '保存失败');
    }
    promptSaveStatus.textContent = '保存成功，已同步到后端。';
  } catch (err) {
    promptSaveStatus.textContent = '保存失败：' + (err.message || '未知错误');
  }
});

promptCategory?.addEventListener('change', () => {
  currentPromptCategoryKey = promptCategory.value;
  renderSections();
});

openPromptEditor?.addEventListener('click', async () => {
  promptSaveStatus.textContent = '';
  try {
    await fetchPromptConfig();
    renderCategorySelector();
    renderSections();
    openModal();
  } catch (err) {
    alert(err.message || '打开配置失败');
  }
});

closePromptEditor?.addEventListener('click', closeModal);

bindSectionEvents();
