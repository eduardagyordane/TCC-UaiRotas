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

const appPage = document.querySelector(".app-page");
const themeToggle = document.querySelector("[data-theme-toggle]");

if (appPage && themeToggle) {
  const savedTheme = localStorage.getItem("uairotas-theme");
  const systemPrefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const initialTheme = savedTheme || (systemPrefersDark ? "dark" : "light");

  const applyTheme = (theme) => {
    const isDark = theme === "dark";
    appPage.dataset.theme = theme;
    themeToggle.setAttribute("aria-pressed", String(isDark));
    themeToggle.setAttribute("aria-label", isDark ? "Ativar modo claro" : "Ativar modo escuro");
  };

  applyTheme(initialTheme);

  themeToggle.addEventListener("click", () => {
    const nextTheme = appPage.dataset.theme === "dark" ? "light" : "dark";
    localStorage.setItem("uairotas-theme", nextTheme);
    applyTheme(nextTheme);
  });
}

const navToggle = document.querySelector("[data-nav-toggle]");
const mainNav = document.querySelector("[data-main-nav]");

if (navToggle && mainNav) {
  navToggle.addEventListener("click", () => {
    const isOpen = mainNav.classList.toggle("is-open");
    navToggle.setAttribute("aria-expanded", String(isOpen));
    navToggle.setAttribute("aria-label", isOpen ? "Fechar menu" : "Abrir menu");
  });

  mainNav.addEventListener("click", () => {
    mainNav.classList.remove("is-open");
    navToggle.setAttribute("aria-expanded", "false");
    navToggle.setAttribute("aria-label", "Abrir menu");
  });
}
