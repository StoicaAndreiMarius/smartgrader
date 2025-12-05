document.getElementById("loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

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
            document.getElementById("error").innerText = data.error || "Login failed";
            return;
        }

        window.location.href = "/"; 

    } catch (error) {
        document.getElementById("error").innerText = "Server error!";
    }
});
