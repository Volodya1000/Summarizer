function toggle(id) {
    const el = document.getElementById(id);
    if (!el) return;

    el.classList.toggle('show');
}
