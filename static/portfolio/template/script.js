// ==========================================================================
// PORTFOLIO CLIENT SCRIPT (DARK/LIGHT THEME, RENDERING & INTERACTION)
// ==========================================================================

// 1. Управление темой (Dark / Light)
const themeToggle = document.getElementById('theme-toggle');
const htmlElement = document.documentElement;

// Проверяем сохраненную тему
const savedTheme = localStorage.getItem('portfolio-theme') || 'dark';
htmlElement.setAttribute('data-theme', savedTheme);

if (themeToggle) {
    themeToggle.addEventListener('click', () => {
        const currentTheme = htmlElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        htmlElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('portfolio-theme', newTheme);
    });
}

// 2. Мобильное меню
const mobileToggle = document.getElementById('mobile-toggle');
const navMenu = document.getElementById('nav-menu');

if (mobileToggle && navMenu) {
    mobileToggle.addEventListener('click', () => {
        navMenu.classList.toggle('active');
    });

    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', () => {
            navMenu.classList.remove('active');
        });
    });
}

// 3. Актуальный год в футере
const yearElem = document.getElementById('current-year');
if (yearElem) {
    yearElem.textContent = new Date().getFullYear();
}

// 4. Глобальная функция рендера данных портфолио
window.renderPortfolio = function(data) {
    if (!data) return;

    // Шапка и Hero
    if (data.name) {
        document.title = `${data.name} — Портфолио`;
        const navName = document.getElementById('nav-name');
        if (navName) navName.textContent = data.name;
        const heroName = document.getElementById('hero-name');
        if (heroName) heroName.textContent = data.name;
    }

    if (data.role) {
        const heroRole = document.getElementById('hero-role');
        if (heroRole) heroRole.textContent = data.role;
    }

    if (data.status) {
        const statusText = document.getElementById('hero-status-text');
        if (statusText) statusText.textContent = data.status;
    }

    if (data.bio) {
        const heroBio = document.getElementById('hero-bio');
        if (heroBio) heroBio.textContent = data.bio;
    }

    if (data.resumeUrl) {
        const resumeBtn = document.getElementById('hero-resume-btn');
        if (resumeBtn) {
            resumeBtn.href = data.resumeUrl;
            resumeBtn.style.display = 'inline-flex';
        }
    } else {
        const resumeBtn = document.getElementById('hero-resume-btn');
        if (resumeBtn) resumeBtn.style.display = 'none';
    }

    // Социальные сети в Hero
    const socialsContainer = document.getElementById('hero-socials');
    if (socialsContainer && data.socials) {
        socialsContainer.innerHTML = '';
        if (data.socials.telegram) {
            socialsContainer.innerHTML += `<a href="https://t.me/${data.socials.telegram.replace('@', '')}" target="_blank" class="social-link" title="Telegram">✈️</a>`;
        }
        if (data.socials.email) {
            socialsContainer.innerHTML += `<a href="mailto:${data.socials.email}" class="social-link" title="Email">✉️</a>`;
        }
        if (data.socials.whatsapp) {
            socialsContainer.innerHTML += `<a href="https://wa.me/${data.socials.whatsapp.replace(/[^0-9]/g, '')}" target="_blank" class="social-link" title="WhatsApp / Телефон">💬</a>`;
        }
        if (data.socials.github) {
            const gh = data.socials.github.startsWith('http') ? data.socials.github : `https://github.com/${data.socials.github}`;
            socialsContainer.innerHTML += `<a href="${gh}" target="_blank" class="social-link" title="GitHub">🐙</a>`;
        }
    }

    // Навыки (Skills)
    const skillsGrid = document.getElementById('skills-grid');
    if (skillsGrid && data.skills && data.skills.length > 0) {
        skillsGrid.innerHTML = data.skills.map(sk => `
            <div class="skill-card">
                <div class="skill-header">
                    <div class="skill-icon-box">${sk.icon || '⚡'}</div>
                    <div>
                        <div class="skill-name">${sk.name}</div>
                        <div class="skill-level-tag">${sk.level || 'Практика'}</div>
                    </div>
                </div>
                <div class="skill-desc">${sk.desc || ''}</div>
                <div class="skill-bar-container">
                    <div class="skill-bar-fill" style="width: ${sk.percent || 85}%"></div>
                </div>
            </div>
        `).join('');
    }

    // Проекты (Projects)
    const projectsGrid = document.getElementById('projects-grid');
    if (projectsGrid && data.projects && data.projects.length > 0) {
        projectsGrid.innerHTML = data.projects.map(p => `
            <div class="project-card">
                <div class="project-preview">
                    ${p.image ? `<img src="${p.image}" alt="${p.title}" class="project-preview-img">` : `<div class="project-preview-icon">${p.icon || '🚀'}</div>`}
                </div>
                <div class="project-body">
                    <div class="project-tag">${p.category || 'Веб-разработка'}</div>
                    <h3 class="project-title">${p.title}</h3>
                    <p class="project-desc">${p.desc || ''}</p>
                    <div class="project-tags">
                        ${(p.tags || []).map(t => `<span class="tech-badge">${t}</span>`).join('')}
                    </div>
                    <div class="project-links">
                        ${p.demoUrl ? `<a href="${p.demoUrl}" target="_blank" class="btn btn-primary btn-sm">🌐 Демо</a>` : ''}
                        ${p.githubUrl ? `<a href="${p.githubUrl}" target="_blank" class="btn btn-secondary btn-sm">💻 Код</a>` : ''}
                        ${p.figmaUrl ? `<a href="${p.figmaUrl}" target="_blank" class="btn btn-secondary btn-sm">🎨 Figma</a>` : ''}
                    </div>
                </div>
            </div>
        `).join('');
    }

    // Опыт и обучение (Timeline)
    const timeline = document.getElementById('experience-timeline');
    if (timeline && data.experience && data.experience.length > 0) {
        timeline.innerHTML = data.experience.map(exp => `
            <div class="timeline-item">
                <div class="timeline-dot"></div>
                <div class="timeline-card">
                    <div class="timeline-period">${exp.period}</div>
                    <div class="timeline-role">${exp.role}</div>
                    <div class="timeline-place">${exp.place}</div>
                    <div class="timeline-text">${exp.desc}</div>
                </div>
            </div>
        `).join('');
    }

    // Контакты
    const contactGrid = document.getElementById('contact-grid');
    if (contactGrid && data.socials) {
        contactGrid.innerHTML = '';
        if (data.socials.telegram) {
            contactGrid.innerHTML += `
                <a href="https://t.me/${data.socials.telegram.replace('@', '')}" target="_blank" class="contact-method">
                    <span>✈️</span>
                    <span>Telegram: ${data.socials.telegram}</span>
                </a>
            `;
        }
        if (data.socials.email) {
            contactGrid.innerHTML += `
                <a href="mailto:${data.socials.email}" class="contact-method">
                    <span>✉️</span>
                    <span>${data.socials.email}</span>
                </a>
            `;
        }
        if (data.socials.whatsapp) {
            contactGrid.innerHTML += `
                <a href="https://wa.me/${data.socials.whatsapp.replace(/[^0-9]/g, '')}" target="_blank" class="contact-method">
                    <span>💬</span>
                    <span>Тел: ${data.socials.whatsapp}</span>
                </a>
            `;
        }
    }
};

// Дефолтные данные Алексея Юпатова
window.DEFAULT_PORTFOLIO_DATA = {
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
            githubUrl: "https://github.com"
        },
        {
            title: "Job Radar — Telegram-бот и парсер вакансий на Python",
            category: "Python & Автоматизация",
            desc: "Многопоточный парсер удаленных вакансий без опыта с HeadHunter, Хабра и Telegram, фильтрацией по зарплате и генерацией Excel-отчетов.",
            tags: ["Python", "Telegram API", "SQLite", "OpenPyXL", "AI Gemini"],
            icon: "🤖",
            demoUrl: "https://t.me/JobRadar111_bot",
            githubUrl: "https://github.com"
        },
        {
            title: "Portfolio & CV Builder — Веб-конструктор портфолио",
            category: "Веб-приложение",
            desc: "Интерактивный конструктор сайта-портфолио с живым Split-Screen превью, переключением тем и экспортом в чистый ZIP.",
            tags: ["HTML5", "Vanilla CSS", "JavaScript", "Python API"],
            icon: "🎨",
            demoUrl: "http://localhost:5174",
            githubUrl: "https://github.com"
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

// Первичная инициализация при открытии шаблона
if (typeof window !== 'undefined') {
    document.addEventListener('DOMContentLoaded', () => {
        window.renderPortfolio(window.DEFAULT_PORTFOLIO_DATA);
    });
}
