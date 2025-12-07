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
            <a href="/tests/${item.id}/" class="test-card-link">
                <div class="test-card">
                    <h3>${escapeHtml(item.title)}</h3>
                    ${descriptionHtml}
                    <div class="stats-box">
                        ${statsHtml}
                    </div>
                    <div class="test-meta">
                        <span class="test-meta-item">${item.num_questions} questions</span>
                        <span class="test-meta-item">${escapeHtml(item.created_at)}</span>
                    </div>
                </div>
            </a>
        `;
    }).join('');
}

function filterAndSortTests() {
    const searchTerm = document.getElementById('search-tests').value.toLowerCase();
    const sortOption = document.getElementById('sort-tests').value;

    // Filter
    let filtered = window.allTests.filter(test =>
        test.title.toLowerCase().includes(searchTerm) ||
        (test.description && test.description.toLowerCase().includes(searchTerm))
    );

    // Sort
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

// Add event listeners
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('search-tests');
    const sortSelect = document.getElementById('sort-tests');
    const dataScript = document.getElementById('tests-data');

    // Load initial data from embedded JSON
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

    // Initial render
    if (window.allTests) {
        displayTests(window.allTests);
    }
});
