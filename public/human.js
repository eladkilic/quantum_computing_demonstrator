const GRID_SIZE = 16;
const COLS = 4, ROWS = 4;

let survivorCell  = null;
let maxSteps      = 10;
let steps         = 0;
let foundCount    = 0;
let selectedCell  = null;
let revealedCells = new Set();
let gameOver      = false;
let cellPositions         = [];
let pollInterval          = null;
let demoMode              = false;
let groverRoundsCompleted = null;
let canHumanPlay          = false;
let humanFoundCell        = null; // which cell the human found the survivor in
let knownGameId           = null;
let waitingForGameStart   = false; // human.html offen, Quantenspiel noch nicht gestartet
let gameAborted           = false;
let currentGameMode       = null;
let wasHumanTurn          = false;
let turnNoticeTimeout     = null;
let opponentFoundNoticeShown = false;
let opponentFoundNoticeTimeout = null;

// Human-vs-Human:
// player=1 benutzt im Backend human_*, player=2 benutzt dort grover_*.
const humanPlayerNumber = new URLSearchParams(window.location.search).get('player') === '2' ? 2 : 1;

let scanLog = [];

const canvas = document.getElementById('thermalCanvas');
const ctx    = canvas.getContext('2d');

function resizeCanvas() {
    const wrapper = canvas.parentElement;
    canvas.width  = wrapper.clientWidth  || 600;
    canvas.height = 420;
    placeCells();
    render();
}

function watchCanvasSize() {
    const wrapper = canvas.parentElement;
    if (!window.ResizeObserver || !wrapper) return;

    const observer = new ResizeObserver(() => {
        resizeCanvas();
    });
    observer.observe(wrapper);
}

async function apiGetState() {
    const res = await fetch(`/state?player=${humanPlayerNumber}`);
    if (!res.ok) throw new Error('state fetch failed');
    return res.json();
}

async function apiScan(cellIndex) {
    const res = await fetch('/human/move', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cell_index: cellIndex, player: humanPlayerNumber })
    });
    if (!res.ok) throw new Error('scan failed');
    return res.json();
}

function showWaitingForGameStart() {
    waitingForGameStart = true;
    const waitOverlay = document.getElementById('wait-overlay');
    waitOverlay.classList.remove('hidden');
    document.querySelector('#wait-overlay .wait-text').textContent =
        'WARTE BIS QUANTENMODUS GESTARTET WIRD...';
}

function showGameAbortedOverlay() {
    if (gameAborted) return;
    gameAborted = true;
    gameOver = true;
    clearInterval(pollInterval);

    document.getElementById('wait-overlay').classList.add('hidden');
    document.getElementById('survivor-wait-overlay').classList.remove('show');
    document.getElementById('end-overlay').classList.remove('show');
    document.getElementById('grover-found-banner').style.display = 'none';

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
        'font-family:"Mokoto",monospace',
        'font-size:18px',
        'letter-spacing:2px',
        'line-height:1.35',
        'color:#ff4444',
        'margin-bottom:24px'
    ].join(';');

    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'game-btn purple';
    button.textContent = 'ZURÜCK';
    button.onclick = goBack;

    card.appendChild(title);
    card.appendChild(button);
    overlay.appendChild(card);
    document.body.appendChild(overlay);
}

function resetLocalUI() {
    steps = 0;
    foundCount = 0;
    selectedCell = null;
    revealedCells = new Set();
    gameOver = false;
    humanFoundCell = null;
    scanLog = [];
    groverRoundsCompleted = null;
    canHumanPlay = false;
    opponentFoundNoticeShown = false;
    document.getElementById('end-overlay').classList.remove('show');
    document.getElementById('survivor-wait-overlay').classList.remove('show');
    document.getElementById('grover-found-banner').style.display = 'none';
    document.getElementById('last-signal-name').textContent = '–';
    document.getElementById('last-temp').textContent = '–';
    document.getElementById('zug-display').textContent = '0';
    document.getElementById('found-count').textContent = '0';
    document.getElementById('spotBtn').disabled = true;
}

function syncToNewGame(state) {
    resetLocalUI();
    knownGameId = state.game_id ?? null;
    waitingForGameStart = false;
    wasHumanTurn = false;
}

async function boot() {
    resizeCanvas();
    resetLocalUI();
    knownGameId = null;
    document.getElementById('wait-overlay').classList.add('hidden');
    try {
        const state = await apiGetState();
        applyState(state);
        placeCells();
        render();
        startPolling();
    } catch {
        showWaitingForGameStart();
        placeCells();
        render();
        startPolling();
    }
}

function applyState(state) {
    // Neues Spiel (z. B. Partner startet Quantenmodus) — mitmachen, nicht zum Hauptmenü
    if (knownGameId !== null && state.game_id && state.game_id !== knownGameId) {
        if (state.game_mode === 'quantum') {
            syncToNewGame(state);
        } else {
            showGameAbortedOverlay();
        }
        return;
    } else if (state.game_id) {
        knownGameId = state.game_id;
        waitingForGameStart = false;
    }

    survivorCell          = state.survivor_cell;
    currentGameMode       = state.game_mode ?? currentGameMode;
    maxSteps              = state.max_steps ?? state.max_zuege ?? 10;
    steps                 = state.player_rounds_completed ?? 0;
    groverRoundsCompleted = state.opponent_rounds_completed ?? state.grover_rounds_completed ?? null;
    const nextCanHumanPlay = state.can_current_human_play ?? state.can_human_play ?? false;
    if (!wasHumanTurn && nextCanHumanPlay && !gameOver) {
        showTurnNotice();
    }
    canHumanPlay          = nextCanHumanPlay;
    wasHumanTurn          = nextCanHumanPlay;
    revealedCells         = new Set(state.revealed_cells ?? []);
    foundCount            = (state.player_found || state.human_survivor_found) ? 1 : 0;
    document.title        = `Spieler ${humanPlayerNumber} - Thermal Search`;
    document.getElementById('maxStepsDisplay').textContent = maxSteps;
    document.getElementById('zug-display').textContent = steps;

    const opponentFound = state.opponent_found ?? false;
    const playerFound = state.player_found ?? (foundCount > 0);
    const banner = document.getElementById('grover-found-banner');
    if (banner) banner.style.display = 'none';
    if (opponentFound && !playerFound && !opponentFoundNoticeShown && !gameOver) {
        showOpponentFoundNotice();
        opponentFoundNoticeShown = true;
    }

    updateSpotBtn();
    updateStepBar();
    render();

    // Warte-Overlay nur für Lobby / fehlendes Quantenspiel — nicht zwischen Zügen
    const waitOverlay = document.getElementById('wait-overlay');
    if (waitingForGameStart && !gameOver) {
        waitOverlay.classList.remove('hidden');
        document.querySelector('#wait-overlay .wait-text').textContent =
            'WARTE BIS QUANTENMODUS GESTARTET WIRD...';
    } else if (state.waiting_for_second_player && !gameOver) {
        waitOverlay.classList.remove('hidden');
        document.querySelector('#wait-overlay .wait-text').textContent = 'WARTE AUF ANDEREN SPIELER...';
    } else {
        waitOverlay.classList.add('hidden');
    }

    // Grover-Warte-Indikator: zeigen wenn Grover gerade spielt (kein blockierendes Overlay)
    const groverWaitIndicator = document.getElementById('grover-wait-indicator');
    if (groverWaitIndicator) {
        const groverPlaying = state.can_grover_play && !canHumanPlay && state.game_phase === 'game' && !gameOver;
        groverWaitIndicator.style.display = groverPlaying ? 'block' : 'none';
    }

    if (state.game_phase === 'end' && !gameOver) {
        gameOver = true;
        clearInterval(pollInterval);
        document.getElementById('survivor-wait-overlay').classList.remove('show');
        setTimeout(() => endGame(foundCount > 0), 2500);
    }
}

function updateSpotBtn() {
    document.getElementById('spotBtn').disabled = !canHumanPlay || selectedCell === null;
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

function showOpponentFoundNotice() {
    const notice = document.getElementById('opponent-found-notice');
    if (!notice) return;

    clearTimeout(opponentFoundNoticeTimeout);
    notice.classList.add('show');
    opponentFoundNoticeTimeout = setTimeout(() => {
        notice.classList.remove('show');
    }, 3000);
}

function startPolling() {
    pollInterval = setInterval(async () => {
        if (gameOver) return;
        try {
            const state = await apiGetState();
            applyState(state);
            render();
        } catch {
            if (knownGameId !== null) {
                showGameAbortedOverlay();
            } else if (!gameOver) {
                showWaitingForGameStart();
            }
        }
    }, 2000);
}

function placeCells() {
    cellPositions = [];
    const W = canvas.width, H = canvas.height;
    const padX = 50, padY = 40;
    const cellW = (W - 2 * padX) / COLS;
    const cellH = (H - 2 * padY) / ROWS;

    for (let row = 0; row < ROWS; row++) {
        for (let col = 0; col < COLS; col++) {
            const idx = row * COLS + col;
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

function seededUnit(index, salt) {
    const raw = Math.sin((index + 1) * 12.9898 + salt * 78.233) * 43758.5453;
    return raw - Math.floor(raw);
}

function render() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    cellPositions.forEach((pos, i) => {
        if (revealedCells.has(i)) {
            if (i === survivorCell) drawSurvivor(pos);
            else                    drawEmpty(pos);
        } else {
            drawHotspot(pos, i === selectedCell);
        }
    });
}

function drawHotspot({ x, y, r }, selected) {
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

    if (selected) {
        const cr = r * 1.4;
        ctx.beginPath();
        ctx.arc(x, y, cr, 0, Math.PI * 2);
        ctx.strokeStyle = 'rgba(255,60,60,0.9)';
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 4]);
        ctx.stroke();
        ctx.setLineDash([]);

        const arm = cr * 1.0;
        ctx.strokeStyle = 'rgba(255,60,60,0.9)';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(x - arm, y); ctx.lineTo(x - cr * 0.25, y);
        ctx.moveTo(x + cr * 0.25, y); ctx.lineTo(x + arm, y);
        ctx.moveTo(x, y - arm); ctx.lineTo(x, y - cr * 0.25);
        ctx.moveTo(x, y + cr * 0.25); ctx.lineTo(x, y + arm);
        ctx.stroke();
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

function drawEmpty({ x, y, r }) {
    const g = ctx.createRadialGradient(x, y, 0, x, y, r * 1.8);
    g.addColorStop(0, 'rgba(70,70,85,0.55)');
    g.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.beginPath();
    ctx.arc(x, y, r * 1.8, 0, Math.PI * 2);
    ctx.fillStyle = g;
    ctx.fill();
}

canvas.addEventListener('click', (e) => {
    if (gameOver || survivorCell === null) return;
    const { cx, cy } = mousePos(e);
    const hit = hitTest(cx, cy);

    if (hit !== null && !revealedCells.has(hit)) {
        selectedCell = (selectedCell === hit) ? null : hit;
    } else if (hit === null) {
        selectedCell = null;
    }

    updateSpotBtn();
    render();
});

canvas.addEventListener('mousemove', (e) => {
    const { cx, cy } = mousePos(e);
    const hit = hitTest(cx, cy);
    const tip = document.getElementById('tooltip');
    if (hit !== null && !revealedCells.has(hit)) {
        tip.style.display = 'block';
        tip.style.left = (e.clientX + 14) + 'px';
        tip.style.top  = (e.clientY + 14) + 'px';
        tip.textContent = `ZELLE ${hit + 1}`;
    } else {
        tip.style.display = 'none';
    }
});
canvas.addEventListener('mouseleave', () => {
    document.getElementById('tooltip').style.display = 'none';
});

function mousePos(e) {
    const rect = canvas.getBoundingClientRect();
    return {
        cx: (e.clientX - rect.left) * (canvas.width  / rect.width),
        cy: (e.clientY - rect.top)  * (canvas.height / rect.height)
    };
}

function hitTest(mx, my) {
    for (let i = cellPositions.length - 1; i >= 0; i--) {
        const { x, y, r } = cellPositions[i];
        if (Math.hypot(mx - x, my - y) <= r * 2.4) return i;
    }
    return null;
}

async function handleSpot() {
    if (selectedCell === null || gameOver) return;

    const cellIndex  = selectedCell;
    selectedCell     = null;
    document.getElementById('spotBtn').disabled = true;

    let found, temp;

    if (demoMode) {
        revealedCells.add(cellIndex);
        steps++;
        found = (cellIndex === survivorCell);
        temp  = found
            ? (36.2 + Math.random() * 1.1).toFixed(1)
            : (14   + Math.random() * 7).toFixed(1);
    } else {
        try {
            const result = await apiScan(cellIndex);
            found = result.found_survivor;
            temp  = result.temperature.toFixed(1);
            revealedCells = new Set(result.revealed_cells ?? []);
            const gs = result.state;
            if (gs) {
                steps = humanPlayerNumber === 2
                    ? (gs.grover_rounds_completed ?? 0)
                    : (gs.human_rounds_completed ?? 0);
            }
        } catch {
            selectedCell = cellIndex;
            updateSpotBtn();
            render();
            alert('Du bist gerade nicht am Zug.');
            return;
        }
    }

    const pos = cellPositions[cellIndex];
    scanLog.push({
        step: steps,
        cell: cellIndex + 1,
        x: pos.x.toFixed(2),
        y: pos.y.toFixed(2),
        temp,
        found
    });

    const signalText = found ? `ZELLE ${cellIndex + 1}` : `KEIN ÜBERLEBENDER`;
    document.getElementById('last-signal-name').textContent = signalText;
    document.getElementById('last-temp').textContent        = `${temp} °C`;
    document.getElementById('zug-display').textContent      = steps;

    if (found) {
        foundCount++;
        humanFoundCell = cellIndex;
        document.getElementById('found-count').textContent = foundCount;
    }

    updateStepBar();
    render();
    drawRevealedTemp(cellIndex, temp, found);

    if (found) {
        canHumanPlay = false;
        updateSpotBtn();
        document.getElementById('grover-found-banner').style.display = 'none';

        // Icon 1.8s sichtbar lassen, dann survivor-wait-overlay zeigen
        setTimeout(() => {
            document.getElementById('survivor-cell-info').textContent =
                `ZELLE ${cellIndex + 1} GEFUNDEN`;
            document.getElementById('survivor-wait-overlay').classList.add('show');
        }, 1800);

        return;
    }

    if (steps >= maxSteps) {
        canHumanPlay = false;
        updateSpotBtn();
    }
}

function drawRevealedTemp(cellIdx, temp, found) {
    const { x, y, r } = cellPositions[cellIdx];
    ctx.font = 'bold 13px Courier New';
    ctx.fillStyle = found ? '#00ff88' : '#ff4444';
    const label = `${temp} °C`;
    const tw = ctx.measureText(label).width;
    ctx.fillText(label, x - tw / 2, y - r * 1.6 - 6);
}

function updateStepBar() {
    const pct = Math.min(steps / maxSteps, 1);
    const bar = document.getElementById('stepBar');
   
    const fillPct = (1 - pct) * 100;
    bar.style.height = `calc(${fillPct}% - ${Math.round(fillPct / 100 * 12)}px)`;
    bar.style.background =
        pct > 0.8 ? '#cc3300' :
        pct > 0.5 ? '#ccaa00' :
                    '#b6ccd7';
    document.getElementById('stepCounter').innerHTML =
        `${steps}/<span id="maxStepsDisplay">${maxSteps}</span>`;
}


function endGame(won) {
    gameOver = true;
    clearInterval(pollInterval);

    document.getElementById('grover-found-banner').style.display = 'none';
    document.getElementById('wait-overlay').classList.add('hidden');
    // Hide survivor-wait overlay if visible
    document.getElementById('survivor-wait-overlay').classList.remove('show');

    const title = document.getElementById('end-title');
    title.textContent = won ? 'MISSION ERFÜLLT' : 'MISSION FEHLGESCHLAGEN';
    title.style.color = won ? '#00ff88' : '#ff4444';

    document.getElementById('rpt-found').textContent = won ? 'JA' : 'NEIN';
    document.getElementById('rpt-found').style.color = won ? '#00ff88' : '#ff4444';
    const humanStepsEl = document.getElementById('rpt-human-steps');
    if (humanStepsEl) {
        humanStepsEl.textContent = won ? `${steps} ZÜGE` : 'NICHT GEFUNDEN';
        humanStepsEl.style.color = won ? '#00ff88' : '#ff4444';
    }

    const groverSteps = (groverRoundsCompleted !== null && groverRoundsCompleted !== undefined)
        ? groverRoundsCompleted + ' ZÜGE'
        : '? ZÜGE';

    const player1Label = document.getElementById('rpt-player1-label');
    const player2Label = document.getElementById('rpt-player2-label');
    if (player1Label && player2Label) {
        if (currentGameMode === 'manual') {
            player1Label.textContent = 'KLASSISCH 1';
            player2Label.textContent = 'KLASSISCH 2';
        } else {
            player1Label.textContent = 'KLASSISCH';
            player2Label.textContent = 'GROVER';
        }
    }

    document.getElementById('rpt-classic-zuege').textContent = won ? `${steps} ZÜGE` : 'NICHT GEFUNDEN';
    document.getElementById('rpt-grover-zuege').textContent  = groverSteps;

    if (!won) {
        revealedCells.add(survivorCell);
        render();
    }

    document.getElementById('end-overlay').classList.add('show');
}

function showHelp() {
    alert(
        'MANUELLER MODUS\n\n' +
        'Klicke auf ein orange Signal um es auszuwählen,\n' +
        'dann "SPOT AUFDECKEN" drücken.\n\n' +
        'Hohe Temperatur (>36°C) = Überlebender!\n' +
        'Niedrige Temperatur = falsches Signal.\n\n' +
        `Du hast nur ${maxSteps} Versuche!`
    );
}

function restartGame() {
    knownGameId = null;
    updateStepBar();
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    boot();
}

function goBack() {
    fetch('/reset', { method: 'POST' })
        .catch(() => {})
        .finally(() => { window.location.href = 'start.html'; });
}

window.addEventListener('resize', () => { resizeCanvas(); });
watchCanvasSize();
boot();


const anleitungOeffnen = function() {
    document.getElementById("anleitung-screen").style.display = "block";
    if (typeof anleitungZurErstenSeite === "function") anleitungZurErstenSeite();
}

const anleitungSchliessen = function() {
    document.getElementById("anleitung-screen").style.display = "none";
}
