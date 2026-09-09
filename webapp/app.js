const TEXTS = {
  about: {
    title: "О проекте",
    body: "Мы — аграрный центр Томской области. Консультируем представителей малого агробизнеса.\n\nРаздел скоро будет наполнен.",
  },
  news: {
    title: "Новости АПК",
    body: "Лента новостей появится здесь. Пока раздел в разработке.",
  },
  events: {
    title: "Календарь мероприятий",
    body: "Ближайшие семинары и встречи появятся в следующих версиях.",
  },
  seminars: {
    title: "Семинары и обучение",
    body: "Список программ обучения появится позже.",
  },
  consult: {
    title: "Запись на консультацию",
    body: "Форма записи будет добавлена.\nПока напишите боту в чат.",
  },
  materials: {
    title: "Полезные материалы",
    body: "Подборки и файлы появятся в этом разделе.",
  },
  contacts: {
    title: "Контакты",
    body: "Телефон: +7 (953) 912-50-70\nТомская область",
  },
  mydata: {
    title: "Мои данные",
    body: "Email и настройки профиля появятся после интеграции с ботом.",
  },
};

function getStartPayload() {
  try {
    const p = window.WebApp?.initDataUnsafe?.start_param;
    if (p) return String(p);
  } catch (_) {}

  try {
    const q = new URLSearchParams(window.location.search);
    return q.get("startapp") || q.get("payload") || "";
  } catch (_) {
    return "";
  }
}

const API_BASE_URL = "https://muskiness-obtrusive-lumping.ngrok-free.dev";

async function checkAccess() {
  const initData = window.WebApp?.initData;

  if (!initData) {
    console.error("MAX initData отсутствует");
    showGate();
    return;
  }

  try {
    const response = await fetch(
      `${API_BASE_URL}/api/auth`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          initData: initData
        })
      }
    );

    if (!response.ok) {
      console.error(
        "Ошибка авторизации:",
        response.status
      );

      showGate();
      return;
    }

    const result = await response.json();

    console.log("Результат проверки:", result);

    if (result.authenticated && result.allowed) {
      initMenu();
    } else {
      showGate();
    }

  } catch (error) {
    console.error(
      "Не удалось проверить доступ:",
      error
    );

    showGate();
  }
}


checkAccess();

function showGate() {
  document.body.innerHTML = `
    <div style="
      padding: 32px 24px;
      font-family: system-ui, sans-serif;
      background: #0f1419;
      color: #e7ecf3;
      min-height: 100vh;
      box-sizing: border-box;
      text-align: center;
    ">
      <div style="
        font-size: 48px;
        margin-bottom: 20px;
      ">🔒</div>

      <h1 style="
        font-size: 1.4rem;
        margin: 0 0 16px;
      ">
        Доступ ограничен
      </h1>

      <p style="
        color: #8b9bb4;
        line-height: 1.6;
        margin: 0;
      ">
        Для доступа к основным функциям
        необходимо завершить регистрацию
        в чат-боте «Томский агробизнес».
      </p>
    </div>
  `;
}

function initMenu() {
  const menu = document.getElementById("menu");
  const panel = document.getElementById("panel");
  const panelTitle = document.getElementById("panel-title");
  const panelBody = document.getElementById("panel-body");
  const btnBack = document.getElementById("btn-back");

  if (!menu || !panel || !btnBack) return;

  function showPanel(key) {
    const data = TEXTS[key];
    if (!data) return;
    panelTitle.textContent = data.title;
    panelBody.textContent = data.body;
    menu.classList.add("hidden");
    panel.classList.remove("hidden");
    try { window.WebApp?.BackButton?.show?.(); } catch (_) {}
  }

  function showMenu() {
    panel.classList.add("hidden");
    menu.classList.remove("hidden");
    try { window.WebApp?.BackButton?.hide?.(); } catch (_) {}
  }

  menu.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-section]");
    if (!btn) return;
    showPanel(btn.dataset.section);
  });

  btnBack.addEventListener("click", showMenu);

  try {
    window.WebApp?.ready?.();
    window.WebApp?.BackButton?.onClick?.(showMenu);
  } catch (e) {
    console.warn(e);
  }
}