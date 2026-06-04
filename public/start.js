
let previousScreen = null; // für die Anleitung, damit immer gespeichert ist was der screen vor der Anleitung war

//Wenn Button "Mission starten" geklickt wird, wird die Funktion aufgerufen
const startMission = function() {
    showStory()
}


const showStory = function() {
    document.getElementById("erster_screen").style.display = "none";
    document.getElementById("story_screen").style.display = "block";
}

const zurRollenAuswahl = function() {
    document.getElementById("erster_screen").style.display = "none";
    document.getElementById("story_screen").style.display = "none";
    document.getElementById("role_screen").style.display = "block";
    document.getElementById("anleitung-screen").style.display = "none";
}

const backToFirstScreen = function() {
    document.getElementById("erster_screen").style.display = "block";
    document.getElementById("story_screen").style.display = "none";
    document.getElementById("role_screen").style.display = "none";
    document.getElementById("anleitung-screen").style.display = "none";
}

const backToStoryScreen = function() {
    document.getElementById("erster_screen").style.display = "none";
    document.getElementById("story_screen").style.display = "block";
    document.getElementById("role_screen").style.display = "none";
    document.getElementById("anleitung-screen").style.display = "none";
}

const startQuantumSearch = function() {
    fetch('/reset', { method: 'POST' })
        .then(() => fetch('/start/game', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ force_new: true })
        }))
        .then(() => { window.location.href = 'grover.html'; });
}

const startManualSearch = function() {
    fetch('/start/manual', { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            if (data.game_mode === 'quantum') {
                window.location.href = 'human.html?player=1';
                return;
            }

            // Zweiter Spieler tritt frischer Lobby bei
            if (data.player === 2) {
                window.location.href = 'human.html?player=2';
                return;
            }
            // Spieler 1 / Neustart: alten Stand verwerfen, ganz neues Spiel
            return fetch('/reset', { method: 'POST' })
                .then(() => fetch('/start/manual', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ force_new: true })
                }))
                .then(r => r.json())
                .then(data2 => {
                    window.location.href = `human.html?player=${data2.player ?? 1}`;
                });
        });
}


const anleitungOeffnen = function() {

    //wenn jetzt erster screen ist, dann wird previous screen auf erster_screen gesetzt
    if (document.getElementById("erster_screen").style.display !== "none") {
        previousScreen = "erster_screen";
    }

    else if (document.getElementById("story_screen").style.display !== "none") {
        previousScreen = "story_screen";
    }
    else if(document.getElementById("role_screen").style.display !== "none") {
        previousScreen = "role_screen";
    }

    if (previousScreen) {
        document.getElementById(previousScreen).style.display = "none";
    }
    
    //Anleitung screen zeigen
    document.getElementById("anleitung-screen").style.display = "block";
    if (typeof anleitungZurErstenSeite === "function") anleitungZurErstenSeite();

}

const anleitungSchliessen = function() {
    document.getElementById("anleitung-screen").style.display = "none";

    if (previousScreen) {
        document.getElementById(previousScreen).style.display = "block";
    }
    
}

