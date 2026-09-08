const TEXTS = {
  about: {
    title: "О проекте",
    body: "Мы — аграрный центр Томской области. Консультируем представителей малого агробизнеса. Раздел скоро будет наполнен.",
  },
  news: {
    title: "Новости АПК",
    body: "Лента новостей появится здесь. Пока раздел в разработке.",
  },
  events: {
    title: "Календарь мероприятий",
    body: "Ближайшие семинары и встречи — в следующих версиях приложения.",
  },
  seminars: {
    title: "Семинары и обучение",
    body: "Список программ обучения появится позже.",
  },
  consult: {
    title: "Запись на консультацию",
    body: "Форма записи будет добавлена. Пока напишите боту в чат.",
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
    body: "Email и настройки профиля будут доступны здесь после интеграции с ботом.",
  },
};

const menu = document.querySelector(".menu");
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
  if (window.WebApp?.BackButton) {
    window.WebApp.BackButton.show();
  }
}

function showMenu() {
  panel.classList.add("hidden");
  menu.classList.remove("hidden");
  if (window.WebApp?.BackButton) {
    window.WebApp.BackButton.hide();
  }
}

menu.addEventListener("click", (e) => {
  const btn = e.target.closest("[data-section]");
  if (!btn) return;
  showPanel(btn.dataset.section);
});

btnBack.addEventListener("click", showMenu);

if (window.WebApp) {
  try {
    window.WebApp.ready?.();
    window.WebApp.BackButton?.onClick?.(showMenu);
  } catch (e) {
    console.warn(e);
  }
}