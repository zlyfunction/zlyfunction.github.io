/**
 * Particle network background animation
 * Tuned to match the site's color scheme and aesthetic.
 * Light theme: a subtle, airy blue-slate particle network.
 * Dark theme:  soft, twinkling star field with faint constellation lines.
 */
(function () {
    const reducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)');
    if (reducedMotion && reducedMotion.matches) return;

    const isMobile = (window.innerWidth || 800) < 640;
    const CONFIG = {
        count: isMobile ? 32 : 52, // fewer particles on small screens
        speed: 0.38,               // gentle drift speed per axis
        colorLight: '42,95,158',   // subtle slate-blue
        colorDark: '200,220,255',  // soft starlight (blue-white)
        opacityLight: 0.22,        // airy & crisp in light mode
        opacityDark: 0.85,         // readable stars on dark background
        linkDist: 5200,            // max squared distance to draw a line between particles
        mouseDist: 16000,          // squared distance for mouse interaction
        mouseRepel: 0.022,         // strength of mouse repulsion
        zIndex: -1,
    };

    function isDark() {
        return document.documentElement.getAttribute('data-theme') === 'dark';
    }

    // Canvas setup
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    canvas.setAttribute('aria-hidden', 'true');
    canvas.style.cssText = [
        'position:fixed',
        'top:0',
        'left:0',
        `z-index:${CONFIG.zIndex}`,
        `opacity:${isDark() ? CONFIG.opacityDark : CONFIG.opacityLight}`,
        'pointer-events:none',
        'transition:opacity 0.3s ease',
    ].join(';');
    document.body.appendChild(canvas);

    let W, H;
    function resize() {
        W = canvas.width = window.innerWidth || document.documentElement.clientWidth;
        H = canvas.height = window.innerHeight || document.documentElement.clientHeight;
    }
    resize();
    window.addEventListener('resize', resize, { passive: true });

    // Keep the canvas opacity in sync with the active theme
    let lastDark = null;
    function syncOpacity(dark) {
        if (dark === lastDark) return;
        canvas.style.opacity = dark ? CONFIG.opacityDark : CONFIG.opacityLight;
        lastDark = dark;
    }

    // Mouse
    const mouse = { x: null, y: null, max: CONFIG.mouseDist };

    window.addEventListener('mousemove', e => {
        mouse.x = e.clientX;
        mouse.y = e.clientY;
    }, { passive: true });
    window.addEventListener('mouseout', () => {
        mouse.x = null;
        mouse.y = null;
    }, { passive: true });

    // Particles
    function randSpeed() {
        const v = (Math.random() * 2 - 1) * CONFIG.speed;
        return v === 0 ? CONFIG.speed * 0.3 : v;
    }

    const particles = Array.from({ length: CONFIG.count }, () => ({
        x: Math.random() * W,
        y: Math.random() * H,
        vx: randSpeed(),
        vy: randSpeed(),
        max: CONFIG.linkDist,
        r: 0.85 + Math.random() * 1.5,           // star radius (dark mode)
        tw: Math.random() * Math.PI * 2,         // twinkle phase
        twSpeed: 0.014 + Math.random() * 0.035,  // twinkle speed
    }));

    const all = particles.concat([mouse]);
    let rafId = null;

    function draw() {
        if (document.hidden) {
            rafId = null;
            return;
        }
        if (reducedMotion && reducedMotion.matches) {
            ctx.clearRect(0, 0, W, H);
            rafId = null;
            return;
        }

        const dark = isDark();
        const color = dark ? CONFIG.colorDark : CONFIG.colorLight;
        const linkBoost = dark ? 0.45 : 0.85;
        syncOpacity(dark);

        ctx.clearRect(0, 0, W, H);

        for (let i = 0; i < particles.length; i++) {
            const p = particles[i];

            // Move
            p.x += p.vx;
            p.y += p.vy;
            if (p.x > W || p.x < 0) p.vx *= -1;
            if (p.y > H || p.y < 0) p.vy *= -1;

            // Draw dot — soft halo circle in dark mode avoids expensive ctx.shadowBlur
            if (dark) {
                p.tw += p.twSpeed;
                const flicker = 0.5 + 0.5 * Math.sin(p.tw);
                ctx.fillStyle = `rgba(${color},${(0.14 * flicker).toFixed(3)})`;
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.r * 2.6, 0, Math.PI * 2);
                ctx.fill();

                ctx.fillStyle = `rgba(${color},${(0.3 + 0.7 * flicker).toFixed(3)})`;
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
                ctx.fill();
            } else {
                ctx.fillStyle = `rgba(${color},0.72)`;
                ctx.beginPath();
                ctx.arc(p.x, p.y, 1.35, 0, Math.PI * 2);
                ctx.fill();
            }

            // Draw links
            for (let j = i + 1; j < all.length; j++) {
                const q = all[j];
                if (q.x === null || q.y === null) continue;

                const dx = p.x - q.x;
                const dy = p.y - q.y;
                const dist2 = dx * dx + dy * dy;

                if (dist2 >= q.max) continue;

                // Mouse repulsion
                if (q === mouse && dist2 < q.max / 2) {
                    p.x -= CONFIG.mouseRepel * dx;
                    p.y -= CONFIG.mouseRepel * dy;
                }

                const alpha = (1 - dist2 / q.max) * 0.55 * linkBoost;
                ctx.beginPath();
                ctx.lineWidth = alpha * 1.15;
                ctx.strokeStyle = `rgba(${color},${alpha.toFixed(3)})`;
                ctx.moveTo(p.x, p.y);
                ctx.lineTo(q.x, q.y);
                ctx.stroke();
            }
        }

        rafId = requestAnimationFrame(draw);
    }

    document.addEventListener('visibilitychange', () => {
        if (!document.hidden && rafId === null) {
            rafId = requestAnimationFrame(draw);
        }
    });

    setTimeout(() => {
        rafId = requestAnimationFrame(draw);
    }, 100);
})();
