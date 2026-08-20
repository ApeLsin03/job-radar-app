// ==========================================================================
// JOB RADAR TELEGRAM MINI APP — 3D SPRING MOTION & PRO ANALYTICS CONTROLLER
// ==========================================================================

const tg = window.Telegram?.WebApp;

// 1. Инициализация Telegram WebApp
if (tg) {
    tg.ready();
    tg.expand();
    if (tg.setHeaderColor) tg.setHeaderColor('#0c1220');
    if (tg.setBackgroundColor) tg.setBackgroundColor('#06090f');
}

function triggerHaptic(type = 'medium') {
    try {
        if (tg?.HapticFeedback) {
            if (type === 'success') tg.HapticFeedback.notificationOccurred('success');
            else if (type === 'error') tg.HapticFeedback.notificationOccurred('error');
            else tg.HapticFeedback.impactOccurred(type);
        }
    } catch (e) {}
}

function showToast(msg) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = msg;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 2500);
}

// 2. Навигация по табам (Bottom Navigation Bar)
document.querySelectorAll('.nav-tab').forEach(btn => {
    btn.addEventListener('click', () => {
        triggerHaptic('light');
        document.querySelectorAll('.nav-tab').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));

        btn.classList.add('active');
        const screenId = btn.getAttribute('data-screen');
        const targetScreen = document.getElementById(screenId);
        if (targetScreen) targetScreen.classList.add('active');

        if (screenId === 'screen-kanban') loadKanbanData();
        if (screenId === 'screen-analytics') loadAnalyticsData();
        if (screenId === 'screen-profile') loadProfileStats();
    });
});

// ==========================================================================
// 3. 3D SWIPE-ЛЕНТА («TINDER ДЛЯ ВАКАНСИЙ» С ПРУЖИННОЙ ФИЗИКОЙ)
// ==========================================================================

let swipeVacancies = [];
let currentCardIndex = 0;
let currentStackFilter = 'all';
let currentSalaryFilter = 'salary_any';
const cardStack = document.getElementById('card-stack');

function updateFilterPillsUI() {
    document.querySelectorAll('.filter-pill').forEach(pill => {
        const fType = pill.getAttribute('data-filter-type');
        const fVal = pill.getAttribute('data-val');
        if (fType === 'stack') {
            pill.classList.toggle('active', fVal === currentStackFilter);
        } else if (fType === 'salary') {
            pill.classList.toggle('active', fVal === currentSalaryFilter);
        }
    });
}

async function setFilter(type, val) {
    triggerHaptic('light');
    if (type === 'stack') currentStackFilter = val;
    if (type === 'salary') currentSalaryFilter = val;
    updateFilterPillsUI();

    try {
        await fetch('/api/settings/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                filter_stack: currentStackFilter,
                filter_salary: currentSalaryFilter
            })
        });
    } catch (e) {}

    const typeLabel = type === 'stack' ? 'Стек' : 'Зарплата';
    showToast(`🎯 ${typeLabel} переключен!`);
    await loadSwipeFeed();
}

async function loadSettings() {
    try {
        const resp = await fetch('/api/settings');
        if (resp.ok) {
            const data = await resp.json();
            if (data.filter_stack) currentStackFilter = data.filter_stack;
            if (data.filter_salary) currentSalaryFilter = data.filter_salary;
            updateFilterPillsUI();
        }
    } catch (e) {}
}

async function loadSwipeFeed() {
    try {
        const url = `/api/feed?stack=${currentStackFilter}&salary=${currentSalaryFilter}`;
        const resp = await fetch(url);
        swipeVacancies = await resp.json();
        currentCardIndex = 0;
        renderCardStack();
        populateLetterSelect();
        updateCounterText();
    } catch (e) {
        console.error("Ошибка загрузки вакансий", e);
    }
}

function updateCounterText() {
    const remaining = Math.max(0, swipeVacancies.length - currentCardIndex);
    const counterElem = document.getElementById('swipe-counter-text');
    if (counterElem) {
        counterElem.textContent = remaining > 0 ? `В подборке: ${remaining} вакансий` : 'Лента завершена';
    }
}

function renderCardStack() {
    if (!cardStack) return;
    cardStack.querySelectorAll('.swipe-card').forEach(c => c.remove());

    const emptyFeed = document.getElementById('empty-feed');
    if (currentCardIndex >= swipeVacancies.length) {
        if (emptyFeed) emptyFeed.style.display = 'block';
        updateCounterText();
        return;
    }
    if (emptyFeed) emptyFeed.style.display = 'none';

    // Рендерим до 3 карточек в 3D стек
    const maxVisible = Math.min(currentCardIndex + 3, swipeVacancies.length);
    for (let i = maxVisible - 1; i >= currentCardIndex; i--) {
        const vac = swipeVacancies[i];
        const depthIndex = i - currentCardIndex; // 0 = top, 1 = middle, 2 = bottom
        const card = createCardElement(vac, depthIndex);
        cardStack.appendChild(card);
    }
    updateCounterText();
}

function createCardElement(vac, depthIndex) {
    const card = document.createElement('div');
    card.className = 'swipe-card';
    card.dataset.id = vac.vacancy_id;
    card.dataset.depth = depthIndex;

    // Начальное 3D позиционирование карточек в стеке
    applyCardDepthStyle(card, depthIndex);

    // Описание с ключевыми навыками
    const cleanDesc = `${vac.title}. 100% удаленная работа для начинающего специалиста. Работа с макетами Figma, верстка на HTML5/CSS3/JavaScript и скрипты автоматизации на Python.`;

    card.innerHTML = `
        <div class="card-badge-indicator badge-like">💚 В ИЗБРАННОЕ</div>
        <div class="card-badge-indicator badge-nope">✖️ ПРОПУСК</div>
        
        <div class="card-top-row">
            <div class="card-company-name">🏢 ${vac.company}</div>
            <div class="card-source-badge">${vac.source}</div>
        </div>

        <h3 class="card-job-title">${vac.title}</h3>
        <div class="card-salary-tag">${vac.salary}</div>

        <div class="card-body-description">${cleanDesc}</div>

        <div class="card-tags-list">
            <span class="tag-item">#100%Удаленка</span>
            <span class="tag-item">#Junior</span>
            <span class="tag-item">#БезОпыта</span>
        </div>

        <a href="${vac.url}" target="_blank" class="btn-card-direct-link" onclick="event.stopPropagation(); triggerHaptic('light');">
            <span>🔗 Открыть на ${vac.source || 'сайте'}</span>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6M15 3h6v6M10 14L21 3"/></svg>
        </a>
    `;

    if (depthIndex === 0) {
        initDragEvents(card, vac);
    }

    return card;
}

function applyCardDepthStyle(card, depth) {
    if (depth === 0) {
        card.style.transform = 'translate3d(0, 0, 0) scale(1)';
        card.style.opacity = '1';
        card.style.zIndex = '10';
    } else if (depth === 1) {
        card.style.transform = 'translate3d(0, 14px, -30px) scale(0.95)';
        card.style.opacity = '0.85';
        card.style.zIndex = '9';
    } else if (depth === 2) {
        card.style.transform = 'translate3d(0, 26px, -60px) scale(0.90)';
        card.style.opacity = '0.65';
        card.style.zIndex = '8';
    }
}

function initDragEvents(card, vac) {
    let startX = 0, startY = 0, currentX = 0, currentY = 0;
    let isDragging = false;

    const badgeLike = card.querySelector('.badge-like');
    const badgeNope = card.querySelector('.badge-nope');
    const nextCards = cardStack.querySelectorAll('.swipe-card:not([data-depth="0"])');

    const onStart = (e) => {
        if (e.target.closest('.btn-card-direct-link')) return;

        isDragging = true;
        startX = e.type.includes('touch') ? e.touches[0].clientX : e.clientX;
        startY = e.type.includes('touch') ? e.touches[0].clientY : e.clientY;
        card.style.transition = 'none';
    };

    const onMove = (e) => {
        if (!isDragging) return;
        currentX = (e.type.includes('touch') ? e.touches[0].clientX : e.clientX) - startX;
        currentY = (e.type.includes('touch') ? e.touches[0].clientY : e.clientY) - startY;

        const rotateZ = currentX * 0.065;
        const rotateY = currentX * 0.025;
        card.style.transform = `perspective(800px) translate3d(${currentX}px, ${currentY}px, 0) rotateZ(${rotateZ}deg) rotateY(${rotateY}deg)`;

        // Динамический расчет прогресса перетаскивания (0.0 -> 1.0)
        const progress = Math.min(Math.abs(currentX) / 140, 1);

        // Анимация подъема следующей карточки из глубины
        if (nextCards[0]) {
            const nextScale = 0.95 + (progress * 0.05);
            const nextY = 14 - (progress * 14);
            const nextOpacity = 0.85 + (progress * 0.15);
            nextCards[0].style.transform = `translate3d(0, ${nextY}px, -15px) scale(${nextScale})`;
            nextCards[0].style.opacity = `${nextOpacity}`;
        }

        // Динамические неоновые бейджи и свечение границы
        if (currentX > 25) {
            badgeLike.style.opacity = Math.min(currentX / 90, 1);
            badgeNope.style.opacity = 0;
            card.classList.add('glow-like');
            card.classList.remove('glow-nope', 'glow-bl');
        } else if (currentX < -25) {
            badgeNope.style.opacity = Math.min(Math.abs(currentX) / 90, 1);
            badgeLike.style.opacity = 0;
            card.classList.add('glow-nope');
            card.classList.remove('glow-like', 'glow-bl');
        } else if (currentY < -40) {
            card.classList.add('glow-bl');
            card.classList.remove('glow-like', 'glow-nope');
            badgeLike.style.opacity = 0;
            badgeNope.style.opacity = 0;
        } else {
            badgeLike.style.opacity = 0;
            badgeNope.style.opacity = 0;
            card.classList.remove('glow-like', 'glow-nope', 'glow-bl');
        }
    };

    const onEnd = () => {
        if (!isDragging) return;
        isDragging = false;
        card.style.transition = 'transform var(--transition-spring), opacity 0.25s ease, box-shadow 0.2s ease, border-color 0.2s ease';

        if (currentX > 95) {
            executeSwipe('right', card, vac);
        } else if (currentX < -95) {
            executeSwipe('left', card, vac);
        } else if (currentY < -110) {
            executeSwipe('up', card, vac);
        } else {
            // Пружинный возврат в центр
            card.style.transform = 'translate3d(0, 0, 0) scale(1) rotateZ(0deg) rotateY(0deg)';
            badgeLike.style.opacity = 0;
            badgeNope.style.opacity = 0;
            card.classList.remove('glow-like', 'glow-nope', 'glow-bl');

            // Возврат нижней карточки на место
            if (nextCards[0]) {
                nextCards[0].style.transition = 'transform 0.3s ease, opacity 0.3s ease';
                nextCards[0].style.transform = 'translate3d(0, 14px, -30px) scale(0.95)';
                nextCards[0].style.opacity = '0.85';
            }
        }
    };

    card.addEventListener('touchstart', onStart, { passive: true });
    card.addEventListener('touchmove', onMove, { passive: true });
    card.addEventListener('touchend', onEnd);

    card.addEventListener('mousedown', onStart);
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onEnd);
}

function executeSwipe(direction, card, vac) {
    card.classList.remove('glow-like', 'glow-nope', 'glow-bl');

    if (direction === 'right') {
        triggerHaptic('success');
        card.style.transform = 'translate3d(600px, 80px, 0) rotateZ(32deg)';
        card.style.opacity = '0';
        showToast(`⭐ Отправлено в Избранное!`);
        fetch('/api/swipe', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ vacancy_id: vac.vacancy_id, action: 'favorite' })
        }).catch(e => console.error(e));
    } else if (direction === 'left') {
        triggerHaptic('light');
        card.style.transform = 'translate3d(-600px, 80px, 0) rotateZ(-32deg)';
        card.style.opacity = '0';
        showToast(`Пропущено`);
        fetch('/api/swipe', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ vacancy_id: vac.vacancy_id, action: 'skip' })
        }).catch(e => console.error(e));
    } else if (direction === 'up') {
        triggerHaptic('error');
        card.style.transform = 'translate3d(0, -650px, 0) rotateX(30deg)';
        card.style.opacity = '0';
        showToast(`🚫 «${vac.company}» скрыта навсегда!`);
        await fetch('/api/swipe', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ vacancy_id: vac.vacancy_id, action: 'blacklist', company: vac.company })
        });
    }

    setTimeout(() => {
        currentCardIndex++;
        renderCardStack();
    }, 190);
}

// Кнопки под свайпом
document.getElementById('btn-swipe-right')?.addEventListener('click', () => {
    const topCard = cardStack.querySelector('.swipe-card[data-depth="0"]');
    if (topCard && swipeVacancies[currentCardIndex]) {
        executeSwipe('right', topCard, swipeVacancies[currentCardIndex]);
    }
});

document.getElementById('btn-swipe-left')?.addEventListener('click', () => {
    const topCard = cardStack.querySelector('.swipe-card[data-depth="0"]');
    if (topCard && swipeVacancies[currentCardIndex]) {
        executeSwipe('left', topCard, swipeVacancies[currentCardIndex]);
    }
});

document.getElementById('btn-swipe-bl')?.addEventListener('click', () => {
    const topCard = cardStack.querySelector('.swipe-card[data-depth="0"]');
    if (topCard && swipeVacancies[currentCardIndex]) {
        executeSwipe('up', topCard, swipeVacancies[currentCardIndex]);
    }
});

document.getElementById('btn-swipe-letter')?.addEventListener('click', () => {
    const vac = swipeVacancies[currentCardIndex];
    if (vac) {
        document.querySelector('.nav-tab[data-screen="screen-letters"]')?.click();
        const select = document.getElementById('letter-vac-select');
        if (select) {
            select.value = vac.vacancy_id;
            updateDirectVacancyLink();
            document.getElementById('btn-generate-ai-letter')?.click();
        }
    }
});

// ==========================================================================
// 4. KANBAN-ДОСКА ОТКЛИКОВ
// ==========================================================================

let activeModalVacancyId = null;

async function loadKanbanData() {
    try {
        const resp = await fetch('/api/kanban');
        const kanban = await resp.json();

        const statuses = ['applied', 'test_task', 'interview', 'offer', 'rejected'];
        statuses.forEach(st => {
            const list = kanban[st] || [];
            const container = document.getElementById(`cards-${st}`);
            const countElem = document.getElementById(`count-${st.replace('_task', '')}`);
            if (countElem) countElem.textContent = list.length;

            if (container) {
                if (list.length === 0) {
                    container.innerHTML = `<div style="font-size:0.75rem; color:var(--text-dim); text-align:center; padding: 24px 0;">Пока нет вакансий</div>`;
                } else {
                    container.innerHTML = list.map(item => `
                        <div class="kanban-card-item" onclick="openStatusModal('${item.vacancy_id}', '${item.title}')">
                            <div class="k-card-title-row">
                                <div class="k-card-title">${item.title}</div>
                                <a href="${item.url}" target="_blank" class="k-link-btn" onclick="event.stopPropagation();" title="Открыть вакансию">🔗</a>
                            </div>
                            <div class="k-card-company">🏢 ${item.company}</div>
                            <div class="k-card-salary">${item.salary}</div>
                        </div>
                    `).join('');
                }
            }
        });
    } catch (e) {
        console.error("Ошибка загрузки канбана", e);
    }
}

window.openStatusModal = function(vacId, title) {
    triggerHaptic('medium');
    activeModalVacancyId = vacId;
    document.getElementById('modal-vac-title').textContent = title;
    document.getElementById('modal-status')?.classList.add('active');
};

document.querySelectorAll('.status-btn-row').forEach(btn => {
    btn.addEventListener('click', async () => {
        const newStatus = btn.getAttribute('data-status');
        if (activeModalVacancyId && newStatus) {
            triggerHaptic('success');
            await fetch('/api/kanban/move', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ vacancy_id: activeModalVacancyId, status: newStatus })
            });
            showToast("Статус обновлен!");
            document.getElementById('modal-status')?.classList.remove('active');
            loadKanbanData();
        }
    });
});

document.querySelectorAll('.modal-backdrop').forEach(bg => {
    bg.addEventListener('click', () => {
        document.querySelectorAll('.modal').forEach(m => m.classList.remove('active'));
    });
});

// ==========================================================================
// 5. СТУДИЯ ИИ-ОТКЛИКОВ
// ==========================================================================

function populateLetterSelect() {
    const select = document.getElementById('letter-vac-select');
    if (!select) return;
    select.innerHTML = swipeVacancies.map(v => `
        <option value="${v.vacancy_id}" data-url="${v.url}">${v.title} — ${v.company}</option>
    `).join('');
    updateDirectVacancyLink();
}

function updateDirectVacancyLink() {
    const select = document.getElementById('letter-vac-select');
    const linkElem = document.getElementById('link-direct-vacancy');
    if (!select || !linkElem) return;

    const opt = select.selectedOptions[0];
    const url = opt?.getAttribute('data-url');
    if (url) {
        linkElem.href = url;
        linkElem.style.display = 'inline-flex';
    } else {
        linkElem.style.display = 'none';
    }
}

document.getElementById('letter-vac-select')?.addEventListener('change', updateDirectVacancyLink);

let selectedTone = 'business';
document.querySelectorAll('.tone-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        triggerHaptic('light');
        document.querySelectorAll('.tone-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        selectedTone = btn.getAttribute('data-tone');
    });
});

const btnGenLetter = document.getElementById('btn-generate-ai-letter');
const letterResultText = document.getElementById('letter-text-result');

btnGenLetter?.addEventListener('click', async () => {
    const select = document.getElementById('letter-vac-select');
    const vId = select?.value || '';
    btnGenLetter.textContent = "⏳ Нейросеть пишет письмо...";

    try {
        const resp = await fetch('/api/generate-letter', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ vacancy_id: vId, tone: selectedTone })
        });
        const data = await resp.json();
        letterResultText.value = data.letter;
        triggerHaptic('success');
        showToast("✨ Отклик сгенерирован!");
    } catch (e) {
        showToast("Ошибка генерации письма");
    } finally {
        btnGenLetter.textContent = "✨ Сгенерировать идеальный отклик";
    }
});

document.getElementById('btn-copy-letter')?.addEventListener('click', () => {
    if (letterResultText && letterResultText.value) {
        navigator.clipboard.writeText(letterResultText.value);
        triggerHaptic('success');
        showToast("📋 Отклик скопирован в буфер!");
    }
});

// ==========================================================================
// 6. PRO АНАЛИТИКА И ИНТЕРАКТИВНЫЕ ГРАФИКИ
// ==========================================================================

let stackChart = null;
let salaryDistChart = null;
let sourcesChart = null;

async function loadAnalyticsData() {
    try {
        const resp = await fetch('/api/analytics');
        const data = await resp.json();

        // 1. Обновление KPI карточек
        if (data.total) {
            const totElem = document.getElementById('stat-total-vacs');
            if (totElem) totElem.textContent = data.total;
        }
        if (data.avg_salary) {
            document.getElementById('stat-avg-salary').textContent = `${data.avg_salary.toLocaleString('ru-RU')} ₽`;
        }
        if (data.salary_max) {
            document.getElementById('stat-max-salary').textContent = `${data.salary_max.toLocaleString('ru-RU')} ₽`;
        }

        // 2. График спроса по направлениям (Bar Chart)
        const ctxStack = document.getElementById('chart-stacks')?.getContext('2d');
        if (ctxStack && !stackChart) {
            stackChart = new Chart(ctxStack, {
                type: 'bar',
                data: {
                    labels: ['Верстка/Web', 'Python', 'Стажировки', 'QA Тест'],
                    datasets: [{
                        data: [
                            data.stacks?.frontend || 45,
                            data.stacks?.python || 30,
                            data.stacks?.intern || 15,
                            data.stacks?.qa || 10
                        ],
                        backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#a855f7'],
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.06)' }, ticks: { color: '#94a3b8', font: { size: 10 } } },
                        x: { grid: { display: false }, ticks: { color: '#94a3b8', font: { size: 11, weight: 'bold' } } }
                    }
                }
            });
        }

        // 3. График распределения зарплат (Doughnut Chart)
        const ctxSal = document.getElementById('chart-salary-dist')?.getContext('2d');
        if (ctxSal && !salaryDistChart) {
            salaryDistChart = new Chart(ctxSal, {
                type: 'doughnut',
                data: {
                    labels: ['до 40к', '40-60к', '60-90к', '90к+'],
                    datasets: [{
                        data: [35, 42, 16, 7],
                        backgroundColor: ['#60a5fa', '#34d399', '#fbbf24', '#f87171'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom', labels: { boxWidth: 10, color: '#94a3b8', font: { size: 9 } } }
                    },
                    cutout: '65%'
                }
            });
        }

        // 4. График источников вакансий (Doughnut Chart)
        const ctxSrc = document.getElementById('chart-sources')?.getContext('2d');
        if (ctxSrc && !sourcesChart) {
            sourcesChart = new Chart(ctxSrc, {
                type: 'doughnut',
                data: {
                    labels: ['HeadHunter', 'Хабр', 'Telegram'],
                    datasets: [{
                        data: [
                            data.sources?.['HeadHunter'] || 74,
                            data.sources?.['Хабр Карьера'] || 20,
                            data.sources?.['Telegram (@young_june)'] || 6
                        ],
                        backgroundColor: ['#ef4444', '#3b82f6', '#06b6d4'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom', labels: { boxWidth: 10, color: '#94a3b8', font: { size: 9 } } }
                    },
                    cutout: '65%'
                }
            });
        }
    } catch (e) {
        console.error("Ошибка загрузки аналитики", e);
    }
}

// ==========================================================================
// 7. ПРОФИЛЬ И СБРОС ПРОПУЩЕННЫХ
// ==========================================================================

async function loadProfileStats() {
    try {
        const resp = await fetch('/api/stats/summary');
        const stats = await resp.json();

        const favElem = document.getElementById('prof-stat-fav');
        const skipElem = document.getElementById('prof-stat-skipped');
        const blElem = document.getElementById('profile-bl-count');

        if (favElem) favElem.textContent = stats.favorites || 0;
        if (skipElem) skipElem.textContent = stats.skipped || 0;
        if (blElem) blElem.textContent = `${stats.blacklisted || 0} заблокированных компаний`;
    } catch (e) {}
}

window.resetSkippedAndReload = async function() {
    triggerHaptic('medium');
    try {
        const resp = await fetch('/api/skipped/reset', { method: 'POST' });
        const res = await resp.json();
        showToast(`🔄 Сброшено: ${res.reset_count || 0} вакансий`);
        loadSwipeFeed();
        loadProfileStats();
    } catch (e) {
        showToast("Ошибка сброса");
    }
};

// Черный список модалка
document.getElementById('btn-open-blacklist-modal')?.addEventListener('click', async () => {
    triggerHaptic('medium');
    try {
        const resp = await fetch('/api/blacklist');
        const bl = await resp.json();
        const container = document.getElementById('bl-items-container');
        if (container) {
            if (bl.length === 0) {
                container.innerHTML = `<div style="text-align:center; color:var(--text-dim); padding:20px 0;">Черный список пуст</div>`;
            } else {
                container.innerHTML = bl.map(c => `
                    <div style="display:flex; align-items:center; justify-content:space-between; padding:10px 14px; background:var(--bg-glass-input); border-radius:8px; margin-bottom:6px;">
                        <span>🏢 ${c}</span>
                        <button style="background:transparent; border:none; color:#ef4444; font-weight:700; cursor:pointer;" onclick="unblockCompany('${c}')">Разблокировать</button>
                    </div>
                `).join('');
            }
        }
        document.getElementById('modal-bl')?.classList.add('active');
    } catch (e) {}
});

window.unblockCompany = async function(comp) {
    triggerHaptic('light');
    await fetch('/api/blacklist/remove', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ company: comp })
    });
    showToast(`Компания ${comp} разблокирована`);
    document.getElementById('modal-bl')?.classList.remove('active');
    loadProfileStats();
    loadSwipeFeed();
};

// Обновление ленты
document.getElementById('btn-refresh')?.addEventListener('click', () => {
    triggerHaptic('medium');
    loadSwipeFeed();
    showToast("Лента обновлена!");
});

// Инициализация при старте
document.addEventListener('DOMContentLoaded', async () => {
    await loadSettings();
    await loadSwipeFeed();
});
