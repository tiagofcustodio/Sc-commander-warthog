/* ==========================================================================
   STAR CITIZEN WARTHOG COMMANDER PRO - CLIENT SCRIPT & AUDIO ENGINE
   ========================================================================== */

let ws = null;
let audioEnabled = true;
let audioCtx = null;
let currentProfile = 'combat';
let currentCurveType = 'expo';
let currentExponent = 1.8;
let currentDeadzone = 0.12;

// Initialize Web Audio Context
function initAudio() {
  if (!audioCtx) {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (AudioContext) {
      audioCtx = new AudioContext();
    }
  }
}

// Cockpit sound generator using Web Audio API
function playCockpitSound(type = 'click') {
  if (!audioEnabled || !audioCtx) return;
  if (audioCtx.state === 'suspended') {
    audioCtx.resume();
  }

  const now = audioCtx.currentTime;

  if (type === 'click') {
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = 'triangle';
    osc.frequency.setValueAtTime(600, now);
    osc.frequency.exponentialRampToValueAtTime(120, now + 0.04);
    gain.gain.setValueAtTime(0.15, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.04);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start(now);
    osc.stop(now + 0.04);

  } else if (type === 'chirp') {
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(880, now);
    osc.frequency.setValueAtTime(1760, now + 0.05);
    gain.gain.setValueAtTime(0.12, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.12);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start(now);
    osc.stop(now + 0.12);

  } else if (type === 'afterburner') {
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(90, now);
    osc.frequency.exponentialRampToValueAtTime(160, now + 0.15);
    gain.gain.setValueAtTime(0.2, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start(now);
    osc.stop(now + 0.25);

  } else if (type === 'alert') {
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(440, now);
    osc.frequency.setValueAtTime(330, now + 0.08);
    gain.gain.setValueAtTime(0.1, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.18);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start(now);
    osc.stop(now + 0.18);
  }
}

function toggleAudio() {
  audioEnabled = !audioEnabled;
  const btn = document.getElementById('btn-sound');
  btn.textContent = audioEnabled ? 'FX: ATIVO' : 'FX: MUDO';
  btn.style.borderColor = audioEnabled ? 'rgba(0, 210, 255, 0.3)' : 'rgba(255, 51, 85, 0.3)';
  if (audioEnabled) {
    initAudio();
    playCockpitSound('chirp');
  }
}

// Tab Switching & Tactical Topbar Sync
const MODULE_META = {
  dashboard:  { code: 'MOD // 01', title: 'Cockpit & Telemetria em Tempo Real' },
  cheatsheet: { code: 'MOD // 02', title: 'Mapa Visual HOTAS (Manche A-10C + Manete Dupla)' },
  matrix:     { code: 'MOD // 03', title: 'Matriz de Teclas & Mapeamentos DirectInput' },
  axes:       { code: 'MOD // 04', title: 'Curvas de Resposta, Slew & Calibração' },
  doctor:     { code: 'MOD // 05', title: 'Auto-Doctor XML & Diagnóstico Star Citizen' },
  macros:     { code: 'MOD // 06', title: 'Macros Multi-Passo & Computador de Bordo AI' },
  system:     { code: 'MOD // 07', title: 'Hardware Multi-Thrustmaster & GitHub Auto-Updater' }
};

function switchTab(tabId) {
  initAudio();
  playCockpitSound('click');
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));

  const activeBtn = Array.from(document.querySelectorAll('.tab-btn')).find(b => (b.getAttribute('onclick') || '').includes(tabId));
  if (activeBtn) activeBtn.classList.add('active');

  const targetTab = document.getElementById('tab-' + tabId);
  if (targetTab) targetTab.classList.add('active');

  const meta = MODULE_META[tabId];
  if (meta) {
    const codeEl = document.getElementById('topbar-module-code');
    const titleEl = document.getElementById('topbar-module-title');
    if (codeEl) codeEl.textContent = meta.code;
    if (titleEl) titleEl.textContent = meta.title;
  }

  if (tabId === 'axes') {
    drawCurveCanvas();
  }
}

// Cockpit Deck Section Sub-Filter
function filterCockpitDeck(section, btnEl) {
  initAudio();
  playCockpitSound('click');
  document.querySelectorAll('.deck-filter-btn').forEach(b => b.classList.remove('active'));
  if (btnEl) btnEl.classList.add('active');

  const baseGrp = document.getElementById('deck-group-base');
  const gripsGrp = document.getElementById('deck-group-grips');
  const stickGrp = document.getElementById('deck-group-stick');

  if (baseGrp) baseGrp.classList.toggle('hidden-deck', section !== 'all' && section !== 'base');
  if (gripsGrp) gripsGrp.classList.toggle('hidden-deck', section !== 'all' && section !== 'grips');
  if (stickGrp) stickGrp.classList.toggle('hidden-deck', section !== 'all' && section !== 'stick');
}

const BASE_MAPPINGS_JS = {
  "APU_ON": { "key": "R", "modifiers": ["ALT"], "desc": "Flight Ready - Ligar Tudo (Alt+R)", "hold_ms": 60 },
  "APU_OFF": { "key": "U", "modifiers": [], "desc": "Power Off - Desligar Sistemas (U)", "hold_ms": 60 },
  "EAC_ON": { "key": "B", "modifiers": [], "desc": "Alternar Master Mode (SCM / NAV - B)", "hold_ms": 300 },
  "EAC_OFF": { "key": "B", "modifiers": [], "desc": "Regressar a Modo Combate SCM (B)", "hold_ms": 300 },
  "RDR_ALTM_ON": { "key": "N", "modifiers": [], "desc": "Recolher Trem de Aterragem (N)", "hold_ms": 60 },
  "RDR_ALTM_OFF": { "key": "N", "modifiers": [], "desc": "Baixar Trem de Aterragem (N)", "hold_ms": 60 },
  "FUEL_L_ON": { "key": "I", "modifiers": [], "desc": "Ligar Propulsores (I)", "hold_ms": 60 },
  "FUEL_L_OFF": { "key": "I", "modifiers": [], "desc": "Desligar Propulsores (I)", "hold_ms": 60 },
  "FUEL_R_ON": { "key": "P", "modifiers": [], "desc": "Ligar Energia das Armas (P)", "hold_ms": 60 },
  "FUEL_R_OFF": { "key": "P", "modifiers": [], "desc": "Desligar Energia das Armas (P)", "hold_ms": 60 },
  "LDGHORN_PRESS": { "key": "N", "modifiers": ["ALT"], "desc": "Chamar ATC / Pedir Aterragem (Alt+N)", "hold_ms": 80 },
  "AP_ENGAGE_PRESS": { "key": "N", "modifiers": ["ALT"], "desc": "Chamar ATC / Aterragem (Alt+N)", "hold_ms": 80 },
  "FLAPS_UP": { "key": "C", "modifiers": [], "desc": "Cruise Control ON/OFF (C)", "hold_ms": 60 },
  "FLAPS_MID": { "key": "K", "modifiers": [], "desc": "Sair de VTOL -> Voo Normal (K)", "hold_ms": 60 },
  "FLAPS_DN": { "key": "K", "modifiers": [], "desc": "Ativar Modo VTOL / Hover (K)", "hold_ms": 60 },
  "PINKY_FWD": { "key": "L", "modifiers": [], "desc": "Faróis Exteriores ON (L)", "hold_ms": 60 },
  "PINKY_MID": { "key": "L", "modifiers": [], "desc": "Faróis Exteriores OFF (L)", "hold_ms": 60 },
  "PINKY_AFT": { "key": "L", "modifiers": [], "desc": "Alternar Luzes / Cabine (L)", "hold_ms": 60 },
  "BOAT_FWD": { "key": "B", "modifiers": [], "desc": "Quantum Mode / Spool (B)", "hold_ms": 60 },
  "BOAT_MID": { "key": "", "modifiers": [], "desc": "Boat Centro (Neutro)", "hold_ms": 0 },
  "BOAT_AFT": { "key": "B", "modifiers": [], "desc": "Regressar SCM / Cancelar Quantum (B)", "hold_ms": 60 },
  "SPDBRK_FWD": { "key": "C", "modifiers": [], "desc": "Cruise Control Toggle (C)", "hold_ms": 60 },
  "SPDBRK_MID": { "key": "", "modifiers": [], "desc": "Speed Brake Neutro", "hold_ms": 0 },
  "SPDBRK_AFT": { "key": "X", "modifiers": [], "desc": "Space Brake / Travão Espacial (X)", "hold_ms": 80 },
  "ENG_L_IGN": { "key": "X", "modifiers": ["ALT"], "desc": "Limpar Visor do Capacete (Alt+X)", "hold_ms": 60 },
  "ENG_L_NORM": { "key": "I", "modifiers": [], "desc": "Propulsores Normais ON (I)", "hold_ms": 60 },
  "ENG_L_MOTOR": { "key": "I", "modifiers": [], "desc": "Cortar Propulsores OFF (I)", "hold_ms": 60 },
  "ENG_R_IGN": { "key": "P", "modifiers": [], "desc": "Alternar Energia das Armas (P)", "hold_ms": 60 },
  "ENG_R_NORM": { "key": "P", "modifiers": [], "desc": "Armas Normais ON (P)", "hold_ms": 60 },
  "ENG_R_MOTOR": { "key": "P", "modifiers": [], "desc": "Cortar Energia das Armas OFF (P)", "hold_ms": 60 },
  "AP_PATH": { "key": "K", "modifiers": ["ALT"], "desc": "Abrir Todas as Portas / Rampas (Alt+K)", "hold_ms": 60 },
  "AP_MID": { "key": "O", "modifiers": ["ALT"], "desc": "Fechar Todas as Portas (Alt+O)", "hold_ms": 60 },
  "AP_ALT": { "key": "L", "modifiers": ["ALT"], "desc": "Trancar Todas as Portas (Alt+L)", "hold_ms": 60 },
  "IDLE_L_OFF": { "key": "I", "modifiers": [], "desc": "Corte Físico Motor Esq. (Cutoff OFF -> I)", "hold_ms": 60 },
  "IDLE_L_IDLE": { "key": "I", "modifiers": [], "desc": "Arranque Motor Esq. (Saída de Cutoff -> I)", "hold_ms": 60 },
  "IDLE_R_OFF": { "key": "I", "modifiers": [], "desc": "Corte Físico Motor Dir. (Cutoff OFF -> I)", "hold_ms": 60 },
  "IDLE_R_IDLE": { "key": "I", "modifiers": [], "desc": "Arranque Motor Dir. (Saída de Cutoff -> I)", "hold_ms": 60 },
  "CHINA_FWD_PRESS": { "key": "LSHIFT", "modifiers": [], "desc": "Boost / Pós-Combustão (Left Shift)", "hold_ms": 100 },
  "CHINA_AFT_PRESS": { "key": "S", "modifiers": [], "desc": "Inverter Propulsão / Recuar (S)", "hold_ms": 80 },
  "MIC_UP_PRESS": { "key": "V", "modifiers": [], "desc": "Modo Scan (V)", "hold_ms": 60 },
  "MIC_RIGHT_PRESS": { "key": "F4", "modifiers": [], "desc": "Câmara Externa 3ª Pessoa (F4)", "hold_ms": 60 },
  "MIC_DOWN_PRESS": { "key": "M", "modifiers": [], "desc": "Modo Mineração / Salvage (M)", "hold_ms": 60 },
  "MIC_LEFT_PRESS": { "key": "", "modifiers": [], "desc": "Desativado (Sem Z / Shift+Z)", "hold_ms": 0 },
  "MIC_PUSH_PRESS": { "key": "NUM_ADD", "modifiers": [], "desc": "Push-to-Talk VOIP (Num +)", "hold_ms": 60 },
  "SLEW_PUSH_PRESS": { "key": "F", "modifiers": [], "desc": "Interação Rápida / Match Vel (F)", "hold_ms": 60 },
  "LTB_PRESS": { "key": "R", "modifiers": ["ALT"], "desc": "Flight Ready Rápido (Alt+R)", "hold_ms": 60 },
  "VISOR_WIPE_PRESS": { "key": "X", "modifiers": ["ALT"], "desc": "Limpar Visor do Capacete (Alt+X)", "hold_ms": 60 },

  // Coolie Hat da Manete (POV 1)
  "COOLIE_UP": { "key": "", "modifiers": [], "desc": "Coolie Hat Cima: Strafe Up (Nativo XML)", "hold_ms": 60 },
  "COOLIE_DOWN": { "key": "", "modifiers": [], "desc": "Coolie Hat Baixo: Strafe Down (Nativo XML)", "hold_ms": 60 },
  "COOLIE_LEFT": { "key": "", "modifiers": [], "desc": "Coolie Hat Esq.: Strafe Left (Nativo XML)", "hold_ms": 60 },
  "COOLIE_RIGHT": { "key": "", "modifiers": [], "desc": "Coolie Hat Dir.: Strafe Right (Nativo XML)", "hold_ms": 60 },

  // Trim Hat do Manche (POV 1 - Capacitores)
  "TRIM_HAT_UP": { "key": "F6", "modifiers": [], "desc": "Capacitor: Energia Máxima aos Propulsores (F6)", "hold_ms": 60 },
  "TRIM_HAT_RIGHT": { "key": "F7", "modifiers": [], "desc": "Capacitor: Energia Máxima aos Escudos (F7)", "hold_ms": 60 },
  "TRIM_HAT_LEFT": { "key": "F5", "modifiers": [], "desc": "Capacitor: Energia Máxima às Armas (F5)", "hold_ms": 60 },
  "TRIM_HAT_DOWN": { "key": "F8", "modifiers": [], "desc": "Capacitor: Equilibrar Energia (F8)", "hold_ms": 60 },

  // Botões Físicos do Manche A-10C (BTN 01 a BTN 19)
  "STICK_BTN_1": { "key": "", "modifiers": [], "desc": "TG1 Gatilho Etapa 1: Armas Grupo 1 (Nativo XML)", "hold_ms": 60 },
  "STICK_BTN_2": { "key": "", "modifiers": [], "desc": "S2 Weapon Release: Lançar Míssil / Laser (Nativo XML)", "hold_ms": 60 },
  "STICK_BTN_3": { "key": "", "modifiers": [], "desc": "S3 Nosewheel Steering: Modo Gimbal / Match Vel (Nativo XML)", "hold_ms": 60 },
  "STICK_BTN_5": { "key": "B", "modifiers": [], "desc": "S1 Master Mode: Alternar SCM / NAV (B)", "hold_ms": 60 },
  "STICK_BTN_6": { "key": "", "modifiers": [], "desc": "TG2 Gatilho Etapa 2: Armas Grupo 2 (Nativo XML)", "hold_ms": 60 },
  "STICK_BTN_7": { "key": "T", "modifiers": [], "desc": "TMS Cima (BTN 07): Selecionar Alvo na Mira (T)", "hold_ms": 60 },
  "STICK_BTN_8": { "key": "5", "modifiers": [], "desc": "TMS Direita (BTN 08): Próximo Alvo Hostil (5)", "hold_ms": 60 },
  "STICK_BTN_9": { "key": "4", "modifiers": [], "desc": "TMS Baixo (BTN 09): Alvo Hostil Mais Próximo (4)", "hold_ms": 60 },
  "STICK_BTN_10": { "key": "", "modifiers": [], "desc": "TMS Esquerda (BTN 10): Fixar Alvo / Hostil Ant. (Nativo XML)", "hold_ms": 60 },
  "STICK_BTN_11": { "key": "TAB", "modifiers": [], "desc": "DMS Cima (BTN 11): Disparar Ping Radar (Tab)", "hold_ms": 60 },
  "STICK_BTN_12": { "key": "7", "modifiers": [], "desc": "DMS Direita (BTN 12): Próximo Todos os Alvos (7)", "hold_ms": 60 },
  "STICK_BTN_13": { "key": "NUM5", "modifiers": [], "desc": "DMS Baixo (BTN 13): Equilibrar Escudos (Num 5)", "hold_ms": 60 },
  "STICK_BTN_14": { "key": "", "modifiers": [], "desc": "DMS Esquerda (BTN 14): Alvo Anterior (Nativo XML)", "hold_ms": 60 },
  "STICK_BTN_15": { "key": "J", "modifiers": [], "desc": "CMS Cima (BTN 15): Lançar Ruído / Chaff (J)", "hold_ms": 60 },
  "STICK_BTN_16": { "key": "", "modifiers": [], "desc": "CMS Direita (BTN 16): +Salva Decoy / Próx. Míssil (Nativo XML)", "hold_ms": 60 },
  "STICK_BTN_17": { "key": "H", "modifiers": [], "desc": "CMS Baixo (BTN 17): Lançar Decoy / Flare (H)", "hold_ms": 60 },
  "STICK_BTN_18": { "key": "", "modifiers": [], "desc": "CMS Esquerda (BTN 18): -Salva Decoy / Míssil Ant. (Nativo XML)", "hold_ms": 60 },
  "STICK_BTN_19": { "key": "", "modifiers": [], "desc": "CMS Push (BTN 19): Salva de Pânico / +Mísseis (Nativo XML)", "hold_ms": 60 },

  // Camada Shift do Manche (S4 Pinky Lever BTN 04 + Botão)
  "S2_SHIFT": { "key": "J", "modifiers": ["ALT"], "desc": "[S4+BTN 02] Ejetar Carga Volátil (Alt+J)", "hold_ms": 80 },
  "S1_SHIFT": { "key": "K", "modifiers": [], "desc": "[S4+BTN 05] Alternar Modo VTOL (K)", "hold_ms": 60 },
  "TMS_UP_SHIFT": { "key": "8", "modifiers": [], "desc": "[S4+BTN 07] Sub-Target: Próximo Sub-componente (8)", "hold_ms": 60 },
  "TMS_RIGHT_SHIFT": { "key": "6", "modifiers": [], "desc": "[S4+BTN 08] Selecionar Próximo Aliado (6)", "hold_ms": 60 },
  "TMS_DOWN_SHIFT": { "key": "8", "modifiers": ["ALT"], "desc": "[S4+BTN 09] Reset Sub-componente (Alt+8)", "hold_ms": 60 },
  "DMS_UP_SHIFT": { "key": "NUM8", "modifiers": [], "desc": "[S4+BTN 11] Reforçar Escudo Frontal (Num 8)", "hold_ms": 60 },
  "DMS_RIGHT_SHIFT": { "key": "NUM6", "modifiers": [], "desc": "[S4+BTN 12] Reforçar Escudo Direito (Num 6)", "hold_ms": 60 },
  "DMS_DOWN_SHIFT": { "key": "NUM2", "modifiers": [], "desc": "[S4+BTN 13] Reforçar Escudo Traseiro (Num 2)", "hold_ms": 60 },
  "DMS_LEFT_SHIFT": { "key": "NUM4", "modifiers": [], "desc": "[S4+BTN 14] Reforçar Escudo Esquerdo (Num 4)", "hold_ms": 60 },
  "CMS_RIGHT_SHIFT": { "key": "G", "modifiers": [], "desc": "[S4+BTN 16] Aumentar Mísseis Armados (G)", "hold_ms": 60 },
  "CMS_LEFT_SHIFT": { "key": "G", "modifiers": ["ALT"], "desc": "[S4+BTN 18] Reset Mísseis Armados (Alt+G)", "hold_ms": 60 }
};

const CLIENT_PROFILES = {
  combat: {
    id: 'combat',
    name: '⚔️ Combate / Dogfight',
    description: 'Otimizado para Master Modes (SCM/NAV), seleção rápida de alvos e contramedidas em pânico.',
    icon: '⚔️',
    borderColor: '#00d2ff',
    afterburner_auto_boost: false,
    split_throttle_mode: 'speed_limiter',
    slider_label: 'LIMITADOR VELOC. (Slider 1):',
    curve_type: 'expo',
    curve_exponent: 2.0,
    highlights: 'EAC: Master Mode (B) • SPDBRK: Cruise(C)/Travão(X) • BOAT: Quantum(B)/SCM • Boost: China FWD (B11)',
    ui_cards: {
      eac_sub: 'Master Mode SCM / NAV',
      eac_tag: 'ARM/OFF: Alternar SCM/NAV (B)',
      spdbrk_sub: 'Cruise (07) / Space Brake (08)',
      spdbrk_tag_a: '07: Cruise (C)',
      spdbrk_tag_b: '08: Travão (X)',
      boat_sub: 'Quantum NAV (09) / SCM (10)',
      boat_tag_a: '09: Quantum (B)',
      boat_tag_b: '10: Armas SCM',
      china_sub: 'Boost (11) / Recuar (12)',
      china_tag_a: '11: Boost (LShift)',
      china_tag_b: '12: Recuar (S)',
      flaps_sub: 'UP (Cruise) / MVR / DN (VTOL)',
      flaps_tag_a: '22: Cruise (C)',
      flaps_tag_b: '23: VTOL (K)'
    },
    mappings: { ...BASE_MAPPINGS_JS }
  },
  mining: {
    id: 'mining',
    name: '⛏️ Mineração & Salvage',
    description: 'Manete esquerda e Slider dedicados à potência do laser de mineração, ajuste de raio trator, scanner de rochas e consumíveis.',
    icon: '⛏️',
    borderColor: '#ffaa00',
    afterburner_auto_boost: false,
    split_throttle_mode: 'mining_laser',
    slider_label: 'POTÊNCIA LASER (Slider 1):',
    curve_type: 'linear',
    curve_exponent: 1.0,
    highlights: 'EAC: Modo Mineração(M) • SPDBRK: Potência/Trator(Wheel) • BOAT: Módulos(Alt+1/2) • CHINA: Ping(Tab)/Jettison',
    ui_cards: {
      eac_sub: 'Modo Mineração / Salvage',
      eac_tag: 'ARM/OFF: Laser Mineração (M)',
      spdbrk_sub: 'Potência Laser / Raio Trator',
      spdbrk_tag_a: '07: +Laser (WheelUp)',
      spdbrk_tag_b: '08: -Laser (WheelDn)',
      boat_sub: 'Consumíveis Mineração 1 & 2',
      boat_tag_a: '09: Módulo 1 (Alt+1)',
      boat_tag_b: '10: Módulo 2 (Alt+2)',
      china_sub: 'Scanner Ping (11) / Ejetar (12)',
      china_tag_a: '11: Ping Rochas (Tab)',
      china_tag_b: '12: Ejetar Carga (Alt+J)',
      flaps_sub: 'Cruise (22) / Hover Estável (23)',
      flaps_tag_a: '22: Cruise (C)',
      flaps_tag_b: '23: Hover VTOL (K)'
    },
    mappings: {
      ...BASE_MAPPINGS_JS,
      "EAC_ON": { "key": "M", "modifiers": [], "desc": "Ativar Modo Mineração / Salvage (M)", "hold_ms": 60 },
      "EAC_OFF": { "key": "M", "modifiers": [], "desc": "Sair do Modo Mineração (M)", "hold_ms": 60 },
      "BOAT_FWD": { "key": "1", "modifiers": ["ALT"], "desc": "Ativar Consumível de Mineração 1 (Alt+1)", "hold_ms": 60 },
      "BOAT_AFT": { "key": "2", "modifiers": ["ALT"], "desc": "Ativar Consumível de Mineração 2 (Alt+2)", "hold_ms": 60 },
      "SPDBRK_FWD": { "key": "MWHEEL_UP", "modifiers": [], "desc": "Aumentar Potência Laser / Distância Trator (Wheel Up)", "hold_ms": 60 },
      "SPDBRK_AFT": { "key": "MWHEEL_DOWN", "modifiers": [], "desc": "Diminuir Potência Laser / Distância Trator (Wheel Down)", "hold_ms": 60 },
      "CHINA_FWD_PRESS": { "key": "TAB", "modifiers": [], "desc": "Disparar Ping de Scanner de Rochas (Tab)", "hold_ms": 80 },
      "CHINA_AFT_PRESS": { "key": "J", "modifiers": ["ALT"], "desc": "Ejetar Carga Instável Quantanium (Alt+J)", "hold_ms": 80 }
    }
  },
  cargo: {
    id: 'cargo',
    name: '📦 Carga & Transporte',
    description: 'Manobras suaves em hangar sem boost acidental, chamada rápida a torres ATC, controlo de portas/rampas e VTOL pesado.',
    icon: '📦',
    borderColor: '#00e676',
    afterburner_auto_boost: false,
    split_throttle_mode: 'speed_limiter',
    slider_label: 'LIMITADOR DOCAGEM (Slider 1):',
    curve_type: 'expo',
    curve_exponent: 1.6,
    highlights: 'EAC: Portas/Rampas(Alt+K) • BOAT: Quantum(B)/Torre ATC(Alt+N) • B15: AutoLand(N) • Auto-Boost: OFF',
    ui_cards: {
      eac_sub: 'Rampas & Portas Exteriores',
      eac_tag: 'ARM/OFF: Abrir/Fechar (Alt+K)',
      spdbrk_sub: 'Cruise Rota (07) / Travão (08)',
      spdbrk_tag_a: '07: Cruise (C)',
      spdbrk_tag_b: '08: Travão (X)',
      boat_sub: 'Quantum (09) / Chamar ATC (10)',
      boat_tag_a: '09: Quantum (B)',
      boat_tag_b: '10: Torre ATC (Alt+N)',
      china_sub: 'Boost Suave (11) / Recuar (12)',
      china_tag_a: '11: Boost (LShift)',
      china_tag_b: '12: Recuar (S)',
      flaps_sub: 'Cruise (22) / VTOL Carga (23)',
      flaps_tag_a: '22: Cruise (C)',
      flaps_tag_b: '23: VTOL Pesado (K)'
    },
    mappings: {
      ...BASE_MAPPINGS_JS,
      "EAC_ON": { "key": "K", "modifiers": ["ALT"], "desc": "Abrir/Fechar Rampas e Portas Exteriores (Alt+K)", "hold_ms": 60 },
      "EAC_OFF": { "key": "K", "modifiers": ["ALT"], "desc": "Fechar Rampas e Portas Exteriores (Alt+K)", "hold_ms": 60 },
      "BOAT_FWD": { "key": "B", "modifiers": [], "desc": "Modo Quantum / Spool de Rota (B)", "hold_ms": 60 },
      "BOAT_AFT": { "key": "N", "modifiers": ["ALT"], "desc": "Chamar Torre ATC / Hangar (Alt+N)", "hold_ms": 80 },
      "LTB_PRESS": { "key": "N", "modifiers": [], "desc": "AutoLand / Aterragem Automática no Pad (Hold N)", "hold_ms": 1200 }
    }
  },
  ground: {
    id: 'ground',
    name: '🚜 Veículos Terrestres',
    description: 'Controlo dedicado para Rovers e Tanques (Ursa, Nova Tonk, Spartan, Cyclone) com travão de mão (Space), faróis e torre.',
    icon: '🚜',
    borderColor: '#ff7733',
    afterburner_auto_boost: false,
    split_throttle_mode: 'speed_limiter',
    slider_label: 'LIMITADOR TERRESTRE (Slider 1):',
    curve_type: 'expo',
    curve_exponent: 1.5,
    highlights: 'EAC: Faróis Veículo(L) • SPDBRK AFT: Travão de Mão(Space) • BOAT: Centrar Torre(R)/Scan(V) • CHINA: Boost/Ré',
    ui_cards: {
      eac_sub: 'Faróis do Veículo Terrestre',
      eac_tag: 'ARM/OFF: Faróis ON/OFF (L)',
      spdbrk_sub: 'Cruise (07) / Travão de Mão (08)',
      spdbrk_tag_a: '07: Cruise (C)',
      spdbrk_tag_b: '08: Travão Mão (Space)',
      boat_sub: 'Centrar Torre (09) / Scan (10)',
      boat_tag_a: '09: Centrar Torre (R)',
      boat_tag_b: '10: Modo Scan (V)',
      china_sub: 'Boost Rover (11) / Marcha-Atrás (12)',
      china_tag_a: '11: Turbo (LShift)',
      china_tag_b: '12: Marcha-Atrás (S)',
      flaps_sub: 'Motor ON (22) / Sistemas OFF (23)',
      flaps_tag_a: '22: Motor ON (I)',
      flaps_tag_b: '23: Power OFF (U)'
    },
    mappings: {
      ...BASE_MAPPINGS_JS,
      "SPDBRK_FWD": { "key": "C", "modifiers": [], "desc": "Cruise / Marcha Constante Terrestre (C)", "hold_ms": 60 },
      "SPDBRK_AFT": { "key": "SPACE", "modifiers": [], "desc": "Travão de Mão Terrestre / Paragem (Space)", "hold_ms": 80 },
      "EAC_ON": { "key": "L", "modifiers": [], "desc": "Ligar Faróis do Veículo Terrestre (L)", "hold_ms": 60 },
      "EAC_OFF": { "key": "L", "modifiers": [], "desc": "Desligar Faróis do Veículo Terrestre (L)", "hold_ms": 60 },
      "BOAT_FWD": { "key": "R", "modifiers": [], "desc": "Centrar Torre do Tanque / Gimbal Lock (R)", "hold_ms": 60 },
      "BOAT_AFT": { "key": "V", "modifiers": [], "desc": "Modo Scan Terrestre (V)", "hold_ms": 60 },
      "FLAPS_UP": { "key": "I", "modifiers": [], "desc": "Ligar Motor do Veículo (I)", "hold_ms": 60 },
      "FLAPS_DN": { "key": "U", "modifiers": [], "desc": "Desligar Sistemas do Veículo (U)", "hold_ms": 60 }
    }
  }
};

// Profile Selection
function selectProfile(profileId) {
  initAudio();
  playCockpitSound('chirp');

  const localProf = CLIENT_PROFILES[profileId] || CLIENT_PROFILES.combat;
  applyProfileData(profileId, localProf);

  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'set_profile', profile: profileId }));
  } else {
    const nowStr = new Date().toLocaleTimeString('pt-PT', { hour12: false });
    appendLog(nowStr, `Perfil alterado para: ${localProf.name}`, `${localProf.icon} ${localProf.highlights}`);
  }
}

function rescanHardware() {
  initAudio();
  playCockpitSound('chirp');
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'rescan_hardware' }));
  }
}

// WebSocket Connection Management
function connectWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws`;

  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    console.log('[Warthog SC] WebSocket conectado.');
    appendLog('SISTEMA', 'Ponte WebSocket ligada ao motor DirectInput/WinMM.');
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handleServerMessage(data);
    } catch (e) {
      console.error('Erro ao analisar mensagem WS:', e);
    }
  };

  ws.onclose = () => {
    console.warn('[Warthog SC] Ligação perdida. A reconectar em 2s...');
    setTimeout(connectWebSocket, 2000);
  };
}

// Message Dispatcher
function handleServerMessage(data) {
  switch (data.type) {
    case 'device_status':
      updateHardwarePods(data.stick, data.throttle, data.sc_live, data.sc_running, data.stick_name, data.throttle_name);
      break;

    case 'cutoff_event':
      updateCutoffBadge(data.left, data.right);
      break;

    case 'hardware_catalog':
      window.cachedCatalog = data;
      renderFullHardwareCatalog(data);
      break;

    case 'shift_event':
      updateShiftLayer(data.active);
      break;

    case 'afterburner_event':
      updateAfterburnerState(data.active);
      break;

    case 'led_status':
      updateBaseLeds(data.leds, data.brightness);
      break;

    case 'profile_changed':
      applyProfileData(data.profile_id, data.profile_data);
      announceProfileVoice(data.profile_id);
      break;

    case 'switch_event':
      updateSwitchUI(data);
      highlightCatalogButton(data.device, data.button, data.is_down);
      logHardwareButton(data);
      break;

    case 'hat_event':
      updateHatUI(data);
      logHardwareHat(data);
      break;

    case 'initial_throttle_state':
      applyInitialThrottleState(data);
      break;

    case 'axis_event':
      updateAxisTelemetry(data);
      break;

    case 'log':
      appendLog(data.timestamp, data.text, data.key_hit);
      {
        let actId = data.action_id;
        if (!actId && data.text) {
          const m = data.text.match(/\[([A-Za-z0-9_:-]+)\]/);
          if (m) actId = m[1];
        }
        if (actId) triggerShipVoiceForAction(actId, data.desc || data.key_hit || '');
      }
      break;

    case 'macros_updated':
      cachedMacros = data.macros || {};
      renderMacrosList();
      populateMacroSelects();
      renderVisualMapping();
      renderMatrixRows();
      break;

    case 'voice_settings_updated':
      applyVoiceSettings(data.voice_settings);
      break;

    case 'hotas_info':
      applyHotasInfo(data);
      break;

    case 'update_status':
      applyUpdateStatus(data);
      break;

    case 'update_applied':
      onUpdateApplied(data);
      break;

    case 'axis_calibration_updated':
      applyAxisCalibrationData(data.axis_calibration);
      break;

    case 'update_status':
      renderGitHubUpdateStatus(data);
      break;

    case 'update_result':
      onGitHubUpdateResult(data);
      break;

    case 'diagnosis':
      renderDiagnosis(data);
      break;

    case 'config':
      populateConfig(data.config);
      break;

    case 'mapping_updated':
      onMappingUpdated(data);
      break;
  }
}

// Hardware & Process Status Pods
function updateHardwarePods(stick, throttle, scLive, scRunning, stickName, throttleName) {
  const podStick = document.getElementById('pod-stick');
  const podThrottle = document.getElementById('pod-throttle');
  const podScProc = document.getElementById('pod-sc-proc');
  const scProcText = document.getElementById('sc-proc-text');

  if (stick) {
    podStick.className = 'pod-badge online';
    podStick.title = stickName || 'Joystick - HOTAS Warthog Conectado';
  } else {
    podStick.className = 'pod-badge offline';
  }

  if (throttle) {
    podThrottle.className = 'pod-badge online';
    podThrottle.title = throttleName || 'Throttle - HOTAS Warthog Conectada';
  } else {
    podThrottle.className = 'pod-badge offline';
  }

  if (scRunning) {
    podScProc.className = 'pod-badge online';
    scProcText.textContent = 'SC.EXE: ONLINE';
  } else {
    podScProc.className = 'pod-badge offline';
    scProcText.textContent = 'SC.EXE: FECHADO';
  }
}

// Idle Cutoff Detent Status Badge (Buttons 29 & 30)
function updateCutoffBadge(cutLeft, cutRight) {
  const badge = document.getElementById('cutoff-badge');
  if (!badge) return;

  if (cutLeft || cutRight) {
    const which = (cutLeft && cutRight) ? 'AMBAS AS MANETES (BTN 29+30)' : (cutLeft ? 'MANETE ESQ. (BTN 29)' : 'MANETE DIR. (BTN 30)');
    badge.style.background = 'rgba(255, 170, 0, 0.18)';
    badge.style.color = 'var(--neon-amber)';
    badge.style.borderColor = 'rgba(255, 170, 0, 0.5)';
    badge.textContent = `⚠️ CUTOFF OFF ATIVO: ${which} — AVANCE PARA IDLE PARA LIBERTAR OS THRUSTERS`;
    playCockpitSound('alert');
  } else {
    badge.style.background = 'rgba(0, 230, 118, 0.12)';
    badge.style.color = 'var(--neon-green)';
    badge.style.borderColor = 'rgba(0, 230, 118, 0.35)';
    badge.textContent = '✅ DETENTOR IDLE: LIVRE (PROPULSORES ATIVOS)';
  }
}

function getThrottleButtonActionId(bNum) {
  const map = {
    1: 'SLEW_PUSH_PRESS', 2: 'MIC_PUSH_PRESS', 3: 'MIC_UP_PRESS', 4: 'MIC_RIGHT_PRESS',
    5: 'MIC_DOWN_PRESS', 6: 'MIC_LEFT_PRESS', 7: 'SPDBRK_FWD', 8: 'SPDBRK_AFT',
    9: 'BOAT_FWD', 10: 'BOAT_AFT', 11: 'CHINA_FWD_PRESS', 12: 'CHINA_AFT_PRESS',
    13: 'PINKY_FWD', 14: 'PINKY_AFT', 15: 'LTB_PRESS', 16: 'FUEL_L_ON',
    17: 'FUEL_R_ON', 18: 'ENG_L_MOTOR', 19: 'ENG_R_MOTOR', 20: 'APU_ON',
    21: 'LDGHORN_PRESS', 22: 'FLAPS_UP', 23: 'FLAPS_DN', 24: 'EAC_ON',
    25: 'RDR_ALTM_ON', 26: 'AP_ENGAGE_PRESS', 27: 'AP_PATH', 28: 'AP_ALT',
    29: 'IDLE_R_OFF', 30: 'IDLE_L_OFF', 31: 'ENG_L_IGN', 32: 'ENG_R_IGN'
  };
  return map[bNum] || null;
}

// Render Full Catalog of 19 Stick Buttons + 32 Throttle Buttons
function renderFullHardwareCatalog(cat) {
  const stickBox = document.getElementById('full-stick-catalog');
  const throttleBox = document.getElementById('full-throttle-catalog');

  if (stickBox && cat.stick_buttons) {
    let html = '';
    // Axes
    for (const [axId, ax] of Object.entries(cat.stick_axes || {})) {
      html += `
        <div class="callout-item" style="border-left-color: var(--neon-green);">
          <div class="callout-num" style="color: var(--neon-green); min-width: 65px;">${axId}</div>
          <div>
            <div class="callout-name">${ax.name} ➔ <code style="color:var(--neon-cyan)">${ax.sc_action}</code></div>
            <div class="callout-desc">${ax.desc}</div>
          </div>
        </div>`;
    }
    // Hats
    for (const [hatId, h] of Object.entries(cat.stick_hats || {})) {
      html += `
        <div class="callout-item" style="border-left-color: var(--neon-cyan); justify-content: space-between;">
          <div style="display: flex; gap: 12px; align-items: center;">
            <div class="callout-num" style="min-width: 65px;">POV</div>
            <div>
              <div class="callout-name">${h.name} (${h.key}) ➔ <code style="color:var(--neon-cyan)">${h.sc_action}</code></div>
              <div class="callout-desc">${h.desc}</div>
            </div>
          </div>
          <button class="edit-btn-pill" onclick="openKeyEditorModal('TRIM_HAT_UP')" title="Configurar teclas do Trim Hat">✏️</button>
        </div>`;
    }
    // All 19 Buttons
    for (const [bNum, b] of Object.entries(cat.stick_buttons)) {
      const isShiftBtn = (bNum === '4');
      const borderCol = isShiftBtn ? 'var(--neon-amber)' : 'rgba(0, 210, 255, 0.45)';
      const actId = `STICK_BTN_${bNum}`;
      html += `
        <div id="cat-stick-btn-${bNum}" class="callout-item" style="border-left-color: ${borderCol}; transition: all 0.15s; justify-content: space-between;">
          <div style="display: flex; gap: 12px; align-items: center;">
            <div class="callout-num" style="min-width: 65px; ${isShiftBtn ? 'color:var(--neon-amber)' : ''}">BTN ${String(bNum).padStart(2, '0')}</div>
            <div>
              <div class="callout-name">${b.name} ➔ <code style="color:var(--neon-cyan)">${b.sc_action}</code></div>
              <div class="callout-desc">${b.desc} <span style="color:var(--neon-amber)">| +Shift: ${b.shift_desc}</span></div>
            </div>
          </div>
          <button class="edit-btn-pill" onclick="openKeyEditorModal('${actId}')" title="Editar tecla deste botão do manche">✏️</button>
        </div>`;
    }
    stickBox.innerHTML = html;
  }

  if (throttleBox && cat.throttle_buttons) {
    let html = '';
    // Axes
    for (const [axId, ax] of Object.entries(cat.throttle_axes || {})) {
      html += `
        <div class="callout-item" style="border-left-color: var(--neon-green);">
          <div class="callout-num" style="color: var(--neon-green); min-width: 65px;">${axId}</div>
          <div>
            <div class="callout-name">${ax.name} ➔ <code style="color:var(--neon-cyan)">${ax.sc_action}</code></div>
            <div class="callout-desc">${ax.desc}</div>
          </div>
        </div>`;
    }
    // Hats
    for (const [hatId, h] of Object.entries(cat.throttle_hats || {})) {
      html += `
        <div class="callout-item" style="border-left-color: var(--neon-cyan); justify-content: space-between;">
          <div style="display: flex; gap: 12px; align-items: center;">
            <div class="callout-num" style="min-width: 65px;">HAT</div>
            <div>
              <div class="callout-name">${h.name} (${h.key}) ➔ <code style="color:var(--neon-cyan)">${h.sc_action}</code></div>
              <div class="callout-desc">${h.desc}</div>
            </div>
          </div>
          <button class="edit-btn-pill" onclick="openKeyEditorModal('COOLIE_UP')" title="Configurar Coolie Hat">✏️</button>
        </div>`;
    }
    // All 32 Buttons
    for (const [bNum, b] of Object.entries(cat.throttle_buttons)) {
      const isCutoff = (bNum === '29' || bNum === '30');
      const borderCol = isCutoff ? 'var(--neon-amber)' : 'rgba(0, 210, 255, 0.45)';
      const actId = getThrottleButtonActionId(Number(bNum));
      const editBtn = actId ? `<button class="edit-btn-pill" onclick="openKeyEditorModal('${actId}')" title="Editar tecla deste interruptor da manete">✏️</button>` : '';
      html += `
        <div id="cat-throttle-btn-${bNum}" class="callout-item" style="border-left-color: ${borderCol}; transition: all 0.15s; justify-content: space-between;">
          <div style="display: flex; gap: 12px; align-items: center;">
            <div class="callout-num" style="min-width: 65px; ${isCutoff ? 'color:var(--neon-amber)' : ''}">BTN ${String(bNum).padStart(2, '0')}</div>
            <div>
              <div class="callout-name">${b.name} ➔ <code style="color:var(--neon-cyan)">${b.sc_action || 'Interno'}</code></div>
              <div class="callout-desc">${b.desc}</div>
            </div>
          </div>
          ${editBtn}
        </div>`;
    }
    throttleBox.innerHTML = html;
  }
  renderVisualMapping();
}

// ==============================================================================
// VISUAL DUAL JOYSTICK MAPPING STUDIO (STICK & THROTTLE)
// ==============================================================================

const STICK_VISUAL_GROUPS = [
  {
    title: '🎯 Gatilhos & Alavancas Frontais',
    color: 'cyan',
    items: [
      { id: '1', actionId: 'STICK_BTN_1', num: 'BTN 01', name: 'TG1 (Gatilho 1º Estágio)', desc: 'Disparo Primário / Laser Mineração (Armas 1)' },
      { id: '6', actionId: 'STICK_BTN_6', num: 'BTN 06', name: 'TG2 (Gatilho 2º Estágio)', desc: 'Fogo Total Grupos 1 + 2' },
      { id: '2', actionId: 'STICK_BTN_2', num: 'BTN 02', name: 'S2 (Weapon Release)', desc: 'Travar e Lançar Mísseis / Bomba' },
      { id: '3', actionId: 'STICK_BTN_3', num: 'BTN 03', name: 'S3 (Nosewheel Steering)', desc: 'Alternar Modo Gimbal / Igualar Velocidade' },
      { id: '4', actionId: 'STICK_BTN_4', num: 'BTN 04', name: 'S4 (Pinky Lever)', desc: '⚡ SHIFT LAYER GLOBAL + Decoupled (Alt+C)', special: 'amber' },
      { id: '5', actionId: 'STICK_BTN_5', num: 'BTN 05', name: 'S1 (Master Mode)', desc: 'Alternar Master Mode SCM / NAV (B)' }
    ]
  },
  {
    title: '🧭 Trim Hat (POV Hat 8-Way)',
    color: 'cyan',
    items: [
      { hatDir: 'up', actionId: 'TRIM_HAT_UP', num: 'POV ▲', name: 'Trim Hat Cima (H1U)', desc: 'Capacitores: Energia Propulsores (F6)' },
      { hatDir: 'right', actionId: 'TRIM_HAT_RIGHT', num: 'POV ▶', name: 'Trim Hat Dir. (H1R)', desc: 'Capacitores: Energia Escudos (F7)' },
      { hatDir: 'down', actionId: 'TRIM_HAT_DOWN', num: 'POV ▼', name: 'Trim Hat Baixo (H1D)', desc: 'Capacitores: Equilibrar Energia (F8)' },
      { hatDir: 'left', actionId: 'TRIM_HAT_LEFT', num: 'POV ◀', name: 'Trim Hat Esq. (H1L)', desc: 'Capacitores: Energia Armas (F5)' }
    ]
  },
  {
    title: '🎯 TMS Hat (Target Management Switch)',
    color: 'cyan',
    items: [
      { id: '7', actionId: 'STICK_BTN_7', num: 'BTN 07', name: 'TMS UP (H2U)', desc: 'Selecionar Alvo sob a Mira (T)' },
      { id: '8', actionId: 'STICK_BTN_8', num: 'BTN 08', name: 'TMS RIGHT (H2R)', desc: 'Próximo Alvo Hostil (5)' },
      { id: '9', actionId: 'STICK_BTN_9', num: 'BTN 09', name: 'TMS DOWN (H2D)', desc: 'Alvo Hostil Mais Próximo / Atacante (4)' },
      { id: '10', actionId: 'STICK_BTN_10', num: 'BTN 10', name: 'TMS LEFT (H2L)', desc: 'Alvo Hostil Anterior' }
    ]
  },
  {
    title: '📡 DMS Hat (Display Management Switch)',
    color: 'cyan',
    items: [
      { id: '11', actionId: 'STICK_BTN_11', num: 'BTN 11', name: 'DMS UP (H3U)', desc: 'Ping de Radar (Tab) + Foco Scan' },
      { id: '12', actionId: 'STICK_BTN_12', num: 'BTN 12', name: 'DMS RIGHT (H3R)', desc: 'Próximo Alvo Geral (7)' },
      { id: '13', actionId: 'STICK_BTN_13', num: 'BTN 13', name: 'DMS DOWN (H3D)', desc: 'Diminuir Foco Scan / Escudos Centro' },
      { id: '14', actionId: 'STICK_BTN_14', num: 'BTN 14', name: 'DMS LEFT (H3L)', desc: 'Alvo Geral Anterior' }
    ]
  },
  {
    title: '🛡️ CMS Hat (Countermeasures Switch)',
    color: 'cyan',
    items: [
      { id: '15', actionId: 'STICK_BTN_15', num: 'BTN 15', name: 'CMS UP (H4U)', desc: 'Lançar Campo de Ruído / Chaff (J)' },
      { id: '16', actionId: 'STICK_BTN_16', num: 'BTN 16', name: 'CMS RIGHT (H4R)', desc: 'Aumentar Salva Decoy / Próximo Míssil' },
      { id: '17', actionId: 'STICK_BTN_17', num: 'BTN 17', name: 'CMS DOWN (H4D)', desc: 'Lançar Flare / Decoy (H)' },
      { id: '18', actionId: 'STICK_BTN_18', num: 'BTN 18', name: 'CMS LEFT (H4L)', desc: 'Diminuir Salva Decoy' },
      { id: '19', actionId: 'STICK_BTN_19', num: 'BTN 19', name: 'CMS PUSH (H4P)', desc: 'Salva de Pânico Contramedidas + Míssil Extra' }
    ]
  },
  {
    title: '📈 Eixos Analógicos Magnéticos H.E.A.R.T (16-Bit)',
    color: 'green',
    items: [
      { num: 'EIXO X', actionId: 'STICK_AXIS_X', name: 'Eixo X (js1_x - Rolar / Roll)', desc: 'Inclinação Lateral Suave 16-Bit', isAxis: true },
      { num: 'EIXO Y', actionId: 'STICK_AXIS_Y', name: 'Eixo Y (js1_y - Arfagem / Pitch)', desc: 'Cabrar e Picar 16-Bit', isAxis: true }
    ]
  }
];

const THROTTLE_VISUAL_GROUPS = [
  {
    title: '🕹️ Punhos das Manetes (Throttle Handles)',
    color: 'amber',
    items: [
      { id: '1', actionId: 'SLEW_PUSH_PRESS', num: 'BTN 01', name: 'SC (Slew Push)', desc: 'Igualar Velocidade Alvo / Interação (F)' },
      { id: '2', actionId: 'MIC_PUSH_PRESS', num: 'BTN 02', name: 'MSP (Mic Push)', desc: 'Push-to-Talk VOIP (Num +)' },
      { id: '3', actionId: 'MIC_UP_PRESS', num: 'BTN 03', name: 'MSU (Mic Up)', desc: 'Alternar Modo Scan (V)' },
      { id: '4', actionId: 'MIC_RIGHT_PRESS', num: 'BTN 04', name: 'MSR (Mic Right)', desc: 'Câmara 3ª Pessoa (F4)' },
      { id: '5', actionId: 'MIC_DOWN_PRESS', num: 'BTN 05', name: 'MSD (Mic Down)', desc: 'Modo Mineração / Salvage (M)' },
      { id: '6', actionId: 'MIC_LEFT_PRESS', num: 'BTN 06', name: 'MSL (Mic Left)', desc: 'Disponível / Personalizado' },
      { id: '7', actionId: 'SPDBRK_FWD', num: 'BTN 07', name: 'SPDF (Speedbrake FWD)', desc: 'Cruise Control ON/OFF (C)' },
      { id: '8', actionId: 'SPDBRK_AFT', num: 'BTN 08', name: 'SPDB (Speedbrake AFT)', desc: 'Travão Espacial (Space Brake - X)' },
      { id: '9', actionId: 'BOAT_FWD', num: 'BTN 09', name: 'BSF (Boat FWD)', desc: 'Quantum Mode / NAV (B)' },
      { id: '10', actionId: 'BOAT_AFT', num: 'BTN 10', name: 'BSB (Boat AFT)', desc: 'Regressar Modo SCM / Armas (B)' },
      { id: '11', actionId: 'CHINA_FWD_PRESS', num: 'BTN 11', name: 'CHF (China Hat FWD)', desc: 'Boost / Pós-Combustão (LShift)' },
      { id: '12', actionId: 'CHINA_AFT_PRESS', num: 'BTN 12', name: 'CHB (China Hat AFT)', desc: 'Inverter Propulsão / Recuar (S)' },
      { id: '13', actionId: 'PINKY_FWD', num: 'BTN 13', name: 'PSF (Pinky FWD)', desc: 'Faróis da Nave (L)' },
      { id: '14', actionId: 'PINKY_AFT', num: 'BTN 14', name: 'PSB (Pinky AFT)', desc: 'Luzes de Cabine' },
      { id: '15', actionId: 'LTB_PRESS', num: 'BTN 15', name: 'LTB (Left Throttle Btn)', desc: 'Flight Ready (Alt+R) / Autoland (N)' }
    ]
  },
  {
    title: '🕹️ Coolie Hat (Strafe 4-Way)',
    color: 'amber',
    items: [
      { hatDir: 'up', actionId: 'COOLIE_UP', num: 'HAT ▲', name: 'Coolie Hat UP (CSU)', desc: 'Propulsor Vertical: Subir (Space)' },
      { hatDir: 'right', actionId: 'COOLIE_RIGHT', num: 'HAT ▶', name: 'Coolie Hat RIGHT (CSR)', desc: 'Guiada Direita / Strafe (D)' },
      { hatDir: 'down', actionId: 'COOLIE_DOWN', num: 'HAT ▼', name: 'Coolie Hat DOWN (CSD)', desc: 'Propulsor Vertical: Descer (LCtrl)' },
      { hatDir: 'left', actionId: 'COOLIE_LEFT', num: 'HAT ◀', name: 'Coolie Hat LEFT (CSL)', desc: 'Guiada Esquerda / Strafe (A)' }
    ]
  },
  {
    title: '🎛️ Consola da Base (Interruptores Físicos)',
    color: 'amber',
    items: [
      { id: '16', actionId: 'FUEL_L_ON', num: 'BTN 16', name: 'EFLNORM (Fuel Left)', desc: 'Energia dos Propulsores ON/OFF (I)' },
      { id: '17', actionId: 'FUEL_R_ON', num: 'BTN 17', name: 'EFRNORM (Fuel Right)', desc: 'Energia das Armas ON/OFF (P)' },
      { id: '18', actionId: 'ENG_L_MOTOR', num: 'BTN 18', name: 'EOLMOTOR (Eng L Motor)', desc: 'Desligar Propulsores (I)' },
      { id: '31', actionId: 'ENG_L_IGN', num: 'BTN 31', name: 'EOLIGN (Eng L IGN)', desc: 'Limpar Visor Capacete (Alt+X)' },
      { id: '19', actionId: 'ENG_R_MOTOR', num: 'BTN 19', name: 'EORMOTOR (Eng R Motor)', desc: 'Desligar Armas (P)' },
      { id: '32', actionId: 'ENG_R_IGN', num: 'BTN 32', name: 'EORIGN (Eng R IGN)', desc: 'Ejetar Nave (Alt+Y)' },
      { id: '20', actionId: 'APU_ON', num: 'BTN 20', name: 'APUON (APU Start)', desc: 'Flight Ready (Alt+R) / Energia Geral' },
      { id: '21', actionId: 'LDGHORN_PRESS', num: 'BTN 21', name: 'LDGH (Horn / ATC)', desc: 'Chamar Torre ATC / Aterragem (Alt+N)' },
      { id: '22', actionId: 'FLAPS_UP', num: 'BTN 22', name: 'FLAPU (Flaps UP)', desc: 'Cruise Control (C) / Retrair Trem' },
      { id: '23', actionId: 'FLAPS_DN', num: 'BTN 23', name: 'FLAPD (Flaps DOWN)', desc: 'Modo VTOL / Hover (K)' },
      { id: '24', actionId: 'EAC_ON', num: 'BTN 24', name: 'EACON (EAC ARM)', desc: 'Energia Geral / Escudos (U)' },
      { id: '25', actionId: 'RDR_ALTM_ON', num: 'BTN 25', name: 'RDRNRM (Radar Altimeter)', desc: 'Trem de Aterragem (N)' },
      { id: '26', actionId: 'AP_ENGAGE_PRESS', num: 'BTN 26', name: 'APENG (Autopilot Btn)', desc: 'Chamar Torre ATC (Alt+N)' },
      { id: '27', actionId: 'AP_PATH', num: 'BTN 27', name: 'APPAT (AP PATH)', desc: 'Abrir Todas as Portas Exteriores (Alt+K)' },
      { id: '28', actionId: 'AP_ALT', num: 'BTN 28', name: 'APALT (AP ALT)', desc: 'Trancar Todas as Portas (Alt+L)' }
    ]
  },
  {
    title: '🛑 Detentores Físicos de Corte (Idle Cutoff)',
    color: 'amber',
    items: [
      { id: '29', actionId: 'IDLE_R_OFF', num: 'BTN 29', name: 'IDLEROFF (Cutoff Dir.)', desc: 'Detentor OFF Manete Direita (Debounce 350ms)' },
      { id: '30', actionId: 'IDLE_L_OFF', num: 'BTN 30', name: 'IDLELOFF (Cutoff Esq.)', desc: 'Detentor OFF Manete Esquerda (Debounce 350ms)' }
    ]
  },
  {
    title: '🚀 Eixos Analógicos & Fricção da Manete',
    color: 'green',
    items: [
      { num: 'EIXO Z', actionId: 'THR_Z', name: 'Eixo Z (js2_z - Manete Esq.)', desc: 'Propulsão Longitudinal Principal', isAxis: true },
      { num: 'EIXO Rz', actionId: 'THR_RZ', name: 'Eixo Rz (js2_rotz - Manete Dir.)', desc: 'Aceleração Sincronizada (Sem Conflito)', isAxis: true },
      { num: 'SLIDER 1', actionId: 'THR_SLIDER', name: 'Slider 1 (js2_slider1 - Fricção)', desc: 'Limitador de Velocidade / Laser', isAxis: true },
      { num: 'SLEW X', actionId: 'THR_SCX', name: 'Eixo X Mini-Stick (js2_x)', desc: 'Strafe Lateral Analógico', isAxis: true },
      { num: 'SLEW Y', actionId: 'THR_SCY', name: 'Eixo Y Mini-Stick (js2_y)', desc: 'Strafe Vertical Analógico', isAxis: true }
    ]
  }
];

function getKeyBadgeHtml(actionId) {
  const m = cachedMatrixMappings[actionId];
  if (!m) {
    return `<span class="key-badge dim" style="font-size:10px; opacity:0.75;">Nativo SC</span>`;
  }
  let html = '';
  if (m.macro_id && cachedMacros[m.macro_id]) {
    const mac = cachedMacros[m.macro_id];
    html = `<span class="key-badge macro-pill" style="font-size:10px; padding:2px 6px;">${mac.icon || '⚡'} MACRO</span>`;
  } else if (m.key && m.key.trim()) {
    const parts = [];
    for (const mod of (m.modifiers || [])) {
      parts.push(`<span class="key-badge mod" style="font-size:10px; padding:2px 5px;">${mod}</span>`);
    }
    parts.push(`<span class="key-badge" style="font-size:10px; padding:2px 5px;">${m.key}</span>`);
    html = parts.join(' + ');
  } else {
    html = `<span class="key-badge dim" style="font-size:10px; opacity:0.75;">Nativo SC</span>`;
  }
  if ((m.long_key && m.long_key.trim()) || (m.long_macro_id && cachedMacros[m.long_macro_id])) {
    const lLabel = (m.long_macro_id && cachedMacros[m.long_macro_id]) ? '⚡HOLD' : `⏱️${m.long_key}`;
    html += ` <span class="key-badge hold-pill" style="font-size:9.5px; padding:2px 5px;" title="Ação Dupla: Pressão Longa (${m.long_threshold_ms || 450}ms)">${lLabel}</span>`;
  }
  return html;
}


// ==============================================================================
// PHYSICAL BUTTON COORDINATES MAP (Percentages relative to transparent cutouts)
// ==============================================================================
const HOTAS_COORDINATES = {
  // Exact grid-verified coordinates for warthog_stick_526x1181.png
  stick: {
    '1': { x: 68.0, y: 28.0, num: 'BTN 01', name: 'TG1 (Gatilho 1º Estágio - Frente)' },
    '6': { x: 66.0, y: 31.5, num: 'BTN 06', name: 'TG2 (Gatilho 2º Estágio - Frente)' },
    '2': { x: 31.0, y: 5.5,  num: 'BTN 02', name: 'S2 (Weapon Release - Botão Vermelho)' },
    '3': { x: 55.0, y: 58.0, num: 'BTN 03', name: 'S3 (Nosewheel Steering - Frente)' },
    '4': { x: 52.0, y: 69.0, num: 'BTN 04', name: 'S4 (Pinky Lever Shift - Base Frente)' },
    '5': { x: 95.5, y: 14.5, num: 'BTN 05', name: 'S1 (Master Mode - Lateral Dir.)' },
    'hat-up':    { x: 61.5, y: 3.5,  num: 'POV ▲', name: 'Trim Hat Cima (H1U)' },
    'hat-right': { x: 71.0, y: 8.0,  num: 'POV ▶', name: 'Trim Hat Dir. (H1R)' },
    'hat-down':  { x: 61.5, y: 12.5, num: 'POV ▼', name: 'Trim Hat Baixo (H1D)' },
    'hat-left':  { x: 52.0, y: 8.0,  num: 'POV ◀', name: 'Trim Hat Esq. (H1L)' },
    '7':  { x: 27.5, y: 14.0, num: 'BTN 07', name: 'TMS UP (H2U)' },
    '8':  { x: 33.0, y: 16.5, num: 'BTN 08', name: 'TMS RIGHT (H2R)' },
    '9':  { x: 27.5, y: 19.0, num: 'BTN 09', name: 'TMS DOWN (H2D)' },
    '10': { x: 22.0, y: 16.5, num: 'BTN 10', name: 'TMS LEFT (H2L)' },
    '11': { x: 53.0, y: 19.0, num: 'BTN 11', name: 'DMS UP (H3U)' },
    '12': { x: 59.0, y: 22.0, num: 'BTN 12', name: 'DMS RIGHT (H3R)' },
    '13': { x: 53.0, y: 25.0, num: 'BTN 13', name: 'DMS DOWN (H3D)' },
    '14': { x: 47.0, y: 22.0, num: 'BTN 14', name: 'DMS LEFT (H3L)' },
    '15': { x: 13.5, y: 31.5, num: 'BTN 15', name: 'CMS UP (H4U)' },
    '16': { x: 19.0, y: 34.5, num: 'BTN 16', name: 'CMS RIGHT (H4R)' },
    '17': { x: 13.5, y: 37.5, num: 'BTN 17', name: 'CMS DOWN (H4D)' },
    '18': { x: 8.5,  y: 34.5, num: 'BTN 18', name: 'CMS LEFT (H4L)' },
    '19': { x: 13.5, y: 34.5, num: 'BTN 19', name: 'CMS PUSH (H4P)' },
    'ax-EIXO_X': { x: 34.0, y: 92.0, num: 'EIXO X', name: 'Eixo Roll (js1_x)' },
    'ax-EIXO_Y': { x: 34.0, y: 92.0, num: 'EIXO Y', name: 'Eixo Pitch (js1_y)' }
  },
  // Exact grid-verified coordinates for warthog_throttle_509x455.png
  throttle: {
    '1':  { x: 50.0, y: 18.0, num: 'BTN 01', name: 'SC (Slew Push - Frente Punho Dir.)' },
    '2':  { x: 72.0, y: 14.5, num: 'BTN 02', name: 'MSP (Mic Push)' },
    '3':  { x: 72.0, y: 11.5, num: 'BTN 03', name: 'MSU (Mic Up)' },
    '4':  { x: 75.0, y: 14.5, num: 'BTN 04', name: 'MSR (Mic Right)' },
    '5':  { x: 72.0, y: 17.5, num: 'BTN 05', name: 'MSD (Mic Down)' },
    '6':  { x: 69.0, y: 14.5, num: 'BTN 06', name: 'MSL (Mic Left)' },
    '7':  { x: 72.5, y: 22.5, num: 'BTN 07', name: 'SPDF (Speedbrake FWD)' },
    '8':  { x: 70.5, y: 25.5, num: 'BTN 08', name: 'SPDB (Speedbrake AFT)' },
    '9':  { x: 69.5, y: 29.5, num: 'BTN 09', name: 'BSF (Boat Switch FWD)' },
    '10': { x: 67.5, y: 32.0, num: 'BTN 10', name: 'BSB (Boat Switch AFT)' },
    '11': { x: 67.5, y: 36.5, num: 'BTN 11', name: 'CHF (China Hat FWD - Vermelho)' },
    '12': { x: 64.5, y: 38.5, num: 'BTN 12', name: 'CHB (China Hat AFT - Vermelho)' },
    '13': { x: 15.0, y: 19.5, num: 'BTN 13', name: 'PSF (Pinky Switch FWD)' },
    '14': { x: 15.0, y: 22.0, num: 'BTN 14', name: 'PSB (Pinky Switch AFT)' },
    '15': { x: 25.0, y: 23.0, num: 'BTN 15', name: 'LTB (Left Throttle Btn)' },
    'hat-up':    { x: 58.0, y: 7.0,  num: 'HAT ▲', name: 'Coolie Hat UP' },
    'hat-right': { x: 61.0, y: 9.0,  num: 'HAT ▶', name: 'Coolie Hat RIGHT' },
    'hat-down':  { x: 58.0, y: 11.0, num: 'HAT ▼', name: 'Coolie Hat DOWN' },
    'hat-left':  { x: 55.0, y: 9.0,  num: 'HAT ◀', name: 'Coolie Hat LEFT' },
    '16': { x: 76.5, y: 39.0, num: 'BTN 16', name: 'EFLNORM (Fuel Flow Left)' },
    '17': { x: 84.5, y: 43.5, num: 'BTN 17', name: 'EFRNORM (Fuel Flow Right)' },
    '18': { x: 64.8, y: 48.0, num: 'BTN 18', name: 'EOLMOTOR (Eng Oper L Motor)' },
    '31': { x: 64.0, y: 44.5, num: 'BTN 31', name: 'EOLIGN (Eng Oper L IGN)' },
    '19': { x: 73.0, y: 51.5, num: 'BTN 19', name: 'EORMOTOR (Eng Oper R Motor)' },
    '32': { x: 72.5, y: 48.0, num: 'BTN 32', name: 'EORIGN (Eng Oper R IGN)' },
    '20': { x: 59.5, y: 53.5, num: 'BTN 20', name: 'APUON (APU Start / Off)' },
    '21': { x: 47.5, y: 61.5, num: 'BTN 21', name: 'LDGH (L/G WRN Silence / ATC)' },
    '22': { x: 27.5, y: 40.5, num: 'BTN 22', name: 'FLAPU (Flaps UP)' },
    '23': { x: 27.5, y: 43.5, num: 'BTN 23', name: 'FLAPD (Flaps DOWN)' },
    '24': { x: 16.0, y: 55.0, num: 'BTN 24', name: 'EACON (EAC ARM / OFF)' },
    '25': { x: 23.0, y: 60.5, num: 'BTN 25', name: 'RDRNRM (RDR ALTM NRM / DIS)' },
    '26': { x: 28.5, y: 66.5, num: 'BTN 26', name: 'APENG (Autopilot Engage)' },
    '27': { x: 34.0, y: 67.0, num: 'BTN 27', name: 'APPAT (AP PATH)' },
    '28': { x: 34.5, y: 70.5, num: 'BTN 28', name: 'APALT (AP ALT)' },
    '29': { x: 47.0, y: 54.5, num: 'BTN 29', name: 'IDLEROFF (Cutoff Dir.)' },
    '30': { x: 43.0, y: 54.0, num: 'BTN 30', name: 'IDLELOFF (Cutoff Esq.)' },
    'ax-SLIDER_1': { x: 62.5, y: 60.0, num: 'SLIDER 1', name: 'Slider 1 (Fricção / Limitador)' },
    'ax-EIXO_Z':   { x: 24.5, y: 15.0, num: 'EIXO Z', name: 'Eixo Z (Manete Esq.)' },
    'ax-EIXO_Rz':  { x: 55.0, y: 14.0, num: 'EIXO Rz', name: 'Eixo Rz (Manete Dir.)' },
    'ax-SLEW_X':   { x: 50.0, y: 18.0, num: 'SLEW X', name: 'Slew X (Mini-Stick)' },
    'ax-SLEW_Y':   { x: 50.0, y: 18.0, num: 'SLEW Y', name: 'Slew Y (Mini-Stick)' }
  }
};

function showButtonPointer(device, key) {
  const coordsMap = HOTAS_COORDINATES[device];
  if (!coordsMap) return;
  const pos = coordsMap[String(key)];
  if (!pos) return;

  const reticle = document.getElementById(`vmap-reticle-${device}`);
  const badge = document.getElementById(`vmap-badge-${device}`);
  const title = document.getElementById(`vmap-title-${device}`);
  const callout = document.getElementById(`vmap-callout-${device}`);

  if (!reticle) return;

  reticle.style.left = pos.x + '%';
  reticle.style.top = pos.y + '%';

  if (badge) badge.textContent = pos.num;
  if (title) title.textContent = pos.name;

  if (callout) {
    if (pos.x > 58) {
      callout.classList.add('flip-left');
    } else {
      callout.classList.remove('flip-left');
    }
  }

  reticle.classList.add('visible');
}

function hideButtonPointer(device) {
  const reticle = document.getElementById(`vmap-reticle-${device}`);
  if (reticle) reticle.classList.remove('visible');
}

function renderOverlayHotspots() {
  const stickOverlay = document.getElementById('vmap-overlay-stick');
  const throttleOverlay = document.getElementById('vmap-overlay-throttle');

  if (stickOverlay) {
    stickOverlay.querySelectorAll('.vmap-hotspot-pin').forEach(p => p.remove());
    for (const [key, pos] of Object.entries(HOTAS_COORDINATES.stick)) {
      const pin = document.createElement('div');
      pin.className = 'vmap-hotspot-pin';
      pin.style.left = pos.x + '%';
      pin.style.top = pos.y + '%';
      pin.title = `${pos.num}: ${pos.name} (Clica para editar)`;
      pin.onmouseenter = () => showButtonPointer('stick', key);
      pin.onmouseleave = () => hideButtonPointer('stick');
      pin.onclick = (e) => {
        e.stopPropagation();
        const row = document.getElementById(`vbtn-stick-${key}`);
        if (row) {
          row.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
          row.click();
        }
      };
      stickOverlay.appendChild(pin);
    }
  }

  if (throttleOverlay) {
    throttleOverlay.querySelectorAll('.vmap-hotspot-pin').forEach(p => p.remove());
    for (const [key, pos] of Object.entries(HOTAS_COORDINATES.throttle)) {
      const pin = document.createElement('div');
      pin.className = 'vmap-hotspot-pin';
      pin.style.left = pos.x + '%';
      pin.style.top = pos.y + '%';
      pin.title = `${pos.num}: ${pos.name} (Clica para editar)`;
      pin.onmouseenter = () => showButtonPointer('throttle', key);
      pin.onmouseleave = () => hideButtonPointer('throttle');
      pin.onclick = (e) => {
        e.stopPropagation();
        const row = document.getElementById(`vbtn-throttle-${key}`);
        if (row) {
          row.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
          row.click();
        }
      };
      throttleOverlay.appendChild(pin);
    }
  }
}

function renderVisualMapping() {
  const stickCont = document.getElementById('vmap-stick-buttons-container');
  const throttleCont = document.getElementById('vmap-throttle-buttons-container');
  if (!stickCont || !throttleCont) return;

  // Render Stick
  let stickHtml = '';
  for (const grp of STICK_VISUAL_GROUPS) {
    stickHtml += `
      <div class="vmap-group-box">
        <div class="vmap-group-title">${grp.title}</div>
        <div class="vmap-btn-list">`;
    for (const item of grp.items) {
      const keyId = item.hatDir ? `hat-${item.hatDir}` : (item.id || `ax-${item.num.replace(/\s+/g, '_')}`);
      const elId = item.hatDir ? `vbtn-stick-hat-${item.hatDir}` : (item.id ? `vbtn-stick-${item.id}` : `vbtn-stick-ax-${item.num.replace(/\s+/g, '_')}`);
      const keyBadge = item.isAxis 
        ? `<span class="key-badge" style="font-size:10px; color:var(--neon-green); border-color:rgba(0,230,118,0.4);">Analógico</span>`
        : getKeyBadgeHtml(item.actionId);
      const idClass = item.special ? `vmap-btn-id ${item.special}` : (grp.color === 'green' ? 'vmap-btn-id green' : 'vmap-btn-id');
      const editBtn = item.isAxis 
        ? `<button class="btn-secondary" style="padding: 3px 8px; font-size: 11px;" onclick="event.stopPropagation(); switchTab('axes')" title="Ajustar curvas e zonas mortas">🎯 Curva</button>`
        : `<button class="edit-btn-pill" onclick="event.stopPropagation(); openKeyEditorModal('${item.actionId}')" title="Editar tecla e modificadores">✏️ Editar</button>
           <button class="btn-secondary" style="padding: 2px 7px; font-size: 11px; margin-left: 4px;" onclick="event.stopPropagation(); manualTrigger('${item.actionId}')" title="Testar envio de pulso DirectInput">▶</button>`;

      stickHtml += `
        <div id="${elId}" class="vmap-btn-row" 
             onmouseenter="showButtonPointer('stick', '${keyId}')"
             onmouseleave="hideButtonPointer('stick')"
             onclick="${item.isAxis ? "switchTab('axes')" : `openKeyEditorModal('${item.actionId}')`}" 
             title="${item.isAxis ? 'Ajustar curvas de eixo' : 'Clica para editar esta tecla'}">
          <div class="${idClass}">${item.num}</div>
          <div class="vmap-btn-content">
            <div class="vmap-btn-action">${item.name}</div>
            <div class="vmap-btn-sub">${item.desc}</div>
          </div>
          <div class="vmap-btn-right">
            ${keyBadge}
            ${editBtn}
          </div>
        </div>`;
    }
    stickHtml += `
        </div>
      </div>`;
  }
  stickCont.innerHTML = stickHtml;

  // Render Throttle
  let throttleHtml = '';
  for (const grp of THROTTLE_VISUAL_GROUPS) {
    throttleHtml += `
      <div class="vmap-group-box">
        <div class="vmap-group-title" style="color: var(--neon-amber);">${grp.title}</div>
        <div class="vmap-btn-list">`;
    for (const item of grp.items) {
      const keyId = item.hatDir ? `hat-${item.hatDir}` : (item.id || `ax-${item.num.replace(/\s+/g, '_')}`);
      const elId = item.hatDir ? `vbtn-throttle-hat-${item.hatDir}` : (item.id ? `vbtn-throttle-${item.id}` : `vbtn-throttle-ax-${item.num.replace(/\s+/g, '_')}`);
      const keyBadge = item.isAxis 
        ? `<span class="key-badge" style="font-size:10px; color:var(--neon-green); border-color:rgba(0,230,118,0.4);">Analógico</span>`
        : getKeyBadgeHtml(item.actionId);
      const idClass = grp.color === 'green' ? 'vmap-btn-id green' : 'vmap-btn-id amber';
      const editBtn = item.isAxis 
        ? `<button class="btn-secondary" style="padding: 3px 8px; font-size: 11px;" onclick="event.stopPropagation(); switchTab('axes')" title="Ajustar curvas e zonas mortas">🎯 Curva</button>`
        : `<button class="edit-btn-pill" onclick="event.stopPropagation(); openKeyEditorModal('${item.actionId}')" title="Editar tecla e modificadores">✏️ Editar</button>
           <button class="btn-secondary" style="padding: 2px 7px; font-size: 11px; margin-left: 4px;" onclick="event.stopPropagation(); manualTrigger('${item.actionId}')" title="Testar envio de pulso DirectInput">▶</button>`;

      throttleHtml += `
        <div id="${elId}" class="vmap-btn-row" 
             onmouseenter="showButtonPointer('throttle', '${keyId}')"
             onmouseleave="hideButtonPointer('throttle')"
             onclick="${item.isAxis ? "switchTab('axes')" : `openKeyEditorModal('${item.actionId}')`}" 
             title="${item.isAxis ? 'Ajustar curvas de eixo' : 'Clica para editar esta tecla'}">
          <div class="${idClass}">${item.num}</div>
          <div class="vmap-btn-content">
            <div class="vmap-btn-action">${item.name}</div>
            <div class="vmap-btn-sub">${item.desc}</div>
          </div>
          <div class="vmap-btn-right">
            ${keyBadge}
            ${editBtn}
          </div>
        </div>`;
    }
    throttleHtml += `
        </div>
      </div>`;
  }
  throttleCont.innerHTML = throttleHtml;

  // Render interactive pin hotspots on overlay
  renderOverlayHotspots();

  // Re-apply filter if text was present
  const searchInput = document.getElementById('vmap-search-input');
  if (searchInput && searchInput.value) {
    filterVisualMap(searchInput.value);
  }
}

function setVisualMapView(mode) {
  const colStick = document.getElementById('vmap-col-stick');
  const colThrottle = document.getElementById('vmap-col-throttle');
  const mainGrid = document.getElementById('vmap-main-grid');
  const btnBoth = document.getElementById('vmap-btn-view-both');
  const btnStick = document.getElementById('vmap-btn-view-stick');
  const btnThrottle = document.getElementById('vmap-btn-view-throttle');

  btnBoth?.classList.remove('active');
  btnStick?.classList.remove('active');
  btnThrottle?.classList.remove('active');

  if (mode === 'stick') {
    if (colStick) colStick.style.display = 'flex';
    if (colThrottle) colThrottle.style.display = 'none';
    if (mainGrid) mainGrid.style.gridTemplateColumns = '1fr';
    btnStick?.classList.add('active');
  } else if (mode === 'throttle') {
    if (colStick) colStick.style.display = 'none';
    if (colThrottle) colThrottle.style.display = 'flex';
    if (mainGrid) mainGrid.style.gridTemplateColumns = '1fr';
    btnThrottle?.classList.add('active');
  } else {
    // Both side-by-side
    if (colStick) colStick.style.display = 'flex';
    if (colThrottle) colThrottle.style.display = 'flex';
    if (mainGrid) mainGrid.style.gridTemplateColumns = '1fr 1fr';
    btnBoth?.classList.add('active');
  }
}

function filterVisualMap(query) {
  const q = (query || '').trim().toLowerCase();
  const rows = document.querySelectorAll('.vmap-btn-row');
  rows.forEach(row => {
    if (!q) {
      row.style.display = 'flex';
    } else {
      const text = row.textContent.toLowerCase();
      row.style.display = text.includes(q) ? 'flex' : 'none';
    }
  });

  document.querySelectorAll('.vmap-group-box').forEach(box => {
    if (!q) {
      box.style.display = 'block';
    } else {
      const visibleRows = box.querySelectorAll('.vmap-btn-row[style*="display: flex"]');
      box.style.display = visibleRows.length > 0 ? 'block' : 'none';
    }
  });
}

function highlightCatalogButton(device, button, isDown) {
  const el = document.getElementById(`cat-${device}-btn-${button}`);
  if (el) {
    if (isDown) {
      el.style.background = 'rgba(0, 210, 255, 0.22)';
      el.style.boxShadow = '0 0 14px rgba(0, 210, 255, 0.35)';
    } else {
      el.style.background = '';
      el.style.boxShadow = '';
    }
  }

  // Visual Joystick Map real-time hardware illumination and reticle pointer
  const vEl = document.getElementById(`vbtn-${device}-${button}`);
  if (vEl) {
    if (isDown) {
      vEl.classList.add('active');
      showButtonPointer(device, String(button));
    } else {
      vEl.classList.remove('active');
      hideButtonPointer(device);
    }
  }
}

// Pinky Shift Layer Notification
function updateShiftLayer(isActive) {
  const strip = document.getElementById('hud-alert-strip');
  const text = document.getElementById('hud-alert-text');
  if (isActive) {
    strip.className = 'hud-alert-strip';
    text.textContent = '⚡ SHIFT LAYER ATIVA (PINKY LEVER PREMIDO - BOTÕES DUPLICADOS)';
    playCockpitSound('chirp');
  } else {
    if (!strip.classList.contains('afterburner')) {
      strip.className = 'hud-alert-strip hidden';
    }
  }
}

// Afterburner Detent Notification
function updateAfterburnerState(isActive) {
  const strip = document.getElementById('hud-alert-strip');
  const text = document.getElementById('hud-alert-text');
  const label = document.getElementById('afterburner-status-label');

  if (isActive) {
    strip.className = 'hud-alert-strip afterburner';
    text.textContent = '🚀 PÓS-COMBUSTÃO ENGATADA (AFTERBURNER DETENT ATIVO - BOOST INJETADO)';
    if (label) {
      label.textContent = 'ENGATADO (BOOST LSHIFT)';
      label.style.color = 'var(--neon-green)';
    }
    playCockpitSound('afterburner');
  } else {
    if (label) {
      label.textContent = 'Pronto';
      label.style.color = 'var(--neon-cyan)';
    }
    strip.className = 'hud-alert-strip hidden';
  }
}

// Warthog Throttle Base LEDs
function updateBaseLeds(leds, brightness) {
  if (leds && leds.length >= 5) {
    for (let i = 1; i <= 5; i++) {
      const unit = document.getElementById(`warthog-led-${i}`);
      if (unit) {
        if (leds[i - 1]) {
          unit.classList.add('lit');
        } else {
          unit.classList.remove('lit');
        }
      }
    }
  }
  if (brightness !== undefined) {
    document.getElementById('slider-backlight').value = brightness;
    document.getElementById('label-backlight').textContent = `Nível ${brightness}`;
  }
}

function toggleHardwareLed(index) {
  initAudio();
  playCockpitSound('click');
  const unit = document.getElementById(`warthog-led-${index}`);
  const isLit = unit.classList.contains('lit');
  const newState = !isLit;
  if (newState) unit.classList.add('lit'); else unit.classList.remove('lit');

  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'set_led', led: index, state: newState }));
  }
}

function updateBacklight(val) {
  document.getElementById('label-backlight').textContent = `Nível ${val}`;
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'set_brightness', brightness: parseInt(val) }));
  }
}

function toggleAutoBoost(checked) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'set_auto_boost', enabled: checked }));
  }
}

// Switch UI State Updates (Todos os 32 Botões + POV1 da Manete Dupla e 19 Botões + POV1 do Manche)
function updateSwitchUI(data, silent = false) {
  if (!silent) {
    playCockpitSound(data.is_down ? 'chirp' : 'click');
  }
  const btnNum = data.button;
  const isDown = data.is_down;

  // --- MANCHE A-10C (JOYSTICK js1: BTN 01..19) ---
  if (data.device === 'stick') {
    if (btnNum === 1) {
      setCardActive('card-stk-1', 'pill-stk-1', isDown, isDown ? 'FOGO GRUPO 1!' : 'LIVRE');
    } else if (btnNum === 6) {
      setCardActive('card-stk-6', 'pill-stk-6', isDown, isDown ? 'FOGO TOTAL (1+2)!' : 'LIVRE');
    } else if (btnNum === 2) {
      setCardActive('card-stk-2', 'pill-stk-2', isDown, isDown ? 'MÍSSIL / RELEASE!' : 'LIVRE');
    } else if (btnNum === 5) {
      setCardActive('card-stk-5', 'pill-stk-5', isDown, isDown ? 'MASTER MODE (B)!' : 'LIVRE');
    } else if (btnNum === 3) {
      setCardActive('card-stk-3', 'pill-stk-3', isDown, isDown ? 'GIMBAL / NWS!' : 'LIVRE');
    } else if (btnNum === 4) {
      setCardActive('card-stk-4', 'pill-stk-4', isDown, isDown ? '⚡ SHIFT ATIVO!' : 'NORMAL');
    } else if (btnNum >= 7 && btnNum <= 10) { // TMS HAT (07..10)
      const tmsMap = {
        7: '⬆️ H2U (07): ALVO NA MIRA (T)',
        8: '➡️ H2R (08): PRÓXIMO HOSTIL (5)',
        9: '⬇️ H2D (09): HOSTIL MAIS PRÓX. (4)',
        10: '⬅️ H2L (10): HOSTIL ANTERIOR / PIN'
      };
      const visTms = document.getElementById('vis-stk-tms');
      setCardActive('card-stk-tms', 'pill-stk-tms', isDown, isDown ? `BTN ${String(btnNum).padStart(2, '0')} ATIVO` : 'CENTRO');
      if (visTms) visTms.textContent = isDown ? tmsMap[btnNum] : '🎯 7:Mira(T) 8:Hostil+ 9:Próx 10:Ant';
    } else if (btnNum >= 11 && btnNum <= 14) { // DMS HAT (11..14)
      const dmsMap = {
        11: '⬆️ H3U (11): PING RADAR (TAB)',
        12: '➡️ H3R (12): PRÓXIMO ALVO (7)',
        13: '⬇️ H3D (13): FOCO SCAN / ESCUDOS',
        14: '⬅️ H3L (14): ALVO ANT. / ÂNGULO'
      };
      const visDms = document.getElementById('vis-stk-dms');
      setCardActive('card-stk-dms', 'pill-stk-dms', isDown, isDown ? `BTN ${btnNum} ATIVO` : 'CENTRO');
      if (visDms) visDms.textContent = isDown ? dmsMap[btnNum] : '📡 11:Ping(Tab) 12:Alvo 13:Foco 14:Âng';
    } else if (btnNum >= 15 && btnNum <= 19) { // CMS HAT (15..19)
      const cmsMap = {
        15: '⬆️ H4U (15): RUÍDO / CHAFF (J)',
        16: '➡️ H4R (16): +SALVA DECOY / MÍSSIL',
        17: '⬇️ H4D (17): LANÇAR DECOY / FLARE (H)',
        18: '⬅️ H4L (18): -SALVA DECOY / MÍSSIL',
        19: '🔴 H4P (19): SALVA DE PÂNICO!'
      };
      const visCms = document.getElementById('vis-stk-cms');
      setCardActive('card-stk-cms', 'pill-stk-cms', isDown, isDown ? `BTN ${btnNum} ATIVO` : 'CENTRO');
      if (visCms) visCms.textContent = isDown ? cmsMap[btnNum] : '🛡️ 15:Chaff(J) 17:Flare(H) 19:Panic';
    }
    return;
  }

  if (data.device !== 'throttle') return;

  // --- INTERRUPTORES DE 2 POSIÇÕES E BOTÕES MOMENTÂNEOS DA BASE ---
  if (btnNum === 16) { // EFL NORM / OVER
    setCardActive('card-efl', 'pill-efl', isDown, isDown ? 'NORM (ENERGIA ON)' : 'OVER (OFF)');
  } else if (btnNum === 17) { // EFR NORM / OVER
    setCardActive('card-efr', 'pill-efr', isDown, isDown ? 'NORM (ARMAS)' : 'OVER (ESCUDOS)');
  } else if (btnNum === 20) { // APU START / OFF
    setCardActive('card-apu', 'pill-apu', isDown, isDown ? 'START (MOTORES)' : 'OFF (DESLIGADO)');
  } else if (btnNum === 21) { // LDG HORN SILENCE BUTTON
    setCardActive('card-ldghorn', 'pill-ldghorn', isDown, isDown ? 'PREMIDO (TREM)' : 'MOMENTÂNEO');
  } else if (btnNum === 24) { // EAC ARM / OFF
    const eacPillMap = {
      combat: isDown ? 'ARM (MODO NAV)' : 'OFF (MODO SCM)',
      mining: isDown ? 'ARM (MINERAÇÃO ON)' : 'OFF (MINERAÇÃO OFF)',
      cargo: isDown ? 'ARM (PORTAS ABERTAS)' : 'OFF (PORTAS FECHADAS)',
      ground: isDown ? 'ARM (FARÓIS ON)' : 'OFF (FARÓIS OFF)'
    };
    setCardActive('card-eac', 'pill-eac', isDown, eacPillMap[currentProfile] || (isDown ? 'ARM (MODO NAV)' : 'OFF (MODO SCM)'));
  } else if (btnNum === 25) { // RDR ALTM NRM / DIS
    setCardActive('card-rdr', 'pill-rdr', isDown, isDown ? 'NRM (TREM RECOLHIDO)' : 'DIS (TREM DESCIDO)');
  } else if (btnNum === 26) { // AUTOPILOT ENGAGE BUTTON
    setCardActive('card-apeng', 'pill-apeng', isDown, isDown ? 'QUANTUM SPOOL!' : 'MOMENTÂNEO');
  } else if (btnNum === 29) { // IDLE CUTOFF LEFT
    setCardActive('card-cutl', 'pill-cutl', isDown, isDown ? 'OFF (CORTE DIR)' : 'IDLE (LIVRE)');
  } else if (btnNum === 30) { // IDLE CUTOFF RIGHT
    setCardActive('card-cutr', 'pill-cutr', isDown, isDown ? 'OFF (CORTE ESQ)' : 'IDLE (LIVRE)');
  }

  // --- INTERRUPTORES DE 3 POSIÇÕES DA BASE ---
  if (btnNum === 18 || btnNum === 31) { // ENG OPER LEFT (31=IGN Cima, 18=MOTOR Baixo)
    set3PosLever('card-eol', 'lever-eol', 'pill-eol', btnNum === 31, isDown, 'IGN (VISOR/RDY)', 'NORM (CENTRO)', 'MOTOR (OFF)');
  } else if (btnNum === 19 || btnNum === 32) { // ENG OPER RIGHT (32=IGN Cima, 19=MOTOR Baixo)
    set3PosLever('card-eor', 'lever-eor', 'pill-eor', btnNum === 32, isDown, 'IGN (ARMAS/EJ)', 'NORM (CENTRO)', 'MOTOR (OFF)');
  } else if (btnNum === 22 || btnNum === 23) { // FLAPS (22=UP, 23=DN)
    if (currentProfile === 'ground') {
      set3PosLever('card-flaps', 'lever-flaps', 'pill-flaps', btnNum === 22, isDown, 'UP (MOTOR ON)', 'MVR (CENTRO)', 'DN (POWER OFF)');
    } else {
      set3PosLever('card-flaps', 'lever-flaps', 'pill-flaps', btnNum === 22, isDown, 'UP (CRUISE)', 'MVR (VOO)', 'DN (VTOL)');
    }
  } else if (btnNum === 27 || btnNum === 28) { // AUTOPILOT SELECT (27=PATH, 28=ALT)
    set3PosLever('card-apsel', 'lever-apsel', 'pill-apsel', btnNum === 27, isDown, 'PATH (ABRIR)', 'ALT/HDG (MID)', 'ALT (TRANCAR)');
  }

  // --- INTERRUPTORES DE 3 POSIÇÕES E BOTÕES DOS PUNHOS (GRIPS) ---
  if (btnNum === 7 || btnNum === 8) { // SPEEDBRAKE (7=FWD, 8=AFT)
    if (currentProfile === 'mining') {
      set3PosLever('card-speedbrake', 'lever-speedbrake', 'pill-speedbrake', btnNum === 7, isDown, 'FWD (+LASER)', 'CENTRO', 'AFT (-LASER)');
    } else if (currentProfile === 'ground') {
      set3PosLever('card-speedbrake', 'lever-speedbrake', 'pill-speedbrake', btnNum === 7, isDown, 'FWD (CRUISE C)', 'CENTRO', 'AFT (TRAVÃO MÃO)');
    } else {
      set3PosLever('card-speedbrake', 'lever-speedbrake', 'pill-speedbrake', btnNum === 7, isDown, 'FWD (CRUISE C)', 'CENTRO', 'AFT (TRAVÃO X)');
    }
  } else if (btnNum === 9 || btnNum === 10) { // BOAT SWITCH (9=FWD, 10=AFT)
    if (currentProfile === 'mining') {
      set3PosLever('card-boat', 'lever-boat', 'pill-boat', btnNum === 9, isDown, 'BSF (MÓDULO 1)', 'BSM (CENTRO)', 'BSB (MÓDULO 2)');
    } else if (currentProfile === 'cargo') {
      set3PosLever('card-boat', 'lever-boat', 'pill-boat', btnNum === 9, isDown, 'BSF (QUANTUM B)', 'BSM (CENTRO)', 'BSB (TORRE ATC)');
    } else if (currentProfile === 'ground') {
      set3PosLever('card-boat', 'lever-boat', 'pill-boat', btnNum === 9, isDown, 'BSF (TORRE R)', 'BSM (CENTRO)', 'BSB (SCAN V)');
    } else {
      set3PosLever('card-boat', 'lever-boat', 'pill-boat', btnNum === 9, isDown, 'BSF (QUANTUM B)', 'BSM (CENTRO)', 'BSB (MODO SCM)');
    }
  } else if (btnNum === 11 || btnNum === 12) { // CHINA HAT (11=FWD, 12=AFT)
    if (currentProfile === 'mining') {
      set3PosLever('card-china', 'lever-china', 'pill-china', btnNum === 11, isDown, 'CHF (PING TAB)', 'CHM (CENTRO)', 'CHB (EJETAR ALT+J)');
    } else {
      set3PosLever('card-china', 'lever-china', 'pill-china', btnNum === 11, isDown, 'CHF (BOOST LSHIFT)', 'CHM (CENTRO)', 'CHB (RECUAR S)');
    }
  } else if (btnNum === 13 || btnNum === 14) { // PINKY SWITCH (13=FWD, 14=AFT)
    set3PosLever('card-pinky', 'lever-pinky', 'pill-pinky', btnNum === 13, isDown, 'PSF (DECOUPLED)', 'PSM (NORMAL)', 'PSB (ESP)');
  } else if (btnNum === 15) { // LEFT THROTTLE BUTTON (LTB)
    setCardActive('card-ltb', 'pill-ltb', isDown, isDown ? 'AUTOLAND ATIVO' : 'MOMENTÂNEO');
  } else if (btnNum === 1) { // SLEW CONTROL PUSH (SC)
    setCardActive('card-slewbtn', 'pill-slewbtn', isDown, isDown ? 'MATCH VELOCITY!' : 'LIVRE');
  } else if (btnNum >= 2 && btnNum <= 6) { // MIC SWITCH 5-WAY HAT (BTN 2..6)
    const micLabels = {
      2: 'MSP (RESET ENERGIA)',
      3: 'MSU (ESCUDOS 100%)',
      4: 'MSR (MOTORES 100%)',
      5: 'MSD (RESET ENERGIA)',
      6: 'MSL (ARMAS 100%)'
    };
    const visMic = document.getElementById('vis-mic');
    if (isDown) {
      setCardActive('card-mic', 'pill-mic', true, `BTN 0${btnNum} ATIVO`);
      if (visMic) visMic.textContent = `⚡ ${micLabels[btnNum]}`;
    } else {
      setCardActive('card-mic', 'pill-mic', false, 'CENTRO');
      if (visMic) visMic.textContent = '⚡ ENERGIA: EQUILIBRADA';
    }
  }
}

function set3PosLever(cardId, pinId, pillId, isUpBtn, isDown, upText, midText, dnText) {
  const card = document.getElementById(cardId);
  const pin = document.getElementById(pinId);
  const pill = document.getElementById(pillId);
  if (!pin || !pill) return;

  if (isUpBtn && isDown) {
    pin.className = 'lever-pin pos-up';
    pill.textContent = upText;
    if (card) card.classList.add('active');
  } else if (!isUpBtn && isDown) {
    pin.className = 'lever-pin pos-dn';
    pill.textContent = dnText;
    if (card) card.classList.add('active');
  } else if (!isDown) {
    pin.className = 'lever-pin pos-mid';
    pill.textContent = midText;
    if (card) card.classList.remove('active');
  }
}

function updateHatUI(data) {
  const dir = (data.direction || 'CENTER').toUpperCase();
  const isActive = dir !== 'CENTER';

  if (data.device === 'stick') {
    const visStickPov = document.getElementById('vis-stk-pov');
    const stickDirMap = {
      'UP': '⬆️ H1U: ENERGIA PROPULSORES (F6)',
      'RIGHT': '➡️ H1R: ENERGIA ESCUDOS (F7)',
      'LEFT': '⬅️ H1L: ENERGIA ARMAS (F5)',
      'DOWN': '⬇️ H1D: EQUILIBRAR ENERGIA (F8)',
      'CENTER': '🔋 CAPACITORES: EQUILÍBRIO'
    };
    setCardActive('card-stk-pov', 'pill-stk-pov', isActive, dir);
    if (visStickPov) visStickPov.textContent = stickDirMap[dir] || `🔋 ${dir}`;

    // Highlight visual map hat buttons for Stick
    ['up', 'right', 'down', 'left'].forEach(d => {
      const vHat = document.getElementById(`vbtn-stick-hat-${d}`);
      if (vHat) {
        if (dir === d.toUpperCase()) vHat.classList.add('active');
        else vHat.classList.remove('active');
      }
    });
    return;
  }

  if (data.device !== 'throttle') return;
  const visCoolie = document.getElementById('vis-coolie');
  const mapDir = {
    'UP': '⬆️ CSU: STRAFE CIMA',
    'DOWN': '⬇️ CSD: STRAFE BAIXO',
    'LEFT': '⬅️ CSL: STRAFE ESQUERDA',
    'RIGHT': '➡️ CSR: STRAFE DIREITA',
    'CENTER': '🕹️ STRAFE: NEUTRO'
  };
  setCardActive('card-coolie', 'pill-coolie', isActive, dir);
  if (visCoolie) visCoolie.textContent = mapDir[dir] || `🕹️ ${dir}`;

  // Highlight visual map hat buttons for Throttle Coolie Hat
  ['up', 'right', 'down', 'left'].forEach(d => {
    const vHat = document.getElementById(`vbtn-throttle-hat-${d}`);
    if (vHat) {
      if (dir === d.toUpperCase()) vHat.classList.add('active');
      else vHat.classList.remove('active');
    }
  });
}

function applyInitialThrottleState(data) {
  const mask = data.buttons_mask || 0;
  for (let b = 1; b <= 32; b++) {
    const pressed = Boolean(mask & (1 << (b - 1)));
    if (pressed) {
      updateSwitchUI({ device: 'throttle', button: b, is_down: true }, true);
      highlightCatalogButton('throttle', b, true);
    }
  }
  if (data.pov) {
    updateHatUI({ device: 'throttle', direction: data.pov });
  }
  const stickMask = data.stick_buttons_mask || 0;
  for (let sb = 1; sb <= 19; sb++) {
    const sPressed = Boolean(stickMask & (1 << (sb - 1)));
    if (sPressed) {
      updateSwitchUI({ device: 'stick', button: sb, is_down: true }, true);
      highlightCatalogButton('stick', sb, true);
    }
  }
  if (data.stick_pov) {
    updateHatUI({ device: 'stick', direction: data.stick_pov });
  }
}

function setCardActive(cardId, pillId, active, text) {
  const card = document.getElementById(cardId);
  const pill = document.getElementById(pillId);
  if (!card) return;
  if (active) card.classList.add('active'); else card.classList.remove('active');
  if (pill && text) pill.textContent = text;
}

// Profile application
function applyProfileData(profileId, profileData) {
  const pid = (profileId && CLIENT_PROFILES[profileId]) ? profileId : 'combat';
  currentProfile = pid;

  const fallback = CLIENT_PROFILES[pid] || CLIENT_PROFILES.combat;
  const merged = {
    ...fallback,
    ...(profileData || {}),
    ui_cards: {
      ...(fallback.ui_cards || {}),
      ...((profileData && profileData.ui_cards) || {})
    },
    mappings: {
      ...(fallback.mappings || {}),
      ...((profileData && profileData.mappings) || {})
    }
  };

  // 1. Botões de seleção de perfil no topo
  document.querySelectorAll('.prof-pill').forEach(p => p.classList.remove('active'));
  const btn = document.getElementById(`prof-${pid}`);
  if (btn) btn.classList.add('active');

  // 2. Banner de Perfil Operacional Ativo no Cockpit Deck
  const banner = document.getElementById('active-profile-banner');
  const titleEl = document.getElementById('active-prof-title');
  const descEl = document.getElementById('active-prof-desc');
  const highEl = document.getElementById('active-prof-highlights');
  const boostBadge = document.getElementById('badge-prof-boost');
  const curveBadge = document.getElementById('badge-prof-curve');
  const modeBadge = document.getElementById('badge-prof-mode');

  if (banner && merged.borderColor) {
    banner.style.borderLeftColor = merged.borderColor;
  }
  if (titleEl) titleEl.textContent = merged.name || fallback.name;
  if (descEl) descEl.textContent = merged.description || fallback.description;
  if (highEl) highEl.textContent = merged.highlights || fallback.highlights;

  const autoBoost = merged.afterburner_auto_boost !== undefined ? Boolean(merged.afterburner_auto_boost) : false;
  if (boostBadge) {
    boostBadge.textContent = autoBoost ? '🔥 Auto-Boost: ON' : '🛡️ Auto-Boost: OFF';
    boostBadge.style.background = autoBoost ? 'rgba(0, 230, 118, 0.14)' : 'rgba(255, 170, 0, 0.14)';
    boostBadge.style.color = autoBoost ? 'var(--neon-green)' : 'var(--neon-amber)';
    boostBadge.style.borderColor = autoBoost ? 'rgba(0, 230, 118, 0.35)' : 'rgba(255, 170, 0, 0.35)';
  }

  const cType = (merged.curve_type || 'expo').toUpperCase();
  const cExp = Number(merged.curve_exponent || 1.8).toFixed(1);
  if (curveBadge) {
    curveBadge.textContent = `📈 Curva: ${cType} ${cExp}`;
  }

  const isMiningMode = merged.split_throttle_mode === 'mining_laser';
  if (modeBadge) {
    modeBadge.textContent = isMiningMode ? '⛏️ Slider: Laser Mineração' : '🕹️ Slider: Limitador Veloc.';
  }

  // 3. Barra de Telemetria (Slider Label + Checkbox Auto-Boost + Estado Afterburner)
  const sliderRoleEl = document.getElementById('slider-role-label');
  if (sliderRoleEl && merged.slider_label) {
    sliderRoleEl.textContent = merged.slider_label;
  }

  const chkBoost = document.getElementById('chk-auto-boost');
  if (chkBoost) {
    chkBoost.checked = autoBoost;
  }
  const abLbl = document.getElementById('afterburner-status-label');
  if (abLbl) {
    abLbl.textContent = autoBoost ? 'Pronto (Auto LShift)' : 'Desativado neste Perfil';
    abLbl.style.color = autoBoost ? 'var(--neon-cyan)' : 'var(--text-dim)';
  }

  // 4. Sincronização das Curvas de Eixos (Aba Curvas & Slew)
  currentCurveType = merged.curve_type || 'expo';
  currentExponent = Number(merged.curve_exponent || 1.8);
  const selCurve = document.getElementById('select-curve-type');
  if (selCurve) selCurve.value = currentCurveType;
  const sldExp = document.getElementById('slider-exponent');
  if (sldExp) sldExp.value = Math.round(currentExponent * 10);
  const lblExp = document.getElementById('label-exponent');
  if (lblExp) lblExp.textContent = currentExponent.toFixed(1);
  drawCurveCanvas();

  // 5. Atualização Dinâmica das Etiquetas dos Cartões Físicos no Cockpit Deck
  const uc = merged.ui_cards || {};
  const setTxt = (id, txt) => {
    const el = document.getElementById(id);
    if (el && txt) el.textContent = txt;
  };
  setTxt('eac-sub', uc.eac_sub);
  setTxt('eac-tag', uc.eac_tag);
  setTxt('spdbrk-sub', uc.spdbrk_sub);
  setTxt('spdbrk-tag-a', uc.spdbrk_tag_a);
  setTxt('spdbrk-tag-b', uc.spdbrk_tag_b);
  setTxt('boat-sub', uc.boat_sub);
  setTxt('boat-tag-a', uc.boat_tag_a);
  setTxt('boat-tag-b', uc.boat_tag_b);
  setTxt('china-sub', uc.china_sub);
  setTxt('china-tag-a', uc.china_tag_a);
  setTxt('china-tag-b', uc.china_tag_b);
  setTxt('flaps-sub', uc.flaps_sub);
  setTxt('flaps-tag-a', uc.flaps_tag_a);
  setTxt('flaps-tag-b', uc.flaps_tag_b);

  // 6. Matriz de Pulsos & Scancodes
  if (merged.mappings) {
    populateMatrix(merged.mappings);
  }
}

// Live Axis Telemetry (Throttle Z, Rz, Slider1 + Slew X/Y + Stick X/Y)
function updateAxisTelemetry(data) {
  updateLiveAxisForCalibration(data);
  // 1. Slew Radar
  if (data.slew_x !== undefined && data.slew_y !== undefined) {
    const dot = document.getElementById('radar-slew-dot');
    if (dot) {
      const posX = (data.slew_x / 65535) * 100;
      const posY = (data.slew_y / 65535) * 100;
      dot.style.left = `${posX}%`;
      dot.style.top = `${posY}%`;
    }
    const sx = document.getElementById('val-slew-x');
    const sy = document.getElementById('val-slew-y');
    if (sx) sx.textContent = data.slew_x;
    if (sy) sy.textContent = data.slew_y;
  }

  // 2. Stick X / Y
  if (data.stick_x !== undefined) {
    const stx = document.getElementById('val-stick-x');
    const sty = document.getElementById('val-stick-y');
    if (stx) stx.textContent = data.stick_x;
    if (sty) sty.textContent = data.stick_y;
  }

  // 3. Throttle Handles (In Warthog hardware: 0 = 100% Forward, 65535 = 0% Idle Back)
  if (data.rz !== undefined) {
    const pctRz = Math.max(0, Math.min(100, Math.round(((65535 - data.rz) / 65535) * 100)));
    const valRz = document.getElementById('val-thr-rz');
    const barRz = document.getElementById('bar-thr-rz');
    if (valRz) valRz.textContent = `${pctRz}%`;
    if (barRz) barRz.style.width = `${pctRz}%`;
  }

  if (data.z !== undefined) {
    const pctZ = Math.max(0, Math.min(100, Math.round(((65535 - data.z) / 65535) * 100)));
    const valZ = document.getElementById('val-thr-z');
    const barZ = document.getElementById('bar-thr-z');
    if (valZ) valZ.textContent = `${pctZ}%`;
    if (barZ) barZ.style.width = `${pctZ}%`;
  }

  if (data.slider !== undefined) {
    const pctSl = Math.max(0, Math.min(100, Math.round(((65535 - data.slider) / 65535) * 100)));
    const valSl = document.getElementById('val-thr-slider');
    const barSl = document.getElementById('bar-thr-slider');
    if (valSl) valSl.textContent = `${pctSl}%`;
    if (barSl) barSl.style.width = `${pctSl}%`;
  }
}

function updateDeadzone(val) {
  document.getElementById('label-deadzone').textContent = `${val}%`;
  currentDeadzone = val / 100;
  const ring = document.getElementById('radar-deadzone-ring');
  if (ring) {
    const size = (val / 50) * 180;
    ring.style.width = `${size}px`;
    ring.style.height = `${size}px`;
  }
  drawCurveCanvas();
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'set_deadzone', value: parseInt(val) }));
  }
}

function updateYawAssist(val) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'set_yaw_assist', value: val }));
  }
}

// Curve Graph Renderer (Canvas)
function drawCurveCanvas() {
  const canvas = document.getElementById('curve-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;

  ctx.clearRect(0, 0, w, h);

  ctx.strokeStyle = 'rgba(0, 210, 255, 0.2)';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(0, h / 2);
  ctx.lineTo(w, h / 2);
  ctx.moveTo(w / 2, 0);
  ctx.lineTo(w / 2, h);
  ctx.stroke();

  const dzPx = currentDeadzone * (w / 2);
  ctx.fillStyle = 'rgba(255, 170, 0, 0.08)';
  ctx.fillRect((w / 2) - dzPx, 0, dzPx * 2, h);

  ctx.strokeStyle = '#00d2ff';
  ctx.lineWidth = 2.5;
  ctx.shadowColor = 'rgba(0, 210, 255, 0.6)';
  ctx.shadowBlur = 8;
  ctx.beginPath();

  const steps = 60;
  for (let i = 0; i <= steps; i++) {
    const normX = -1.0 + (2.0 * i / steps);
    let effectiveX = 0;
    if (Math.abs(normX) > currentDeadzone) {
      const sign = normX > 0 ? 1 : -1;
      effectiveX = sign * ((Math.abs(normX) - currentDeadzone) / (1.0 - currentDeadzone));
    }

    let normY = 0;
    if (currentCurveType === 'linear') {
      normY = effectiveX;
    } else if (currentCurveType === 'expo') {
      const sign = effectiveX >= 0 ? 1 : -1;
      normY = sign * Math.pow(Math.abs(effectiveX), currentExponent);
    } else if (currentCurveType === 's_curve') {
      const sign = effectiveX >= 0 ? 1 : -1;
      const ax = Math.abs(effectiveX);
      const smooth = (3.0 * ax * ax) - (2.0 * ax * ax * ax);
      normY = sign * (0.5 * smooth + 0.5 * Math.pow(ax, currentExponent));
    }

    const canvasX = (normX + 1.0) * 0.5 * w;
    const canvasY = h - ((normY + 1.0) * 0.5 * h);

    if (i === 0) ctx.moveTo(canvasX, canvasY);
    else ctx.lineTo(canvasX, canvasY);
  }
  ctx.stroke();
  ctx.shadowBlur = 0;
}

function changeCurveType(val) {
  currentCurveType = val;
  drawCurveCanvas();
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'set_curve_type', curve_type: val }));
  }
}

function changeCurveExponent(val) {
  currentExponent = parseFloat(val);
  document.getElementById('label-exponent').textContent = currentExponent.toFixed(1);
  drawCurveCanvas();
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'set_curve_exponent', exponent: currentExponent }));
  }
}

// Event Stream Log & Scroll Controls
function updateLogCountBadge() {
  const stream = document.getElementById('log-stream');
  const badge = document.getElementById('log-count-badge');
  if (!stream || !badge) return;
  const count = stream.children.length;
  badge.textContent = `${count} ${count === 1 ? 'registo' : 'registos'}`;
}

function logHardwareButton(data) {
  const nowStr = new Date().toLocaleTimeString('pt-PT', { hour12: false });
  const devLabel = data.device === 'stick' ? 'MANCHE (js1)' : 'MANETE (js2)';
  const bNumStr = String(data.button).padStart(2, '0');
  let btnName = `BTN ${bNumStr}`;
  let scAct = '';
  if (window.cachedCatalog) {
    const dict = data.device === 'stick' ? window.cachedCatalog.stick_buttons : window.cachedCatalog.throttle_buttons;
    if (dict && dict[data.button]) {
      btnName = `BTN ${bNumStr} • ${dict[data.button].name}`;
      scAct = dict[data.button].sc_action || '';
    }
  }
  const stateTxt = data.is_down ? '🟢 PREMIDO / ON' : '⚪ LIBERTADO / OFF';
  appendLog(nowStr, `${devLabel} [${btnName}]`, `${stateTxt}${scAct ? ' • ' + scAct : ''}`);
}

function logHardwareHat(data) {
  const nowStr = new Date().toLocaleTimeString('pt-PT', { hour12: false });
  const devLabel = data.device === 'stick' ? 'MANCHE (js1)' : 'MANETE (js2)';
  appendLog(nowStr, `${devLabel} [POV HAT]`, `Direção: ${data.direction}`);
}

function appendLog(timestamp, text, keyHit = '') {
  const stream = document.getElementById('log-stream');
  if (!stream) return;

  const entry = document.createElement('div');
  entry.className = 'log-entry';

  const timeSpan = document.createElement('span');
  timeSpan.className = 'timestamp';
  timeSpan.textContent = `[${timestamp}]`;

  const textNode = document.createTextNode(` ${text} `);
  entry.appendChild(timeSpan);
  entry.appendChild(textNode);

  if (keyHit) {
    const keySpan = document.createElement('span');
    keySpan.className = 'key-hit';
    keySpan.textContent = `➔ [${keyHit}]`;
    entry.appendChild(keySpan);
  }

  stream.appendChild(entry);

  // Limitar a 250 registos para manter o scroll fluido
  while (stream.children.length > 250) {
    stream.removeChild(stream.firstChild);
  }

  updateLogCountBadge();

  const autoScrollChk = document.getElementById('chk-log-autoscroll');
  if (!autoScrollChk || autoScrollChk.checked) {
    stream.scrollTop = stream.scrollHeight;
  }
}

function scrollLogToTop() {
  const stream = document.getElementById('log-stream');
  if (stream) stream.scrollTop = 0;
}

function scrollLogToBottom() {
  const stream = document.getElementById('log-stream');
  if (stream) stream.scrollTop = stream.scrollHeight;
}

function clearLogStream() {
  initAudio();
  playCockpitSound('click');
  const stream = document.getElementById('log-stream');
  if (!stream) return;
  const nowStr = new Date().toLocaleTimeString('pt-PT', { hour12: false });
  stream.innerHTML = `
    <div class="log-entry">
      <span class="timestamp">[${nowStr}]</span> Registo limpo. A aguardar eventos dos botões físicos...
    </div>`;
  updateLogCountBadge();
}

// Auto-Doctor UI Renderer
function renderDiagnosis(data) {
  const banner = document.getElementById('doctor-banner');
  const title = document.getElementById('doctor-title');
  const desc = document.getElementById('doctor-desc');
  const js1Name = document.getElementById('diag-js1-name');
  const js2Name = document.getElementById('diag-js2-name');
  const anomaliesBox = document.getElementById('anomalies-box');

  if (data.healthy) {
    banner.className = 'glass-panel health-banner hud-brackets healthy';
    title.textContent = '✅ Thrusters, Manche (19B) e Manete (32B) Perfeitamente Sincronizados';
    desc.textContent = 'Nenhum bloqueio de Speed Limiter ou inversão de eixos no actionmaps.xml.';
  } else {
    banner.className = 'glass-panel health-banner hud-brackets warning';
    title.textContent = '⚠️ Anomalias de Thrusters / Controlos Detetadas no Star Citizen';
    desc.textContent = data.summary;
  }

  if (data.instances && data.instances['1']) {
    js1Name.textContent = data.instances['1'].product || 'Vazio / Não configurado';
  }
  if (data.instances && data.instances['2']) {
    js2Name.textContent = data.instances['2'].product || 'Vazio / Não configurado';
  }

  if (data.anomalies && data.anomalies.length > 0) {
    anomaliesBox.innerHTML = data.anomalies.map(a => `• ${a}`).join('<br>');
  } else {
    anomaliesBox.innerHTML = '✅ Nenhuma anomalia detetada! Todos os eixos e botões estão prontos.';
  }
}

// Actions from UI
function manualTrigger(actionId) {
  initAudio();
  triggerShipVoiceForAction(actionId);
  playCockpitSound('chirp');
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'trigger_action', action_id: actionId }));
  }
}

function fixActionMaps() {
  initAudio();
  playCockpitSound('chirp');
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'fix_actionmaps' }));
  }
}

function installProfile() {
  initAudio();
  playCockpitSound('chirp');
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'install_profile' }));
  }
}

function createBackup() {
  initAudio();
  playCockpitSound('chirp');
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'create_backup' }));
  }
}

function requestDiagnosis() {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'request_diagnosis' }));
  }
}

function populateConfig(cfg) {
  if (!cfg) return;
  if (cfg.slew_deadzone_percent) {
    document.getElementById('slider-deadzone').value = cfg.slew_deadzone_percent;
    updateDeadzone(cfg.slew_deadzone_percent);
  }
  if (cfg.virtual_yaw_assist !== undefined) {
    document.getElementById('chk-yaw-assist').checked = cfg.virtual_yaw_assist;
  }
  if (cfg.active_profile) {
    const localProf = CLIENT_PROFILES[cfg.active_profile] || CLIENT_PROFILES.combat;
    applyProfileData(cfg.active_profile, {
      ...localProf,
      curve_type: cfg.curve_type || localProf.curve_type,
      curve_exponent: cfg.curve_exponent || localProf.curve_exponent,
      afterburner_auto_boost: cfg.afterburner_auto_boost !== undefined ? cfg.afterburner_auto_boost : localProf.afterburner_auto_boost,
      mappings: cfg.mappings || localProf.mappings
    });
  } else {
    if (cfg.curve_exponent) {
      currentExponent = cfg.curve_exponent;
      document.getElementById('slider-exponent').value = Math.round(cfg.curve_exponent * 10);
      document.getElementById('label-exponent').textContent = cfg.curve_exponent.toFixed(1);
    }
    if (cfg.curve_type) {
      currentCurveType = cfg.curve_type;
      document.getElementById('select-curve-type').value = cfg.curve_type;
    }
    drawCurveCanvas();
    if (cfg.mappings) {
      populateMatrix(cfg.mappings);
    }
  }
}

// State for Matrix Filtering & Modal Editor
let cachedMatrixMappings = {};
let matrixFilterSearch = '';
let matrixCategoryFilter = 'all';
let editingActionId = null;
let isKeyCapturing = false;

function getActionCategory(actionId) {
  if (actionId.endsWith('_SHIFT') || actionId.startsWith('S2_SHIFT') || actionId.startsWith('S1_SHIFT') || (actionId.startsWith('TMS_') && actionId.includes('SHIFT')) || (actionId.startsWith('DMS_') && actionId.includes('SHIFT')) || (actionId.startsWith('CMS_') && actionId.includes('SHIFT'))) {
    return { id: 'shift', label: 'Camada Shift S4', color: 'var(--neon-amber)' };
  }
  if (actionId.startsWith('STICK_BTN_') || actionId.startsWith('TRIM_HAT_')) {
    return { id: 'stick', label: 'Manche A-10C', color: 'var(--neon-green)' };
  }
  if (actionId.startsWith('CHINA_') || actionId.startsWith('MIC_') || actionId.startsWith('SLEW_') || 
      actionId.startsWith('LTB_') || actionId.startsWith('VISOR_') || actionId.startsWith('SPDBRK_') || 
      actionId.startsWith('BOAT_') || actionId.startsWith('PINKY_') || actionId.startsWith('COOLIE_')) {
    return { id: 'throttle_grips', label: 'Punhos Manete', color: 'var(--neon-cyan)' };
  }
  return { id: 'throttle_base', label: 'Base Manete', color: '#88aaff' };
}

function filterMatrixTable(searchTerm) {
  matrixFilterSearch = (searchTerm || '').trim().toLowerCase();
  renderMatrixRows();
}

function setMatrixCategoryFilter(cat, btnElement) {
  matrixCategoryFilter = cat || 'all';
  document.querySelectorAll('.matrix-cat-btn').forEach(b => b.classList.remove('active'));
  if (btnElement) btnElement.classList.add('active');
  renderMatrixRows();
}

function renderMatrixRows() {
  const tbody = document.getElementById('matrix-tbody');
  const countBadge = document.getElementById('matrix-count-badge');
  if (!tbody) return;
  tbody.innerHTML = '';

  const entries = Object.entries(cachedMatrixMappings);
  let visibleCount = 0;

  for (const [id, m] of entries) {
    const cat = getActionCategory(id);

    // Apply category filter
    if (matrixCategoryFilter !== 'all' && cat.id !== matrixCategoryFilter) {
      continue;
    }

    // Apply search filter
    const keyStr = (m.key || '').toLowerCase();
    const modsStr = (m.modifiers || []).join(' ').toLowerCase();
    const descStr = (m.desc || '').toLowerCase();
    const idStr = id.toLowerCase();
    if (matrixFilterSearch) {
      const match = idStr.includes(matrixFilterSearch) || 
                    descStr.includes(matrixFilterSearch) || 
                    keyStr.includes(matrixFilterSearch) || 
                    modsStr.includes(matrixFilterSearch) ||
                    cat.label.toLowerCase().includes(matrixFilterSearch);
      if (!match) continue;
    }

    visibleCount++;
    const tr = document.createElement('tr');
    tr.style.borderBottom = '1px solid rgba(255, 255, 255, 0.05)';
    tr.style.transition = 'background 0.15s';
    tr.onmouseenter = () => { tr.style.background = 'rgba(0, 210, 255, 0.06)'; };
    tr.onmouseleave = () => { tr.style.background = ''; };

    const modsArray = m.modifiers || [];
    const hasKey = Boolean(m.key && m.key.trim());
    
    let keyBadgeHtml = '';
    if (hasKey) {
      const parts = [];
      for (const mod of modsArray) {
        parts.push(`<span class="key-badge mod">${mod}</span>`);
      }
      parts.push(`<span class="key-badge">${m.key}</span>`);
      keyBadgeHtml = parts.join(' + ');
    } else {
      keyBadgeHtml = `<span class="key-badge dim">Desativado / Nativo</span>`;
    }

    tr.innerHTML = `
      <td style="padding: 10px 12px; font-weight: bold;">
        <span style="color: var(--neon-cyan);">${id}</span><br>
        <span style="font-size: 10px; color: ${cat.color}; font-weight: normal;">${cat.label}</span>
      </td>
      <td style="padding: 10px 12px; color: #fff; font-size: 12px;">${m.desc || id}</td>
      <td style="padding: 10px 12px;">${keyBadgeHtml}</td>
      <td style="padding: 10px 12px; color: var(--neon-amber);">${modsArray.join('+') || '<span style="color:var(--text-dim)">Nenhum</span>'}</td>
      <td style="padding: 10px 12px; color: var(--text-dim);">${m.hold_ms || 60}ms</td>
      <td style="padding: 10px 12px; text-align: right; white-space: nowrap;">
        <button class="edit-btn-pill" onclick="openKeyEditorModal('${id}')" title="Editar tecla e modificadores">✏️ Editar</button>
        <button class="btn-secondary" style="padding: 3px 8px; font-size: 11px; margin-left: 4px;" onclick="manualTrigger('${id}')" title="Testar envio do pulso DirectInput">⚡ Testar</button>
        <button class="btn-secondary" style="padding: 3px 8px; font-size: 11px; margin-left: 4px; color: var(--neon-red);" onclick="quickClearKey('${id}')" title="Limpar tecla (deixar como nativo)">❌</button>
      </td>
    `;
    tbody.appendChild(tr);
  }

  if (countBadge) {
    countBadge.textContent = `${visibleCount} ${visibleCount === 1 ? 'ação' : 'ações'}`;
  }
  renderVisualMapping();
}

function populateMatrix(mappings) {
  if (!mappings) return;
  cachedMatrixMappings = { ...mappings };
  const tagEl = document.getElementById('matrix-active-profile-tag');
  if (tagEl && CLIENT_PROFILES[currentProfile]) {
    tagEl.textContent = CLIENT_PROFILES[currentProfile].name || currentProfile;
  }
  renderMatrixRows();
}

// Modal Open / Close
function openKeyEditorModal(actionId) {
  initAudio();
  playCockpitSound('chirp');
  editingActionId = actionId;
  const m = cachedMatrixMappings[actionId] || { key: '', modifiers: [], desc: actionId, hold_ms: 60 };

  document.getElementById('modal-action-id').textContent = actionId;
  document.getElementById('modal-input-desc').value = m.desc || actionId;
  document.getElementById('modal-input-key').value = m.key || '';
  
  const mods = m.modifiers || [];
  document.getElementById('modal-chk-alt').checked = mods.includes('ALT');
  document.getElementById('modal-chk-ctrl').checked = mods.includes('CTRL');
  document.getElementById('modal-chk-shift').checked = mods.includes('SHIFT');

  const hold = m.hold_ms !== undefined ? m.hold_ms : 60;
  document.getElementById('modal-slider-hold').value = hold;
  document.getElementById('modal-hold-display').textContent = `${hold}ms`;

  populateMacroSelects();
  const selMacro = document.getElementById('modal-select-macro');
  if (selMacro) selMacro.value = m.macro_id || '';

  const longKeyEl = document.getElementById('modal-input-long-key');
  if (longKeyEl) longKeyEl.value = m.long_key || '';
  const selLongMacro = document.getElementById('modal-select-long-macro');
  if (selLongMacro) selLongMacro.value = m.long_macro_id || '';
  const lMods = m.long_modifiers || [];
  const lAlt = document.getElementById('modal-chk-long-alt');
  const lCtrl = document.getElementById('modal-chk-long-ctrl');
  const lShift = document.getElementById('modal-chk-long-shift');
  if (lAlt) lAlt.checked = lMods.includes('ALT');
  if (lCtrl) lCtrl.checked = lMods.includes('CTRL');
  if (lShift) lShift.checked = lMods.includes('SHIFT');
  const lThresh = m.long_threshold_ms || 450;
  const lSlider = document.getElementById('modal-slider-long-threshold');
  const lDisp = document.getElementById('modal-long-threshold-display');
  if (lSlider) lSlider.value = lThresh;
  if (lDisp) lDisp.textContent = `${lThresh}ms`;

  stopKeyCapture();
  updateModalPreview();

  const modal = document.getElementById('key-editor-modal');
  if (modal) modal.classList.add('active');
}

function closeKeyEditorModal() {
  stopKeyCapture();
  const modal = document.getElementById('key-editor-modal');
  if (modal) modal.classList.remove('active');
  editingActionId = null;
}

function updateHoldDurationDisplay(val) {
  document.getElementById('modal-hold-display').textContent = `${val}ms`;
}

function updateModalPreview() {
  const key = document.getElementById('modal-input-key').value.trim().toUpperCase();
  const alt = document.getElementById('modal-chk-alt').checked;
  const ctrl = document.getElementById('modal-chk-ctrl').checked;
  const shift = document.getElementById('modal-chk-shift').checked;

  const display = document.getElementById('modal-key-display');
  if (!key) {
    display.textContent = 'NENHUMA (Nativo DirectInput)';
    display.style.color = 'var(--text-dim)';
    return;
  }

  const parts = [];
  if (ctrl) parts.push('CTRL');
  if (alt) parts.push('ALT');
  if (shift) parts.push('SHIFT');
  parts.push(key);

  display.textContent = parts.join(' + ');
  display.style.color = 'var(--neon-cyan)';
}

function selectMouseKey(mouseKey) {
  initAudio();
  document.getElementById('modal-input-key').value = mouseKey;
  stopKeyCapture();
  updateModalPreview();
  playCockpitSound('chirp');
}

function startKeyCapture() {
  initAudio();
  playCockpitSound('chirp');
  isKeyCapturing = true;
  window._captureStartTs = Date.now();
  const box = document.getElementById('modal-key-listener-box');
  const status = document.getElementById('modal-listener-status');
  if (box) box.classList.add('listening');
  if (status) {
    status.textContent = '🔴 A OUVIR TECLADO... PRESSIONA A TECLA DESEJADA (OU ESC PARA CANCELAR)';
    status.style.color = 'var(--neon-amber)';
  }
}

function stopKeyCapture() {
  isKeyCapturing = false;
  const box = document.getElementById('modal-key-listener-box');
  const status = document.getElementById('modal-listener-status');
  if (box) box.classList.remove('listening');
  if (status) {
    status.textContent = '🖱️ Clica aqui para capturar tecla automaticamente';
    status.style.color = 'var(--neon-cyan)';
  }
}

function handleGlobalKeyCapture(event) {
  const modal = document.getElementById('key-editor-modal');
  if (!modal || !modal.classList.contains('active')) return;

  if (event.key === 'Escape') {
    if (isKeyCapturing) {
      stopKeyCapture();
    } else {
      closeKeyEditorModal();
    }
    return;
  }

  if (!isKeyCapturing) return;

  event.preventDefault();
  event.stopPropagation();

  const isShift = event.shiftKey;
  const isCtrl = event.ctrlKey;
  const isAlt = event.altKey;

  // Ignore if pressed ONLY modifier
  if (['Shift', 'Control', 'Alt', 'Meta'].includes(event.key)) {
    document.getElementById('modal-chk-shift').checked = isShift;
    document.getElementById('modal-chk-ctrl').checked = isCtrl;
    document.getElementById('modal-chk-alt').checked = isAlt;
    updateModalPreview();
    return;
  }

  let keyName = event.key.toUpperCase();
  if (keyName === ' ') keyName = 'SPACE';
  else if (keyName === 'ARROWUP') keyName = 'UP';
  else if (keyName === 'ARROWDOWN') keyName = 'DOWN';
  else if (keyName === 'ARROWLEFT') keyName = 'LEFT';
  else if (keyName === 'ARROWRIGHT') keyName = 'RIGHT';
  else if (event.code && event.code.startsWith('Numpad')) {
    keyName = event.code.toUpperCase().replace('NUMPAD', 'NUM');
  }

  // Star Citizen safety rule: never allow Shift+Z conflict
  if (keyName === 'Z' && isShift) {
    alert('Aviso: A combinação Shift+Z causa conflito no Star Citizen ("Fly mode cannot be activated"). Escolha outra tecla.');
    stopKeyCapture();
    return;
  }

  document.getElementById('modal-input-key').value = keyName;
  document.getElementById('modal-chk-shift').checked = isShift;
  document.getElementById('modal-chk-ctrl').checked = isCtrl;
  document.getElementById('modal-chk-alt').checked = isAlt;

  stopKeyCapture();
  updateModalPreview();
  playCockpitSound('chirp');
}

function saveModalKey() {
  if (!editingActionId) return;
  initAudio();
  playCockpitSound('click');

  const key = document.getElementById('modal-input-key').value.trim().toUpperCase();
  const desc = document.getElementById('modal-input-desc').value.trim() || editingActionId;
  const hold = parseInt(document.getElementById('modal-slider-hold').value, 10) || 60;

  const mods = [];
  if (document.getElementById('modal-chk-alt').checked) mods.push('ALT');
  if (document.getElementById('modal-chk-ctrl').checked) mods.push('CTRL');
  if (document.getElementById('modal-chk-shift').checked) mods.push('SHIFT');

  const macroId = (document.getElementById('modal-select-macro')?.value || '').trim();
  const longKey = (document.getElementById('modal-input-long-key')?.value || '').trim().toUpperCase();
  const longMacroId = (document.getElementById('modal-select-long-macro')?.value || '').trim();
  const longMods = [];
  if (document.getElementById('modal-chk-long-alt')?.checked) longMods.push('ALT');
  if (document.getElementById('modal-chk-long-ctrl')?.checked) longMods.push('CTRL');
  if (document.getElementById('modal-chk-long-shift')?.checked) longMods.push('SHIFT');
  const longThresh = parseInt(document.getElementById('modal-slider-long-threshold')?.value || '450', 10);

  const payload = {
    type: 'update_mapping',
    action_id: editingActionId,
    key: key,
    modifiers: mods,
    desc: desc,
    hold_ms: hold,
    macro_id: macroId,
    long_key: longKey,
    long_modifiers: longMods,
    long_macro_id: longMacroId,
    long_threshold_ms: longThresh
  };

  cachedMatrixMappings[editingActionId] = {
    key: key,
    modifiers: mods,
    desc: desc,
    hold_ms: hold,
    macro_id: macroId,
    long_key: longKey,
    long_modifiers: longMods,
    long_macro_id: longMacroId,
    long_threshold_ms: longThresh
  };

  if (CLIENT_PROFILES[currentProfile]) {
    CLIENT_PROFILES[currentProfile].mappings[editingActionId] = { ...cachedMatrixMappings[editingActionId] };
  }

  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(payload));
  }

  renderMatrixRows();
  closeKeyEditorModal();
}

function clearCurrentModalKey() {
  document.getElementById('modal-input-key').value = '';
  document.getElementById('modal-chk-alt').checked = false;
  document.getElementById('modal-chk-ctrl').checked = false;
  document.getElementById('modal-chk-shift').checked = false;
  updateModalPreview();
  saveModalKey();
}

function quickClearKey(actionId) {
  initAudio();
  playCockpitSound('click');
  if (!cachedMatrixMappings[actionId]) return;
  cachedMatrixMappings[actionId].key = '';
  cachedMatrixMappings[actionId].modifiers = [];

  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({
      type: 'update_mapping',
      action_id: actionId,
      key: '',
      modifiers: [],
      desc: cachedMatrixMappings[actionId].desc,
      hold_ms: cachedMatrixMappings[actionId].hold_ms || 60
    }));
  }
  renderMatrixRows();
}

function testModalKey() {
  initAudio();
  playCockpitSound('chirp');
  if (editingActionId && ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'trigger_action', action_id: editingActionId }));
  }
}

function saveAllCurrentMappings() {
  initAudio();
  playCockpitSound('chirp');
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'save_all_mappings', mappings: cachedMatrixMappings }));
  }
}

function resetActiveProfileMappings() {
  if (confirm(`Tem a certeza que deseja restaurar as teclas padrão de fábrica para o perfil "${CLIENT_PROFILES[currentProfile]?.name || currentProfile}"?`)) {
    initAudio();
    playCockpitSound('chirp');
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'reset_profile_mappings', profile: currentProfile }));
    }
  }
}

function onMappingUpdated(data) {
  if (data.mappings) {
    cachedMatrixMappings = { ...data.mappings };
    if (CLIENT_PROFILES[data.profile_id]) {
      CLIENT_PROFILES[data.profile_id].mappings = { ...data.mappings };
    }
    renderMatrixRows();
  }
}

// Start WebSocket & Event Listeners on Load
window.addEventListener('DOMContentLoaded', () => {
  renderVisualMapping();
  connectWebSocket();
  document.body.addEventListener('click', initAudio, { once: true });
  window.addEventListener('keydown', handleGlobalKeyCapture, true);

  const lBox = document.getElementById('modal-key-listener-box');
  if (lBox) {
    lBox.addEventListener('wheel', (e) => {
      if (!isKeyCapturing) return;
      e.preventDefault();
      const wheelKey = e.deltaY < 0 ? 'MWHEEL_UP' : 'MWHEEL_DOWN';
      selectMouseKey(wheelKey);
    });
    lBox.addEventListener('mousedown', (e) => {
      if (!isKeyCapturing) return;
      // Avoid capturing the initial left-click that triggered startKeyCapture()
      if (Date.now() - (window._captureStartTs || 0) < 180) return;
      e.preventDefault();
      e.stopPropagation();
      const btnMap = { 0: 'MOUSE1', 1: 'MOUSE3', 2: 'MOUSE2', 3: 'MOUSE4', 4: 'MOUSE5' };
      const mapped = btnMap[e.button];
      if (mapped) {
        selectMouseKey(mapped);
      }
    });
    lBox.addEventListener('contextmenu', (e) => {
      if (isKeyCapturing) e.preventDefault();
    });
  }

  const modal = document.getElementById('key-editor-modal');
  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeKeyEditorModal();
    });
  }

  setTimeout(drawCurveCanvas, 200);
});


// ==============================================================================
// FEATURE 1: MACROS & MULTI-STEP SEQUENCES STUDIO
// ==============================================================================
let cachedMacros = {
  macro_full_landing: {
    id: 'macro_full_landing',
    name: 'Aterragem Completa (ATC + Trem + VTOL + Faróis)',
    icon: '🛬',
    steps: [
      { key: 'N', modifiers: ['ALT'], hold_ms: 80, delay_after_ms: 450, note: 'Chamar Torre ATC' },
      { key: 'N', modifiers: [], hold_ms: 80, delay_after_ms: 350, note: 'Baixar Trem' },
      { key: 'K', modifiers: [], hold_ms: 80, delay_after_ms: 350, note: 'Ativar VTOL' },
      { key: 'L', modifiers: [], hold_ms: 80, delay_after_ms: 0, note: 'Ligar Faróis' }
    ]
  }
};
let editingMacroId = null;
let editingMacroSteps = [];

function renderMacrosList() {
  const cont = document.getElementById('macros-list-container');
  if (!cont) return;
  const entries = Object.values(cachedMacros);
  if (!entries.length) {
    cont.innerHTML = `<div style="font-size:12px; color:var(--text-dim); padding:10px;">Nenhuma macro criada. Clica em "+ Nova Macro".</div>`;
    return;
  }
  cont.innerHTML = entries.map(m => `
    <div class="macro-card">
      <div style="display:flex; align-items:center; gap:10px; min-width:0;">
        <span style="font-size:18px;">${m.icon || '⚡'}</span>
        <div style="min-width:0;">
          <div style="font-weight:700; font-size:13px; color:#fff; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${m.name}</div>
          <div style="font-family:var(--font-mono); font-size:10.5px; color:var(--text-secondary);">
            ${(m.steps || []).length} passos • ${(m.steps || []).map(s => ((s.modifiers||[]).length ? s.modifiers.join('+')+'+' : '') + s.key).join(' ➔ ')}
          </div>
        </div>
      </div>
      <div style="display:flex; gap:5px; flex-shrink:0;">
        <button class="btn-secondary" style="padding:3px 8px; font-size:11px;" onclick="runMacro('${m.id}')" title="Executar Macro Agora">▶</button>
        <button class="edit-btn-pill" onclick="openMacroEditor('${m.id}')" title="Editar Passos">✏️</button>
        <button class="btn-secondary" style="padding:3px 7px; font-size:11px; color:var(--mil-red);" onclick="deleteMacro('${m.id}')" title="Eliminar Macro">🗑️</button>
      </div>
    </div>
  `).join('');

  if (!editingMacroId && entries.length > 0) {
    openMacroEditor(entries[0].id);
  }
}

function createNewMacro() {
  editingMacroId = 'macro_' + Date.now();
  editingMacroSteps = [{ key: 'N', modifiers: [], hold_ms: 80, delay_after_ms: 300, note: 'Passo 1' }];
  document.getElementById('macro-editing-id').textContent = editingMacroId;
  document.getElementById('macro-input-icon').value = '⚡';
  document.getElementById('macro-input-name').value = 'Nova Sequência Tática';
  const vEl = document.getElementById('macro-input-voice'); if (vEl) vEl.value = '';
  renderMacroSteps();
}

function openMacroEditor(macroId) {
  const m = cachedMacros[macroId];
  if (!m) return;
  editingMacroId = m.id;
  editingMacroSteps = JSON.parse(JSON.stringify(m.steps || []));
  const idEl = document.getElementById('macro-editing-id');
  if (idEl) idEl.textContent = m.id;
  const iconEl = document.getElementById('macro-input-icon');
  if (iconEl) iconEl.value = m.icon || '⚡';
  const nameEl = document.getElementById('macro-input-name');
  if (nameEl) nameEl.value = m.name || '';
  const voiceEl = document.getElementById('macro-input-voice');
  if (voiceEl) voiceEl.value = m.voice_text || '';
  renderMacroSteps();
}

function renderMacroSteps() {
  const cont = document.getElementById('macro-steps-container');
  if (!cont) return;
  cont.innerHTML = editingMacroSteps.map((s, idx) => `
    <div class="macro-step-row">
      <span style="color:var(--mil-amber); font-weight:700;">#${idx + 1}</span>
      <input type="text" class="form-input" style="padding:3px 6px; font-size:11px;" value="${s.key || ''}" placeholder="Tecla/Rato" onchange="editingMacroSteps[${idx}].key = this.value.trim().toUpperCase()">
      <div style="display:flex; gap:5px; align-items:center; flex-wrap:wrap;">
        <label style="font-size:10px; cursor:pointer;"><input type="checkbox" ${(s.modifiers||[]).includes('ALT') ? 'checked' : ''} onchange="toggleMacroStepMod(${idx}, 'ALT', this.checked)"> ALT</label>
        <label style="font-size:10px; cursor:pointer;"><input type="checkbox" ${(s.modifiers||[]).includes('CTRL') ? 'checked' : ''} onchange="toggleMacroStepMod(${idx}, 'CTRL', this.checked)"> CTRL</label>
        <label style="font-size:10px; cursor:pointer;"><input type="checkbox" ${(s.modifiers||[]).includes('SHIFT') ? 'checked' : ''} onchange="toggleMacroStepMod(${idx}, 'SHIFT', this.checked)"> SHIFT</label>
      </div>
      <input type="number" class="form-input" style="padding:3px 5px; font-size:11px;" value="${s.hold_ms || 80}" min="20" max="1500" title="Pulso (ms)" onchange="editingMacroSteps[${idx}].hold_ms = parseInt(this.value||80,10)">
      <input type="number" class="form-input" style="padding:3px 5px; font-size:11px;" value="${s.delay_after_ms || 0}" min="0" max="5000" title="Pausa após passo (ms)" onchange="editingMacroSteps[${idx}].delay_after_ms = parseInt(this.value||0,10)">
      <button class="btn-secondary" style="padding:2px 5px; font-size:10px; color:var(--mil-red);" onclick="removeMacroStep(${idx})" title="Remover passo">✕</button>
    </div>
  `).join('');
}

function toggleMacroStepMod(idx, mod, checked) {
  const mods = new Set(editingMacroSteps[idx].modifiers || []);
  if (checked) mods.add(mod); else mods.delete(mod);
  editingMacroSteps[idx].modifiers = Array.from(mods);
}

function addMacroStep() {
  editingMacroSteps.push({ key: 'SPACE', modifiers: [], hold_ms: 80, delay_after_ms: 250, note: '' });
  renderMacroSteps();
}

function removeMacroStep(idx) {
  editingMacroSteps.splice(idx, 1);
  renderMacroSteps();
}

function saveCurrentMacro() {
  if (!editingMacroId) editingMacroId = 'macro_' + Date.now();
  const macro = {
    id: editingMacroId,
    icon: (document.getElementById('macro-input-icon')?.value || '⚡').trim(),
    name: (document.getElementById('macro-input-name')?.value || 'Macro Personalizada').trim(),
    voice_text: (document.getElementById('macro-input-voice')?.value || '').trim(),
    steps: editingMacroSteps.filter(s => s.key && s.key.trim())
  };
  cachedMacros[macro.id] = macro;
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'save_macro', macro }));
  }
  playCockpitSound('chirp');
  renderMacrosList();
  populateMacroSelects();
}

function deleteMacro(macroId) {
  if (!confirm('Eliminar esta macro permanentemente?')) return;
  delete cachedMacros[macroId];
  if (editingMacroId === macroId) editingMacroId = null;
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'delete_macro', macro_id: macroId }));
  }
  renderMacrosList();
  populateMacroSelects();
}

function runMacro(macroId) {
  initAudio();
  playCockpitSound('chirp');
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'run_macro', macro_id: macroId }));
  }
}

function testCurrentEditorMacro() {
  saveCurrentMacro();
  if (editingMacroId) runMacro(editingMacroId);
}

function populateMacroSelects() {
  const selShort = document.getElementById('modal-select-macro');
  const selLong = document.getElementById('modal-select-long-macro');
  const entries = Object.values(cachedMacros);
  const optsShort = '<option value="">— Nenhuma Macro (Usar Tecla/Rato acima) —</option>' +
    entries.map(m => `<option value="${m.id}">${m.icon || '⚡'} ${m.name}</option>`).join('');
  const optsLong = '<option value="">— Nenhuma Macro —</option>' +
    entries.map(m => `<option value="${m.id}">${m.icon || '⚡'} ${m.name}</option>`).join('');
  if (selShort) {
    const v = selShort.value;
    selShort.innerHTML = optsShort;
    selShort.value = v;
  }
  if (selLong) {
    const v = selLong.value;
    selLong.innerHTML = optsLong;
    selLong.value = v;
  }
}

// ==============================================================================
// FEATURE 2: COMPUTADOR DE BORDO POR VOZ (SHIP AI VOICE - AEGIS / ANVIL TTS)
// ==============================================================================
let voiceSettings = { enabled: true, lang: 'en', rate: 1.05, pitch: 0.85, volume: 0.85 };
let _lastVoiceSpokenTs = 0;
let _lastVoiceText = '';

const VOICE_CALLOUTS = {
  en: {
    APU_ON: 'Systems online. Flight ready.',
    APU_OFF: 'Powering down ship systems.',
    EAC_ON: 'Master mode. Navigation.',
    EAC_OFF: 'Master mode. Standard combat.',
    RDR_ALTM_ON: 'Landing gear retracted.',
    RDR_ALTM_OFF: 'Landing gear deployed.',
    FLAPS_DN: 'VTOL thrusters engaged.',
    FLAPS_MID: 'Flight mode normal.',
    FLAPS_UP: 'Cruise control toggled.',
    BOAT_FWD: 'Quantum drive spooling.',
    BOAT_AFT: 'Weapons mode active.',
    BOAT_MID: 'Mode neutral.',
    SPDBRK_FWD: 'Cruise control engaged.',
    SPDBRK_AFT: 'Space brake engaged.',
    SPDBRK_MID: 'Cruise control disengaged.',
    PINKY_FWD: 'Exterior headlights on.',
    PINKY_AFT: 'Cabin lights toggled.',
    PINKY_MID: 'Exterior headlights off.',
    LDGHORN_PRESS: 'Requesting landing clearance.',
    AP_ENGAGE_PRESS: 'Requesting landing clearance.',
    AP_PATH: 'Exterior doors opening.',
    AP_ALT: 'Ship doors locked.',
    AP_MID: 'Exterior doors closing.',
    SHIFT_MODIFIER_ON: 'Shift layer active.',
    FUEL_L_ON: 'Thrusters online.',
    FUEL_L_OFF: 'Thrusters offline.',
    FUEL_R_ON: 'Weapons online.',
    FUEL_R_OFF: 'Weapons offline.',
    ENG_L_IGN: 'Helmet visor wiped.',
    ENG_L_MOTOR: 'Left engine offline.',
    ENG_L_NORM: 'Left engine online.',
    ENG_R_IGN: 'Warning. Ejection sequence.',
    ENG_R_MOTOR: 'Weapons offline.',
    ENG_R_NORM: 'Weapons online.',
    IDLE_L_OFF: 'Left throttle cutoff.',
    IDLE_R_OFF: 'Right throttle cutoff.',
    IDLE_L_IDLE: 'Left throttle idle ready.',
    IDLE_R_IDLE: 'Right throttle idle ready.',
    LTB_PRESS: 'Flight ready.',
    CHINA_FWD_PRESS: 'Boost engaged.',
    CHINA_AFT_PRESS: 'Reverse thrust.',
    MIC_UP_PRESS: 'Scanner mode.',
    MIC_DOWN_PRESS: 'Mining mode.',
    MIC_RIGHT_PRESS: 'External camera.',
    SLEW_PUSH_PRESS: 'Target speed matched.',
    TRIM_HAT_UP: 'Power to engines.',
    TRIM_HAT_RIGHT: 'Power to shields.',
    TRIM_HAT_LEFT: 'Power to weapons.',
    TRIM_HAT_DOWN: 'Power balanced.',
    STICK_BTN_2: 'Missile lock.',
    STICK_BTN_5: 'Master mode toggled.',
    STICK_BTN_11: 'Radar ping.',
    STICK_BTN_15: 'Noise countermeasure deployed.',
    STICK_BTN_17: 'Decoy flare deployed.',
    STICK_BTN_19: 'Panic countermeasures deployed.',
    PROF_combat: 'Combat profile loaded.',
    PROF_mining: 'Mining profile loaded.',
    PROF_cargo: 'Cargo logistics profile loaded.',
    PROF_ground: 'Ground vehicle profile loaded.'
  },
  pt: {
    APU_ON: 'Sistemas ligados. Nave pronta para voo.',
    APU_OFF: 'A desligar sistemas da nave.',
    EAC_ON: 'Modo de navegação ativado.',
    EAC_OFF: 'Modo de combate ativado.',
    RDR_ALTM_ON: 'Trem de aterragem recolhido.',
    RDR_ALTM_OFF: 'Trem de aterragem baixado.',
    FLAPS_DN: 'Propulsores VTOL ativados.',
    FLAPS_MID: 'Modo de voo normal.',
    FLAPS_UP: 'Controlo de cruzeiro alternado.',
    BOAT_FWD: 'Motor Quantum em preparação.',
    BOAT_AFT: 'Modo de armas ativo.',
    BOAT_MID: 'Modo neutro.',
    SPDBRK_FWD: 'Controlo de cruzeiro ativado.',
    SPDBRK_AFT: 'Travão espacial ativo.',
    SPDBRK_MID: 'Controlo de cruzeiro desligado.',
    PINKY_FWD: 'Faróis exteriores ligados.',
    PINKY_AFT: 'Luzes de cabine alternadas.',
    PINKY_MID: 'Faróis exteriores desligados.',
    LDGHORN_PRESS: 'A contactar torre de controlo.',
    AP_ENGAGE_PRESS: 'A contactar torre de controlo.',
    AP_PATH: 'A abrir todas as portas.',
    AP_ALT: 'Portas da nave trancadas.',
    AP_MID: 'A fechar portas exteriores.',
    SHIFT_MODIFIER_ON: 'Camada shift ativa.',
    FUEL_L_ON: 'Propulsores ligados.',
    FUEL_L_OFF: 'Propulsores desligados.',
    FUEL_R_ON: 'Armas ligadas.',
    FUEL_R_OFF: 'Armas desligadas.',
    ENG_L_IGN: 'Visor do capacete limpo.',
    ENG_L_MOTOR: 'Motor esquerdo desligado.',
    ENG_L_NORM: 'Motor esquerdo ligado.',
    ENG_R_IGN: 'Alerta. Sequência de ejeção.',
    ENG_R_MOTOR: 'Armas desligadas.',
    ENG_R_NORM: 'Armas ligadas.',
    IDLE_L_OFF: 'Corte de motor esquerdo.',
    IDLE_R_OFF: 'Corte de motor direito.',
    IDLE_L_IDLE: 'Motor esquerdo pronto.',
    IDLE_R_IDLE: 'Motor direito pronto.',
    LTB_PRESS: 'Nave pronta para voo.',
    CHINA_FWD_PRESS: 'Pós-combustão ativa.',
    CHINA_AFT_PRESS: 'Propulsão invertida.',
    MIC_UP_PRESS: 'Modo de scan.',
    MIC_DOWN_PRESS: 'Modo de mineração.',
    MIC_RIGHT_PRESS: 'Câmara exterior.',
    SLEW_PUSH_PRESS: 'Velocidade igualada ao alvo.',
    TRIM_HAT_UP: 'Energia nos propulsores.',
    TRIM_HAT_RIGHT: 'Energia nos escudos.',
    TRIM_HAT_LEFT: 'Energia nas armas.',
    TRIM_HAT_DOWN: 'Energia equilibrada.',
    STICK_BTN_2: 'Míssil armado.',
    STICK_BTN_5: 'Master mode alternado.',
    STICK_BTN_11: 'Ping de radar.',
    STICK_BTN_15: 'Campo de ruído lançado.',
    STICK_BTN_17: 'Contramedida flare lançada.',
    STICK_BTN_19: 'Salva de pânico lançada.',
    PROF_combat: 'Perfil de combate carregado.',
    PROF_mining: 'Perfil de mineração carregado.',
    PROF_cargo: 'Perfil de carga carregado.',
    PROF_ground: 'Perfil terrestre carregado.'
  }
};

function applyVoiceSettings(vs) {
  if (!vs) return;
  voiceSettings = { ...voiceSettings, ...vs };
  const chk = document.getElementById('chk-voice-enabled');
  const sel = document.getElementById('select-voice-lang');
  const vol = document.getElementById('slider-voice-volume');
  const rate = document.getElementById('slider-voice-rate');
  const pitch = document.getElementById('slider-voice-pitch');
  if (chk) chk.checked = !!voiceSettings.enabled;
  if (sel) sel.value = voiceSettings.lang || 'en';
  if (vol) { vol.value = Math.round((voiceSettings.volume ?? 0.85) * 100); document.getElementById('lbl-voice-vol').textContent = vol.value + '%'; }
  if (rate) { rate.value = Math.round((voiceSettings.rate ?? 1.05) * 100); document.getElementById('lbl-voice-rate').textContent = (rate.value / 100).toFixed(2) + 'x'; }
  if (pitch) { pitch.value = Math.round((voiceSettings.pitch ?? 0.85) * 100); document.getElementById('lbl-voice-pitch').textContent = (pitch.value / 100).toFixed(2); }
}

function onVoiceSettingChanged() {
  voiceSettings = {
    enabled: !!document.getElementById('chk-voice-enabled')?.checked,
    lang: document.getElementById('select-voice-lang')?.value || 'en',
    volume: (parseInt(document.getElementById('slider-voice-volume')?.value || '85', 10)) / 100,
    rate: (parseInt(document.getElementById('slider-voice-rate')?.value || '105', 10)) / 100,
    pitch: (parseInt(document.getElementById('slider-voice-pitch')?.value || '85', 10)) / 100
  };
  applyVoiceSettings(voiceSettings);
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'save_voice_settings', voice_settings: voiceSettings }));
  }
}

function speakShipAI(text, force = false) {
  if (!('speechSynthesis' in window) || !text) return;
  if (!voiceSettings.enabled && !force) return;
  const now = Date.now();
  // Only block duplicate identical phrase within 400ms
  if (!force && text === _lastVoiceText && (now - _lastVoiceSpokenTs < 400)) return;
  _lastVoiceSpokenTs = now;
  _lastVoiceText = text;

  try {
    window.speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(text);
    const targetLang = voiceSettings.lang === 'pt' ? 'pt' : 'en';
    utter.lang = targetLang === 'pt' ? 'pt-PT' : 'en-US';
    utter.volume = Math.max(0.1, Math.min(1.0, voiceSettings.volume ?? 0.85));
    utter.rate = Math.max(0.6, Math.min(1.6, voiceSettings.rate ?? 1.05));
    utter.pitch = Math.max(0.5, Math.min(1.5, voiceSettings.pitch ?? 0.85));

    const voices = window.speechSynthesis.getVoices();
    if (voices && voices.length) {
      const preferred = voices.find(v => v.lang.toLowerCase().startsWith(targetLang));
      if (preferred) utter.voice = preferred;
    }
    window.speechSynthesis.speak(utter);
  } catch (e) {
    // Ignore browser autoplay restrictions before first user click
  }
}

function triggerShipVoiceForAction(actionId, desc) {
  if (!voiceSettings.enabled || !actionId) return;
  const cleanId = actionId.replace(/_LONG$/, '');

  if (cleanId.startsWith('MACRO:')) {
    const mid = cleanId.slice(6);
    const mac = cachedMacros[mid];
    const msg = voiceSettings.lang === 'pt'
      ? `A executar macro ${mac ? mac.name.split('(')[0] : ''}`
      : `Executing macro ${mac ? mac.name.split('(')[0] : ''}`;
    speakShipAI(msg);
    return;
  }

  const bank = VOICE_CALLOUTS[voiceSettings.lang] || VOICE_CALLOUTS.en;
  if (bank[cleanId]) {
    speakShipAI(bank[cleanId]);
    return;
  }

  // Fallback: speak custom action description if mapped
  const m = cachedMatrixMappings[cleanId];
  const fallbackDesc = (m && m.desc) || desc || '';
  if (fallbackDesc && !cleanId.startsWith('SPDBRK_RELEASE')) {
    const shortTxt = fallbackDesc.split('(')[0].replace(/\[.*?\]/g, '').trim();
    if (shortTxt) speakShipAI(shortTxt);
  }
}

function announceProfileVoice(profileId) {
  if (!voiceSettings.enabled) return;
  const bank = VOICE_CALLOUTS[voiceSettings.lang] || VOICE_CALLOUTS.en;
  const key = 'PROF_' + profileId;
  if (bank[key]) speakShipAI(bank[key]);
}

function testShipVoice(actionId) {
  const bank = VOICE_CALLOUTS[voiceSettings.lang] || VOICE_CALLOUTS.en;
  speakShipAI(bank[actionId] || 'Aegis combat computer online.', true);
}

window.addEventListener('DOMContentLoaded', () => {
  renderMacrosList();
  populateMacroSelects();
});


// ==============================================================================
// MULTI-THRUSTMASTER HARDWARE CATALOG & LIVE DEVICE LIST
// ==============================================================================
let lastUpdateInfo = null;
let _didAutoUpdateCheck = false;

function renderMultiThrustmasterDevices(data) {
  if (!data) return;
  // Update sidebar pod short labels with actual detected Thrustmaster model!
  const stickLbl = document.getElementById('pod-stick-text');
  const thrLbl = document.getElementById('pod-throttle-text');
  if (stickLbl && data.stick_short && data.stick) stickLbl.textContent = data.stick_short;
  if (thrLbl && data.throttle_short && data.throttle) thrLbl.textContent = data.throttle_short;

  const detCont = document.getElementById('detected-devices-list');
  const supCont = document.getElementById('supported-tm-grid');
  const detected = data.detected_devices || [];
  const detectedPids = new Set(detected.map(d => d.pid_hex));

  if (detCont) {
    if (!detected.length) {
      detCont.innerHTML = `<div style="font-size:12px; color:var(--text-dim); padding:10px; background:rgba(5,10,16,0.6); border:1px solid rgba(255,255,255,0.06);">Nenhum joystick USB detetado neste momento. Liga o teu Thrustmaster e clica em "Re-escanear USB".</div>`;
    } else {
      detCont.innerHTML = detected.map(d => `
        <div class="macro-card" style="border-left-color: ${d.is_thrustmaster ? 'var(--mil-green)' : 'var(--sc-cyan)'};">
          <div style="min-width:0;">
            <div style="font-weight:700; font-size:13px; color:#fff;">${d.name}</div>
            <div style="font-family:var(--font-mono); font-size:10.5px; color:var(--text-secondary);">
              Slot ${d.slot} • VID ${d.vid_hex} / PID ${d.pid_hex} • ${d.btns} Botões • ${d.axes} Eixos
            </div>
          </div>
          <span class="key-badge" style="color:var(--mil-green); border-color:rgba(56,226,157,0.5); background:rgba(56,226,157,0.12);">${(d.role || 'HID').toUpperCase()}</span>
        </div>
      `).join('');
    }
  }

  if (supCont && data.supported_devices) {
    supCont.innerHTML = data.supported_devices.map(s => {
      const isOnline = detectedPids.has(s.pid_hex);
      return `
        <div style="padding:8px 10px; background:${isOnline ? 'rgba(56,226,157,0.10)' : 'rgba(6,12,19,0.65)'}; border:1px solid ${isOnline ? 'rgba(56,226,157,0.55)' : 'rgba(72,220,255,0.14)'}; display:flex; flex-direction:column; gap:3px;">
          <div style="display:flex; justify-content:space-between; align-items:center; gap:6px;">
            <strong style="font-size:12px; color:${isOnline ? 'var(--mil-green)' : '#fff'};">${isOnline ? '● ' : ''}${s.name}</strong>
            <span style="font-family:var(--font-mono); font-size:9.5px; color:var(--mil-amber);">${s.pid_hex}</span>
          </div>
          <div style="font-size:10.5px; color:var(--text-secondary);">${s.desc}</div>
          <div style="font-family:var(--font-mono); font-size:9.5px; color:var(--text-dim);">${s.buttons}B • ${s.axes} Eixos • ${(s.role||'').toUpperCase()}</div>
        </div>
      `;
    }).join('');
  }
}

// ==============================================================================
// GITHUB AUTO-UPDATER FRONTEND
// ==============================================================================
function applyGitHubConfig(cfg) {
  if (!cfg) return;
  const verEl = document.getElementById('gh-current-version');
  if (verEl && cfg.app_version) verEl.textContent = 'v' + cfg.app_version;
  const repoEl = document.getElementById('gh-input-repo');
  const branchEl = document.getElementById('gh-input-branch');
  const autoEl = document.getElementById('gh-chk-autocheck');
  if (repoEl && cfg.github_repo !== undefined) repoEl.value = cfg.github_repo || '';
  if (branchEl && cfg.github_branch) branchEl.value = cfg.github_branch;
  if (autoEl && cfg.auto_check_updates !== undefined) autoEl.checked = !!cfg.auto_check_updates;

  if (!_didAutoUpdateCheck && cfg.auto_check_updates && cfg.github_repo) {
    _didAutoUpdateCheck = true;
    setTimeout(() => checkGitHubUpdate(), 1200);
  }
}

function saveGitHubConfig() {
  initAudio();
  playCockpitSound('chirp');
  const repo = (document.getElementById('gh-input-repo')?.value || '').trim();
  const branch = (document.getElementById('gh-input-branch')?.value || 'main').trim() || 'main';
  const autoCheck = !!document.getElementById('gh-chk-autocheck')?.checked;
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({
      type: 'save_github_config',
      github_repo: repo,
      github_branch: branch,
      auto_check_updates: autoCheck
    }));
  }
}

function checkGitHubUpdate() {
  initAudio();
  const titleEl = document.getElementById('gh-status-title');
  const msgEl = document.getElementById('gh-status-msg');
  if (titleEl) titleEl.textContent = 'A CONTACTAR GITHUB API...';
  if (msgEl) msgEl.textContent = 'A verificar releases e commits mais recentes...';
  const repo = (document.getElementById('gh-input-repo')?.value || '').trim();
  const branch = (document.getElementById('gh-input-branch')?.value || 'main').trim() || 'main';
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({
      type: 'check_github_update',
      github_repo: repo,
      github_branch: branch
    }));
  }
}

function renderGitHubUpdateStatus(data) {
  lastUpdateInfo = data;
  const card = document.getElementById('gh-update-status-card');
  const titleEl = document.getElementById('gh-status-title');
  const timeEl = document.getElementById('gh-status-time');
  const msgEl = document.getElementById('gh-status-msg');
  const logEl = document.getElementById('gh-status-changelog');
  const applyBtn = document.getElementById('btn-apply-gh-update');
  const dot = document.getElementById('nav-update-dot');

  if (timeEl) timeEl.textContent = data.checked_at || '';
  if (msgEl) msgEl.textContent = data.message || '';

  if (data.changelog && logEl) {
    logEl.style.display = 'block';
    logEl.textContent = data.changelog;
  } else if (logEl) {
    logEl.style.display = 'none';
  }

  if (data.update_available) {
    if (titleEl) { titleEl.textContent = `⬆️ NOVA ATUALIZAÇÃO DISPONÍVEL (${data.remote_version})`; titleEl.style.color = 'var(--mil-amber)'; }
    if (card) card.style.borderLeftColor = 'var(--mil-amber)';
    if (applyBtn) applyBtn.style.display = 'block';
    if (dot) dot.style.display = 'inline-block';
  } else if (data.status === 'up_to_date') {
    if (titleEl) { titleEl.textContent = '✅ PROGRAMA ATUALIZADO'; titleEl.style.color = 'var(--mil-green)'; }
    if (card) card.style.borderLeftColor = 'var(--mil-green)';
    if (applyBtn) applyBtn.style.display = 'none';
    if (dot) dot.style.display = 'none';
  } else if (data.status === 'error') {
    if (titleEl) { titleEl.textContent = '⚠️ ERRO AO VERIFICAR GITHUB'; titleEl.style.color = 'var(--mil-red)'; }
    if (card) card.style.borderLeftColor = 'var(--mil-red)';
    if (applyBtn) applyBtn.style.display = 'none';
  } else {
    if (titleEl) { titleEl.textContent = 'REPOSITÓRIO NÃO CONFIGURADO'; titleEl.style.color = 'var(--sc-cyan)'; }
    if (card) card.style.borderLeftColor = 'var(--sc-cyan)';
    if (applyBtn) applyBtn.style.display = 'none';
  }
}

function applyGitHubUpdateNow() {
  if (!lastUpdateInfo || !lastUpdateInfo.repo) return;
  if (!confirm(`Transferir e aplicar atualização de "${lastUpdateInfo.repo}"?\n(O teu config.json será automaticamente guardado em backup e preservado.)`)) return;
  initAudio();
  playCockpitSound('chirp');
  const btn = document.getElementById('btn-apply-gh-update');
  if (btn) { btn.disabled = true; btn.textContent = '⏳ A transferir e atualizar...'; }
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({
      type: 'apply_github_update',
      github_repo: lastUpdateInfo.repo,
      github_branch: lastUpdateInfo.branch || 'main',
      download_url: lastUpdateInfo.download_url || '',
      remote_sha: lastUpdateInfo.remote_sha || ''
    }));
  }
}

function onGitHubUpdateResult(res) {
  const btn = document.getElementById('btn-apply-gh-update');
  const titleEl = document.getElementById('gh-status-title');
  const msgEl = document.getElementById('gh-status-msg');
  if (btn) {
    btn.disabled = false;
    btn.textContent = '⬇️ Transferir & Aplicar Atualização do GitHub';
    if (res.success) btn.style.display = 'none';
  }
  if (titleEl) {
    titleEl.textContent = res.success ? '✅ ATUALIZAÇÃO CONCLUÍDA — REINICIA O SERVIDOR' : '❌ FALHA NA ATUALIZAÇÃO';
    titleEl.style.color = res.success ? 'var(--mil-green)' : 'var(--mil-red)';
  }
  if (msgEl) msgEl.textContent = res.message || '';
  if (res.success) {
    const dot = document.getElementById('nav-update-dot');
    if (dot) dot.style.display = 'none';
    playCockpitSound('chirp');
  }
}


// ==============================================================================
// MULTI-HOTAS REGISTRY (THRUSTMASTER FAMILY + SAITEK / LOGITECH X56 RHINO)
// + AUTOMATIC UPDATE ENGINE UI
// ==============================================================================
let activeHotasKit = 'warthog';
let cachedHotasKits = {
  warthog: {
    id: 'warthog',
    name: 'Thrustmaster HOTAS Warthog (A-10C)',
    brand: 'Thrustmaster',
    stick_label: 'MANCHE A-10C (js1 • PID 0402)',
    throttle_label: 'MANETE DUPLA (js2 • PID 0404)',
    stick_summary: '19 BOTÕES + TRIM HAT + 2 EIXOS',
    throttle_summary: '32 BOTÕES + COOLIE HAT + 5 EIXOS'
  },
  saitek_x56: {
    id: 'saitek_x56',
    name: 'Saitek / Logitech G X56 Rhino HOTAS',
    brand: 'Saitek / Logitech',
    stick_label: 'X56 RHINO STICK (PID 2221)',
    throttle_label: 'X56 RHINO THROTTLE (PID A221)',
    stick_summary: '17 BOTÕES + C-STICK + TWIST YAW + 2 HATS',
    throttle_summary: '32 BOTÕES + 7 TOGGLES + 4 ROTATIVOS + M1/M2/S1'
  },
  tm_t16000m: {
    id: 'tm_t16000m',
    name: 'Thrustmaster T.16000M FCS + TWCS',
    brand: 'Thrustmaster',
    stick_label: 'T.16000M FCS STICK (PID B10A)',
    throttle_label: 'TWCS THROTTLE (PID B687)',
    stick_summary: '16 BOTÕES (12 BASE + 4 GRIP) + POV + TWIST',
    throttle_summary: '14 BOTÕES + MINI-STICK + 3 HATS + PADDLE'
  },
  tm_tca: {
    id: 'tm_tca',
    name: 'Thrustmaster TCA Officer Pack Airbus',
    brand: 'Thrustmaster',
    stick_label: 'TCA SIDESTICK (PID 0405/0406)',
    throttle_label: 'TCA QUADRANT (PID 0407)',
    stick_summary: '17 BOTÕES + POV 8-WAY + TWIST YAW',
    throttle_summary: '17 BOTÕES + DUPLA MANETE + REVERSORES'
  },
  tm_tflight: {
    id: 'tm_tflight',
    name: 'Thrustmaster T.Flight HOTAS (X / 4 / One)',
    brand: 'Thrustmaster',
    stick_label: 'T.FLIGHT STICK (PID B108/B67B/B68D)',
    throttle_label: 'T.FLIGHT THROTTLE MODULE',
    stick_summary: 'GATILHO + R1/L1/R3 + POV + TWIST YAW',
    throttle_summary: 'ALAVANCA + ROCKER LEME + BOTÕES 5..12'
  }
};
let cachedDetectedUsb = [];
let latestUpdateDownloadUrl = '';

// Clean Tactical HUD SVG Schematics for non-Warthog kits (data URI)
function makeTacticalSvgUri(title, subtitle, accentColor, isThrottle) {
  const body = isThrottle
    ? `<rect x="35" y="120" width="230" height="125" rx="8" fill="#0d1824" stroke="${accentColor}" stroke-width="2"/>
       <rect x="65" y="38" width="75" height="90" rx="10" fill="#132333" stroke="${accentColor}" stroke-width="2"/>
       <rect x="155" y="38" width="85" height="90" rx="10" fill="#132333" stroke="${accentColor}" stroke-width="2"/>
       <circle cx="85" cy="175" r="10" fill="#1b3044" stroke="${accentColor}"/>
       <circle cx="130" cy="175" r="10" fill="#1b3044" stroke="${accentColor}"/>
       <circle cx="175" cy="175" r="10" fill="#1b3044" stroke="${accentColor}"/>
       <circle cx="220" cy="175" r="10" fill="#1b3044" stroke="${accentColor}"/>
       <rect x="60" y="205" width="180" height="22" rx="4" fill="#09111a" stroke="${accentColor}" stroke-opacity="0.5"/>`
    : `<rect x="80" y="210" width="140" height="55" rx="8" fill="#0d1824" stroke="${accentColor}" stroke-width="2"/>
       <path d="M120 210 L110 85 Q110 35 150 30 Q190 35 190 85 L180 210 Z" fill="#132333" stroke="${accentColor}" stroke-width="2"/>
       <circle cx="150" cy="70" r="18" fill="#0a141f" stroke="${accentColor}" stroke-width="2"/>
       <circle cx="122" cy="98" r="11" fill="#1b3044" stroke="${accentColor}"/>
       <circle cx="178" cy="98" r="11" fill="#1b3044" stroke="${accentColor}"/>
       <circle cx="150" cy="128" r="12" fill="#1b3044" stroke="${accentColor}"/>
       <rect x="140" y="160" width="20" height="32" rx="4" fill="#09111a" stroke="${accentColor}"/>`;
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 280" width="300" height="280">
    <defs>
      <pattern id="g" width="20" height="20" patternUnits="userSpaceOnUse">
        <path d="M 20 0 L 0 0 0 20" fill="none" stroke="${accentColor}" stroke-opacity="0.12" stroke-width="1"/>
      </pattern>
    </defs>
    <rect width="300" height="280" fill="#070d14"/>
    <rect width="300" height="280" fill="url(#g)"/>
    ${body}
    <text x="150" y="22" text-anchor="middle" fill="${accentColor}" font-family="monospace" font-size="13" font-weight="bold">${title}</text>
    <text x="150" y="272" text-anchor="middle" fill="#92adb8" font-family="monospace" font-size="10">${subtitle}</text>
  </svg>`;
  return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
}

function getStickImageForKit(kitId) {
  if (kitId === 'warthog') return '/warthog_stick_526x1181.png';
  if (kitId === 'saitek_x56') return makeTacticalSvgUri('SAITEK / LOGITECH X56 STICK', '17B • C-STICK • TWIST YAW • RGB', '#48dcff', false);
  if (kitId === 'tm_t16000m') return makeTacticalSvgUri('THRUSTMASTER T.16000M FCS', '16B • H.E.A.R.T • TWIST YAW', '#48dcff', false);
  if (kitId === 'tm_tca') return makeTacticalSvgUri('THRUSTMASTER TCA SIDESTICK', '17B • AIRBUS EDITION • TWIST', '#48dcff', false);
  if (kitId === 'tm_tflight') return makeTacticalSvgUri('THRUSTMASTER T.FLIGHT STICK', '12B • R1/L1/R3 • TWIST YAW', '#48dcff', false);
  return '/warthog_stick_526x1181.png';
}

function getThrottleImageForKit(kitId) {
  if (kitId === 'warthog') return '/warthog_throttle_509x455.png';
  if (kitId === 'saitek_x56') return makeTacticalSvgUri('SAITEK / LOGITECH X56 THROTTLE', '32B • 7 TOGGLES • 4 ROTATIVOS • M1/M2/S1', '#f0a426', true);
  if (kitId === 'tm_t16000m') return makeTacticalSvgUri('THRUSTMASTER TWCS THROTTLE', '14B • S.M.A.R.T RAIL • PADDLE', '#f0a426', true);
  if (kitId === 'tm_tca') return makeTacticalSvgUri('THRUSTMASTER TCA QUADRANT', '17B • DUAL THRUST • REVERSERS', '#f0a426', true);
  if (kitId === 'tm_tflight') return makeTacticalSvgUri('THRUSTMASTER T.FLIGHT THROTTLE', 'ALAVANCA • ROCKER LEME • BTN 5-12', '#f0a426', true);
  return '/warthog_throttle_509x455.png';
}

function applyHotasInfo(data) {
  if (data.kits) cachedHotasKits = data.kits;
  if (data.detected_devices) cachedDetectedUsb = data.detected_devices;

  // Auto-switch visual map images to match physically connected Stick & Throttle (including mixed setups!)
  let stickKit = data.selected_kit || activeHotasKit || 'warthog';
  let throttleKit = stickKit;

  if (data.auto_switch && (data.detected_stick_kit || data.detected_throttle_kit || data.detected_kit)) {
    activeHotasKit = data.detected_kit || data.detected_stick_kit || data.detected_throttle_kit || activeHotasKit;
    stickKit = data.detected_stick_kit || activeHotasKit;
    throttleKit = data.detected_throttle_kit || activeHotasKit;
  } else if (data.selected_kit) {
    activeHotasKit = data.selected_kit;
    stickKit = activeHotasKit;
    throttleKit = activeHotasKit;
  }

  const sel = document.getElementById('vmap-kit-selector');
  if (sel && cachedHotasKits[activeHotasKit]) sel.value = activeHotasKit;

  updateVisualKitGraphics(stickKit, throttleKit, !!data.detected_stick_kit, !!data.detected_throttle_kit);
  renderHotasKitsGrid();
  renderDetectedUsbList();
}

function selectHotasKit(kitId) {
  activeHotasKit = kitId || 'warthog';
  const sel = document.getElementById('vmap-kit-selector');
  if (sel) sel.value = activeHotasKit;

  updateVisualKitGraphics(activeHotasKit, activeHotasKit, false, false);
  renderHotasKitsGrid();

  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'set_hotas_kit', kit_id: activeHotasKit }));
  }
  playCockpitSound('chirp');
}

function updateVisualKitGraphics(stickKitId, throttleKitId, stickAuto = false, throttleAuto = false) {
  const sId = stickKitId || 'warthog';
  const tId = throttleKitId || sId;
  const sKit = cachedHotasKits[sId] || cachedHotasKits.warthog;
  const tKit = cachedHotasKits[tId] || cachedHotasKits.warthog;

  const stickImg = document.getElementById('vmap-img-stick');
  const thrImg = document.getElementById('vmap-img-throttle');
  const stickTag = document.getElementById('vmap-stick-header-tag');
  const stickMode = document.getElementById('vmap-stick-mode-tag');
  const thrTag = document.getElementById('vmap-throttle-header-tag');
  const thrMode = document.getElementById('vmap-throttle-mode-tag');

  if (stickTag) stickTag.textContent = (stickAuto ? '● AUTO: ' : '') + sKit.stick_label;
  if (stickMode) stickMode.textContent = sKit.stick_summary;
  if (thrTag) thrTag.textContent = (throttleAuto ? '● AUTO: ' : '') + tKit.throttle_label;
  if (thrMode) thrMode.textContent = tKit.throttle_summary;

  if (stickImg) stickImg.src = getStickImageForKit(sId);
  if (thrImg) thrImg.src = getThrottleImageForKit(tId);
}

function renderHotasKitsGrid() {
  const grid = document.getElementById('hotas-kits-grid');
  if (!grid) return;
  grid.innerHTML = Object.values(cachedHotasKits).map(k => {
    const isAct = k.id === activeHotasKit;
    return `
      <div class="glass-panel switch-card ${isAct ? 'active' : ''}" onclick="selectHotasKit('${k.id}')" style="padding: 12px;">
        <div class="switch-header">
          <div>
            <div class="switch-label">${k.name}</div>
            <div class="switch-sub">${k.brand}</div>
          </div>
          <div class="switch-status-pill">${isAct ? 'ATIVO' : 'SELECIONAR'}</div>
        </div>
        <div style="font-family: var(--font-mono); font-size: 10px; color: var(--text-secondary); line-height: 1.45;">
          <div><span style="color:var(--sc-cyan);">STICK:</span> ${k.stick_summary}</div>
          <div><span style="color:var(--mil-amber);">THROTTLE:</span> ${k.throttle_summary}</div>
        </div>
      </div>`;
  }).join('');
}

function renderDetectedUsbList() {
  const cont = document.getElementById('detected-usb-list');
  if (!cont) return;
  if (!cachedDetectedUsb || !cachedDetectedUsb.length) {
    cont.innerHTML = `<div style="font-family:var(--font-mono); font-size:11px; color:var(--text-dim); padding:8px; background:rgba(5,10,16,0.6); border:1px solid rgba(72,220,255,0.12);">Nenhum joystick USB detetado neste momento. Liga o teu Thrustmaster ou Saitek X56 e clica em "Re-escanear USB".</div>`;
    return;
  }
  cont.innerHTML = cachedDetectedUsb.map(d => `
    <div style="display:flex; justify-content:space-between; align-items:center; padding:8px 10px; background:rgba(6,12,20,0.75); border:1px solid rgba(56,226,157,0.3); border-left:3px solid var(--mil-green); font-family:var(--font-mono); font-size:11px;">
      <div>
        <div style="color:#fff; font-weight:700;">${d.model || d.name}</div>
        <div style="color:var(--text-secondary); font-size:10px;">VID_${d.vid_hex} &amp; PID_${d.pid_hex} • ${d.btns} Botões • ${d.axes} Eixos • Slot ${d.slot}</div>
      </div>
      <span class="key-badge" style="font-size:10px;">${(d.role || 'HID').toUpperCase()}</span>
    </div>
  `).join('');
}

// ---------------- AUTO-UPDATER FUNCTIONS ----------------
function applyUpdateStatus(data) {
  const pill = document.getElementById('update-version-pill');
  const box = document.getElementById('update-status-box');
  const chk = document.getElementById('chk-auto-update');
  const inp = document.getElementById('input-update-source');
  const btnApply = document.getElementById('btn-apply-update');

  if (pill && data.current_version) pill.textContent = 'v' + data.current_version;
  if (chk && data.auto_check_updates !== undefined) chk.checked = !!data.auto_check_updates;
  if (inp && data.update_source !== undefined) inp.value = data.update_source;

  latestUpdateDownloadUrl = data.download_url || '';

  if (box) {
    let html = `<div><strong>${data.message || 'Estado verificado.'}</strong></div>`;
    if (data.checked_at) html += `<div style="font-size:10px; color:var(--text-dim); margin-top:3px;">Última verificação: ${data.checked_at}</div>`;
    if (data.update_available && data.changelog) {
      html += `<div style="margin-top:6px; padding-top:6px; border-top:1px solid rgba(255,255,255,0.1); color:var(--mil-amber);">${String(data.changelog).slice(0, 300)}</div>`;
    }
    box.innerHTML = html;
    box.style.borderLeftColor = data.update_available ? 'var(--mil-amber)' : 'var(--mil-green)';
  }

  if (btnApply) {
    btnApply.style.display = data.update_available ? 'block' : 'none';
  }
}

function saveUpdateSettings() {
  const autoCheck = !!document.getElementById('chk-auto-update')?.checked;
  const source = (document.getElementById('input-update-source')?.value || '').trim();
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({
      type: 'save_update_settings',
      auto_check_updates: autoCheck,
      update_source: source
    }));
  }
}

function checkUpdatesNow() {
  initAudio();
  playCockpitSound('chirp');
  const box = document.getElementById('update-status-box');
  if (box) box.innerHTML = '⏳ A verificar atualizações...';
  const source = (document.getElementById('input-update-source')?.value || '').trim();
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'check_updates', update_source: source }));
  }
}

function applyUpdateNow() {
  if (!confirm('Criar backup ZIP de segurança e aplicar a atualização agora? (O teu config.json será preservado)')) return;
  initAudio();
  playCockpitSound('chirp');
  const box = document.getElementById('update-status-box');
  if (box) box.innerHTML = '⏳ A criar backup ZIP e transferir atualização...';
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'apply_update', download_url: latestUpdateDownloadUrl }));
  }
}

function createAppBackupNow() {
  initAudio();
  playCockpitSound('chirp');
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'create_app_backup' }));
  }
}

function onUpdateApplied(data) {
  const box = document.getElementById('update-status-box');
  if (box) {
    box.innerHTML = `<strong>${data.ok ? '✅' : '⚠️'} ${data.message}</strong>`;
    box.style.borderLeftColor = data.ok ? 'var(--mil-green)' : 'var(--mil-red)';
  }
}

window.addEventListener('DOMContentLoaded', () => {
  renderHotasKitsGrid();
  renderDetectedUsbList();
});


// ==============================================================================
// INDIVIDUAL X / Y / Z AXIS CURVES & ANTI-DRIFT CALIBRATION STUDIO
// ==============================================================================
let selectedCalAxis = 'x';
let axisCalibration = {
  x: { curve_type: 'expo', exponent: 1.8, deadzone: 3, saturation: 100, invert: false },
  y: { curve_type: 'expo', exponent: 1.8, deadzone: 3, saturation: 100, invert: false },
  z: { curve_type: 'expo', exponent: 1.5, deadzone: 4, saturation: 100, invert: false }
};
let liveAxisNorm = { x: 0.0, y: 0.0, z: 0.0 };

function applyAxisCalibrationData(cal) {
  if (!cal) return;
  ['x', 'y', 'z'].forEach(ax => {
    if (cal[ax]) axisCalibration[ax] = { ...axisCalibration[ax], ...cal[ax] };
  });
  syncAxisCalControlsUI();
  drawCurveCanvas();
}

function selectCalibrationAxis(ax) {
  if (!axisCalibration[ax]) return;
  selectedCalAxis = ax;
  ['x', 'y', 'z'].forEach(k => {
    const btn = document.getElementById('axis-tab-' + k);
    if (btn) btn.classList.toggle('active', k === ax);
  });
  const lbl = document.getElementById('cal-axis-label');
  if (lbl) lbl.textContent = 'EIXO ' + ax.toUpperCase();
  syncAxisCalControlsUI();
  drawCurveCanvas();
}

function syncAxisCalControlsUI() {
  const cfg = axisCalibration[selectedCalAxis] || axisCalibration.x;
  const selType = document.getElementById('select-curve-type');
  const slExp = document.getElementById('slider-exponent');
  const lbExp = document.getElementById('label-exponent');
  const slDz = document.getElementById('slider-axis-deadzone');
  const lbDz = document.getElementById('label-axis-deadzone');
  const slSat = document.getElementById('slider-axis-saturation');
  const lbSat = document.getElementById('label-axis-saturation');
  const chkInv = document.getElementById('chk-axis-invert');

  if (selType) selType.value = cfg.curve_type || 'expo';
  if (slExp) slExp.value = Math.round((cfg.exponent || 1.8) * 10);
  if (lbExp) lbExp.textContent = Number(cfg.exponent || 1.8).toFixed(1);
  if (slDz) slDz.value = Math.round(cfg.deadzone ?? 3);
  if (lbDz) lbDz.textContent = Math.round(cfg.deadzone ?? 3) + '%';
  if (slSat) slSat.value = Math.round(cfg.saturation ?? 100);
  if (lbSat) lbSat.textContent = Math.round(cfg.saturation ?? 100) + '%';
  if (chkInv) chkInv.checked = !!cfg.invert;
}

function onAxisCalControlChanged() {
  const cfg = axisCalibration[selectedCalAxis];
  cfg.curve_type = document.getElementById('select-curve-type')?.value || 'expo';
  cfg.exponent = parseFloat(document.getElementById('slider-exponent')?.value || '18') / 10.0;
  cfg.deadzone = parseInt(document.getElementById('slider-axis-deadzone')?.value || '3', 10);
  cfg.saturation = parseInt(document.getElementById('slider-axis-saturation')?.value || '100', 10);
  cfg.invert = !!document.getElementById('chk-axis-invert')?.checked;

  syncAxisCalControlsUI();
  drawCurveCanvas();

  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'save_axis_calibration', axis_calibration: axisCalibration }));
  }
}

function evalAxisCurve(normIn, cfg) {
  let x = Math.max(-1, Math.min(1, normIn));
  if (cfg.invert) x = -x;
  const dz = Math.max(0, Math.min(0.45, (cfg.deadzone || 0) / 100.0));
  const sat = Math.max(0.5, Math.min(1.0, (cfg.saturation || 100) / 100.0));
  const absX = Math.abs(x);
  if (absX <= dz) return 0.0;

  let t = Math.min(1.0, (absX - dz) / Math.max(0.01, sat - dz));
  const exp = cfg.exponent || 1.8;
  let mag = t;
  if (cfg.curve_type === 'expo') {
    mag = Math.pow(t, exp);
  } else if (cfg.curve_type === 's_curve') {
    mag = t < 0.5
      ? 0.5 * Math.pow(2 * t, exp)
      : 1 - 0.5 * Math.pow(2 * (1 - t), exp);
  }
  return Math.sign(x) * mag;
}

function updateLiveAxisForCalibration(data) {
  if (!data) return;
  if (data.stick_x !== undefined) liveAxisNorm.x = (data.stick_x - 32767.5) / 32767.5;
  if (data.stick_y !== undefined) liveAxisNorm.y = (data.stick_y - 32767.5) / 32767.5;
  if (data.thr_z !== undefined)   liveAxisNorm.z = (data.thr_z - 32767.5) / 32767.5;

  const axesTab = document.getElementById('tab-axes');
  if (axesTab && axesTab.classList.contains('active')) {
    drawCurveCanvas();
  }
}

function autoCalibrateAxisDrift() {
  initAudio();
  playCockpitSound('chirp');
  const rawPct = Math.abs(liveAxisNorm[selectedCalAxis] || 0) * 100.0;
  // Sets deadzone to current idle drift + 2% safety margin (clamped 2%..20%)
  const recommended = Math.min(20, Math.max(2, Math.ceil(rawPct) + 2));
  axisCalibration[selectedCalAxis].deadzone = recommended;
  syncAxisCalControlsUI();
  drawCurveCanvas();
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'save_axis_calibration', axis_calibration: axisCalibration }));
  }
  appendLog(new Date().toTimeString().slice(0, 8), `Auto-Calibração Anti-Drift [EIXO ${selectedCalAxis.toUpperCase()}]`, `Deadzone ajustada para ${recommended}% (Desvio medido: ${rawPct.toFixed(1)}%)`);
}

function applyAxisCalibrationToSC() {
  initAudio();
  playCockpitSound('chirp');
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'apply_axis_calibration_xml', axis_calibration: axisCalibration }));
  }
}

// Override drawCurveCanvas with full bipolar (-100%..+100%) X/Y/Z Anti-Drift Visualizer
function drawCurveCanvas() {
  const canvas = document.getElementById('curve-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;
  const cfg = axisCalibration[selectedCalAxis] || axisCalibration.x;

  ctx.clearRect(0, 0, w, h);

  // Subtle Grid
  ctx.strokeStyle = 'rgba(72, 220, 255, 0.12)';
  ctx.lineWidth = 1;
  for (let i = 1; i < 8; i++) {
    ctx.beginPath(); ctx.moveTo((w / 8) * i, 0); ctx.lineTo((w / 8) * i, h); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(0, (h / 8) * i); ctx.lineTo(w, (h / 8) * i); ctx.stroke();
  }

  // Center Axes
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.25)';
  ctx.beginPath(); ctx.moveTo(w / 2, 0); ctx.lineTo(w / 2, h); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(0, h / 2); ctx.lineTo(w, h / 2); ctx.stroke();

  // Anti-Drift Deadzone Band (Amber shaded center zone)
  const dzFrac = (cfg.deadzone || 0) / 100.0;
  const dzPx = dzFrac * (w / 2);
  if (dzPx > 0.5) {
    ctx.fillStyle = 'rgba(240, 164, 38, 0.16)';
    ctx.fillRect(w / 2 - dzPx, 0, dzPx * 2, h);
    ctx.strokeStyle = 'rgba(240, 164, 38, 0.55)';
    ctx.setLineDash([4, 3]);
    ctx.beginPath(); ctx.moveTo(w / 2 - dzPx, 0); ctx.lineTo(w / 2 - dzPx, h); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(w / 2 + dzPx, 0); ctx.lineTo(w / 2 + dzPx, h); ctx.stroke();
    ctx.setLineDash([]);
  }

  // Linear reference diagonal
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.14)';
  ctx.setLineDash([3, 4]);
  ctx.beginPath(); ctx.moveTo(0, h); ctx.lineTo(w, 0); ctx.stroke();
  ctx.setLineDash([]);

  // Actual Axis Curve (-1..+1)
  ctx.strokeStyle = selectedCalAxis === 'z' ? '#f0a426' : '#48dcff';
  ctx.lineWidth = 2.5;
  ctx.shadowColor = selectedCalAxis === 'z' ? 'rgba(240,164,38,0.6)' : 'rgba(72,220,255,0.6)';
  ctx.shadowBlur = 8;
  ctx.beginPath();
  for (let px = 0; px <= w; px += 2) {
    const nx = (px / w) * 2 - 1;
    const ny = evalAxisCurve(nx, cfg);
    const py = h / 2 - ny * (h / 2 - 8);
    if (px === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  }
  ctx.stroke();
  ctx.shadowBlur = 0;

  // Live Hardware Position Pip
  const rawVal = liveAxisNorm[selectedCalAxis] || 0;
  const outVal = evalAxisCurve(rawVal, cfg);
  const dotX = ((rawVal + 1) / 2) * w;
  const dotY = h / 2 - outVal * (h / 2 - 8);

  ctx.fillStyle = '#ffffff';
  ctx.strokeStyle = '#38e29d';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(dotX, dotY, 5, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  // Update live readouts & drift badge
  const rawEl = document.getElementById('cal-live-raw');
  const outEl = document.getElementById('cal-live-out');
  const badgeEl = document.getElementById('cal-drift-badge');
  if (rawEl) rawEl.textContent = (rawVal * 100).toFixed(1) + '%';
  if (outEl) outEl.textContent = (outVal * 100).toFixed(1) + '%';
  if (badgeEl) {
    if (Math.abs(outVal) < 0.001) {
      badgeEl.textContent = '✅ ZERO DRIFT';
      badgeEl.style.color = 'var(--mil-green)';
      badgeEl.style.borderColor = 'rgba(56,226,157,0.5)';
    } else if (Math.abs(rawVal) < 0.15) {
      badgeEl.textContent = '⚠️ DRIFT DETETADO';
      badgeEl.style.color = 'var(--mil-amber)';
      badgeEl.style.borderColor = 'rgba(240,164,38,0.6)';
    } else {
      badgeEl.textContent = '🕹️ EM MOVIMENTO';
      badgeEl.style.color = 'var(--sc-cyan)';
      badgeEl.style.borderColor = 'rgba(72,220,255,0.5)';
    }
  }
}

window.addEventListener('DOMContentLoaded', () => {
  syncAxisCalControlsUI();
  setTimeout(drawCurveCanvas, 250);
});

function minimizeToTray() {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'minimize_to_tray' }));
  }
}


// ==============================================================================
// CUSTOMIZABLE SHIP AI VOICE PHRASES EDITOR (EDIT EVERY CALLOUT & MUTE TOGGLE)
// ==============================================================================
const VOICE_EVENT_LABELS = {
  APU_ON: 'APU START — Flight Ready',
  APU_OFF: 'APU OFF — Desligar Sistemas',
  EAC_ON: 'EAC ARM — Master Mode NAV',
  EAC_OFF: 'EAC OFF — Master Mode SCM',
  RDR_ALTM_ON: 'RDR ALTM NRM — Recolher Trem',
  RDR_ALTM_OFF: 'RDR ALTM DIS — Baixar Trem',
  FLAPS_DN: 'FLAPS DOWN — Modo VTOL',
  FLAPS_MID: 'FLAPS MID — Voo Normal',
  FLAPS_UP: 'FLAPS UP — Cruise Control',
  BOAT_FWD: 'BOAT FWD — Quantum Spool',
  BOAT_AFT: 'BOAT AFT — Modo Armas',
  BOAT_MID: 'BOAT MID — Neutro',
  SPDBRK_FWD: 'SPEEDBRAKE FWD — Cruise ON',
  SPDBRK_AFT: 'SPEEDBRAKE AFT — Space Brake',
  SPDBRK_MID: 'SPEEDBRAKE MID — Cruise OFF',
  PINKY_FWD: 'PINKY FWD — Faróis ON',
  PINKY_AFT: 'PINKY AFT — Luzes Cabine',
  PINKY_MID: 'PINKY MID — Faróis OFF',
  LDGHORN_PRESS: 'BTN 21 LDGH — Chamar ATC',
  AP_ENGAGE_PRESS: 'BTN 26 APENG — Chamar ATC',
  AP_PATH: 'AP PATH — Abrir Portas',
  AP_ALT: 'AP ALT — Trancar Portas',
  AP_MID: 'AP MID — Fechar Portas',
  SHIFT_MODIFIER_ON: 'S4 PINKY — Camada Shift',
  FUEL_L_ON: 'FUEL LEFT ON — Propulsores ON',
  FUEL_L_OFF: 'FUEL LEFT OFF — Propulsores OFF',
  FUEL_R_ON: 'FUEL RIGHT ON — Armas ON',
  FUEL_R_OFF: 'FUEL RIGHT OFF — Armas OFF',
  ENG_L_IGN: 'ENG L IGN — Limpar Visor',
  ENG_L_MOTOR: 'ENG L MOTOR — Motor Esq. OFF',
  ENG_L_NORM: 'ENG L NORM — Motor Esq. ON',
  ENG_R_IGN: 'ENG R IGN — Ejeção Emergência',
  ENG_R_MOTOR: 'ENG R MOTOR — Armas OFF',
  ENG_R_NORM: 'ENG R NORM — Armas ON',
  IDLE_L_OFF: 'IDLE CUTOFF ESQ — Corte Motor',
  IDLE_R_OFF: 'IDLE CUTOFF DIR — Corte Motor',
  IDLE_L_IDLE: 'IDLE READY ESQ — Motor Pronto',
  IDLE_R_IDLE: 'IDLE READY DIR — Motor Pronto',
  LTB_PRESS: 'LTB — Flight Ready / Autoland',
  CHINA_FWD_PRESS: 'CHINA FWD — Boost / Afterburner',
  CHINA_AFT_PRESS: 'CHINA AFT — Propulsão Invertida',
  MIC_UP_PRESS: 'MIC UP — Modo Scan',
  MIC_DOWN_PRESS: 'MIC DOWN — Modo Mineração',
  MIC_RIGHT_PRESS: 'MIC RIGHT — Câmara Exterior',
  SLEW_PUSH_PRESS: 'SLEW PUSH — Igualar Velocidade',
  TRIM_HAT_UP: 'TRIM UP — Energia Propulsores',
  TRIM_HAT_RIGHT: 'TRIM RIGHT — Energia Escudos',
  TRIM_HAT_LEFT: 'TRIM LEFT — Energia Armas',
  TRIM_HAT_DOWN: 'TRIM DOWN — Equilibrar Energia',
  STICK_BTN_2: 'S2 — Míssil Armado',
  STICK_BTN_5: 'S1 — Master Mode',
  STICK_BTN_11: 'DMS UP — Ping de Radar',
  STICK_BTN_15: 'CMS UP — Noise / Chaff',
  STICK_BTN_17: 'CMS DOWN — Decoy / Flare',
  STICK_BTN_19: 'CMS PUSH — Salva de Pânico',
  PROF_combat: 'PERFIL — Combate',
  PROF_mining: 'PERFIL — Mineração',
  PROF_cargo: 'PERFIL — Carga',
  PROF_ground: 'PERFIL — Terrestre'
};

function getResolvedVoicePhrase(actionId) {
  const custom = (voiceSettings.custom_callouts || {})[actionId];
  if (custom !== undefined && custom !== null && String(custom).trim() !== '') {
    return String(custom).trim();
  }
  const bank = VOICE_CALLOUTS[voiceSettings.lang] || VOICE_CALLOUTS.en;
  return bank[actionId] || '';
}

function isVoiceEventMuted(actionId) {
  return Array.isArray(voiceSettings.muted_callouts) && voiceSettings.muted_callouts.includes(actionId);
}

function renderVoiceCalloutsEditor() {
  const cont = document.getElementById('voice-callouts-editor-list');
  if (!cont) return;
  const q = (document.getElementById('voice-callouts-search')?.value || '').trim().toLowerCase();
  const bank = VOICE_CALLOUTS[voiceSettings.lang] || VOICE_CALLOUTS.en;
  const keys = Object.keys(VOICE_EVENT_LABELS);

  const rows = [];
  for (const k of keys) {
    const label = VOICE_EVENT_LABELS[k] || k;
    const phrase = getResolvedVoicePhrase(k);
    const muted = isVoiceEventMuted(k);
    const isCustom = Boolean((voiceSettings.custom_callouts || {})[k]);
    if (q && !label.toLowerCase().includes(q) && !k.toLowerCase().includes(q) && !phrase.toLowerCase().includes(q)) {
      continue;
    }
    const safePhrase = phrase.replace(/&/g, '&amp;').replace(/"/g, '&quot;');
    rows.push(`
      <div style="display:flex; align-items:center; gap:6px; padding:6px 8px; background:rgba(6,12,20,0.75); border:1px solid ${isCustom ? 'rgba(240,164,38,0.45)' : 'rgba(72,220,255,0.14)'}; opacity:${muted ? '0.45' : '1'};">
        <input type="checkbox" ${muted ? '' : 'checked'} onchange="toggleVoiceCalloutMute('${k}', !this.checked)" title="Ativar/Silenciar este aviso" style="accent-color:var(--sc-cyan); cursor:pointer;">
        <div style="flex:1; min-width:0; display:flex; flex-direction:column; gap:3px;">
          <div style="font-family:var(--font-mono); font-size:9.5px; color:${isCustom ? 'var(--mil-amber)' : 'var(--sc-cyan)'}; display:flex; justify-content:space-between;">
            <span>${label}</span>
            <span style="color:var(--text-dim);">${k}</span>
          </div>
          <input type="text" class="form-input" style="padding:3px 7px; font-size:11px; width:100%;" value="${safePhrase}" placeholder="Escreve a frase falada pela nave..." onchange="updateCustomVoiceCallout('${k}', this.value)">
        </div>
        <button class="btn-secondary" style="padding:4px 7px; font-size:11px; flex-shrink:0;" onclick="speakShipAI(getResolvedVoicePhrase('${k}'), true)" title="Ouvir esta frase">🔊</button>
      </div>
    `);
  }
  cont.innerHTML = rows.join('') || '<div style="font-size:11px; color:var(--text-dim); padding:8px;">Nenhum evento encontrado.</div>';
}

function updateCustomVoiceCallout(actionId, newText) {
  if (!voiceSettings.custom_callouts) voiceSettings.custom_callouts = {};
  const trimmed = (newText || '').trim();
  const defTxt = (VOICE_CALLOUTS[voiceSettings.lang] || VOICE_CALLOUTS.en)[actionId] || '';
  if (!trimmed || trimmed === defTxt) {
    delete voiceSettings.custom_callouts[actionId];
  } else {
    voiceSettings.custom_callouts[actionId] = trimmed;
  }
  persistVoiceSettingsNow();
  renderVoiceCalloutsEditor();
}

function toggleVoiceCalloutMute(actionId, isMuted) {
  if (!Array.isArray(voiceSettings.muted_callouts)) voiceSettings.muted_callouts = [];
  const set = new Set(voiceSettings.muted_callouts);
  if (isMuted) set.add(actionId); else set.delete(actionId);
  voiceSettings.muted_callouts = Array.from(set);
  persistVoiceSettingsNow();
  renderVoiceCalloutsEditor();
}

function resetAllVoiceCallouts() {
  if (!confirm('Restaurar todas as frases personalizadas do computador de bordo para o padrão?')) return;
  voiceSettings.custom_callouts = {};
  voiceSettings.muted_callouts = [];
  persistVoiceSettingsNow();
  renderVoiceCalloutsEditor();
  speakShipAI(voiceSettings.lang === 'pt' ? 'Frases padrão restauradas.' : 'Default voice bank restored.', true);
}

function persistVoiceSettingsNow() {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'save_voice_settings', voice_settings: voiceSettings }));
  }
}

// Override handlers to honor custom_callouts, muted_callouts, and macro.voice_text
function applyVoiceSettings(vs) {
  if (!vs) return;
  voiceSettings = {
    custom_callouts: {},
    muted_callouts: [],
    ...voiceSettings,
    ...vs
  };
  const chk = document.getElementById('chk-voice-enabled');
  const sel = document.getElementById('select-voice-lang');
  const vol = document.getElementById('slider-voice-volume');
  const rate = document.getElementById('slider-voice-rate');
  const pitch = document.getElementById('slider-voice-pitch');
  if (chk) chk.checked = !!voiceSettings.enabled;
  if (sel) sel.value = voiceSettings.lang || 'en';
  if (vol) { vol.value = Math.round((voiceSettings.volume ?? 0.85) * 100); document.getElementById('lbl-voice-vol').textContent = vol.value + '%'; }
  if (rate) { rate.value = Math.round((voiceSettings.rate ?? 1.05) * 100); document.getElementById('lbl-voice-rate').textContent = (rate.value / 100).toFixed(2) + 'x'; }
  if (pitch) { pitch.value = Math.round((voiceSettings.pitch ?? 0.85) * 100); document.getElementById('lbl-voice-pitch').textContent = (pitch.value / 100).toFixed(2); }
  renderVoiceCalloutsEditor();
}

function onVoiceSettingChanged() {
  voiceSettings = {
    ...voiceSettings,
    enabled: !!document.getElementById('chk-voice-enabled')?.checked,
    lang: document.getElementById('select-voice-lang')?.value || 'en',
    volume: (parseInt(document.getElementById('slider-voice-volume')?.value || '85', 10)) / 100,
    rate: (parseInt(document.getElementById('slider-voice-rate')?.value || '105', 10)) / 100,
    pitch: (parseInt(document.getElementById('slider-voice-pitch')?.value || '85', 10)) / 100
  };
  applyVoiceSettings(voiceSettings);
  persistVoiceSettingsNow();
}

function triggerShipVoiceForAction(actionId, desc) {
  if (!voiceSettings.enabled || !actionId) return;
  const cleanId = actionId.replace(/_LONG$/, '');
  if (isVoiceEventMuted(cleanId)) return;

  if (cleanId.startsWith('MACRO:')) {
    const mid = cleanId.slice(6);
    const mac = cachedMacros[mid];
    if (mac && mac.voice_text && mac.voice_text.trim()) {
      speakShipAI(mac.voice_text.trim());
      return;
    }
    const msg = voiceSettings.lang === 'pt'
      ? `A executar macro ${mac ? mac.name.split('(')[0] : ''}`
      : `Executing macro ${mac ? mac.name.split('(')[0] : ''}`;
    speakShipAI(msg);
    return;
  }

  const phrase = getResolvedVoicePhrase(cleanId);
  if (phrase) {
    speakShipAI(phrase);
    return;
  }

  const m = cachedMatrixMappings[cleanId];
  const fallbackDesc = (m && m.desc) || desc || '';
  if (fallbackDesc && !cleanId.startsWith('SPDBRK_RELEASE')) {
    const shortTxt = fallbackDesc.split('(')[0].replace(/\[.*?\]/g, '').trim();
    if (shortTxt) speakShipAI(shortTxt);
  }
}

function announceProfileVoice(profileId) {
  if (!voiceSettings.enabled) return;
  const key = 'PROF_' + profileId;
  if (isVoiceEventMuted(key)) return;
  const phrase = getResolvedVoicePhrase(key);
  if (phrase) speakShipAI(phrase);
}

function testShipVoice(actionId) {
  const phrase = getResolvedVoicePhrase(actionId) || 'Aegis combat computer online.';
  speakShipAI(phrase, true);
}

window.addEventListener('DOMContentLoaded', () => {
  renderVoiceCalloutsEditor();
});
