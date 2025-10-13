function toggleOriginal() {
    const el = document.querySelector('.original');
    el.classList.toggle('is-open');
    if (el.classList.contains('is-open')) {
        el.style.maxHeight = el.scrollHeight + "px";
    } else {
        el.style.maxHeight = "400px"; // исходная высота
    }
}

// Функция для вкладок (уже есть)
function showTab(tabId, button) {
    document.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));
    document.querySelectorAll('.tab-buttons button').forEach(btn => btn.classList.remove('active'));
    document.getElementById(tabId).classList.add('active');
    button.classList.add('active');
}
