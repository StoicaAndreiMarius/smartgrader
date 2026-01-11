document.getElementById("loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const emailInput = document.getElementById("email");
    const passwordInput = document.getElementById("password");
    const errorEl = document.getElementById("error");
    const submitBtn = document.querySelector("#loginForm .submit-button");

    const email = emailInput.value.trim();
    const password = passwordInput.value;

    errorEl.textContent = "";

    if (!email || !password) {
        errorEl.textContent = "Please enter email and password";
        return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = "Logging in...";

    try {
        const res = await fetch("/accounts/api-login/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ email, password })
        });

        const data = await res.json();

        if (!res.ok) {
            errorEl.textContent = data.error || "Login failed";
            submitBtn.disabled = false;
            submitBtn.textContent = "Login";
            return;
        }

        // Redirect based on user role
        if (data.role === 'teacher') {
            window.location.href = "/tests/";
        } else if (data.role === 'student') {
            window.location.href = "/student/dashboard/";
        } else {
            window.location.href = "/";
        }
    } catch (error) {
        errorEl.textContent = "Server error!";
        submitBtn.disabled = false;
        submitBtn.textContent = "Login";
    }
});
