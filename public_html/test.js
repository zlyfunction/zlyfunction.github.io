/**
 * Particle network background animation
 * Tuned to match the site's color scheme and aesthetic.
 */
(function () {
    const CONFIG = {
        count: 60,           // number of particles
        speed: 0.45,         // max speed per axis
        color: '42,95,158',  // --color-accent-light (#2a5f9e)
        opacity: 0.38,       // canvas layer opacity
        linkDist: 5500,      // max squared distance to draw a line between particles
        mouseDist: 18000,    // squared distance for mouse interaction
        mouseRepel: 0.025,   // strength of mouse repulsion
        zIndex: -1,
    };

    // Canvas setup
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    canvas.style.cssText = [
        'position:fixed',
        'top:0',
        'left:0',
        `z-index:${CONFIG.zIndex}`,
        `opacity:${CONFIG.opacity}`,
        'pointer-events:none',
    ].join(';');
    document.body.appendChild(canvas);

    let W, H;
    function resize() {
        W = canvas.width = window.innerWidth || document.documentElement.clientWidth;
        H = canvas.height = window.innerHeight || document.documentElement.clientHeight;
    }
    resize();
    window.addEventListener('resize', resize);

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
    }));

    const all = particles.concat([mouse]);

    function draw() {
        ctx.clearRect(0, 0, W, H);

        for (let i = 0; i < particles.length; i++) {
            const p = particles[i];

            // Move
            p.x += p.vx;
            p.y += p.vy;
            if (p.x > W || p.x < 0) p.vx *= -1;
            if (p.y > H || p.y < 0) p.vy *= -1;

            // Draw dot
            ctx.fillStyle = `rgba(${CONFIG.color},0.8)`;
            ctx.beginPath();
            ctx.arc(p.x, p.y, 1.5, 0, Math.PI * 2);
            ctx.fill();

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

                const alpha = (1 - dist2 / q.max) * 0.6;
                ctx.beginPath();
                ctx.lineWidth = alpha * 1.2;
                ctx.strokeStyle = `rgba(${CONFIG.color},${alpha})`;
                ctx.moveTo(p.x, p.y);
                ctx.lineTo(q.x, q.y);
                ctx.stroke();
            }
        }

        requestAnimationFrame(draw);
    }

    setTimeout(draw, 100);
})();
