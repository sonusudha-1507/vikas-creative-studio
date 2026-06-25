// Global JS placeholder
console.log("VIKAS frontend loaded");
// Portfolio reveal
gsap.from(".portfolio-card", {
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
gsap.registerPlugin(ScrollTrigger);

gsap.utils.toArray("section").forEach(section => {
  gsap.from(section, {
    opacity: 0,
    y: 60,
    duration: 1,
    ease: "power3.out",
    scrollTrigger: {
      trigger: section,
      start: "top 80%"
    }
  });
});
document.querySelectorAll(".portfolio-card").forEach(card => {
  const video = card.querySelector(".portfolio-video");

  if (!video) return;

  card.addEventListener("mouseenter", () => {
    video.style.opacity = "1";
    video.play().catch(error => {
      console.error("Video playback failed:", error);
    });
  });

  card.addEventListener("mouseleave", () => {
    video.pause();
    video.currentTime = 0;
    video.style.opacity = "0";
  });
});

