let questionCount = 0;

document.addEventListener('DOMContentLoaded', function() {
    const addQuestionBtn = document.getElementById('add-question-btn');
    const questionsContainer = document.getElementById('questions-container');
    const testForm = document.getElementById('test-form');
    const cancelBtn = document.getElementById('cancel-btn');
    const saveBtn = document.getElementById('save-btn');
    const saveAndGenerateBtn = document.getElementById('save-and-generate-btn');
    const numOptionsSelect = document.getElementById('num-options');
    const fileUpload = document.getElementById('file-upload');
    const enableRandomization = document.getElementById('enable-randomization');
    const randomizationSettings = document.getElementById('randomization-settings');
    const modal = document.getElementById('test-generator-modal');
    const openers = document.querySelectorAll('[data-open="test-generator"]');
    const closeButtons = modal ? modal.querySelectorAll('[data-close="test-generator"]') : [];

    const openModal = (event) => {
        if (event) event.preventDefault();
        if (!modal) return;
        modal.hidden = false;
        modal.classList.add('is-open');
        document.body.classList.add('tg-modal-open');
    };

    const closeModal = (event) => {
        if (event) event.preventDefault();
        if (!modal) return;
        modal.classList.remove('is-open');
        modal.hidden = true;
        document.body.classList.remove('tg-modal-open');
    };

    openers.forEach((btn) => {
        btn.addEventListener('click', openModal);
    });

    closeButtons.forEach((btn) => {
        btn.addEventListener('click', closeModal);
    });

    if (modal) {
        modal.addEventListener('click', (event) => {
            if (
                event.target === modal ||
                event.target.classList.contains('tg-overlay__backdrop')
            ) {
                closeModal(event);
            }
        });
    }

    // Check if critical elements exist
    if (!questionsContainer) {
        console.error('Critical error: questions-container element not found');
        if (typeof Toast !== 'undefined') {
            Toast.error('Initialization Error', 'Failed to initialize test generator. Please refresh the page.');
        }
        return;
    }

    // Helper functions for messages using Toast notifications
    function showError(message) {
        if (typeof Toast !== 'undefined') {
            Toast.error('Error', message);
        } else {
            console.error('Error:', message);
        }
    }

    function showSuccess(message) {
        if (typeof Toast !== 'undefined') {
            Toast.success('Success', message);
        } else {
            console.log('Success:', message);
        }
    }

    // Add first question by default
    addQuestion();

    // File upload handler
    if (fileUpload) {
        fileUpload.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (!file) return;

        console.log('File selected:', file.name);

        const reader = new FileReader();
        reader.onload = function(event) {
            try {
                const content = event.target.result;
                console.log('File content loaded, length:', content.length);
                let questions;

                if (file.name.endsWith('.json')) {
                    console.log('Parsing as JSON...');
                    questions = parseJSONFile(content);
                    console.log('Parsed questions:', questions);
                } else if (file.name.endsWith('.csv')) {
                    console.log('Parsing as CSV...');
                    questions = parseCSVFile(content);
                    console.log('Parsed questions:', questions);
                } else {
                    showError('Unsupported file format. Please upload a CSV or JSON file.');
                    return;
                }

                if (questions && questions.length > 0) {
                    console.log('Importing', questions.length, 'questions');
                    // Clear existing questions
                    questionsContainer.innerHTML = '';
                    questionCount = 0;

                    // Add imported questions
                    questions.forEach((q, index) => {
                        console.log(`Adding question ${index + 1}:`, q);
                        addQuestionFromData(q);
                    });

                    showSuccess(`Successfully imported ${questions.length} questions!`);
                } else {
                    console.error('No questions parsed from file');
                    showError('No valid questions found in the file.');
                }
            } catch (error) {
                showError('Error parsing file: ' + error.message);
                console.error('Parse error:', error);
            }
        };

        reader.onerror = function(error) {
            console.error('File reading error:', error);
            showError('Error reading file. Please try again.');
        };

        reader.readAsText(file);
        // Reset file input
        e.target.value = '';
        });
    }

    // Randomization toggle
    if (enableRandomization) {
        enableRandomization.addEventListener('change', function() {
            randomizationSettings.style.display = this.checked ? 'block' : 'none';
        });
    }

    // Add question button click
    if (addQuestionBtn) {
        addQuestionBtn.addEventListener('click', function() {
            addQuestion();
        });
    }

    // Form submission
    if (testForm) {
        testForm.addEventListener('submit', function(e) {
            e.preventDefault();
            saveTest(false);
        });
    }

    // Save and generate PDF button
    if (saveAndGenerateBtn) {
        saveAndGenerateBtn.addEventListener('click', function() {
            saveTest(true);
        });
    }

    // Cancel button
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function(event) {
            if (modal && modal.classList.contains('is-open')) {
                closeModal(event);
            } else if (confirm('Are you sure you want to cancel? All unsaved changes will be lost.')) {
                window.location.href = '/';
            }
        });
    }

    // Update options when number of options changes
    if (numOptionsSelect) {
        numOptionsSelect.addEventListener('change', function() {
            updateAllQuestionOptions();
        });
    }

    function parseJSONFile(content) {
        const data = JSON.parse(content);

        // Helper function to parse correct answer (handles both string and number)
        const parseCorrectAnswer = (q) => {
            let answer = q.correct_answer !== undefined ? q.correct_answer :
                        (q.correctAnswer !== undefined ? q.correctAnswer : 0);
            // Convert string to number if needed
            return typeof answer === 'string' ? parseInt(answer) : answer;
        };

        // Support multiple JSON formats
        // Format 1: Array of question objects
        if (Array.isArray(data)) {
            return data.map(q => ({
                question: q.question || q.text || q.questionText || '',
                options: q.options || q.answers || q.choices || [],
                correct_answer: parseCorrectAnswer(q)
            }));
        }

        // Format 2: Object with questions array (including formats with num_questions, num_answers)
        if (data.questions && Array.isArray(data.questions)) {
            return data.questions.map(q => ({
                question: q.question || q.text || q.questionText || '',
                options: q.options || q.answers || q.choices || [],
                correct_answer: parseCorrectAnswer(q)
            }));
        }

        return [];
    }

    function parseCSVFile(content) {
        const lines = content.split('\n').filter(line => line.trim());
        if (lines.length < 2) return [];

        const questions = [];

        // Skip header row, process data rows
        for (let i = 1; i < lines.length; i++) {
            const line = lines[i].trim();
            if (!line) continue;

            // Parse CSV line (handle quoted values)
            const values = parseCSVLine(line);

            if (values.length >= 3) {
                // Format: question, option1, option2, option3, ..., correct_answer_index
                const question = values[0];
                const correctAnswer = parseInt(values[values.length - 1]) || 0;
                const options = values.slice(1, values.length - 1);

                questions.push({
                    question: question,
                    options: options,
                    correct_answer: correctAnswer
                });
            }
        }

        return questions;
    }

    function parseCSVLine(line) {
        const values = [];
        let current = '';
        let inQuotes = false;

        for (let i = 0; i < line.length; i++) {
            const char = line[i];

            if (char === '"') {
                inQuotes = !inQuotes;
            } else if (char === ',' && !inQuotes) {
                values.push(current.trim());
                current = '';
            } else {
                current += char;
            }
        }

        if (current) {
            values.push(current.trim());
        }

        return values;
    }

    function addQuestionFromData(questionData) {
        if (!questionsContainer) {
            console.error('Questions container not found');
            showError('Failed to add question. Please refresh the page.');
            return;
        }

        // Validate question data
        if (!questionData || !questionData.question || !questionData.options || questionData.options.length === 0) {
            console.error('Invalid question data:', questionData);
            return;
        }

        questionCount++;
        const numOptions = Math.max(questionData.options.length, parseInt(numOptionsSelect.value));

        const questionCard = document.createElement('div');
        questionCard.className = 'question-card';
        questionCard.dataset.questionId = questionCount;

        const optionLabels = ['A', 'B', 'C', 'D', 'E'];
        let optionsHTML = '';

        // Escape HTML in option values
        const escapeHtml = (text) => {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        };

        for (let i = 0; i < numOptions; i++) {
            const optionValue = escapeHtml(questionData.options[i] || '');
            optionsHTML += `
                <div class="option-group">
                    <label>Option ${optionLabels[i]}:</label>
                    <input type="text"
                           name="question_${questionCount}_option_${i}"
                           placeholder="Enter option ${optionLabels[i]}"
                           value="${optionValue}"
                           required>
                    <div class="correct-answer-label">
                        <input type="radio"
                               name="question_${questionCount}_correct"
                               value="${i}"
                               ${i === questionData.correct_answer ? 'checked' : ''}>
                        <span>Correct</span>
                    </div>
                </div>
            `;
        }

        const questionText = escapeHtml(questionData.question);

        questionCard.innerHTML = `
            <div class="question-header">
                <span class="question-number">Question ${questionCount}</span>
                <button type="button" class="remove-question-btn" onclick="removeQuestion(${questionCount})">
                    Remove
                </button>
            </div>
            <div class="form-group">
                <label>Question Text *</label>
                <textarea name="question_${questionCount}_text"
                          placeholder="Enter your question here"
                          required>${questionText}</textarea>
            </div>
            <div class="options-container">
                <label style="margin-bottom: 10px; display: block; color: #ddd;">Options & Correct Answer *</label>
                ${optionsHTML}
            </div>
        `;

        questionsContainer.appendChild(questionCard);
    }

    function addQuestion() {
        if (!questionsContainer) {
            console.error('Questions container not found');
            showError('Failed to add question. Please refresh the page.');
            return;
        }

        questionCount++;
        const numOptions = parseInt(numOptionsSelect.value);

        const questionCard = document.createElement('div');
        questionCard.className = 'question-card';
        questionCard.dataset.questionId = questionCount;

        let optionsHTML = '';
        const optionLabels = ['A', 'B', 'C', 'D', 'E'];

        for (let i = 0; i < numOptions; i++) {
            optionsHTML += `
                <div class="option-group">
                    <label>Option ${optionLabels[i]}:</label>
                    <input type="text"
                           name="question_${questionCount}_option_${i}"
                           placeholder="Enter option ${optionLabels[i]}"
                           required>
                    <div class="correct-answer-label">
                        <input type="radio"
                               name="question_${questionCount}_correct"
                               value="${i}"
                               ${i === 0 ? 'checked' : ''}>
                        <span>Correct</span>
                    </div>
                </div>
            `;
        }

        questionCard.innerHTML = `
            <div class="question-header">
                <span class="question-number">Question ${questionCount}</span>
                <button type="button" class="remove-question-btn" onclick="removeQuestion(${questionCount})">
                    Remove
                </button>
            </div>
            <div class="form-group">
                <label>Question Text *</label>
                <textarea name="question_${questionCount}_text"
                          placeholder="Enter your question here"
                          required></textarea>
            </div>
            <div class="options-container">
                <label style="margin-bottom: 10px; display: block; color: #ddd;">Options & Correct Answer *</label>
                ${optionsHTML}
            </div>
        `;

        questionsContainer.appendChild(questionCard);
    }

    function updateAllQuestionOptions() {
        const cards = questionsContainer.querySelectorAll('.question-card');
        cards.forEach(card => {
            const questionId = card.dataset.questionId;
            updateQuestionOptions(card, questionId);
        });
    }

    function updateQuestionOptions(card, questionId) {
        const numOptions = parseInt(numOptionsSelect.value);
        const optionsContainer = card.querySelector('.options-container');
        const optionLabels = ['A', 'B', 'C', 'D', 'E'];

        // Get current values
        const currentValues = [];
        const currentCorrect = card.querySelector(`input[name="question_${questionId}_correct"]:checked`)?.value || '0';

        for (let i = 0; i < 5; i++) {
            const input = card.querySelector(`input[name="question_${questionId}_option_${i}"]`);
            currentValues[i] = input ? input.value : '';
        }

        // Rebuild options
        let optionsHTML = '<label style="margin-bottom: 10px; display: block; color: #ddd;">Options & Correct Answer *</label>';

        for (let i = 0; i < numOptions; i++) {
            optionsHTML += `
                <div class="option-group">
                    <label>Option ${optionLabels[i]}:</label>
                    <input type="text"
                           name="question_${questionId}_option_${i}"
                           placeholder="Enter option ${optionLabels[i]}"
                           value="${currentValues[i] || ''}"
                           required>
                    <div class="correct-answer-label">
                        <input type="radio"
                               name="question_${questionId}_correct"
                               value="${i}"
                               ${i === parseInt(currentCorrect) ? 'checked' : ''}>
                        <span>Correct</span>
                    </div>
                </div>
            `;
        }

        optionsContainer.innerHTML = optionsHTML;
    }

    function saveTest(generatePDF) {
        // Clear previous messages
        document.getElementById('error-message').style.display = 'none';
        document.getElementById('success-message').style.display = 'none';

        // Collect form data
        const title = document.getElementById('test-title').value.trim();
        const description = document.getElementById('test-description').value.trim();
        const numOptions = parseInt(numOptionsSelect.value);

        if (!title) {
            showError('Please enter a test title');
            return;
        }

        // Collect questions
        const questions = [];
        const questionCards = questionsContainer.querySelectorAll('.question-card');

        if (questionCards.length === 0) {
            showError('Please add at least one question');
            return;
        }

        questionCards.forEach((card, index) => {
            const questionId = card.dataset.questionId;
            const questionText = card.querySelector(`textarea[name="question_${questionId}_text"]`).value.trim();

            if (!questionText) {
                showError(`Please enter text for question ${index + 1}`);
                return;
            }

            const options = [];
            let correctAnswer = 0;

            for (let i = 0; i < numOptions; i++) {
                const optionInput = card.querySelector(`input[name="question_${questionId}_option_${i}"]`);
                const optionValue = optionInput ? optionInput.value.trim() : '';

                if (!optionValue) {
                    showError(`Please enter all options for question ${index + 1}`);
                    return;
                }

                options.push(optionValue);
            }

            const correctRadio = card.querySelector(`input[name="question_${questionId}_correct"]:checked`);
            if (correctRadio) {
                correctAnswer = parseInt(correctRadio.value);
            }

            questions.push({
                question: questionText,
                options: options,
                correct_answer: correctAnswer
            });
        });

        if (questions.length === 0) {
            showError('Please add at least one valid question');
            return;
        }

        // Check for randomization
        const enableRandom = document.getElementById('enable-randomization').checked;
        let numVariants = 1;
        let questionsPerVariant = questions.length;

        if (enableRandom) {
            numVariants = parseInt(document.getElementById('num-variants').value) || 1;
            if (numVariants < 1) numVariants = 1;
            questionsPerVariant = parseInt(document.getElementById('questions-per-variant').value);

            if (!questionsPerVariant || questionsPerVariant <= 0) {
                showError('Please specify the number of questions per variant');
                return;
            }

            if (questionsPerVariant > questions.length) {
                showError(`Cannot create variants with ${questionsPerVariant} questions when you only have ${questions.length} questions in the pool`);
                return;
            }
        }

        // Prepare payload
        const payload = {
            title: title,
            description: description,
            num_options: numOptions,
            questions: questions,
            generate_pdf: generatePDF,
            enable_randomization: enableRandom,
            num_variants: numVariants,
            questions_per_variant: questionsPerVariant
        };

        // Send to API
        fetch('/accounts/api-create-test/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin',
            body: JSON.stringify(payload)
        })
        .then(async response => {
            let data = {};
            try {
                data = await response.json();
            } catch (err) {
                // ignore parse errors
            }

            if (!response.ok || data.error) {
                const message = data.error || `Failed to save test (status ${response.status})`;
                showError(message);
                return;
            }

            showSuccess(data.message || 'Test created successfully!');

            if (data.pdf_urls && data.pdf_urls.length > 0) {
                setTimeout(() => {
                    data.pdf_urls.forEach(url => window.open(url, '_blank'));
                    window.location.href = '/tests/';
                }, 2000);
            } else if (data.pdf_url) {
                setTimeout(() => {
                    window.open(data.pdf_url, '_blank');
                    window.location.href = '/tests/';
                }, 1500);
            } else {
                setTimeout(() => {
                    window.location.href = '/tests/';
                }, 1500);
            }
        })
        .catch(error => {
            showError('An error occurred while saving the test. Please try again.');
            console.error('Error:', error);
        });
    }

    // Make saveTest available globally for the submit button
    window.saveTest = saveTest;

    // ============================================
    // AI QUESTION GENERATION
    // ============================================

    const aiGenerateBtn = document.getElementById('ai-generate-btn');
    const aiModal = document.getElementById('ai-modal');
    const aiModalClose = document.getElementById('ai-modal-close');
    const aiCancel = document.getElementById('ai-cancel');
    const aiGenerate = document.getElementById('ai-generate');
    const aiError = document.getElementById('ai-error');
    const aiLoading = document.getElementById('ai-loading');

    // Check if AI button exists
    if (aiGenerateBtn) {
        // Disable AI generate feature for now
        aiGenerateBtn.disabled = true;
        aiGenerateBtn.classList.add('is-disabled');
        aiGenerateBtn.setAttribute('title', 'AI generation is currently disabled');
    }
});

// Global function to remove question
function removeQuestion(questionId) {
    const card = document.querySelector(`[data-question-id="${questionId}"]`);
    if (card) {
        if (confirm('Are you sure you want to remove this question?')) {
            card.remove();
            updateQuestionNumbers();
        }
    }
}

function updateQuestionNumbers() {
    const cards = document.querySelectorAll('.question-card');
    cards.forEach((card, index) => {
        const numberSpan = card.querySelector('.question-number');
        if (numberSpan) {
            numberSpan.textContent = `Question ${index + 1}`;
        }
    });
}
