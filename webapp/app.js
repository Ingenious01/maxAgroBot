const API_BASE =
  "https://muskiness-obtrusive-lumping.ngrok-free.dev";

const loadingScreen =
  document.getElementById("loading-screen");

const gateScreen =
  document.getElementById("gate-screen");

const appShell =
  document.getElementById("app-shell");

const themeToggle =
  document.getElementById("theme-toggle");

const changeEmailButton =
  document.getElementById("change-email");

const themeIconSun =
  document.getElementById("theme-icon-sun");

const themeIconMoon =
  document.getElementById("theme-icon-moon");

const EVENT_ICONS = [
  "🌱",
  "🌾",
  "🌻",
  "🚜",
  "🐄",
];

function getDeviceTheme() {
  return window.matchMedia(
    "(prefers-color-scheme: dark)"
  ).matches
    ? "dark"
    : "light";
}

function getInitialTheme() {
  const savedTheme =
    localStorage.getItem("theme");

  if (
    savedTheme === "light" ||
    savedTheme === "dark"
  ) {
    return savedTheme;
  }

  return getDeviceTheme();
}

function applyTheme(
  theme,
  save = false
) {
  document.documentElement.dataset.theme =
    theme;

  if (save) {
    localStorage.setItem(
      "theme",
      theme
    );
  }

  const isDark =
    theme === "dark";

  themeToggle?.classList.toggle(
    "is-dark",
    isDark
  );

  themeToggle?.setAttribute(
    "aria-label",
    isDark
      ? "Включить светлую тему"
      : "Включить тёмную тему"
  );
}

function initTheme() {
  applyTheme(
    getInitialTheme()
  );

  themeToggle?.addEventListener(
    "click",
    () => {
      const currentTheme =
        document.documentElement
          .dataset.theme ||
        getDeviceTheme();

      const nextTheme =
        currentTheme === "dark"
          ? "light"
          : "dark";

      applyTheme(
        nextTheme,
        true
      );
    }
  );
}

function initEventIcons() {
  const icons = [...EVENT_ICONS];

  for (
    let i = icons.length - 1;
    i > 0;
    i--
  ) {
    const j =
      Math.floor(
        Math.random() * (i + 1)
      );

    [icons[i], icons[j]] =
      [icons[j], icons[i]];
  }

  document
    .querySelectorAll(
      "[data-event-icon]"
    )
    .forEach(
      (element, index) => {
        element.textContent =
          icons[
            index % icons.length
          ];
      }
    );
}

function initAccordion() {
  const toggle =
    document.getElementById(
      "events-toggle"
    );

  const content =
    document.getElementById(
      "events-content"
    );

  const chevron =
    document.getElementById(
      "events-chevron"
    );

  if (
    !toggle ||
    !content ||
    !chevron
  ) {
    return;
  }

  toggle.addEventListener(
    "click",
    () => {
      const isOpen =
        toggle.getAttribute(
          "aria-expanded"
        ) === "true";

      toggle.setAttribute(
        "aria-expanded",
        String(!isOpen)
      );

      content.classList.toggle(
        "collapsed",
        isOpen
      );

      chevron.classList.toggle(
        "collapsed",
        isOpen
      );
    }
  );
}

function showLoading() {
  loadingScreen?.classList.remove(
    "hidden",
    "fade-out"
  );

  gateScreen?.classList.add(
    "hidden"
  );

  appShell?.classList.add(
    "hidden"
  );
}

function hideLoading(
  callback
) {
  if (!loadingScreen) {
    callback?.();
    return;
  }

  loadingScreen.classList.add(
    "fade-out"
  );

  setTimeout(() => {
    loadingScreen.classList.add(
      "hidden"
    );

    callback?.();
  }, 550);
}

function showGate() {
  hideLoading(() => {
    gateScreen?.classList.remove(
      "hidden"
    );

    requestAnimationFrame(() => {
      gateScreen?.classList.add(
        "screen-visible"
      );
    });
  });

  appShell?.classList.add(
    "hidden"
  );
}

function showError(message) {
  hideLoading(() => {
    if (!gateScreen) {
      return;
    }

    gateScreen.innerHTML = `
      <div class="gate-icon">⚠️</div>

      <h1 class="gate-title">
        Не удалось проверить доступ
      </h1>

      <p class="gate-text">
        ${message}
      </p>
    `;

    gateScreen.classList.remove(
      "hidden"
    );

    requestAnimationFrame(() => {
      gateScreen.classList.add(
        "screen-visible"
      );
    });
  });

  appShell?.classList.add(
    "hidden"
  );
}

function showApp() {
  hideLoading(() => {
    gateScreen?.classList.add(
      "hidden"
    );

    appShell?.classList.remove(
      "hidden"
    );

    requestAnimationFrame(() => {
      appShell?.classList.add(
        "screen-visible"
      );
    });
  });
}

function initApp() {
  showApp();

  initEventIcons();
  initAccordion();

  try {
    window.WebApp?.ready?.();
  } catch (e) {
    console.warn(e);
  }

  document
    .getElementById("menu")
    ?.addEventListener(
      "click",
      (e) => {
        const link =
          e.target.closest(
            "a[href]"
          );

        if (!link) {
          return;
        }

        if (
          window.WebApp?.openLink
        ) {
          e.preventDefault();

          window.WebApp.openLink(
            link.href
          );
        }
      }
    );
}

async function checkAccess() {
  showLoading();

  try {
    window.WebApp?.ready?.();
  } catch (_) {}

  const initData =
    window.WebApp?.initData;

  if (!initData) {
    showGate();
    return;
  }

  try {
    const response =
      await fetch(
        `${API_BASE}/api/auth`,
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json",
          },
          body: JSON.stringify({
            initData,
          }),
        }
      );

    if (!response.ok) {
      const error =
        await response
          .json()
          .catch(() => ({}));

      console.error(
        "Ошибка авторизации:",
        response.status,
        error
      );

      showGate();
      return;
    }

    const result =
      await response.json();

    console.log(
      "Результат проверки:",
      result
    );

    if (
      result.authenticated &&
      result.allowed
    ) {
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