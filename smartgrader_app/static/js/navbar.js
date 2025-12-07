document.addEventListener('DOMContentLoaded', function () {
        const navbar = document.querySelector('.navbar');
        const toggle = navbar?.querySelector('.nav-toggle');
        const menu = navbar?.querySelector('.menu');

        if (!navbar || !toggle || !menu) return;

        const closeMenu = () => {
            navbar.classList.remove('menu-open');
            toggle.setAttribute('aria-expanded', 'false');
        };

        toggle.addEventListener('click', function (event) {
            event.stopPropagation();
            const isOpen = navbar.classList.toggle('menu-open');
            toggle.setAttribute('aria-expanded', String(isOpen));
        });

        document.addEventListener('click', function (event) {
            const target = event.target;
            if (!navbar.contains(target)) {
                closeMenu();
            }
        });

        menu.querySelectorAll('a').forEach(function (link) {
            link.addEventListener('click', closeMenu);
        });

        document.addEventListener('keydown', function (event) {
            if (event.key === 'Escape') {
                closeMenu();
            }
        });
    });