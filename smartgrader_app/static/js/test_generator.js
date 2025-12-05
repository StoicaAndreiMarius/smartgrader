let questionCount = 0;

document.addEventListener('DOMContentLoaded', function() {
    const addQuestionBtn = document.getElementById('add-question-btn');
    const questionsContainer = document.getElementById('questions-container');
    const testForm = document.getElementById('test-form');
    const cancelBtn = document.getElementById('cancel-btn');
    const saveBtn = document.getElementById('save-btn');
    const saveAndGenerateBtn = document.getElementById('save-and-generate-btn');
    const numOptionsSelect = document.getElementById('num-options');

    // Add first question by default
    addQuestion();

    // Add question button click
    addQuestionBtn.addEventListener('click', function() {
        addQuestion();
    });

    // Form submission
    testForm.addEventListener('submit', function(e) {
        e.preventDefault();
        saveTest(false);
    });

    // Save and generate PDF button
    saveAndGenerateBtn.addEventListener('click', function() {
        saveTest(true);
    });

    // Cancel button
    cancelBtn.addEventListener('click', function() {
        if (confirm('Are you sure you want to cancel? All unsaved changes will be lost.')) {
            window.location.href = '/';
        }
    });

    // Update options when number of options changes
    numOptionsSelect.addEventListener('change', function() {
        updateAllQuestionOptions();
    });

    function addQuestion() {
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
                <label style="margin-bottom: 10px; display: block;">Options & Correct Answer *</label>
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
        let optionsHTML = '<label style="margin-bottom: 10px; display: block;">Options & Correct Answer *</label>';

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

        // Prepare payload
        const payload = {
            title: title,
            description: description,
            num_options: numOptions,
            questions: questions,
            generate_pdf: generatePDF
        };

        // Send to API
        fetch('/accounts/api-create-test/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showError(data.error);
            } else {
                showSuccess(data.message || 'Test created successfully!');

                if (data.pdf_url) {
                    setTimeout(() => {
                        window.open(data.pdf_url, '_blank');
                        window.location.href = '/';
                    }, 1500);
                } else {
                    setTimeout(() => {
                        window.location.href = '/';
                    }, 1500);
                }
            }
        })
        .catch(error => {
            showError('An error occurred while saving the test. Please try again.');
            console.error('Error:', error);
        });
    }

    function showError(message) {
        const errorDiv = document.getElementById('error-message');
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        errorDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    function showSuccess(message) {
        const successDiv = document.getElementById('success-message');
        successDiv.textContent = message;
        successDiv.style.display = 'block';
        successDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    // Make saveTest available globally for the submit button
    window.saveTest = saveTest;
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
