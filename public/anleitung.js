let aktuelleAnleitungSeite = 0;

function getAnleitungSlides() {
    const screen = document.getElementById("anleitung-screen");
    if (!screen) return [];

    return Array.from(screen.querySelectorAll(
        ".anleitung-text1, .anleitung-text-grover, .anleitung-text-funktion, .anleitung-text-messen, .anleitung-text-orakel"
    ));
}

function updateAnleitungNavigation() {
    const slides = getAnleitungSlides();
    const prevButton = document.getElementById("anleitung-zurueck-button");
    const nextButton = document.getElementById("anleitung-weiter-button");
    const counter = document.getElementById("anleitung-counter");
    const nav = document.getElementById("anleitung-navigation");

    if (!slides.length) {
        if (nav) nav.style.display = "none";
        return;
    }

    if (nav) nav.style.display = "flex";

    slides.forEach((slide, index) => {
        slide.classList.add("anleitung-slide");
        slide.classList.toggle("active", index === aktuelleAnleitungSeite);
    });

    if (prevButton) prevButton.disabled = aktuelleAnleitungSeite === 0;
    if (nextButton) nextButton.disabled = aktuelleAnleitungSeite === slides.length - 1;
    if (counter) counter.textContent = `${aktuelleAnleitungSeite + 1}/${slides.length}`;
}

function anleitungSeiteWechseln(richtung) {
    const slides = getAnleitungSlides();
    if (!slides.length) return;

    aktuelleAnleitungSeite = Math.max(0, Math.min(slides.length - 1, aktuelleAnleitungSeite + richtung));
    updateAnleitungNavigation();
}

function anleitungVorherigeSeite() {
    anleitungSeiteWechseln(-1);
}

function anleitungNaechsteSeite() {
    anleitungSeiteWechseln(1);
}

function anleitungZurErstenSeite() {
    aktuelleAnleitungSeite = 0;
    updateAnleitungNavigation();
}

function initAnleitungNavigation() {
    const container = document.querySelector("#anleitung-screen .anleitung");
    if (!container || document.getElementById("anleitung-navigation")) {
        updateAnleitungNavigation();
        return;
    }

    const navigation = document.createElement("div");
    navigation.id = "anleitung-navigation";
    navigation.className = "anleitung-navigation";

    const prevButton = document.createElement("button");
    prevButton.type = "button";
    prevButton.id = "anleitung-zurueck-button";
    prevButton.className = "button anleitung-nav-button";
    prevButton.onclick = anleitungVorherigeSeite;
    prevButton.innerHTML = "<span>&lt;</span>";

    const counter = document.createElement("div");
    counter.id = "anleitung-counter";
    counter.className = "anleitung-counter";

    const nextButton = document.createElement("button");
    nextButton.type = "button";
    nextButton.id = "anleitung-weiter-button";
    nextButton.className = "button anleitung-nav-button";
    nextButton.onclick = anleitungNaechsteSeite;
    nextButton.innerHTML = "<span>&gt;</span>";

    navigation.appendChild(prevButton);
    navigation.appendChild(counter);
    navigation.appendChild(nextButton);

    const closeForm = container.querySelector("form");
    container.insertBefore(navigation, closeForm);
    updateAnleitungNavigation();
}

document.addEventListener("DOMContentLoaded", initAnleitungNavigation);
