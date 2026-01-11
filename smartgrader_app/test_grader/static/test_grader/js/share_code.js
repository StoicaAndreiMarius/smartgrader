// Share Code Management for Teachers

class ShareCodeManager {
    constructor(testId) {
        this.testId = testId;
        this.init();
    }

    init() {
        // Load share code info on page load
        this.loadShareInfo();

        // Bind event listeners
        const generateBtn = document.getElementById('generateShareCodeBtn');
        const regenerateBtn = document.getElementById('regenerateShareCodeBtn');
        const copyLinkBtn = document.getElementById('copyShareLinkBtn');
        const copyCodeBtn = document.getElementById('copyShareCodeBtn');
        const toggleSwitch = document.getElementById('submissionsToggle');

        if (generateBtn) {
            generateBtn.addEventListener('click', () => this.generateShareCode());
        }

        if (regenerateBtn) {
            regenerateBtn.addEventListener('click', () => this.regenerateShareCode());
        }

        if (copyLinkBtn) {
            copyLinkBtn.addEventListener('click', () => this.copyShareLink());
        }

        if (copyCodeBtn) {
            copyCodeBtn.addEventListener('click', () => this.copyShareCode());
        }

        if (toggleSwitch) {
            toggleSwitch.addEventListener('change', (e) => this.toggleSubmissions(e.target.checked));
        }
    }

    async loadShareInfo() {
        try {
            const response = await fetch(`/tests/${this.testId}/share-info/`);
            const data = await response.json();

            if (data.share_code) {
                this.displayShareCode(data);
            } else {
                this.showGenerateButton();
            }
        } catch (error) {
            console.error('Error loading share info:', error);
        }
    }

    async generateShareCode() {
        try {
            const response = await fetch(`/tests/${this.testId}/generate-share-code/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCsrfToken()
                }
            });

            const data = await response.json();

            if (data.success) {
                this.displayShareCode(data);
                this.showNotification('Share code generated successfully!', 'success');
            } else {
                this.showNotification('Failed to generate share code', 'error');
            }
        } catch (error) {
            console.error('Error generating share code:', error);
            this.showNotification('An error occurred', 'error');
        }
    }

    async regenerateShareCode() {
        if (!confirm('Are you sure you want to generate a new share code? The old link will no longer work.')) {
            return;
        }

        await this.generateShareCode();
    }

    async toggleSubmissions(isOpen) {
        try {
            const response = await fetch(`/tests/${this.testId}/toggle-submissions/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({ is_open: isOpen })
            });

            const data = await response.json();

            if (data.success) {
                this.showNotification(
                    isOpen ? 'Submissions opened' : 'Submissions closed',
                    'success'
                );
            } else {
                this.showNotification('Failed to update submission status', 'error');
            }
        } catch (error) {
            console.error('Error toggling submissions:', error);
            this.showNotification('An error occurred', 'error');
        }
    }

    copyToClipboard(text, buttonId, successMessage) {
        // Try modern clipboard API first
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text).then(() => {
                this.showCopySuccess(buttonId, successMessage);
            }).catch(err => {
                // Fallback to older method
                this.copyToClipboardFallback(text, buttonId, successMessage);
            });
        } else {
            // Use fallback method
            this.copyToClipboardFallback(text, buttonId, successMessage);
        }
    }

    copyToClipboardFallback(text, buttonId, successMessage) {
        // Create temporary textarea
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();

        try {
            document.execCommand('copy');
            this.showCopySuccess(buttonId, successMessage);
        } catch (err) {
            console.error('Failed to copy:', err);
            this.showNotification('Failed to copy. Please copy manually.', 'error');
        } finally {
            document.body.removeChild(textarea);
        }
    }

    showCopySuccess(buttonId, message) {
        this.showNotification(message, 'success');

        const copyBtn = document.getElementById(buttonId);
        if (copyBtn) {
            const originalHTML = copyBtn.innerHTML;
            const originalBg = copyBtn.style.background;

            copyBtn.innerHTML = '<i class="bx bx-check"></i> Copied!';
            copyBtn.style.background = '#4CAF50';
            copyBtn.disabled = true;

            setTimeout(() => {
                copyBtn.innerHTML = originalHTML;
                copyBtn.style.background = originalBg;
                copyBtn.disabled = false;
            }, 2000);
        }
    }

    copyShareLink() {
        const shareLink = document.getElementById('shareLink');
        if (shareLink) {
            const link = shareLink.textContent.trim();
            this.copyToClipboard(link, 'copyShareLinkBtn', 'Link copied to clipboard!');
        }
    }

    copyShareCode() {
        const codeElement = document.getElementById('shareCodeText');
        if (codeElement) {
            const code = codeElement.textContent.trim();
            this.copyToClipboard(code, 'copyShareCodeBtn', 'Code copied to clipboard!');
        }
    }

    displayShareCode(data) {
        const container = document.getElementById('shareCodeContainer');
        if (!container) return;

        container.innerHTML = `
            <div class="share-code-display">
                <div class="share-code-header">
                    <h3>Share Code</h3>
                    <button id="regenerateShareCodeBtn" class="btn-regenerate">
                        <i class='bx bx-refresh'></i> Regenerate
                    </button>
                </div>

                <div class="share-code-box">
                    <div class="code-formatted" id="shareCodeText">${data.formatted_code || data.share_code}</div>
                    <button id="copyShareCodeBtn" class="btn-copy-code">
                        <i class='bx bx-copy'></i> Copy Code
                    </button>
                </div>

                <div class="share-link-box">
                    <label>Share Link:</label>
                    <div class="link-container">
                        <span id="shareLink">${data.share_url}</span>
                        <button id="copyShareLinkBtn" class="btn-copy">
                            <i class='bx bx-copy'></i> Copy Link
                        </button>
                    </div>
                </div>

                <div class="submission-toggle">
                    <label class="toggle-label">
                        <span>Submissions Open</span>
                        <input type="checkbox" id="submissionsToggle" ${data.is_open ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                </div>
            </div>
        `;

        // Re-bind event listeners
        this.init();
    }

    showGenerateButton() {
        const container = document.getElementById('shareCodeContainer');
        if (!container) return;

        container.innerHTML = `
            <div class="share-code-generate">
                <p>Generate a share code to allow students to access this test.</p>
                <button id="generateShareCodeBtn" class="btn-primary">
                    <i class='bx bx-share-alt'></i> Generate Share Code
                </button>
            </div>
        `;

        // Re-bind event listeners
        this.init();
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;

        // Add to page
        document.body.appendChild(notification);

        // Show notification
        setTimeout(() => notification.classList.add('show'), 10);

        // Remove after 3 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    getCsrfToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const testId = document.getElementById('shareCodeContainer')?.dataset.testId;
    if (testId) {
        new ShareCodeManager(testId);
    }
});
