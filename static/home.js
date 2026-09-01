// Array of images
const images = [
  "/static/backgphoto.png",
  "/static/Decoration.png",
  "/static/photog.png",
  "/static/makeup.png",
  "/static/image/mehendi.png",
  "/static/image/dhol_band.png",
  "/static/image/choreographer.png",
  "/static/image/anchor.png",
  "/static/image/fireworks.png"
];

let currentIndex = 0;
const heroSection = document.querySelector(".hero");

// Function to change background
function changeBackground() {
  heroSection.style.backgroundImage = `url(${images[currentIndex]})`;
  currentIndex = (currentIndex + 1) % images.length;
}

// Initial call
changeBackground();

// Change every 5 seconds
setInterval(changeBackground, 5000);
