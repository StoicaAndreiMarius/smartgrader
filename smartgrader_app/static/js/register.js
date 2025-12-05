document.getElementById("registerForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const confirmPassword = document.getElementById("confirm_password").value;

    if (password !== confirmPassword) {
        document.getElementById("error").innerText = "Parolele nu coincid!";
        return;
    }

    try {
        const res = await fetch("/accounts/api-register/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ email, password })
        });

        const data = await res.json();

        if (!res.ok) {
            document.getElementById("error").innerText = data.error || "Register failed";
            return;
        }

        window.location.href = "/";

    } catch (error) {
        document.getElementById("error").innerText = "Server error!";
    }
});
