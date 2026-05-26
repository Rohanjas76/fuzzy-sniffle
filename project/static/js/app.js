// Face Recognition System — Main Script

/* ── DOM refs ── */
const dropZone       = document.getElementById('drop-zone');
const fileInput      = document.getElementById('file-input');
const previewArea    = document.getElementById('preview-area');
const previewImg     = document.getElementById('preview-img');
const previewName    = document.getElementById('preview-name');
const previewSize    = document.getElementById('preview-size');
const clearBtn       = document.getElementById('clear-btn');
const recognizeBtn   = document.getElementById('recognize-btn');
const errorMsg       = document.getElementById('error-msg');
const loadingOverlay = document.getElementById('loading-overlay');
const loadingStep    = document.getElementById('loading-step');
const resultSection  = document.getElementById('result-section');

let currentFile = null;

/* ── Drag and Drop ── */
['dragenter','dragover'].forEach(ev =>
  dropZone.addEventListener(ev, e => { e.preventDefault(); dropZone.classList.add('drag-over'); })
);
['dragleave','drop'].forEach(ev =>
  dropZone.addEventListener(ev, e => { e.preventDefault(); dropZone.classList.remove('drag-over'); })
);
dropZone.addEventListener('drop', e => {
  if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
});
dropZone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', () => {
  if (fileInput.files.length) handleFile(fileInput.files[0]);
});

/* ── File preview ── */
function handleFile(file) {
  if (!file.type.startsWith('image/')) {
    showError('Please upload a valid image file (PNG, JPG, JPEG, WEBP, BMP).');
    return;
  }
  if (file.size > 16 * 1024 * 1024) {
    showError('File too large. Maximum allowed size is 16 MB.');
    return;
  }
  hideError();
  currentFile = file;
  const reader = new FileReader();
  reader.onload = e => {
    previewImg.src = e.target.result;
    previewName.textContent = file.name.length > 30 ? file.name.slice(0,27)+'…' : file.name;
    previewSize.textContent = formatBytes(file.size);
    previewArea.classList.remove('hidden');
    recognizeBtn.disabled = false;
    resultSection.classList.add('hidden');
    resultSection.innerHTML = '';
  };
  reader.readAsDataURL(file);
}

clearBtn.addEventListener('click', () => {
  currentFile = null;
  fileInput.value = '';
  previewArea.classList.add('hidden');
  recognizeBtn.disabled = true;
  hideError();
  resultSection.classList.add('hidden');
  resultSection.innerHTML = '';
});

/* ── Recognition ── */
const LOADING_STEPS = [
  'Preprocessing image…',
  'Detecting all faces…',
  'Extracting embeddings…',
  'Matching against database…',
];

recognizeBtn.addEventListener('click', async () => {
  if (!currentFile) return;
  hideError();
  resultSection.classList.add('hidden');
  resultSection.innerHTML = '';

  loadingOverlay.classList.remove('hidden');
  const dots = document.querySelectorAll('.sdot');
  let stepIdx = 0;
  const stepInterval = setInterval(() => {
    stepIdx = (stepIdx + 1) % LOADING_STEPS.length;
    loadingStep.textContent = LOADING_STEPS[stepIdx];
    dots.forEach((d, i) => d.classList.toggle('active', i <= stepIdx));
  }, 700);

  const formData = new FormData();
  formData.append('image', currentFile);

  try {
    const res  = await fetch('/recognize', { method: 'POST', body: formData });
    const data = await res.json();
    clearInterval(stepInterval);
    loadingOverlay.classList.add('hidden');
    if (data.error) showError(data.error);
    else renderResult(data);
  } catch (err) {
    clearInterval(stepInterval);
    loadingOverlay.classList.add('hidden');
    showError('Server error — make sure Flask is running and try again.');
    console.error(err);
  }
});

/* ── Result rendering ── */
function renderResult(data) {
  const allFaces   = data.all_faces || [];
  const matchCount = allFaces.filter(f => f.matched).length;
  const total      = allFaces.length;
  const hasMatch   = matchCount > 0;

  /* ── Banner ── */
  const bannerHTML = `
    <div class="result-banner ${hasMatch ? 'match' : 'no-match'}">
      <div class="status-icon">${hasMatch ? '✅' : '❌'}</div>
      <div>
        <div class="status-title ${hasMatch ? 'match' : 'no-match'}">
          ${hasMatch ? `${matchCount} Person${matchCount>1?'s':''} Identified` : 'No Match Found'}
        </div>
        <div class="status-sub">
          ${total} face${total>1?'s':''} detected &nbsp;·&nbsp;
          ${data.known_faces_count} known ${data.known_faces_count===1?'identity':'identities'} in database
        </div>
      </div>
    </div>`;

  /* ── Annotated image ── */
  const primaryFace2 = allFaces.find(f => f.matched) || allFaces[0];
  const annotatedHTML = `
    <div class="result-img-box">
      <p class="result-img-label">Uploaded Image · Annotated</p>
      <img src="${data.result_image}" alt="Annotated result" style="width:100%;border-radius:10px;border:1px solid var(--border);" />
      ${primaryFace2 ? `
      <div style="margin-top:14px;text-align:center;">
        <div style="font-size:1.5rem;font-weight:800;color:var(--accent);">${primaryFace2.name}</div>
        <div style="font-size:2rem;font-weight:800;color:var(--green);margin-top:4px;">${primaryFace2.confidence.toFixed(1)}%</div>
        <div class="conf-bar-wrap" style="margin-top:8px;">
          <div class="conf-bar-fill ${primaryFace2.matched ? 'match' : 'no-match'}" id="bar-main" style="width:0%"></div>
        </div>
        <div class="badge-row" style="justify-content:center;margin-top:8px;">
          <span class="badge ${primaryFace2.matched ? 'green' : 'red'}">${primaryFace2.matched ? 'CONFIRMED MATCH' : 'NO MATCH'}</span>
        </div>
      </div>` : ''}
    </div>`;

  /* ── Best match DB image ── */
  const primaryFace   = allFaces.find(f => f.matched) || allFaces[0];
  const dbMatchHTML = data.db_image
    ? `<div class="result-img-box">
         <p class="result-img-label">Best Match · Database</p>
         <img src="${data.db_image}" alt="DB match" style="width:100%;border-radius:10px;border:1px solid var(--border);" />
       </div>`
    : `<div class="result-img-box">
         <p class="result-img-label">Best Match · Database</p>
         <div style="min-height:180px;border:1px dashed var(--border);border-radius:10px;display:flex;align-items:center;justify-content:center;color:var(--muted);font-size:.85rem;">No match found</div>
       </div>`;

  /* ── Per-face cards ── */
  const faceCardsHTML = allFaces.map((face, idx) => {
    const matched    = face.matched;
    const badgeClass = matched ? 'green' : 'red';
    const confClass  = matched ? 'match' : 'no-match';
    const barId      = `bar-${idx}`;
    return `
      <div class="face-card ${matched ? 'face-card-match' : 'face-card-unknown'}">
        <div class="face-card-header">
          <span class="face-num">#${idx + 1}</span>
          <span class="badge ${badgeClass}">${matched ? 'MATCHED' : 'UNKNOWN'}</span>
        </div>
        <div class="face-name">${face.name}</div>
        <div class="face-conf">${face.confidence.toFixed(1)}%</div>
        <div class="conf-bar-wrap" style="margin-top:8px;">
          <div class="conf-bar-fill ${confClass}" id="${barId}" style="width:0%"></div>
        </div>
        <div style="margin-top:10px;font-family:var(--ff-mono);font-size:.7rem;color:var(--muted);">
          distance: ${face.distance !== undefined ? face.distance.toFixed(4) : '—'}
        </div>
      </div>`;
  }).join('');

  /* ── Stats row ── */
  const statsHTML = `
    <div class="stats-row">
      <div class="stat-block">
        <div class="stat-label">Faces Detected</div>
        <div class="stat-value">${total}</div>
        <div class="badge-row"><span class="badge blue">HOG Detector</span></div>
      </div>
      <div class="stat-block">
        <div class="stat-label">Identified</div>
        <div class="stat-value" style="color:var(--green)">${matchCount}</div>
        <div class="badge-row"><span class="badge green">matched</span></div>
      </div>
      <div class="stat-block">
        <div class="stat-label">Unknown</div>
        <div class="stat-value" style="color:var(--red)">${total - matchCount}</div>
        <div class="badge-row"><span class="badge red">unmatched</span></div>
      </div>
      <div class="stat-block">
        <div class="stat-label">DB Size</div>
        <div class="stat-value">${data.known_faces_count}</div>
        <div class="badge-row"><span class="badge blue">128-d embeddings</span></div>
      </div>
      <div class="stat-block">
        <div class="stat-label">Facial Landmarks</div>
        <div class="stat-value">${data.landmark_count || '—'}</div>
        <div class="badge-row"><span class="badge blue">68-point model</span></div>
      </div>
    </div>`;

  resultSection.innerHTML = `
    <div class="result-card">
      ${bannerHTML}
      <div style="padding:28px 32px 0;">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-bottom:24px;">
          ${annotatedHTML}
          ${dbMatchHTML}
        </div>
        ${allFaces.length > 1 ? `<div><p class="result-img-label" style="margin-bottom:12px;">All Detected Persons</p><div class="face-cards-grid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px;max-height:none;">${faceCardsHTML}</div></div>` : ''}
      </div>
      <div style="padding:24px 32px 32px;">
        ${statsHTML}
      </div>
    </div>`;

  resultSection.classList.remove('hidden');

  /* Animate all confidence bars */
  setTimeout(() => {
    allFaces.forEach((face, idx) => {
      const bar = document.getElementById(`bar-${idx}`);
      if (bar) bar.style.width = face.confidence + '%';
    });
    const mainBar = document.getElementById('bar-main');
    if (mainBar && primaryFace2) mainBar.style.width = primaryFace2.confidence + '%';
  }, 200);

  resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/* ── Utilities ── */
function showError(msg) {
  errorMsg.textContent = msg;
  errorMsg.classList.remove('hidden');
}
function hideError() {
  errorMsg.classList.add('hidden');
  errorMsg.textContent = '';
}
function formatBytes(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}
