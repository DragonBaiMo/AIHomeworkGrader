const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('fileInfo');
const apiUrl = document.getElementById('apiUrl');
const apiKey = document.getElementById('apiKey');
const modelName = document.getElementById('modelName');
const template = document.getElementById('template');
const mockMode = document.getElementById('mockMode');
const startBtn = document.getElementById('startBtn');
const statusText = document.getElementById('statusText');
const progress = document.getElementById('progress');
const progressBar = document.getElementById('progressBar');
const summary = document.getElementById('summary');
const downloadLinks = document.getElementById('downloadLinks');
const resultLink = document.getElementById('resultLink');
const errorLink = document.getElementById('errorLink');

const STORAGE_KEY = 'ai-homework-config';

function loadConfig() {
  const cache = localStorage.getItem(STORAGE_KEY);
  if (!cache) return;
  try {
    const cfg = JSON.parse(cache);
    apiUrl.value = cfg.apiUrl || '';
    apiKey.value = cfg.apiKey || '';
    modelName.value = cfg.modelName || '';
    template.value = cfg.template || '职业规划';
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
    mockMode: mockMode.checked,
  };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(cfg));
}

function updateFileInfo() {
  const files = fileInput.files;
  if (!files || files.length === 0) {
    fileInfo.textContent = '未选择文件';
    return;
  }
  const details = Array.from(files).map((f) => `${f.name} (${(f.size / 1024).toFixed(1)} KB)`).join('，');
  fileInfo.textContent = `已选择 ${files.length} 个文件：${details}`;
}

fileInput.addEventListener('change', updateFileInfo);

startBtn.addEventListener('click', async () => {
  const files = fileInput.files;
  if (!files || files.length === 0) {
    alert('请先选择至少一个 docx 文件');
    return;
  }
  if (!mockMode.checked && !apiUrl.value) {
    alert('请填写模型接口地址，或启用离线模拟评分');
    return;
  }

  saveConfig();
  startBtn.disabled = true;
  statusText.textContent = '正在解析与评分，请稍候...';
  progress.classList.remove('hidden');
  progressBar.style.width = '30%';
  downloadLinks.classList.add('hidden');

  const formData = new FormData();
  Array.from(files).forEach((f) => formData.append('files', f));
  formData.append('api_url', apiUrl.value);
  formData.append('api_key', apiKey.value);
  formData.append('model_name', modelName.value);
  formData.append('template', template.value);
  formData.append('mock', mockMode.checked);

  try {
    const resp = await fetch('/api/grade', {
      method: 'POST',
      body: formData,
    });
    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.detail || '服务异常');
    }
    progressBar.style.width = '70%';
    const data = await resp.json();
    renderSummary(data);
    progressBar.style.width = '100%';
    statusText.textContent = '批改完成';
  } catch (err) {
    console.error(err);
    alert(err.message || '批改失败');
    statusText.textContent = '批改失败，请检查配置或文件格式';
  } finally {
    startBtn.disabled = false;
    setTimeout(() => progress.classList.add('hidden'), 1200);
  }
});

function renderSummary(data) {
  summary.innerHTML = `
    <p>批次 ID：${data.batch_id}</p>
    <p>总文件数：${data.total_files}</p>
    <p>成功评分：${data.success_count}</p>
    <p>异常文件：${data.error_count}</p>
    <p>平均分：${data.average_score ?? '暂无'}</p>
  `;
  downloadLinks.classList.remove('hidden');
  resultLink.href = data.download_result_url;
  errorLink.href = data.download_error_url;
}

loadConfig();
updateFileInfo();
