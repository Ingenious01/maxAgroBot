const API_BASE = "https://muskiness-obtrusive-lumping.ngrok-free.dev";

const loadingScreen = document.getElementById("loading-screen");
const gateScreen = document.getElementById("gate-screen");
const appShell = document.getElementById("app-shell");
const themeToggle = document.getElementById("theme-toggle");
const themeIcon = document.getElementById("theme-icon");

function showLoading() {
  loadingScreen?.classList.remove("hidden");
  gateScreen?.classList.add("hidden");
  appShell?.classList.add("hidden");
}

function showGate() {
  loadingScreen?.classList.add("hidden");
  appShell?.classList.add("hidden");
  gateScreen?.classList.remove("hidden");
}

function showApp() {
  loadingScreen?.classList.add("hidden");
  gateScreen?.classList.add("hidden");
  appShell?.classList.remove("hidden");
}

function showError(message) {
  loadingScreen?.classList.add("hidden");
  appShell?.classList.add("hidden");
  gateScreen?.classList.remove("hidden");

  if (gateScreen) {
    gateScreen.innerHTML = `
      <div class="gate-icon">⚠️</div>

      <h1 class="gate-title">
        Не удалось проверить доступ
      </h1>

      <p class="gate-text">
        ${message}
      </p>
    `;
  }
}

function getSystemTheme() {
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;

  if (themeIcon) {
    themeIcon.textContent = theme === "dark" ? "☀️" : "🌙";
  }

  themeToggle?.setAttribute(
    "aria-label",
    theme === "dark"
      ? "Включить светлую тему"
      : "Включить тёмную тему"
  );
}

function initTheme() {
  applyTheme(
    document.documentElement.dataset.theme || getSystemTheme()
  );

  themeToggle?.addEventListener("click", () => {
    const currentTheme =
      document.documentElement.dataset.theme || getSystemTheme();

    const nextTheme =
      currentTheme === "dark"
        ? "light"
        : "dark";

    applyTheme(nextTheme);
  });
}

function initApp() {
  showApp();

  try {
    window.WebApp?.ready?.();
  } catch (e) {
    console.warn(e);
  }

  document.getElementById("menu")?.addEventListener("click", (e) => {
    const link = e.target.closest("a[href]");

    if (!link) return;

    if (window.WebApp?.openLink) {
      e.preventDefault();
      window.WebApp.openLink(link.href);
    }
  });
}

async function checkAccess() {
  showLoading();

  try {
    window.WebApp?.ready?.();
  } catch (_) {}

  const initData = window.WebApp?.initData;

  if (!initData) {
    showGate();
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/api/auth`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        initData,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));

      console.error(
        "Ошибка авторизации:",
        response.status,
        error
      );

      showGate();
      return;
    }

    const result = await response.json();

    console.log("Результат проверки:", result);

    if (result.authenticated && result.allowed) {
      initApp();
    } else {
      showGate();
    }
  } catch (error) {
    console.error(
      "Не удалось проверить доступ:",
      error
    );

    showError(
      "Проверьте, что сервер приложения доступен."
    );
  }
}

initTheme();
checkAccess();