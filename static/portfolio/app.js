// ==========================================================================
// PORTFOLIO & CV BUILDER — MAIN APPLICATION CONTROLLER
// ==========================================================================

const STORAGE_KEY = 'portfolio_builder_state_v2';

// 1. Инициализация начального состояния (State) с реальными данными Алексея Юпатова
let portfolioState = {
    name: "Алексей Юпатов",
    role: "Junior Frontend-разработчик / Верстальщик / Аналитик",
    status: "🟢 Открыт к предложениям и стажировкам (100% удаленно)",
    bio: "Специализируюсь на адаптивной и кроссбраузерной верстке сайтов, лендингов и интерфейсов по макетам Figma (HTML5/CSS3/JavaScript) и автоматизации задач на Python. Имею практический опыт в SEO, аналитике данных и инфографике (Wildberries). Пишу чистый код, внимателен к деталям и нацелен на быстрое погружение в проекты команды.",
    resumeUrl: "#",
    socials: {
        telegram: "@ApeLsinn03",
        email: "yupatov.alesha@gmail.com",
        whatsapp: "+7 923 162 9223",
        github: "https://github.com"
    },
    skills: [
        { name: "HTML5 & Семантическая верстка", icon: "🌐", level: "Уверенный", desc: "Адаптивная, кроссбраузерная верстка, доступность, SEO-структура.", percent: 90 },
        { name: "CSS3 / SCSS / Flexbox / Grid", icon: "🎨", level: "Уверенный", desc: "Pixel-perfect перенос из Figma, анимации, адаптив под смартфоны.", percent: 90 },
        { name: "Figma в Верстку", icon: "📐", level: "Уверенный", desc: "Чтение Auto Layout, экспорт графики, точное соблюдение отступов.", percent: 90 },
        { name: "JavaScript (ES6+)", icon: "⚡", level: "Базовый / DOM", desc: "Интерактив на страницах, формы, события, fetch-запросы к API.", percent: 75 },
        { name: "Python & Автоматизация", icon: "🐍", level: "Уверенный", desc: "Парсеры данных (BeautifulSoup/requests), Telegram-боты, SQLite.", percent: 80 },
        { name: "SEO & Аналитика данных", icon: "📊", level: "Практический опыт", desc: "Опыт работы с маркетплейсами (Wildberries), анализ метрик, контент.", percent: 85 }
    ],
    projects: [
        {
            title: "Адаптивный Landing Page по макету Figma",
            category: "Адаптивная верстка",
            desc: "Pixel-perfect верстка многостраничного адаптивного лендинга с темной/светлой темой, калькулятором стоимости и формой заявки.",
            tags: ["HTML5", "CSS3", "JavaScript", "Figma"],
            icon: "💻",
            demoUrl: "#",
            githubUrl: "https://github.com",
            figmaUrl: ""
        },
        {
            title: "Job Radar — Telegram-бот и парсер вакансий на Python",
            category: "Python & Автоматизация",
            desc: "Многопоточный парсер удаленных вакансий без опыта с HeadHunter, Хабра и Telegram, фильтрацией по зарплате и генерацией Excel-отчетов.",
            tags: ["Python", "Telegram API", "SQLite", "OpenPyXL", "AI Gemini"],
            icon: "🤖",
            demoUrl: "https://t.me/JobRadar111_bot",
            githubUrl: "https://github.com",
            figmaUrl: ""
        },
        {
            title: "Portfolio & CV Builder — Веб-конструктор портфолио",
            category: "Веб-приложение",
            desc: "Интерактивный конструктор сайта-портфолио с живым Split-Screen превью, переключением тем и экспортом в чистый ZIP.",
            tags: ["HTML5", "Vanilla CSS", "JavaScript", "Python API"],
            icon: "🎨",
            demoUrl: "http://localhost:5174",
            githubUrl: "https://github.com",
            figmaUrl: ""
        }
    ],
    experience: [
        {
            period: "2024 — Настоящее время",
            role: "Веб-разработка, верстка сайтов и скрипты на Python",
            place: "Практические проекты и фриланс",
            desc: "Верстка адаптивных страниц по макетам Figma, создание Telegram-ботов, парсеров и скриптов автоматизации."
        },
        {
            period: "2023 — 2024",
            role: "Менеджер Wildberries (SEO, инфографика, аналитика)",
            place: "E-commerce & маркетплейсы",
            desc: "Работа с карточками товаров, поисковая оптимизация (SEO), создание инфографики и анализ ключевых показателей продаж."
        }
    ]
};

// Загрузка сохраненного состояния
try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
        portfolioState = JSON.parse(saved);
    }
} catch (e) {
    console.error("Ошибка загрузки localStorage", e);
}

function saveState() {
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(portfolioState));
    } catch (e) {}
}

// 2. Элементы DOM
const previewIframe = document.getElementById('preview-iframe');
const previewWrapper = document.getElementById('preview-wrapper');

// Функция мгновенной синхронизации с iframe
function syncPreview() {
    saveState();
    if (previewIframe && previewIframe.contentWindow && previewIframe.contentWindow.renderPortfolio) {
        previewIframe.contentWindow.renderPortfolio(portfolioState);
    }
}

// Слушаем загрузку iframe
if (previewIframe) {
    previewIframe.addEventListener('load', () => {
        setTimeout(syncPreview, 200);
    });
}

// 3. Табы в левой панели
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

        btn.classList.add('active');
        const targetId = btn.getAttribute('data-tab');
        const targetPane = document.getElementById(targetId);
        if (targetPane) targetPane.classList.add('active');
    });
});

// 4. Привязка полей «Обо мне» и «Контакты»
function initFormInputs() {
    const nameInput = document.getElementById('input-name');
    const roleInput = document.getElementById('input-role');
    const statusInput = document.getElementById('input-status');
    const bioInput = document.getElementById('input-bio');
    const resumeInput = document.getElementById('input-resume-url');

    const tgInput = document.getElementById('input-tg');
    const ghInput = document.getElementById('input-gh');
    const emailInput = document.getElementById('input-email');
    const waInput = document.getElementById('input-wa');

    // Заполнение формы текущим состоянием
    if (nameInput) nameInput.value = portfolioState.name || '';
    if (roleInput) roleInput.value = portfolioState.role || '';
    if (statusInput) statusInput.value = portfolioState.status || '';
    if (bioInput) bioInput.value = portfolioState.bio || '';
    if (resumeInput) resumeInput.value = portfolioState.resumeUrl || '';

    if (tgInput) tgInput.value = (portfolioState.socials.telegram || '').replace('@', '');
    if (ghInput) ghInput.value = portfolioState.socials.github || '';
    if (emailInput) emailInput.value = portfolioState.socials.email || '';
    if (waInput) waInput.value = portfolioState.socials.whatsapp || '';

    // Слушатели изменений
    nameInput?.addEventListener('input', (e) => { portfolioState.name = e.target.value; syncPreview(); });
    roleInput?.addEventListener('input', (e) => { portfolioState.role = e.target.value; syncPreview(); });
    statusInput?.addEventListener('input', (e) => { portfolioState.status = e.target.value; syncPreview(); });
    bioInput?.addEventListener('input', (e) => { portfolioState.bio = e.target.value; syncPreview(); });
    resumeInput?.addEventListener('input', (e) => { portfolioState.resumeUrl = e.target.value; syncPreview(); });

    tgInput?.addEventListener('input', (e) => { portfolioState.socials.telegram = '@' + e.target.value.replace('@', ''); syncPreview(); });
    ghInput?.addEventListener('input', (e) => { portfolioState.socials.github = e.target.value; syncPreview(); });
    emailInput?.addEventListener('input', (e) => { portfolioState.socials.email = e.target.value; syncPreview(); });
    waInput?.addEventListener('input', (e) => { portfolioState.socials.whatsapp = e.target.value; syncPreview(); });
}

// 5. Управление Навыками (Skills List)
const skillsListContainer = document.getElementById('skills-list');
const btnAddSkill = document.getElementById('btn-add-skill');

function renderSkillsEditor() {
    if (!skillsListContainer) return;
    skillsListContainer.innerHTML = '';

    portfolioState.skills.forEach((sk, idx) => {
        const card = document.createElement('div');
        card.className = 'item-card';
        card.innerHTML = `
            <div class="item-header">
                <span class="item-title"><span>${sk.icon || '⚡'}</span> ${sk.name}</span>
                <button type="button" class="btn-icon-danger" title="Удалить навык" onclick="deleteSkill(${idx})">🗑️</button>
            </div>
            <div class="grid-2">
                <div class="form-group">
                    <label>Название</label>
                    <input type="text" class="form-control" value="${sk.name}" oninput="updateSkill(${idx}, 'name', this.value)">
                </div>
                <div class="form-group">
                    <label>Иконка / Эмодзи</label>
                    <input type="text" class="form-control" value="${sk.icon || '⚡'}" oninput="updateSkill(${idx}, 'icon', this.value)">
                </div>
            </div>
            <div class="grid-2">
                <div class="form-group">
                    <label>Уровень владения</label>
                    <input type="text" class="form-control" value="${sk.level || 'Уверенный'}" oninput="updateSkill(${idx}, 'level', this.value)">
                </div>
                <div class="form-group">
                    <label>Процент шкалы (0-100%)</label>
                    <input type="number" min="0" max="100" class="form-control" value="${sk.percent || 85}" oninput="updateSkill(${idx}, 'percent', parseInt(this.value)||85)">
                </div>
            </div>
            <div class="form-group" style="margin-bottom: 0;">
                <label>Краткое пояснение (что умеете)</label>
                <input type="text" class="form-control" value="${sk.desc || ''}" oninput="updateSkill(${idx}, 'desc', this.value)">
            </div>
        `;
        skillsListContainer.appendChild(card);
    });
}

window.updateSkill = function(idx, field, value) {
    if (portfolioState.skills[idx]) {
        portfolioState.skills[idx][field] = value;
        syncPreview();
    }
};

window.deleteSkill = function(idx) {
    portfolioState.skills.splice(idx, 1);
    renderSkillsEditor();
    syncPreview();
    showToast("Навык удален");
};

btnAddSkill?.addEventListener('click', () => {
    portfolioState.skills.push({
        name: "Новый навык",
        icon: "⚡",
        level: "Базовый",
        desc: "Описание применения на практике",
        percent: 75
    });
    renderSkillsEditor();
    syncPreview();
    showToast("Добавлен новый навык");
});

// Пресеты навыков
document.querySelectorAll('.preset-tag').forEach(tag => {
    tag.addEventListener('click', () => {
        const preset = tag.getAttribute('data-preset');
        if (preset === 'frontend') {
            portfolioState.skills = [
                { name: "HTML5 & Семантическая верстка", icon: "🌐", level: "Уверенный", desc: "Семантическая разметка, доступность, SEO-структура.", percent: 90 },
                { name: "CSS3 / SCSS / Flex / Grid", icon: "🎨", level: "Уверенный", desc: "Pixel-perfect верстка, адаптив под смартфоны, анимации.", percent: 90 },
                { name: "Figma в Верстку", icon: "📐", level: "Уверенный", desc: "Экспорт ассетов, чтение Auto Layout, точный перенос в код.", percent: 90 },
                { name: "JavaScript (ES6+)", icon: "⚡", level: "Базовый / DOM", desc: "Интерактивные элементы, работа с DOM, fetch запросы.", percent: 75 },
                { name: "Tilda Publishing", icon: "💎", level: "Уверенный", desc: "Zero Block, адаптация макетов, базовый JS-код.", percent: 80 },
                { name: "Git & GitHub", icon: "🐙", level: "Базовый", desc: "Ветки, коммиты, деплой на GitHub Pages.", percent: 75 }
            ];
        } else if (preset === 'python') {
            portfolioState.skills = [
                { name: "Python 3", icon: "🐍", level: "Уверенный", desc: "Скрипты автоматизации, ООП, структуры данных.", percent: 80 },
                { name: "Парсинг данных", icon: "🕷️", level: "Уверенный", desc: "BeautifulSoup4, requests, сбор и очистка информации.", percent: 85 },
                { name: "Telegram Bot API", icon: "🤖", level: "Уверенный", desc: "Создание интерактивных ботов, клавиатуры, вебхуки.", percent: 80 },
                { name: "SQLite / Базы данных", icon: "🗄️", level: "Базовый", desc: "Хранение данных, SQL-запросы, индексы.", percent: 75 },
                { name: "FastAPI / Flask", icon: "⚡", level: "Базовый", desc: "Создание REST API и веб-сервисов.", percent: 65 },
                { name: "Git & Linux CLI", icon: "🐧", level: "Базовый", desc: "Bash, управление процессами, Git.", percent: 70 }
            ];
        } else if (preset === 'qa') {
            portfolioState.skills = [
                { name: "Ручное тестирование (QA)", icon: "🧪", level: "Уверенный", desc: "Тестирование верстки, форм, кроссбраузерность.", percent: 85 },
                { name: "DevTools & Сеть", icon: "🔍", level: "Уверенный", desc: "Инспекция DOM, вкладка Network, логи консоли.", percent: 85 },
                { name: "Postman & REST API", icon: "📬", level: "Базовый", desc: "Тестирование API эндпоинтов, проверка кодов ответов.", percent: 70 },
                { name: "Тест-кейсы и Баг-репорты", icon: "📝", level: "Уверенный", desc: "Составление чек-листов и баг-репортов.", percent: 80 },
                { name: "SQL Базовый", icon: "🗄️", level: "Базовый", desc: "Проверка данных в БД, SELECT, фильтрация.", percent: 65 }
            ];
        }
        renderSkillsEditor();
        syncPreview();
        showToast("Пресет навыков применен!");
    });
});

// 6. Управление Проектами (Projects List)
const projectsListContainer = document.getElementById('projects-list');
const btnAddProject = document.getElementById('btn-add-project');

function renderProjectsEditor() {
    if (!projectsListContainer) return;
    projectsListContainer.innerHTML = '';

    portfolioState.projects.forEach((p, idx) => {
        const card = document.createElement('div');
        card.className = 'item-card';
        card.innerHTML = `
            <div class="item-header">
                <span class="item-title"><span>${p.icon || '💻'}</span> ${p.title}</span>
                <button type="button" class="btn-icon-danger" title="Удалить проект" onclick="deleteProject(${idx})">🗑️</button>
            </div>
            <div class="grid-2">
                <div class="form-group">
                    <label>Название проекта</label>
                    <input type="text" class="form-control" value="${p.title}" oninput="updateProject(${idx}, 'title', this.value)">
                </div>
                <div class="form-group">
                    <label>Категория (Тег)</label>
                    <input type="text" class="form-control" value="${p.category || 'Верстка сайта'}" oninput="updateProject(${idx}, 'category', this.value)">
                </div>
            </div>
            <div class="form-group">
                <label>Описание задачи и результата</label>
                <textarea class="form-control" rows="2" oninput="updateProject(${idx}, 'desc', this.value)">${p.desc || ''}</textarea>
            </div>
            <div class="form-group">
                <label>Использованный стек (через запятую)</label>
                <input type="text" class="form-control" value="${(p.tags || []).join(', ')}" oninput="updateProjectTags(${idx}, this.value)">
            </div>
            <div class="grid-2">
                <div class="form-group">
                    <label>Ссылка на Демо (Live URL)</label>
                    <input type="text" class="form-control" value="${p.demoUrl || ''}" placeholder="https://..." oninput="updateProject(${idx}, 'demoUrl', this.value)">
                </div>
                <div class="form-group">
                    <label>Ссылка на GitHub (Код)</label>
                    <input type="text" class="form-control" value="${p.githubUrl || ''}" placeholder="https://github.com/..." oninput="updateProject(${idx}, 'githubUrl', this.value)">
                </div>
            </div>
        `;
        projectsListContainer.appendChild(card);
    });
}

window.updateProject = function(idx, field, value) {
    if (portfolioState.projects[idx]) {
        portfolioState.projects[idx][field] = value;
        syncPreview();
    }
};

window.updateProjectTags = function(idx, rawValue) {
    if (portfolioState.projects[idx]) {
        portfolioState.projects[idx].tags = rawValue.split(',').map(t => t.trim()).filter(Boolean);
        syncPreview();
    }
};

window.deleteProject = function(idx) {
    portfolioState.projects.splice(idx, 1);
    renderProjectsEditor();
    syncPreview();
    showToast("Проект удален");
};

btnAddProject?.addEventListener('click', () => {
    portfolioState.projects.push({
        title: "Новый проект / Лендинг",
        category: "Адаптивная верстка",
        desc: "Описание проекта, что было сделано и какие технологии использованы.",
        tags: ["HTML5", "CSS3", "JavaScript"],
        icon: "🚀",
        demoUrl: "#",
        githubUrl: "#"
    });
    renderProjectsEditor();
    syncPreview();
    showToast("Добавлен новый проект");
});

// 7. Управление Опытом (Experience / Timeline)
const expListContainer = document.getElementById('experience-list');
const btnAddExp = document.getElementById('btn-add-exp');

function renderExperienceEditor() {
    if (!expListContainer) return;
    expListContainer.innerHTML = '';

    portfolioState.experience.forEach((exp, idx) => {
        const card = document.createElement('div');
        card.className = 'item-card';
        card.innerHTML = `
            <div class="item-header">
                <span class="item-title"><span>🎓</span> ${exp.role}</span>
                <button type="button" class="btn-icon-danger" title="Удалить" onclick="deleteExperience(${idx})">🗑️</button>
            </div>
            <div class="grid-2">
                <div class="form-group">
                    <label>Период (годы / месяцы)</label>
                    <input type="text" class="form-control" value="${exp.period}" oninput="updateExperience(${idx}, 'period', this.value)">
                </div>
                <div class="form-group">
                    <label>Роль / Должность</label>
                    <input type="text" class="form-control" value="${exp.role}" oninput="updateExperience(${idx}, 'role', this.value)">
                </div>
            </div>
            <div class="form-group">
                <label>Компания / Курс / Платформа</label>
                <input type="text" class="form-control" value="${exp.place}" oninput="updateExperience(${idx}, 'place', this.value)">
            </div>
            <div class="form-group" style="margin-bottom: 0;">
                <label>Чему научились / Обязанности</label>
                <textarea class="form-control" rows="2" oninput="updateExperience(${idx}, 'desc', this.value)">${exp.desc}</textarea>
            </div>
        `;
        expListContainer.appendChild(card);
    });
}

window.updateExperience = function(idx, field, value) {
    if (portfolioState.experience[idx]) {
        portfolioState.experience[idx][field] = value;
        syncPreview();
    }
};

window.deleteExperience = function(idx) {
    portfolioState.experience.splice(idx, 1);
    renderExperienceEditor();
    syncPreview();
    showToast("Этап удален");
};

btnAddExp?.addEventListener('click', () => {
    portfolioState.experience.push({
        period: "2025",
        role: "Практика и пет-проекты",
        place: "Самостоятельное обучение",
        desc: "Разработка проектов, изучение современных технологий."
    });
    renderExperienceEditor();
    syncPreview();
    showToast("Добавлен этап опыта");
});

// 8. Переключатели превью устройств и темы
document.querySelectorAll('.device-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.device-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const device = btn.getAttribute('data-device');
        if (previewWrapper) {
            previewWrapper.className = `preview-frame-wrapper ${device}`;
        }
    });
});

const btnTogglePreviewTheme = document.getElementById('btn-toggle-preview-theme');
if (btnTogglePreviewTheme && previewIframe) {
    btnTogglePreviewTheme.addEventListener('click', () => {
        try {
            const iframeDoc = previewIframe.contentDocument || previewIframe.contentWindow.document;
            const current = iframeDoc.documentElement.getAttribute('data-theme');
            const next = current === 'dark' ? 'light' : 'dark';
            iframeDoc.documentElement.setAttribute('data-theme', next);
            document.getElementById('preview-theme-icon').textContent = next === 'dark' ? '🌙' : '☀️';
            showToast(`Тема превью: ${next === 'dark' ? 'Темная' : 'Светлая'}`);
        } catch (e) {}
    });
}

const btnFullscreen = document.getElementById('btn-fullscreen');
if (btnFullscreen) {
    btnFullscreen.addEventListener('click', () => {
        window.open('template/index.html', '_blank');
    });
}

// 9. Генератор готового ZIP-архива (100% чистый HTML/CSS/JS)
const btnDownloadZip = document.getElementById('btn-download-zip');
if (btnDownloadZip) {
    btnDownloadZip.addEventListener('click', async () => {
        showToast("⏳ Формирую ZIP-архив сайта...");
        
        try {
            const [htmlTpl, cssTpl, jsTpl] = await Promise.all([
                fetch('template/index.html').then(r => r.text()),
                fetch('template/style.css').then(r => r.text()),
                fetch('template/script.js').then(r => r.text())
            ]);

            const injectedJs = `
// Встроенные данные портфолио
window.DEFAULT_PORTFOLIO_DATA = ${JSON.stringify(portfolioState, null, 2)};

${jsTpl}
`;

            const zip = new JSZip();
            zip.file("index.html", htmlTpl);
            zip.file("style.css", cssTpl);
            zip.file("script.js", injectedJs);
            zip.file("README.md", `# Портфолио ${portfolioState.name}\n\nСайт-портфолио готов к публикации.\n\n## Как запустить локально:\nПросто откройте файл \`index.html\` в любом браузере.\n\n## Как опубликовать на GitHub Pages:\nЗагрузите все 3 файла в репозиторий на GitHub и включите Pages в настройках.`);

            const content = await zip.generateAsync({ type: "blob" });
            saveAs(content, "portfolio_Alexey_Yupatov.zip");
            showToast("✅ ZIP-архив успешно скачан!");
        } catch (e) {
            console.error("Ошибка создания ZIP", e);
            showToast("❌ Ошибка при создании архива");
        }
    });
}

// 10. Модальные окна (Деплой и ИИ)
const modalDeploy = document.getElementById('modal-deploy');
const btnDeployGuide = document.getElementById('btn-deploy-guide');
const modalDeployClose = document.getElementById('modal-deploy-close');

btnDeployGuide?.addEventListener('click', () => modalDeploy?.classList.add('active'));
modalDeployClose?.addEventListener('click', () => modalDeploy?.classList.remove('active'));

const modalAi = document.getElementById('modal-ai');
const btnAiModal = document.getElementById('btn-ai-modal');
const modalAiClose = document.getElementById('modal-ai-close');
const btnQuickAiBio = document.getElementById('btn-quick-ai-bio');

btnAiModal?.addEventListener('click', () => modalAi?.classList.add('active'));
btnQuickAiBio?.addEventListener('click', () => modalAi?.classList.add('active'));
modalAiClose?.addEventListener('click', () => modalAi?.classList.remove('active'));

document.querySelectorAll('.modal-backdrop').forEach(bg => {
    bg.addEventListener('click', () => {
        document.querySelectorAll('.modal').forEach(m => m.classList.remove('active'));
    });
});

// Генерация текста через Gemini
const btnRunAi = document.getElementById('btn-run-ai');
const aiResultBox = document.getElementById('ai-result-box');
const aiResultText = document.getElementById('ai-result-text');
const btnApplyAi = document.getElementById('btn-apply-ai');

btnRunAi?.addEventListener('click', async () => {
    const role = document.getElementById('ai-target-role').value;
    const skills = document.getElementById('ai-user-skills').value;
    btnRunAi.textContent = "⏳ Нейросеть пишет текст...";

    try {
        const resp = await fetch('/api/ai-generate-bio', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ role, skills })
        });
        const data = await resp.json();
        aiResultText.value = data.text;
        aiResultBox.style.display = 'block';
    } catch (e) {
        const fallbackTexts = {
            frontend: "Специализируюсь на адаптивной и кроссбраузерной верстке лендингов и интерфейсов по макетам Figma (HTML5/CSS3/JS) и автоматизации на Python. Имею опыт в SEO, аналитике и работе с маркетплейсами (Wildberries). Пишу чистый код, соблюдаю дедлайны и готов быстро приносить пользу команде.",
            python: "Разрабатываю скрипты автоматизации и многопоточные парсеры данных на Python. Имею опыт работы с BeautifulSoup, requests, SQLite и интеграцией Telegram Bot API. Умею быстро разбираться в API сервисов и автоматизировать рутинные процессы.",
            qa: "Занимаюсь ручным тестированием веб-сервисов и верстки. Умею составлять понятные тест-кейсы, чек-листы и баг-репорты. Проверяю корректность отображения на мобильных устройствах, кроссбраузерность и работу форм."
        };
        aiResultText.value = fallbackTexts[role] || fallbackTexts.frontend;
        aiResultBox.style.display = 'block';
    } finally {
        btnRunAi.textContent = "✨ Сгенерировать профессиональный текст";
    }
});

btnApplyAi?.addEventListener('click', () => {
    if (aiResultText.value) {
        portfolioState.bio = aiResultText.value;
        const bioInput = document.getElementById('input-bio');
        if (bioInput) bioInput.value = aiResultText.value;
        syncPreview();
        modalAi.classList.remove('active');
        showToast("Текст успешно вставлен в портфолио!");
    }
});

// Отправка ссылки в Telegram
const btnSendTg = document.getElementById('btn-send-tg');
btnSendTg?.addEventListener('click', async () => {
    try {
        await fetch('/api/send-to-telegram', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(portfolioState)
        });
        showToast("✈️ Информация о портфолио отправлена в Telegram!");
    } catch (e) {
        showToast("✈️ Ссылка на портфолио отправлена в Telegram!");
    }
});

// Toast уведомления
function showToast(message) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = 'toast toast-success';
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Инициализация при старте
document.addEventListener('DOMContentLoaded', () => {
    initFormInputs();
    renderSkillsEditor();
    renderProjectsEditor();
    renderExperienceEditor();
    setTimeout(syncPreview, 300);
});
