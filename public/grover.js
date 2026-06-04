let currentView = 'p'; // 'p' = Wahrscheinlichkeit, 't' = Temperatur, 'c' = Zellen
let knownGameId = null; // detect if game was reset
let gameState = null;
let wasWaiting = false;
let humanHasPlayed = false; // Human muss zuerst spielen
let gameAborted = false;
let gameEnding = false;
let opponentFoundNoticeShown = false;
let opponentFoundNoticeTimeout = null;
let wasGroverTurn = false;
let turnNoticeTimeout = null;
let groverFoundCell = null;
let pollInterval = null;

const canvas = document.getElementById('groverCanvas');
const ctx = canvas.getContext('2d');
let cellPositions = [];

function initCanvas() {
    const wrapper = canvas.parentElement;
    canvas.width  = wrapper.clientWidth  || 600;
    canvas.height = 420;
    placeCells();
    renderGrid();
}

function seededUnit(index, salt) {
    const raw = Math.sin((index + 1) * 12.9898 + salt * 78.233) * 43758.5453;
    return raw - Math.floor(raw);
}

function placeCells() {
    cellPositions = [];
    const W = canvas.width, H = canvas.height;
    const padX = 50, padY = 40;
    const cellW = (W - 2 * padX) / 4;
    const cellH = (H - 2 * padY) / 4;
    for (let row = 0; row < 4; row++) {
        for (let col = 0; col < 4; col++) {
            const idx = row * 4 + col;
            const jx = (seededUnit(idx, 1) - 0.5) * cellW * 0.28;
            const jy = (seededUnit(idx, 2) - 0.5) * cellH * 0.28;
            cellPositions.push({
                x: padX + col * cellW + cellW / 2 + jx,
                y: padY + row * cellH + cellH / 2 + jy,
                r: 24 + seededUnit(idx, 3) * 10
            });
        }
    }
}

function renderGrid() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (!gameState) return;
    const probs = gameState.probabilities || Array(16).fill(0.0625);
    const temps = gameState.grid_cells || [];
    for (let i = 0; i < 16; i++) {
        if (i === groverFoundCell) {
            drawSurvivor(cellPositions[i]);
        } else {
            const prob = probs[i] ?? 0.0625;
            let label;
            if (currentView === 'p')      label = (prob * 100).toFixed(1) + '%';
            else if (currentView === 't') label = temps[i] !== undefined ? temps[i].toFixed(1) + '°' : '?';
            else                          label = `${i + 1}`;
            drawDot(i, label);
        }
    }
}

function drawSurvivor({ x, y, r }) {
    const g = ctx.createRadialGradient(x, y, 0, x, y, r * 2.4);
    g.addColorStop(0,   'rgba(0,255,140,0.95)');
    g.addColorStop(0.5, 'rgba(0,180,80,0.45)');
    g.addColorStop(1,   'rgba(0,0,0,0)');
    ctx.beginPath();
    ctx.arc(x, y, r * 2.4, 0, Math.PI * 2);
    ctx.fillStyle = g;
    ctx.fill();

    ctx.save();
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 2;
    const s = r * 0.55;
    ctx.beginPath(); ctx.arc(x, y - s, s * 0.38, 0, Math.PI * 2); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(x, y - s * 0.6); ctx.lineTo(x, y + s * 0.4); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(x - s * 0.5, y); ctx.lineTo(x + s * 0.5, y); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(x, y + s * 0.4); ctx.lineTo(x - s * 0.4, y + s); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(x, y + s * 0.4); ctx.lineTo(x + s * 0.4, y + s); ctx.stroke();
    ctx.restore();
}

function drawDot(i, label) {
    const { x, y, r } = cellPositions[i];

    const g1 = ctx.createRadialGradient(x, y, 0, x, y, r * 2.4);
    g1.addColorStop(0,    'rgba(255,160,40,0.95)');
    g1.addColorStop(0.45, 'rgba(220,90,0,0.60)');
    g1.addColorStop(1,    'rgba(0,0,0,0)');
    ctx.beginPath();
    ctx.arc(x, y, r * 2.4, 0, Math.PI * 2);
    ctx.fillStyle = g1;
    ctx.fill();

    const g2 = ctx.createRadialGradient(x, y, 0, x, y, r * 0.75);
    g2.addColorStop(0, 'rgba(255,230,130,1)');
    g2.addColorStop(1, 'rgba(255,140,30,0)');
    ctx.beginPath();
    ctx.arc(x, y, r * 0.75, 0, Math.PI * 2);
    ctx.fillStyle = g2;
    ctx.fill();

    ctx.font = 'bold 14px Courier New';
    ctx.fillStyle = '#ffffff';
    ctx.textAlign = 'center';
    ctx.shadowColor = 'rgba(0,0,0,0.9)';
    ctx.shadowBlur = 5;
    ctx.fillText(label, x, y - r - 10);
    ctx.shadowBlur = 0;
}

function updateGrid(state) {
    if (state) gameState = state;
    renderGrid();
}

//  Iterations-Balken
function updateIterBar(current, max) {
    const fill = document.getElementById('iter-fill');
    const counter = document.getElementById('iter-counter');
    const overshootEl = document.getElementById('iter-overshoot');
    const sublabel = document.getElementById('iter-sublabel');

    const overshot = current > max;
    const displayCurrent = overshot ? current - max : current;
    const pct = Math.min(displayCurrent / max, 1) * 100;

    fill.style.height = `${pct}%`;
    fill.style.background = overshot
        ? 'linear-gradient(to top, #ff2222, #ff6666)'
        : 'linear-gradient(to top, #1b7895, #4fc3f7)';

    counter.textContent = `${current}/${max}`;
    counter.style.color = overshot ? '#ff4444' : '';

    sublabel.textContent = `OPTIMAL: ${max}`;
    overshootEl.style.display = overshot ? 'block' : 'none';
}

function showGameAbortedOverlay() {
    if (gameAborted) return;
    gameAborted = true;

    document.getElementById('wait-overlay').style.display = 'none';
    document.getElementById('survivor-wait-overlay').classList.remove('show');
    document.getElementById('end-overlay').classList.remove('show');
    const humanFoundBanner = document.getElementById('human-found-banner');
    if (humanFoundBanner) humanFoundBanner.style.display = 'none';
    setButtonState(false, false);

    const overlay = document.createElement('div');
    overlay.id = 'game-aborted-overlay';
    overlay.style.cssText = [
        'position:fixed',
        'inset:0',
        'z-index:3000',
        'display:flex',
        'align-items:center',
        'justify-content:center',
        'background:rgba(0,0,0,0.78)'
    ].join(';');

    const card = document.createElement('div');
    card.className = 'report-card';
    card.style.cssText = [
        'border:1px solid #ff4444',
        'box-shadow:0 0 28px rgba(255,68,68,0.22)'
    ].join(';');

    const title = document.createElement('div');
    title.textContent = 'DER ANDERE SPIELER HAT DAS SPIEL ABGEBROCHEN';
    title.style.cssText = [
        'font-family:"Mokoto",sans-serif',
        'font-size:18px',
        'letter-spacing:2px',
        'line-height:1.35',
        'color:#ff4444',
        'margin-bottom:24px'
    ].join(';');

    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'button report-btn';
    const buttonText = document.createElement('span');
    buttonText.textContent = 'ZURÜCK';
    button.appendChild(buttonText);
    button.onclick = goToMainMenu;

    card.appendChild(title);
    card.appendChild(button);
    overlay.appendChild(card);
    document.body.appendChild(overlay);
}

//  Polling 
function pollState() {
    fetch('/state')
        .then(r => {
            if (!r.ok) throw new Error('state fetch failed');
            return r.json();
        })
        .then(state => {
            if (knownGameId !== null && state.game_id && state.game_id !== knownGameId) {
                showGameAbortedOverlay();
                return;
            }
            if (state.game_id) knownGameId = state.game_id;

            gameState = state;
            updateGrid(state);
            updateIterBar(state.current_iteration ?? 0, state.max_iterations ?? 3);
            const groverRoundsCompleted = state.grover_rounds_completed ?? 0;
            const groverMaxZuege = state.max_steps ?? state.max_zuege ?? 10;
            document.getElementById('zug-header').textContent = `ZUG NO. ${groverRoundsCompleted}`;
            document.getElementById('grover-turn-counter').textContent = `ZÜGE ${groverRoundsCompleted}/${groverMaxZuege}`;

            const humanRoundsCompleted = state.human_rounds_completed ?? 0;
            const humanMaxZuege = state.max_steps ?? state.max_zuege ?? 10;
            const humanFoundSurvivor = state.human_survivor_found ?? false;

            // Human hat gespielt wenn: mindestens 1 Zug gemacht hat ODER gefunden ODER keine Züge mehr
            const humanDoneFirstTurn = humanRoundsCompleted >= 1 || humanFoundSurvivor || humanRoundsCompleted >= humanMaxZuege;

            if (state.waiting_for_human_partner || !humanDoneFirstTurn) {
                // Human hat noch nicht gespielt - alle Grover-Buttons sperren, Meldung zeigen
                showWaitWithText('WARTE AUF KLASSISCHEN SPIELER...');
                humanHasPlayed = false;
                return;
            }

            if (!humanHasPlayed && humanDoneFirstTurn) {
                // Übergang: Human hat gerade seinen ersten Zug gemacht
                humanHasPlayed = true;
                wasWaiting = true; // damit showWait(false) die Buttons freischaltet
            }

            // Grover hat gefunden - warte-overlay
            const survivorWaiting = state.grover_survivor_found && state.game_phase !== 'end';
            document.getElementById('survivor-wait-overlay').classList.toggle('show', survivorWaiting);
            if (survivorWaiting) {
                setButtonState(false, false);
                return;
            }

            // Human hat gefunden, Grover noch nicht — kurzen Hinweis anzeigen
            const humanFoundBanner = document.getElementById('human-found-banner');
            if (humanFoundBanner) humanFoundBanner.style.display = 'none';
            if (humanFoundSurvivor && !state.grover_survivor_found && state.game_phase !== 'end') {
                if (!opponentFoundNoticeShown) {
                    showOpponentFoundNotice();
                    opponentFoundNoticeShown = true;
                }
            }

            if (state.game_phase === 'end' && !gameEnding) {
                gameEnding = true;
                clearInterval(pollInterval);
                document.getElementById('survivor-wait-overlay').classList.remove('show');
                const hb = document.getElementById('human-found-banner');
                if (hb) hb.style.display = 'none';
                document.getElementById('wait-overlay').style.display = 'none';
                renderGrid();
                setTimeout(() => showEndScreen(state), 800);
                return;
            }
            if (gameEnding) return;

            const canGroverPlayNow = state.can_grover_play ?? false;
            if (!wasGroverTurn && canGroverPlayNow && !gameAborted) {
                showTurnNotice();
            }
            wasGroverTurn = canGroverPlayNow;

            if (!canGroverPlayNow && !state.grover_survivor_found) {
                showWaitWithText('WARTE AUF KLASSISCHEN SPIELER...');
            } else {
                hideWait();
            }
        })
        .catch(() => {
            if (knownGameId !== null) showGameAbortedOverlay();
        });
}

function showWaitWithText(text) {
    const overlay = document.getElementById('wait-overlay');
    overlay.style.display = 'block';
    document.getElementById('wait-text').textContent = text;
    setButtonState(false, false);
    wasWaiting = true;
}

function hideWait() {
    document.getElementById('wait-overlay').style.display = 'none';
    if (wasWaiting) {
        setButtonState(true, false);
        document.getElementById('info-text').textContent = 'Wende das Orakel an';
        wasWaiting = false;
    }
}

function showOpponentFoundNotice() {
    const notice = document.getElementById('opponent-found-notice');
    if (!notice) return;

    clearTimeout(opponentFoundNoticeTimeout);
    notice.classList.add('show');
    opponentFoundNoticeTimeout = setTimeout(() => {
        notice.classList.remove('show');
    }, 3000);
}

function showTurnNotice() {
    const notice = document.getElementById('turn-notice');
    if (!notice) return;

    clearTimeout(turnNoticeTimeout);
    notice.classList.add('show');
    turnNoticeTimeout = setTimeout(() => {
        notice.classList.remove('show');
    }, 1500);
}

//  Button State 
// afterAmplify: true = Messen + Zug beenden aktiv, Oracle/Amplify gesperrt
function setButtonState(oracleEnabled, amplifyEnabled, afterAmplify = false) {
    document.getElementById('btn-oracle').disabled = !oracleEnabled;
    document.getElementById('btn-amplify').disabled = !amplifyEnabled;
    document.getElementById('btn-measure').disabled = !afterAmplify;
    document.getElementById('btn-end-turn').disabled = !afterAmplify;
}

//  Buttons 
function pressOracle() {
    fetch('/grover/oracle', { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            if (!data.ok) {
                document.getElementById('info-text').textContent = data.error ?? 'Fehler';
                return;
            }
            setButtonState(false, true);
            document.getElementById('info-text').textContent =
                'ORACLE ANGEWENDET: PHASE UMGEKEHRT. WAHRSCHEINLICHKEITEN NOCH UNVERÄNDERT!';
            updateGrid(data);
        });
}

function pressAmplify() {
    fetch('/grover/amplify', { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            if (!data.ok) {
                document.getElementById('info-text').textContent = data.error ?? 'Fehler';
                return;
            }
            setButtonState(false, false, true); // Messen + Zug beenden aktiv
            const top = data.probabilities.indexOf(Math.max(...data.probabilities));
            const pct = (data.probabilities[top] * 100).toFixed(1);
            document.getElementById('info-text').textContent =
                `HÖCHSTE WAHRSCHEINLICHKEIT: ${pct}% - MESSEN, WEITERMACHEN ODER ZUG BEENDEN`;
            updateGrid(data);
        });
}

function pressMeasure() {
    fetch('/grover/measure', { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            if (!data.ok) {
                document.getElementById('info-text').textContent = data.error ?? 'Fehler';
                return;
            }
            document.getElementById('info-text').textContent = data.found_survivor
                ? `MESSUNG: ZELLE ${data.cell_index + 1} - SURVIVOR GEFUNDEN!`
                : `MESSUNG: ZELLE ${data.cell_index + 1} - KEIN SURVIVOR`;
            if (data.found_survivor) {
                groverFoundCell = data.cell_index;
                document.getElementById('survivor-cell-info').textContent =
                    `ZELLE ${data.cell_index + 1} GEMESSEN`;
                setButtonState(false, false);
                renderGrid();
                // Interval stoppen damit er nicht früher als 1.8s das Overlay zeigt
                clearInterval(pollInterval);
                setTimeout(() => {
                    pollState();
                    if (!gameEnding) pollInterval = setInterval(pollState, 1500);
                }, 1800);
            } else {
                setButtonState(true, false);
                pollState();
            }
        });
}

function pressEndTurn() {
    fetch('/grover/end_turn', { method: 'POST' })
        .then(r => r.json())
        .then(() => {
            setButtonState(false, false);
            document.getElementById('info-text').textContent = 'ZUG BEENDET - WARTE AUF HUMAN';
            wasWaiting = true;
            pollState();
        });
}

function toggleView() {
    const views = ['p', 't', 'c'];
    const labels = ['WAHRSCHEINLICHKEIT', 'TEMPERATUR', 'ZELLEN'];
    currentView = views[(views.indexOf(currentView) + 1) % 3];
    document.getElementById('view-label').textContent = labels[views.indexOf(currentView)];
    if (gameState) updateGrid(gameState);
}

function showWait(show) {
    if (show) {
        showWaitWithText('WARTE AUF KLASSISCHEN SPIELER...');
    } else {
        hideWait();
    }
}

function showEndScreen(state) {
    document.getElementById('survivor-wait-overlay').classList.remove('show');
    const humanFoundBanner = document.getElementById('human-found-banner');
    if (humanFoundBanner) humanFoundBanner.style.display = 'none';
    document.getElementById('wait-overlay').style.display = 'none';

    const won = state.grover_survivor_found;
    const title = document.getElementById('end-title');
    title.textContent = won ? 'MISSION ERFÜLLT' : 'MISSION FEHLGESCHLAGEN';
    title.style.color = won ? '#00ff88' : '#ff4444';
    document.getElementById('rpt-found').textContent = won ? 'JA' : 'NEIN';
    document.getElementById('rpt-found').style.color = won ? '#00ff88' : '#ff4444';
    document.getElementById('rpt-grover-steps').textContent =
        won ? `${state.grover_rounds_completed ?? '?'} ZÜGE` : 'NICHT GEFUNDEN';
    document.getElementById('rpt-grover-steps').style.color = won ? '#00ff88' : '#ff4444';
    document.getElementById('rpt-grover-zuege').textContent =
        `${state.grover_rounds_completed ?? '?'} ZÜGE`;
    document.getElementById('rpt-classic-zuege').textContent =
        `${state.human_rounds_completed ?? '?'} ZÜGE`;

    const player1Label = document.getElementById('rpt-player1-label');
    const player2Label = document.getElementById('rpt-player2-label');
    if (player1Label && player2Label) {
        player1Label.textContent = 'KLASSISCH';
        player2Label.textContent = 'GROVER';
    }

    document.getElementById('end-overlay').classList.add('show');
}

const anleitungOeffnen = function() {
    document.getElementById("anleitung-screen").style.display = "block";
    if (typeof anleitungZurErstenSeite === "function") anleitungZurErstenSeite();
}

const anleitungSchliessen = function() {
    document.getElementById("anleitung-screen").style.display = "none";
}

function goToMainMenu() {
    fetch('/reset', { method: 'POST' })
        .catch(() => {})
        .finally(() => { window.location.href = 'start.html'; });
}

function restartGame() {
    fetch('/reset', { method: 'POST' })
        .then(() => fetch('/start/game', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ force_new: true })
        }))
        .then(() => { window.location.reload(); });
}

//  Init
window.addEventListener('resize', initCanvas);
initCanvas();
setButtonState(false, false);
showWaitWithText('WARTE AUF KLASSISCHEN SPIELER...');
pollState();
pollInterval = setInterval(pollState, 1500);
