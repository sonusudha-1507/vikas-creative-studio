// Custom Cursor (guarded for missing DOM or mobile)
const dot = document.querySelector(".cursor-dot");
const outline = document.querySelector(".cursor-outline");

if (dot && outline && window.matchMedia("(pointer: fine)").matches) {
    window.addEventListener("mousemove", e => {
        dot.style.left = e.clientX + "px";
        dot.style.top = e.clientY + "px";
        outline.style.left = e.clientX + "px";
        outline.style.top = e.clientY + "px";
    });
}

// Hero Intro
if (typeof gsap !== "undefined") {
    gsap.from(".hero-tag", { opacity: 0, y: 16, duration: 0.7 });
    gsap.from(".hero-title", { opacity: 0, y: 28, duration: 0.85, delay: 0.15 });
    gsap.from(".hero-subtitle", { opacity: 0, y: 20, duration: 0.75, delay: 0.3 });
}

// Portfolio Video Hover Preview
document.querySelectorAll(".showcase-card").forEach(card => {
    const video = card.querySelector("video");
    if (!video) return;

    card.addEventListener("mouseenter", () => {
        video.play().catch(() => {});
    });

    card.addEventListener("mouseleave", () => {
        video.pause();
        video.currentTime = 0;
    });
});
