// Mobile Navigation Toggle
const navToggle = document.getElementById("navToggle");
const navCollapse = document.getElementById("navCollapse");

if (navToggle && navCollapse) {
    navToggle.addEventListener("click", () => {
        navCollapse.classList.toggle("open");
    });
}

// Auto-dismiss flash toasts after 5 seconds
setTimeout(() => {
    document.querySelectorAll(".flash-toast").forEach(toast => {
        toast.style.opacity = "0";
        toast.style.transition = "opacity 0.4s ease";
        setTimeout(() => toast.remove(), 400);
    });
}, 5000);

// Optional subtle GSAP entrance without hiding elements if ScrollTrigger fails
if (typeof gsap !== "undefined" && typeof ScrollTrigger !== "undefined") {
    gsap.registerPlugin(ScrollTrigger);
    gsap.utils.toArray(".service-card, .package-card, .trust-card").forEach(card => {
        gsap.from(card, {
            y: 24,
            duration: 0.6,
            ease: "power2.out",
            scrollTrigger: {
                trigger: card,
                start: "top 90%",
                once: true,
            },
        });
    });
}
