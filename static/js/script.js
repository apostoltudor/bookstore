// bookstore/static/js/script.js

document.addEventListener('DOMContentLoaded', () => {
    console.log('Pagina a fost încărcată cu succes.');
    const images = document.querySelectorAll('img');
    images.forEach(img => {
        if (!img.complete) {
            img.addEventListener('load', () => console.log(`Imagine încărcată: ${img.src}`));
            img.addEventListener('error', () => console.error(`Eroare la încărcarea imaginii: ${img.src}`));
        }
    });
});