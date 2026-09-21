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

const interactiveMap = document.querySelector("[data-interactive-map]");

if (interactiveMap) {
  const mapStage = interactiveMap.querySelector("[data-map-stage]");
  const mapControls = interactiveMap.querySelectorAll("[data-map-action]");
  const routeButtons = document.querySelectorAll("[data-focus-route]");
  const mapState = { scale: 1, x: 0, y: 0, dragging: false, startX: 0, startY: 0 };

  const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

  const renderMap = () => {
    mapStage.style.transform = `translate(${mapState.x}px, ${mapState.y}px) scale(${mapState.scale})`;
  };

  const changeZoom = (step) => {
    mapState.scale = clamp(mapState.scale + step, 0.8, 2.4);
    renderMap();
  };

  const resetMap = () => {
    mapState.scale = 1;
    mapState.x = 0;
    mapState.y = 0;
    interactiveMap.removeAttribute("data-focused-route");
    renderMap();
  };

  mapControls.forEach((control) => {
    control.addEventListener("click", async () => {
      const action = control.dataset.mapAction;
      if (action === "zoom-in") changeZoom(0.2);
      if (action === "zoom-out") changeZoom(-0.2);
      if (action === "reset") resetMap();
      if (action === "fullscreen") {
        if (document.fullscreenElement) await document.exitFullscreen();
        else if (interactiveMap.requestFullscreen) await interactiveMap.requestFullscreen();
      }
    });
  });

  interactiveMap.addEventListener("wheel", (event) => {
    event.preventDefault();
    changeZoom(event.deltaY < 0 ? 0.12 : -0.12);
  }, { passive: false });

  interactiveMap.addEventListener("pointerdown", (event) => {
    if (event.target.closest("button")) return;
    mapState.dragging = true;
    mapState.startX = event.clientX - mapState.x;
    mapState.startY = event.clientY - mapState.y;
    interactiveMap.classList.add("is-dragging");
    interactiveMap.setPointerCapture(event.pointerId);
  });

  interactiveMap.addEventListener("pointermove", (event) => {
    if (!mapState.dragging) return;
    mapState.x = clamp(event.clientX - mapState.startX, -420, 420);
    mapState.y = clamp(event.clientY - mapState.startY, -280, 280);
    renderMap();
  });

  const stopDragging = (event) => {
    if (!mapState.dragging) return;
    mapState.dragging = false;
    interactiveMap.classList.remove("is-dragging");
    if (interactiveMap.hasPointerCapture(event.pointerId)) interactiveMap.releasePointerCapture(event.pointerId);
  };

  interactiveMap.addEventListener("pointerup", stopDragging);
  interactiveMap.addEventListener("pointercancel", stopDragging);

  interactiveMap.addEventListener("keydown", (event) => {
    const movement = 24;
    if (["+", "="].includes(event.key)) changeZoom(0.2);
    else if (event.key === "-") changeZoom(-0.2);
    else if (event.key === "ArrowLeft") mapState.x += movement;
    else if (event.key === "ArrowRight") mapState.x -= movement;
    else if (event.key === "ArrowUp") mapState.y += movement;
    else if (event.key === "ArrowDown") mapState.y -= movement;
    else if (event.key === "0") resetMap();
    else return;
    event.preventDefault();
    renderMap();
  });

  routeButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const route = button.dataset.focusRoute;
      const alreadyFocused = interactiveMap.dataset.focusedRoute === route;
      if (alreadyFocused) interactiveMap.removeAttribute("data-focused-route");
      else interactiveMap.dataset.focusedRoute = route;
      interactiveMap.scrollIntoView({ behavior: "smooth", block: "center" });
    });
  });
}

const fleetDialogOpeners = document.querySelectorAll("[data-open-fleet-dialog]");
const fleetDialogClosers = document.querySelectorAll("[data-close-fleet-dialog]");

fleetDialogOpeners.forEach((opener) => {
  opener.addEventListener("click", () => {
    const dialog = document.getElementById(opener.dataset.openFleetDialog);
    if (!dialog) return;

    const createMenu = opener.closest(".fleet-create-menu");
    if (createMenu) createMenu.removeAttribute("open");
    dialog.showModal();
    const firstField = dialog.querySelector("input:not([type='hidden']), select, textarea");
    if (firstField) firstField.focus();
  });
});

fleetDialogClosers.forEach((closer) => {
  closer.addEventListener("click", () => closer.closest("dialog")?.close());
});

document.querySelectorAll(".fleet-dialog").forEach((dialog) => {
  dialog.addEventListener("click", (event) => {
    const bounds = dialog.getBoundingClientRect();
    const clickedBackdrop = event.clientX < bounds.left || event.clientX > bounds.right
      || event.clientY < bounds.top || event.clientY > bounds.bottom;
    if (clickedBackdrop) dialog.close();
  });
});
