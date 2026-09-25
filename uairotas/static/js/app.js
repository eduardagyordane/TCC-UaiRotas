(() => {
  "use strict";
  const $ = selector => document.querySelector(selector);
  const $$ = selector => [...document.querySelectorAll(selector)];
  const storage = UaiRotas.safeStorage(() => window.localStorage);
  const sessionStore = UaiRotas.safeStorage(() => window.sessionStorage);
  const themeButton = $("[data-theme-toggle]");
  function updateTheme() {
    const dark = document.documentElement.dataset.theme === "dark";
    themeButton?.setAttribute("aria-pressed", String(dark));
    themeButton?.setAttribute("aria-label", dark ? "Ativar modo claro" : "Ativar modo escuro");
  }
  themeButton?.addEventListener("click", () => {
    document.documentElement.dataset.theme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    storage.set("uairotas-theme", document.documentElement.dataset.theme);
    updateTheme(); window.dispatchEvent(new CustomEvent("uairotas:theme"));
  });
  updateTheme();
  $("[data-password-toggle]")?.addEventListener("click", event => {
    const input = $("#password"), button = event.currentTarget, show = input.type === "password";
    input.type = show ? "text" : "password";
    button.setAttribute("aria-label", show ? "Ocultar senha" : "Mostrar senha");
    button.setAttribute("aria-pressed", String(show));
  });
  const navButton = $("[data-nav-toggle]"), nav = $("[data-main-nav]");
  const closeNav = () => { nav?.classList.remove("is-open"); navButton?.setAttribute("aria-expanded", "false"); };
  navButton?.addEventListener("click", () => {
    const opened = nav.classList.toggle("is-open");
    navButton.setAttribute("aria-expanded", String(opened));
  });
  document.addEventListener("click", event => {
    if (!event.target.closest(".app-header")) closeNav();
    for (const menu of $$(".profile-menu[open], .action-menu[open]"))
      if (!menu.contains(event.target)) menu.open = false;
  });
  document.addEventListener("keydown", event => {
    if (event.key !== "Escape") return;
    if (nav?.classList.contains("is-open")) { closeNav(); navButton.focus(); }
    for (const menu of $$(".profile-menu[open], .action-menu[open]")) { menu.open = false; menu.querySelector("summary").focus(); }
  });
  function openDialog(dialog, opener = document.activeElement) {
    if (!dialog) return;
    dialog._opener = opener;
    for (const menu of $$(".action-menu[open], .profile-menu[open]")) menu.open = false;
    if (!dialog.open) dialog.showModal();
    (dialog.querySelector("[data-form-errors]") || dialog.querySelector("[aria-invalid='true']") ||
      dialog.querySelector("input:not([type=hidden]),select") || dialog.querySelector("button"))?.focus();
  }
  $$("[data-dialog-open]").forEach(button => button.addEventListener("click", () => openDialog(document.getElementById(button.dataset.dialogOpen), button)));
  $$("[data-dialog-close]").forEach(button => button.addEventListener("click", () => button.closest("dialog").close()));
  $$("dialog").forEach(dialog => {
    dialog.addEventListener("close", () => dialog._opener?.focus());
    dialog.addEventListener("click", event => {
      const r = dialog.getBoundingClientRect();
      if (event.target === dialog && (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom)) dialog.close();
    });
  });
  $$("[data-auto-open]").forEach(dialog => openDialog(dialog));
  $$("input[type=file][name=foto]").forEach(input => {
    const preview = document.createElement("img");
    preview.alt = "Prévia da foto selecionada"; preview.className = "photo-preview"; preview.hidden = true;
    input.after(preview);
    let objectUrl;
    input.addEventListener("change", () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl);
      preview.hidden = true; input.setCustomValidity("");
      const file = input.files[0];
      if (!file) return;
      if (file.size > 512 * 1024 || !["image/png","image/jpeg"].includes(file.type)) {
        input.setCustomValidity("Escolha uma imagem PNG ou JPEG de até 512 KB."); input.reportValidity(); return;
      }
      objectUrl = URL.createObjectURL(file); preview.src = objectUrl; preview.hidden = false;
    });
  });
  const userForm = $("[data-user-form]");
  function resetUser() {
    userForm.reset(); userForm.querySelector("[data-form-errors]")?.remove();
    userForm.querySelectorAll(".field-error").forEach(e => e.remove());
    userForm.querySelectorAll("[aria-invalid]").forEach(e => { e.removeAttribute("aria-invalid"); e.removeAttribute("aria-describedby"); });
    for (const input of userForm.elements) if (input.name && input.name !== "csrf_token") {
      if (input.type === "checkbox") input.checked = true; else input.value = "";
    }
    userForm.elements.role.value = "supervisor";
  }
  $("[data-user-create]")?.addEventListener("click", event => {
    resetUser(); userForm.action = userForm.dataset.createAction; userForm.elements.password.required = true;
    $("#user-dialog-title").textContent = "Novo usuário"; openDialog($("#user-dialog"), event.currentTarget);
  });
  $$("[data-user-edit]").forEach(button => button.addEventListener("click", async () => {
    button.disabled = true; const controller = new AbortController(), timeout = setTimeout(() => controller.abort(), 10000);
    const message = $("[data-user-message]"); message.textContent = "Carregando cadastro…";
    try {
      const response = await fetch(button.dataset.userEdit, { signal:controller.signal, headers:{Accept:"application/json"} });
      if (!response.ok) throw new Error("http");
      const data = await response.json(); resetUser();
      for (const [key, value] of Object.entries(data)) {
        const control = userForm.elements.namedItem(key);
        if (control) { if (control.type === "checkbox") control.checked = !!value; else control.value = value; }
      }
      const action = new URL(data.action, window.location.origin);
      action.search = new URL(userForm.dataset.createAction, window.location.origin).search;
      userForm.action = action.pathname + action.search; userForm.elements.password.required = false;
      $("#user-dialog-title").textContent = "Editar usuário"; message.textContent = ""; openDialog($("#user-dialog"), button);
    } catch (_) { message.textContent = "Não foi possível carregar o cadastro. Atualize a página e tente novamente."; }
    finally { clearTimeout(timeout); button.disabled = false; }
  }));
  $$("form[method='post']").forEach(form => form.addEventListener("submit", () => {
    form.setAttribute("aria-busy", "true");
    form.querySelectorAll("button[type=submit]").forEach(button => { button.disabled = true; });
  }));
  window.addEventListener("pageshow", () => {
    $$("form[aria-busy]").forEach(form => { form.removeAttribute("aria-busy"); form.querySelectorAll("button[type=submit]").forEach(b => { b.disabled = false; }); });
  });
  let printDetails = [];
  window.addEventListener("beforeprint", () => { printDetails = $$("details.data-alternative:not([open])"); printDetails.forEach(d => { d.open = true; }); });
  window.addEventListener("afterprint", () => printDetails.forEach(d => { d.open = false; }));
  $("[data-print]")?.addEventListener("click", () => window.print());
  const audio = $("[data-system-alert-audio]"), soundButton = $("[data-alert-sound-toggle]");
  if (!audio || !soundButton) return;
  const player = UaiRotas.alertPlayer({
    audio, preferences:storage, heardStorage:sessionStore, userId:document.body.dataset.userId,
    update(state) {
      soundButton.classList.toggle("is-muted", !state.enabled);
      soundButton.classList.toggle("needs-interaction", state.blocked && state.pending > 0);
      soundButton.classList.toggle("has-audio-error", state.failed);
      const label = state.enabled ? ((state.blocked || state.failed) ? "Ativar reprodução dos alertas" : "Desativar alertas sonoros") : "Ativar alertas sonoros";
      soundButton.setAttribute("aria-label", label); soundButton.setAttribute("title", label);
      soundButton.setAttribute("aria-pressed", String(state.enabled));
      const badge = $("[data-alert-sound-badge]"); badge.hidden = !state.pending; badge.textContent = String(state.pending);
      $("[data-sound-volume]").value = Math.round(state.volume * 100);
      $$("[data-sound-category]").forEach(input => { input.checked = state.categories[input.dataset.soundCategory] !== false; });
      const text = state.failed ? "Falha ao reproduzir. Tente novamente pelo sino." : state.blocked ? "O navegador bloqueou o áudio. Clique no sino para liberar." : !state.enabled ? "Som desativado. Os alertas continuam visíveis." : "Som ativado · volume " + Math.round(state.volume * 100) + "%";
      $("[data-alert-sound-status]").textContent = text; $("[data-sound-feedback]").textContent = text;
    }
  });
  soundButton.addEventListener("click", () => player.toggle());
  $("[data-sound-volume]").addEventListener("input", event => player.setVolume(event.target.value / 100));
  $$("[data-sound-category]").forEach(input => input.addEventListener("change", () => player.setCategory(input.dataset.soundCategory, input.checked)));
  $("[data-sound-test]").addEventListener("click", () => player.play(true));
  player.receive($$("[data-audible-alert]").map(element => ({ id:element.dataset.alertId, category:element.dataset.alertCategory })));
  setTimeout(() => player.play(), 300);
  const unlock = event => {
    if (event.target.closest("[data-alert-sound-toggle],#sound-settings")) return;
    if (player.state().blocked) player.play();
  };
  document.addEventListener("pointerdown", unlock);
  document.addEventListener("keydown", unlock);
  window.addEventListener("uairotas:alert", event => { if (event.detail?.id) { player.receive([event.detail]); player.play(); } });
})();
