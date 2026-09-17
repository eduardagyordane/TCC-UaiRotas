const passwordToggle = document.querySelector("[data-password-toggle]");

if (passwordToggle) {
  passwordToggle.addEventListener("click", () => {
    const passwordInput = document.querySelector("#password");
    const shouldShow = passwordInput.type === "password";

    passwordInput.type = shouldShow ? "text" : "password";
    passwordToggle.setAttribute("aria-pressed", String(shouldShow));
    passwordToggle.setAttribute("aria-label", shouldShow ? "Ocultar senha" : "Mostrar senha");
  });
}

