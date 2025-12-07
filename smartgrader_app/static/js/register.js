document.getElementById('registerForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const submitBtn = document.querySelector('#registerForm .submit-button');
    const errorDiv = document.getElementById('error');

    let successDiv = document.getElementById('success-message');
    if (!successDiv) {
        successDiv = document.createElement('p');
        successDiv.id = 'success-message';
        successDiv.className = 'success-message';
        successDiv.style.display = 'none';
        errorDiv.insertAdjacentElement('beforebegin', successDiv);
    }

    errorDiv.style.display = 'none';
    successDiv.style.display = 'none';

    const firstName = document.getElementById('first-name').value.trim();
    const lastName = document.getElementById('last-name').value.trim();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirm_password').value;
    const role = document.getElementById('role').value;

    if (!firstName || !lastName) {
        errorDiv.textContent = 'Please enter your first and last name';
        errorDiv.style.display = 'block';
        return;
    }

    if (password !== confirmPassword) {
        errorDiv.textContent = 'Passwords do not match';
        errorDiv.style.display = 'block';
        return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = 'Creating Account...';

    try {
        const response = await fetch('/accounts/api-register/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email,
                password,
                role,
                first_name: firstName,
                last_name: lastName
            })
        });

        const data = await response.json();

        if (response.ok) {
            successDiv.textContent = 'Account created successfully! Redirecting...';
            successDiv.style.display = 'block';
            setTimeout(() => {
                if (role === 'teacher') {
                    window.location.href = '/tests/';
                } else {
                    window.location.href = '/';
                }
            }, 1000);
        } else {
            errorDiv.textContent = data.error || 'Registration failed';
            errorDiv.style.display = 'block';
            submitBtn.disabled = false;
            submitBtn.textContent = 'Create Account';
        }
    } catch (error) {
        errorDiv.textContent = 'An error occurred. Please try again.';
        errorDiv.style.display = 'block';
        submitBtn.disabled = false;
        submitBtn.textContent = 'Create Account';
    }
});
