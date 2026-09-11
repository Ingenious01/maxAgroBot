function getStartPayload() {
  try {
    const p = window.WebApp?.initDataUnsafe?.start_param;
    if (p) return String(p);
  } catch (_) {}
  try {
    const q = new URLSearchParams(window.location.search);
    return q.get("payload") || q.get("startapp") || "";
  } catch (_) {
    return "";
  }
}

function isOnboarded() {
  // TODO: включить проверку, когда будет бэкенд или стабильный start_param
  return true;
}

function showGate() {
  document.body.innerHTML = `
    <div style="padding:24px;font-family:system-ui,sans-serif;background:#0f1419;color:#e7ecf3;min-height:100vh">
      <h1 style="font-size:1.2rem;margin:0 0 12px">Доступ пока закрыт</h1>
      <p style="color:#8b9bb4;line-height:1.5;margin:0">
        Сначала в чате с ботом примите политику и укажите email
        или нажмите «Пропустить». Затем откройте приложение кнопкой в сообщении бота.
      </p>
    </div>
  `;
}

function initApp() {
  try {
    window.WebApp?.ready?.();
  } catch (e) {
    console.warn(e);
  }

  // Ссылки внутри MAX лучше открывать через Bridge, если есть
  document.getElementById("menu")?.addEventListener("click", (e) => {
    const a = e.target.closest("a[href]");
    if (!a) return;
    const url = a.href;
    if (window.WebApp?.openLink) {
      e.preventDefault();
      window.WebApp.openLink(url);
    }
  });
}

if (!isOnboarded()) {
  showGate();
} else {
  initApp();
}