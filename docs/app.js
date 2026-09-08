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

const menu = document.getElementById("menu");
const panel = document.getElementById("panel");
const panelTitle = document.getElementById("panel-title");
const panelBody = document.getElementById("panel-body");
const btnBack = document.getElementById("btn-back");

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