/**
 * Adds eye toggle to password fields on auth forms.
 */
(function () {
    function createToggleButton() {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'password-toggle-btn';
        btn.setAttribute('aria-label', 'Show password');
        btn.innerHTML =
            '<i data-lucide="eye" class="icon-show w-4 h-4"></i>' +
            '<i data-lucide="eye-off" class="icon-hide w-4 h-4"></i>';
        return btn;
    }

    function bindToggle(wrap, input, btn) {
        btn.addEventListener('click', () => {
            const visible = input.type === 'text';
            input.type = visible ? 'password' : 'text';
            btn.classList.toggle('is-visible', !visible);
            btn.setAttribute('aria-label', visible ? 'Show password' : 'Hide password');
            input.focus();
        });
    }

    function initPasswordField(input) {
        if (input.dataset.toggleReady === 'true') return;

        let wrap = input.closest('.password-toggle-wrap');
        if (!wrap) {
            wrap = document.createElement('div');
            wrap.className = 'password-toggle-wrap';
            input.parentNode.insertBefore(wrap, input);
            wrap.appendChild(input);
        }

        if (wrap.querySelector('.password-toggle-btn')) {
            input.dataset.toggleReady = 'true';
            return;
        }

        const btn = createToggleButton();
        wrap.appendChild(btn);
        bindToggle(wrap, input, btn);
        input.dataset.toggleReady = 'true';
    }

    function initAll() {
        document.querySelectorAll('input[type="password"]').forEach(initPasswordField);
        if (window.lucide) lucide.createIcons();
    }

    document.addEventListener('DOMContentLoaded', initAll);
})();
