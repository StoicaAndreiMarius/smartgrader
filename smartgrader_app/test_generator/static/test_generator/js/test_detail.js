document.addEventListener('DOMContentLoaded', () => {
    const pdfBtn = document.getElementById('generate-pdf-btn');
    if (!pdfBtn) return;

    pdfBtn.addEventListener('click', () => {
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
    });
});
