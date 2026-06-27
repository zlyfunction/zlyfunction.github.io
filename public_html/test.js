/**
 * Particle network background animation
 * Tuned to match the site's color scheme and aesthetic.
 * Light theme: a subtle dark-blue particle network.
 * Dark theme:  soft, twinkling star field with faint constellation lines.
 */
(function () {
    const CONFIG = {
        count: 60,           // number of particles
        speed: 0.45,         // max speed per axis
        colorLight: '42,95,158',    // --color-accent-light (#2a5f9e)
        colorDark: '200,220,255',   // soft starlight (blue-white)
        opacityLight: 0.38,  // canvas layer opacity in light mode
        opacityDark: 0.9,    // brighter so stars read on the dark background
        linkDist: 5500,      // max squared distance to draw a line between particles
        mouseDist: 18000,    // squared distance for mouse interaction
        mouseRepel: 0.025,   // strength of mouse repulsion
        zIndex: -1,
    };

    function isDark() {
        return document.documentElement.getAttribute('data-theme') === 'dark';
    }

    // Canvas setup
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    canvas.style.cssText = [
        'position:fixed',
        'top:0',
        'left:0',
        `z-index:${CONFIG.zIndex}`,
        `opacity:${CONFIG.opacityLight}`,
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
    window.addEventListener('resize', resize);

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
    });
    window.addEventListener('mouseout', () => {
        mouse.x = null;
        mouse.y = null;
    });

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
        r: 0.8 + Math.random() * 1.7,           // star radius (dark mode)
        tw: Math.random() * Math.PI * 2,         // twinkle phase
        twSpeed: 0.015 + Math.random() * 0.04,   // twinkle speed
    }));

    const all = particles.concat([mouse]);

    function draw() {
        const dark = isDark();
        const color = dark ? CONFIG.colorDark : CONFIG.colorLight;
        const linkBoost = dark ? 0.5 : 1;
        syncOpacity(dark);

        ctx.clearRect(0, 0, W, H);

        for (let i = 0; i < particles.length; i++) {
            const p = particles[i];

            // Move
            p.x += p.vx;
            p.y += p.vy;
            if (p.x > W || p.x < 0) p.vx *= -1;
            if (p.y > H || p.y < 0) p.vy *= -1;

            // Draw dot — twinkling, glowing stars in dark mode
            if (dark) {
                p.tw += p.twSpeed;
                const flicker = 0.5 + 0.5 * Math.sin(p.tw); // 0 .. 1
                ctx.fillStyle = `rgba(${color},${0.25 + 0.75 * flicker})`;
                ctx.shadowColor = `rgba(${color},0.9)`;
                ctx.shadowBlur = 4 + 4 * flicker;
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
                ctx.fill();
                ctx.shadowBlur = 0;
            } else {
                ctx.fillStyle = `rgba(${color},0.8)`;
                ctx.beginPath();
                ctx.arc(p.x, p.y, 1.5, 0, Math.PI * 2);
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

                const alpha = (1 - dist2 / q.max) * 0.6 * linkBoost;
                ctx.beginPath();
                ctx.lineWidth = alpha * 1.2;
                ctx.strokeStyle = `rgba(${color},${alpha})`;
                ctx.moveTo(p.x, p.y);
                ctx.lineTo(q.x, q.y);
                ctx.stroke();
            }
        }

        requestAnimationFrame(draw);
    }

    setTimeout(draw, 100);
})();
