function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function displayTests(tests) {
    const grid = document.getElementById('test-grid');
    if (!grid) return;

    if (tests.length === 0) {
        grid.innerHTML = '<p style="color: #aaa; text-align: center; padding: 40px;">No tests match your search.</p>';
        return;
    }

    grid.innerHTML = tests.map(item => {
        let descriptionHtml = '';
        if (item.description) {
            const truncated = item.description.length > 100 ? item.description.substring(0, 100) + '...' : item.description;
            descriptionHtml = '<p>' + escapeHtml(truncated) + '</p>';
        }

        let statsHtml = '';
        if (item.submission_count > 0) {
            let latestHtml = '';
            if (item.latest_submission) {
                latestHtml = '<div class="stat-secondary">Latest: ' + escapeHtml(item.latest_submission) + ' (' + item.latest_percentage + '%)</div>';
            }
            statsHtml = `
                <div class="stats-row">
                    <span class="stat-label">Submissions</span>
                    <span class="stat-value">${item.submission_count}</span>
                </div>
                <div class="stats-row">
                    <span class="stat-label">Class Average</span>
                    <span class="stat-value">${item.average_percentage}%</span>
                </div>
                ${latestHtml}
            `;
        } else {
            statsHtml = '<div class="no-stats">No submissions yet</div>';
        }

        return `
            <div class="test-card">
                <div class="test-card-header">
                    <h3><a href="/tests/${item.id}/" class="test-card-link">${escapeHtml(item.title)}</a></h3>
                    <div class="test-card-actions">
                        <button class="btn btn-tertiary pdf-btn" data-id="${item.id}">Generate PDF</button>
                        <button class="btn btn-danger delete-test-btn" data-id="${item.id}">Delete</button>
                    </div>
                </div>
                ${descriptionHtml}
                <div class="stats-box">
                    ${statsHtml}
                </div>
                <div class="test-meta">
                    <span class="test-meta-item">${item.num_questions} questions</span>
                    <span class="test-meta-item">${escapeHtml(item.created_at)}</span>
                </div>
            </div>
        `;
    }).join('');
}

function filterAndSortTests() {
    const searchTerm = document.getElementById('search-tests').value.toLowerCase();
    const sortOption = document.getElementById('sort-tests').value;

    let filtered = window.allTests.filter(test =>
        test.title.toLowerCase().includes(searchTerm) ||
        (test.description && test.description.toLowerCase().includes(searchTerm))
    );

    filtered.sort((a, b) => {
        switch(sortOption) {
            case 'date-desc':
                return b.created_timestamp - a.created_timestamp;
            case 'date-asc':
                return a.created_timestamp - b.created_timestamp;
            case 'name-asc':
                return a.title.localeCompare(b.title);
            case 'name-desc':
                return b.title.localeCompare(a.title);
            case 'submissions-desc':
                return b.submission_count - a.submission_count;
            case 'average-desc':
                return b.average_percentage - a.average_percentage;
            default:
                return 0;
        }
    });

    displayTests(filtered);
}

document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('search-tests');
    const sortSelect = document.getElementById('sort-tests');
    const dataScript = document.getElementById('tests-data');

    if (dataScript && dataScript.textContent) {
        try {
            window.allTests = JSON.parse(dataScript.textContent);
        } catch (err) {
            console.error('Failed to parse tests data:', err);
            window.allTests = [];
        }
    } else {
        window.allTests = window.allTests || [];
    }

    if (searchInput) {
        searchInput.addEventListener('input', filterAndSortTests);
    }

    if (sortSelect) {
        sortSelect.addEventListener('change', filterAndSortTests);
    }

    if (window.allTests) {
        displayTests(window.allTests);
    }

    gridClickHandler();
});

function gridClickHandler() {
    const grid = document.getElementById('test-grid');
    if (!grid) return;

    grid.addEventListener('click', function (e) {
        const deleteBtn = e.target.closest('.delete-test-btn');
        const pdfBtn = e.target.closest('.pdf-btn');

        if (pdfBtn) {
            e.preventDefault();
            e.stopPropagation();
            const testId = pdfBtn.dataset.id;
            if (!testId) return;

            const originalText = pdfBtn.textContent;
            pdfBtn.disabled = true;
            pdfBtn.textContent = 'Generating...';

            fetch(`/tests/${testId}/pdf/`, {
                method: 'GET',
                credentials: 'same-origin',
                headers: { 'Content-Type': 'application/json' },
            })
                .then((res) => res.json().then((data) => ({ ok: res.ok, data })))
                .then(({ ok, data }) => {
                    pdfBtn.disabled = false;
                    pdfBtn.textContent = originalText;
                    if (!ok || data.error || !data.pdf_url) {
                        alert(data && data.error ? data.error : 'Failed to generate PDF.');
                        return;
                    }
                    window.open(data.pdf_url, '_blank');
                })
                .catch((err) => {
                    pdfBtn.disabled = false;
                    pdfBtn.textContent = originalText;
                    console.error(err);
                    alert('Failed to generate PDF.');
                });
            return;
        }

        if (!deleteBtn) return;
        e.preventDefault();
        e.stopPropagation();

        const testId = deleteBtn.dataset.id;
        if (!testId) return;

        if (!confirm('Delete this test?')) return;

        fetch(`/tests/${testId}/delete/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
        })
            .then((res) => res.json().then((data) => ({ ok: res.ok, data })))
            .then(({ ok, data }) => {
                if (!ok || data.error) {
                    alert(data.error || 'Failed to delete test.');
                    return;
                }
                window.allTests = (window.allTests || []).filter((t) => String(t.id) !== String(testId));
                filterAndSortTests();
            })
            .catch((err) => {
                console.error(err);
                alert('Failed to delete test.');
            });
    });
}
