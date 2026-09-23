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

const userDialogOpeners = document.querySelectorAll("[data-open-user-dialog]");
const userDialogClosers = document.querySelectorAll("[data-close-user-dialog]");

userDialogOpeners.forEach((opener) => {
  opener.addEventListener("click", () => {
    const dialog = document.getElementById(opener.dataset.openUserDialog);
    if (!dialog) return;
    dialog.showModal();
    const firstField = dialog.querySelector("input:not([type='hidden']), select, textarea");
    if (firstField) firstField.focus();
  });
});

userDialogClosers.forEach((closer) => {
  closer.addEventListener("click", () => closer.closest("dialog")?.close());
});

document.querySelectorAll(".user-dialog").forEach((dialog) => {
  dialog.addEventListener("click", (event) => {
    const bounds = dialog.getBoundingClientRect();
    const clickedBackdrop = event.clientX < bounds.left || event.clientX > bounds.right
      || event.clientY < bounds.top || event.clientY > bounds.bottom;
    if (clickedBackdrop) dialog.close();
  });
});

const systemAlertAudio = document.querySelector("[data-system-alert-audio]");
const alertSoundToggle = document.querySelector("[data-alert-sound-toggle]");

if (systemAlertAudio && alertSoundToggle) {
  const preferenceKey = "uairotas-alert-sound";
  const heardKey = "uairotas-heard-alerts";
  const soundBadge = alertSoundToggle.querySelector("[data-alert-sound-badge]");
  const soundStatus = document.querySelector("[data-alert-sound-status]");
  let soundEnabled = localStorage.getItem(preferenceKey) !== "off";
  let isPlaying = false;

  const readHeardAlerts = () => {
    try {
      return new Set(JSON.parse(sessionStorage.getItem(heardKey) || "[]"));
    } catch (error) {
      return new Set();
    }
  };

  const heardAlerts = readHeardAlerts();
  const pendingAlerts = new Set(
    [...document.querySelectorAll("[data-audible-alert]")]
      .map((alert) => alert.dataset.alertId)
      .filter((alertId) => alertId && !heardAlerts.has(alertId)),
  );

  const saveHeardAlerts = () => {
    try {
      sessionStorage.setItem(heardKey, JSON.stringify([...heardAlerts]));
    } catch (error) {
      // O alerta continua funcional mesmo quando o armazenamento está indisponível.
    }
  };

  const updateSoundControl = () => {
    alertSoundToggle.classList.toggle("is-muted", !soundEnabled);
    alertSoundToggle.classList.toggle("has-pending-alerts", pendingAlerts.size > 0);
    alertSoundToggle.setAttribute("aria-pressed", String(soundEnabled));
    alertSoundToggle.setAttribute(
      "aria-label",
      soundEnabled ? "Desativar alertas sonoros" : "Ativar alertas sonoros",
    );
    alertSoundToggle.title = soundEnabled ? "Alertas sonoros ativados" : "Alertas sonoros desativados";
    if (soundBadge) {
      soundBadge.textContent = String(pendingAlerts.size);
      soundBadge.hidden = pendingAlerts.size === 0;
    }
  };

  const markPendingAsHeard = () => {
    pendingAlerts.forEach((alertId) => heardAlerts.add(alertId));
    pendingAlerts.clear();
    saveHeardAlerts();
    updateSoundControl();
  };

  const playPendingAlert = async () => {
    if (!soundEnabled || pendingAlerts.size === 0 || isPlaying) return false;
    systemAlertAudio.currentTime = 0;
    systemAlertAudio.volume = 0.72;
    try {
      isPlaying = true;
      await systemAlertAudio.play();
      markPendingAsHeard();
      alertSoundToggle.classList.remove("needs-interaction");
      if (soundStatus) soundStatus.textContent = "Alerta sonoro reproduzido.";
      return true;
    } catch (error) {
      isPlaying = false;
      alertSoundToggle.classList.add("needs-interaction");
      if (soundStatus) {
        soundStatus.textContent = "Existem alertas novos. Interaja com a página ou use o botão de som para ouvi-los.";
      }
      return false;
    }
  };

  systemAlertAudio.addEventListener("ended", () => {
    isPlaying = false;
    playPendingAlert();
  });
  systemAlertAudio.addEventListener("error", () => {
    isPlaying = false;
    alertSoundToggle.classList.add("has-audio-error");
    if (soundStatus) soundStatus.textContent = "Não foi possível carregar o som dos alertas.";
  });

  const unlockAudio = async (event) => {
    if (event.target.closest?.("[data-alert-sound-toggle]")) return;
    const played = await playPendingAlert();
    if (played) {
      document.removeEventListener("pointerdown", unlockAudio, true);
      document.removeEventListener("keydown", unlockAudio, true);
    }
  };

  document.addEventListener("pointerdown", unlockAudio, true);
  document.addEventListener("keydown", unlockAudio, true);

  alertSoundToggle.addEventListener("click", async () => {
    soundEnabled = !soundEnabled;
    localStorage.setItem(preferenceKey, soundEnabled ? "on" : "off");
    if (!soundEnabled) {
      systemAlertAudio.pause();
      systemAlertAudio.currentTime = 0;
      isPlaying = false;
      if (soundStatus) soundStatus.textContent = "Alertas sonoros desativados.";
    } else {
      if (soundStatus) soundStatus.textContent = "Alertas sonoros ativados.";
    }
    updateSoundControl();
    if (soundEnabled) await playPendingAlert();
  });

  window.addEventListener("uairotas:alert", (event) => {
    const alertId = event.detail?.id || `realtime-${Date.now()}`;
    if (heardAlerts.has(alertId)) return;
    pendingAlerts.add(alertId);
    updateSoundControl();
    playPendingAlert();
  });

  updateSoundControl();
  window.setTimeout(playPendingAlert, 250);
}
