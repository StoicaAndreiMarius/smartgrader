/**
 * Submission upload + list manager for the test detail page.
 */

class SubmissionUploader {
    constructor(testId) {
        this.testId = testId;
        this.isUploading = false;
        this.init();
    }

    init() {
        this.imageInput = document.getElementById('image-uploads');
        this.zipInput = document.getElementById('zip-upload');
        this.imageUploadBtn = document.getElementById('upload-images-btn');
        this.zipUploadBtn = document.getElementById('upload-zip-btn');
        this.statusDiv = document.getElementById('upload-status');
        this.progressBar = document.getElementById('upload-progress-bar');
        this.progressText = document.getElementById('upload-progress-text');
        this.bindEvents();
    }

    bindEvents() {
        if (this.imageUploadBtn) {
            this.imageUploadBtn.addEventListener('click', () => this.imageInput && this.imageInput.click());
        }
        if (this.zipUploadBtn) {
            this.zipUploadBtn.addEventListener('click', () => this.zipInput && this.zipInput.click());
        }
        if (this.imageInput) {
            this.imageInput.addEventListener('change', (e) => {
                const files = Array.from(e.target.files || []);
                if (files.length > 0) {
                    this.handleImageUpload(files);
                }
            });
        }
        if (this.zipInput) {
            this.zipInput.addEventListener('change', (e) => {
                const file = (e.target.files || [])[0];
                if (file) {
                    this.handleZipUpload(file);
                }
            });
        }
        this.setupDragAndDrop();
    }

    setupDragAndDrop() {
        const dropZone = document.getElementById('upload-drop-zone');
        if (!dropZone) return;

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach((eventName) => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });

        ['dragenter', 'dragover'].forEach((eventName) => {
            dropZone.addEventListener(eventName, () => dropZone.classList.add('drag-over'));
        });

        ['dragleave', 'drop'].forEach((eventName) => {
            dropZone.addEventListener(eventName, () => dropZone.classList.remove('drag-over'));
        });

        dropZone.addEventListener('drop', (e) => {
            const files = Array.from(e.dataTransfer.files || []);
            if (files.length === 0) return;

            const isZip = files.length === 1 && files[0].name.endsWith('.zip');
            if (isZip) {
                this.handleZipUpload(files[0]);
                return;
            }

            const imageFiles = files.filter((file) => file.type.startsWith('image/'));
            if (imageFiles.length > 0) {
                this.handleImageUpload(imageFiles);
            } else {
                this.showError('Please drop image files or a zip file');
            }
        });
    }

    handleImageUpload(files) {
        if (this.isUploading) {
            this.showError('An upload is already in progress');
            return;
        }
        const validFiles = files.filter((file) => {
            if (!file.type.startsWith('image/')) {
                this.showError(`${file.name} is not an image file`);
                return false;
            }
            if (file.size > 10 * 1024 * 1024) {
                this.showError(`${file.name} is too large (max 10MB)`);
                return false;
            }
            return true;
        });
        if (!validFiles.length) return;
        this.showProgress(`Uploading ${validFiles.length} image(s)...`);
        this.uploadFiles(validFiles, false);
    }

    handleZipUpload(file) {
        if (this.isUploading) {
            this.showError('An upload is already in progress');
            return;
        }
        if (!file.name.endsWith('.zip')) {
            this.showError('Please select a ZIP file');
            return;
        }
        if (file.size > 50 * 1024 * 1024) {
            this.showError('ZIP file is too large (max 50MB)');
            return;
        }
        this.showProgress('Uploading ZIP file...');
        this.uploadFiles([file], true);
    }

    uploadFiles(files, isZip) {
        this.isUploading = true;
        this.disableUploadButtons();

        const formData = new FormData();
        if (isZip) {
            formData.append('zip_file', files[0]);
        } else {
            files.forEach((file) => formData.append('files', file));
        }

        const xhr = new XMLHttpRequest();
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percentComplete = Math.round((e.loaded / e.total) * 100);
                this.updateProgress(percentComplete, 'Uploading...');
            }
        });

        xhr.addEventListener('load', () => {
            this.isUploading = false;
            this.enableUploadButtons();
            this.hideProgress();

            const tryParse = () => {
                try {
                    return JSON.parse(xhr.responseText);
                } catch (err) {
                    return null;
                }
            };
            const data = tryParse();
            if (xhr.status === 200 && data) {
                this.handleUploadSuccess(data);
            } else {
                this.handleUploadError((data && data.error) || `Upload failed with status ${xhr.status}`);
            }
        });

        xhr.addEventListener('error', () => {
            this.isUploading = false;
            this.enableUploadButtons();
            this.hideProgress();
            this.handleUploadError('Network error occurred');
        });

        xhr.addEventListener('abort', () => {
            this.isUploading = false;
            this.enableUploadButtons();
            this.hideProgress();
            this.handleUploadError('Upload was cancelled');
        });

        xhr.open('POST', `/tests/${this.testId}/upload-submissions/`);
        xhr.send(formData);
    }

    handleUploadSuccess(data) {
        if (data.error) {
            this.showError(data.error);
            return;
        }
        if (data.results && data.results.length > 0) {
            const successCount = data.results.filter((r) => r.success).length;
            const totalCount = data.results.length;
            if (successCount === totalCount) {
                this.showSuccess(`✓ All ${successCount} submission(s) processed successfully!`);
            } else {
                this.showWarning(`Processed ${successCount}/${totalCount} submission(s)`);
            }
            this.displayResults(data.results);
            if (typeof window.loadSubmissions === 'function') {
                window.loadSubmissions();
            }
        } else {
            this.showSuccess(data.message || 'Upload completed');
        }
        if (this.imageInput) this.imageInput.value = '';
        if (this.zipInput) this.zipInput.value = '';
    }

    handleUploadError(message) {
        this.showError(message);
    }

    displayResults(results) {
        const resultsDiv = document.getElementById('upload-results');
        if (!resultsDiv) return;

        let html = '<div class="upload-results-container">';
        html += '<h4>Upload Results:</h4><ul class="results-list">';
        results.forEach((result) => {
            const icon = result.success ? '✓' : '✗';
            const className = result.success ? 'success' : 'error';
            const scoreText = result.success
                ? `Score: ${result.score}/${result.total} (${result.percentage}%)`
                : `Error: ${result.error}`;

            html += `
                <li class="result-item ${className}">
                    <span class="result-icon">${icon}</span>
                    <span class="result-filename">${result.filename}</span>
                    <span class="result-score">${scoreText}</span>
                </li>`;
        });
        html += '</ul></div>';
        resultsDiv.innerHTML = html;

        setTimeout(() => {
            resultsDiv.innerHTML = '';
        }, 10000);
    }

    showProgress(message) {
        if (this.statusDiv) {
            this.statusDiv.textContent = message;
            this.statusDiv.classList.add('visible');
        }
        if (this.progressBar) {
            this.progressBar.style.display = 'block';
            const fill = this.progressBar.querySelector('.progress-fill');
            if (fill) fill.style.width = '0%';
        }
        if (this.progressText) {
            this.progressText.textContent = message;
        }
    }

    updateProgress(percent, message) {
        if (this.progressBar) {
            const fill = this.progressBar.querySelector('.progress-fill');
            if (fill) fill.style.width = `${percent}%`;
        }
        if (this.progressText) {
            this.progressText.textContent = `${percent}% - ${message}`;
        }
        if (this.statusDiv) {
            this.statusDiv.textContent = `${message} ${percent}%`;
        }
    }

    hideProgress() {
        if (this.statusDiv) {
            setTimeout(() => this.statusDiv.classList.remove('visible'), 1500);
        }
        if (this.progressBar) {
            this.progressBar.style.display = 'none';
        }
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showWarning(message) {
        this.showNotification(message, 'warning');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type) {
        if (typeof Toast !== 'undefined' && Toast[type]) {
            Toast[type](message);
            return;
        }
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        document.body.appendChild(notification);

        setTimeout(() => notification.classList.add('show'), 10);
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);

        console.log(`[${type.toUpperCase()}] ${message}`);
    }

    disableUploadButtons() {
        if (this.imageUploadBtn) this.imageUploadBtn.disabled = true;
        if (this.zipUploadBtn) this.zipUploadBtn.disabled = true;
    }

    enableUploadButtons() {
        if (this.imageUploadBtn) this.imageUploadBtn.disabled = false;
        if (this.zipUploadBtn) this.zipUploadBtn.disabled = false;
    }
}

function escapeHtml(str) {
    return (str || '').replace(/[&<>"']/g, (c) => {
        const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
        return map[c] || c;
    });
}

let currentSubmissions = [];

function renderSubmissions(submissions) {
    const container = document.getElementById('submissions-list');
    if (!container) return;

    const letters = ['A', 'B', 'C', 'D', 'E'];
    currentSubmissions = submissions || [];

    if (!submissions || !submissions.length) {
        container.innerHTML = '<div class="empty-state">No submissions yet.</div>';
        return;
    }

    const rows = submissions
        .map((sub) => {
            const omrText = (sub.answers || [])
                .map((ans) => (ans === null || ans === undefined || ans < 0 ? '-' : letters[ans] || ans))
                .join(', ');
            return `
                <div class="submission-row" data-id="${sub.id}">
                    <div>
                        <div class="student">${escapeHtml(sub.student_name || 'Unnamed student')}</div>
                        <div class="submission-meta">${sub.score}/${sub.total} (${sub.percentage}%) • ${sub.submitted_at}</div>
                        <div class="submission-meta">OMR: ${escapeHtml(omrText)}</div>
                    </div>
                    <div class="name-edit">
                        <input data-field="first" type="text" placeholder="First name" value="${escapeHtml(sub.first_name)}" />
                        <input data-field="last" type="text" placeholder="Last name" value="${escapeHtml(sub.last_name)}" />
                    </div>
                    <div class="upload-actions" style="margin:0; justify-content:flex-end;">
                        <button class="btn btn-primary save-name-btn" data-id="${sub.id}">Save name</button>
                        <button class="btn btn-secondary view-stats-btn" data-id="${sub.id}" data-image="${sub.image_url || ''}">Details</button>
                    </div>
                </div>
            `;
        })
        .join('');

    container.innerHTML = rows;
    bindNameSaves();
    bindImageViews();
    bindStatsViews();
}

function updateMeta(count, average) {
    const metaSubmissions = document.getElementById('meta-submissions');
    if (metaSubmissions) metaSubmissions.textContent = `Submissions: ${count || 0}`;

    const metaAverage = document.getElementById('meta-average');
    if (metaAverage) metaAverage.textContent = `Average: ${average || 0}%`;

    const statCount = document.getElementById('stat-submission-count');
    if (statCount) statCount.textContent = count || 0;

    const statAverage = document.getElementById('stat-average');
    if (statAverage) statAverage.textContent = `${average || 0}%`;

    const statCount2 = document.getElementById('stat-submission-count-2');
    if (statCount2) statCount2.textContent = count || 0;

    const statAverage2 = document.getElementById('stat-average-2');
    if (statAverage2) statAverage2.textContent = `${average || 0}%`;
}

function bindNameSaves() {
    const buttons = document.querySelectorAll('.save-name-btn');
    buttons.forEach((btn) => {
        btn.onclick = () => {
            const row = btn.closest('.submission-row');
            if (!row) return;
            const subId = btn.dataset.id;
            const first = row.querySelector('input[data-field="first"]')?.value || '';
            const last = row.querySelector('input[data-field="last"]')?.value || '';
            if (!first.trim() || !last.trim()) {
                alert('First and last name are required');
                return;
            }

            btn.disabled = true;
            fetch(`/tests/${window.testId}/submissions/${subId}/update-name/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ first_name: first, last_name: last }),
            })
                .then((res) => res.json().then((data) => ({ ok: res.ok, data })))
                .then(({ ok, data }) => {
                    btn.disabled = false;
                    if (!ok || data.error) {
                        alert(data.error || 'Failed to update name');
                        return;
                    }
                    if (row.querySelector('.student')) {
                        row.querySelector('.student').textContent = data.full_name || 'Unnamed student';
                    }
                })
                .catch((err) => {
                    btn.disabled = false;
                    console.error(err);
                    alert('Failed to update name');
                });
        };
    });
}

function loadSubmissions() {
    const testId = window.testId || document.body.dataset.testId;
    if (!testId) return;
    fetch(`/tests/${testId}/submissions/`, { credentials: 'same-origin' })
        .then((res) => res.json().then((data) => ({ ok: res.ok, data })))
        .then(({ ok, data }) => {
            if (!ok || data.error) {
                console.error(data.error || 'Failed to load submissions');
                return;
            }
            if (Array.isArray(data.correct_answers)) {
                window.correctAnswers = data.correct_answers;
            }
            renderSubmissions(data.submissions || []);
            updateMeta(data.count, data.average_percentage);
        })
        .catch((err) => console.error(err));
}

window.loadSubmissions = loadSubmissions;

document.addEventListener('DOMContentLoaded', () => {
    const testId = window.testId || document.body.dataset.testId;
    if (!testId) return;

    window.submissionUploader = new SubmissionUploader(testId);

    const refreshBtn = document.getElementById('refresh-submissions');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadSubmissions);
    }

    if (Array.isArray(window.initialSubmissions)) {
        renderSubmissions(window.initialSubmissions);
        const avg =
            window.initialSubmissions.length > 0
                ? Math.round(
                      (window.initialSubmissions.reduce(
                          (total, sub) => total + Number(sub.percentage || 0),
                          0,
                      ) /
                          window.initialSubmissions.length) *
                          100,
                  ) / 100
                : 0;
        updateMeta(window.initialSubmissions.length, avg);
    } else {
        loadSubmissions();
    }
});

function bindImageViews() {
    // Image handling is now part of the combined stats modal.
}

function bindStatsViews() {
    const modal = document.getElementById('submission-modal');
    const body = document.getElementById('submission-modal-body');
    const closeBtn = document.getElementById('submission-modal-close');
    if (!modal || !body) return;

    const letters = ['A', 'B', 'C', 'D', 'E'];

    const open = (sub) => {
        const correctAnswers = window.correctAnswers || sub.correct_answers || [];
        const answersList = (sub.answers || [])
            .map((ans, idx) => {
                const detected = ans === null || ans === undefined || ans < 0 ? '-' : letters[ans] || ans;
                const correctVal =
                    idx < correctAnswers.length && correctAnswers[idx] !== null && correctAnswers[idx] !== undefined
                        ? letters[correctAnswers[idx]] || correctAnswers[idx]
                        : '-';
                const isCorrect = detected === correctVal;
                const cls = isCorrect ? 'correct' : 'incorrect';
                return `<li class="${cls}"><span class="q-label">Q${idx + 1}</span><span class="detected">${detected}</span><span class="divider">/</span><span class="correct">${correctVal}</span><span class="mark">${isCorrect ? '✓' : '✗'}</span></li>`;
            })
            .join('');

        const first = escapeHtml(sub.first_name || '');
        const last = escapeHtml(sub.last_name || '');

        body.innerHTML = `
            <h3>${escapeHtml(sub.student_name || 'Submission #' + sub.id)}</h3>
            <div class="submission-preview">
                <div class="preview-image">
                    ${
                        sub.image_url
                            ? `<img src="${sub.image_url}" alt="Submission image">`
                            : '<div class="empty-state">No image available.</div>'
                    }
                </div>
                <div class="preview-meta">
                    <div class="stat-line">Score: ${sub.score}/${sub.total}</div>
                    <div class="stat-line">Percentage: ${sub.percentage}%</div>
                    <div class="stat-line">Submitted: ${sub.submitted_at}</div>
                    <div class="stat-line name-edit-inline">
                        <input type="text" id="modal-first-name" value="${first}" placeholder="First name">
                        <input type="text" id="modal-last-name" value="${last}" placeholder="Last name">
                        <button class="btn btn-primary" id="modal-save-name" data-id="${sub.id}">Save</button>
                    </div>
                    <div class="answers-block">
                        <div class="answers-title">OMR Answers</div>
                        <ul class="answers-list">${answersList || '<li class="muted">No answers detected</li>'}</ul>
                    </div>
                </div>
            </div>
        `;

        modal.classList.add('open');
    };

    const close = () => {
        modal.classList.remove('open');
        body.innerHTML = '';
    };

    const attachSave = () => {
        const saveBtn = document.getElementById('modal-save-name');
        if (!saveBtn) return;
        saveBtn.onclick = () => {
            const subId = saveBtn.dataset.id;
            const first = document.getElementById('modal-first-name')?.value || '';
            const last = document.getElementById('modal-last-name')?.value || '';
            if (!first.trim() || !last.trim()) {
                alert('First and last name are required');
                return;
            }
            saveBtn.disabled = true;
            fetch(`/tests/${window.testId}/submissions/${subId}/update-name/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ first_name: first, last_name: last }),
            })
                .then((res) => res.json().then((data) => ({ ok: res.ok, data })))
                .then(({ ok, data }) => {
                    saveBtn.disabled = false;
                    if (!ok || data.error) {
                        alert(data.error || 'Failed to update name');
                        return;
                    }
                    // refresh list to reflect new name
                    loadSubmissions();
                    const title = body.querySelector('h3');
                    if (title) title.textContent = data.full_name || `Submission #${subId}`;
                })
                .catch((err) => {
                    saveBtn.disabled = false;
                    console.error(err);
                    alert('Failed to update name');
                });
        };
    };

    document.querySelectorAll('.view-stats-btn').forEach((btn) => {
        btn.onclick = () => {
            const id = Number(btn.dataset.id);
            const sub = currentSubmissions.find((s) => Number(s.id) === id);
            if (sub) {
                open(sub);
                attachSave();
            }
        };
    });

    if (closeBtn) closeBtn.onclick = close;
    modal.addEventListener('click', (e) => {
        if (e.target === modal) close();
    });
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') close();
    });
}
