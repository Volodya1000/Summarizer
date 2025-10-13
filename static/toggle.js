// static/toggle.js
// Более надёжный переключатель для сворачиваемых блоков.

function toggle(id, button) {
    const el = document.getElementById(id);
    if (!el) {
        console.error('Элемент с ID ' + id + ' не найден.');
        return;
    }

    // Берём реальное вычисленное значение max-height
    const computedMax = window.getComputedStyle(el).maxHeight;

    // Если элемент видим (maxHeight отличен от 0px и НЕ равен 'none'), свернуть
    if (computedMax && computedMax !== '0px' && computedMax !== 'none') {
        // Свернуть
        el.style.maxHeight = '0px';
        el.classList.remove('is-open');
        if (button) button.textContent = 'Показать';
    } else {
        // Раскрыть: устанавливаем в точную высоту содержимого (scrollHeight)
        // Добавляем небольшой запас +10px чтобы учесть вертикальные отступы
        el.style.maxHeight = (el.scrollHeight + 10) + 'px';
        el.classList.add('is-open');
        if (button) button.textContent = 'Свернуть';

        // Подстраховка: если окно изменит размер, пересчитаем высоту
        const onResize = () => {
            if (el.classList.contains('is-open')) {
                el.style.maxHeight = (el.scrollHeight + 10) + 'px';
            }
        };
        // Используем одноразовый слушатель на resize (удаляем через 300ms после последнего изменения)
        let resizeTimer;
        const resizeHandler = () => {
            clearTimeout(resizeTimer);
            onResize();
            resizeTimer = setTimeout(() => {
                window.removeEventListener('resize', resizeHandler);
            }, 300);
        };
        window.addEventListener('resize', resizeHandler);
    }
}
