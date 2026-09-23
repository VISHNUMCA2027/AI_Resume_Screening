document.addEventListener("DOMContentLoaded", function () {

    // ==========================================
    // Professional Background Particle Animation
    // ==========================================

    const canvas = document.createElement("canvas");

    canvas.id = "background-animation";

    canvas.style.position = "fixed";
    canvas.style.left = "0";
    canvas.style.top = "0";
    canvas.style.width = "100%";
    canvas.style.height = "100%";
    canvas.style.pointerEvents = "none";
    canvas.style.zIndex = "1";

    document.body.appendChild(canvas);

    const ctx = canvas.getContext("2d");

    let width;
    let height;

    function resizeCanvas() {

        const dpr = Math.min(
            window.devicePixelRatio || 1,
            2
        );

        width = window.innerWidth;
        height = window.innerHeight;

        canvas.width = width * dpr;
        canvas.height = height * dpr;

        canvas.style.width = width + "px";
        canvas.style.height = height + "px";

        ctx.setTransform(
            dpr,
            0,
            0,
            dpr,
            0,
            0
        );
    }

    resizeCanvas();

    window.addEventListener(
        "resize",
        resizeCanvas
    );


    // ==========================================
    // Mouse Position
    // ==========================================

    let mouseX = width / 2;
    let mouseY = height / 2;

    let targetMouseX = mouseX;
    let targetMouseY = mouseY;

    document.addEventListener(
        "mousemove",
        function (event) {

            targetMouseX = event.clientX;
            targetMouseY = event.clientY;

        }
    );


    // ==========================================
    // Particles
    // ==========================================

    const particles = [];

    const particleCount = 70;


    function createParticle() {

        return {

            x: Math.random() * width,

            y: Math.random() * height,

            size:
                Math.random() * 2.5 + 0.5,

            speedX:
                (Math.random() - 0.5) * 0.35,

            speedY:
                (Math.random() - 0.5) * 0.35,

            opacity:
                Math.random() * 0.6 + 0.2,

            pulse:
                Math.random() * Math.PI * 2,

            pulseSpeed:
                Math.random() * 0.025 + 0.01
        };
    }


    for (
        let i = 0;
        i < particleCount;
        i++
    ) {

        particles.push(
            createParticle()
        );

    }


    // ==========================================
    // Draw Glow
    // ==========================================

    function drawGlow(
        x,
        y,
        radius,
        opacity
    ) {

        const gradient =
            ctx.createRadialGradient(
                x,
                y,
                0,
                x,
                y,
                radius
            );

        gradient.addColorStop(
            0,
            `rgba(168, 85, 247, ${opacity})`
        );

        gradient.addColorStop(
            0.35,
            `rgba(124, 58, 237, ${opacity * 0.45})`
        );

        gradient.addColorStop(
            1,
            "rgba(0, 0, 0, 0)"
        );

        ctx.beginPath();

        ctx.fillStyle = gradient;

        ctx.arc(
            x,
            y,
            radius,
            0,
            Math.PI * 2
        );

        ctx.fill();
    }


    // ==========================================
    // Animation
    // ==========================================

    function animate() {

        ctx.clearRect(
            0,
            0,
            width,
            height
        );


        // Smooth mouse movement

        mouseX +=
            (targetMouseX - mouseX) *
            0.06;

        mouseY +=
            (targetMouseY - mouseY) *
            0.06;


        // ======================================
        // Mouse Glow
        // ======================================

        drawGlow(
            mouseX,
            mouseY,
            180,
            0.10
        );


        // ======================================
        // Background Glow
        // ======================================

        drawGlow(
            width * 0.2,
            height * 0.25,
            260,
            0.035
        );

        drawGlow(
            width * 0.8,
            height * 0.75,
            300,
            0.035
        );


        // ======================================
        // Particles
        // ======================================

        for (
            let i = 0;
            i < particles.length;
            i++
        ) {

            const p =
                particles[i];


            // Movement

            p.x += p.speedX;

            p.y += p.speedY;


            // Pulse

            p.pulse +=
                p.pulseSpeed;


            const pulse =
                Math.sin(p.pulse) *
                0.25;


            // Screen wrap

            if (p.x < -10)
                p.x = width + 10;

            if (p.x > width + 10)
                p.x = -10;

            if (p.y < -10)
                p.y = height + 10;

            if (p.y > height + 10)
                p.y = -10;


            // Distance from mouse

            const dx =
                p.x - mouseX;

            const dy =
                p.y - mouseY;

            const distance =
                Math.sqrt(
                    dx * dx +
                    dy * dy
                );


            let opacity =
                p.opacity + pulse;


            // Mouse interaction

            if (distance < 180) {

                const force =
                    (180 - distance) /
                    180;

                p.x +=
                    dx *
                    force *
                    0.008;

                p.y +=
                    dy *
                    force *
                    0.008;

                opacity +=
                    force * 0.4;
            }


            opacity =
                Math.max(
                    0,
                    Math.min(
                        opacity,
                        1
                    )
                );


            // Glow

            ctx.shadowBlur = 12;

            ctx.shadowColor =
                "#A855F7";


            // Particle

            ctx.beginPath();

            ctx.arc(
                p.x,
                p.y,
                p.size,
                0,
                Math.PI * 2
            );

            ctx.fillStyle =
                `rgba(168, 85, 247, ${opacity})`;

            ctx.fill();


            ctx.shadowBlur = 0;
        }


        requestAnimationFrame(
            animate
        );
    }


    // ==========================================
    // Start
    // ==========================================

    animate();

});