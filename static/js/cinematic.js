// Scroll Progress Bar
const scrollProgress = document.getElementById("scrollProgress");
if (scrollProgress) {
    window.addEventListener("scroll", () => {
        const scrollTop = window.scrollY;
        const docHeight = document.documentElement.scrollHeight - window.innerHeight;
        const pct = docHeight > 0 ? Math.min(100, (scrollTop / docHeight) * 100) : 0;
        scrollProgress.style.width = pct + "%";
    });
}

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

// Magnetic Buttons Micro-interaction (desktop only)
if (window.matchMedia("(pointer: fine)").matches) {
    document.querySelectorAll(".magnetic").forEach(btn => {
        btn.addEventListener("mousemove", e => {
            const rect = btn.getBoundingClientRect();
            const x = (e.clientX - rect.left - rect.width / 2) * 0.16;
            const y = (e.clientY - rect.top - rect.height / 2) * 0.16;
            btn.style.transform = `translate(${x}px, ${y}px)`;
        });
        btn.addEventListener("mouseleave", () => {
            btn.style.transform = "";
        });
    });
}

// Hero Intro
if (typeof gsap !== "undefined") {
    gsap.from(".hero-tag", { opacity: 0, y: 16, duration: 0.7 });
    gsap.from(".hero-title", { opacity: 0, y: 28, duration: 0.85, delay: 0.15 });
    gsap.from(".hero-subtitle", { opacity: 0, y: 20, duration: 0.75, delay: 0.3 });
}

// Portfolio Video Hover Preview & Click-to-Watch Lightbox
const lightbox = document.getElementById("videoLightbox");
const lightboxVideo = document.getElementById("lightboxVideo");
const lightboxTitle = document.getElementById("lightboxTitle");
const lightboxTag = document.getElementById("lightboxTag");
const lightboxOrderBtn = document.getElementById("lightboxOrderBtn");
const lightboxClose = document.getElementById("lightboxClose");
const lightboxBackdrop = document.getElementById("lightboxBackdrop");

function closeLightbox() {
    if (!lightbox || !lightboxVideo) return;
    lightbox.classList.remove("open");
    lightbox.setAttribute("aria-hidden", "true");
    lightboxVideo.pause();
    lightboxVideo.removeAttribute("src");
    lightboxVideo.load();
}

document.querySelectorAll(".showcase-card").forEach(card => {
    const video = card.querySelector("video");
    if (video) {
        card.addEventListener("mouseenter", () => video.play().catch(() => {}));
        card.addEventListener("mouseleave", () => {
            video.pause();
            video.currentTime = 0;
        });
    }

    card.addEventListener("click", () => {
        if (!lightbox || !lightboxVideo) return;
        const src = card.dataset.video;
        const title = card.dataset.title || "Studio Showcase";
        const tag = card.dataset.tag || "FEATURED EDIT";
        const service = card.dataset.service || "Video Editing";

        lightboxVideo.src = src;
        lightboxTitle.textContent = title;
        lightboxTag.textContent = tag;
        if (lightboxOrderBtn) {
            lightboxOrderBtn.href = `/start-project?service=${encodeURIComponent(service)}`;
        }
        lightbox.classList.add("open");
        lightbox.setAttribute("aria-hidden", "false");
        lightboxVideo.play().catch(() => {});
    });
});

if (lightboxClose) lightboxClose.addEventListener("click", closeLightbox);
if (lightboxBackdrop) lightboxBackdrop.addEventListener("click", closeLightbox);
document.addEventListener("keydown", e => {
    if (e.key === "Escape") closeLightbox();
});

// Before / After Interactive Slider
const compareBox = document.getElementById("compareBox");
const compareRange = document.getElementById("compareRange");
if (compareBox && compareRange) {
    compareRange.addEventListener("input", () => {
        compareBox.style.setProperty("--pos", compareRange.value + "%");
    });

    const beforeVid = compareBox.querySelector(".compare-before");
    const afterVid = compareBox.querySelector(".compare-after");
    if (beforeVid && afterVid) {
        setInterval(() => {
            if (Math.abs(beforeVid.currentTime - afterVid.currentTime) > 0.25) {
                beforeVid.currentTime = afterVid.currentTime;
            }
        }, 600);
    }
}

// FAQ Accordion
document.querySelectorAll(".faq-question").forEach(btn => {
    btn.addEventListener("click", () => {
        const item = btn.closest(".faq-item");
        if (!item) return;
        const isOpen = item.classList.contains("open");
        document.querySelectorAll(".faq-item").forEach(i => i.classList.remove("open"));
        if (!isOpen) item.classList.add("open");
    });
});
