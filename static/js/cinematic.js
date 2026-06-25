// ======================
// CUSTOM CURSOR
// ======================

const dot = document.querySelector(".cursor-dot");
const outline = document.querySelector(".cursor-outline");


window.addEventListener("mousemove", (e)=>{

    dot.style.left = e.clientX + "px";
    dot.style.top = e.clientY + "px";


    outline.style.left =
    e.clientX - 17 + "px";

    outline.style.top =
    e.clientY - 17 + "px";

});
// HERO INTRO


gsap.from(".hero-tag",{

opacity:0,
y:20,
duration:1

});


gsap.from(".hero-title",{

opacity:0,
y:60,
duration:1.2,
delay:.3

});


gsap.from(".hero-subtitle",{

opacity:0,
y:40,
duration:1,
delay:.6

});


gsap.from(".floating-element",{

opacity:0,
scale:.5,
duration:1,
delay:1,
stagger:.2

});
// PREMIUM PORTFOLIO PLAY


document
.querySelectorAll(".showcase-card")
.forEach(card=>{


let video =
card.querySelector("video");


card.addEventListener(
"mouseenter",
()=>{

video.play();

});


card.addEventListener(
"mouseleave",
()=>{

video.pause();

video.currentTime=0;

});


});