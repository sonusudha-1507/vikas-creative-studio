// Global JS placeholder
console.log("VIKAS frontend loaded");
// Portfolio reveal
gsap.from(".portfolio-item", {
    scrollTrigger: {
        trigger: ".portfolio-preview",
        start: "top 80%",
    },
    y: 30,
    opacity: 0,
    duration: 0.8,
    stagger: 0.15,
    ease: "power2.out"
});
