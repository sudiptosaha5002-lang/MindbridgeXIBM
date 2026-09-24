/**
 * MindBridge - Psychological Care & Conversational Bridge Controller
 * Features:
 * - Neuro-Biophilic Interactive Canvas & Ambient Lighting
 * - Psychoacoustic Soundscapes (Web Audio API: Soft Rain, Alpha Waves, 432Hz Harmony, Forest)
 * - Emotional Weather Barometer & Somatic Tension Mapping
 * - Multilingual Speech Recognition (Web Speech STT) & Calming Voice Synthesis (TTS)
 * - Strict Non-Diagnostic Guardrail & Instant Crisis Triage
 * - Verified Specialist Directory & Appointment Booking
 */

// ==========================================================================
// UNIVERSAL BACKEND CONNECTION BRIDGE
// Ensures frontend connects seamlessly whether opened from http://localhost:5000,
// 127.0.0.1:5000, Live Server (port 5500), or double-clicked as file:///
// ==========================================================================

(function setupUniversalBackendBridge() {
  const isDirectFile = window.location.protocol === 'file:';
  const isCustomPort = window.location.port && window.location.port !== '5000';
  const isLocalHost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' || window.location.hostname === '';
  
  window.MINDBRIDGE_BACKEND_ORIGIN = (isDirectFile || (isCustomPort && isLocalHost)) ? 'http://127.0.0.1:5000' : '';

  const originalFetch = window.fetch;
  window.fetch = function(input, init) {
    if (window.MINDBRIDGE_BACKEND_ORIGIN) {
      if (typeof input === 'string') {
        if (input.startsWith('/api/') || input.startsWith('/resources/') || input.startsWith('/music/')) {
          input = window.MINDBRIDGE_BACKEND_ORIGIN + input;
        } else if (input.startsWith('api/') || input.startsWith('resources/') || input.startsWith('music/')) {
          input = window.MINDBRIDGE_BACKEND_ORIGIN + '/' + input;
        }
      } else if (input && typeof input === 'object' && input.url) {
        const url = input.url;
        if (url.startsWith('/api/') || url.startsWith('/resources/') || url.startsWith('/music/')) {
          input = new Request(window.MINDBRIDGE_BACKEND_ORIGIN + url, init || input);
        }
      }
    }
    return originalFetch.call(this, input, init);
  };
})();

// Global Application State
const state = {
  conversationId: localStorage.getItem('mb_conv_id') || null,
  userId: localStorage.getItem('mb_user_id') || `user-${Math.random().toString(36).substring(2, 9)}`,
  ttsEnabled: true,
  selectedLanguage: 'en-US',
  isRecording: false,
  recognition: null,
  providers: [],
  selectedProvider: null,
  breathingInterval: null,
  breathingActive: false,
  soundscapeActive: localStorage.getItem('mb_music_pref') || 'off',
  soundVolume: parseFloat(localStorage.getItem('mb_sound_volume')) || 0.28,
  soundMuted: false,
  soundPlaying: false,
  voiceCompanionMode: false,
  consecutiveSilenceCount: 0,
  voiceRestartTimer: null,
  ttsWatchdogTimer: null,
  userExplicitlyStoppedVoice: false,
  neuroMode: localStorage.getItem('mb_neuro_mode') || 'alpha',
  audioElement: null,
  currentChatAbortController: null,
  isRecognitionStarting: false,
  isRecognitionActive: false,
  vcSelectedLang: 'auto',
  activeVoicePerspective: localStorage.getItem('mb_voice_perspective') || 'auto',
  interruptionBannerTimer: null,
  geminiApiKey: localStorage.getItem('mb_gemini_api_key') || '',
  geminiVoice: localStorage.getItem('mb_gemini_voice') || 'Kore',
  pastLifeActive: false,
  pastLifeSessionId: localStorage.getItem('mb_past_life_sid') || null,
  pastLifeMode: 'short'
};

localStorage.setItem('mb_user_id', state.userId);

// DOM Elements
const elements = {
  // Navigation
  tabs: document.querySelectorAll('.nav-tab'),
  panes: document.querySelectorAll('.tab-pane'),
  brandHomeBtn: document.getElementById('brandHomeBtn'),

  // Controls & Soundscapes
  soundscapeBtn: document.getElementById('soundscapeBtn'),
  soundscapeMenu: document.getElementById('soundscapeMenu'),
  soundscapeLabel: document.getElementById('soundscapeLabel'),
  soundscapeIcon: document.getElementById('soundscapeIcon'),
  ttsToggleBtn: document.getElementById('ttsToggleBtn'),
  ttsLabel: document.getElementById('ttsLabel'),
  ttsIcon: document.getElementById('ttsIcon'),
  languageSelect: document.getElementById('languageSelect'),
  headerSosBtn: document.getElementById('headerSosBtn'),

  // Settings & Music Modal Elements
  headerSettingsBtn: document.getElementById('headerSettingsBtn'),
  settingsModal: document.getElementById('settingsModal'),
  closeSettingsModalBtn: document.getElementById('closeSettingsModalBtn'),
  doneSettingsBtn: document.getElementById('doneSettingsBtn'),
  settingsActiveTrackBadge: document.getElementById('settingsActiveTrackBadge'),
  settingsNowPlayingName: document.getElementById('settingsNowPlayingName'),
  settingsMuteBtn: document.getElementById('settingsMuteBtn'),
  settingsMuteIcon: document.getElementById('settingsMuteIcon'),
  settingsMuteText: document.getElementById('settingsMuteText'),
  settingsVolumeSlider: document.getElementById('settingsVolumeSlider'),
  settingsVolumeVal: document.getElementById('settingsVolumeVal'),
  settingsTrackCards: document.querySelectorAll('.settings-track-card'),
  settingsLanguageSelect: document.getElementById('settingsLanguageSelect'),
  settingsClearBtn: document.getElementById('settingsClearBtn'),

  // Emotional Weather & Somatics
  weatherPills: document.querySelectorAll('.weather-pill'),
  somaticBtns: document.querySelectorAll('.somatic-btn'),

  // Chat Elements
  chatMessages: document.getElementById('chatMessages'),
  chatInput: document.getElementById('chatInput'),
  sendBtn: document.getElementById('sendBtn'),
  micBtn: document.getElementById('micBtn'),
  micIcon: document.getElementById('micIcon'),
  audioVisualizer: document.getElementById('audioVisualizer'),
  chipsList: document.getElementById('chipsList'),

  // Sidebar Triage Widgets
  liveStressVal: document.getElementById('liveStressVal'),
  liveStressBar: document.getElementById('liveStressBar'),
  liveMoodVal: document.getElementById('liveMoodVal'),
  liveEmotionTags: document.getElementById('liveEmotionTags'),
  quickBreatheBtn: document.getElementById('quickBreatheBtn'),

  // Providers Elements
  providersGrid: document.getElementById('providersGrid'),
  filterSpecialty: document.getElementById('filterSpecialty'),
  filterLanguage: document.getElementById('filterLanguage'),
  filterMode: document.getElementById('filterMode'),
  filterMaxPrice: document.getElementById('filterMaxPrice'),
  resetFiltersBtn: document.getElementById('resetFiltersBtn'),
  providerCountBadge: document.getElementById('providerCountBadge'),

  // Insights Elements
  sessionSummaryText: document.getElementById('sessionSummaryText'),
  sessionThemesList: document.getElementById('sessionThemesList'),
  sessionStepsList: document.getElementById('sessionStepsList'),
  insightStressNum: document.getElementById('insightStressNum'),
  insightMoodTone: document.getElementById('insightMoodTone'),
  insightSleepStatus: document.getElementById('insightSleepStatus'),
  exportSummaryBtn: document.getElementById('exportSummaryBtn'),
  insightsBookDocBtn: document.getElementById('insightsBookDocBtn'),

  // Emergency & Hotlines
  emergencyHotlinesList: document.getElementById('emergencyHotlinesList'),
  emergencyModal: document.getElementById('emergencyModal'),
  modalHotlinesGrid: document.getElementById('modalHotlinesGrid'),
  closeEmergencyModalBtn: document.getElementById('closeEmergencyModalBtn'),
  modalDismissBtn: document.getElementById('modalDismissBtn'),
  modalGroundingBtn: document.getElementById('modalGroundingBtn'),

  // Breathing Pacer
  breathingCircle: document.getElementById('breathingCircle'),
  breathingActionText: document.getElementById('breathingActionText'),
  breathingCountdown: document.getElementById('breathingCountdown'),
  startBreathingBtn: document.getElementById('startBreathingBtn'),
  stopBreathingBtn: document.getElementById('stopBreathingBtn'),

  // Booking Modal
  bookingModal: document.getElementById('bookingModal'),
  bookingForm: document.getElementById('bookingForm'),
  closeBookingModalBtn: document.getElementById('closeBookingModalBtn'),
  cancelBookingBtn: document.getElementById('cancelBookingBtn'),
  bookDocAvatar: document.getElementById('bookDocAvatar'),
  bookDocName: document.getElementById('bookDocName'),
  bookDocTitle: document.getElementById('bookDocTitle'),
  bookDocMeta: document.getElementById('bookDocMeta'),
  bookProviderId: document.getElementById('bookProviderId'),
  bookDate: document.getElementById('bookDate'),
  bookSlot: document.getElementById('bookSlot'),

  // Success Modal
  successModal: document.getElementById('successModal'),
  closeSuccessModalBtn: document.getElementById('closeSuccessModalBtn'),
  doneBookingBtn: document.getElementById('doneBookingBtn'),
  vCode: document.getElementById('vCode'),
  vDoc: document.getElementById('vDoc'),
  vDateTime: document.getElementById('vDateTime'),
  vMode: document.getElementById('vMode'),
  vFee: document.getElementById('vFee')
};

// ==========================================================================
// NEURO-BIOPHILIC AMBIENT CANVAS
// ==========================================================================

function initAmbientCanvas() {
  const canvas = document.getElementById('ambientCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  let width = canvas.width = window.innerWidth;
  let height = canvas.height = window.innerHeight;

  window.addEventListener('resize', () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  });

  const particles = [];
  const particleCount = 28;

  for (let i = 0; i < particleCount; i++) {
    particles.push({
      x: Math.random() * width,
      y: Math.random() * height,
      radius: Math.random() * 2.5 + 1.2,
      vx: (Math.random() - 0.5) * 0.35,
      vy: (Math.random() - 0.5) * 0.35,
      alpha: Math.random() * 0.4 + 0.15,
      hue: Math.random() > 0.5 ? 174 : 260 // Teal or Lavender
    });
  }

  function render() {
    ctx.clearRect(0, 0, width, height);

    particles.forEach((p, idx) => {
      p.x += p.vx;
      p.y += p.vy;

      if (p.x < 0) p.x = width;
      if (p.x > width) p.x = 0;
      if (p.y < 0) p.y = height;
      if (p.y > height) p.y = 0;

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
      ctx.fillStyle = `hsla(${p.hue}, 80%, 65%, ${p.alpha})`;
      ctx.shadowBlur = 12;
      ctx.shadowColor = `hsla(${p.hue}, 80%, 65%, 0.4)`;
      ctx.fill();

      // Connect near particles
      for (let j = idx + 1; j < particles.length; j++) {
        const p2 = particles[j];
        const dist = Math.hypot(p.x - p2.x, p.y - p2.y);
        if (dist < 130) {
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(p2.x, p2.y);
          ctx.strokeStyle = `hsla(${p.hue}, 70%, 60%, ${0.12 * (1 - dist / 130)})`;
          ctx.lineWidth = 0.7;
          ctx.stroke();
        }
      }
    });

    requestAnimationFrame(render);
  }

  render();
}

// ==========================================================================
// THERAPEUTIC CALMING MUSIC ENGINE (PROJECT AUDIO TRACKS)
// ==========================================================================

const MUSIC_TRACKS = {
  off: {
    id: 'off',
    title: 'No Sound (Muted)',
    short: 'Music: Off',
    src: null,
    desc: 'Completely quiet dialogue space without background audio',
    tempo: '0 BPM',
    rhythm: 'Silent',
    harmony: 'Neutral',
    icon: 'volume-x',
    normGain: 1.0
  },
  track1: {
    id: 'track1',
    title: '1. Peaceful Sanctuary',
    short: 'Music: Sanctuary',
    src: 'music/WhatsApp Audio 2026-08-31 at 22.32.33.mpeg',
    desc: 'Calming acoustic for peaceful mental settlement · 68 BPM gentle modal harmony',
    tempo: '68 BPM',
    rhythm: 'Steady, predictable rhythm; zero percussion',
    harmony: 'Warm, consonant Major/Lydian harmony',
    icon: 'sparkles',
    normGain: 1.00
  },
  track2: {
    id: 'track2',
    title: '2. Deep Emotional Calm',
    short: 'Music: Deep Calm',
    src: 'music/WhatsApp Audio 2026-08-31 at 22.36.20.mpeg',
    desc: 'Restorative steady track for emotional balance · 64 BPM predictable ambient flow',
    tempo: '64 BPM',
    rhythm: 'Slow predictable cadence; no harsh drums',
    harmony: 'Consonant, emotionally neutral healing chords',
    icon: 'heart',
    normGain: 1.05
  },
  track3: {
    id: 'track3',
    title: '3. Tranquil Zen Meditation',
    short: 'Music: Zen Meditation',
    src: 'music/WhatsApp Audio 2026-08-31 at 22.38.50.mpeg',
    desc: 'Gentle acoustic harmony for peace & stillness · 72 BPM repetitive soothing melody',
    tempo: '72 BPM',
    rhythm: 'Steady, relaxing heartbeat tempo; no percussion',
    harmony: 'Warm stable consonant modal harmony',
    icon: 'wind',
    normGain: 0.95
  },
  track4: {
    id: 'track4',
    title: '4. Soft Healing Harmony',
    short: 'Music: Soft Harmony',
    src: 'music/WhatsApp Audio 2026-08-31 at 22.40.44.mpeg',
    desc: 'Resonant chords for settling racing thoughts · 66 BPM low-complexity melody',
    tempo: '66 BPM',
    rhythm: 'Predictable, fluid ambient rhythm',
    harmony: 'Consonant modal chords; emotionally settling',
    icon: 'activity',
    normGain: 1.00
  },
  track5: {
    id: 'track5',
    title: '5. Gentle Mind Equilibrium',
    short: 'Music: Equilibrium',
    src: 'music/WhatsApp Audio 2026-08-31 at 22.42.35.mpeg',
    desc: 'Balancing soothing melodic chords · 70 BPM soft repetitive progression',
    tempo: '70 BPM',
    rhythm: 'Steady gentle pulse; zero prominent percussion',
    harmony: 'Warm, grounded, consonant harmony',
    icon: 'compass',
    normGain: 0.92
  },
  track6: {
    id: 'track6',
    title: '6. Quiet Solace & Breath',
    short: 'Music: Quiet Solace',
    src: 'music/WhatsApp Audio 2026-08-31 at 22.44.43.mpeg',
    desc: 'Slow peaceful tempo for deep somatic grounding · 60 BPM resting heart cadence',
    tempo: '60 BPM',
    rhythm: 'Simple, ultra-steady, predictable rhythm',
    harmony: 'Gentle modal sound; emotionally neutral',
    icon: 'cloud-moon',
    normGain: 1.08
  },
  track7: {
    id: 'track7',
    title: '7. Ethereal Serenity',
    short: 'Music: Serenity',
    src: 'music/WhatsApp Audio 2026-08-31 at 22.47.10.mpeg',
    desc: 'Light peaceful mental clarity & soft focus · 76 BPM repetitive acoustic serenity',
    tempo: '76 BPM',
    rhythm: 'Smooth continuous flow; no percussion',
    harmony: 'Consonant, bright, emotionally uplifting modal bed',
    icon: 'sun',
    normGain: 0.96
  },
  track8: {
    id: 'track8',
    title: '8. Restorative Stillness',
    short: 'Music: Stillness',
    src: 'music/WhatsApp Audio 2026-08-31 at 22.49.28.mpeg',
    desc: 'Deep relaxation & nervous system ease · 62 BPM low-complexity ambient body',
    tempo: '62 BPM',
    rhythm: 'Soft, predictable cadence; zero percussion',
    harmony: 'Consonant, grounded, emotionally stabilizing',
    icon: 'waves',
    normGain: 1.04
  }
};

// ==========================================================================
// NEURO-ACOUSTIC MIND HEALING & BRAINWAVE STABILIZATION ENGINE
// Transforms depression, sadness, anxiety, and tension into emotional balance
// ==========================================================================

const NEURO_MODES = {
  alpha: {
    id: 'alpha',
    name: '432 Hz Alpha Wave',
    badge: 'Tension & Panic Relief',
    baseFreq: 432,      // 432 Hz Solfeggio sacred harmonic
    beatFreq: 10.0,     // 10 Hz Alpha: reduces cortisol, calms chest tightness & anxiety
    vol: 0.038
  },
  theta: {
    id: 'theta',
    name: '528 Hz Solfeggio Theta',
    badge: 'Sadness & Grief Lift',
    baseFreq: 528,      // 528 Hz Transformation Solfeggio
    beatFreq: 6.0,      // 6 Hz Theta: lifts melancholic depression, sorrow & burnout
    vol: 0.035
  },
  delta: {
    id: 'delta',
    name: '174 Hz Delta Stillness',
    badge: 'Deep Somatic Rest',
    baseFreq: 174,      // 174 Hz Anesthetic / grounding resonance
    beatFreq: 3.5,      // 3.5 Hz Delta: full-body nervous system release
    vol: 0.042
  },
  pure: {
    id: 'pure',
    name: 'Pure Acoustic Melody',
    badge: 'Standard',
    baseFreq: 0,
    beatFreq: 0,
    vol: 0
  }
};

let neuroAudioCtx = null;
let neuroOscLeft = null;
let neuroOscRight = null;
let neuroGain = null;
let neuroPannerLeft = null;
let neuroPannerRight = null;

function setNeuroMode(modeKey) {
  state.neuroMode = modeKey;
  localStorage.setItem('mb_neuro_mode', modeKey);
  const mode = NEURO_MODES[modeKey] || NEURO_MODES.alpha;

  // Update UI buttons
  const btns = document.querySelectorAll('.neuro-mode-btn');
  btns.forEach(b => {
    b.classList.toggle('active', b.getAttribute('data-neuro') === modeKey);
  });

  const badge = document.getElementById('neuroStatusBadge');
  if (badge) {
    badge.innerHTML = `<i data-lucide="sparkles"></i> ${mode.name} Active`;
    if (window.lucide) window.lucide.createIcons();
  }

  // Update real-time harmonic tone
  applyNeuroTone(mode);
}

function applyNeuroTone(mode) {
  if (state.soundMuted || state.soundscapeActive === 'off' || !mode || mode.baseFreq === 0) {
    if (neuroGain && neuroAudioCtx) {
      neuroGain.gain.setTargetAtTime(0, neuroAudioCtx.currentTime, 0.8);
    }
    return;
  }

  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return;

    if (!neuroAudioCtx) {
      neuroAudioCtx = new AudioCtx();
    }

    if (neuroAudioCtx.state === 'suspended') {
      neuroAudioCtx.resume().catch(() => {});
    }

    if (!neuroGain) {
      neuroGain = neuroAudioCtx.createGain();
      neuroGain.gain.setValueAtTime(0, neuroAudioCtx.currentTime);

      const filter = neuroAudioCtx.createBiquadFilter();
      filter.type = 'lowpass';
      filter.frequency.setValueAtTime(300, neuroAudioCtx.currentTime);

      neuroGain.connect(filter);
      filter.connect(neuroAudioCtx.destination);
    }

    // Stop old oscillators if running
    if (neuroOscLeft) {
      try { neuroOscLeft.stop(); neuroOscLeft.disconnect(); } catch(e){}
    }
    if (neuroOscRight) {
      try { neuroOscRight.stop(); neuroOscRight.disconnect(); } catch(e){}
    }

    // Left ear carrier wave (Base - Beat/2)
    neuroOscLeft = neuroAudioCtx.createOscillator();
    neuroOscLeft.type = 'sine';
    neuroOscLeft.frequency.setValueAtTime(mode.baseFreq - (mode.beatFreq / 2), neuroAudioCtx.currentTime);

    // Right ear carrier wave (Base + Beat/2)
    neuroOscRight = neuroAudioCtx.createOscillator();
    neuroOscRight.type = 'sine';
    neuroOscRight.frequency.setValueAtTime(mode.baseFreq + (mode.beatFreq / 2), neuroAudioCtx.currentTime);

    neuroPannerLeft = neuroAudioCtx.createStereoPanner ? neuroAudioCtx.createStereoPanner() : null;
    neuroPannerRight = neuroAudioCtx.createStereoPanner ? neuroAudioCtx.createStereoPanner() : null;

    if (neuroPannerLeft && neuroPannerRight) {
      neuroPannerLeft.pan.setValueAtTime(-0.7, neuroAudioCtx.currentTime);
      neuroPannerRight.pan.setValueAtTime(0.7, neuroAudioCtx.currentTime);

      neuroOscLeft.connect(neuroPannerLeft);
      neuroPannerLeft.connect(neuroGain);

      neuroOscRight.connect(neuroPannerRight);
      neuroPannerRight.connect(neuroGain);
    } else {
      neuroOscLeft.connect(neuroGain);
      neuroOscRight.connect(neuroGain);
    }

    neuroOscLeft.start();
    neuroOscRight.start();

    // Smooth gentle sinusoidal volume ramp
    neuroGain.gain.setTargetAtTime(mode.vol, neuroAudioCtx.currentTime, 1.2);
  } catch (err) {
    console.log('Neuro-Acoustic synthesis note:', err);
  }
}

// ==========================================================================
// THERAPEUTIC CALMING AUDIO ENGINE (ZERO-CLICK AUTOPLAY & SMOOTH FADES)
// ==========================================================================

let fadeAnimationTimer = null;
let autoplayWatchdogTimer = null;
let gestureListenersBound = false;

// Standard gradual fade durations (2-5s specification)
const FADE_IN_DURATION_MS = 3800;  // 3.8s gradual sinusoidal fade-in
const FADE_OUT_DURATION_MS = 3200; // 3.2s gradual sinusoidal fade-out

/**
 * Strict Safe Volume Ceiling Limiter (WHO & Evidence-based audio specification)
 * 1. Maximum Volume Cap: User can increase only up to 15–25% (0.22 actual gain)
 * 2. Default Volume: Starts around 5–10% (~0.075 actual gain on initial opt-in)
 * 3. Volume Slider Mapping: Range 0-100 mapped to 0.0 - 0.22 actual gain
 * 4. Loudness Normalization: Perceived loudness equalized across all tracks via normGain
 * 5. Auto-Ducking: Lower music by 12–18 dB when chatbot speaks
 * 6. Full Pause During Recording: Zero audio enters microphone
 */
const MAX_SAFE_CEILING_VOLUME = 0.22; // 22% maximum physical gain cap
const DEFAULT_SAFE_START_VOLUME = 0.35; // 35% on UI slider = ~0.075 actual audio gain (in 5–10% range)

function getRealVolume(sliderVal, trackKey = state.soundscapeActive) {
  const norm = Math.max(0, Math.min(1, parseFloat(sliderVal) || 0));
  const track = MUSIC_TRACKS[trackKey] || {};
  const normGain = track.normGain || 1.0;
  // Exponential curve mapping 0-100 to 0.0 - 0.22 gain with loudness normalization
  const calculated = Math.pow(norm, 1.15) * MAX_SAFE_CEILING_VOLUME * normGain;
  return Math.min(MAX_SAFE_CEILING_VOLUME, calculated);
}

function getVolumeLevelLabel(percent) {
  if (state.soundMuted || percent === 0) return '0% (Muted)';
  if (percent <= 20) return `${percent}% (Whisper ~4% gain)`;
  if (percent <= 45) return `${percent}% (Gentle Default ~8% gain)`;
  if (percent <= 75) return `${percent}% (Balanced Calming ~14% gain)`;
  return `${percent}% (Max Safe Ceiling 22% gain)`;
}

let isAudioDucked = false;
let duckingIntervalTimer = null;

/**
 * Auto-Ducking Engine: Lowers music by 12–18 dB (0.18x multiplier) when chatbot speaks
 */
function duckBackgroundAudio(shouldDuck, durationMs = 350) {
  const audio = getAudioElement();
  if (!audio || audio.paused || state.soundscapeActive === 'off' || state.soundMuted) return;

  if (duckingIntervalTimer) {
    clearInterval(duckingIntervalTimer);
    duckingIntervalTimer = null;
  }

  isAudioDucked = shouldDuck;
  const baseGain = getRealVolume(state.soundVolume, state.soundscapeActive);
  
  // Auto-Ducking: Lower music by 12–18 dB (approx 15 dB = 0.18x multiplier)
  const targetGain = shouldDuck ? (baseGain * 0.18) : baseGain;
  const startGain = audio.volume;
  const startTime = Date.now();

  duckingIntervalTimer = setInterval(() => {
    const elapsed = Date.now() - startTime;
    const progress = Math.min(1, elapsed / durationMs);
    audio.volume = startGain + (targetGain - startGain) * progress;
    if (progress >= 1) {
      audio.volume = targetGain;
      clearInterval(duckingIntervalTimer);
      duckingIntervalTimer = null;
    }
  }, 20);
}

function cancelFade() {
  if (fadeAnimationTimer) {
    clearInterval(fadeAnimationTimer);
    fadeAnimationTimer = null;
  }
}

/**
 * Gradual 2-5s Sinusoidal Fade-In (Soft, gradual, zero clicks or abrupt loudness)
 */
function fadeAudioIn(audio, targetSliderVol = DEFAULT_SAFE_START_VOLUME, durationMs = FADE_IN_DURATION_MS) {
  cancelFade();
  if (state.soundMuted) {
    if (audio) audio.volume = 0;
    return;
  }

  if (!audio) return;
  audio.volume = 0;
  const startVolume = 0;
  const endVolume = getRealVolume(targetSliderVol, state.soundscapeActive);
  const startTime = Date.now();
  const stepInterval = 25;

  fadeAnimationTimer = setInterval(() => {
    const elapsed = Date.now() - startTime;
    const progress = Math.min(1, elapsed / durationMs);

    // Smooth Cosine S-Curve easing for ultra-gentle, silky entry
    const easedProgress = 0.5 * (1 - Math.cos(progress * Math.PI));
    const currentVol = startVolume + (endVolume - startVolume) * easedProgress;

    audio.volume = Math.min(MAX_SAFE_CEILING_VOLUME, currentVol);

    if (progress >= 1) {
      audio.volume = endVolume;
      clearInterval(fadeAnimationTimer);
      fadeAnimationTimer = null;
    }
  }, stepInterval);
}

/**
 * Gradual 2-5s Sinusoidal Fade-Out (Softly decays to silence before pausing)
 */
function fadeAudioOut(audio, durationMs = FADE_OUT_DURATION_MS, onComplete) {
  cancelFade();
  if (!audio || audio.paused) {
    if (onComplete) onComplete();
    return;
  }

  const startVolume = audio.volume;
  const startTime = Date.now();
  const stepInterval = 25;

  fadeAnimationTimer = setInterval(() => {
    const elapsed = Date.now() - startTime;
    const progress = Math.min(1, elapsed / durationMs);

    // Inverse Cosine S-Curve for smooth, gentle decay
    const easedProgress = 0.5 * (1 + Math.cos(progress * Math.PI));
    const currentVol = Math.max(0, startVolume * easedProgress);

    audio.volume = currentVol;

    if (progress >= 1 || currentVol <= 0.002) {
      audio.volume = 0;
      clearInterval(fadeAnimationTimer);
      fadeAnimationTimer = null;
      audio.pause();
      if (onComplete) onComplete();
    }
  }, stepInterval);
}

function getAudioElement() {
  if (!state.audioElement) {
    const domAudio = document.getElementById('bgMusicAudio');
    state.audioElement = domAudio || new Audio();
    state.audioElement.loop = true;
    state.audioElement.preload = 'auto';
    state.audioElement.playsInline = true;
    state.audioElement.playbackRate = 1.0;
    state.audioElement.defaultPlaybackRate = 1.0;
    if ('preservesPitch' in state.audioElement) {
      state.audioElement.preservesPitch = true;
    }

    const defaultSrc = MUSIC_TRACKS.track3.src;
    if (!state.audioElement.src || !state.audioElement.src.includes('WhatsApp')) {
      state.audioElement.src = defaultSrc;
    }

    state.audioElement.addEventListener('play', () => {
      state.soundPlaying = true;
      updateSoundUI();
    });

    state.audioElement.addEventListener('playing', () => {
      state.soundPlaying = true;
      updateSoundUI();
    });

    state.audioElement.addEventListener('pause', () => {
      if (state.soundscapeActive === 'off') {
        state.soundPlaying = false;
      }
      updateSoundUI();
    });

    // Seamless clean loop handler
    let isLoopBoundaryActive = false;
    state.audioElement.addEventListener('ended', () => {
      if (state.soundscapeActive !== 'off') {
        state.audioElement.currentTime = 0.01;
        state.audioElement.play().catch(() => {});
      }
    });

    // Sub-second precision seamless clean loop smoothing (zero clicks or sudden interruptions)
    state.audioElement.addEventListener('timeupdate', () => {
      if (state.soundscapeActive !== 'off' && state.audioElement.duration && !isLoopBoundaryActive) {
        const remaining = state.audioElement.duration - state.audioElement.currentTime;
        if (remaining <= 0.12 && remaining > 0) {
          isLoopBoundaryActive = true;
          state.audioElement.currentTime = 0.01;
          setTimeout(() => { isLoopBoundaryActive = false; }, 200);
        }
      }
    });

    state.audioElement.addEventListener('error', (e) => {
      console.warn('MindBridge Background Music notice:', e);
    });
  }
  return state.audioElement;
}

function startAutoMusic() {
  if (state.soundscapeActive === 'off') return;

  const audio = getAudioElement();
  const track = MUSIC_TRACKS[state.soundscapeActive] || MUSIC_TRACKS.track3;
  const targetSliderVol = state.soundMuted ? 0 : state.soundVolume;

  if (!audio.src.includes(encodeURI(track.src)) && !audio.src.endsWith(track.src)) {
    audio.src = track.src;
  }

  audio.loop = true;

  const playPromise = audio.play();
  if (playPromise !== undefined) {
    playPromise.then(() => {
      state.soundPlaying = true;
      fadeAudioIn(audio, targetSliderVol, FADE_IN_DURATION_MS);
      updateSoundUI();
    }).catch(() => {});
  }
}

function initSoundscapes() {
  // 1. Setup Header Quick Buttons to open Settings Modal
  const soundscapeBtn = document.getElementById('soundscapeBtn');
  if (soundscapeBtn) {
    soundscapeBtn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      openSettingsModal();
    });
  }

  const headerSettingsBtn = document.getElementById('headerSettingsBtn');
  if (headerSettingsBtn) {
    headerSettingsBtn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      openSettingsModal();
    });
  }

  // 2. Setup Comprehensive Settings Modal
  initSettingsModal();

  // 3. Setup Evidence-Informed Welcome Audio Opt-in (PDF Spec Section 1 & 4)
  initWelcomeAudioOptIn();

  // 4. Setup Always-Visible Quick Audio Tool (Rule #1: Visible pause, mute, volume controls)
  initQuickSoundPopup();

  // 5. Playback default: OFF by default
  state.soundscapeActive = localStorage.getItem('mb_music_pref') || 'off';
  state.soundPlaying = false;
  state.soundMuted = false;
  if (!state.soundVolume) state.soundVolume = DEFAULT_SAFE_START_VOLUME;

  // 6. Initial UI & Neuro-Acoustic sync
  updateSoundUI();
  setNeuroMode(state.neuroMode || 'alpha');
}

/**
 * Welcome Screen Audio Opt-In Card Handlers (PDF Spec Section 1 & 4)
 */
function initWelcomeAudioOptIn() {
  const optInCard = document.getElementById('welcomeAudioOptIn');
  const noSoundBtn = document.getElementById('optInNoSoundBtn');
  const instBtn = document.getElementById('optInInstrumentalBtn');
  const natureBtn = document.getElementById('optInNatureBtn');
  const laterBtn = document.getElementById('optInLaterBtn');

  if (noSoundBtn) {
    noSoundBtn.addEventListener('click', () => {
      setSoundscape('off');
      if (optInCard) optInCard.style.display = 'none';
      localStorage.setItem('mb_optin_done', 'true');
    });
  }

  if (instBtn) {
    instBtn.addEventListener('click', () => {
      setSoundVolume(DEFAULT_SAFE_START_VOLUME);
      setSoundscape('track3', true); // 03 Tranquil Zen / Soft Instrumental (72 BPM)
      if (optInCard) optInCard.style.display = 'none';
      localStorage.setItem('mb_optin_done', 'true');
    });
  }

  if (natureBtn) {
    natureBtn.addEventListener('click', () => {
      setSoundVolume(DEFAULT_SAFE_START_VOLUME);
      setSoundscape('track8', true); // 08 Restorative Stillness / Nature Waves (62 BPM)
      if (optInCard) optInCard.style.display = 'none';
      localStorage.setItem('mb_optin_done', 'true');
    });
  }

  if (laterBtn) {
    laterBtn.addEventListener('click', () => {
      if (optInCard) optInCard.style.display = 'none';
    });
  }
}

/**
 * Universal Popup Coordinator for All Tool Badges & Dropdowns
 */
function closeAllConsolePopups(exceptEl = null) {
  const popups = [
    document.getElementById('perspectivePopupMenu'),
    document.getElementById('moodPopupMenu'),
    document.getElementById('somaticPopupMenu'),
    document.getElementById('pastLifePopupMenu'),
    document.getElementById('soundQuickPopup')
  ];
  popups.forEach(p => {
    if (p && p !== exceptEl) {
      p.style.display = 'none';
    }
  });
}

/**
 * Always-Visible Audio Controller Popup (Rule #1: Visible pause, mute, volume controls)
 */
function initQuickSoundPopup() {
  const quickSoundBtn = document.getElementById('quickSoundBtn');
  const soundPopup = document.getElementById('soundQuickPopup');
  const playPauseBtn = document.getElementById('sqpPlayPauseBtn');
  const muteBtn = document.getElementById('sqpMuteBtn');
  const volSlider = document.getElementById('sqpVolumeSlider');

  if (quickSoundBtn && soundPopup) {
    quickSoundBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const isShowing = soundPopup.style.display === 'flex';
      closeAllConsolePopups();
      if (!isShowing) {
        soundPopup.style.display = 'flex';
      }
    });

    soundPopup.addEventListener('click', (e) => {
      e.stopPropagation(); // prevent closing when interacting with popup sliders/buttons
    });
  }

  if (playPauseBtn) {
    playPauseBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      toggleSoundPlayback();
    });
  }

  if (muteBtn) {
    muteBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      toggleSoundMute();
    });
  }

  if (volSlider) {
    volSlider.value = Math.round(state.soundVolume * 100);
    volSlider.addEventListener('input', (e) => {
      const val = parseFloat(e.target.value) / 100;
      setSoundVolume(val);
    });
  }
}

function initSettingsModal() {
  const modal = document.getElementById('settingsModal');
  if (!modal) return;

  // Open & Close handlers
  const closeBtn = document.getElementById('closeSettingsModalBtn');
  if (closeBtn) {
    closeBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      hideSettingsModal();
    });
  }

  const doneBtn = document.getElementById('doneSettingsBtn');
  if (doneBtn) {
    doneBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      hideSettingsModal();
    });
  }

  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      hideSettingsModal();
    }
  });

  // Global Escape key close
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && (modal.classList.contains('active') || modal.style.display === 'flex')) {
      hideSettingsModal();
    }
  });

  // Settings Mute Button
  const muteBtn = document.getElementById('settingsMuteBtn');
  if (muteBtn) {
    muteBtn.addEventListener('click', () => {
      toggleSoundMute();
    });
  }

  // Settings Volume Slider
  const volSlider = document.getElementById('settingsVolumeSlider');
  const volVal = document.getElementById('settingsVolumeVal');
  if (volSlider) {
    volSlider.value = Math.round(state.soundVolume * 100);
    if (volVal) {
      volVal.textContent = getVolumeLevelLabel(Math.round(state.soundVolume * 100));
    }
    volSlider.addEventListener('input', (e) => {
      const val = parseFloat(e.target.value) / 100;
      setSoundVolume(val);
    });
  }

  // Safe Ambient Preset Buttons (Whisper / Gentle / Balanced / Safe Ceiling)
  document.querySelectorAll('.preset-vol-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const targetPct = parseInt(btn.getAttribute('data-vol'), 10) || 18;
      setSoundVolume(targetPct / 100);
    });
  });

  // Settings Track Selection Cards
  const trackCards = document.querySelectorAll('.settings-track-card');
  trackCards.forEach(card => {
    card.addEventListener('click', () => {
      const soundType = card.getAttribute('data-sound');
      setSoundscape(soundType, true);
    });
  });

  // Settings Language Select Sync
  const langSelect = document.getElementById('settingsLanguageSelect');
  if (langSelect) {
    langSelect.value = state.selectedLanguage;
    langSelect.addEventListener('change', (e) => {
      applyLanguage(e.target.value);
    });
  }

  // Voice Preview Button
  const previewVoiceBtn = document.getElementById('previewVoiceBtn');
  if (previewVoiceBtn) {
    previewVoiceBtn.addEventListener('click', () => {
      const previewPhrases = {
        'hi-IN': 'नमस्ते... मैं माइंडब्रिज हूँ। पहले एक गहरी और शांत साँस लीजिए... मैं हमेशा आपकी बात सुनने के लिए यहाँ मौजूद हूँ।',
        'en-IN': 'Hello... main MindBridge hoon. Pehle ek gentle, deep breath lijiye... main hamesha aapke saath hoon.',
        'en-US': 'Hello... I am MindBridge. Take a gentle, deep breath with me... I am right here listening with you.',
        'es-ES': 'Hola... soy MindBridge. Regálate una respiración suave y profunda... aquí estoy para escucharte con todo el corazón.',
        'pt-BR': 'Olá... eu sou o MindBridge. Respire fundo e com calma... eu estou aqui com você para te acolher.',
        'bn-IN': 'নমস্কার... আমি মাইন্ডব্রিজ। চলুন আগে একটি শান্ত ও গভীর শ্বাস নিই... আমি সর্বদা আপনার পাশে আছি।'
      };
      const phrase = previewPhrases[state.selectedLanguage] || previewPhrases['en-US'];
      speakText(phrase);
    });
  }

  // Settings Neuro-Acoustic Mode Buttons
  const neuroBtns = document.querySelectorAll('.neuro-mode-btn');
  neuroBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const neuro = btn.getAttribute('data-neuro');
      setNeuroMode(neuro);
    });
  });

  // Settings Clear History Button
  const clearBtn = document.getElementById('settingsClearBtn');
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      if (confirm('Start a fresh session? Current messages will be cleared.')) {
        state.conversationId = `conv-${Math.random().toString(36).substring(2, 9)}`;
        localStorage.setItem('mb_conv_id', state.conversationId);
        if (elements.chatMessages) {
          elements.chatMessages.innerHTML = '';
          addSystemMessage('Welcome to MindBridge. Take a gentle breath—I am here to listen whenever you feel ready.');
        }
        hideSettingsModal();
      }
    });
  }
}

function openSettingsModal() {
  const modal = elements.settingsModal || document.getElementById('settingsModal');
  if (modal) {
    modal.classList.add('active');
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    updateSoundUI();
    if (window.lucide) window.lucide.createIcons();
  }
}

function hideSettingsModal() {
  const modal = elements.settingsModal || document.getElementById('settingsModal');
  if (modal) {
    modal.classList.remove('active');
    modal.style.display = 'none';
    document.body.style.overflow = '';
  }
}

window.openSettingsModal = openSettingsModal;
window.hideSettingsModal = hideSettingsModal;

function setSoundscape(trackKey, isFadeIn = true) {
  if (trackKey === 'off') {
    fadeAudioOut(state.audioElement, FADE_OUT_DURATION_MS, () => {
      state.soundscapeActive = 'off';
      state.soundPlaying = false;
      localStorage.setItem('mb_music_pref', 'off');
      updateSoundUI();
    });
    return;
  }

  // Map legacy keys if any
  if (trackKey === 'instrumental') trackKey = 'track1';
  if (trackKey === 'nature' || trackKey === 'rain') trackKey = 'track2';
  if (trackKey === 'ocean') trackKey = 'track3';
  if (trackKey === 'binaural') trackKey = 'track4';
  if (trackKey === 'forest') trackKey = 'track6';

  const track = MUSIC_TRACKS[trackKey] || MUSIC_TRACKS.track3;
  const previousTrack = state.soundscapeActive;
  state.soundscapeActive = track.id;
  localStorage.setItem('mb_music_pref', track.id);

  const audio = getAudioElement();
  const encodedSrc = encodeURI(track.src);

  const startNewTrack = () => {
    if (!audio.src.endsWith(encodedSrc) && !audio.src.endsWith(track.src)) {
      audio.src = track.src;
      audio.load();
    }

    state.soundPlaying = true;
    updateSoundUI();

    const targetSliderVol = state.soundMuted ? 0 : state.soundVolume;

    const playPromise = audio.play();
    if (playPromise !== undefined) {
      playPromise.then(() => {
        state.soundPlaying = true;
        if (isFadeIn && !state.soundMuted) {
          fadeAudioIn(audio, targetSliderVol, FADE_IN_DURATION_MS); // 3.8s gradual smooth fade in
        } else {
          audio.volume = getRealVolume(targetSliderVol);
        }
        updateSoundUI();
      }).catch(err => {
        console.log('Autoplay waiting for user gesture:', err);
        updateSoundUI();
      });
    }
  };

  // If already playing another track, fade out current track first then switch
  if (state.soundPlaying && previousTrack !== 'off' && previousTrack !== track.id && !audio.paused) {
    fadeAudioOut(audio, 2400, () => {
      startNewTrack();
    });
  } else {
    startNewTrack();
  }
}

function stopMusic() {
  fadeAudioOut(state.audioElement, FADE_OUT_DURATION_MS, () => {
    state.soundPlaying = false;
    updateSoundUI();
  });
}

function stopAudioImmediately() {
  cancelFade();
  if (state.audioElement) {
    state.audioElement.pause();
    state.audioElement.volume = 0;
  }
  state.soundPlaying = false;
  state.soundscapeActive = 'off';
  localStorage.setItem('mb_music_pref', 'off');
  updateSoundUI();
}

function toggleSoundPlayback() {
  const audio = getAudioElement();
  if (state.soundPlaying && !audio.paused && state.soundscapeActive !== 'off') {
    fadeAudioOut(audio, FADE_OUT_DURATION_MS, () => {
      state.soundPlaying = false;
      updateSoundUI();
    });
  } else {
    const target = (state.soundscapeActive && state.soundscapeActive !== 'off') ? state.soundscapeActive : 'track3';
    setSoundscape(target, true);
  }
  updateSoundUI();
}

function toggleSoundMute() {
  state.soundMuted = !state.soundMuted;
  localStorage.setItem('mb_sound_muted', state.soundMuted);
  const audio = getAudioElement();
  if (state.soundMuted) {
    fadeAudioOut(audio, FADE_OUT_DURATION_MS);
  } else {
    fadeAudioIn(audio, state.soundVolume, FADE_IN_DURATION_MS);
  }
  applyNeuroTone(NEURO_MODES[state.neuroMode || 'alpha']);
  updateSoundUI();
}

function setSoundVolume(sliderVolume) {
  state.soundVolume = Math.max(0, Math.min(1, sliderVolume));
  state.soundMuted = false;
  localStorage.setItem('mb_sound_volume', state.soundVolume);
  localStorage.setItem('mb_sound_muted', 'false');
  cancelFade();
  if (state.audioElement) {
    state.audioElement.volume = getRealVolume(state.soundVolume);
  }
  updateSoundUI();
}

function updateSoundUI() {
  const currentTrack = MUSIC_TRACKS[state.soundscapeActive] || MUSIC_TRACKS.off;
  const isPlaying = state.soundPlaying && state.soundscapeActive !== 'off' && !state.soundMuted;

  // 1. Header controls & Left dock
  if (elements.soundscapeLabel) {
    elements.soundscapeLabel.textContent = isPlaying ? currentTrack.short : 'Music: Off';
  }
  if (elements.soundscapeBtn) {
    if (isPlaying) {
      elements.soundscapeBtn.classList.add('active');
    } else {
      elements.soundscapeBtn.classList.remove('active');
    }
  }

  const eqBars = document.getElementById('musicEqBars');
  if (eqBars) {
    eqBars.style.opacity = isPlaying ? '1' : '0.35';
  }

  // 2. Settings Modal Status Badge & Now Playing Name
  const trackDisplayName = currentTrack.title ? currentTrack.title.replace(/^\d+\.\s*/, '').trim() : currentTrack.short;
  if (elements.settingsActiveTrackBadge) {
    if (state.soundscapeActive === 'off' || !state.soundPlaying) {
      elements.settingsActiveTrackBadge.textContent = 'Music: Off · Click track to play';
    } else {
      elements.settingsActiveTrackBadge.textContent = `${trackDisplayName} · Playing (${currentTrack.tempo || '60-80 BPM'})`;
    }
  }
  if (elements.settingsNowPlayingName) {
    elements.settingsNowPlayingName.textContent = state.soundscapeActive === 'off' ? 'No Sound (Muted)' : trackDisplayName;
  }

  // 3. Settings Mute Button
  if (elements.settingsMuteIcon) {
    elements.settingsMuteIcon.setAttribute('data-lucide', state.soundMuted || state.soundVolume === 0 ? 'volume-x' : 'volume-2');
  }
  if (elements.settingsMuteText) {
    elements.settingsMuteText.textContent = state.soundMuted ? 'Unmute' : 'Mute';
  }

  // 4. Settings Volume Slider & Number
  const currentPct = Math.round(state.soundVolume * 100);
  if (elements.settingsVolumeSlider) {
    elements.settingsVolumeSlider.value = state.soundMuted ? 0 : currentPct;
  }
  if (elements.settingsVolumeVal) {
    elements.settingsVolumeVal.textContent = getVolumeLevelLabel(state.soundMuted ? 0 : currentPct);
  }

  // 4b. Sync Preset Buttons active state
  document.querySelectorAll('.preset-vol-btn').forEach(btn => {
    const btnVol = parseInt(btn.getAttribute('data-vol'), 10);
    btn.classList.toggle('active', btnVol === currentPct && !state.soundMuted);
  });

  // 5. Always-Visible Quick Audio Tool Popup (Rule #1)
  const sqpTrackName = document.getElementById('sqpTrackName');
  if (sqpTrackName) {
    sqpTrackName.textContent = state.soundscapeActive === 'off' ? 'No Sound (Silent)' : trackDisplayName;
  }
  const sqpStatusBadge = document.getElementById('sqpStatusBadge');
  if (sqpStatusBadge) {
    sqpStatusBadge.textContent = isPlaying ? 'Playing' : 'Off';
  }
  const sqpPlayPauseIcon = document.getElementById('sqpPlayPauseIcon');
  if (sqpPlayPauseIcon) {
    sqpPlayPauseIcon.setAttribute('data-lucide', isPlaying ? 'pause' : 'play');
  }
  const sqpMuteIcon = document.getElementById('sqpMuteIcon');
  if (sqpMuteIcon) {
    sqpMuteIcon.setAttribute('data-lucide', state.soundMuted ? 'volume-x' : 'volume-2');
  }
  const sqpVolSlider = document.getElementById('sqpVolumeSlider');
  if (sqpVolSlider) {
    sqpVolSlider.value = state.soundMuted ? 0 : Math.round(state.soundVolume * 100);
  }
  const sqpVolVal = document.getElementById('sqpVolumeVal');
  if (sqpVolVal) {
    sqpVolVal.textContent = state.soundMuted ? '0%' : `${Math.round(state.soundVolume * 100)}%`;
  }

  // 6. Active state on Settings Track Cards
  if (elements.settingsTrackCards) {
    elements.settingsTrackCards.forEach(card => {
      const snd = card.getAttribute('data-sound');
      if (snd === state.soundscapeActive) {
        card.classList.add('active');
      } else {
        card.classList.remove('active');
      }
    });
  }

  if (window.lucide) {
    window.lucide.createIcons();
  }
}

// ==========================================================================
// EMOTIONAL WEATHER & SOMATIC TENSION MAPPING
// ==========================================================================

function initEmotionalWeather() {
  const moodMenu = document.getElementById('moodPopupMenu');
  if (!moodMenu) return;

  moodMenu.querySelectorAll('.weather-pill').forEach(pill => {
    pill.addEventListener('click', (e) => {
      e.stopPropagation();
      moodMenu.querySelectorAll('.weather-pill').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      closeAllConsolePopups();

      const prompt = pill.getAttribute('data-prompt');
      const mood = pill.getAttribute('data-mood');

      // Shift dynamic ambient atmosphere
      const glowTeal = document.querySelector('.glow-teal');
      const glowAmethyst = document.querySelector('.glow-amethyst');

      if (mood === 'overwhelmed' || mood === 'anxious') {
        if (glowTeal) glowTeal.style.background = 'radial-gradient(circle, #f59e0b 0%, rgba(245,158,11,0) 70%)';
        if (glowAmethyst) glowAmethyst.style.background = 'radial-gradient(circle, #8b5cf6 0%, rgba(139,92,246,0) 70%)';
        setNeuroMode('alpha'); // 432Hz Alpha: stabilizes tension & panic
      } else if (mood === 'heavy') {
        if (glowTeal) glowTeal.style.background = 'radial-gradient(circle, #3b82f6 0%, rgba(59,130,246,0) 70%)';
        if (glowAmethyst) glowAmethyst.style.background = 'radial-gradient(circle, #4c1d95 0%, rgba(76,29,149,0) 70%)';
        setNeuroMode('theta'); // 528Hz Theta: relieves sadness, sorrow & grief
      } else if (mood === 'sleep') {
        if (glowTeal) glowTeal.style.background = 'radial-gradient(circle, #6366f1 0%, rgba(99,102,241,0) 70%)';
        if (glowAmethyst) glowAmethyst.style.background = 'radial-gradient(circle, #1e1b4b 0%, rgba(30,27,75,0) 70%)';
        setNeuroMode('delta'); // 174Hz Delta: deep somatic rest
      } else if (mood === 'hopeful') {
        if (glowTeal) glowTeal.style.background = 'radial-gradient(circle, #10b981 0%, rgba(16,185,129,0) 70%)';
        if (glowAmethyst) glowAmethyst.style.background = 'radial-gradient(circle, #06b6d4 0%, rgba(6,182,212,0) 70%)';
      } else {
        if (glowTeal) glowTeal.style.background = 'radial-gradient(circle, #0d9488 0%, rgba(13,148,136,0) 70%)';
        if (glowAmethyst) glowAmethyst.style.background = 'radial-gradient(circle, #6366f1 0%, rgba(99,102,241,0) 70%)';
      }

      if (prompt) {
        elements.chatInput.value = prompt;
        submitChatMessage();
      }
    });
  });
}

function initSomaticCheckin() {
  const somaticMenu = document.getElementById('somaticPopupMenu');
  if (!somaticMenu) return;

  somaticMenu.querySelectorAll('.somatic-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      closeAllConsolePopups();
      const prompt = btn.getAttribute('data-prompt');
      const text = btn.textContent.toLowerCase();

      if (text.includes('chest') || text.includes('racing') || text.includes('head')) {
        setNeuroMode('alpha'); // Dissolves acute somatic adrenaline spikes
      } else if (text.includes('drain') || text.includes('knots') || text.includes('stomach') || text.includes('neck')) {
        setNeuroMode('delta'); // Deep nervous system physical decompression
      }

      if (prompt) {
        elements.chatInput.value = prompt;
        submitChatMessage();
      }
    });
  });
}

// ==========================================================================
// TAB NAVIGATION
// ==========================================================================

function initTabs() {
  elements.tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const target = tab.getAttribute('data-tab');
      switchTab(target);
    });
  });

  if (elements.brandHomeBtn) {
    elements.brandHomeBtn.addEventListener('click', () => switchTab('chat'));
  }

  if (elements.insightsBookDocBtn) {
    elements.insightsBookDocBtn.addEventListener('click', () => switchTab('providers'));
  }
}

function switchTab(tabId) {
  elements.tabs.forEach(t => {
    t.classList.toggle('active', t.getAttribute('data-tab') === tabId);
  });
  elements.panes.forEach(p => {
    p.classList.toggle('active', p.id === `tab-${tabId}`);
  });

  if (tabId === 'insights') {
    loadInsights();
  }
  if (tabId === 'screener') {
    loadScreenerSession();
  }
  if (window.lucide) {
    window.lucide.createIcons();
  }
}

// ==========================================================================
// CHAT & CONVERSATIONAL ENGINE
// ==========================================================================

function initChatInput() {
  if (elements.sendBtn) {
    elements.sendBtn.addEventListener('click', (e) => {
      e.preventDefault();
      submitChatMessage();
    });
  }

  if (elements.chatInput) {
    elements.chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        submitChatMessage();
      }
    });

    // Auto-expand textarea
    elements.chatInput.addEventListener('input', () => {
      elements.chatInput.style.height = 'auto';
      elements.chatInput.style.height = Math.min(160, elements.chatInput.scrollHeight) + 'px';
    });
  }

  // Suggestion Prompt Cards (Past Life, Surprise me, Somatic release, Specialist care)
  document.querySelectorAll('.prompt-suggestion-card').forEach(card => {
    card.addEventListener('click', (e) => {
      closeAllConsolePopups();
      const action = card.getAttribute('data-action');
      const prompt = card.getAttribute('data-prompt');
      if (action === 'tab-providers') {
        switchTab('providers');
      } else if (prompt) {
        elements.chatInput.value = prompt;
        submitChatMessage();
      }
    });
  });

  // Mood Climate & Somatic Popups
  const quickMoodBtn = document.getElementById('quickMoodBtn');
  const moodMenu = document.getElementById('moodPopupMenu');
  if (quickMoodBtn && moodMenu) {
    quickMoodBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const isShowing = moodMenu.style.display === 'flex';
      closeAllConsolePopups();
      if (!isShowing) moodMenu.style.display = 'flex';
    });
  }

  const quickSomaticBtn = document.getElementById('quickSomaticBtn');
  const somaticMenu = document.getElementById('somaticPopupMenu');
  if (quickSomaticBtn && somaticMenu) {
    quickSomaticBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const isShowing = somaticMenu.style.display === 'flex';
      closeAllConsolePopups();
      if (!isShowing) somaticMenu.style.display = 'flex';
    });
  }

  // Header Guardrails Badge Clickable
  const safetyBadge = document.querySelector('.stage-safety-badge');
  if (safetyBadge && !safetyBadge.dataset.bound) {
    safetyBadge.dataset.bound = 'true';
    safetyBadge.style.cursor = 'pointer';
    safetyBadge.title = 'Click to view safety and evidence grounding';
    safetyBadge.addEventListener('click', () => {
      alert('MindBridge Sanctuary Safety & Evidence Guardrails:\n\n• Grounded in clinical psychometrics (PHQ-9, GAD-7, DASS-21, WHO-5, C-SSRS).\n• Non-diagnostic: MindBridge provides emotional reflection, somatic grounding, and specialist matching.\n• Automatic Crisis Escalation: Acute distress markers immediately prioritize 24/7 crisis hotlines.');
    });
  }

  // Global Outside-Click Coordinator for Console Dropdowns
  document.addEventListener('click', (e) => {
    const isInsidePopupWrap = e.target.closest(
      '.perspective-dropdown-wrap, .mood-dropdown-wrap, .somatic-dropdown-wrap, .past-life-dropdown-wrap, .soundscape-dropdown-wrap'
    );
    if (!isInsidePopupWrap) {
      closeAllConsolePopups();
    }
  });

  // Dynamic Suggestion Chips
  document.addEventListener('click', (e) => {
    const chip = e.target.closest('.chip-btn');
    if (chip) {
      closeAllConsolePopups();
      const promptText = chip.getAttribute('data-text');
      if (promptText) {
        elements.chatInput.value = promptText;
        submitChatMessage();
      }
    }
  });

  if (elements.exportSummaryBtn) {
    elements.exportSummaryBtn.addEventListener('click', downloadSummaryDocument);
  }
}

async function submitChatMessage(audioDetected = false) {
  const message = elements.chatInput.value.trim();
  if (!message) return;

  // Stop any ongoing speech playback immediately — but skip if barge-in already handled it
  if (!audioDetected) {
    stopSpeaking();
  }

  // Reveal messages feed
  if (elements.chatMessages) {
    elements.chatMessages.style.display = 'flex';
  }

  // Smoothly minimize hero stage when conversation begins
  const heroStage = document.getElementById('chatHeroStage');
  if (heroStage) {
    heroStage.style.display = 'none';
  }
  const promptGrid = document.getElementById('promptCardsGrid');
  if (promptGrid) {
    promptGrid.style.display = 'none';
  }

  appendMessageBubble('user', message);

  if (state.voiceCompanionMode) {
    const userSection = document.getElementById('vcUserSection');
    const userTranscriptDisplay = document.getElementById('vcUserTranscriptDisplay');
    const speechTime = document.getElementById('vcSpeechTime');
    if (userSection) userSection.style.display = 'flex';
    if (userTranscriptDisplay) {
      userTranscriptDisplay.classList.remove('placeholder');
      userTranscriptDisplay.textContent = message;
    }
    if (speechTime) speechTime.textContent = 'Voice Input Interpreted';

    // Show analyzing shimmer state on nuance breakdown while server processes
    const analysisBreakdown = document.getElementById('vcAnalysisBreakdown');
    if (analysisBreakdown) {
      analysisBreakdown.style.display = 'flex';
      const chipTone = document.getElementById('vcChipTone');
      const chipMood = document.getElementById('vcChipMood');
      const chipSomatic = document.getElementById('vcChipSomatic');
      const chipResonance = document.getElementById('vcChipResonance');
      const chipResource = document.getElementById('vcChipResource');
      if (chipTone) {
        chipTone.textContent = '🎙️ Tone: Analyzing vocal cadence...';
        chipTone.classList.add('analyzing-shimmer');
      }
      if (chipMood) {
        chipMood.textContent = '🌧️ Emotion: Interpreting semantic nuance...';
        chipMood.classList.add('analyzing-shimmer');
      }
      if (chipSomatic) {
        chipSomatic.textContent = '🌱 Somatic: Detecting stress markers...';
        chipSomatic.classList.add('analyzing-shimmer');
      }
      if (chipResonance) {
        chipResonance.textContent = '🤍 Mirror: Calibrating empathetic resonance...';
        chipResonance.classList.add('analyzing-shimmer');
      }
      if (chipResource) {
        chipResource.textContent = '📚 Resource: Grounding in clinical evidence...';
        chipResource.classList.add('analyzing-shimmer');
      }
    }
  }

  elements.chatInput.value = '';
  elements.chatInput.style.height = 'auto';

  // 1. Explicit Pre-Screening Crisis Check API
  try {
    const crisisRes = await fetch('/api/crisis-check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: message })
    });
    const crisisData = await crisisRes.json();
    if (crisisData.requires_crisis_flow) {
      openEmergencyModal();
      return; // Stop normal screening
    }
  } catch (e) { console.error('Crisis check failed', e); }

  // 2. Input Category Classification (Fallback Detection)
  try {
    const classRes = await fetch('/api/classify-user-input', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: message, conversation_context: [] })
    });
    const classData = await classRes.json();
    
    // Check if fallback emotion interview is required due to low confidence or unclear input
    if (classData.next_action === 'open_fallback_emotion_window') {
      const typingId = showTypingIndicator();
      setTimeout(() => {
        removeTypingIndicator(typingId);
        appendMessageBubble('mindbridge', classData.expected_chatbot_response);
        openEmotionInterviewModal(state.selectedLanguage, 'fallback');
      }, 1000);
      return; // Stop normal flow
    } else if (classData.next_action === 'offer_emotion_interview') {
      const typingId = showTypingIndicator();
      setTimeout(() => {
        removeTypingIndicator(typingId);
        appendMessageBubble('mindbridge', classData.expected_chatbot_response);
        openEmotionInterviewModal(state.selectedLanguage, 'normal');
      }, 1000);
      return; // Bypass LLM and immediately offer
    }
  } catch (e) { console.error('Classification failed', e); }

  const typingId = showTypingIndicator();

  // If a previous turn's request is still in flight when new user input arrives (barge-in),
  // immediately abort the previous request to pivot right to the current input!
  if (state.currentChatAbortController) {
    try { state.currentChatAbortController.abort(); } catch (e) {}
  }
  state.currentChatAbortController = new AbortController();

  // Zero-delay response: no artificial delay in voice companion mode or text chat!
  const isVoiceActive = Boolean(audioDetected || state.voiceCompanionMode);

  try {
    const fetchPromise = fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      signal: state.currentChatAbortController.signal,
      body: JSON.stringify({
        message: message,
        conversation_id: state.conversationId,
        user_id: state.userId,
        language: state.selectedLanguage,
        audio_detected: isVoiceActive,
        past_life_session_id: state.pastLifeActive ? state.pastLifeSessionId : null,
        past_life_mode: state.pastLifeMode || 'short'
      })
    });

    const response = await fetchPromise;
    const data = await response.json();
    removeTypingIndicator(typingId);

    if (data.conversation_id) {
      state.conversationId = data.conversation_id;
      localStorage.setItem('mb_conv_id', data.conversation_id);
    }

    // Past Life Reflection Session State Handling: Automatically Open Dedicated Window!
    if (data.past_life_active && data.past_life_session) {
      state.pastLifeActive = true;
      state.pastLifeSessionId = data.past_life_session.session_id || state.pastLifeSessionId;
      localStorage.setItem('mb_past_life_sid', state.pastLifeSessionId);

      if (data.past_life_completed) {
        state.pastLifeActive = false;
        state.pastLifeSessionId = null;
        localStorage.removeItem('mb_past_life_sid');
      } else if (!pastLifeStudioState.isOpen) {
        // Automatically pop open the dedicated Past Life Reflection Studio Modal Window!
        openPastLifeModal(data.past_life_session.language || state.selectedLanguage, state.pastLifeMode || 'short', data.past_life_session);
      }
    }

    // AUTOMATIC DYNAMIC LANGUAGE SWITCHING:
    // If user spoke in a different language, automatically switch companion language & voice!
    if (data.detected_language && data.detected_language !== state.selectedLanguage) {
      console.log(`[Auto-Language Switch] Mid-conversation switch: ${state.selectedLanguage} -> ${data.detected_language}`);
      state.selectedLanguage = data.detected_language;
      if (elements.languageSelect) {
        elements.languageSelect.value = data.detected_language;
      }
      syncVoiceCompanionModalLanguage();
      syncVoiceCompanionBarLanguage();
      if (state.recognition) {
        state.recognition.lang = data.detected_language;
      }
    }

    if (state.voiceCompanionMode) {
      setVoiceCompanionState('speaking');

      // Populate nuance breakdown chips with extracted semantic analysis
      const analysisBreakdown = document.getElementById('vcAnalysisBreakdown');
      if (analysisBreakdown) {
        analysisBreakdown.style.display = 'flex';
        const nuance = data.nuance_analysis || {};
        const chipTone = document.getElementById('vcChipTone');
        const chipMood = document.getElementById('vcChipMood');
        const chipSomatic = document.getElementById('vcChipSomatic');
        const chipResonance = document.getElementById('vcChipResonance');

        if (chipTone) {
          chipTone.textContent = nuance.vocal_tone || '🎙️ Vocal Nuance: Attuned Tone';
          chipTone.classList.remove('analyzing-shimmer');
        }
        if (chipMood) {
          chipMood.textContent = nuance.detected_emotion || '🌧️ Emotion: Expressed Feeling';
          chipMood.classList.remove('analyzing-shimmer');
        }
        if (chipSomatic) {
          chipSomatic.textContent = nuance.somatic_indicator || '🌱 Somatic: Somatic State';
          chipSomatic.classList.remove('analyzing-shimmer');
        }
        if (chipResonance) {
          if (data.voice_module_profile && data.voice_module_profile.speaking_rate_wpm) {
            chipResonance.textContent = `🎙️ Calibrated Voice: ${data.voice_module_profile.speaking_rate_wpm} WPM · 0.97 Pitch`;
          } else {
            chipResonance.textContent = nuance.calibrated_resonance || '🤍 Resonance: Empathetic Mirror';
          }
          chipResonance.classList.remove('analyzing-shimmer');
        }
        const chipResource = document.getElementById('vcChipResource');
        const resourceInsights = data.resource_insights || {};
        if (chipResource) {
          chipResource.textContent = resourceInsights.chip_badge || '📚 Resource: WHO Evidence Grounded';
          chipResource.classList.remove('analyzing-shimmer');
        }
      }

      // Populate Bot reflection inside Companion Modal
      const botSection = document.getElementById('vcBotSection');
      const botResponseDisplay = document.getElementById('vcBotResponseDisplay');
      const speakingIndicator = document.getElementById('vcSpeakingIndicator');
      if (botSection) botSection.style.display = 'flex';
      if (botResponseDisplay) botResponseDisplay.textContent = data.response;
      if (speakingIndicator) speakingIndicator.style.display = 'inline-flex';

      const activePersp = getActivePerspective(data);
      const bnCard = document.getElementById('vcPerspBnBtn');
      const enCard = document.getElementById('vcPerspEnBtn');
      if (bnCard) bnCard.classList.toggle('active-perspective', activePersp === 'bn');
      if (enCard) enCard.classList.toggle('active-perspective', activePersp === 'en');

      if (window.lucide) window.lucide.createIcons();
    }

    appendMessageBubble('mindbridge', data.response, data.guardrail_triggered, data.voice_perspectives);

    // If past life analysis completed, render the rich analysis card
    if (data.past_life_completed && data.past_life_session && data.past_life_session.analysis) {
      renderPastLifeAnalysisCard(data.past_life_session.analysis);
    }

    const activePersp = getActivePerspective(data);
    const isPastLifeActiveNow = (data.past_life_active && !data.past_life_completed) || pastLifeStudioState.isOpen;
    if (!isPastLifeActiveNow && (state.voiceCompanionMode || state.ttsEnabled)) {
      if (state.activeVoicePerspective && state.activeVoicePerspective !== 'auto') {
        runResponsePerspective(activePersp);
      } else {
        speakText(data.response);
      }
    }

    if (data.suggested_actions && data.suggested_actions.length > 0) {
      renderSuggestionChips(data.suggested_actions);
    }

    if (data.dimensions) {
      updateTriageWidget(data.dimensions);
    }

    if (data.risk_level === 'emergency') {
      openEmergencyModal();
    }

    // Emotion Interview Trigger Check:
    // If emotional input detected (moderate/high intensity or sensitive flags),
    // wait until speech finishes, then offer gentle invitation
    if (data.emotion_detection && data.emotion_detection.needs_emotion_interview && !emotionInterviewState.isOpen && !pastLifeStudioState.isOpen) {
      setTimeout(() => {
        showEmotionInviteModal(data.emotion_detection);
      }, 1800);
    }


  } catch (err) {
    if (err.name === 'AbortError') {
      console.debug('[Chat] Previous request aborted in favor of new user input (barge-in).');
      removeTypingIndicator(typingId);
      return;
    }
    console.error('Chat error:', err);
    removeTypingIndicator(typingId);
    appendMessageBubble('mindbridge', `
      <div style="display: flex; flex-direction: column; gap: 0.6rem;">
        <div style="display: flex; align-items: center; gap: 0.45rem; color: #fb7185; font-weight: 700; font-size: 0.88rem;">
          <i data-lucide="wifi-off" style="width: 15px; height: 15px;"></i>
          <span>Neural Connection Pause</span>
        </div>
        <div style="font-size: 0.9rem; color: #cbd5e1; line-height: 1.45;">I encountered a brief connection pause. Please know that your thoughts and feelings matter deeply, and I'm right here with you.</div>
        <div style="display: flex; gap: 0.5rem; margin-top: 0.2rem;">
          <button type="button" class="tool-pill-btn" onclick="submitChatMessage()" style="border-color: rgba(56,189,248,0.4); color: #38bdf8; background: rgba(14,165,233,0.12); cursor: pointer;">
            <i data-lucide="refresh-cw" style="width: 13px; height: 13px;"></i>
            <span>Reconnect & Retry</span>
          </button>
        </div>
      </div>
    `);
  }
}

function appendMessageBubble(sender, content, guardrail = null, perspectives = null) {
  const isBot = sender === 'mindbridge';
  const bubble = document.createElement('div');
  bubble.className = `message-bubble ${isBot ? 'bot-message' : 'user-message'} animate-fade-in`;

  const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  
  let formattedContent = content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/•\s*(.*?)(?=\n|$)/g, '<li>$1</li>')
    .replace(/\n\n/g, '<br><br>')
    .replace(/\n/g, '<br>');

  let guardrailHtml = '';
  if (guardrail === 'non_diagnostic_ethical_shield') {
    guardrailHtml = `<div class="guardrail-pill"><i data-lucide="shield-alert" class="inline-icon"></i> Non-Diagnostic Ethical Guardrail Active</div>`;
  } else if (guardrail === 'crisis_safety') {
    guardrailHtml = `<div class="guardrail-pill" style="color: var(--rose-sos); background: rgba(244,63,94,0.15); border-color: var(--rose-sos);"><i data-lucide="alert-triangle" class="inline-icon"></i> Immediate Safety Intervention Triggered</div>`;
  }

  let perspectiveBarHtml = '';
  if (isBot) {
    perspectiveBarHtml = `
      <div class="message-perspective-bar">
        <div class="mp-header">
          <span class="mp-tag"><i data-lucide="headphones"></i> Response Perspectives:</span>
        </div>
        <div class="mp-actions">
          <button type="button" class="mp-btn mp-btn-bn" data-persp="bn" title="Bengali Reflective Perspective (WhatsApp Audio 2026-09-13 at 8.46.54 PM.mpeg)">
            <i data-lucide="play"></i>
            <span>Bengali: সাফল্য ও আত্মবিশ্বাস</span>
          </button>
          <button type="button" class="mp-btn mp-btn-en" data-persp="en" title="English Grounded Courage (WhatsApp Audio 2026-09-13 at 8.48.14 PM.mpeg)">
            <i data-lucide="play"></i>
            <span>English: Overcoming Fear</span>
          </button>
        </div>
      </div>
    `;
  }

  bubble.innerHTML = `
    <div class="${isBot ? 'bot-avatar' : 'user-avatar'}">
      <i data-lucide="${isBot ? 'sparkles' : 'user'}"></i>
    </div>
    <div class="message-content-box">
      <div class="message-sender-name">${isBot ? 'MindBridge Companion' : 'You'}</div>
      <div class="message-text">${formattedContent}</div>
      ${guardrailHtml}
      ${perspectiveBarHtml}
      <div class="message-meta-row" style="display: flex; align-items: center; justify-content: space-between; margin-top: 0.35rem;">
        <div class="message-time">${timeStr}</div>
        ${isBot ? `<button type="button" class="btn-voice-replay" title="Listen to response voice module" style="background: none; border: 1px solid var(--border-glass); color: var(--text-muted); cursor: pointer; display: inline-flex; align-items: center; gap: 0.3rem; font-size: 0.74rem; padding: 2px 8px; border-radius: 999px; transition: all 0.2s;"><i data-lucide="volume-2" style="width: 12px; height: 12px;"></i> <span>Listen</span></button>` : ''}
      </div>
    </div>
  `;

  if (isBot) {
    const replayBtn = bubble.querySelector('.btn-voice-replay');
    if (replayBtn) {
      replayBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const persp = getActivePerspective();
        runResponsePerspective(persp);
      });
    }

    bubble.querySelectorAll('.mp-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const persp = btn.getAttribute('data-persp');
        runResponsePerspective(persp, btn);
      });
    });
  }

  elements.chatMessages.appendChild(bubble);
  elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;

  if (window.lucide) {
    window.lucide.createIcons();
  }
}

function showTypingIndicator() {
  const id = `typing-${Date.now()}`;
  const typingBubble = document.createElement('div');
  typingBubble.id = id;
  typingBubble.className = 'message-bubble bot-message animate-fade-in';
  typingBubble.innerHTML = `
    <div class="bot-avatar"><i data-lucide="sparkles"></i></div>
    <div class="message-content-box" style="padding: 0.85rem 1.25rem; background: rgba(13, 20, 36, 0.88); border-color: rgba(56, 189, 248, 0.3);">
      <div class="eva-loader-container">
        <div class="eva-loader-wrapper">
          <div class="loader">
            <div class="modelViewPort">
              <div class="eva">
                <div class="head">
                  <div class="eyeChamber">
                    <div class="eye"></div>
                    <div class="eye"></div>
                  </div>
                </div>
                <div class="body">
                  <div class="hand"></div>
                  <div class="hand"></div>
                  <div class="scannerThing"></div>
                  <div class="scannerOrigin"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="eva-loader-status-text" id="${id}-status">
          <i data-lucide="sparkles" style="width: 13px; height: 13px; color: var(--cyan-glow);"></i>
          <span>MindBridge AI Synthesizing Response...</span>
        </div>
        <div class="eva-loader-subtext" id="${id}-subtext">Calibrating empathetic reflection & non-diagnostic safety guardrails</div>
      </div>
    </div>
  `;
  elements.chatMessages.appendChild(typingBubble);
  elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
  if (window.lucide) window.lucide.createIcons();

  // If loading takes > 2.5s, update status to indicate deeper neural scanning
  setTimeout(() => {
    const statusElem = document.getElementById(`${id}-status`);
    const subtextElem = document.getElementById(`${id}-subtext`);
    if (statusElem && subtextElem) {
      statusElem.innerHTML = `<i data-lucide="activity" style="width: 13px; height: 13px; color: var(--teal-accent);"></i> <span>EVA Neural Scanner Analyzing Emotional State...</span>`;
      subtextElem.textContent = 'Harmonizing tone & co-regulating emotional frequencies...';
      if (window.lucide) window.lucide.createIcons();
    }
  }, 2500);

  return id;
}

function removeTypingIndicator(id) {
  const elem = document.getElementById(id);
  if (elem) elem.remove();
}

function renderSuggestionChips(chips) {
  elements.chipsList.innerHTML = '';
  chips.forEach(text => {
    const btn = document.createElement('button');
    btn.className = 'chip-btn';
    btn.setAttribute('data-text', text);
    
    let iconName = 'sparkles';
    if (text.toLowerCase().includes('doctor') || text.toLowerCase().includes('psychologist') || text.toLowerCase().includes('specialist')) {
      iconName = 'user-check';
    } else if (text.toLowerCase().includes('breath') || text.toLowerCase().includes('calm')) {
      iconName = 'wind';
    } else if (text.toLowerCase().includes('sleep')) {
      iconName = 'moon';
    } else if (text.toLowerCase().includes('stress') || text.toLowerCase().includes('burnout')) {
      iconName = 'flame';
    }

    btn.innerHTML = `<i data-lucide="${iconName}"></i> ${text}`;
    elements.chipsList.appendChild(btn);
  });

  if (window.lucide) window.lucide.createIcons();
}

function updateTriageWidget(dimensions) {
  if (elements.liveStressBar && elements.liveStressVal) {
    const stress = dimensions.stress_level || 45;
    elements.liveStressBar.style.width = `${stress}%`;
    let stressLabel = "Low Stress";
    if (stress > 70) stressLabel = `High Alert (${stress}%)`;
    else if (stress > 45) stressLabel = `Moderate (${stress}%)`;
    else stressLabel = `Calm & Grounded (${stress}%)`;
    elements.liveStressVal.textContent = stressLabel;
  }

  if (elements.liveMoodVal && dimensions.mood_label) {
    elements.liveMoodVal.textContent = dimensions.mood_label;
  }

  if (elements.liveEmotionTags && dimensions.detected_emotions) {
    elements.liveEmotionTags.innerHTML = '';
    dimensions.detected_emotions.forEach(e => {
      const tag = document.createElement('span');
      tag.className = 'emotion-tag';
      tag.textContent = e.replace('stressor:', '');
      elements.liveEmotionTags.appendChild(tag);
    });
  }
}

// ==========================================================================
// ==========================================================================
// TWO-WAY CONTINUOUS VOICE COMPANION MODE & SPEECH RECOGNITION (STT)
// ==========================================================================

function setVoiceCompanionState(statusKey, customText = '') {
  // Update in-capsule console bar
  const bar = document.getElementById('voiceCompanionBar');
  const dot = document.getElementById('vcPulseDot') || document.querySelector('.vc-pulse-dot');
  const liveState = document.getElementById('vcLiveState');
  const wave = document.getElementById('vcSoundwave');

  // Update dedicated Two-Way Companion Modal
  const modalDot = document.getElementById('vcModalPulseDot');
  const modalTitle = document.getElementById('vcModalStateTitle');
  const modalDesc = document.getElementById('vcModalStateDesc');
  const modalWave = document.getElementById('vcModalSoundwave');

  const currentDict = I18N_DICTIONARY[state.selectedLanguage] || I18N_DICTIONARY['en-US'];

  if (dot) dot.className = 'vc-pulse-dot';
  if (modalDot) modalDot.className = 'vc-pulse-dot-modal';

  if (statusKey === 'listening') {
    if (dot) dot.classList.add('listening');
    if (modalDot) modalDot.classList.add('listening');
    if (liveState) liveState.textContent = customText || currentDict.voice_companion_listening || 'Listening... speak naturally';
    if (modalTitle) modalTitle.textContent = 'Listening...';
    if (modalDesc) modalDesc.textContent = customText || 'Speak freely. Voice companion remains active until you exit.';
    if (wave) wave.style.display = 'flex';
    if (modalWave) modalWave.style.display = 'flex';
    const speakingIndicator = document.getElementById('vcSpeakingIndicator');
    if (speakingIndicator) speakingIndicator.style.display = 'none';
  } else if (statusKey === 'analyzing') {
    if (dot) dot.classList.add('analyzing');
    if (modalDot) modalDot.classList.add('analyzing');
    if (liveState) liveState.textContent = customText || currentDict.voice_companion_analyzing || 'Reflecting on your thoughts...';
    if (modalTitle) modalTitle.textContent = 'Analyzing Voice Nuances & Semantics...';
    if (modalDesc) modalDesc.textContent = customText || 'MindBridge is interpreting vocal cadence and emotional depth.';
    if (wave) wave.style.display = 'none';
    if (modalWave) modalWave.style.display = 'none';
    const speakingIndicator = document.getElementById('vcSpeakingIndicator');
    if (speakingIndicator) speakingIndicator.style.display = 'none';
  } else if (statusKey === 'speaking') {
    if (dot) dot.classList.add('speaking');
    if (modalDot) modalDot.classList.add('speaking');
    if (liveState) liveState.textContent = customText || currentDict.voice_companion_speaking || 'MindBridge is speaking...';
    if (modalTitle) modalTitle.textContent = 'MindBridge is speaking...';
    if (modalDesc) modalDesc.textContent = customText || 'Listening will resume automatically the moment speech concludes.';
    if (wave) wave.style.display = 'flex';
    if (modalWave) modalWave.style.display = 'flex';
    const speakingIndicator = document.getElementById('vcSpeakingIndicator');
    if (speakingIndicator) speakingIndicator.style.display = 'inline-flex';
  } else if (statusKey === 'ready') {
    if (liveState) liveState.textContent = customText || 'Ready... speak anytime';
    if (modalTitle) modalTitle.textContent = 'Ready...';
    if (modalDesc) modalDesc.textContent = customText || 'Waiting for your voice. Speak freely anytime.';
    if (wave) wave.style.display = 'none';
    if (modalWave) modalWave.style.display = 'none';
    const speakingIndicator = document.getElementById('vcSpeakingIndicator');
    if (speakingIndicator) speakingIndicator.style.display = 'none';
  }
}

function syncVoiceCompanionModalLanguage() {
  const langText = document.getElementById('vcModalLangText');
  if (langText) {
    const langMap = {
      'en-US': 'English (US)',
      'hi-IN': 'Hindi (हिन्दी)',
      'hinglish': 'Hinglish (भारत)',
      'es-ES': 'Español',
      'pt-BR': 'Português',
      'bn-IN': 'বাংলা (Bengali)'
    };
    langText.textContent = langMap[state.selectedLanguage] || state.selectedLanguage || 'English';
  }

  // Synchronize interactive language pills
  const activeLang = (state.vcSelectedLang === 'auto') ? 'auto' : state.selectedLanguage;
  document.querySelectorAll('.vc-lang-pill').forEach(pill => {
    const pillLang = pill.getAttribute('data-vc-lang');
    if (pillLang === activeLang || (state.vcSelectedLang === 'auto' && pillLang === 'auto')) {
      pill.classList.add('active');
    } else {
      pill.classList.remove('active');
    }
  });
}

function flashInterruptionAlert() {
  const banner = document.getElementById('vcInterruptionBanner');
  const speechTime = document.getElementById('vcSpeechTime');
  if (banner) {
    banner.style.display = 'inline-flex';
    if (state.interruptionBannerTimer) clearTimeout(state.interruptionBannerTimer);
    state.interruptionBannerTimer = setTimeout(() => {
      if (banner) banner.style.display = 'none';
    }, 2800);
  }
  if (speechTime) {
    speechTime.textContent = '⚡ Interrupted: Attuned to your words';
  }
  const speakingIndicator = document.getElementById('vcSpeakingIndicator');
  if (speakingIndicator) speakingIndicator.style.display = 'none';
}

function getEffectiveRecognitionLang() {
  if (state.vcSelectedLang && state.vcSelectedLang !== 'auto') {
    return state.vcSelectedLang;
  }
  return state.selectedLanguage || navigator.language || 'en-US';
}

// ==========================================================================
// REAL-TIME AUDIO BUFFERING, VAD & DIRECT SERVER TRANSCRIBE
// ==========================================================================

let vcAudioContext = null;
let vcScriptProcessor = null;
let vcMediaStreamSource = null;
let vcAudioBuffers = [];
let vcIsSpeaking = false;
let vcSilenceStartTime = 0;
let vcTranscribing = false;

function encodeWAVFromBuffers(buffers, inputSampleRate = 44100) {
  let totalLength = 0;
  for (const b of buffers) totalLength += b.length;
  if (totalLength === 0) return new Blob([], { type: 'audio/wav' });

  const merged = new Float32Array(totalLength);
  let offset = 0;
  for (const b of buffers) {
    merged.set(b, offset);
    offset += b.length;
  }

  // Find peak amplitude for intelligent Auto-Gain Normalization
  let peak = 0;
  for (let i = 0; i < totalLength; i++) {
    const abs = Math.abs(merged[i]);
    if (abs > peak) peak = abs;
  }

  // Boost quiet microphone signal up to 15x so speech recognition engines hear crystal-clear audio
  const gain = (peak > 0.00005 && peak < 0.45) ? Math.min(15.0, 0.75 / peak) : 1.0;

  const sampleRate = inputSampleRate || 44100;
  // 16-bit Mono PCM WAV
  const buffer = new ArrayBuffer(44 + totalLength * 2);
  const view = new DataView(buffer);

  function writeString(view, offset, string) {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  }

  writeString(view, 0, 'RIFF');
  view.setUint32(4, 36 + totalLength * 2, true);
  writeString(view, 8, 'WAVE');
  writeString(view, 12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true); // PCM format
  view.setUint16(22, 1, true); // 1 channel (mono)
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true); // block align
  view.setUint16(34, 16, true); // bits per sample
  writeString(view, 36, 'data');
  view.setUint32(40, totalLength * 2, true);

  let p = 44;
  for (let i = 0; i < totalLength; i++, p += 2) {
    const s = Math.max(-1, Math.min(1, merged[i] * gain));
    view.setInt16(p, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
  }

  return new Blob([view], { type: 'audio/wav' });
}

function startAudioCaptureVAD(stream) {
  try {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) return;

    if (!vcAudioContext || vcAudioContext.state === 'closed') {
      vcAudioContext = new AudioContextClass();
    }
    if (vcAudioContext.state === 'suspended') {
      vcAudioContext.resume();
    }

    if (vcMediaStreamSource) {
      try { vcMediaStreamSource.disconnect(); } catch (e) {}
    }

    vcMediaStreamSource = vcAudioContext.createMediaStreamSource(stream);

    // 1. AnalyserNode for live visualizer meter and soundwave bars
    const analyser = vcAudioContext.createAnalyser();
    analyser.fftSize = 64;
    vcMediaStreamSource.connect(analyser);

    const dataArray = new Uint8Array(analyser.frequencyBinCount);
    const vadBars = document.querySelectorAll('.vc-vad-bar');
    const modalWaveBars = document.querySelectorAll('#vcModalSoundwave span');

    function updateMeter() {
      if (!state.voiceCompanionMode || state.userExplicitlyStoppedVoice) return;
      analyser.getByteFrequencyData(dataArray);
      let sum = 0;
      for (let i = 0; i < dataArray.length; i++) sum += dataArray[i];
      const avg = sum / dataArray.length;

      if (vadBars.length > 0) {
        vadBars.forEach((bar, idx) => {
          const h = Math.max(3, Math.min(14, (avg / 255) * 16 + (idx % 2) * 2));
          bar.style.height = `${h}px`;
          bar.style.background = avg > 8 ? '#38bdf8' : 'rgba(56, 189, 248, 0.35)';
        });
      }
      if (modalWaveBars.length > 0 && avg > 10) {
        modalWaveBars.forEach((span, idx) => {
          const scale = Math.max(0.3, Math.min(2.0, (avg / 60) * (0.8 + (idx % 4) * 0.25)));
          span.style.transform = `scaleY(${scale})`;
        });
      }
      requestAnimationFrame(updateMeter);
    }
    requestAnimationFrame(updateMeter);

    // 2. Continuous Audio Buffer & Real-Time VAD Processor
    // Runs in ALL browsers (Brave, Chrome, Edge, Safari) with zero hardware contention
    if (vcScriptProcessor) {
      try { vcScriptProcessor.disconnect(); } catch (e) {}
    }
    vcAudioBuffers = [];
    vcIsSpeaking = false;
    vcSilenceStartTime = 0;
    vcTranscribing = false;

    vcScriptProcessor = vcAudioContext.createScriptProcessor(4096, 1, 1);
    const vadThreshold = 0.009; // Sensitively calibrated for natural voice

    vcScriptProcessor.onaudioprocess = (e) => {
      if (!state.voiceCompanionMode || state.userExplicitlyStoppedVoice || vcTranscribing) {
        return;
      }

      const input = e.inputBuffer.getChannelData(0);
      let sum = 0;
      for (let i = 0; i < input.length; i++) sum += input[i] * input[i];
      const rms = Math.sqrt(sum / input.length);

      // BARGE-IN INTERRUPTION:
      // If user speaks while AI is currently outputting voice, halt AI voice immediately!
      // Grace period: first 1200ms after TTS starts are protected from self-interruption.
      // Cooldown: 1800ms between successive barge-ins to prevent rapid-fire triggers.
      const now = Date.now();
      const withinGrace = (now - ttsStartedAt) < BARGE_IN_GRACE_MS;
      const withinCooldown = (now - lastBargeInAt) < BARGE_IN_COOLDOWN_MS;
      if (rms > 0.080 && isSpeakingSequence && !withinGrace && !withinCooldown) {
        console.debug('[VAD Barge-In] User voice activity detected during AI output! Halting speech immediately.');
        lastBargeInAt = now;
        stopSpeaking(true);
        if (state.currentChatAbortController) {
          try { state.currentChatAbortController.abort(); } catch (err) {}
        }
        const banner = document.getElementById('vcInterruptionBanner');
        if (banner) {
          banner.style.display = 'inline-flex';
          setTimeout(() => { if (banner) banner.style.display = 'none'; }, 2400);
        }
      }

      // Keep a pre-roll buffer of ~700ms (approx 8 chunks at 4096 samples) to avoid clipping first words
      if (!vcIsSpeaking && rms <= vadThreshold) {
        vcAudioBuffers.push(new Float32Array(input));
        if (vcAudioBuffers.length > 8) vcAudioBuffers.shift();
      }

      if (rms > vadThreshold) {
        if (!vcIsSpeaking) {
          vcIsSpeaking = true;
          vcSilenceStartTime = 0;
          const speechTime = document.getElementById('vcSpeechTime');
          if (speechTime) speechTime.textContent = '🎙️ Hearing your voice...';
          const userTranscriptDisplay = document.getElementById('vcUserTranscriptDisplay');
          if (userTranscriptDisplay && userTranscriptDisplay.classList.contains('placeholder')) {
            userTranscriptDisplay.classList.remove('placeholder');
            userTranscriptDisplay.textContent = 'Hearing your voice... (Speak freely)';
          }
        }
        vcAudioBuffers.push(new Float32Array(input));
        // Allow up to ~3 minutes of continuous speech buffering
        if (vcAudioBuffers.length > 2000) vcAudioBuffers.shift();
      } else {
        if (vcIsSpeaking) {
          vcAudioBuffers.push(new Float32Array(input));
          if (vcSilenceStartTime === 0) {
            vcSilenceStartTime = Date.now();
          } else if (Date.now() - vcSilenceStartTime > 2000) { // 2000ms timeout for natural pauses
            // Silence detected: user completed utterance
            vcIsSpeaking = false;
            vcSilenceStartTime = 0;

            // Check if Web Speech API captured text (standard Chrome/Edge)
            const webSpeechText = (currentSpokenAccumulator || elements.chatInput.value || '').trim();
            const hasWebSpeech = webSpeechText &&
              !webSpeechText.includes('Listening for your voice') &&
              !webSpeechText.includes('Hearing your voice');

            if (hasWebSpeech) {
              console.debug('[Turn-Taking] Handled by Web Speech API. Forcing submission due to VAD silence!', webSpeechText);
              vcAudioBuffers = [];
              
              // Instantly submit using VAD's snappy silence detection instead of waiting for Chrome's slow finalize
              clearTimeout(vcSpeechSubmitTimer);
              currentSpokenAccumulator = '';
              elements.chatInput.value = webSpeechText;
              setVoiceCompanionState('analyzing', 'Interpreting voice nuance...');
              const txRow = document.getElementById('vcTranscriptRow');
              if (txRow) txRow.style.display = 'none';
              
              // Force stop recognition to prevent delayed ghost-triggers
              if (state.recognition && state.isRecognitionActive) {
                try { state.recognition.abort(); } catch(e) {}
              }
              
              submitChatMessage(true);
              
            } else if ((!state.recognition || state.webSpeechDisabled) && vcAudioBuffers.length >= 2) {
              // Only trigger server transcription if Web Speech is explicitly disabled/unsupported.
              // Otherwise, we trust Web Speech. If it heard nothing, it was just background noise, so discard it!
              console.debug('[Turn-Taking] Web Speech blocked/unsupported. Automatically transcribing via server engine!');
              triggerAudioTranscribe();
            } else {
              console.debug('[Turn-Taking] VAD detected noise but Web Speech ignored it. Discarding buffer to prevent hallucinations.');
              vcAudioBuffers = [];
            }
          }
        }
      }
    };

    // Connect processor through a zero-gain node to mute speaker output (avoids echo and WASAPI contention)
    const muteNode = vcAudioContext.createGain();
    muteNode.gain.value = 0;
    vcMediaStreamSource.connect(vcScriptProcessor);
    vcScriptProcessor.connect(muteNode);
    muteNode.connect(vcAudioContext.destination);

  } catch (err) {
    console.debug('VAD AudioContext setup note:', err);
  }
}

function stopAudioCaptureVAD() {
  if (vcScriptProcessor) {
    try { vcScriptProcessor.disconnect(); } catch (e) {}
    vcScriptProcessor = null;
  }
  if (vcMediaStreamSource) {
    try { vcMediaStreamSource.disconnect(); } catch (e) {}
    vcMediaStreamSource = null;
  }
  if (vcAudioContext && vcAudioContext.state !== 'closed') {
    try { vcAudioContext.close(); } catch (e) {}
    vcAudioContext = null;
  }
  vcAudioBuffers = [];
  vcIsSpeaking = false;
  vcSilenceStartTime = 0;
  vcTranscribing = false;
}

async function triggerAudioTranscribe() {
  if (vcTranscribing || vcAudioBuffers.length < 2) {
    vcAudioBuffers = [];
    return;
  }

  vcTranscribing = true;
  setVoiceCompanionState('analyzing', 'Interpreting voice nuance...');
  const speechTime = document.getElementById('vcSpeechTime');
  if (speechTime) speechTime.textContent = '⚡ Transcribing voice...';
  const userTranscriptDisplay = document.getElementById('vcUserTranscriptDisplay');
  if (userTranscriptDisplay) {
    userTranscriptDisplay.classList.remove('placeholder');
    userTranscriptDisplay.textContent = 'Interpreting what you said...';
  }

  try {
    const sampleRate = vcAudioContext ? vcAudioContext.sampleRate : 44100;
    const buffersSnapshot = vcAudioBuffers.slice(); // snapshot before clearing
    vcAudioBuffers = [];

    const effectiveLang = state.vcSelectedLang || state.selectedLanguage || 'auto';

    // ====================================================================
    // PRIMARY ENGINE: Voicebox Transcriber (Jamie Pine Architecture STT)
    // Uses /api/voicebox/transcribe with Whisper + NeMo dual-ASR failover
    // ====================================================================
    let recognized = null;
    let engineUsed = '';
    let failoverTriggered = false;
    let detectedLanguage = '';

    if (window.VoiceboxTranscriber && !window.VoiceboxTranscriber.isTranscribing) {
      try {
        const vbResult = await window.VoiceboxTranscriber.transcribe(buffersSnapshot, sampleRate, effectiveLang);
        if (vbResult && vbResult.text && vbResult.text.trim()) {
          recognized = vbResult.text.trim();
          engineUsed = vbResult.engine || 'Voicebox Neural STT';
          detectedLanguage = vbResult.language || '';
          console.debug('[Voicebox STT] Primary transcription success:', recognized);
        }
      } catch (vbErr) {
        console.debug('[Voicebox STT] Primary engine error, falling back:', vbErr);
      }
    }

    // ====================================================================
    // FALLBACK ENGINE: Legacy /api/voice/transcribe endpoint
    // Activates only if Voicebox primary did not return a result
    // ====================================================================
    if (!recognized) {
      try {
        const wavBlob = encodeWAVFromBuffers(buffersSnapshot, sampleRate);
        const formData = new FormData();
        formData.append('audio', wavBlob, 'user_speech.wav');

        const res = await fetch(`/api/voice/transcribe?language=${encodeURIComponent(effectiveLang)}`, {
          method: 'POST',
          body: formData
        });

        const data = await res.json();
        if (data.status === 'success' && data.text && data.text.trim()) {
          recognized = data.text.trim();
          engineUsed = data.engine_used || 'Whisper Large v3 Turbo';
          failoverTriggered = data.failover_triggered || false;
          detectedLanguage = data.detected_language || '';
          console.debug('[Fallback STT] Secondary transcription success:', recognized);
        }
      } catch (fallbackErr) {
        console.debug('[Fallback STT] Secondary engine error:', fallbackErr);
      }
    }

    // ====================================================================
    // PROCESS TRANSCRIPTION RESULT
    // ====================================================================
    if (recognized) {
      elements.chatInput.value = recognized;

      // Dynamically update Dual ASR Engine Badge & Failover Indicator
      const asrBadge = document.getElementById('vcAsrEngineBadge');
      const asrName = document.getElementById('vcAsrEngineName');
      const asrSubtext = document.getElementById('vcAsrSubtext');
      if (asrBadge && asrName) {
        if (failoverTriggered) {
          asrBadge.classList.add('failover-active');
          asrName.textContent = engineUsed || 'NVIDIA NeMo Canary / Parakeet';
          if (asrSubtext) asrSubtext.textContent = 'Auto-Failover Active';
          const banner = document.getElementById('vcInterruptionBanner');
          const bannerText = document.getElementById('vcInterruptionText');
          if (banner && bannerText) {
            bannerText.textContent = `⚡ Auto-Failover: ${engineUsed || 'NVIDIA NeMo Speech'} successfully transcribed!`;
            banner.style.display = 'inline-flex';
            setTimeout(() => { if (banner) banner.style.display = 'none'; }, 3200);
          }
        } else {
          asrBadge.classList.remove('failover-active');
          asrName.textContent = engineUsed || 'Voicebox Neural STT';
          if (asrSubtext) asrSubtext.textContent = 'Primary ASR Active';
        }
      }

      const userSection = document.getElementById('vcUserSection');
      if (userSection) userSection.style.display = 'flex';
      if (userTranscriptDisplay) {
        userTranscriptDisplay.classList.remove('placeholder');
        userTranscriptDisplay.textContent = recognized;
      }
      if (speechTime) speechTime.textContent = 'Voice Interpreted';

      // Auto-switch language if detected
      if (detectedLanguage && detectedLanguage !== state.selectedLanguage) {
        state.selectedLanguage = detectedLanguage;
        syncVoiceCompanionModalLanguage();
        syncVoiceCompanionBarLanguage();
      }

      // Immediately inform state & submit
      setVoiceCompanionState('analyzing', 'MindBridge is reflecting on your thoughts...');
      submitChatMessage(true);
    } else {
      if (speechTime) speechTime.textContent = '● Live Listening · Hands-Free';
      setVoiceCompanionState('listening');
      if (userTranscriptDisplay && userTranscriptDisplay.textContent.includes('Interpreting what you said')) {
        userTranscriptDisplay.classList.add('placeholder');
        userTranscriptDisplay.textContent = 'Listening for your voice... Speak naturally in any language, MindBridge is attuned to you.';
      }
    }
  } catch (err) {
    console.debug('Transcribe error:', err);
    if (speechTime) speechTime.textContent = '● Live Listening · Hands-Free';
  } finally {
    vcTranscribing = false;
  }
}


async function fetchVoiceEnginesStatus() {
  try {
    const res = await fetch('/api/voice/engines/status');
    const data = await res.json();
    if (data.status === 'success' && data.engines) {
      const p = data.engines.primary_engine;
      const s = data.engines.secondary_engine;
      const f = data.engines.failover_system;
      const asrName = document.getElementById('vcAsrEngineName');
      const asrSubtext = document.getElementById('vcAsrSubtext');
      const asrBadge = document.getElementById('vcAsrEngineBadge');
      if (asrName && asrSubtext) {
        if (f.total_failovers_triggered > 0 && f.last_engine_used === s.name) {
          asrName.textContent = s.name;
          asrSubtext.textContent = 'Auto-Failover Active';
          if (asrBadge) asrBadge.classList.add('failover-active');
        } else {
          asrName.textContent = p.name;
          asrSubtext.textContent = 'Auto-Failover Ready';
          if (asrBadge) asrBadge.classList.remove('failover-active');
        }
      }
    }
  } catch (e) {
    console.debug('Voice engines status note:', e);
  }
}

function startVoiceCompanionMode() {
  state.voiceCompanionMode = true;
  state.userExplicitlyStoppedVoice = false;
  state.ttsEnabled = true;
  state.consecutiveSilenceCount = 0;
  state.webSpeechDisabled = false;

  // Resume audio context if suspended by browser autoplay policy
  if (vcAudioContext && vcAudioContext.state === 'suspended') {
    vcAudioContext.resume().catch(() => {});
  }

  // Check Dual ASR Engine health & failover readiness
  fetchVoiceEnginesStatus();

  // 1. Open the dedicated Two-Way Voice Companion Modal
  const modal = document.getElementById('voiceCompanionModal');
  if (modal) {
    modal.style.display = 'flex';
    modal.classList.add('active', 'open');
    
    // Ensure User Section is ready with friendly placeholder
    const userSection = document.getElementById('vcUserSection');
    const userTranscriptDisplay = document.getElementById('vcUserTranscriptDisplay');
    const speechTime = document.getElementById('vcSpeechTime');
    if (userSection) userSection.style.display = 'flex';
    if (userTranscriptDisplay && (!userTranscriptDisplay.textContent || userTranscriptDisplay.classList.contains('placeholder'))) {
      userTranscriptDisplay.classList.add('placeholder');
      userTranscriptDisplay.textContent = 'Listening for your voice... Speak naturally in any language, MindBridge is attuned to you.';
    }
    if (speechTime) speechTime.textContent = '● Live Listening · Hands-Free';

    // Hide interruption banner initially
    const banner = document.getElementById('vcInterruptionBanner');
    if (banner) banner.style.display = 'none';

    if (window.lucide) window.lucide.createIcons();
  }

  // 2. Open the console HUD bar
  const bar = document.getElementById('voiceCompanionBar');
  if (bar) {
    bar.style.display = 'flex';
    syncVoiceCompanionBarLanguage();
  }

  // 3. Highlight capsule and buttons
  const capsule = document.querySelector('.console-inner-capsule');
  if (capsule) {
    capsule.classList.add('voice-companion-mode-active');
  }

  const micBtn = document.getElementById('micBtn');
  if (micBtn) {
    micBtn.classList.add('voice-companion-active');
  }

  if (elements.ttsToggleBtn) {
    elements.ttsToggleBtn.classList.add('active');
    if (elements.ttsLabel) elements.ttsLabel.textContent = 'Voice: ON';
  }

  syncVoiceCompanionModalLanguage();
  setVoiceCompanionState('listening');

  // Passive visualizer capture (non-blocking for Web Speech API)
  if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } }).then((stream) => {
      state.micStream = stream;
      startAudioCaptureVAD(stream);
    }).catch((err) => {
      console.debug('Microphone access note:', err);
    });
  }

  // Start continuous listening loop IMMEDIATELY upon opening (Hands-Free!)
  startListening();
}

function stopVoiceCompanionMode(byUser = true) {
  state.voiceCompanionMode = false;
  state.userExplicitlyStoppedVoice = byUser;
  state.consecutiveSilenceCount = 0;

  stopAudioCaptureVAD();

  if (state.voiceRestartTimer) {
    clearTimeout(state.voiceRestartTimer);
    state.voiceRestartTimer = null;
  }
  if (state.ttsWatchdogTimer) {
    clearTimeout(state.ttsWatchdogTimer);
    state.ttsWatchdogTimer = null;
  }

  // Close the Two-Way Voice Companion Modal
  const modal = document.getElementById('voiceCompanionModal');
  if (modal) {
    modal.style.display = 'none';
    modal.classList.remove('active', 'open');
  }

  // Close the console HUD bar
  const bar = document.getElementById('voiceCompanionBar');
  if (bar) {
    bar.style.display = 'none';
  }

  const capsule = document.querySelector('.console-inner-capsule');
  if (capsule) {
    capsule.classList.remove('voice-companion-mode-active');
  }

  const txRow = document.getElementById('vcTranscriptRow');
  if (txRow) txRow.style.display = 'none';

  const micBtn = document.getElementById('micBtn');
  if (micBtn) {
    micBtn.classList.remove('voice-companion-active', 'recording');
  }

  if (state.recognition) {
    try {
      state.recognition.stop();
    } catch (e) {}
  }

  if (state.micStream) {
    try {
      state.micStream.getTracks().forEach(t => t.stop());
      state.micStream = null;
    } catch (e) {}
  }

  stopRecording();
  stopSpeaking();
}

let lastVoiceCompanionToggleTime = 0;

function toggleVoiceCompanionMode(e) {
  if (e) {
    try { e.preventDefault(); e.stopPropagation(); } catch (err) {}
  }
  const now = Date.now();
  if (now - lastVoiceCompanionToggleTime < 450) {
    return;
  }
  lastVoiceCompanionToggleTime = now;

  if (state.voiceCompanionMode) {
    stopVoiceCompanionMode(true);
  } else {
    startVoiceCompanionMode();
  }
}

window.toggleVoiceCompanionMode = toggleVoiceCompanionMode;
window.startVoiceCompanionMode = startVoiceCompanionMode;
window.stopVoiceCompanionMode = stopVoiceCompanionMode;

function syncVoiceCompanionBarLanguage() {
  const t = I18N_DICTIONARY[state.selectedLanguage] || I18N_DICTIONARY['en-US'];
  const modeTitle = document.getElementById('vcModeTitle');
  const liveState = document.getElementById('vcLiveState');
  const exitLabel = document.getElementById('vcExitLabel');

  if (modeTitle) modeTitle.textContent = t.voice_companion_active || 'Two-Way Voice Companion Active';
  if (liveState && !isSpeakingSequence) liveState.textContent = t.voice_companion_listening || 'Listening... speak naturally';
  if (exitLabel) exitLabel.textContent = t.voice_companion_exit || 'Exit Voice';
}

let vcSpeechSubmitTimer = null;
let currentSpokenAccumulator = '';

function scheduleListeningRestart(delay = 60) {
  if (!state.voiceCompanionMode || state.userExplicitlyStoppedVoice) return;
  if (state.voiceRestartTimer) {
    clearTimeout(state.voiceRestartTimer);
  }
  state.voiceRestartTimer = setTimeout(() => {
    if (state.voiceCompanionMode && !state.userExplicitlyStoppedVoice && !state.isRecognitionActive && !state.isRecognitionStarting) {
      startListening();
    }
  }, delay);
}

function startListening() {
  if (!state.voiceCompanionMode || state.userExplicitlyStoppedVoice) return;
  if (state.webSpeechDisabled) return;
  if (state.isRecognitionActive || state.isRecognitionStarting) return;

  if (state.voiceRestartTimer) {
    clearTimeout(state.voiceRestartTimer);
    state.voiceRestartTimer = null;
  }

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!state.recognition && SpeechRecognition) {
    setupSpeechRecognitionInstance(SpeechRecognition);
  }

  if (state.recognition) {
    try {
      state.isRecognitionStarting = true;
      const targetLang = getEffectiveRecognitionLang();
      state.recognition.lang = targetLang;
      state.recognition.start();
      if (!isSpeakingSequence) {
        setVoiceCompanionState('listening', 'Microphone active · Listening for your voice');
      }
    } catch (err) {
      state.isRecognitionStarting = false;
      if (err.name === 'InvalidStateError' || (err.message && err.message.includes('already started'))) {
        state.isRecognitionActive = true;
      } else {
        console.debug('Recognition start note:', err);
        scheduleListeningRestart(100);
      }
    }
  } else {
    setVoiceCompanionState('listening', 'Microphone active · Hands-free companion open');
  }
}

function setupSpeechRecognitionInstance(SpeechRecognition) {
  state.recognition = new SpeechRecognition();
  state.recognition.continuous = true;
  state.recognition.interimResults = true;
  state.recognition.maxAlternatives = 1;
  state.recognition.lang = getEffectiveRecognitionLang();

  state.recognition.onstart = () => {
    state.isRecording = true;
    state.isRecognitionActive = true;
    state.isRecognitionStarting = false;
    currentSpokenAccumulator = '';
    const micBtn = document.getElementById('micBtn');
    if (micBtn) micBtn.classList.add('recording');
    if (elements.audioVisualizer) elements.audioVisualizer.style.display = 'flex';
    if (!isSpeakingSequence) {
      setVoiceCompanionState('listening', 'Microphone active · Listening for your voice');
      const speechTime = document.getElementById('vcSpeechTime');
      if (speechTime) speechTime.textContent = '● Live Listening · Hands-Free';
    }

    const audio = getAudioElement();
    if (state.soundPlaying && !audio.paused && state.soundscapeActive !== 'off') {
      state.wasPlayingBeforeRecording = true;
      cancelFade();
      audio.pause();
      audio.volume = 0;
    } else {
      state.wasPlayingBeforeRecording = false;
    }
  };

  state.recognition.onspeechstart = () => {
    // BARGE-IN INTERRUPTION:
    // If AI is currently speaking, user started vocalizing -> CUT OFF voice output!
    // Respect grace period to avoid self-interruption from TTS audio.
    const now = Date.now();
    const withinGrace = (now - ttsStartedAt) < BARGE_IN_GRACE_MS;
    const withinCooldown = (now - lastBargeInAt) < BARGE_IN_COOLDOWN_MS;
    if (isSpeakingSequence && !withinGrace && !withinCooldown) {
      console.debug('[Barge-In] Speech start detected during AI output! Halting voice.');
      lastBargeInAt = now;
      stopSpeaking(true);
      if (state.currentChatAbortController) {
        try { state.currentChatAbortController.abort(); } catch (e) {}
      }
    }
    const wave = document.getElementById('vcModalSoundwave');
    if (wave) wave.classList.add('active');
    const speechTime = document.getElementById('vcSpeechTime');
    if (speechTime && !speechTime.textContent.includes('Interrupted')) {
      speechTime.textContent = '🎙️ Hearing your voice...';
    }
  };

  state.recognition.onsoundstart = () => {
    const now = Date.now();
    const withinGrace = (now - ttsStartedAt) < BARGE_IN_GRACE_MS;
    const withinCooldown = (now - lastBargeInAt) < BARGE_IN_COOLDOWN_MS;
    if (isSpeakingSequence && !withinGrace && !withinCooldown) {
      lastBargeInAt = now;
      stopSpeaking(true);
      if (state.currentChatAbortController) {
        try { state.currentChatAbortController.abort(); } catch (e) {}
      }
    }
  };

  state.recognition.onspeechend = () => {
    const wave = document.getElementById('vcModalSoundwave');
    if (wave) wave.classList.remove('active');
  };

  state.recognition.onresult = (event) => {
    // BARGE-IN INTERRUPTION: If AI is outputting voice and user speaks,
    // halt voice output and listen to the user right now!
    // Respect grace period to avoid self-interruption.
    const bargeNow = Date.now();
    const bargeWithinGrace = (bargeNow - ttsStartedAt) < BARGE_IN_GRACE_MS;
    const bargeWithinCooldown = (bargeNow - lastBargeInAt) < BARGE_IN_COOLDOWN_MS;
    if (isSpeakingSequence && !bargeWithinGrace && !bargeWithinCooldown) {
      console.debug('[Barge-In] User words detected! Halting TTS output immediately.');
      lastBargeInAt = bargeNow;
      stopSpeaking(true);
      if (state.currentChatAbortController) {
        try { state.currentChatAbortController.abort(); } catch (e) {}
      }
    }

    let interimTranscript = '';
    let finalTranscript = '';
    for (let i = event.resultIndex; i < event.results.length; ++i) {
      const res = event.results[i];
      if (res.isFinal) {
        finalTranscript += res[0].transcript;
      } else {
        interimTranscript += res[0].transcript;
      }
    }

    const liveWords = (finalTranscript || interimTranscript).trim();
    if (liveWords) {
      if (finalTranscript) {
        currentSpokenAccumulator = (currentSpokenAccumulator + ' ' + finalTranscript).trim();
      }
      const activeDisplay = currentSpokenAccumulator || liveWords;
      elements.chatInput.value = activeDisplay;

      // Real-time live visual transcript update (ZERO DELAY)
      const txRow = document.getElementById('vcTranscriptRow');
      const txText = document.getElementById('vcTranscriptText');
      if (txRow && txText && state.voiceCompanionMode) {
        txRow.style.display = 'flex';
        txText.textContent = activeDisplay;
      }

      const userSection = document.getElementById('vcUserSection');
      const userTranscriptDisplay = document.getElementById('vcUserTranscriptDisplay');
      const speechTime = document.getElementById('vcSpeechTime');
      if (userSection) userSection.style.display = 'flex';
      if (userTranscriptDisplay) {
        userTranscriptDisplay.classList.remove('placeholder');
        userTranscriptDisplay.textContent = activeDisplay;
      }
      if (speechTime) speechTime.textContent = '🎙️ Speaking live...';

      // Subtle Orb pulse during live speaking
      const orb = document.getElementById('vcOrbSphere');
      if (orb) {
        orb.style.transform = 'scale(1.05)';
        setTimeout(() => { if (orb) orb.style.transform = 'scale(1)'; }, 180);
      }

      // Check for voice exit command
      const lower = activeDisplay.toLowerCase();
      const isExitCmd = /^(exit|stop|quit|close|goodbye|bye)(\s+(voice|companion|listening|mode))?$/i.test(lower) ||
                        lower === 'exit voice' || lower === 'stop voice' || lower === 'stop listening' || lower === 'goodbye' || lower === 'bye mindbridge';

      if (isExitCmd) {
        clearTimeout(vcSpeechSubmitTimer);
        elements.chatInput.value = '';
        if (txRow) txRow.style.display = 'none';
        stopVoiceCompanionMode(true);
        speakText("Voice companion ended. Take good care, I am always right here for you.");
        return;
      }

      // Natural turn taking:
      // Wait for a 2-second pause before submitting so user isn't cut off mid-thought.
      clearTimeout(vcSpeechSubmitTimer);
      const debounceDelay = 2000;
      vcSpeechSubmitTimer = setTimeout(() => {
        const textToSubmit = elements.chatInput.value.trim();
        if (textToSubmit && textToSubmit.length > 0 && !isSpeakingSequence) {
          clearTimeout(vcSpeechSubmitTimer);
          currentSpokenAccumulator = '';
          setVoiceCompanionState('analyzing', 'Interpreting voice nuance...');
          if (txRow) txRow.style.display = 'none';
          submitChatMessage(true);
        }
      }, debounceDelay);
    }
  };

  state.recognition.onerror = (event) => {
    state.isRecognitionStarting = false;
    console.debug('Speech recognition event:', event.error);
    if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
      state.isRecording = false;
      state.isRecognitionActive = false;
      setVoiceCompanionState('ready', 'Microphone access blocked. Please allow microphone in browser.');
      return;
    }

    if (event.error === 'network') {
      console.warn('[Voice Engine] Web Speech cloud service blocked by browser privacy (e.g. Brave Shield). Seamlessly utilizing continuous live audio VAD engine.');
      state.webSpeechDisabled = true;
      state.isRecording = false;
      state.isRecognitionActive = false;
      return;
    }

    if (event.error === 'no-speech') {
      // Just waiting for speech, keep attuned
      return;
    }

    // Never terminate companion mode on brief silences or timeouts
    if (state.voiceCompanionMode && !state.userExplicitlyStoppedVoice && !state.webSpeechDisabled) {
      scheduleListeningRestart(80);
    }
  };

  state.recognition.onend = () => {
    state.isRecording = false;
    state.isRecognitionActive = false;
    state.isRecognitionStarting = false;
    const micBtn = document.getElementById('micBtn');
    if (micBtn) micBtn.classList.remove('recording');

    if (state.wasPlayingBeforeRecording && state.soundscapeActive !== 'off' && !state.soundMuted) {
      const audio = getAudioElement();
      audio.play().then(() => {
        fadeAudioIn(audio, state.soundVolume, 2600);
      }).catch(() => {});
      state.wasPlayingBeforeRecording = false;
    }

    // Instantly re-arm continuous listening loop (half-duplex hands-free)
    if (state.voiceCompanionMode && !state.userExplicitlyStoppedVoice && !isSpeakingSequence) {
      scheduleListeningRestart(50);
    }
  };
}

function initSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  
  if (elements.languageSelect) {
    elements.languageSelect.addEventListener('change', (e) => {
      state.selectedLanguage = e.target.value;
      if (state.recognition) {
        state.recognition.lang = getEffectiveRecognitionLang();
      }
      if (state.voiceCompanionMode) {
        syncVoiceCompanionBarLanguage();
        syncVoiceCompanionModalLanguage();
      }
    });
  }

  // Wire Interactive Voice Companion Language Switcher Pills
  document.querySelectorAll('.vc-lang-pill').forEach(pill => {
    pill.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      const langCode = pill.getAttribute('data-vc-lang');
      document.querySelectorAll('.vc-lang-pill').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');

      state.vcSelectedLang = langCode;
      if (langCode !== 'auto') {
        state.selectedLanguage = langCode;
        if (elements.languageSelect) {
          elements.languageSelect.value = langCode;
        }
      }

      syncVoiceCompanionBarLanguage();
      syncVoiceCompanionModalLanguage();

      if (state.recognition) {
        try {
          state.recognition.lang = getEffectiveRecognitionLang();
          if (state.isRecognitionActive) {
            state.recognition.stop();
          } else {
            startListening();
          }
        } catch (e) {}
      }
    });
  });

  // Bind Voice Companion Exit Buttons (User Intimation)
  const stopVoiceCompanionBtn = document.getElementById('stopVoiceCompanionBtn');
  if (stopVoiceCompanionBtn) {
    stopVoiceCompanionBtn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      stopVoiceCompanionMode(true);
    });
  }

  const closeVcModalBtn = document.getElementById('closeVoiceCompanionModalBtn');
  if (closeVcModalBtn) {
    closeVcModalBtn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      stopVoiceCompanionMode(true);
    });
  }

  const vcModalExitBtn = document.getElementById('vcModalExitBtn');
  if (vcModalExitBtn) {
    vcModalExitBtn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      stopVoiceCompanionMode(true);
    });
  }

  const vcModalTapSpeakBtn = document.getElementById('vcModalTapSpeakBtn');
  if (vcModalTapSpeakBtn) {
    vcModalTapSpeakBtn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      stopSpeaking(true);
      startListening();
    });
  }

  const vcModal = document.getElementById('voiceCompanionModal');
  if (vcModal) {
    vcModal.addEventListener('click', (e) => {
      if (e.target === vcModal) {
        stopVoiceCompanionMode(true);
      }
    });
  }

  // Quick test prompt chips inside companion modal
  document.querySelectorAll('.vc-prompt-chip').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      const prompt = btn.getAttribute('data-prompt');
      if (prompt) {
        stopSpeaking(true);
        if (state.currentChatAbortController) {
          try { state.currentChatAbortController.abort(); } catch (e) {}
        }
        elements.chatInput.value = prompt;
        const userSection = document.getElementById('vcUserSection');
        const userTranscriptDisplay = document.getElementById('vcUserTranscriptDisplay');
        const speechTime = document.getElementById('vcSpeechTime');
        if (userSection) userSection.style.display = 'flex';
        if (userTranscriptDisplay) {
          userTranscriptDisplay.classList.remove('placeholder');
          userTranscriptDisplay.textContent = prompt;
        }
        if (speechTime) speechTime.textContent = 'Voice Thought Selected';
        submitChatMessage(true);
      }
    });
  });

  // Interpret Voice Button inside Companion Input Box
  const doneSpeakingBtn = document.getElementById('vcDoneSpeakingBtn');
  if (doneSpeakingBtn) {
    doneSpeakingBtn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      stopSpeaking(true);
      const userTranscriptDisplay = document.getElementById('vcUserTranscriptDisplay');
      const text = userTranscriptDisplay ? userTranscriptDisplay.textContent.trim() : '';
      const isTransient = !text || userTranscriptDisplay.classList.contains('placeholder') ||
        text.includes('Listening for your voice') ||
        text.includes('Hearing your voice') ||
        text.includes('Interpreting what you said') ||
        text.includes('Transcribing voice');

      if (!isTransient && text.length > 0) {
        elements.chatInput.value = text;
        submitChatMessage(true);
      } else if (vcAudioBuffers && vcAudioBuffers.length >= 1) {
        vcIsSpeaking = false;
        vcSilenceStartTime = 0;
        triggerAudioTranscribe();
      } else {
        const speechTime = document.getElementById('vcSpeechTime');
        if (speechTime) speechTime.textContent = 'Speak or tap a thought to interpret...';
      }
    });
  }

  // Allow Enter key on userTranscriptDisplay if user edits directly
  const userTranscriptDisplayEl = document.getElementById('vcUserTranscriptDisplay');
  if (userTranscriptDisplayEl) {
    userTranscriptDisplayEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        stopSpeaking(true);
        const text = userTranscriptDisplayEl.textContent.trim();
        if (text && !userTranscriptDisplayEl.classList.contains('placeholder')) {
          elements.chatInput.value = text;
          submitChatMessage(true);
        }
      }
    });
    userTranscriptDisplayEl.addEventListener('focus', () => {
      if (userTranscriptDisplayEl.classList.contains('placeholder')) {
        userTranscriptDisplayEl.textContent = '';
        userTranscriptDisplayEl.classList.remove('placeholder');
      }
    });
  }

  // Global Escape key to exit voice companion mode upon user intimation
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && state.voiceCompanionMode) {
      stopVoiceCompanionMode(true);
    }
  });

  // CRITICAL: Unconditionally bind mic button so clicking Voice ALWAYS opens companion mode!
  const micBtn = document.getElementById('micBtn');
  if (micBtn && !micBtn.dataset.voiceBound) {
    micBtn.dataset.voiceBound = 'true';
    micBtn.addEventListener('click', (e) => {
      toggleVoiceCompanionMode(e);
    });
  }

  // Pre-initialize SpeechRecognition instance if supported
  if (SpeechRecognition) {
    setupSpeechRecognitionInstance(SpeechRecognition);
  } else {
    console.warn('SpeechRecognition not natively supported in this browser; fallback audio active.');
  }
}

function stopRecording() {
  state.isRecording = false;
  if (elements.micBtn) elements.micBtn.classList.remove('recording');
  if (elements.audioVisualizer) elements.audioVisualizer.style.display = 'none';
}

// ==========================================================================
// HUMANIZED SPEECH SYNTHESIS ENGINE (REALISTIC CONVERSATIONAL CADENCE)
// ==========================================================================

let speechQueue = [];
let isSpeakingSequence = false;
let ttsStartedAt = 0;
const BARGE_IN_GRACE_MS = 2500; // Increased to 2.5s to prevent immediate echo self-interruption
let lastBargeInAt = 0;
const BARGE_IN_COOLDOWN_MS = 1500;

function initTTS() {
  if (elements.ttsToggleBtn) {
    elements.ttsToggleBtn.addEventListener('click', () => {
      state.ttsEnabled = !state.ttsEnabled;
      elements.ttsLabel.textContent = `Voice: ${state.ttsEnabled ? 'ON' : 'OFF'}`;
      elements.ttsToggleBtn.classList.toggle('active', state.ttsEnabled);
      if (!state.ttsEnabled) {
        stopSpeaking();
        if (state.voiceCompanionMode) {
          stopVoiceCompanionMode();
        }
      }
    });
  }

  const geminiVoiceSelect = document.getElementById('geminiVoiceSelect');
  if (geminiVoiceSelect) {
    geminiVoiceSelect.value = state.geminiVoice || 'Kore';
    geminiVoiceSelect.addEventListener('change', (e) => {
      state.geminiVoice = e.target.value;
      localStorage.setItem('mb_gemini_voice', e.target.value);
    });
  }

  const geminiApiKeyInput = document.getElementById('geminiApiKeyInput');
  if (geminiApiKeyInput) {
    geminiApiKeyInput.value = state.geminiApiKey || '';
    geminiApiKeyInput.addEventListener('input', (e) => {
      state.geminiApiKey = e.target.value.trim();
      localStorage.setItem('mb_gemini_api_key', e.target.value.trim());
    });
  }

  // Bind Voicebox Studio Persona Selector
  const vcPersonaSelect = document.getElementById('vcPersonaSelect');
  if (vcPersonaSelect) {
    const saved = localStorage.getItem('mb_voicebox_persona');
    if (saved) {
      vcPersonaSelect.value = saved;
      if (window.VoiceboxPipeline) window.VoiceboxPipeline.selectedPersona = saved;
    }
    vcPersonaSelect.addEventListener('change', (e) => {
      if (window.VoiceboxPipeline) {
        window.VoiceboxPipeline.selectedPersona = e.target.value;
      }
      localStorage.setItem('mb_voicebox_persona', e.target.value);
    });
  }

  // Connect Voicebox Web Audio Pipeline Visualizer & Gating
  if (window.VoiceboxPipeline && !window.VoiceboxPipeline._boundAppListeners) {
    window.VoiceboxPipeline._boundAppListeners = true;
    
    window.VoiceboxPipeline.onSpeechStart(() => {
      isSpeakingSequence = true;
      ttsStartedAt = Date.now();
      setVoiceCompanionState('speaking');
      duckBackgroundAudio(true);
      const speakingIndicator = document.getElementById('vcSpeakingIndicator');
      if (speakingIndicator) speakingIndicator.style.display = 'inline-flex';
      if (state.voiceCompanionMode && state.recognition) {
        try { state.recognition.stop(); } catch (e) {}
      }
    });

    window.VoiceboxPipeline.onSpeechEnd(() => {
      isSpeakingSequence = false;
      duckBackgroundAudio(false);
      const speakingIndicator = document.getElementById('vcSpeakingIndicator');
      if (speakingIndicator) speakingIndicator.style.display = 'none';
      if (state.voiceCompanionMode && !state.userExplicitlyStoppedVoice) {
        setVoiceCompanionState('listening');
        scheduleListeningRestart(80);
      }
    });

    window.VoiceboxPipeline.onVisualizerFrame((dataArray, avg) => {
      const modalWaveBars = document.querySelectorAll('#vcModalSoundwave span');
      if (modalWaveBars.length > 0 && avg > 6) {
        modalWaveBars.forEach((span, idx) => {
          const val = dataArray[idx % dataArray.length] || avg;
          const scale = Math.max(0.2, Math.min(2.2, (val / 75) * (0.8 + (idx % 3) * 0.25)));
          span.style.transform = `scaleY(${scale})`;
        });
      }
    });
  }
}

function getBestHumanVoice(langCode) {
  if (!window.speechSynthesis) return null;
  const voices = window.speechSynthesis.getVoices() || [];
  if (!voices.length) return null;

  const lang = (langCode || 'en-US').toLowerCase();
  const langPrefix = lang.split('-')[0];

  function scoreVoice(v) {
    let score = 0;
    const vLang = (v.lang || '').toLowerCase();
    const vName = (v.name || '').toLowerCase();

    // 1. Language matching
    if (lang === 'en-in' || lang === 'hinglish') {
      // For Hinglish: Prioritize authentic Indian Natural voices (Neerja, Prabhat, Swara, Madhur, Google English India)
      if (vLang === 'en-in' || vName.includes('india') || vName.includes('neerja') || vName.includes('prabhat') || vName.includes('heera') || vName.includes('ravi')) score += 60;
      if (vLang === 'hi-in' || vName.includes('hindi') || vName.includes('swara') || vName.includes('madhur')) score += 50;
    } else if (vLang === lang) {
      score += 40;
    } else if (vLang.startsWith(langPrefix)) {
      score += 25;
    }

    // 2. High-Fidelity Natural / Neural voice priority
    if (vName.includes('natural') || vName.includes('neural') || vName.includes('online')) score += 35;
    if (vName.includes('google')) score += 25;
    if (vName.includes('enhanced') || vName.includes('premium') || vName.includes('samantha') || vName.includes('jenny') || vName.includes('sonia') || vName.includes('elvira') || vName.includes('francisca') || vName.includes('bashkar')) score += 20;

    // Penalize legacy robotic voices if natural ones exist
    if (vName.includes('desktop') || vName.includes('espeak') || vName.includes('microsoft david') || vName.includes('microsoft mark') || vName.includes('microsoft zira')) score -= 15;

    return score;
  }

  const sortedVoices = [...voices].sort((a, b) => scoreVoice(b) - scoreVoice(a));
  return sortedVoices[0] || null;
}

function humanizeTextForSpeech(rawText, langCode) {
  if (!rawText) return '';
  let clean = rawText;

  // 1. Remove markdown bold, italic, headings, horizontal rules
  clean = clean.replace(/\*\*(.*?)\*\*/g, '$1');
  clean = clean.replace(/\*(.*?)\*/g, '$1');
  clean = clean.replace(/#{1,6}\s+/g, '');
  clean = clean.replace(/---/g, '');

  // 2. Remove emojis and unicode symbols so TTS doesn't read symbol names
  clean = clean.replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F700}-\u{1F77F}\u{1F780}-\u{1F7FF}\u{1F800}-\u{1F8FF}\u{1F900}-\u{1F9FF}\u{1FA00}-\u{1FA6F}\u{1FA70}-\u{1FAFF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, '');

  // 3. Convert bullet points into natural conversational phrasing
  clean = clean.replace(/^[•\-*]\s+/gm, ', ');
  clean = clean.replace(/\n[•\-*]\s+/g, ', ');

  // 4. Clean phone numbers & helpline IDs for natural spoken flow
  clean = clean.replace(/Tele-MANAS\s*\([^)]*\):/gi, 'Tele-Manas Helpline:');
  clean = clean.replace(/14416/g, '1 4 4 1 6');
  clean = clean.replace(/1800\s*891\s*4416/g, '1800 891 4416');
  clean = clean.replace(/\+91\s*9999\s*666\s*555/g, '9 9 9 9, 6 6 6, 5 5 5');
  clean = clean.replace(/\+91\s*98204\s*66726/g, '9 8 2 0 4, 6 6 7 2 6');
  clean = clean.replace(/\+91/g, 'plus 91');

  // 5. Clean URLs, brackets, extra whitespace
  clean = clean.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1');
  clean = clean.replace(/\s+/g, ' ').trim();

  return clean;
}

// ==========================================================================
// VOICE OUTPUT RESPONSE PERSPECTIVES ENGINE
// Authentic WhatsApp Audio Modules:
// 1. WhatsApp Audio 2026-09-13 at 8.46.54 PM.mpeg (Bengali Reflective Healing)
// 2. WhatsApp Audio 2026-09-13 at 8.48.14 PM.mpeg (English Grounded Courage)
// ==========================================================================

const VOICE_PERSPECTIVES = {
  bn: {
    id: 'bn',
    name: 'Bengali Reflective Perspective',
    shortName: 'Bengali (সাফল্য ও আত্মবিশ্বাস)',
    title: 'সাফল্য ও আত্মবিশ্বাস · Reflective Healing',
    url: '/resources/' + encodeURIComponent('WhatsApp Audio 2026-09-13 at 8.46.54 PM.mpeg'),
    altUrl: '/assets/voice_models/bengali_voice_module.mp3',
    duration: 71,
    description: 'Warm, deeply reflective, emotionally supportive cadence emphasizing self-compassion and inner strength.'
  },
  en: {
    id: 'en',
    name: 'English Grounded Courage Perspective',
    shortName: 'English (Overcoming Fear)',
    title: 'Overcoming Fear & Grounded Action',
    url: '/resources/' + encodeURIComponent('WhatsApp Audio 2026-09-13 at 8.48.14 PM.mpeg'),
    altUrl: '/assets/voice_models/english_voice_module.mp3',
    duration: 71,
    description: 'Gentle, commanding clarity, grounded courage, contemplative pauses that soothe anxiety and inspire forward action.'
  }
};

let currentPerspectiveAudio = null;
let currentPerspectiveTrack = null;
let activeTriggerButton = null;

function getActivePerspective(chatData = null) {
  if (state.activeVoicePerspective && state.activeVoicePerspective !== 'auto') {
    return state.activeVoicePerspective;
  }
  if (chatData) {
    if (chatData.voice_perspectives && chatData.voice_perspectives.recommended) {
      return chatData.voice_perspectives.recommended;
    }
    if (chatData.detected_language === 'bn' || (chatData.response && /[\u0980-\u09FF]/.test(chatData.response))) {
      return 'bn';
    }
  }
  const currentLang = state.selectedLanguage || 'en-US';
  return (currentLang.startsWith('bn') || currentLang === 'bn') ? 'bn' : 'en';
}

function stopCurrentPerspectiveAudio(isInterruptedByUser = false) {
  if (currentPerspectiveAudio) {
    try {
      currentPerspectiveAudio.pause();
      currentPerspectiveAudio.currentTime = 0;
    } catch (e) {}
    currentPerspectiveAudio = null;
  }
  currentPerspectiveTrack = null;

  // Reset companion modal cards and strip
  const bnCard = document.getElementById('vcPerspBnBtn');
  const enCard = document.getElementById('vcPerspEnBtn');
  const bnPlay = document.getElementById('vcPerspBnPlay');
  const enPlay = document.getElementById('vcPerspEnPlay');
  const strip = document.getElementById('vcPerspPlayerStrip');

  if (bnCard) bnCard.classList.remove('playing');
  if (enCard) enCard.classList.remove('playing');
  if (bnPlay) bnPlay.innerHTML = '<i data-lucide="play"></i>';
  if (enPlay) enPlay.innerHTML = '<i data-lucide="play"></i>';
  if (strip) strip.style.display = 'none';

  // Reset message bubble buttons
  document.querySelectorAll('.mp-btn.playing').forEach(btn => {
    btn.classList.remove('playing');
    const label = btn.getAttribute('data-persp') === 'bn' ? 'Bengali: সাফল্য ও আত্মবিশ্বাস' : 'English: Overcoming Fear';
    btn.innerHTML = `<i data-lucide="play"></i> <span>${label}</span>`;
  });

  if (window.lucide) window.lucide.createIcons();
  duckBackgroundAudio(false);

  if (isInterruptedByUser) {
    if (state.voiceCompanionMode && !state.userExplicitlyStoppedVoice) {
      setVoiceCompanionState('listening', 'You spoke · Listening to you now...');
      if (!state.isRecognitionActive && !state.isRecognitionStarting) {
        startListening();
      }
    }
  }
}

// Backward compatibility alias
function stopBenchmarkVoice() {
  stopCurrentPerspectiveAudio();
}

function runResponsePerspective(perspId, triggerElement = null) {
  const config = VOICE_PERSPECTIVES[perspId] || VOICE_PERSPECTIVES['en'];

  // If already playing this track, toggle stop
  if (currentPerspectiveAudio && currentPerspectiveTrack === perspId && !currentPerspectiveAudio.paused) {
    stopCurrentPerspectiveAudio();
    if (state.voiceCompanionMode && !state.userExplicitlyStoppedVoice) {
      setVoiceCompanionState('listening');
      scheduleListeningRestart(200);
    }
    return;
  }

  // Stop any other playing audio or speech synthesis
  stopCurrentPerspectiveAudio();
  if (window.speechSynthesis) {
    speechQueue = [];
    isSpeakingSequence = false;
    window.speechSynthesis.cancel();
  }

  // Audio instance with fallback
  let audio = new Audio(config.url);
  audio.addEventListener('error', (err) => {
    console.warn(`[Perspective Voice] Primary audio failed (${config.url}), using fallback:`, err);
    if (config.altUrl && !audio.src.endsWith(config.altUrl)) {
      audio.src = config.altUrl;
      audio.play().catch(e => console.warn('[Perspective Voice] Alt audio also failed:', e));
    }
  });

  currentPerspectiveAudio = audio;
  currentPerspectiveTrack = perspId;
  activeTriggerButton = triggerElement;

  // Visual cues in Voice Companion modal
  const bnCard = document.getElementById('vcPerspBnBtn');
  const enCard = document.getElementById('vcPerspEnBtn');
  const bnPlay = document.getElementById('vcPerspBnPlay');
  const enPlay = document.getElementById('vcPerspEnPlay');
  const strip = document.getElementById('vcPerspPlayerStrip');
  const trackLabel = document.getElementById('vcPerspTrackLabel');
  const trackTime = document.getElementById('vcPerspTrackTime');

  if (bnCard) bnCard.classList.toggle('playing', perspId === 'bn');
  if (enCard) enCard.classList.toggle('playing', perspId === 'en');
  if (bnPlay) bnPlay.innerHTML = `<i data-lucide="${perspId === 'bn' ? 'square' : 'play'}"></i>`;
  if (enPlay) enPlay.innerHTML = `<i data-lucide="${perspId === 'en' ? 'square' : 'play'}"></i>`;
  if (strip) strip.style.display = 'flex';
  if (trackLabel) trackLabel.textContent = `Playing ${config.name}...`;
  if (trackTime) trackTime.textContent = `0:00 / 1:11`;

  // Visual cues on message bubble buttons if trigger exists
  if (triggerElement) {
    document.querySelectorAll('.mp-btn.playing').forEach(b => {
      b.classList.remove('playing');
      const l = b.getAttribute('data-persp') === 'bn' ? 'Bengali: সাফল্য ও আত্মবিশ্বাস' : 'English: Overcoming Fear';
      b.innerHTML = `<i data-lucide="play"></i> <span>${l}</span>`;
    });
    triggerElement.classList.add('playing');
    triggerElement.innerHTML = `<i data-lucide="square"></i> <span>Playing ${config.shortName}</span>`;
  }

  if (window.lucide) window.lucide.createIcons();

  setVoiceCompanionState('speaking', `Playing ${config.name}`);
  duckBackgroundAudio(true);

  // HALF-DUPLEX: stop mic listener while audio is playing
  if (state.voiceCompanionMode && !state.userExplicitlyStoppedVoice) {
    if (state.recognition) {
      try { state.recognition.stop(); } catch(e) {}
    }
  }

  audio.addEventListener('timeupdate', () => {
    if (!currentPerspectiveAudio) return;
    const cur = Math.floor(currentPerspectiveAudio.currentTime);
    const dur = Math.floor(currentPerspectiveAudio.duration) || config.duration;
    const curMin = Math.floor(cur / 60);
    const curSec = (cur % 60).toString().padStart(2, '0');
    const durMin = Math.floor(dur / 60);
    const durSec = (dur % 60).toString().padStart(2, '0');
    if (trackTime) trackTime.textContent = `${curMin}:${curSec} / ${durMin}:${durSec}`;
  });

  audio.addEventListener('ended', () => {
    stopCurrentPerspectiveAudio();
    if (state.voiceCompanionMode && !state.userExplicitlyStoppedVoice) {
      setVoiceCompanionState('listening');
      scheduleListeningRestart(100);
    }
  });

  audio.play().catch(err => {
    console.warn('[Perspective Voice] Autoplay blocked or failed:', err);
    stopCurrentPerspectiveAudio();
  });
}

function toggleBenchmarkVoice(lang) {
  runResponsePerspective(lang);
}

window.runResponsePerspective = runResponsePerspective;
window.stopCurrentPerspectiveAudio = stopCurrentPerspectiveAudio;
window.toggleBenchmarkVoice = toggleBenchmarkVoice;
window.stopBenchmarkVoice = stopBenchmarkVoice;
window.getActivePerspective = getActivePerspective;

function stopSpeaking(isInterruptedByUser = false) {
  if (window.VoiceboxPipeline) {
    if (isInterruptedByUser) {
      window.VoiceboxPipeline.bargeIn();
    } else {
      window.VoiceboxPipeline.stop(0.04);
    }
  }
  if (currentGeminiAudio) {
    try {
      currentGeminiAudio.pause();
      currentGeminiAudio.currentTime = 0;
    } catch (e) {}
    currentGeminiAudio = null;
  }
  stopCurrentPerspectiveAudio(isInterruptedByUser);
  if (state.ttsWatchdogTimer) {
    clearTimeout(state.ttsWatchdogTimer);
    state.ttsWatchdogTimer = null;
  }
  if (window.speechSynthesis) {
    speechQueue = [];
    isSpeakingSequence = false;
    window.speechSynthesis.cancel();
    duckBackgroundAudio(false);
  }
  const speakingIndicator = document.getElementById('vcSpeakingIndicator');
  if (speakingIndicator) speakingIndicator.style.display = 'none';

  if (isInterruptedByUser) {
    flashInterruptionAlert();
    if (state.voiceCompanionMode && !state.userExplicitlyStoppedVoice) {
      setVoiceCompanionState('listening', 'You spoke · Listening to you now...');
      if (!state.isRecognitionActive && !state.isRecognitionStarting) {
        startListening();
      }
    }
  }
}

let currentGeminiAudio = null;

async function speakWithGeminiTTS(text, voice = 'Kore') {
  try {
    const key = state.geminiApiKey || localStorage.getItem('mb_gemini_api_key') || '';
    if (!key) {
      return false; // Instant fallback to Voicebox synthesis
    }
    const res = await fetch('/api/voice/tts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: text,
        voice: voice || state.geminiVoice || 'Kore',
        api_key: key
      })
    });

    if (!res.ok) {
      return false;
    }

    const contentType = res.headers.get('Content-Type') || '';
    if (contentType.includes('application/json')) {
      return false;
    }

    const blob = await res.blob();
    if (!blob || blob.size < 100) return false;

    const audioUrl = URL.createObjectURL(blob);
    stopSpeaking();

    const audio = new Audio(audioUrl);
    currentGeminiAudio = audio;
    isSpeakingSequence = true;
    ttsStartedAt = Date.now();

    setVoiceCompanionState('speaking');
    duckBackgroundAudio(true);

    if (state.voiceCompanionMode && !state.userExplicitlyStoppedVoice) {
      if (state.recognition) {
        try { state.recognition.stop(); } catch (e) {}
      }
    }

    const speakingIndicator = document.getElementById('vcSpeakingIndicator');
    if (speakingIndicator) speakingIndicator.style.display = 'inline-flex';

    audio.onended = () => {
      isSpeakingSequence = false;
      duckBackgroundAudio(false);
      URL.revokeObjectURL(audioUrl);
      currentGeminiAudio = null;
      if (speakingIndicator) speakingIndicator.style.display = 'none';

      if (state.voiceCompanionMode && !state.userExplicitlyStoppedVoice) {
        setVoiceCompanionState('listening');
        scheduleListeningRestart(100);
      }
    };

    audio.onerror = () => {
      isSpeakingSequence = false;
      duckBackgroundAudio(false);
      URL.revokeObjectURL(audioUrl);
      currentGeminiAudio = null;
      if (speakingIndicator) speakingIndicator.style.display = 'none';
      speakTextNative(text);
    };

    await audio.play();
    return true;
  } catch (err) {
    console.debug('[Gemini TTS] Fallback to Voicebox synthesis:', err);
    return false;
  }
}

async function speakText(text) {
  if (!text || !text.trim()) return;

  // 1. Primary Engine: Voicebox Studio Neural Audio Pipeline (Jamie Pine Architecture)
  if (window.VoiceboxPipeline) {
    try {
      const persona = window.VoiceboxPipeline.selectedPersona || window.VoiceboxPipeline.getPersonaForLanguage(state.selectedLanguage);
      await window.VoiceboxPipeline.speak(text, persona);
      return;
    } catch (err) {
      console.warn('[Voicebox] Primary synthesis note:', err);
    }
  }

  // 2. Secondary Engine: Google Gemini 3.1 TTS if API key provided
  const geminiOk = await speakWithGeminiTTS(text, state.geminiVoice || 'Kore');
  if (geminiOk) {
    return;
  }

  // 3. Graceful fallback: Calibrated Human Local synthesis
  speakTextNative(text);
}

function speakTextNative(text) {
  if (!window.speechSynthesis) return;

  // Cancel any existing speech or audio sequence immediately
  stopSpeaking();

  const currentLang = state.selectedLanguage || 'en-US';
  const cleanedText = humanizeTextForSpeech(text, currentLang);
  if (!cleanedText) {
    if (state.voiceCompanionMode && !state.userExplicitlyStoppedVoice) {
      setVoiceCompanionState('listening');
      scheduleListeningRestart(100);
    }
    return;
  }

  const bestVoice = getBestHumanVoice(currentLang);

  // Acoustically Calibrated to Benchmark Audio Modules (English & Bengali WhatsApp Audio):
  // Segment into natural contemplative clauses (sentences and clause pauses)
  const rawSentences = cleanedText.match(/[^.!?;\n—–]+[.!?;\n—–]+|[^.!?;\n—–]+$/g) || [cleanedText];
  const sentences = rawSentences
    .map(s => s.trim())
    .filter(s => s.length > 0);

  if (!sentences.length) {
    if (state.voiceCompanionMode && !state.userExplicitlyStoppedVoice) {
      setVoiceCompanionState('listening');
      scheduleListeningRestart(100);
    }
    return;
  }

  speechQueue = sentences;
  isSpeakingSequence = true;
  ttsStartedAt = Date.now();

  // Update Voice Companion state to speaking
  setVoiceCompanionState('speaking');

  // Auto-ducking: gently softens background soundscape during speech
  duckBackgroundAudio(true);

  // HALF-DUPLEX LISTENING: Stop microphone listener during speech output so it doesn't pick up the TTS output!
  if (state.voiceCompanionMode && !state.userExplicitlyStoppedVoice) {
    if (state.recognition) {
      try { state.recognition.stop(); } catch(e) {}
    }
  }

  function speakNextChunk() {
    if (state.ttsWatchdogTimer) {
      clearTimeout(state.ttsWatchdogTimer);
      state.ttsWatchdogTimer = null;
    }

    if (!isSpeakingSequence || speechQueue.length === 0) {
      isSpeakingSequence = false;
      duckBackgroundAudio(false);

      // TWO-WAY COMPANION CONTINUOUS MODE:
      // When AI finishes speaking, automatically re-activate microphone listening without clicking!
      if (state.voiceCompanionMode && !state.userExplicitlyStoppedVoice) {
        setVoiceCompanionState('listening');
        scheduleListeningRestart(100);
      }
      return;
    }

    const chunk = speechQueue.shift();
    const utterance = new SpeechSynthesisUtterance(chunk);

    // Acoustically Calibrated Parameters:
    // Pacing: 150-155 WPM (rate: 1.05) — natural conversational friend pace
    // Pitch: 0.97 (grounded, warm frequency)
    utterance.rate = 1.05;
    utterance.pitch = 0.97;
    utterance.volume = 1.0;
    utterance.lang = currentLang;

    if (bestVoice) {
      utterance.voice = bestVoice;
    }

    // TTS Watchdog: in case Chrome drops onend or stalls
    const wordsCount = chunk.split(/\s+/).length;
    const maxDurationMs = Math.max(8000, (wordsCount / 1.5) * 1000 + 6000);
    state.ttsWatchdogTimer = setTimeout(() => {
      if (isSpeakingSequence) {
        console.debug('TTS watchdog: proceeding to next chunk or restarting listener');
        window.speechSynthesis.cancel(); // Ensure stuck utterance is killed
        if (speechQueue.length > 0) {
          speakNextChunk();
        } else {
          isSpeakingSequence = false;
          duckBackgroundAudio(false);
          if (state.voiceCompanionMode && !state.userExplicitlyStoppedVoice) {
            setVoiceCompanionState('listening');
            scheduleListeningRestart(100);
          }
        }
      }
    }, maxDurationMs);

    // Chrome TTS pause bug workaround: periodic resume every 10s if it's long
    if (!window.ttsResumeInterval) {
      window.ttsResumeInterval = setInterval(() => {
        if (window.speechSynthesis && window.speechSynthesis.speaking) {
          window.speechSynthesis.resume();
        }
      }, 10000);
    }

    utterance.onend = () => {
      if (state.ttsWatchdogTimer) {
        clearTimeout(state.ttsWatchdogTimer);
        state.ttsWatchdogTimer = null;
      }

      // 60ms natural pause between clauses — friend-like conversational flow
      if (speechQueue.length > 0 && isSpeakingSequence) {
        setTimeout(speakNextChunk, 60);
      } else {
        isSpeakingSequence = false;
        duckBackgroundAudio(false);

        // TWO-WAY COMPANION CONTINUOUS MODE:
        // Automatically re-arms listening when utterance sequence completes!
        if (state.voiceCompanionMode && !state.userExplicitlyStoppedVoice) {
          setVoiceCompanionState('listening');
          scheduleListeningRestart(100);
        }
      }
    };

    utterance.onerror = (e) => {
      if (state.ttsWatchdogTimer) {
        clearTimeout(state.ttsWatchdogTimer);
        state.ttsWatchdogTimer = null;
      }

      if (e.error !== 'canceled') {
        if (speechQueue.length > 0 && isSpeakingSequence) {
          setTimeout(speakNextChunk, 50);
        } else {
          isSpeakingSequence = false;
          duckBackgroundAudio(false);

          if (state.voiceCompanionMode && !state.userExplicitlyStoppedVoice) {
            setVoiceCompanionState('listening');
            scheduleListeningRestart(100);
          }
        }
      }
    };

    window.speechSynthesis.speak(utterance);
  }

  speakNextChunk();
}

// ==========================================================================
// PROVIDERS DIRECTORY & FILTERING
// ==========================================================================

async function fetchProviders() {
  const params = new URLSearchParams();
  if (elements.filterSpecialty && elements.filterSpecialty.value) {
    params.append('specialty', elements.filterSpecialty.value);
  }
  if (elements.filterLanguage && elements.filterLanguage.value) {
    params.append('language', elements.filterLanguage.value);
  }
  if (elements.filterMode && elements.filterMode.value) {
    params.append('mode', elements.filterMode.value);
  }
  if (elements.filterMaxPrice && elements.filterMaxPrice.value) {
    params.append('max_price', elements.filterMaxPrice.value);
  }

  try {
    const res = await fetch(`/api/providers?${params.toString()}`);
    const data = await res.json();
    state.providers = data.providers || [];
    renderProviders(state.providers);
    if (elements.providerCountBadge) {
      elements.providerCountBadge.textContent = `${data.count} Verified`;
    }
  } catch (err) {
    console.error('Failed to fetch providers:', err);
  }
}

function renderProviders(providers) {
  if (!elements.providersGrid) return;
  elements.providersGrid.innerHTML = '';

  if (providers.length === 0) {
    elements.providersGrid.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 3rem; color: var(--text-sub);">
        <i data-lucide="search-x" style="width: 48px; height: 48px; margin-bottom: 1rem; color: var(--text-muted);"></i>
        <h3>No matching specialists found</h3>
        <p>Try resetting the filter criteria to browse all verified clinical psychologists and psychiatrists.</p>
      </div>
    `;
    if (window.lucide) window.lucide.createIcons();
    return;
  }

  providers.forEach(p => {
    const card = document.createElement('div');
    card.className = 'provider-card';

    const specBadges = p.specializations.map(s => `<span class="spec-badge">${s}</span>`).join('');
    const langList = p.languages.join(', ');
    const modeBadge = p.consultation_modes.includes('online') && p.consultation_modes.includes('in-person') 
      ? 'Online & In-Person' : (p.consultation_modes.includes('online') ? 'Online Video Call' : 'Clinic Visit');

    card.innerHTML = `
      <div>
        <div class="doc-card-top">
          <img src="${p.avatar_url}" alt="${p.name}" class="doc-avatar-img">
          <div class="doc-meta-right">
            <h3 class="doc-name">${p.name}</h3>
            <span class="doc-title">${p.title}</span>
            <span class="doc-qual">${p.qualification} • ${p.experience_years} yrs exp</span>
            <div class="doc-rating-row">
              <span class="rating-star">★ ${p.rating}</span>
              <span style="color: var(--text-muted);">(${p.reviews_count} verified reviews)</span>
            </div>
          </div>
        </div>

        <p class="doc-bio">${p.bio}</p>

        <div class="doc-badges-row">
          ${specBadges}
        </div>

        <div style="font-size: 0.76rem; color: var(--text-sub); margin-bottom: 1rem; display: flex; flex-direction: column; gap: 0.2rem;">
          <span><i data-lucide="globe" class="inline-icon text-teal"></i> <strong>Languages:</strong> ${langList}</span>
          <span><i data-lucide="video" class="inline-icon text-lavender"></i> <strong>Modes:</strong> ${modeBadge}</span>
          <span><i data-lucide="map-pin" class="inline-icon text-amber"></i> ${p.location_city}</span>
        </div>
      </div>

      <div class="doc-footer-row">
        <div class="doc-fee">
          ₹${p.fee_per_session.toLocaleString()} <span>/ 50-min session</span>
        </div>
        <button class="btn btn-primary book-doctor-btn" data-id="${p.id}">
          <i data-lucide="calendar"></i> Book Slot
        </button>
      </div>
    `;

    elements.providersGrid.appendChild(card);
  });

  document.querySelectorAll('.book-doctor-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const docId = e.currentTarget.getAttribute('data-id');
      openBookingModal(docId);
    });
  });

  if (window.lucide) window.lucide.createIcons();
}

if (elements.filterSpecialty) elements.filterSpecialty.addEventListener('change', fetchProviders);
if (elements.filterLanguage) elements.filterLanguage.addEventListener('change', fetchProviders);
if (elements.filterMode) elements.filterMode.addEventListener('change', fetchProviders);
if (elements.filterMaxPrice) elements.filterMaxPrice.addEventListener('change', fetchProviders);
if (elements.resetFiltersBtn) {
  elements.resetFiltersBtn.addEventListener('click', () => {
    elements.filterSpecialty.value = '';
    elements.filterLanguage.value = '';
    elements.filterMode.value = '';
    elements.filterMaxPrice.value = '';
    fetchProviders();
  });
}

// ==========================================================================
// APPOINTMENT BOOKING MODAL & SUBMISSION
// ==========================================================================

function openBookingModal(providerId) {
  const provider = state.providers.find(p => p.id === providerId);
  if (!provider) return;

  state.selectedProvider = provider;
  elements.bookProviderId.value = provider.id;
  elements.bookDocName.textContent = provider.name;
  elements.bookDocTitle.textContent = provider.title;
  elements.bookDocAvatar.src = provider.avatar_url;
  elements.bookDocMeta.innerHTML = `
    <span><i data-lucide="map-pin"></i> ${provider.location_city}</span> • 
    <span><i data-lucide="wallet"></i> ₹${provider.fee_per_session.toLocaleString()} / session</span>
  `;

  elements.bookSlot.innerHTML = '<option value="">Choose time...</option>';
  provider.available_slots.forEach(slot => {
    const opt = document.createElement('option');
    opt.value = slot;
    opt.textContent = slot;
    elements.bookSlot.appendChild(opt);
  });

  elements.bookingModal.style.display = 'flex';
  if (window.lucide) window.lucide.createIcons();
}

function initModals() {
  if (elements.closeBookingModalBtn) {
    elements.closeBookingModalBtn.addEventListener('click', () => {
      elements.bookingModal.style.display = 'none';
    });
  }
  if (elements.cancelBookingBtn) {
    elements.cancelBookingBtn.addEventListener('click', () => {
      elements.bookingModal.style.display = 'none';
    });
  }

  if (elements.bookingForm) {
    elements.bookingForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const payload = {
        provider_id: elements.bookProviderId.value,
        user_id: state.userId,
        patient_name: document.getElementById('bookPatientName').value,
        patient_email: document.getElementById('bookPatientEmail').value,
        patient_phone: document.getElementById('bookPatientPhone').value,
        appointment_date: elements.bookDate.value,
        appointment_time: elements.bookSlot.value,
        consultation_mode: document.getElementById('bookMode').value,
        concerns_summary: document.getElementById('bookNotes').value
      };

      try {
        const res = await fetch('/api/book', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const result = await res.json();

        if (result.success) {
          elements.bookingModal.style.display = 'none';
          showSuccessVoucher(result.appointment_details);
        } else {
          alert(result.error || 'Booking could not be completed.');
        }
      } catch (err) {
        console.error('Booking failed:', err);
        alert('Connection error while booking. Please try again.');
      }
    });
  }

  if (elements.closeSuccessModalBtn) {
    elements.closeSuccessModalBtn.addEventListener('click', () => {
      elements.successModal.style.display = 'none';
    });
  }
  if (elements.doneBookingBtn) {
    elements.doneBookingBtn.addEventListener('click', () => {
      elements.successModal.style.display = 'none';
      switchTab('chat');
    });
  }

  if (elements.headerSosBtn) {
    elements.headerSosBtn.addEventListener('click', openEmergencyModal);
  }
  if (elements.closeEmergencyModalBtn) {
    elements.closeEmergencyModalBtn.addEventListener('click', () => {
      elements.emergencyModal.style.display = 'none';
    });
  }
  if (elements.modalDismissBtn) {
    elements.modalDismissBtn.addEventListener('click', () => {
      elements.emergencyModal.style.display = 'none';
    });
  }
  if (elements.modalGroundingBtn) {
    elements.modalGroundingBtn.addEventListener('click', () => {
      elements.emergencyModal.style.display = 'none';
      switchTab('emergency');
      startBreathingPacer();
    });
  }
  if (elements.quickBreatheBtn) {
    elements.quickBreatheBtn.addEventListener('click', () => {
      switchTab('emergency');
      startBreathingPacer();
    });
  }
}

function showSuccessVoucher(details) {
  elements.vCode.textContent = details.confirmation_code;
  elements.vDoc.textContent = `${details.provider_name} (${details.provider_title})`;
  elements.vDateTime.textContent = `${details.date} at ${details.time}`;
  elements.vMode.textContent = details.mode === 'online' ? 'Secure Tele-health Video Link' : details.clinic_address;
  elements.vFee.textContent = `₹${details.fee.toLocaleString()} (Verified consultation)`;
  elements.successModal.style.display = 'flex';
  if (window.lucide) window.lucide.createIcons();
}

function openEmergencyModal() {
  // Mandatory Rule #3: Stop audio immediately when a crisis/self-harm/emergency flow is triggered
  stopAudioImmediately();
  
  if (elements.emergencyModal) {
    elements.emergencyModal.style.display = 'flex';
  }
  switchTab('emergency');
  
  const emergPane = document.getElementById('tab-emergency');
  if (emergPane) {
    emergPane.scrollTop = 0;
  }
  window.scrollTo({ top: 0, behavior: 'smooth' });
  
  initEmergencyModeInteractive();
  if (window.lucide) window.lucide.createIcons();
}

function initEmergencyModeInteractive() {
  // 1. SOS GPS Location Broadcast
  const sosLocationBtn = document.getElementById('sosLocationDispatchBtn');
  if (sosLocationBtn && !sosLocationBtn.dataset.bound) {
    sosLocationBtn.dataset.bound = 'true';
    sosLocationBtn.addEventListener('click', () => {
      sosLocationBtn.disabled = true;
      sosLocationBtn.innerHTML = '<i data-lucide="loader-2" class="spin"></i> Broadcasting GPS to Responders...';
      if (window.lucide) window.lucide.createIcons();

      const onDispatched = (lat, lon) => {
        sosLocationBtn.disabled = false;
        sosLocationBtn.innerHTML = '<i data-lucide="check-circle-2"></i> Location Dispatched to Emergency Line';
        sosLocationBtn.style.background = 'linear-gradient(135deg, #16a34a, #15803d)';
        if (window.lucide) window.lucide.createIcons();
        alert(`🚨 EMERGENCY SOS BROADCAST SENT\n\nCoordinates: ${lat.toFixed(4)}° N, ${lon.toFixed(4)}° E\nStatus: Nearest Emergency Ambulance & Crisis Responders Alerted.\nEstimated Response Time: 8-10 Minutes.`);
        setTimeout(() => {
          sosLocationBtn.innerHTML = '<i data-lucide="map-pin"></i> Broadcast GPS Location to Responders';
          sosLocationBtn.style.background = '';
          if (window.lucide) window.lucide.createIcons();
        }, 8000);
      };

      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          pos => onDispatched(pos.coords.latitude, pos.coords.longitude),
          () => onDispatched(28.6139, 77.2090),
          { timeout: 4000 }
        );
      } else {
        onDispatched(28.6139, 77.2090);
      }
    });
  }

  // 2. Nearby Clinical Hospitals Auto-Detector
  const findClinicsBtn = document.getElementById('findNearbyClinicsBtn');
  if (findClinicsBtn && !findClinicsBtn.dataset.bound) {
    findClinicsBtn.dataset.bound = 'true';
    findClinicsBtn.addEventListener('click', () => {
      findClinicsBtn.disabled = true;
      findClinicsBtn.innerHTML = '<i data-lucide="loader-2" class="spin"></i> Scanning Regional Emergency Hospitals...';
      if (window.lucide) window.lucide.createIcons();

      setTimeout(() => {
        findClinicsBtn.disabled = false;
        findClinicsBtn.innerHTML = '<i data-lucide="check"></i> Emergency Facilities Nearby';
        const d1 = document.getElementById('dist-nimhans');
        const d2 = document.getElementById('dist-aiims');
        const d3 = document.getElementById('dist-fortis');
        if (d1) d1.innerHTML = '<i data-lucide="navigation"></i> <span>1.8 km (Closest Inpatient Crisis Ward)</span>';
        if (d2) d2.innerHTML = '<i data-lucide="navigation"></i> <span>3.4 km (24/7 Casualty & Triage)</span>';
        if (d3) d3.innerHTML = '<i data-lucide="navigation"></i> <span>4.9 km (Dedicated Ambulance Station)</span>';
        if (window.lucide) window.lucide.createIcons();
      }, 700);
    });
  }

  // 3. Quick nav pills smooth scroll
  document.querySelectorAll('.emergency-nav-pill').forEach(pill => {
    if (!pill.dataset.bound) {
      pill.dataset.bound = 'true';
      pill.addEventListener('click', (e) => {
        const href = pill.getAttribute('href');
        if (href && href.startsWith('#')) {
          e.preventDefault();
          const target = document.querySelector(href);
          if (target) {
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }
          document.querySelectorAll('.emergency-nav-pill').forEach(p => p.classList.remove('active-pill'));
          pill.classList.add('active-pill');
        }
      });
    }
  });
}

// ==========================================================================
// CRISIS RESOURCES & HOTLINES
// ==========================================================================

async function fetchEmergencyResources() {
  try {
    const res = await fetch('/api/emergency-resources');
    const data = await res.json();
    const hotlines = data.resources || [];
    renderHotlines(hotlines);
  } catch (err) {
    console.error('Failed to load emergency resources:', err);
  }
}

function renderHotlines(hotlines) {
  if (elements.emergencyHotlinesList) {
    elements.emergencyHotlinesList.innerHTML = '';
    hotlines.forEach(h => {
      const item = document.createElement('div');
      item.className = 'hotline-entry';
      item.innerHTML = `
        <div class="hotline-meta">
          <h4>${h.name}</h4>
          <div class="hotline-num">${h.number}</div>
          <p class="hotline-desc">${h.description}</p>
        </div>
        <a href="${h.action}" class="hotline-call-btn">
          <i data-lucide="phone-call"></i> Call Now
        </a>
      `;
      elements.emergencyHotlinesList.appendChild(item);
    });
  }

  if (elements.modalHotlinesGrid) {
    elements.modalHotlinesGrid.innerHTML = '';
    hotlines.slice(0, 3).forEach(h => {
      const item = document.createElement('div');
      item.className = 'urgent-hotline-item';
      item.innerHTML = `
        <div>
          <strong style="font-size: 0.92rem;">${h.name}</strong>
          <div style="color: var(--teal-glow); font-weight: 700;">${h.number}</div>
          <div style="font-size: 0.7rem; color: var(--text-muted);">${h.badge}</div>
        </div>
        <a href="${h.action}" class="hotline-call-btn" style="padding: 0.4rem 0.85rem; font-size: 0.78rem;">
          <i data-lucide="phone-call"></i> Call
        </a>
      `;
      elements.modalHotlinesGrid.appendChild(item);
    });
  }

  if (window.lucide) window.lucide.createIcons();
}

// ==========================================================================
// 4-7-8 GROUNDING BREATHING PACER
// ==========================================================================

function initBreathingPacer() {
  if (elements.startBreathingBtn) {
    elements.startBreathingBtn.addEventListener('click', startBreathingPacer);
  }
  if (elements.stopBreathingBtn) {
    elements.stopBreathingBtn.addEventListener('click', stopBreathingPacer);
  }
}

function startBreathingPacer() {
  if (state.breathingActive) return;
  state.breathingActive = true;

  elements.startBreathingBtn.style.display = 'none';
  elements.stopBreathingBtn.style.display = 'inline-flex';

  let phase = 0;
  let count = 4;

  const cycle = () => {
    if (!state.breathingActive) return;

    if (phase === 0) {
      elements.breathingActionText.textContent = "Inhale slowly...";
      elements.breathingCircle.style.transform = "scale(1.35)";
      elements.breathingCircle.style.borderColor = "var(--teal-glow)";
      count = 4;
    } else if (phase === 1) {
      elements.breathingActionText.textContent = "Hold gently...";
      elements.breathingCircle.style.transform = "scale(1.35)";
      elements.breathingCircle.style.borderColor = "var(--amethyst-glow)";
      count = 7;
    } else if (phase === 2) {
      elements.breathingActionText.textContent = "Exhale completely...";
      elements.breathingCircle.style.transform = "scale(1.0)";
      elements.breathingCircle.style.borderColor = "var(--teal-light)";
      count = 8;
    }

    elements.breathingCountdown.textContent = `${count}s`;

    clearInterval(state.breathingInterval);
    state.breathingInterval = setInterval(() => {
      count--;
      if (count > 0) {
        elements.breathingCountdown.textContent = `${count}s`;
      } else {
        clearInterval(state.breathingInterval);
        phase = (phase + 1) % 3;
        cycle();
      }
    }, 1000);
  };

  cycle();
}

function stopBreathingPacer() {
  state.breathingActive = false;
  clearInterval(state.breathingInterval);
  elements.startBreathingBtn.style.display = 'inline-flex';
  elements.stopBreathingBtn.style.display = 'none';
  elements.breathingActionText.textContent = "Inhale";
  elements.breathingCountdown.textContent = "4s";
  elements.breathingCircle.style.transform = "scale(1.0)";
}

// ==========================================================================
// EMOTIONAL INSIGHTS
// ==========================================================================

async function loadInsights() {
  if (!state.conversationId) return;

  try {
    const res = await fetch(`/api/insights/${state.conversationId}`);
    const data = await res.json();

    if (elements.sessionSummaryText) {
      elements.sessionSummaryText.textContent = data.summary;
    }
    if (elements.insightStressNum) {
      elements.insightStressNum.textContent = `${data.average_stress} / 100`;
    }
    if (elements.insightMoodTone) {
      elements.insightMoodTone.textContent = data.mood_label || 'Reflective';
    }
    if (elements.insightSleepStatus) {
      elements.insightSleepStatus.textContent = data.sleep_status || 'Unspecified';
    }

    if (elements.sessionThemesList && data.dominant_themes) {
      elements.sessionThemesList.innerHTML = '';
      data.dominant_themes.forEach(t => {
        const span = document.createElement('span');
        span.className = 'theme-tag';
        span.textContent = t;
        elements.sessionThemesList.appendChild(span);
      });
    }

    if (elements.sessionStepsList && data.recommended_next_steps) {
      elements.sessionStepsList.innerHTML = '';
      data.recommended_next_steps.forEach(s => {
        const li = document.createElement('li');
        li.innerHTML = `<i data-lucide="check-circle-2"></i> ${s}`;
        elements.sessionStepsList.appendChild(li);
      });
      if (window.lucide) window.lucide.createIcons();
    }
  } catch (err) {
    console.error('Failed to load insights:', err);
  }
}

function downloadSummaryDocument() {
  const summary = elements.sessionSummaryText.textContent;
  const stress = elements.insightStressNum.textContent;
  const mood = elements.insightMoodTone.textContent;
  const dateStr = new Date().toLocaleDateString();

  const content = `=====================================================
MINDBRIDGE EMOTIONAL WELL-BEING & CONSULTATION SUMMARY
Generated on: ${dateStr}
Security Notice: Non-Diagnostic Client Reflection Record
=====================================================

1. SESSION OVERVIEW:
${summary}

2. EMOTIONAL METRICS:
• Subjective Stress Index: ${stress}
• Dominant Valence Tone: ${mood}

3. PURPOSE & PROFESSIONAL DISCLAIMER:
This document is synthesized to assist you when consulting a licensed
Clinical Psychologist or Psychiatrist. MindBridge does not diagnose or
treat medical conditions.

Verified specialist directory & booking available at: MindBridge Platform.
=====================================================`;

  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `MindBridge_Session_Summary_${Date.now()}.txt`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// ==========================================================================
// SIRI-LIKE ORGANIC ORB PHYSICS & CURSOR PARALLAX
// ==========================================================================

function initSiriOrbPhysics() {
  const orbContainer = document.getElementById('orbContainer');
  const orbFrame = document.getElementById('orbSphereFrame');
  if (!orbContainer || !orbFrame) return;

  const orbVideo = document.getElementById('aiHoloOrbVideo');
  const fallbackImg = document.getElementById('aiHoloOrb');
  if (orbVideo) {
    orbVideo.play().catch(() => {
      if (fallbackImg) fallbackImg.style.display = 'block';
    });
  }

  // Touch / Hover Glow Reactive Lift
  orbContainer.addEventListener('mouseenter', () => {
    orbContainer.style.filter = 'drop-shadow(0 0 35px rgba(56, 189, 248, 0.8))';
  });

  orbContainer.addEventListener('mouseleave', () => {
    orbContainer.style.filter = '';
  });

  // Click on Orb triggers mindful reflection
  orbContainer.addEventListener('click', () => {
    if (elements.chatInput) {
      elements.chatInput.value = "Surprise me with a calming reflection or mindful grounding thought.";
      submitChatMessage();
    }
  });
}

// ==========================================================================
// 10-MINUTE CHROMATIC ROTATION SYSTEM (27-COLOR THERAPEUTIC PALETTES)
// ==========================================================================

const THERAPEUTIC_THEMES = [
  { id: 'theme-azure', name: 'Azure Sanctuary', hex: '#3F6F8F', icon: 'palette', desc: 'Calm, trust & stability' },
  { id: 'theme-sage', name: 'Sage & Recovery', hex: '#2D857A', icon: 'leaf', desc: 'Healing, rest & renewal' },
  { id: 'theme-lavender', name: 'Lavender Gratitude', hex: '#7FA9C9', icon: 'sparkles', desc: 'Introspection & peace' },
  { id: 'theme-peach', name: 'Peach Compassion', hex: '#C96C7A', icon: 'heart', desc: 'Self-kindness & warmth' },
  { id: 'theme-amber', name: 'Amber Grounding', hex: '#B97519', icon: 'sun', desc: 'Bedtime comfort & focus' },
  { id: 'theme-obsidian', name: 'Obsidian Comfort', hex: '#182027', icon: 'moon', desc: 'Nighttime low-light calm' }
];

const TEN_MINUTES_MS = 10 * 60 * 1000; // 10 minutes = 600,000 ms

function initThemeSystem() {
  const toggleBtn = document.getElementById('themeToggleBtn');
  const toggleText = document.getElementById('themeToggleText');
  const toggleIcon = document.getElementById('themeToggleIcon');
  const timerDigits = document.getElementById('themeTimerDigits');
  const autoRotateToggle = document.getElementById('autoRotateThemeToggle');
  const themeSelectDropdown = document.getElementById('themeSelectDropdown');

  let currentThemeIndex = parseInt(localStorage.getItem('mb_theme_idx') || '0', 10);
  if (isNaN(currentThemeIndex) || currentThemeIndex < 0 || currentThemeIndex >= THERAPEUTIC_THEMES.length) {
    currentThemeIndex = 0;
  }

  let autoRotateEnabled = localStorage.getItem('mb_autorotate_theme') !== 'false';
  let rotationStartTime = parseInt(localStorage.getItem('mb_theme_start') || Date.now().toString(), 10);
  
  if (Date.now() - rotationStartTime > TEN_MINUTES_MS) {
    rotationStartTime = Date.now();
    localStorage.setItem('mb_theme_start', rotationStartTime.toString());
  }

  applyThemeIndex(currentThemeIndex);

  if (autoRotateToggle) {
    autoRotateToggle.checked = autoRotateEnabled;
    autoRotateToggle.addEventListener('change', (e) => {
      autoRotateEnabled = e.target.checked;
      localStorage.setItem('mb_autorotate_theme', autoRotateEnabled ? 'true' : 'false');
      if (timerDigits) {
        timerDigits.textContent = autoRotateEnabled ? formatTimeRemaining() : 'Paused';
      }
    });
  }

  if (themeSelectDropdown) {
    themeSelectDropdown.value = THERAPEUTIC_THEMES[currentThemeIndex].id;
    themeSelectDropdown.addEventListener('change', (e) => {
      const selectedId = e.target.value;
      const idx = THERAPEUTIC_THEMES.findIndex(t => t.id === selectedId);
      if (idx !== -1) {
        currentThemeIndex = idx;
        rotationStartTime = Date.now();
        localStorage.setItem('mb_theme_start', rotationStartTime.toString());
        applyThemeIndex(currentThemeIndex);
      }
    });
  }

  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      currentThemeIndex = (currentThemeIndex + 1) % THERAPEUTIC_THEMES.length;
      rotationStartTime = Date.now();
      localStorage.setItem('mb_theme_start', rotationStartTime.toString());
      applyThemeIndex(currentThemeIndex);
    });
  }

  // 1-second interval to update countdown and trigger automatic 10-minute rotation
  setInterval(() => {
    if (!autoRotateEnabled) {
      if (timerDigits) timerDigits.textContent = 'Paused';
      return;
    }

    const elapsed = Date.now() - rotationStartTime;
    if (elapsed >= TEN_MINUTES_MS) {
      // 10 minutes reached: smoothly rotate to the next therapeutic palette
      currentThemeIndex = (currentThemeIndex + 1) % THERAPEUTIC_THEMES.length;
      rotationStartTime = Date.now();
      localStorage.setItem('mb_theme_start', rotationStartTime.toString());
      applyThemeIndex(currentThemeIndex);
    } else {
      if (timerDigits) {
        timerDigits.textContent = formatTimeRemaining();
      }
    }
  }, 1000);

  function formatTimeRemaining() {
    const elapsed = Date.now() - rotationStartTime;
    const remainingMs = Math.max(0, TEN_MINUTES_MS - elapsed);
    const totalSecs = Math.floor(remainingMs / 1000);
    const mins = Math.floor(totalSecs / 60);
    const secs = totalSecs % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }

  function applyThemeIndex(index) {
    const theme = THERAPEUTIC_THEMES[index];
    localStorage.setItem('mb_theme_idx', index.toString());
    localStorage.setItem('mb_theme', theme.id);

    // Remove all previous theme classes
    THERAPEUTIC_THEMES.forEach(t => document.body.classList.remove(t.id));
    document.body.classList.remove('theme-dark', 'dark-theme');

    // Add active theme class
    document.body.classList.add(theme.id);
    if (theme.id === 'theme-obsidian') {
      document.body.classList.add('theme-dark', 'dark-theme');
    }

    // Update UI elements
    if (toggleText) toggleText.textContent = theme.name;
    if (toggleIcon) {
      toggleIcon.setAttribute('data-lucide', theme.icon);
      toggleIcon.style.color = theme.hex;
    }
    if (themeSelectDropdown) {
      themeSelectDropdown.value = theme.id;
    }
    if (timerDigits) {
      timerDigits.textContent = autoRotateEnabled ? formatTimeRemaining() : 'Paused';
    }
    if (window.lucide) window.lucide.createIcons();
  }
}

// ==========================================================================
// COMPREHENSIVE MULTILINGUAL I18N SYSTEM (ENGLISH / HINDI / HINGLISH)
// ==========================================================================

const I18N_DICTIONARY = {
  'en-US': {
    brand_title: 'MindBridge Sanctuary',
    safety_badge: 'Non-Diagnostic Guardrails Active',
    sos_btn: 'Emergency Service Mode',
    nav_chat: 'AI Psychological Chat & Reflection',
    nav_providers: 'Verified Specialists & Clinical Directory',
    nav_insights: 'Emotional Landscape & Clinical Narrative',
    nav_breathing: '4-7-8 Somatic Resonance Pacer',
    nav_soundscapes: 'Therapeutic Soundscapes (60-80 BPM)',
    nav_settings: 'Settings, Music & Neuro-Acoustic Frequencies',
    dock_badge_verified: '5 Verified',
    greeting: 'Hi, Friend',
    hero_title: 'How can I help today?',
    hero_subtitle: 'I\'m here to help — from compassionate emotional reflections to smart recommendations.',
    console_clarity: 'Unlock deeper clarity with MindBridge · Non-Diagnostic',
    co_regulation: 'Co-regulation Active',
    input_placeholder: 'Ask me anything ...',
    tool_voice: 'Voice',
    voice_companion_active: 'Two-Way Voice Companion Active',
    voice_companion_listening: 'Listening... speak naturally',
    voice_companion_analyzing: 'Analyzing your thoughts...',
    voice_companion_speaking: 'MindBridge is speaking...',
    voice_companion_exit: 'Exit Voice',
    tool_climate: 'Climate',
    tool_somatic: 'Somatic',
    tool_past: 'Past Reflection',
    music_off: 'Music: Off',
    music_on: 'Music: On',
    prompt_past_title: 'Past Life & Memories',
    prompt_past_desc: 'Reflect gently on childhood memories, turning points & mental state.',
    prompt_past_msg: 'I want to reflect on my past and childhood memories.',
    prompt_surprise_title: 'Surprise me!',
    prompt_surprise_desc: 'Surprise me with a mindful reflection or grounding exercise.',
    prompt_surprise_msg: 'Surprise me with a mindful reflection, grounding exercise, or calming thought.',
    prompt_somatic_title: 'Somatic release',
    prompt_somatic_desc: 'Guide me to release chest tightness, overthinking, or tension.',
    prompt_somatic_msg: 'I am feeling stress and physical tension in my body. Can you guide me through releasing it?',
    prompt_specialist_title: 'Specialist care',
    prompt_specialist_desc: 'Connect with verified clinical psychologists & psychiatrists.',
    mood_reflective: '🍃 Reflective',
    mood_overwhelmed: '🌪️ Overwhelmed',
    mood_anxious: '⚡ Anxious',
    mood_heavy: '🌧️ Heavy / Sad',
    mood_sleep: '🌙 Sleep Troubled',
    mood_hopeful: '☀️ Hopeful',
    mood_prompts: {
      reflective: "I'm feeling reflective and want to gently unpack my thoughts.",
      overwhelmed: "I feel intensely overwhelmed with life and cognitive fatigue.",
      anxious: "I am experiencing racing anxiety and chest tightness right now.",
      heavy: "My heart feels heavy, sad, and depleted of emotional energy.",
      sleep: "I am struggling with sleep disruption, insomnia, and midnight loops.",
      hopeful: "I'm beginning to feel a little more grounded and hopeful today."
    },
    somatic_mind: '🧠 Racing Mind / Head',
    somatic_chest: '🫁 Tight Chest',
    somatic_neck: '🦴 Shoulders & Neck',
    somatic_stomach: '🌊 Knots in Stomach',
    somatic_body: '🔋 Overall Body Drain',
    somatic_prompts: {
      mind: "I have racing thoughts and tight pressure in my head.",
      chest: "I am feeling tightness in my chest and difficulty breathing deeply.",
      neck: "I have severe stiffness and tension in my neck and shoulders.",
      stomach: "I feel nervous knots and distress in my stomach.",
      body: "My entire body feels deeply exhausted and physically drained."
    },
    dir_title: 'Verified Mental Health Specialists',
    dir_subtitle: 'Connect with licensed clinical psychologists & psychiatrists for structured therapeutic care.',
    filter_reset_btn: 'Reset',
    book_btn: 'Book Consultation',
    insights_title: 'Emotional Telemetry & Reflection Summary',
    insights_subtitle: 'Private, non-diagnostic reflection synthesis to support conversations with licensed specialists.',
    export_btn: 'Export Doctor Takeaway (.txt)',
    metric_stress_label: 'Subjective Stress Index',
    metric_stress_hint: 'Calculated via linguistic stress density & somatic signals.',
    metric_tone_label: 'Dominant Valence Tone',
    metric_tone_hint: 'Real-time affective sentiment classification.',
    metric_sleep_label: 'Sleep & Rhythm Status',
    metric_sleep_hint: 'Self-reported sleep quality tracking.',
    narrative_heading: 'Client Narrative Synthesis',
    themes_title: 'Dominant Themes Explored:',
    steps_title: 'Recommended Grounding Steps:',
    sos_hero_title: 'Immediate 24/7 Crisis Support Hub',
    sos_hero_subtitle: 'If you or someone you know is in acute distress or feeling unsafe, free, confidential, and professional help is available 24/7.',
    breathing_pacer_title: '4-7-8 Parasympathetic Breathing Pacer',
    breathing_pacer_desc: 'Follow the circle to slow heart rate variability and ground the nervous system.',
    start_breathing_btn: 'Start 4-7-8 Breathing',
    stop_breathing_btn: 'Stop',
    settings_title: 'Settings & Soundscape Experience',
    settings_subtitle: '60–80 BPM calming audio, neuro-acoustic frequencies & preferences',
    settings_preview_btn: 'Preview Voice',
    settings_clear_btn: 'Clear History',
    settings_done_btn: 'Done',
    booking_modal_title: 'Schedule Clinical Consultation',
    booking_modal_subtitle: 'Book appointment with your selected specialist',
    booking_confirm_btn: 'Confirm & Book Appointment',
    booking_cancel_btn: 'Cancel'
  },

  'hi-IN': {
    brand_title: 'माइंडब्रिज शांति केंद्र',
    safety_badge: 'गैर-नैदानिक सुरक्षा सक्रिय',
    sos_btn: 'Emergency Service Mode',
    nav_chat: 'मनोवैज्ञानिक बातचीत व मार्गदर्शन',
    nav_providers: 'सत्यापित विशेषज्ञ व क्लिनिकल डायरेक्टरी',
    nav_insights: 'भावनात्मक स्वास्थ्य व क्लिनिकल सारांश',
    nav_breathing: '4-7-8 प्राणायाम गति नियंत्रक',
    nav_soundscapes: 'उपचारात्मक ध्वनियाँ (60-80 BPM)',
    nav_settings: 'सेटिंग्स, संगीत व ऑडियो कैलिब्रेशन',
    dock_badge_verified: '5 सत्यापित',
    greeting: 'नमस्ते, मित्र',
    hero_title: 'आज मैं आपकी कैसे सहायता करूँ?',
    hero_subtitle: 'मैं यहाँ आपकी भावनात्मक सहायता और सुरक्षित मार्गदर्शन के लिए उपस्थित हूँ।',
    console_clarity: 'माइंडब्रिज के साथ स्पष्टता प्राप्त करें · गैर-नैदानिक',
    co_regulation: 'सह-विनियमन सक्रिय',
    input_placeholder: 'मुझसे अपने मन की बात साझा करें...',
    tool_voice: 'आवाज़',
    voice_companion_active: 'द्विमार्गी वॉयस साथी मोड सक्रिय',
    voice_companion_listening: 'सुन रहा हूँ... सहजता से बोलें',
    voice_companion_analyzing: 'विचारों का विश्लेषण हो रहा है...',
    voice_companion_speaking: 'माइंडब्रिज बोल रहा है...',
    voice_companion_exit: 'वॉयस बंद करें',
    tool_climate: 'मनोदशा',
    tool_somatic: 'शारीरिक तनाव',
    tool_past: 'अतीत संस्मरण',
    music_off: 'संगीत: बंद',
    music_on: 'संगीत: चालू',
    prompt_past_title: 'अतीत व बाल्यकाल संस्मरण',
    prompt_past_desc: 'बचपन की यादों, अनुभवों व जीवन के महत्वपूर्ण मोड़ों पर विचार करें।',
    prompt_past_msg: 'मैं अपने अतीत और बचपन की यादों पर विचार करना चाहता हूँ।',
    prompt_surprise_title: 'शांत विचार!',
    prompt_surprise_desc: 'एक शांत विचार या माइंडफुलनेस अभ्यास साझा करें।',
    prompt_surprise_msg: 'मुझे एक शांत विचार, प्राणायाम या माइंडफुलनेस अभ्यास के साथ मार्गदर्शन करें।',
    prompt_somatic_title: 'शारीरिक तनाव मुक्ति',
    prompt_somatic_desc: 'छाती के भारीपन और अत्यधिक सोच को शांत करने का मार्गदर्शन।',
    prompt_somatic_msg: 'कृपया मुझे शरीर के तनाव और अत्यधिक सोच को शांत करने का मार्गदर्शन दें।',
    prompt_specialist_title: 'विशेषज्ञ परामर्श',
    prompt_specialist_desc: 'सत्यापित मनोवैज्ञानिकों और मनोचिकित्सकों से संपर्क करें।',
    mood_reflective: '🍃 विचारशील / शांत',
    mood_overwhelmed: '🌪️ अत्यधिक तनावग्रस्त',
    mood_anxious: '⚡ बेचैन / चिंतित',
    mood_heavy: '🌧️ उदास / भारी मन',
    mood_sleep: '🌙 नींद में कठिनाई',
    mood_hopeful: '☀️ आशान्वित / सकारात्मक',
    mood_prompts: {
      reflective: "मैं विचारशील महसूस कर रहा हूँ और अपने विचारों को शांत मन से समझना चाहता हूँ।",
      overwhelmed: "मैं अत्यधिक तनाव, काम के बोझ और मानसिक थकान से बहुत परेशान महसूस कर रहा हूँ।",
      anxious: "मुझे इस समय बहुत घबराहट, चिंता और बेचैनी महसूस हो रही है।",
      heavy: "मेरा मन बहुत उदास, भारी और ऊर्जाहीन महसूस कर रहा है।",
      sleep: "मुझे रात को नींद न आने और बेचैन विचारों की समस्या हो रही है।",
      hopeful: "मैं आज थोड़ा अधिक शांत, सकारात्मक और आशान्वित महसूस कर रहा हूँ।"
    },
    somatic_mind: '🧠 सिर में भारीपन व तनाव',
    somatic_chest: '🫁 छाती में जकड़न',
    somatic_neck: '🦴 गर्दन व कंधों में अकड़न',
    somatic_stomach: '🌊 पेट में बेचैनी व घबराहट',
    somatic_body: '🔋 पूरे शरीर में अत्यधिक थकान',
    somatic_prompts: {
      mind: "मेरे सिर में भारीपन और अनियंत्रित विचारों का तनाव महसूस हो रहा है।",
      chest: "मुझे छाती में जकड़न और सांस लेने में भारीपन महसूस हो रहा है।",
      neck: "मेरी गर्दन और कंधों में बहुत अकड़न व शारीरिक तनाव है।",
      stomach: "मेरे पेट में घबराहट और बेचैनी की ऐंठन महसूस हो रही है।",
      body: "मेरा पूरा शरीर पूरी तरह थका हुआ और ऊर्जाहीन महसूस कर रहा है।"
    },
    dir_title: 'सत्यापित मानसिक स्वास्थ्य विशेषज्ञ',
    dir_subtitle: 'लाइसेंस प्राप्त अनुभवी मनोवैज्ञानिकों और मनोचिकित्सकों से व्यक्तिगत परामर्श लें।',
    filter_reset_btn: 'रीसेट',
    book_btn: 'परामर्श बुक करें',
    insights_title: 'भावनात्मक अंतर्दृष्टि और क्लिनिकल सारांश',
    insights_subtitle: 'आपके सत्रों से सुरक्षित रूप से विश्लेषित भावनात्मक स्वास्थ्य सारांश।',
    export_btn: 'डॉक्टर रिपोर्ट डाउनलोड करें (.txt)',
    metric_stress_label: 'व्यक्तिपरक तनाव सूचकांक',
    metric_stress_hint: 'भाषा तनाव घनत्व और शारीरिक संकेतों द्वारा गणना।',
    metric_tone_label: 'प्रमुख भावनात्मक स्वर',
    metric_tone_hint: 'वास्तविक समय भावनात्मक वर्गीकरण।',
    metric_sleep_label: 'नींद और विश्राम स्थिति',
    metric_sleep_hint: 'व्यक्तिगत नींद गुणवत्ता ट्रैकिंग।',
    narrative_heading: 'सत्र का भावनात्मक सारांश',
    themes_title: 'सत्र में विश्लेषित मुख्य विषय:',
    steps_title: 'अनुशंसित उपचारात्मक कदम:',
    sos_hero_title: '24/7 तत्काल संकट सहायता केंद्र',
    sos_hero_subtitle: 'यदि आप या आपका कोई परिचित अत्यधिक तनाव या असुरक्षित महसूस कर रहा है, तो 24/7 निःशुल्क सहायता उपलब्ध है।',
    breathing_pacer_title: '4-7-8 प्राणायाम गति नियंत्रक',
    breathing_pacer_desc: 'हृदय गति को शांत करने और तंत्रिका तंत्र को स्थिर करने के लिए वृत्त का अनुसरण करें।',
    start_breathing_btn: '4-7-8 प्राणायाम शुरू करें',
    stop_breathing_btn: 'रोकें',
    settings_title: 'शांति केंद्र सेटिंग्स व ऑडियो अनुभव',
    settings_subtitle: '60–80 BPM उपचारात्मक ध्वनियाँ, न्यूरो-ध्वनि तरंगें व प्राथमिकताएं',
    settings_preview_btn: 'आवाज़ का पूर्वावलोकन',
    settings_clear_btn: 'इतिहास मिटाएं',
    settings_done_btn: 'पूर्ण',
    booking_modal_title: 'क्लिनिकल परामर्श शेड्यूल करें',
    booking_modal_subtitle: 'अपने चयनित विशेषज्ञ के साथ अपॉइंटमेंट बुक करें',
    booking_confirm_btn: 'पुष्टि करें और बुक करें',
    booking_cancel_btn: 'रद्द करें'
  },

  'en-IN': {
    brand_title: 'MindBridge Sanctuary',
    safety_badge: 'Non-Diagnostic Guardrails Active',
    sos_btn: 'Emergency Service Mode',
    nav_chat: 'AI Psychological Chat & Reflection',
    nav_providers: 'Verified Specialists & Doctor Directory',
    nav_insights: 'Emotional Insights & Session Summary',
    nav_breathing: '4-7-8 Breathing Resonance Pacer',
    nav_soundscapes: 'Therapeutic Soundscapes (60-80 BPM)',
    nav_settings: 'Settings, Music & Audio Calibration',
    dock_badge_verified: '5 Verified',
    greeting: 'Hello, Friend',
    hero_title: 'Aaj main aapki kaise help karoon?',
    hero_subtitle: 'Main yahan aapki emotional support aur safe guidance ke liye ready hoon.',
    console_clarity: 'MindBridge ke saath clarity paayein · Non-Diagnostic',
    co_regulation: 'Co-regulation Active',
    input_placeholder: 'Apne man ki baat share karein...',
    tool_voice: 'Voice',
    voice_companion_active: 'Two-Way Voice Companion Active',
    voice_companion_listening: 'Sun raha hoon... naturally boliye',
    voice_companion_analyzing: 'Thoughts analyze ho rahe hain...',
    voice_companion_speaking: 'MindBridge bol raha hai...',
    voice_companion_exit: 'Exit Voice',
    tool_climate: 'Mood/Climate',
    tool_somatic: 'Somatic Relief',
    tool_past: 'Past Reflection',
    music_off: 'Music: Off',
    music_on: 'Music: On',
    prompt_past_title: 'Past Life & Memories',
    prompt_past_desc: 'Childhood memories aur past turning points par gentle reflection.',
    prompt_past_msg: 'Main apne past aur childhood memories par reflect karna chahta hoon.',
    prompt_surprise_title: 'Surprise me!',
    prompt_surprise_desc: 'Ek calming reflection ya grounding exercise batayein.',
    prompt_surprise_msg: 'Mujhe ek mindful reflection, grounding exercise ya calming thought ke saath guide karein.',
    prompt_somatic_title: 'Somatic release',
    prompt_somatic_desc: 'Chest tightness aur overthinking ko release karne ka guidance.',
    prompt_somatic_msg: 'Mujhe body me physical tension aur chest tightness release karne ka step-by-step guidance dein.',
    prompt_specialist_title: 'Specialist care',
    prompt_specialist_desc: 'Verified clinical psychologists aur doctors se connect karein.',
    mood_reflective: '🍃 Reflective & Calm',
    mood_overwhelmed: '🌪️ Overwhelmed',
    mood_anxious: '⚡ Anxious / Restless',
    mood_heavy: '🌧️ Heavy / Sad',
    mood_sleep: '🌙 Sleep Troubled',
    mood_hopeful: '☀️ Hopeful & Grounded',
    mood_prompts: {
      reflective: "Main reflective feel kar raha hoon aur apne thoughts ko gently unpack karna chahta hoon.",
      overwhelmed: "Main life ke pressure, deadlines aur mental fatigue se bohot overwhelmed feel kar raha hoon.",
      anxious: "Mujhe abhi bohot ghabrahat, anxiety aur tension feel ho rahi hai.",
      heavy: "Mera man bohot heavy aur sad feel kar raha hai, low energy lag rahi hai.",
      sleep: "Mujhe night me neend nahi aa rahi aur overthinking se sleep disrupt ho rahi hai.",
      hopeful: "Main aaj thoda better, positive aur grounded feel kar raha hoon."
    },
    somatic_mind: '🧠 Racing Mind / Head Tension',
    somatic_chest: '🫁 Tight Chest',
    somatic_neck: '🦴 Neck & Shoulder Stiffness',
    somatic_stomach: '🌊 Knots in Stomach',
    somatic_body: '🔋 Full Body Exhaustion',
    somatic_prompts: {
      mind: "Mere mind me racing thoughts aur head me bohot tension feel ho rahi hai.",
      chest: "Mujhe chest me tightness aur breathlessness feel ho rahi hai.",
      neck: "Mere neck aur shoulders me bohot stiffness aur somatic tension hai.",
      stomach: "Mere stomach me anxiety aur nervous knots feel ho rahe hain.",
      body: "Meri puri body completely exhausted aur physically drained lag rahi hai."
    },
    dir_title: 'Verified Mental Health Specialists',
    dir_subtitle: 'Licensed clinical psychologists aur psychiatrists se personal consultation lein.',
    filter_reset_btn: 'Reset',
    book_btn: 'Book Consultation',
    insights_title: 'Emotional Landscape & Clinical Narrative',
    insights_subtitle: 'Aapke sessions se synthesized safe emotional health summary.',
    export_btn: 'Download Doctor Report (.txt)',
    metric_stress_label: 'Subjective Stress Index',
    metric_stress_hint: 'Linguistic stress density aur somatic signals se calculate kiya gaya.',
    metric_tone_label: 'Dominant Valence Tone',
    metric_tone_hint: 'Real-time affective sentiment classification.',
    metric_sleep_label: 'Sleep & Rhythm Status',
    metric_sleep_hint: 'Self-reported sleep quality tracking.',
    narrative_heading: 'Client Narrative Synthesis',
    themes_title: 'Dominant Themes Explored:',
    steps_title: 'Recommended Grounding Steps:',
    sos_hero_title: '24/7 Immediate Crisis Support Available',
    sos_hero_subtitle: 'Aap akele nahi hain. Free aur confidential help abhi available hai.',
    breathing_pacer_title: '4-7-8 Breathing Resonance Pacer',
    breathing_pacer_desc: 'Heart rate ko calm karne aur nervous system ko relax karne ke liye circle follow karein.',
    start_breathing_btn: 'Start 4-7-8 Breathing',
    stop_breathing_btn: 'Stop',
    settings_title: 'Sanctuary Settings & Audio Calibration',
    settings_subtitle: '60–80 BPM calming audio, neuro-acoustic frequencies & preferences',
    settings_preview_btn: 'Preview Voice',
    settings_clear_btn: 'Clear History',
    settings_done_btn: 'Done',
    booking_modal_title: 'Schedule Clinical Consultation',
    booking_modal_subtitle: 'Selected specialist ke saath appointment book karein',
    booking_confirm_btn: 'Confirm & Book Appointment',
    booking_cancel_btn: 'Cancel'
  },

  'es-ES': {
    brand_title: 'Santuario MindBridge',
    safety_badge: 'Protección No-Diagnóstica Activa',
    sos_btn: '24/7 SOS',
    nav_chat: 'Chat Psicológico y Reflexión Empática',
    nav_providers: 'Especialistas Verificados y Directorio',
    nav_insights: 'Paisaje Emocional y Resumen Clínico',
    nav_breathing: 'Guía de Respiración 4-7-8',
    nav_soundscapes: 'Paisajes Sonoros Terapéuticos (60-80 BPM)',
    nav_settings: 'Ajustes, Música y Calibración Acústica',
    dock_badge_verified: '5 Verificados',
    greeting: 'Hola, Amigo',
    hero_title: '¿Cómo puedo acompañarte hoy?',
    hero_subtitle: 'Estoy aquí para escucharte — desde reflexiones emocionales cálidas hasta orientación profesional.',
    console_clarity: 'Encuentra claridad y calma con MindBridge · No-Diagnóstico',
    co_regulation: 'Co-regulación Activa',
    input_placeholder: 'Comparte lo que sientes con total libertad...',
    tool_voice: 'Voz',
    voice_companion_active: 'Modo Acompañante de Voz Activo',
    voice_companion_listening: 'Escuchándote... habla con calma',
    voice_companion_analyzing: 'Analizando tus sentimientos...',
    voice_companion_speaking: 'MindBridge está hablando...',
    voice_companion_exit: 'Salir de Voz',
    tool_climate: 'Clima Emocional',
    tool_somatic: 'Tensión Somática',
    tool_past: 'Reflexión Pasada',
    music_off: 'Música: Apagada',
    music_on: 'Música: Encendida',
    prompt_past_title: 'Vida Pasada y Recuerdos',
    prompt_past_desc: 'Reflexiona suavemente sobre recuerdos de la infancia y momentos clave.',
    prompt_past_msg: 'Quiero reflexionar sobre mi pasado y recuerdos de la infancia.',
    prompt_surprise_title: '¡Sorpréndeme!',
    prompt_surprise_desc: 'Comparte una reflexión consciente o un ejercicio de calma.',
    prompt_surprise_msg: 'Sorpréndeme con una reflexión consciente, ejercicio de calma o pensamiento reconfortante.',
    prompt_somatic_title: 'Alivio somático',
    prompt_somatic_desc: 'Guíame para liberar la tensión en el pecho o pensamientos rumiantes.',
    prompt_somatic_msg: 'Guíame para liberar la tensión muscular, la opresión en el pecho y el exceso de pensamientos.',
    prompt_specialist_title: 'Atención profesional',
    prompt_specialist_desc: 'Conecta con psicólogos y psiquiatras clínicos verificados.',
    mood_reflective: '🍃 Reflexivo y Tranquilo',
    mood_overwhelmed: '🌪️ Abrumado / Agotado',
    mood_anxious: '⚡ Ansioso / Inquieto',
    mood_heavy: '🌧️ Con el corazón pesado / Triste',
    mood_sleep: '🌙 Dificultad para dormir',
    mood_hopeful: '☀️ Con esperanza y optimismo',
    mood_prompts: {
      reflective: "Me siento reflexivo y deseo ordenar y comprender mis pensamientos con calma.",
      overwhelmed: "Me siento intensamente abrumado por la presión, el cansancio y el ritmo diario.",
      anxious: "Siento mucha ansiedad, inquietud y una opresión en el pecho en este momento.",
      heavy: "Mi corazón se siente pesado, triste y con muy poca energía emocional.",
      sleep: "Tengo problemas para dormir, insomnio y pensamientos acelerados por la noche.",
      hopeful: "Hoy comienzo a sentirme un poco más tranquilo, motivado y con esperanza."
    },
    somatic_mind: '🧠 Mente acelerada / Presión en la cabeza',
    somatic_chest: '🫁 Opresión en el pecho',
    somatic_neck: '🦴 Rigidez en cuello y hombros',
    somatic_stomach: '🌊 Nudo en el estómago',
    somatic_body: '🔋 Agotamiento físico general',
    somatic_prompts: {
      mind: "Tengo la cabeza llena de pensamientos acelerados y mucha tensión mental.",
      chest: "Siento una opresión en el pecho y dificultad para respirar hondo.",
      neck: "Tengo mucha rigidez y tensión acumulada en el cuello y los hombros.",
      stomach: "Siento un nudo de nervios y malestar en el estómago.",
      body: "Siento un agotamiento físico profundo en todo el cuerpo."
    },
    dir_title: 'Especialistas en Salud Mental Verificados',
    dir_subtitle: 'Conéctate con psicólogos y psiquiatras clínicos para una atención terapéutica estructurada.',
    filter_reset_btn: 'Restablecer',
    book_btn: 'Reservar Consulta',
    insights_title: 'Telemetría Emocional y Resumen de Sesión',
    insights_subtitle: 'Síntesis privada y no-diagnóstica para apoyar tus conversaciones con especialistas.',
    export_btn: 'Descargar Informe para el Médico (.txt)',
    metric_stress_label: 'Índice de Estrés Subjetivo',
    metric_stress_hint: 'Calculado mediante densidad de estrés lingüístico y señales somáticas.',
    metric_tone_label: 'Tono Emocional Dominante',
    metric_tone_hint: 'Clasificación afectiva en tiempo real.',
    metric_sleep_label: 'Estado del Sueño y Ritmo',
    metric_sleep_hint: 'Monitoreo de la calidad de descanso autoreportada.',
    narrative_heading: 'Síntesis Narrativa del Consultante',
    themes_title: 'Temas Dominantes Explorados:',
    steps_title: 'Pasos de Calma y Bienestar Recomendados:',
    sos_hero_title: 'Centro de Apoyo en Crisis Inmediato 24/7',
    sos_hero_subtitle: 'Si tú o alguien que conoces está en crisis o se siente en peligro, hay ayuda gratuita, confidencial y profesional disponible 24/7.',
    breathing_pacer_title: 'Guía de Respiración Parasimpática 4-7-8',
    breathing_pacer_desc: 'Sigue el ritmo del círculo para reducir la frecuencia cardíaca y calmar tu sistema nervioso.',
    start_breathing_btn: 'Iniciar Respiración 4-7-8',
    stop_breathing_btn: 'Detener',
    settings_title: 'Ajustes del Santuario y Experiencia Acústica',
    settings_subtitle: 'Audio relajante a 60–80 BPM, frecuencias neuro-acústicas y preferencias',
    settings_preview_btn: 'Escuchar Voz',
    settings_clear_btn: 'Borrar Historial',
    settings_done_btn: 'Listo',
    booking_modal_title: 'Programar Consulta Clínica',
    booking_modal_subtitle: 'Reserva una cita con tu especialista seleccionado',
    booking_confirm_btn: 'Confirmar y Reservar Cita',
    booking_cancel_btn: 'Cancelar'
  },

  'pt-BR': {
    brand_title: 'Santuário MindBridge',
    safety_badge: 'Proteção Não-Diagnóstica Ativa',
    sos_btn: '24/7 SOS',
    nav_chat: 'Chat Psicológico e Reflexão Acolhedora',
    nav_providers: 'Especialistas Verificados e Diretório',
    nav_insights: 'Paisagem Emocional e Síntese Clínica',
    nav_breathing: 'Guia de Respiração 4-7-8',
    nav_soundscapes: 'Paisagens Sonoras Terapêuticas (60-80 BPM)',
    nav_settings: 'Configurações, Música e Calibração Acústica',
    dock_badge_verified: '5 Verificados',
    greeting: 'Olá, Amigo',
    hero_title: 'Como posso te acolher hoje?',
    hero_subtitle: 'Estou aqui para te ouvir com carinho — desde reflexões emocionais gentis até orientação segura.',
    console_clarity: 'Encontre clareza e paz com MindBridge · Não-Diagnóstico',
    co_regulation: 'Co-regulação Ativa',
    input_placeholder: 'Compartilhe o que você está sentindo com total liberdade...',
    tool_voice: 'Voz',
    voice_companion_active: 'Modo Companheiro de Voz Ativo',
    voice_companion_listening: 'Ouvindo você... fale com calma',
    voice_companion_analyzing: 'Analisando seus sentimentos...',
    voice_companion_speaking: 'MindBridge está falando...',
    voice_companion_exit: 'Sair de Voz',
    tool_climate: 'Clima Emocional',
    tool_somatic: 'Tensão Corporal',
    tool_past: 'Reflexão Passada',
    music_off: 'Música: Desligada',
    music_on: 'Música: Ligada',
    prompt_past_title: 'Vida Passada e Memórias',
    prompt_past_desc: 'Reflita suavemente sobre memórias de infância e pontos de virada.',
    prompt_past_msg: 'Quero refletir sobre meu passado e memórias de infância.',
    prompt_surprise_title: 'Surpreenda-me!',
    prompt_surprise_desc: 'Compartilhe uma reflexão acolhedora ou exercício de respiração.',
    prompt_surprise_msg: 'Surpreenda-me com uma reflexão acolhedora, exercício de respiração ou pensamento de paz.',
    prompt_somatic_title: 'Alívio corporal',
    prompt_somatic_desc: 'Ajude-me a aliviar o aperto no peito, ansiedade ou pensamentos acelerados.',
    prompt_somatic_msg: 'Guie-me para aliviar a tensão no corpo, o aperto no peito e o excesso de pensamentos.',
    prompt_specialist_title: 'Apoio profissional',
    prompt_specialist_desc: 'Conecte-se com psicólogos e psiquiatras clínicos verificados.',
    mood_reflective: '🍃 Reflexivo e Calmo',
    mood_overwhelmed: '🌪️ Sobrecarregado / Esgotado',
    mood_anxious: '⚡ Ansioso / Agitado',
    mood_heavy: '🌧️ Coração pesado / Triste',
    mood_sleep: '🌙 Dificuldade para dormir',
    mood_hopeful: '☀️ Esperançoso e Confiante',
    mood_prompts: {
      reflective: "Estou reflexivo e quero acolher e organizar meus pensamentos com tranquilidade.",
      overwhelmed: "Estou me sentindo muito sobrecarregado com o excesso de pressão e cansaço mental.",
      anxious: "Estou sentindo muita ansiedade, inquietude e tensão no peito agora.",
      heavy: "Meu coração está pesado, triste e com pouca energia emocional.",
      sleep: "Estou com insônia, sono agitado e muitos pensamentos na hora de dormir.",
      hopeful: "Hoje estou começando a me sentir mais centrado, leve e esperançoso."
    },
    somatic_mind: '🧠 Mente acelerada / Pressão na cabeça',
    somatic_chest: '🫁 Aperto no peito',
    somatic_neck: '🦴 Tensão nos ombros e pescoço',
    somatic_stomach: '🌊 Nó no estômago',
    somatic_body: '🔋 Exaustão corporal geral',
    somatic_prompts: {
      mind: "Minha mente está acelerada com pensamentos e muita tensão na cabeça.",
      chest: "Sinto um aperto no peito e dificuldade para respirar com calma.",
      neck: "Estou com os ombros e o pescoço muito rígidos e tensos.",
      stomach: "Sinto um nó no estômago e desconforto causado pela ansiedade.",
      body: "Meu corpo inteiro está exausto e sem energia física."
    },
    dir_title: 'Especialistas em Saúde Mental Verificados',
    dir_subtitle: 'Conecte-se com psicólogos e psiquiatras clínicos para um cuidado terapêutico estruturado.',
    filter_reset_btn: 'Redefinir',
    book_btn: 'Agendar Consulta',
    insights_title: 'Telemetria Emocional e Síntese da Sessão',
    insights_subtitle: 'Síntese privada e não-diagnóstica para apoiar suas conversas com especialistas.',
    export_btn: 'Baixar Relatório para o Médico (.txt)',
    metric_stress_label: 'Índice de Estresse Subjetivo',
    metric_stress_hint: 'Calculado através da densidade emocional e sinais somáticos.',
    metric_tone_label: 'Tom Emocional Dominante',
    metric_tone_hint: 'Classificação afetiva em tempo real.',
    metric_sleep_label: 'Qualidade do Sono e Ritmo',
    metric_sleep_hint: 'Acompanhamento do descanso e ciclos noturnos.',
    narrative_heading: 'Síntese Narrativa da Sessão',
    themes_title: 'Principais Temas Explorados:',
    steps_title: 'Práticas Recomendadas de Acolhimento:',
    sos_hero_title: 'Centro de Apoio em Crise 24/7 Imediato',
    sos_hero_subtitle: 'Se você ou alguém que você conhece está em sofrimento agudo, há apoio gratuito, confidencial e profissional disponível 24 horas por dia.',
    breathing_pacer_title: 'Guia de Respiração Parassimpática 4-7-8',
    breathing_pacer_desc: 'Acompanhe o círculo para desacelerar os batimentos e acalmar o sistema nervoso.',
    start_breathing_btn: 'Iniciar Respiração 4-7-8',
    stop_breathing_btn: 'Parar',
    settings_title: 'Configurações do Santuário e Experiência Sonora',
    settings_subtitle: 'Áudio relaxante a 60–80 BPM, frequências neuro-acústicas e preferências',
    settings_preview_btn: 'Ouvir Voz',
    settings_clear_btn: 'Limpar Histórico',
    settings_done_btn: 'Concluído',
    booking_modal_title: 'Agendar Consulta Clínica',
    booking_modal_subtitle: 'Agende uma consulta com o especialista selecionado',
    booking_confirm_btn: 'Confirmar e Agendar Consulta',
    booking_cancel_btn: 'Cancelar'
  },

  'bn-IN': {
    brand_title: 'মাইন্ডব্রিজ প্রশান্তি কেন্দ্র',
    safety_badge: 'অ-রোগনির্ণয়মূলক সুরক্ষা সক্রিয়',
    sos_btn: '২৪/৭ জরুরি সহায়তা',
    nav_chat: 'মনস্তাত্ত্বিক কথোপকথন ও অনুভূতি শেয়ার',
    nav_providers: 'যাচাইকৃত বিশেষজ্ঞ ও ক্লিনিকাল ডিরেক্টরি',
    nav_insights: 'মানসিক অবস্থার বিশ্লেষণ ও সারাংশ',
    nav_breathing: '৪-৭-৮ শ্বাস-প্রশ্বাসের গতি নিয়ন্ত্রক',
    nav_soundscapes: 'নিরাময়মূলক সুর ও ধ্বনি (৬০-৮০ BPM)',
    nav_settings: 'সেটিংস, সঙ্গীত ও অডিও ক্যালিব্রেশন',
    dock_badge_verified: '৫ জন যাচাইকৃত',
    greeting: 'নমস্কার, বন্ধু',
    hero_title: 'আজ আমি কীভাবে আপনাকে সাহায্য করতে পারি?',
    hero_subtitle: 'আমি আপনার মনের কথা শোনার জন্য এবং মানসিক স্বস্তির জন্য এখানে উপস্থিত আছি।',
    console_clarity: 'মাইন্ডব্রিজের সাথে মনের স্পষ্টতা ও প্রশান্তি পান · অ-রোগনির্ণয়মূলক',
    co_regulation: 'সহ-নিয়ন্ত্রণ সক্রিয়',
    input_placeholder: 'আপনার মনের কথা নিঃসংকোচে লিখুন...',
    tool_voice: 'কণ্ঠস্বর',
    voice_companion_active: 'দ্বিমুখী ভয়েস সঙ্গী মোড সক্রিয়',
    voice_companion_listening: 'শুনছি... স্বাভাবিকভাবে কথা বলুন',
    voice_companion_analyzing: 'আপনার ভাবনা বিশ্লেষণ করা হচ্ছে...',
    voice_companion_speaking: 'মাইন্ডব্রিজ কথা বলছে...',
    voice_companion_exit: 'ভয়েস বন্ধ করুন',
    tool_climate: 'মনোভাব',
    tool_somatic: 'শারীরিক অনুভূতি',
    tool_past: 'অতীত অনুধ্যান',
    music_off: 'সঙ্গীত: বন্ধ',
    music_on: 'সঙ্গীত: চালু',
    prompt_past_title: 'অতীত জীবন ও স্মৃতি',
    prompt_past_desc: 'শৈশবের মধুর স্মৃতি, জীবনের মোড় ও মানসিক অবস্থা নিয়ে ভাবুন।',
    prompt_past_msg: 'আমি আমার অতীত ও শৈশবের স্মৃতি নিয়ে আলোচনা ও অনুধ্যান করতে চাই।',
    prompt_surprise_title: 'প্রশান্তিদায়ক ভাবনা!',
    prompt_surprise_desc: 'একটি সুন্দর প্রতিফলন বা মাইন্ডফুলনেস অনুশীলন শেয়ার করুন।',
    prompt_surprise_msg: 'আমাকে একটি প্রশান্তিদায়ক মাইন্ডফুলনেস ভাবনা বা শান্ত করার ব্যায়াম জানান।',
    prompt_somatic_title: 'শারীরিক চাপমুক্তি',
    prompt_somatic_desc: 'বুকের ভারীভাব ও অতিরিক্ত চিন্তা দূর করার উপায় জানান।',
    prompt_somatic_msg: 'শরীরের ক্লান্তি ও বুকের ভারীভাব দূর করার কার্যকরী উপায় সম্পর্কে আমাকে জানান।',
    prompt_specialist_title: 'বিশেষজ্ঞের পরামর্শ',
    prompt_specialist_desc: 'অভিজ্ঞ মনোবিজ্ঞানী ও মনোরোগ বিশেষজ্ঞদের সাথে যোগাযোগ করুন।',
    mood_reflective: '🍃 চিন্তাশীল ও শান্ত',
    mood_overwhelmed: '🌪️ মানসিক চাপে বিপর্যস্ত',
    mood_anxious: '⚡ উদ্বিগ্ন ও অস্থির',
    mood_heavy: '🌧️ ভারী মন / বিষণ্ণ',
    mood_sleep: '🌙 ঘুমে সমস্যা',
    mood_hopeful: '☀️ আশাবাদী ও ইতিবাচক',
    mood_prompts: {
      reflective: "আমি নিজের মতো করে একটু শান্তভাবে মনের চিন্তাগুলো বুঝতে ও আলোচনা করতে চাই।",
      overwhelmed: "আমি কাজের চাপ, ক্লান্তি এবং অতিরিক্ত মানসিক চাপে খুব বিপর্যস্ত অনুভব করছি।",
      anxious: "আমার এই মুহূর্তে খুব অস্থিরতা, উদ্বেগ ও মানসিক অশান্তি অনুভব হচ্ছে।",
      heavy: "আমার মন খুব ভারাক্রান্ত, বিষণ্ণ এবং ক্লান্ত লাগছে।",
      sleep: "আমার রাতে ভালো ঘুম হচ্ছে না, অনিদ্রা ও অতিরিক্ত চিন্তায় কষ্ট পাচ্ছি।",
      hopeful: "আমি আজ আগের চেয়ে কিছুটা শান্ত, আশাবাদী ও স্বস্তিবোধ করছি।"
    },
    somatic_mind: '🧠 মাথায় অতিরিক্ত চিন্তা ও চাপ',
    somatic_chest: '🫁 বুকে ভারী অনুভূতি ও টান',
    somatic_neck: '🦴 ঘাড় ও কাঁধের পেশিতে টান',
    somatic_stomach: '🌊 পেটে অস্বস্তি ও উৎকণ্ঠা',
    somatic_body: '🔋 শরীর জুড়ে তীব্র ক্লান্তি',
    somatic_prompts: {
      mind: "আমার মাথায় প্রচণ্ড চাপ ও অনিয়ন্ত্রিত চিন্তা ঘুরপাক খাচ্ছে।",
      chest: "আমার বুকে চাপ ও নিশ্বাস নিতে কিছুটা অস্বস্তি লাগছে।",
      neck: "আমার ঘাড় ও কাঁধে অতিরিক্ত টান ও শারীরিক অস্বস্তি আছে।",
      stomach: "আমার পেটের ভেতরে উদ্বেগজনিত অস্বস্তি ও টান অনুভব হচ্ছে।",
      body: "আমার সারা শরীর প্রচণ্ড ক্লান্ত ও অবসাদগ্রস্ত লাগছে।"
    },
    dir_title: 'যাচাইকৃত মানসিক স্বাস্থ্য বিশেষজ্ঞগণ',
    dir_subtitle: 'লাইসেন্সপ্রাপ্ত মনোবিজ্ঞানী ও মনোরোগ বিশেষজ্ঞদের সাথে ব্যক্তিগত পরামর্শ নিন।',
    filter_reset_btn: 'রিসেট',
    book_btn: 'পরামর্শ বুক করুন',
    insights_title: 'মানসিক অবস্থা ও সেশনের সারাংশ',
    insights_subtitle: 'আপনার কথোপকথন থেকে প্রস্তুতকৃত সম্পূর্ণ ব্যক্তিগত স্বাস্থ্য সারাংশ।',
    export_btn: 'ডাক্তারের জন্য রিপোর্ট ডাউনলোড করুন (.txt)',
    metric_stress_label: 'ব্যক্তিগত মানসিক চাপ সূচক',
    metric_stress_hint: 'কথোপকথনের ভাষা ও শারীরিক লক্ষণের ভিত্তিতে প্রস্তুত।',
    metric_tone_label: 'প্রধান মানসিক সুর',
    metric_tone_hint: 'রিয়েল-টাইম অনুভূতি মূল্যায়ন।',
    metric_sleep_label: 'ঘুম ও বিশ্রামের মান',
    metric_sleep_hint: 'ব্যবহারকারীর নিজস্ব ঘুম ট্র্যাকিং।',
    narrative_heading: 'সেশনের মূল মানসিক সারাংশ',
    themes_title: 'আলোচিত প্রধান বিষয়সমূহ:',
    steps_title: 'প্রস্তাবিত প্রশান্তিদায়ক পদক্ষেপ:',
    sos_hero_title: '২৪/৭ তাৎক্ষণিক সংকটকালীন সহায়তা কেন্দ্র',
    sos_hero_subtitle: 'আপনি একা নন। যেকোনো কঠিন সময়ে বিনামূল্যে এবং সম্পূর্ণ গোপনীয় পেশাদার সহায়তা ২৪/৭ উপলব্ধ।',
    breathing_pacer_title: '৪-৭-৮ স্নায়ু-শান্ত শ্বাসক্রিয়া নিয়ন্ত্রক',
    breathing_pacer_desc: 'হৃদস্পন্দন শান্ত করতে এবং স্নায়ুতন্ত্র শিথিল করতে বৃত্তের তাল অনুসরণ করুন।',
    start_breathing_btn: '৪-৭-৮ শ্বাসক্রিয়া শুরু করুন',
    stop_breathing_btn: 'থামুন',
    settings_title: 'প্রশান্তি কেন্দ্র সেটিংস ও অডিও অভিজ্ঞতা',
    settings_subtitle: '৬০–৮০ BPM নিরাময়ী সুর, নিউরো-অ্যাকোস্টিক তরঙ্গ ও পছন্দসমূহ',
    settings_preview_btn: 'কণ্ঠস্বর শুনুন',
    settings_clear_btn: 'ইতিহাস মুছুন',
    settings_done_btn: 'সম্পন্ন',
    booking_modal_title: 'বিশেষজ্ঞের অ্যাপয়েন্টমেন্ট নির্ধারণ করুন',
    booking_modal_subtitle: 'আপনার নির্বাচিত চিকিৎসকের সাথে সরাসরি সময় বুক করুন',
    booking_confirm_btn: 'নিশ্চিত করুন ও বুক করুন',
    booking_cancel_btn: 'বাতিল'
  }
};

function initLanguageSystem() {
  const langSelect = document.getElementById('languageSelect');
  const settingsLangSelect = document.getElementById('settingsLanguageSelect');

  const savedLang = localStorage.getItem('mb_language') || 'en-US';
  applyLanguage(savedLang);

  if (langSelect) {
    langSelect.addEventListener('change', (e) => {
      applyLanguage(e.target.value);
    });
  }

  if (settingsLangSelect) {
    settingsLangSelect.addEventListener('change', (e) => {
      applyLanguage(e.target.value);
    });
  }
}

function applyLanguage(lang) {
  state.selectedLanguage = lang || 'en-US';
  localStorage.setItem('mb_language', state.selectedLanguage);

  const t = I18N_DICTIONARY[state.selectedLanguage] || I18N_DICTIONARY['en-US'];

  // 1. Sync Select dropdowns
  const langSelect = document.getElementById('languageSelect');
  const settingsLangSelect = document.getElementById('settingsLanguageSelect');
  if (langSelect) langSelect.value = state.selectedLanguage;
  if (settingsLangSelect) settingsLangSelect.value = state.selectedLanguage;

  // 2. STT Recognition language
  if (state.recognition) {
    state.recognition.lang = state.selectedLanguage;
  }

  // 3. Header
  const brandPill = document.querySelector('.stage-brand-pill');
  if (brandPill) brandPill.textContent = t.brand_title;

  const safetyBadge = document.querySelector('.stage-safety-badge');
  if (safetyBadge) safetyBadge.innerHTML = `<i data-lucide="shield-check"></i> ${t.safety_badge}`;

  const sosBtn = document.getElementById('headerSosBtn');
  if (sosBtn) sosBtn.innerHTML = `<span class="sos-dot"></span> ${t.sos_btn}`;

  // 4. Sidebar Dock Tooltips & Badges
  const navChat = document.getElementById('navBtn-chat');
  if (navChat) navChat.setAttribute('title', t.nav_chat);

  const navProviders = document.getElementById('navBtn-providers');
  if (navProviders) navProviders.setAttribute('title', t.nav_providers);

  const dockBadge = document.querySelector('.dock-badge');
  if (dockBadge) dockBadge.textContent = t.dock_badge_verified;

  const navInsights = document.getElementById('navBtn-insights');
  if (navInsights) navInsights.setAttribute('title', t.nav_insights);

  const navBreathing = document.getElementById('navBtn-breathing') || document.getElementById('navBtn-emergency');
  if (navBreathing) navBreathing.setAttribute('title', t.nav_breathing);

  const soundscapeBtn = document.getElementById('soundscapeBtn');
  if (soundscapeBtn) soundscapeBtn.setAttribute('title', t.nav_soundscapes);

  const settingsBtn = document.getElementById('headerSettingsBtn');
  if (settingsBtn) settingsBtn.setAttribute('title', t.nav_settings);

  // 5. Chat Hero Stage
  const userGreeting = document.querySelector('.hero-user-greeting');
  if (userGreeting) userGreeting.textContent = t.greeting;

  const mainHeading = document.querySelector('.hero-main-heading');
  if (mainHeading) mainHeading.textContent = t.hero_title;

  const subtitle = document.querySelector('.hero-subtitle');
  if (subtitle) subtitle.textContent = t.hero_subtitle;

  // 6. Console Status Bar
  const consoleStatus = document.querySelector('.console-status-left span');
  if (consoleStatus) consoleStatus.textContent = t.console_clarity;

  const coRegText = document.querySelector('.co-regulation-mini span:last-child');
  if (coRegText) coRegText.textContent = t.co_regulation;

  const chatInput = document.getElementById('chatInput');
  if (chatInput) chatInput.placeholder = t.input_placeholder;

  // 7. Console Tool Pills
  const micSpan = document.querySelector('#micBtn span');
  if (micSpan) micSpan.textContent = t.tool_voice;

  const moodSpan = document.querySelector('#quickMoodBtn span');
  if (moodSpan) moodSpan.textContent = t.tool_climate;

  const somaticSpan = document.querySelector('#quickSomaticBtn span');
  if (somaticSpan) somaticSpan.textContent = t.tool_somatic;

  const pastLifeSpan = document.querySelector('#quickPastLifeBtn span');
  if (pastLifeSpan) pastLifeSpan.textContent = t.tool_past || 'Past Reflection';

  const soundLabel = document.getElementById('soundscapeLabel');
  if (soundLabel) soundLabel.textContent = state.soundPlaying ? t.music_on : t.music_off;

  // 8. Suggestion Prompt Cards (4 total)
  const card1 = document.querySelector('.prompt-suggestion-card:nth-child(1)');
  if (card1) {
    const title = card1.querySelector('.prompt-card-title');
    const desc = card1.querySelector('.prompt-card-desc');
    if (title) title.textContent = t.prompt_past_title || 'Past Life & Memories';
    if (desc) desc.textContent = t.prompt_past_desc || 'Reflect gently on childhood memories, turning points & mental state.';
    card1.setAttribute('data-prompt', t.prompt_past_msg || 'I want to reflect on my past and childhood memories.');
  }

  const card2 = document.querySelector('.prompt-suggestion-card:nth-child(2)');
  if (card2) {
    const title = card2.querySelector('.prompt-card-title');
    const desc = card2.querySelector('.prompt-card-desc');
    if (title) title.textContent = t.prompt_surprise_title || 'Surprise me!';
    if (desc) desc.textContent = t.prompt_surprise_desc || 'Surprise me with a mindful reflection or grounding exercise.';
    card2.setAttribute('data-prompt', t.prompt_surprise_msg || 'Surprise me with a mindful reflection, grounding exercise, or calming thought.');
  }

  const card3 = document.querySelector('.prompt-suggestion-card:nth-child(3)');
  if (card3) {
    const title = card3.querySelector('.prompt-card-title');
    const desc = card3.querySelector('.prompt-card-desc');
    if (title) title.textContent = t.prompt_somatic_title || 'Somatic release';
    if (desc) desc.textContent = t.prompt_somatic_desc || 'Guide me to release chest tightness, overthinking, or tension.';
    card3.setAttribute('data-prompt', t.prompt_somatic_msg || 'I am feeling stress and physical tension in my body. Can you guide me through releasing it?');
  }

  const card4 = document.querySelector('.prompt-suggestion-card:nth-child(4)');
  if (card4) {
    const title = card4.querySelector('.prompt-card-title');
    const desc = card4.querySelector('.prompt-card-desc');
    if (title) title.textContent = t.prompt_specialist_title || 'Specialist care';
    if (desc) desc.textContent = t.prompt_specialist_desc || 'Connect with verified clinical psychologists & psychiatrists.';
  }

  // 9. Weather Mood Popup
  const moodOpts = document.querySelectorAll('#moodPopupMenu .mood-popup-opt');
  if (moodOpts.length >= 6) {
    moodOpts[0].textContent = t.mood_reflective;
    moodOpts[1].textContent = t.mood_overwhelmed;
    moodOpts[2].textContent = t.mood_anxious;
    moodOpts[3].textContent = t.mood_heavy;
    moodOpts[4].textContent = t.mood_sleep;
    moodOpts[5].textContent = t.mood_hopeful;
    if (t.mood_prompts) {
      moodOpts[0].setAttribute('data-prompt', t.mood_prompts.reflective);
      moodOpts[1].setAttribute('data-prompt', t.mood_prompts.overwhelmed);
      moodOpts[2].setAttribute('data-prompt', t.mood_prompts.anxious);
      moodOpts[3].setAttribute('data-prompt', t.mood_prompts.heavy);
      moodOpts[4].setAttribute('data-prompt', t.mood_prompts.sleep);
      moodOpts[5].setAttribute('data-prompt', t.mood_prompts.hopeful);
    }
  }

  // 10. Somatic Popup
  const somOpts = document.querySelectorAll('.somatic-popup-opt');
  if (somOpts.length >= 5) {
    somOpts[0].textContent = t.somatic_mind;
    somOpts[1].textContent = t.somatic_chest;
    somOpts[2].textContent = t.somatic_neck;
    somOpts[3].textContent = t.somatic_stomach;
    somOpts[4].textContent = t.somatic_body;
    if (t.somatic_prompts) {
      somOpts[0].setAttribute('data-prompt', t.somatic_prompts.mind);
      somOpts[1].setAttribute('data-prompt', t.somatic_prompts.chest);
      somOpts[2].setAttribute('data-prompt', t.somatic_prompts.neck);
      somOpts[3].setAttribute('data-prompt', t.somatic_prompts.stomach);
      somOpts[4].setAttribute('data-prompt', t.somatic_prompts.body);
    }
  }

  // 11. Directory View
  const dirView = document.getElementById('tab-providers');
  if (dirView) {
    const title = dirView.querySelector('.view-title');
    const sub = dirView.querySelector('.view-subtitle');
    const verifiedBadge = dirView.querySelector('.verified-count-badge');
    if (title) title.textContent = t.dir_title;
    if (sub) sub.textContent = t.dir_subtitle;
    if (verifiedBadge) verifiedBadge.innerHTML = `<i data-lucide="check-circle-2"></i> ${t.dock_badge_verified} Online`;

    const resetBtn = document.getElementById('resetFiltersBtn');
    if (resetBtn) resetBtn.innerHTML = `<i data-lucide="rotate-ccw"></i> ${t.filter_reset_btn}`;
  }

  // 12. Emotional Insights View
  const insView = document.getElementById('tab-insights');
  if (insView) {
    const title = insView.querySelector('.view-title');
    const sub = insView.querySelector('.view-subtitle');
    const exportBtn = document.getElementById('exportSummaryBtn');
    if (title) title.textContent = t.insights_title;
    if (sub) sub.textContent = t.insights_subtitle;
    if (exportBtn) exportBtn.innerHTML = `<i data-lucide="download"></i> ${t.export_btn}`;

    const metricLabels = insView.querySelectorAll('.metric-label');
    const metricHints = insView.querySelectorAll('.metric-hint');
    if (metricLabels.length >= 3) {
      metricLabels[0].textContent = t.metric_stress_label;
      metricLabels[1].textContent = t.metric_tone_label;
      metricLabels[2].textContent = t.metric_sleep_label;
    }
    if (metricHints.length >= 3) {
      metricHints[0].textContent = t.metric_stress_hint;
      metricHints[1].textContent = t.metric_tone_hint;
      metricHints[2].textContent = t.metric_sleep_hint;
    }

    const narrHeading = insView.querySelector('.narrative-heading');
    if (narrHeading) narrHeading.innerHTML = `<i data-lucide="file-text"></i> ${t.narrative_heading}`;

    const themesTitle = insView.querySelector('.themes-title');
    if (themesTitle) themesTitle.textContent = t.themes_title;

    const nextStepsTitle = insView.querySelector('.next-steps-block .themes-title');
    if (nextStepsTitle) nextStepsTitle.textContent = t.steps_title;
  }

  // 13. Emergency SOS View & Breathing Pacer
  const emergView = document.getElementById('tab-emergency');
  if (emergView) {
    const sosTitle = emergView.querySelector('.sos-hero-title');
    const sosSub = emergView.querySelector('.sos-hero-subtitle');
    if (sosTitle) sosTitle.textContent = t.sos_hero_title;
    if (sosSub) sosSub.textContent = t.sos_hero_subtitle;

    const breathTitle = emergView.querySelector('.breathing-card-title');
    const breathDesc = emergView.querySelector('.breathing-card-desc');
    const startBtn = document.getElementById('startBreathingBtn');
    const stopBtn = document.getElementById('stopBreathingBtn');
    if (breathTitle) breathTitle.innerHTML = `<i data-lucide="wind"></i> ${t.breathing_pacer_title}`;
    if (breathDesc) breathDesc.textContent = t.breathing_pacer_desc;
    if (startBtn) startBtn.textContent = t.start_breathing_btn;
    if (stopBtn) stopBtn.textContent = t.stop_breathing_btn;
  }

  // 14. Settings Modal
  const setModal = document.getElementById('settingsModal');
  if (setModal) {
    const title = setModal.querySelector('.modal-title');
    const sub = setModal.querySelector('.modal-subtitle');
    const doneBtn = document.getElementById('doneSettingsBtn');
    const previewBtn = document.getElementById('previewVoiceBtn');
    const clearBtn = document.getElementById('settingsClearBtn');
    if (title) title.textContent = t.settings_title;
    if (sub) sub.textContent = t.settings_subtitle;
    if (doneBtn) doneBtn.textContent = t.settings_done_btn;
    if (previewBtn) previewBtn.innerHTML = `<i data-lucide="volume-2"></i> ${t.settings_preview_btn}`;
    if (clearBtn) clearBtn.innerHTML = `<i data-lucide="trash-2"></i> ${t.settings_clear_btn}`;
  }

  // 15. Re-render providers with localized CTA buttons
  if (typeof renderProvidersGrid === 'function' && state.providers && state.providers.length > 0) {
    renderProvidersGrid(state.providers);
  }

  // 16. Voice Companion Bar
  syncVoiceCompanionBarLanguage();

  if (window.lucide) window.lucide.createIcons();
}

function initVoicePerspectives() {
  const perspBtn = document.getElementById('quickPerspBtn');
  const popupMenu = document.getElementById('perspectivePopupMenu');
  const label = document.getElementById('activePerspectiveLabel');

  function updateLabel(val) {
    if (!label) return;
    if (val === 'bn') label.textContent = 'Perspective: Bengali';
    else if (val === 'en') label.textContent = 'Perspective: English';
    else label.textContent = 'Perspective: Auto';
  }

  updateLabel(state.activeVoicePerspective);

  if (popupMenu) {
    popupMenu.querySelectorAll('.persp-popup-opt').forEach(opt => {
      if (opt.getAttribute('data-persp') === state.activeVoicePerspective) {
        opt.classList.add('active');
      } else {
        opt.classList.remove('active');
      }

      opt.addEventListener('click', (e) => {
        e.stopPropagation();
        const val = opt.getAttribute('data-persp');
        state.activeVoicePerspective = val;
        localStorage.setItem('mb_voice_perspective', val);
        popupMenu.querySelectorAll('.persp-popup-opt').forEach(o => o.classList.remove('active'));
        opt.classList.add('active');
        updateLabel(val);
        closeAllConsolePopups();
      });
    });
  }

  if (perspBtn && popupMenu) {
    perspBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const isVisible = popupMenu.style.display === 'flex';
      closeAllConsolePopups();
      if (!isVisible) {
        popupMenu.style.display = 'flex';
      }
    });
  }
}

// ==========================================================================
// CLINICAL SCREENING ASSESSMENT CONTROLLER (100 RESEARCH-GROUNDED INQUIRIES)
// ==========================================================================

const screenerState = {
  sessionId: localStorage.getItem('mb_screener_session_id') || null,
  currentQuestion: null,
  currentIndex: 0,
  totalQuestions: 100,
  inputMode: 'voice', // Default: Voice Preferred
  isRecording: false,
  recognition: null,
  rawTranscript: '',
  selectedOptionIndex: null,
  selectedVsaqValue: null,
  isCrisisHalted: false,
  isCompleted: false,
  evaluationResult: null,
  isHandsFreeActive: true,
  isDoctorSpeaking: false,
  silenceTimer: null,
  doctorSpeechQueue: [],
  spokenPrompt: '',
  webSpeechBlocked: false
};

let screenerAudioContext = null;
let screenerMediaStream = null;
let screenerScriptProcessor = null;
let screenerAudioBuffers = [];
let screenerIsUserSpeaking = false;
let screenerSilenceStartTime = 0;
let screenerTranscribing = false;
let screenerDoctorTtsWatchdog = null;

function warmUpScreenerAudioContext() {
  const AudioContextClass = window.AudioContext || window.webkitAudioContext;
  if (!AudioContextClass) return;
  if (!screenerAudioContext || screenerAudioContext.state === 'closed') {
    screenerAudioContext = new AudioContextClass();
  }
  if (screenerAudioContext.state === 'suspended') {
    screenerAudioContext.resume().catch(() => {});
  }
}
let screenerMediaRecorder = null;
let screenerMediaChunks = [];
let screenerMaxDurationTimer = null;
let screenerUseWebSpeechMode = false;
let screenerMimeType = '';

function getBestMediaRecorderMimeType() {
  const candidates = [
    'audio/webm;codecs=opus',
    'audio/webm',
    'audio/ogg;codecs=opus',
    'audio/mp4',
    'audio/wav'
  ];
  if (window.MediaRecorder && typeof MediaRecorder.isTypeSupported === 'function') {
    for (const c of candidates) {
      if (MediaRecorder.isTypeSupported(c)) return c;
    }
  }
  return '';
}

function toggleWebSpeechMode() {
  screenerUseWebSpeechMode = !screenerUseWebSpeechMode;
  const label = document.getElementById('webSpeechLabel');
  const btn = document.getElementById('screenerWebSpeechToggleBtn');
  if (label) {
    label.textContent = screenerUseWebSpeechMode 
      ? 'Engine: Web Speech (Browser)' 
      : 'Engine: Whisper AI (Server)';
  }
  if (btn) btn.classList.toggle('active', screenerUseWebSpeechMode);
}

async function ensureScreenerMicPermission() {
  warmUpScreenerAudioContext();
  const errorBanner = document.getElementById('screenerMicErrorBanner');
  if (errorBanner) errorBanner.style.display = 'none';

  if (screenerMediaStream && screenerMediaStream.active) {
    return screenerMediaStream;
  }
  if (state.micStream && state.micStream.active) {
    screenerMediaStream = state.micStream;
    return screenerMediaStream;
  }

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    if (errorBanner) {
      errorBanner.innerHTML = '<i data-lucide="alert-triangle"></i><span>Microphone access is not supported in this browser. Please use Chrome, Edge, or Firefox.</span>';
      errorBanner.style.display = 'flex';
      if (window.lucide) window.lucide.createIcons();
    }
    return null;
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true
      }
    });
    screenerMediaStream = stream;
    state.micStream = stream;
    if (errorBanner) errorBanner.style.display = 'none';
    return stream;
  } catch (err) {
    console.warn('[Screener Mic Access Error]:', err);
    let msg = 'Could not access microphone: ' + (err.message || err.name);
    if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
      msg = 'Microphone permission was denied. Please click the permissions icon next to the URL in your browser bar and select "Allow".';
    } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
      msg = 'No microphone device was detected. Please check that your microphone is plugged in.';
    } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
      msg = 'Microphone is currently in use by another tab or app.';
    }
    if (errorBanner) {
      errorBanner.innerHTML = `<i data-lucide="alert-triangle"></i><span>${msg}</span>`;
      errorBanner.style.display = 'flex';
      if (window.lucide) window.lucide.createIcons();
    }
    return null;
  }
}

function setScreenerInputMode(mode) {
  screenerState.inputMode = mode;
  const voiceTab = document.getElementById('inputTabVoice');
  const textTab = document.getElementById('inputTabText');
  const voiceContainer = document.getElementById('screenerVoiceContainer');
  const textContainer = document.getElementById('screenerTextContainer');

  if (mode === 'voice') {
    if (voiceTab) voiceTab.classList.add('active');
    if (textTab) textTab.classList.remove('active');
    if (voiceContainer) voiceContainer.style.display = 'block';
    if (textContainer) textContainer.style.display = 'none';

    ensureScreenerMicPermission().catch(() => {});

    // When entering voice mode, speak question if not already speaking or recording
    if (screenerState.currentQuestion && !screenerState.isDoctorSpeaking && !screenerState.isRecording && !screenerState.isCrisisHalted && !screenerState.isCompleted) {
      speakDoctorVoice(screenerState.spokenPrompt || screenerState.currentQuestion.question_text);
    } else if (!screenerState.isDoctorSpeaking && !screenerState.isRecording) {
      startScreenerRecording();
    }
  } else {
    // If leaving voice mode, halt active doctor voice and mic recording
    stopDoctorVoice();
    stopScreenerRecording();

    if (voiceTab) voiceTab.classList.remove('active');
    if (textTab) textTab.classList.add('active');
    if (voiceContainer) voiceContainer.style.display = 'none';
    if (textContainer) textContainer.style.display = 'block';
  }
}

async function loadScreenerSession(forceNew = false) {
  try {
    const progressCard = document.getElementById('screenerProgressCard');
    const questionCard = document.getElementById('screenerQuestionCard');
    const resultsStage = document.getElementById('screenerResultsStage');
    const crisisOverlay = document.getElementById('screenerCrisisOverlay');

    if (crisisOverlay) crisisOverlay.style.display = 'none';
    if (resultsStage) resultsStage.style.display = 'none';
    if (progressCard) progressCard.style.display = 'block';
    if (questionCard) questionCard.style.display = 'flex';

    const res = await fetch('/api/screener/session/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: state.userId,
        force_new: forceNew
      })
    });

    const data = await res.json();
    if (data.status === 'success') {
      screenerState.sessionId = data.session_id;
      localStorage.setItem('mb_screener_session_id', data.session_id);
      screenerState.currentIndex = data.current_index;
      screenerState.totalQuestions = data.total_questions || 100;

      if (data.current_question) {
        screenerState.currentQuestion = data.current_question;
        renderScreenerQuestion(data.current_question, data.current_index, screenerState.totalQuestions);
      } else {
        fetchCurrentScreenerQuestion();
      }
    }
  } catch (err) {
    console.error('[Screener Session Error]:', err);
  }
}

async function fetchCurrentScreenerQuestion() {
  if (!screenerState.sessionId) return;
  try {
    const res = await fetch(`/api/screener/question?session_id=${encodeURIComponent(screenerState.sessionId)}`);
    const data = await res.json();
    if (data.status === 'completed') {
      evaluateAndShowResults();
    } else if (data.status === 'success' && data.question) {
      screenerState.currentIndex = data.current_index;
      screenerState.currentQuestion = data.question;
      renderScreenerQuestion(data.question, data.current_index, data.total_questions);
    }
  } catch (err) {
    console.error('[Fetch Question Error]:', err);
  }
}

function renderScreenerQuestion(q, idx, total) {
  screenerState.currentQuestion = q;
  screenerState.selectedOptionIndex = null;
  screenerState.selectedVsaqValue = null;
  screenerState.rawTranscript = '';
  screenerState.spokenPrompt = q.spoken_prompt || q.question_text;

  // Update Progress Bar & Telemetry
  const stepTitle = document.getElementById('screenerStepTitle');
  const percentText = document.getElementById('screenerPercentText');
  const progressBar = document.getElementById('screenerProgressBar');
  const badgeProgress = document.getElementById('screenerProgressBadge');
  const domainBadge = document.getElementById('screenerDomainBadge');
  const sourceBadge = document.getElementById('screenerSourceBadge');
  const typeBadge = document.getElementById('screenerTypeBadge');
  const safetyBadge = document.getElementById('screenerSafetyBadge');
  const questionHeading = document.getElementById('screenerQuestionHeading');

  const currNum = (idx || 0) + 1;
  const pct = Math.min(100, Math.round(((idx || 0) / (total || 100)) * 100));

  if (stepTitle) stepTitle.textContent = `Question ${currNum} of ${total || 100}`;
  if (percentText) percentText.textContent = `${pct}% Completed`;
  if (progressBar) progressBar.style.width = `${Math.max(1, pct)}%`;
  if (badgeProgress) badgeProgress.textContent = `${currNum}/${total || 100}`;

  const domainNames = {
    mood: 'Mood & Depressive Spectrum',
    anxiety: 'Anxiety & Somatic Tension',
    stress: 'Stress, Burnout & Coping',
    sleep: 'Sleep Quality & Restoration',
    functioning: 'Daily Functioning & Executive Flow',
    safety: 'Safety & Risk Assessment',
    protective: 'Protective Factors & Anchors'
  };

  if (domainBadge) domainBadge.textContent = domainNames[q.domain] || q.domain;
  if (sourceBadge) sourceBadge.textContent = q.source_paper ? q.source_paper.split('(')[0].trim() : 'Clinical Psychometrics';

  if (typeBadge) {
    typeBadge.textContent = q.question_type === 'MCQ' ? 'Multiple Choice (MCQ)' : 'Very Short Answer (VSAQ)';
  }

  if (safetyBadge) {
    safetyBadge.style.display = q.is_safety_question ? 'inline-flex' : 'none';
  }

  if (questionHeading) {
    questionHeading.textContent = q.question_text;
  }

  // Clear Text & Transcript inputs
  const transcriptInput = document.getElementById('screenerTranscriptInput');
  const textInput = document.getElementById('screenerTextInput');
  const charCount = document.getElementById('transcriptCharCount');

  if (transcriptInput) transcriptInput.value = '';
  if (textInput) textInput.value = '';
  if (charCount) charCount.textContent = '0 words';

  // Render Input Controls according to type
  const mcqGrid = document.getElementById('screenerMcqOptions');
  const vsaqStage = document.getElementById('screenerVsaqStage');

  if (q.question_type === 'MCQ' && q.options && q.options.length > 0) {
    if (mcqGrid) {
      mcqGrid.style.display = 'grid';
      mcqGrid.innerHTML = '';
      q.options.forEach((opt, optIdx) => {
        const tile = document.createElement('div');
        tile.className = 'mcq-option-tile';
        tile.id = `mcq-opt-${optIdx}`;
        tile.innerHTML = `
          <div class="mcq-label-chip">${opt.label || String.fromCharCode(65 + optIdx)}</div>
          <div class="mcq-option-text">${opt.text}</div>
        `;
        tile.addEventListener('click', () => selectMcqOption(optIdx, opt.text, opt.score));
        mcqGrid.appendChild(tile);
      });
    }
    if (vsaqStage) vsaqStage.style.display = 'none';
  } else {
    // VSAQ
    if (mcqGrid) mcqGrid.style.display = 'none';
    if (vsaqStage) {
      vsaqStage.style.display = 'flex';
      const quickChips = document.getElementById('screenerQuickChips');
      if (quickChips) {
        quickChips.innerHTML = '';
        const fmt = q.answer_format || 'Likert_0_3';
        let chips = [];
        if (fmt === 'Likert_0_3') {
          chips = [
            { label: '0: Not at all', val: 'Not at all' },
            { label: '1: Several days', val: 'Several days' },
            { label: '2: More than half the days', val: 'More than half the days' },
            { label: '3: Nearly every day', val: 'Nearly every day' }
          ];
        } else if (fmt === 'yes_no') {
          chips = [
            { label: 'Yes', val: 'Yes' },
            { label: 'No', val: 'No' }
          ];
        } else if (fmt === 'numeric_0_10') {
          for (let n = 0; n <= 10; n += 2) {
            chips.push({ label: `${n}/10`, val: `${n}` });
          }
        } else if (fmt === 'numeric_hours') {
          chips = [
            { label: '5 hrs', val: '5' },
            { label: '6 hrs', val: '6' },
            { label: '7 hrs', val: '7' },
            { label: '8 hrs', val: '8' },
            { label: '9+ hrs', val: '9' }
          ];
        }

        chips.forEach((c) => {
          const btn = document.createElement('button');
          btn.type = 'button';
          btn.className = 'vsaq-chip-btn';
          btn.textContent = c.label;
          btn.addEventListener('click', () => selectVsaqChip(c.val, btn));
          quickChips.appendChild(btn);
        });
      }
    }
  }

  // Ensure default mode is Voice as requested
  screenerState.inputMode = 'voice';
  const voiceTab = document.getElementById('inputTabVoice');
  const textTab = document.getElementById('inputTabText');
  const voiceContainer = document.getElementById('screenerVoiceContainer');
  const textContainer = document.getElementById('screenerTextContainer');
  if (voiceTab) voiceTab.classList.add('active');
  if (textTab) textTab.classList.remove('active');
  if (voiceContainer) voiceContainer.style.display = 'block';
  if (textContainer) textContainer.style.display = 'none';

  ensureScreenerMicPermission().catch(() => {});

  // Automatic Doctor Speech for new inquiry: speaks the question and arms mic hands-free
  if (screenerState.inputMode === 'voice' && screenerState.isHandsFreeActive && !screenerState.isCrisisHalted && !screenerState.isCompleted) {
    // Use 600ms base delay for first question to allow speechSynthesis voices to load;
    // subsequent questions use 350ms since voices are already cached.
    const isFirstQuestion = (idx === 0 || idx === undefined);
    const speakDelay = isFirstQuestion ? 600 : 350;

    setTimeout(() => {
      if (screenerState.inputMode === 'voice' && !screenerState.isCrisisHalted && !screenerState.isCompleted) {
        const textToSpeak = screenerState.spokenPrompt || (screenerState.currentQuestion && screenerState.currentQuestion.question_text);
        speakDoctorVoice(textToSpeak);
      }
    }, speakDelay);
  }

  if (window.lucide) window.lucide.createIcons();
}

function selectMcqOption(optIndex, optText, optScore) {
  screenerState.selectedOptionIndex = optIndex;
  const tiles = document.querySelectorAll('.mcq-option-tile');
  tiles.forEach((t, i) => {
    t.classList.toggle('selected', i === optIndex);
  });

  const transcriptInput = document.getElementById('screenerTranscriptInput');
  const textInput = document.getElementById('screenerTextInput');
  if (transcriptInput) transcriptInput.value = optText;
  if (textInput) textInput.value = optText;

  updateTranscriptWordCount(optText);
}

function selectVsaqChip(val, chipBtn) {
  screenerState.selectedVsaqValue = val;
  const chips = document.querySelectorAll('.vsaq-chip-btn');
  chips.forEach(c => c.classList.remove('selected'));
  if (chipBtn) chipBtn.classList.add('selected');

  const transcriptInput = document.getElementById('screenerTranscriptInput');
  const textInput = document.getElementById('screenerTextInput');
  if (transcriptInput) transcriptInput.value = val;
  if (textInput) textInput.value = val;

  updateTranscriptWordCount(val);
}

function updateTranscriptWordCount(text) {
  const charCount = document.getElementById('transcriptCharCount');
  if (charCount) {
    const words = (text || '').trim().split(/\s+/).filter(Boolean);
    charCount.textContent = `${words.length} word${words.length === 1 ? '' : 's'}`;
  }
}

// Editable transcript live input sync
document.addEventListener('input', (e) => {
  if (e.target && e.target.id === 'screenerTranscriptInput') {
    updateTranscriptWordCount(e.target.value);
  }
});

function clearScreenerTranscript() {
  const transcriptInput = document.getElementById('screenerTranscriptInput');
  const textInput = document.getElementById('screenerTextInput');
  if (transcriptInput) transcriptInput.value = '';
  if (textInput) textInput.value = '';
  updateTranscriptWordCount('');
}

// ==========================================================================
// DR. MINDBRIDGE HANDS-FREE VOICE DOCTOR & EVALUATION ENGINE
// ==========================================================================

function stopDoctorVoice() {
  if (screenerDoctorTtsWatchdog) {
    clearTimeout(screenerDoctorTtsWatchdog);
    screenerDoctorTtsWatchdog = null;
  }
  screenerState.isDoctorSpeaking = false;
  screenerState.doctorSpeechQueue = [];
  if (window.speechSynthesis) {
    try {
      window.speechSynthesis.cancel();
    } catch (e) {}
  }
  const micWrap = document.getElementById('screenerMicWrap');
  if (micWrap) micWrap.classList.remove('ai-speaking');
  const micIcon = document.getElementById('screenerMicIcon');
  if (micIcon) micIcon.setAttribute('data-lucide', 'mic');
  if (window.lucide) window.lucide.createIcons();
}

/**
 * Ensures speechSynthesis voices are loaded before attempting TTS.
 * Chrome/Edge load voices asynchronously — getVoices() returns [] until
 * the 'voiceschanged' event fires (can take 500ms-2s on first call).
 * This function returns a Promise that resolves when voices are available.
 */
function ensureVoicesLoaded() {
  return new Promise((resolve) => {
    if (!window.speechSynthesis) {
      resolve([]);
      return;
    }

    const voices = window.speechSynthesis.getVoices();
    if (voices && voices.length > 0) {
      resolve(voices);
      return;
    }

    // Voices not loaded yet — wait for the voiceschanged event
    let resolved = false;
    const onVoicesChanged = () => {
      if (resolved) return;
      resolved = true;
      window.speechSynthesis.removeEventListener('voiceschanged', onVoicesChanged);
      resolve(window.speechSynthesis.getVoices() || []);
    };

    window.speechSynthesis.addEventListener('voiceschanged', onVoicesChanged);

    // Safety timeout: if voiceschanged never fires (some browsers), resolve after 2s anyway
    setTimeout(() => {
      if (!resolved) {
        resolved = true;
        window.speechSynthesis.removeEventListener('voiceschanged', onVoicesChanged);
        resolve(window.speechSynthesis.getVoices() || []);
      }
    }, 2000);
  });
}

function speakDoctorVoice(spokenText, onComplete) {
  if (!spokenText) {
    if (onComplete) onComplete();
    return;
  }

  ensureScreenerMicPermission().catch(() => {});

  // Halt any active mic recording and any previous speech before doctor talks
  stopScreenerRecording();
  stopDoctorVoice();

  screenerState.isDoctorSpeaking = true;

  const micWrap = document.getElementById('screenerMicWrap');
  const statusTitle = document.getElementById('screenerVoiceStatusTitle');
  const statusSub = document.getElementById('screenerVoiceStatusSub');
  const micIcon = document.getElementById('screenerMicIcon');

  if (micWrap) {
    micWrap.classList.remove('recording');
    micWrap.classList.add('ai-speaking');
  }
  if (statusTitle) statusTitle.textContent = 'Dr. MindBridge Speaking...';
  if (statusSub) statusSub.textContent = 'Please listen to the clinical inquiry. Microphone will open automatically when finished.';
  if (micIcon) micIcon.setAttribute('data-lucide', 'volume-2');
  if (window.lucide) window.lucide.createIcons();

  if (typeof duckBackgroundAudio === 'function') {
    duckBackgroundAudio(true);
  }

  const currentLang = state.selectedLanguage || 'en-US';
  const clean = (typeof humanizeTextForSpeech === 'function')
    ? humanizeTextForSpeech(spokenText, currentLang)
    : spokenText.replace(/[*_#]/g, '').trim();

  // Watchdog timer: if speech synthesis is blocked by autoplay or takes too long, never starve mic
  const words = clean.split(/\s+/).filter(Boolean).length;
  const timeoutMs = Math.max(3200, words * 380 + 1500);

  if (screenerDoctorTtsWatchdog) {
    clearTimeout(screenerDoctorTtsWatchdog);
  }
  screenerDoctorTtsWatchdog = setTimeout(() => {
    if (screenerState.isDoctorSpeaking) {
      console.warn('[Doctor Speech Watchdog] Timed out waiting for speech end; automatically opening microphone.');
      stopDoctorVoice();
      onDoctorSpeechEnded(onComplete);
    }
  }, timeoutMs);

  if (!window.speechSynthesis) {
    setTimeout(() => {
      onDoctorSpeechEnded(onComplete);
    }, 800);
    return;
  }

  const rawSentences = clean.match(/[^.!?;\n—–]+[.!?;\n—–]+|[^.!?;\n—–]+$/g) || [clean];
  const queue = rawSentences.map(s => s.trim()).filter(Boolean);

  if (!queue.length) {
    onDoctorSpeechEnded(onComplete);
    return;
  }

  screenerState.doctorSpeechQueue = queue;

  function speakNextDoctorClause() {
    if (!screenerState.isDoctorSpeaking || !screenerState.doctorSpeechQueue || !screenerState.doctorSpeechQueue.length) {
      onDoctorSpeechEnded(onComplete);
      return;
    }

    const chunk = screenerState.doctorSpeechQueue.shift();
    const utterance = new SpeechSynthesisUtterance(chunk);
    utterance.lang = currentLang;
    utterance.rate = 0.94; // Calm, clinical doctor cadence
    utterance.pitch = 0.98;

    if (typeof getBestHumanVoice === 'function') {
      const v = getBestHumanVoice(currentLang);
      if (v) utterance.voice = v;
    }

    utterance.onend = () => {
      setTimeout(() => {
        speakNextDoctorClause();
      }, 150);
    };

    utterance.onerror = (e) => {
      console.warn('[Doctor Speech Note]:', e);
      speakNextDoctorClause();
    };

    try {
      if (window.speechSynthesis.paused) {
        window.speechSynthesis.resume();
      }
      window.speechSynthesis.speak(utterance);
    } catch (err) {
      console.warn('[SpeechSynthesis speak error]:', err);
      speakNextDoctorClause();
    }
  }

  // CRITICAL FIX: Ensure voices are loaded before starting speech synthesis.
  // Chrome/Edge load voices asynchronously, so the very first call to
  // speechSynthesis.speak() can silently fail if voices aren't loaded yet.
  ensureVoicesLoaded().then(() => {
    // Re-check state hasn't changed while waiting for voices
    if (!screenerState.isDoctorSpeaking) return;
    speakNextDoctorClause();
  });
}

function onDoctorSpeechEnded(onComplete) {
  if (screenerDoctorTtsWatchdog) {
    clearTimeout(screenerDoctorTtsWatchdog);
    screenerDoctorTtsWatchdog = null;
  }
  screenerState.isDoctorSpeaking = false;
  const micWrap = document.getElementById('screenerMicWrap');
  const statusTitle = document.getElementById('screenerVoiceStatusTitle');
  const statusSub = document.getElementById('screenerVoiceStatusSub');
  const micIcon = document.getElementById('screenerMicIcon');

  if (micWrap) micWrap.classList.remove('ai-speaking');
  if (micIcon) micIcon.setAttribute('data-lucide', 'mic');
  if (statusTitle) statusTitle.textContent = 'Listening... Speak naturally';
  if (statusSub) statusSub.textContent = 'Dr. MindBridge is attuned to your speech. Natural pause automatically advances.';
  if (window.lucide) window.lucide.createIcons();

  if (typeof duckBackgroundAudio === 'function') {
    duckBackgroundAudio(false);
  }

  if (onComplete) {
    onComplete();
  } else if (screenerState.inputMode === 'voice' && screenerState.isHandsFreeActive && !screenerState.isCrisisHalted && !screenerState.isCompleted) {
    // Automatically engage microphone without any manual clicking!
    startScreenerRecording();
  }
}

function toggleScreenerVoiceDoctor() {
  warmUpScreenerAudioContext();
  if (screenerState.isDoctorSpeaking) {
    // Tapping mic cuts off doctor speech immediately (barge-in action)
    stopDoctorVoice();
    startScreenerRecording();
    return;
  }

  if (screenerState.isRecording) {
    // Stop recording and process captured audio
    stopScreenerRecording();
    return;
  }

  startScreenerRecording();
}

function rerecordScreenerAnswer() {
  stopScreenerRecording();
  const transcriptInput = document.getElementById('screenerTranscriptInput');
  const textInput = document.getElementById('screenerTextInput');
  if (transcriptInput) {
    transcriptInput.value = '';
    transcriptInput.style.borderColor = '';
    transcriptInput.style.boxShadow = '';
  }
  if (textInput) textInput.value = '';
  updateTranscriptWordCount('');

  const statusTitle = document.getElementById('screenerVoiceStatusTitle');
  const statusSub = document.getElementById('screenerVoiceStatusSub');
  if (statusTitle) statusTitle.textContent = 'Listening... Speak naturally';
  if (statusSub) statusSub.textContent = 'Dr. MindBridge is ready. Speak your answer aloud.';

  setTimeout(() => {
    startScreenerRecording();
  }, 200);
}
window.rerecordScreenerAnswer = rerecordScreenerAnswer;

function repeatCurrentDoctorQuestion() {
  stopScreenerRecording();
  if (screenerState.spokenPrompt || (screenerState.currentQuestion && screenerState.currentQuestion.question_text)) {
    speakDoctorVoice(screenerState.spokenPrompt || screenerState.currentQuestion.question_text);
  }
}

function toggleHandsFreeAutoAdvance() {
  screenerState.isHandsFreeActive = !screenerState.isHandsFreeActive;
  const btn = document.getElementById('screenerHandsFreeToggleBtn');
  const label = document.getElementById('handsFreeLabel');
  if (btn) btn.classList.toggle('active', screenerState.isHandsFreeActive);
  if (label) label.textContent = `Hands-Free Voice Flow: ${screenerState.isHandsFreeActive ? 'ON' : 'OFF'}`;

  if (screenerState.isHandsFreeActive && !screenerState.isDoctorSpeaking && !screenerState.isRecording && screenerState.inputMode === 'voice') {
    startScreenerRecording();
  }
}

async function startScreenerRecording() {
  if (screenerState.isDoctorSpeaking) return; // Half-duplex guard: never transcribe doctor speech
  if (screenerState.isRecording) return;

  screenerState.isRecording = true;
  screenerState.rawTranscript = '';

  const micWrap = document.getElementById('screenerMicWrap');
  const statusTitle = document.getElementById('screenerVoiceStatusTitle');
  const statusSub = document.getElementById('screenerVoiceStatusSub');
  const micIcon = document.getElementById('screenerMicIcon');
  const errorBanner = document.getElementById('screenerMicErrorBanner');

  if (errorBanner) errorBanner.style.display = 'none';
  if (micWrap) {
    micWrap.classList.remove('ai-speaking');
    micWrap.classList.add('recording');
  }
  if (micIcon) micIcon.setAttribute('data-lucide', 'mic');
  if (window.lucide) window.lucide.createIcons();

  if (statusTitle) statusTitle.textContent = 'Listening... Speak naturally';
  if (statusSub) statusSub.textContent = screenerState.isHandsFreeActive
    ? 'Dr. MindBridge is attuned to your voice. Speak your answer; pause to transcribe.'
    : 'Recording in progress. Speak your answer, then click Confirm Answer or tap mic to stop.';

  // 1. Hardware Microphone Access with Error Handling
  const stream = await ensureScreenerMicPermission();
  if (!stream) {
    screenerState.isRecording = false;
    if (micWrap) micWrap.classList.remove('recording');
    return;
  }

  // 2. Primary Recording Pipeline: MediaRecorder API (WebM/Opus)
  startScreenerMediaRecorder(stream);

  // 3. Parallel Web Audio VAD: drives visual meter rings & natural pause detection
  startScreenerAudioVAD(stream);

  // 4. Optional Web Speech API Fast-Path (if user enabled it and not blocked)
  if (screenerUseWebSpeechMode && !screenerState.webSpeechBlocked) {
    startScreenerWebSpeech();
  }
}

// ==============================================================================
// PRODUCTION VOICERECORDER CLASS (2026 Mobile & Desktop Resilient)
// ==============================================================================

class VoiceRecorder {
  constructor(options = {}) {
    this.stream = null;
    this.mediaRecorder = null;
    this.chunks = [];
    this.mimeType = '';
    this.timeslice = options.timeslice || 1000; // 1-second chunks for mobile stability
    this._isRecording = false;
    this.onStopCallback = null;
    this.maxDurationMs = options.maxDurationMs || 60000;
    this.maxTimer = null;
  }

  isRecording() {
    return this._isRecording;
  }

  async startRecording(stream, onStop) {
    if (this._isRecording) return false;
    this.onStopCallback = onStop;
    this.chunks = [];
    this.stream = stream;

    this.mimeType = getBestMediaRecorderMimeType();
    const recorderOptions = this.mimeType ? { mimeType: this.mimeType } : undefined;

    try {
      this.mediaRecorder = new MediaRecorder(stream, recorderOptions);
    } catch (e) {
      console.warn('[VoiceRecorder] Fallback default MediaRecorder:', e);
      try {
        this.mediaRecorder = new MediaRecorder(stream);
      } catch (err2) {
        console.error('[VoiceRecorder] MediaRecorder not supported on this device:', err2);
        return false;
      }
    }

    this.mediaRecorder.ondataavailable = (event) => {
      // Mobile Safari / iOS fix: ignore 0-byte chunks
      if (event.data && event.data.size > 0) {
        this.chunks.push(event.data);
      }
    };

    this.mediaRecorder.onstop = () => {
      this._isRecording = false;
      if (this.maxTimer) {
        clearTimeout(this.maxTimer);
        this.maxTimer = null;
      }
      const validChunks = this.chunks.filter(c => c && c.size > 0);
      const audioBlob = new Blob(validChunks, { type: this.mimeType || 'audio/webm' });
      if (typeof this.onStopCallback === 'function') {
        this.onStopCallback(audioBlob, this.mimeType);
      }
    };

    try {
      this.mediaRecorder.start(this.timeslice);
      this._isRecording = true;
    } catch (startErr) {
      console.warn('[VoiceRecorder] start error:', startErr);
      return false;
    }

    if (this.maxTimer) clearTimeout(this.maxTimer);
    this.maxTimer = setTimeout(() => {
      if (this._isRecording) {
        console.debug('[VoiceRecorder] 60s max watchdog reached.');
        this.stopRecording();
      }
    }, this.maxDurationMs);

    return true;
  }

  stopRecording() {
    if (!this._isRecording || !this.mediaRecorder) return;
    if (this.mediaRecorder.state !== 'inactive') {
      try {
        this.mediaRecorder.stop();
      } catch (e) {
        console.debug('[VoiceRecorder] Stop note:', e);
      }
    }
    this._isRecording = false;
  }
}

const activeVoiceRecorder = new VoiceRecorder({ timeslice: 1000, maxDurationMs: 60000 });
window.VoiceRecorder = VoiceRecorder;
window.activeVoiceRecorder = activeVoiceRecorder;

function startScreenerMediaRecorder(stream) {
  screenerMediaChunks = [];
  screenerMimeType = getBestMediaRecorderMimeType();

  activeVoiceRecorder.startRecording(stream, (audioBlob, mimeType) => {
    transcribeAudio(audioBlob, mimeType);
  });
}

function startScreenerWebSpeech() {
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRec) return;

  try {
    if (screenerState.recognition) {
      try { screenerState.recognition.abort(); } catch (e) {}
      screenerState.recognition = null;
    }

    const recognition = new SpeechRec();
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.lang = state.selectedLanguage || 'en-IN';

    const transcriptInput = document.getElementById('screenerTranscriptInput');
    const textInput = document.getElementById('screenerTextInput');

    recognition.onresult = (event) => {
      let accumulated = '';
      for (let i = 0; i < event.results.length; ++i) {
        accumulated += event.results[i][0].transcript + ' ';
      }
      accumulated = accumulated.trim();

      if (accumulated) {
        screenerState.rawTranscript = accumulated;
        if (transcriptInput) {
          transcriptInput.value = accumulated;
          updateTranscriptWordCount(accumulated);
        }
        if (textInput) textInput.value = accumulated;
        autoMatchAnswerToQuestion(accumulated);
      }
    };

    recognition.onerror = (event) => {
      console.warn('[Web Speech API Notice]:', event.error);
      if (event.error === 'network' || event.error === 'service-not-allowed') {
        console.warn('[Web Speech Blocked] Browser privacy active. Gracefully falling back to MediaRecorder + Whisper.');
        screenerState.webSpeechBlocked = true;
        screenerUseWebSpeechMode = false;
        const label = document.getElementById('webSpeechLabel');
        if (label) label.textContent = 'Engine: Whisper AI (Server)';
      }
    };

    screenerState.recognition = recognition;
    recognition.start();
  } catch (err) {
    console.warn('[Web Speech Exception]:', err);
    screenerState.webSpeechBlocked = true;
  }
}

function startScreenerAudioVAD(stream) {
  try {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) return;

    if (!screenerAudioContext || screenerAudioContext.state === 'closed') {
      screenerAudioContext = new AudioContextClass();
    }
    if (screenerAudioContext.state === 'suspended') {
      screenerAudioContext.resume().catch(() => {});
    }

    if (screenerScriptProcessor) {
      try { screenerScriptProcessor.disconnect(); } catch (e) {}
      screenerScriptProcessor = null;
    }

    const source = screenerAudioContext.createMediaStreamSource(stream);
    screenerScriptProcessor = screenerAudioContext.createScriptProcessor(4096, 1, 1);

    screenerAudioBuffers = [];
    screenerIsUserSpeaking = false;
    screenerSilenceStartTime = 0;
    screenerTranscribing = false;

    // Sensitive calibrated threshold for natural voice & whispers
    const vadThreshold = 0.0012;

    screenerScriptProcessor.onaudioprocess = (e) => {
      const input = e.inputBuffer.getChannelData(0);
      let sum = 0;
      for (let i = 0; i < input.length; i++) sum += input[i] * input[i];
      const rms = Math.sqrt(sum / input.length);

      // Barge-in: If doctor is speaking and user vocalizes, halt doctor voice
      if (screenerState.isDoctorSpeaking) {
        if (rms > 0.025) {
          stopDoctorVoice();
          startScreenerRecording();
        }
        return;
      }

      if (!screenerState.isRecording || screenerTranscribing) {
        return;
      }

      // Visual meter ring pulsation
      const w1 = document.getElementById('micWave1');
      const w2 = document.getElementById('micWave2');
      if (w1 && rms > 0.001) {
        w1.style.transform = `scale(${1 + Math.min(rms * 20, 0.85)})`;
        w1.style.opacity = `${0.40 + Math.min(rms * 15, 0.60)}`;
      }
      if (w2 && rms > 0.001) {
        w2.style.transform = `scale(${1 + Math.min(rms * 35, 1.35)})`;
        w2.style.opacity = `${0.30 + Math.min(rms * 12, 0.50)}`;
      }

      // Buffer audio as PCM fallback
      screenerAudioBuffers.push(new Float32Array(input));
      if (screenerAudioBuffers.length > 2500) screenerAudioBuffers.shift();

      if (rms > vadThreshold) {
        if (!screenerIsUserSpeaking) {
          screenerIsUserSpeaking = true;
          screenerSilenceStartTime = 0;
          const statusTitle = document.getElementById('screenerVoiceStatusTitle');
          if (statusTitle) statusTitle.textContent = '🎙️ Hearing your voice... Speak naturally';

          const transcriptInput = document.getElementById('screenerTranscriptInput');
          if (transcriptInput && (!transcriptInput.value || transcriptInput.value.startsWith('🎙️') || transcriptInput.value.includes('Listening'))) {
            transcriptInput.value = '🎙️ Hearing your voice... [Pause when finished to transcribe]';
          }
        }
      } else {
        if (screenerIsUserSpeaking) {
          if (screenerSilenceStartTime === 0) {
            screenerSilenceStartTime = Date.now();
          } else if (Date.now() - screenerSilenceStartTime > 1300) {
            // User finished speaking; natural pause detected!
            screenerIsUserSpeaking = false;
            screenerSilenceStartTime = 0;

            const transcriptInput = document.getElementById('screenerTranscriptInput');
            const webSpeechText = (screenerState.rawTranscript || (transcriptInput ? transcriptInput.value : '')).trim();
            const words = webSpeechText.split(/\s+/).filter(Boolean);
            const isPlaceholder = webSpeechText.startsWith('🎙️') || webSpeechText.startsWith('⚡') || webSpeechText.includes('Hearing') || webSpeechText.includes('Listening');

            if (!isPlaceholder && words.length >= 1 && screenerUseWebSpeechMode) {
              if (screenerState.isHandsFreeActive) {
                submitCurrentScreenerAnswer('voice', true);
              }
            } else {
              stopScreenerRecording();
            }
          }
        }
      }
    };

    const muteNode = screenerAudioContext.createGain();
    muteNode.gain.value = 0;
    source.connect(screenerScriptProcessor);
    screenerScriptProcessor.connect(muteNode);
    muteNode.connect(screenerAudioContext.destination);

  } catch (err) {
    console.debug('[Screener VAD Setup Note]:', err);
  }
}

async function transcribeAudio(audioBlob, mimeType) {
  if (screenerTranscribing) return;
  if (!audioBlob || audioBlob.size < 60) {
    if (screenerAudioBuffers && screenerAudioBuffers.length >= 2) {
      const sampleRate = screenerAudioContext ? screenerAudioContext.sampleRate : 44100;
      audioBlob = encodeWAVFromBuffers(screenerAudioBuffers, sampleRate);
      mimeType = 'audio/wav';
    }
  }

  if (!audioBlob || audioBlob.size < 60) {
    return;
  }

  screenerTranscribing = true;
  const statusTitle = document.getElementById('screenerVoiceStatusTitle');
  const statusSub = document.getElementById('screenerVoiceStatusSub');
  const transcriptInput = document.getElementById('screenerTranscriptInput');
  const textInput = document.getElementById('screenerTextInput');

  if (statusTitle) statusTitle.textContent = '⚡ Transcribing your voice...';
  if (statusSub) statusSub.textContent = 'Voicebox MLX-Audio AI is translating speech into text...';
  if (transcriptInput && (!transcriptInput.value || transcriptInput.value.startsWith('🎙️'))) {
    transcriptInput.value = '⚡ Transcribing your voice into text...';
  }

  try {
    let ext = 'webm';
    if (mimeType && mimeType.includes('mp4')) ext = 'mp4';
    else if (mimeType && mimeType.includes('ogg')) ext = 'ogg';
    else if (mimeType && mimeType.includes('wav')) ext = 'wav';

    const lang = state.selectedLanguage || 'en-IN';
    const sessionId = screenerState.sessionId || '';
    const currQ = screenerState.currentQuestion;
    const qid = currQ ? currQ.question_id : '';
    const consentTone = screenerState.voiceToneConsent !== false;

    let recognized = '';
    let engineUsed = 'Voicebox MLX-Audio STT';
    let voiceTone = null;

    // 1. Primary Engine: Voicebox MLX-Audio Transcriber
    if (window.VoiceboxTranscriber) {
      try {
        const vbRes = await window.VoiceboxTranscriber.transcribeBlob(audioBlob, lang, {
          analyzeTone: consentTone,
          sessionId: sessionId,
          questionId: qid
        });
        if (vbRes && vbRes.text && vbRes.text.trim()) {
          recognized = vbRes.text.trim();
          engineUsed = vbRes.engine || engineUsed;
          voiceTone = vbRes.voiceTone || null;
        }
      } catch (vbErr) {
        console.debug('[Screener VoiceboxTranscriber note]:', vbErr);
      }
    }

    // 2. Direct /api/voicebox/transcribe fallback
    if (!recognized) {
      try {
        const formData = new FormData();
        formData.append('audio', audioBlob, `recording.${ext}`);
        let vbUrl = `/api/voicebox/transcribe?language=${encodeURIComponent(lang)}`;
        if (sessionId) vbUrl += `&session_id=${encodeURIComponent(sessionId)}`;
        if (qid) vbUrl += `&question_id=${encodeURIComponent(qid)}`;
        if (consentTone) vbUrl += `&analyze_tone=true`;

        const res = await fetch(vbUrl, { method: 'POST', body: formData });
        if (res.ok) {
          const data = await res.json();
          if (data.status === 'success' && (data.text || data.transcription)) {
            recognized = (data.text || data.transcription).trim();
            engineUsed = data.engine_used || engineUsed;
            voiceTone = data.voice_tone || null;
          }
        }
      } catch (e) {
        console.debug('[Screener /api/voicebox/transcribe fallback]:', e);
      }
    }

    // 3. Fallback Engine: /api/transcribe
    if (!recognized) {
      const formData = new FormData();
      formData.append('audio', audioBlob, `recording.${ext}`);
      let url = `/api/transcribe?language=${encodeURIComponent(lang)}`;
      if (sessionId) url += `&session_id=${encodeURIComponent(sessionId)}`;
      if (qid) url += `&question_id=${encodeURIComponent(qid)}`;
      if (consentTone) url += `&analyze_tone=true`;

      const res = await fetch(url, {
        method: 'POST',
        body: formData
      });

      const data = await res.json();
      if (data.status === 'success' && data.text && data.text.trim()) {
        recognized = data.text.trim();
        engineUsed = data.engine_used || 'Faster-Whisper';
        voiceTone = data.voice_tone || null;
      }
    }

    if (recognized) {
      screenerState.rawTranscript = recognized;

      if (transcriptInput) {
        transcriptInput.value = recognized;
        transcriptInput.style.borderColor = '#10b981';
        transcriptInput.style.boxShadow = '0 0 0 2px rgba(16, 185, 129, 0.25)';
        updateTranscriptWordCount(recognized);
        setTimeout(() => {
          if (transcriptInput) {
            transcriptInput.style.borderColor = '';
            transcriptInput.style.boxShadow = '';
          }
        }, 3000);
      }
      if (textInput) textInput.value = recognized;

      autoMatchAnswerToQuestion(recognized);

      // Display live tone indicator if returned
      if (data.voice_tone && data.voice_tone.tone_label) {
        const toneCard = document.getElementById('screenerToneCard');
        const toneLabel = document.getElementById('screenerToneLabel');
        if (toneCard) toneCard.style.display = 'block';
        if (toneLabel) {
          toneLabel.textContent = `Acoustic Tone: ${data.voice_tone.tone_label} · Cadence: ${data.voice_tone.prosodic_features?.speaking_rate_units_per_sec || 3.2} units/s`;
        }
      }

      if (statusTitle) statusTitle.textContent = '✓ Voice Captured: "' + recognized + '"';
      if (statusSub) statusSub.textContent = `Transcribed via ${data.engine_used || 'Faster-Whisper'}. You can review and edit above, then click Confirm Answer.`;

      if (screenerState.isHandsFreeActive) {
        if (statusSub) statusSub.textContent = `✓ Captured: "${recognized}". Advancing in 2s (or click Confirm Answer)...`;
        setTimeout(() => {
          if (screenerState.inputMode === 'voice' && screenerState.isHandsFreeActive) {
            submitCurrentScreenerAnswer('voice', true);
          }
        }, 2000);
      }
    } else {
      if (statusTitle) statusTitle.textContent = 'Listening... Speak naturally';
      if (statusSub) statusSub.textContent = 'Could not transcribe your voice. Please try again or switch to text.';
      if (transcriptInput && transcriptInput.value.startsWith('⚡')) {
        transcriptInput.value = '';
      }
    }
  } catch (err) {
    console.warn('[transcribeAudio Error]:', err);
    if (statusTitle) statusTitle.textContent = 'Listening... Speak naturally';
    if (statusSub) statusSub.textContent = 'Could not transcribe your voice. Please try again or switch to text.';
    if (transcriptInput && transcriptInput.value.startsWith('⚡')) {
      transcriptInput.value = '';
    }
  } finally {
    screenerTranscribing = false;
  }
}

// Backward-compatible wrapper
async function uploadAndTranscribeRecording() {
  if (screenerMediaChunks.length > 0) {
    const mime = screenerMimeType || 'audio/webm';
    const blob = new Blob(screenerMediaChunks, { type: mime });
    screenerMediaChunks = [];
    return transcribeAudio(blob, mime);
  } else if (screenerAudioBuffers && screenerAudioBuffers.length >= 2) {
    const sampleRate = screenerAudioContext ? screenerAudioContext.sampleRate : 44100;
    const blob = encodeWAVFromBuffers(screenerAudioBuffers, sampleRate);
    screenerAudioBuffers = [];
    return transcribeAudio(blob, 'audio/wav');
  }
}

function autoMatchAnswerToQuestion(recognized) {
  if (!screenerState.currentQuestion || !recognized) return;
  const lower = recognized.toLowerCase().trim();
  const q = screenerState.currentQuestion;

  if (q.question_type === 'MCQ' && q.options && q.options.length > 0) {
    let matchedIdx = -1;
    q.options.forEach((opt, idx) => {
      const optTextLower = (opt.text || '').toLowerCase();
      const labelLower = (opt.label || String.fromCharCode(65 + idx)).toLowerCase();
      if (lower === labelLower || lower.startsWith(`option ${labelLower}`) || lower.includes(optTextLower) || optTextLower.includes(lower)) {
        matchedIdx = idx;
      }
    });
    if (matchedIdx !== -1) {
      selectMcqOption(matchedIdx, q.options[matchedIdx].text, q.options[matchedIdx].score);
    }
  } else {
    // VSAQ
    const chipBtns = document.querySelectorAll('.vsaq-chip-btn');
    chipBtns.forEach(btn => {
      const chipVal = btn.textContent.toLowerCase();
      if (lower === chipVal || lower.includes(chipVal) || chipVal.includes(lower)) {
        btn.click();
      }
    });
  }
}

function stopScreenerRecording() {
  screenerState.isRecording = false;

  if (screenerMaxDurationTimer) {
    clearTimeout(screenerMaxDurationTimer);
    screenerMaxDurationTimer = null;
  }
  if (screenerState.silenceTimer) {
    clearTimeout(screenerState.silenceTimer);
    screenerState.silenceTimer = null;
  }

  const micWrap = document.getElementById('screenerMicWrap');
  const w1 = document.getElementById('micWave1');
  const w2 = document.getElementById('micWave2');

  if (micWrap) micWrap.classList.remove('recording');
  if (w1) { w1.style.transform = ''; w1.style.opacity = ''; }
  if (w2) { w2.style.transform = ''; w2.style.opacity = ''; }

  // Stop MediaRecorder (fires onstop and triggers uploadAndTranscribeRecording)
  if (screenerMediaRecorder && screenerMediaRecorder.state !== 'inactive') {
    try {
      screenerMediaRecorder.stop();
    } catch (e) {
      console.debug('[MediaRecorder Stop Note]:', e);
    }
  } else {
    // If MediaRecorder wasn't active, check if we have PCM audio buffers to transcribe
    if (screenerAudioBuffers && screenerAudioBuffers.length >= 2) {
      uploadAndTranscribeRecording();
    }
  }

  // Stop Web Speech API if active
  if (screenerState.recognition) {
    try {
      screenerState.recognition.stop();
    } catch (e) {}
    screenerState.recognition = null;
  }

  if (screenerScriptProcessor) {
    try { screenerScriptProcessor.disconnect(); } catch (e) {}
    screenerScriptProcessor = null;
  }

  screenerIsUserSpeaking = false;
  screenerSilenceStartTime = 0;
}

async function submitCurrentScreenerAnswer(inputMode = 'voice', autoAdvance = false) {
  if (screenerState.silenceTimer) {
    clearTimeout(screenerState.silenceTimer);
    screenerState.silenceTimer = null;
  }

  stopScreenerRecording();
  stopDoctorVoice();

  if (!screenerState.sessionId || !screenerState.currentQuestion) {
    alert('Session is not initialized. Please click New Session.');
    return;
  }

  let answerText = '';
  if (inputMode === 'voice') {
    const transcriptInput = document.getElementById('screenerTranscriptInput');
    answerText = transcriptInput ? transcriptInput.value.trim() : '';
  } else {
    const textInput = document.getElementById('screenerTextInput');
    answerText = textInput ? textInput.value.trim() : '';
  }

  if (!answerText) {
    const transcriptInput = document.getElementById('screenerTranscriptInput');
    const textInput = document.getElementById('screenerTextInput');
    answerText = (transcriptInput && transcriptInput.value.trim()) || (textInput && textInput.value.trim()) || '';
  }

  if (!answerText) {
    if (screenerState.isHandsFreeActive && inputMode === 'voice') {
      const statusTitle = document.getElementById('screenerVoiceStatusTitle');
      const statusSub = document.getElementById('screenerVoiceStatusSub');
      if (statusTitle) statusTitle.textContent = 'Listening for your answer...';
      if (statusSub) statusSub.textContent = 'Please share your thoughts aloud. Dr. MindBridge is listening.';
      setTimeout(() => startScreenerRecording(), 500);
      return;
    }
    alert('Please speak or select your answer before proceeding.');
    return;
  }

  const qid = screenerState.currentQuestion.question_id;

  // Show status feedback
  const statusTitle = document.getElementById('screenerVoiceStatusTitle');
  const statusSub = document.getElementById('screenerVoiceStatusSub');
  if (statusTitle) statusTitle.textContent = 'Analyzing Vocal Nuance & Clinical Telemetry...';
  if (statusSub) statusSub.textContent = 'Grounded AI Doctor evaluating emotional tone, cadence, and validated scales.';

  try {
    const res = await fetch('/api/screener/answer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: screenerState.sessionId,
        user_id: state.userId,
        question_id: qid,
        answer_text: answerText,
        input_mode: inputMode,
        raw_transcript: screenerState.rawTranscript || answerText
      })
    });

    const data = await res.json();

    // Check Immediate Crisis Interception
    if (data.crisis_detected || data.status === 'crisis_triggered') {
      triggerImmediateCrisisFlow(data);
      return;
    }

    // Display AI Doctor Tone & Emotional Telemetry Box
    const toneCard = document.getElementById('screenerToneCard');
    const toneLabel = document.getElementById('screenerToneLabel');
    const docFeedback = document.getElementById('screenerDoctorFeedback');

    if (data.tone_analysis) {
      if (toneCard) toneCard.style.display = 'block';
      if (toneLabel) {
        toneLabel.textContent = `Acoustic Tone: ${data.tone_analysis.primary_tone.toUpperCase()} (${data.tone_analysis.tone_confidence}% confidence) · Cadence: ${data.tone_analysis.cadence}`;
      }
      if (docFeedback && data.doctor_dialogue) {
        docFeedback.textContent = `"${data.doctor_dialogue}"`;
      }
    }

    if (data.is_completed) {
      if (data.doctor_dialogue && screenerState.inputMode === 'voice') {
        speakDoctorVoice(data.doctor_dialogue, () => {
          evaluateAndShowResults();
        });
      } else {
        evaluateAndShowResults();
      }
      return;
    }

    // Transition to next question
    if (data.next_question) {
      if (screenerState.inputMode === 'voice' && screenerState.isHandsFreeActive && data.doctor_dialogue) {
        // Speak empathetic conversational acknowledgment first, then smoothly transition and speak next question!
        speakDoctorVoice(data.doctor_dialogue, () => {
          renderScreenerQuestion(data.next_question, data.current_index, data.total_questions);
        });
      } else {
        renderScreenerQuestion(data.next_question, data.current_index, data.total_questions);
      }
    } else {
      fetchCurrentScreenerQuestion();
    }
  } catch (err) {
    console.error('[Submit Answer Error]:', err);
    if (statusTitle) statusTitle.textContent = 'Ready for Next Question';
    if (statusSub) statusSub.textContent = 'An error occurred during submission. Please tap Next Question.';
  }
}

// Expose functions on window for onclick attributes
window.toggleScreenerVoiceDoctor = toggleScreenerVoiceDoctor;
window.repeatCurrentDoctorQuestion = repeatCurrentDoctorQuestion;
window.toggleHandsFreeAutoAdvance = toggleHandsFreeAutoAdvance;
window.setScreenerInputMode = setScreenerInputMode;
window.clearScreenerTranscript = clearScreenerTranscript;
window.submitCurrentScreenerAnswer = submitCurrentScreenerAnswer;
window.rerecordScreenerAnswer = rerecordScreenerAnswer;
window.toggleWebSpeechMode = toggleWebSpeechMode;

function triggerImmediateCrisisFlow(crisisData) {
  screenerState.isCrisisHalted = true;
  const overlay = document.getElementById('screenerCrisisOverlay');
  const msgBody = document.getElementById('screenerCrisisMessage');
  const questionCard = document.getElementById('screenerQuestionCard');
  const progressCard = document.getElementById('screenerProgressCard');

  if (overlay) overlay.style.display = 'flex';
  if (questionCard) questionCard.style.display = 'none';
  if (progressCard) progressCard.style.display = 'none';

  if (msgBody && crisisData.message) {
    msgBody.textContent = crisisData.message;
  }

  // Play audio silence if soundscapes active
  if (state.soundPlaying && typeof pauseSoundscape === 'function') {
    pauseSoundscape();
  }

  if (window.lucide) window.lucide.createIcons();
}

async function evaluateAndShowResults() {
  if (!screenerState.sessionId) return;
  try {
    const res = await fetch('/api/screener/evaluate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: screenerState.sessionId
      })
    });

    const data = await res.json();
    if (data.status === 'success' && data.result) {
      screenerState.evaluationResult = data.result;
      renderScreenerResults(data.result);
    }
  } catch (err) {
    console.error('[Evaluate Error]:', err);
  }
}

function renderScreenerResults(result) {
  screenerState.isCompleted = true;
  const progressCard = document.getElementById('screenerProgressCard');
  const questionCard = document.getElementById('screenerQuestionCard');
  const resultsStage = document.getElementById('screenerResultsStage');

  if (progressCard) progressCard.style.display = 'none';
  if (questionCard) questionCard.style.display = 'none';
  if (resultsStage) resultsStage.style.display = 'flex';

  // Timestamps
  const timestampPill = document.getElementById('resultsTimestamp');
  if (timestampPill && result.timestamp) {
    const d = new Date(result.timestamp);
    timestampPill.textContent = d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  // Overall Distress
  const distressBadge = document.getElementById('resultsDistressBadge');
  const summaryText = document.getElementById('resultsSummaryText');
  const actionName = document.getElementById('resultsActionName');
  const actionBtnText = document.getElementById('resultsActionBtnText');

  if (distressBadge) {
    const tierMap = {
      low: 'Low Distress (Wellbeing Range)',
      moderate: 'Moderate Distress',
      high: 'Elevated Clinical Distress'
    };
    distressBadge.textContent = tierMap[result.overall_distress] || result.overall_distress;
    if (result.overall_distress === 'low') {
      distressBadge.style.color = '#22c55e';
    } else if (result.overall_distress === 'moderate') {
      distressBadge.style.color = '#eab308';
    } else {
      distressBadge.style.color = '#ef4444';
    }
  }

  if (summaryText) {
    summaryText.textContent = result.summary_text || 'Assessment completed successfully.';
  }

  // Recommended Care Pathway Action
  if (actionName && actionBtnText) {
    if (result.recommended_action === 'self_care') {
      actionName.textContent = 'Self-Care, Grounding & Sleep Hygiene';
      actionBtnText.textContent = 'Explore Audio Sanctuary & Exercises';
    } else if (result.recommended_action === 'psychologist_referral') {
      actionName.textContent = 'Consult a Licensed Clinical Psychologist';
      actionBtnText.textContent = 'Explore Verified Psychologists';
    } else if (result.recommended_action === 'urgent_psychiatrist_referral') {
      actionName.textContent = 'Urgent Clinical Evaluation (Psychiatrist / Psychologist)';
      actionBtnText.textContent = 'Find Available Specialists';
    } else if (result.recommended_action === 'crisis_resources') {
      actionName.textContent = 'Immediate Crisis Support & Safety Hotlines';
      actionBtnText.textContent = 'Access 24/7 Emergency Support';
    }
  }

  // Psychometric subscales
  // PHQ-9
  const phqScore = document.getElementById('resultsPhq9Score');
  const phqSev = document.getElementById('resultsPhq9Severity');
  const phqMeter = document.getElementById('resultsPhq9Meter');
  if (phqScore) phqScore.textContent = result.phq9_score ?? 0;
  if (phqSev) phqSev.textContent = `${(result.phq9_severity || 'minimal').replace('_', ' ')} tier`;
  if (phqMeter) phqMeter.style.width = `${Math.min(100, Math.round(((result.phq9_score || 0) / 27) * 100))}%`;

  // GAD-7
  const gadScore = document.getElementById('resultsGad7Score');
  const gadSev = document.getElementById('resultsGad7Severity');
  const gadMeter = document.getElementById('resultsGad7Meter');
  if (gadScore) gadScore.textContent = result.gad7_score ?? 0;
  if (gadSev) gadSev.textContent = `${(result.gad7_severity || 'minimal').replace('_', ' ')} tier`;
  if (gadMeter) gadMeter.style.width = `${Math.min(100, Math.round(((result.gad7_score || 0) / 21) * 100))}%`;

  // Stress
  const stressScore = document.getElementById('resultsStressScore');
  const stressSev = document.getElementById('resultsStressSeverity');
  const stressMeter = document.getElementById('resultsStressMeter');
  if (stressScore) stressScore.textContent = result.stress_score ?? 0;
  if (stressSev) {
    const s = result.stress_score || 0;
    stressSev.textContent = s < 15 ? 'Normal Tension' : s < 19 ? 'Mild Stress' : s < 26 ? 'Moderate Stress' : 'Elevated Burnout';
  }
  if (stressMeter) stressMeter.style.width = `${Math.min(100, Math.round(((result.stress_score || 0) / 42) * 100))}%`;

  // Sleep
  const sleepScore = document.getElementById('resultsSleepScore');
  const sleepSev = document.getElementById('resultsSleepSeverity');
  const sleepMeter = document.getElementById('resultsSleepMeter');
  if (sleepScore) sleepScore.textContent = result.sleep_score ?? 0;
  if (sleepSev) {
    const sl = result.sleep_score || 0;
    sleepSev.textContent = sl < 5 ? 'Restorative Sleep' : sl < 10 ? 'Mild Fragmentation' : 'Significant Sleep Strain';
  }
  if (sleepMeter) sleepMeter.style.width = `${Math.min(100, Math.round(((result.sleep_score || 0) / 20) * 100))}%`;

  // Functioning
  const funcScore = document.getElementById('resultsFunctioningScore');
  const funcSev = document.getElementById('resultsFunctioningSeverity');
  const funcMeter = document.getElementById('resultsFunctioningMeter');
  if (funcScore) funcScore.textContent = result.functioning_score ?? 0;
  if (funcSev) {
    const fn = result.functioning_score || 0;
    funcSev.textContent = fn < 4 ? 'Intact Daily Routine' : fn < 8 ? 'Mild Executive Strain' : 'Noticeable Impairment';
  }
  if (funcMeter) funcMeter.style.width = `${Math.min(100, Math.round(((result.functioning_score || 0) / 18) * 100))}%`;

  // Safety
  const safetyTier = document.getElementById('resultsSafetyRiskTier');
  const safetySev = document.getElementById('resultsSafetySeverity');
  if (safetyTier) safetyTier.textContent = (result.risk_flag || 'none').toUpperCase();
  if (safetySev) {
    safetySev.textContent = result.risk_flag === 'none' ? 'No Acute Risk Indicated' : `${result.risk_flag} safety attention`;
  }

  // Voice-Tone & Prosodic Telemetry Rendering
  if (result.voice_tone_summary) {
    renderVoiceToneResults(result.voice_tone_summary);
  } else if (screenerState.sessionId) {
    fetchSessionVoiceTone(screenerState.sessionId);
  }

  if (window.lucide) window.lucide.createIcons();
}

function renderVoiceToneResults(summary) {
  const card = document.getElementById('resultsVoiceToneCard');
  if (!card) return;

  if (!summary || !summary.tone_distribution) {
    card.style.display = 'none';
    return;
  }

  card.style.display = 'block';

  // Dominant tone pill
  const domLabel = document.getElementById('resultsDominantToneLabel');
  const domPill = document.getElementById('resultsDominantTonePill');
  if (domLabel) domLabel.textContent = summary.dominant_tone_label || summary.dominant_tone;
  if (domPill) {
    if (summary.dominant_tone === 'neutral_calm') {
      domPill.style.background = 'rgba(20, 184, 166, 0.15)';
      domPill.style.borderColor = 'rgba(20, 184, 166, 0.4)';
      domPill.style.color = '#2dd4bf';
    } else if (summary.dominant_tone === 'tense_anxious') {
      domPill.style.background = 'rgba(245, 158, 11, 0.15)';
      domPill.style.borderColor = 'rgba(245, 158, 11, 0.4)';
      domPill.style.color = '#fbbf24';
    } else if (summary.dominant_tone === 'sad_low_energy') {
      domPill.style.background = 'rgba(96, 165, 250, 0.15)';
      domPill.style.borderColor = 'rgba(96, 165, 250, 0.4)';
      domPill.style.color = '#93c5fd';
    } else if (summary.dominant_tone === 'flat_monotone') {
      domPill.style.background = 'rgba(148, 163, 184, 0.15)';
      domPill.style.borderColor = 'rgba(148, 163, 184, 0.4)';
      domPill.style.color = '#cbd5e1';
    } else if (summary.dominant_tone === 'energetic_positive') {
      domPill.style.background = 'rgba(236, 72, 153, 0.15)';
      domPill.style.borderColor = 'rgba(236, 72, 153, 0.4)';
      domPill.style.color = '#f472b6';
    }
  }

  // Distribution progress bars
  const dist = summary.tone_distribution || {};
  const setBar = (pctId, barId, val) => {
    const p = Math.round((val || 0) * 100);
    const pEl = document.getElementById(pctId);
    const bEl = document.getElementById(barId);
    if (pEl) pEl.textContent = `${p}%`;
    if (bEl) bEl.style.width = `${p}%`;
  };

  setBar('vtPctCalm', 'vtBarCalm', dist.neutral_calm);
  setBar('vtPctTense', 'vtBarTense', dist.tense_anxious);
  setBar('vtPctSad', 'vtBarSad', dist.sad_low_energy);
  setBar('vtPctFlat', 'vtBarFlat', dist.flat_monotone);
  setBar('vtPctEnergetic', 'vtBarEnergetic', dist.energetic_positive);

  // Prosodic Telemetry
  const prosody = summary.prosodic_features || {};
  const pPitch = document.getElementById('resultsAvgPitch');
  const pEnergy = document.getElementById('resultsAvgEnergy');
  const pRate = document.getElementById('resultsAvgRate');
  const pVar = document.getElementById('resultsToneVariability');

  if (pPitch) pPitch.textContent = prosody.avg_pitch_hz ? `${prosody.avg_pitch_hz} Hz` : '-- Hz';
  if (pEnergy) pEnergy.textContent = prosody.avg_energy_db ? `${prosody.avg_energy_db} dB` : '-- dB';
  if (pRate) pRate.textContent = prosody.speaking_rate_units_per_sec ? `${prosody.speaking_rate_units_per_sec} units/s` : '-- units/s';
  if (pVar) {
    const v = summary.tone_variability || 0;
    pVar.textContent = v > 0.18 ? 'Dynamic' : 'Steady';
  }

  // Non-Diagnostic Interpretation Text
  const interpEl = document.getElementById('resultsToneInterpretationText');
  if (interpEl) {
    interpEl.textContent = summary.interpretation_text || 'Observed tone pattern summary across your voice responses.';
  }

  if (window.lucide) window.lucide.createIcons();
}

async function fetchSessionVoiceTone(sessionId) {
  if (!sessionId) return;
  try {
    const res = await fetch(`/api/screener/session/${encodeURIComponent(sessionId)}/voice-tone`);
    const data = await res.json();
    if (data.status === 'success' && data.voice_tone_summary) {
      renderVoiceToneResults(data.voice_tone_summary);
    }
  } catch (e) {}
}

function toggleVoiceToneConsent(enabled) {
  screenerState.voiceToneConsent = !!enabled;
}

window.ensureMicrophonePermission = ensureScreenerMicPermission;
window.renderVoiceToneResults = renderVoiceToneResults;
window.toggleVoiceToneConsent = toggleVoiceToneConsent;

function startFreshScreenerSession() {
  localStorage.removeItem('mb_screener_session_id');
  screenerState.sessionId = null;
  screenerState.isCrisisHalted = false;
  screenerState.isCompleted = false;
  loadScreenerSession(true);
}

function navigateFromScreenerAction() {
  const res = screenerState.evaluationResult;
  if (!res) {
    switchTab('providers');
    return;
  }
  if (res.recommended_action === 'self_care') {
    switchTab('chat');
  } else if (res.recommended_action === 'crisis_resources') {
    switchTab('emergency');
  } else {
    switchTab('providers');
  }
}

function openEmergencyTab() {
  const overlay = document.getElementById('screenerCrisisOverlay');
  if (overlay) overlay.style.display = 'none';
  switchTab('emergency');
}

// ==========================================================================
// PAST LIFE & LIFE REFLECTION STUDIO CONTROLLER (DEDICATED MODAL WINDOW)
// ==========================================================================

const pastLifeStudioState = {
  isOpen: false,
  sessionId: null,
  language: 'en',
  mode: 'short', // 'short' (6 questions) or 'full' (13 questions)
  currentIndex: 0,
  totalQuestions: 6,
  currentQuestion: null,
  isDoctorSpeaking: false,
  isUserSpeaking: false,
  recognition: null,
  isRecognitionActive: false,
  activeAudioElement: null,
  speechSynthUtterance: null
};

function openPastLifeModal(lang = 'en', mode = 'short', initialSession = null) {
  pastLifeStudioState.isOpen = true;
  pastLifeStudioState.language = (lang && (lang.startsWith('bn') || lang.startsWith('hi') || lang.startsWith('en'))) ? lang.substring(0, 2) : (lang || 'en');
  pastLifeStudioState.mode = mode || 'short';

  // 1. CRITICAL: Pause and Stop any background chatbot voice module, TTS, and soundscapes!
  if (state.voiceCompanionMode) {
    stopVoiceCompanionMode();
  }
  if (window.VoiceboxPipeline) {
    window.VoiceboxPipeline.stop(0.01);
  }
  stopSpeaking();
  if (state.soundPlaying) {
    pauseSoundscape();
  }
  if (window.speechSynthesis) {
    window.speechSynthesis.cancel();
  }

  // 2. Reveal Modal Window
  const modal = document.getElementById('pastLifeModal');
  if (modal) {
    modal.style.display = 'flex';
  }

  // Set active language pill in modal header
  document.querySelectorAll('.plm-lang-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-lang') === pastLifeStudioState.language);
  });

  // Switch to question stage
  const qStage = document.getElementById('plmQuestionStage');
  const rStage = document.getElementById('plmResultsStage');
  if (qStage) qStage.style.display = 'flex';
  if (rStage) rStage.style.display = 'none';

  // Update mode badge
  const modeBadge = document.getElementById('plmModeBadge');
  const modeSwitchLabel = document.getElementById('plmModeSwitchLabel');
  if (pastLifeStudioState.mode === 'short') {
    if (modeBadge) modeBadge.textContent = '🌱 6 Core Reflection Questions';
    if (modeSwitchLabel) modeSwitchLabel.textContent = 'Switch to 13 Questions';
  } else {
    if (modeBadge) modeBadge.textContent = '📜 Full 13-Question Journey';
    if (modeSwitchLabel) modeSwitchLabel.textContent = 'Switch to 6 Questions';
  }

  // Load initial question or start fresh session from server
  if (initialSession && initialSession.question_text) {
    pastLifeStudioState.sessionId = initialSession.session_id;
    pastLifeStudioState.currentIndex = initialSession.current_index || 0;
    pastLifeStudioState.totalQuestions = initialSession.total_questions || (pastLifeStudioState.mode === 'short' ? 6 : 13);
    pastLifeStudioState.currentQuestion = {
      id: initialSession.question_id || 1,
      question_text: initialSession.question_text,
      gentle_support: initialSession.gentle_support,
      suggested_chips: initialSession.suggested_chips,
      category: 'Life Reflection'
    };
    renderCurrentPastLifeQuestion();
  } else {
    startFreshPastLifeSession(pastLifeStudioState.language, pastLifeStudioState.mode);
  }
}

async function startFreshPastLifeSession(lang = 'en', mode = 'short') {
  try {
    const res = await fetch('/api/past-life/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: state.userId,
        conversation_id: state.conversationId,
        language: lang,
        mode: mode
      })
    });
    const data = await res.json();
    if (data.status === 'success' && data.session) {
      const sess = data.session;
      pastLifeStudioState.sessionId = sess.session_id;
      pastLifeStudioState.currentIndex = sess.current_index;
      pastLifeStudioState.totalQuestions = sess.total_questions;
      pastLifeStudioState.currentQuestion = {
        id: sess.question_id,
        question_text: sess.question_text,
        gentle_support: sess.gentle_support,
        suggested_chips: sess.suggested_chips,
        category: 'Emotional Safety & Comfort'
      };
      renderCurrentPastLifeQuestion();
    }
  } catch (err) {
    console.error('Failed to start past life session:', err);
  }
}

function renderCurrentPastLifeQuestion() {
  const q = pastLifeStudioState.currentQuestion;
  if (!q) return;

  const idx = pastLifeStudioState.currentIndex + 1;
  const total = pastLifeStudioState.totalQuestions;

  // Update progress
  const progressLabel = document.getElementById('plmProgressLabel');
  const categoryLabel = document.getElementById('plmCategoryLabel');
  const progressFill = document.getElementById('plmProgressFill');
  const qBadge = document.getElementById('plmQBadge');
  const qText = document.getElementById('plmQuestionText');
  const supportQuote = document.getElementById('plmSupportQuote');
  const answerInput = document.getElementById('plmAnswerInput');
  const chipsContainer = document.getElementById('plmChipsContainer');
  const submitBtnLabel = document.getElementById('plmSubmitBtnLabel');

  if (progressLabel) progressLabel.textContent = `Question ${idx} of ${total}`;
  if (categoryLabel) categoryLabel.textContent = q.category || 'Life Reflection';
  if (progressFill) progressFill.style.width = `${Math.min(100, Math.round((idx / total) * 100))}%`;
  if (qBadge) qBadge.textContent = `Question ${idx}`;
  if (qText) qText.textContent = q.question_text;
  if (supportQuote) supportQuote.textContent = q.gentle_support || '';
  if (answerInput) {
    answerInput.value = '';
    answerInput.placeholder = (pastLifeStudioState.language === 'bn') 
      ? 'তোমার উত্তর এখানে বলো বা লিখো...' 
      : (pastLifeStudioState.language === 'hi')
      ? 'अपना उत्तर यहाँ बोलें या लिखें...'
      : 'Your spoken words or typed thoughts will appear here...';
  }

  if (submitBtnLabel) {
    submitBtnLabel.textContent = (idx >= total) ? 'Complete & Analyze' : 'Next Question';
  }

  // Render suggestion chips
  if (chipsContainer) {
    chipsContainer.innerHTML = '';
    const chips = q.suggested_chips || [];
    chips.forEach(chipText => {
      const chipBtn = document.createElement('button');
      chipBtn.type = 'button';
      chipBtn.className = 'past-life-chip-btn';
      chipBtn.innerHTML = `<i data-lucide="sparkles" style="width: 12px; height: 12px; color: #10b981;"></i> <span>${chipText}</span>`;
      chipBtn.addEventListener('click', () => {
        if (answerInput) {
          if (answerInput.value.trim().length > 0) {
            answerInput.value += ` · ${chipText}`;
          } else {
            answerInput.value = chipText;
          }
        }
      });
      chipsContainer.appendChild(chipBtn);
    });
  }

  if (window.lucide) window.lucide.createIcons();

  // ECHO & FEEDBACK PREVENTION:
  // 1. Mark AI speaking state
  pastLifeStudioState.isDoctorSpeaking = true;
  // 2. STOP user microphone recognition immediately while AI speaks
  stopPastLifeSpeechRecognition();

  // Update UI indicators
  const speakingBanner = document.getElementById('plmAiSpeakingBanner');
  const speakingWave = document.getElementById('plmSpeakingWave');
  const speakingText = document.getElementById('plmAiSpeakingText');
  const micDot = document.getElementById('plmMicStateDot');
  const micText = document.getElementById('plmMicStateText');
  const micBtn = document.getElementById('plmMicToggleBtn');

  if (speakingBanner) speakingBanner.style.display = 'flex';
  if (speakingWave) speakingWave.style.display = 'flex';
  if (speakingText) speakingText.textContent = (pastLifeStudioState.language === 'bn')
    ? 'মাইন্ডব্রিজ প্রশ্নটি পাঠ করছে... (মাইক্রোফোন স্থগিত)'
    : (pastLifeStudioState.language === 'hi')
    ? 'माइंडब्रिज सवाल पढ़ रहा है... (माइक रुका हुआ है)'
    : 'MindBridge is reading the question... (Mic paused)';

  if (micDot) micDot.className = 'plm-mic-state-dot speaking';
  if (micText) micText.textContent = (pastLifeStudioState.language === 'bn')
    ? 'প্রশ্ন পাঠ শেষ হলে মাইক চালু হবে...'
    : (pastLifeStudioState.language === 'hi')
    ? 'सवाल पूरा होने पर माइक शुरू होगा...'
    : 'Mic will activate after question reading...';

  if (micBtn) micBtn.classList.remove('active');

  // Read aloud the question text with sequence guard and onEnd callback
  speakPastLifeQuestion(q.question_text, pastLifeStudioState.language, () => {
    // When question audio finishes:
    pastLifeStudioState.isDoctorSpeaking = false;
    if (speakingWave) speakingWave.style.display = 'none';
    if (speakingText) speakingText.textContent = (pastLifeStudioState.language === 'bn')
      ? 'প্রশ্ন পাঠ সম্পন্ন'
      : (pastLifeStudioState.language === 'hi')
      ? 'सवाल पूरा हुआ'
      : 'Question read complete';

    if (micDot) micDot.className = 'plm-mic-state-dot active';
    if (micText) micText.textContent = (pastLifeStudioState.language === 'bn')
      ? 'তোমার উত্তর শুনছি... কণ্ঠ বা কীবোর্ডে উত্তর দাও'
      : (pastLifeStudioState.language === 'hi')
      ? 'आपका उत्तर सुन रहा हूँ... आवाज़ या टाइप करके बताएं'
      : 'Listening for your answer... Speak or type below';

    if (micBtn) micBtn.classList.add('active');

    // Automatically start speech recognition for user's answer
    startPastLifeSpeechRecognition();
  });
}

let pastLifeQuestionSequenceId = 0;
let pastLifeTtsWatchdog = null;

function stopPastLifeDoctorReading() {
  pastLifeStudioState.isDoctorSpeaking = false;
  if (pastLifeTtsWatchdog) {
    clearTimeout(pastLifeTtsWatchdog);
    pastLifeTtsWatchdog = null;
  }
  if (pastLifeStudioState.activeAudioElement) {
    try {
      pastLifeStudioState.activeAudioElement.pause();
      pastLifeStudioState.activeAudioElement = null;
    } catch(e) {}
  }
  if (window.speechSynthesis) {
    window.speechSynthesis.cancel();
  }
  if (window.VoiceboxPipeline) {
    window.VoiceboxPipeline.stop(0.01);
  }
  stopSpeaking();
  const speakingWave = document.getElementById('plmSpeakingWave');
  if (speakingWave) speakingWave.style.display = 'none';
  const speakingBanner = document.getElementById('plmAiSpeakingBanner');
  if (speakingBanner) speakingBanner.style.display = 'none';
  const micDot = document.getElementById('plmMicStateDot');
  if (micDot) micDot.className = 'plm-mic-state-dot active';
  const micBtn = document.getElementById('plmMicToggleBtn');
  if (micBtn) micBtn.classList.add('active');
  const micText = document.getElementById('plmMicStateText');
  if (micText) {
    micText.textContent = (pastLifeStudioState.language === 'bn')
      ? 'তোমার উত্তর শুনছি... কণ্ঠ বা কীবোর্ডে উত্তর দাও'
      : (pastLifeStudioState.language === 'hi')
      ? 'आपका उत्तर सुन रहा हूँ... आवाज़ या टाइप करके बताएं'
      : 'Listening for your answer... Speak or type below';
  }
}

function speakPastLifeQuestion(text, lang, onEndCallback) {
  if (!text) {
    if (onEndCallback) onEndCallback();
    return;
  }

  const seqId = ++pastLifeQuestionSequenceId;

  // 1. Strictly cancel and silence any ongoing speech
  stopPastLifeDoctorReading();
  pastLifeStudioState.isDoctorSpeaking = true;

  const speakingBanner = document.getElementById('plmAiSpeakingBanner');
  const speakingWave = document.getElementById('plmSpeakingWave');
  if (speakingBanner) speakingBanner.style.display = 'flex';
  if (speakingWave) speakingWave.style.display = 'flex';

  const langCode = (lang && (lang.startsWith('bn') || lang.startsWith('hi') || lang.startsWith('en'))) ? lang.substring(0, 2) : (lang || 'en');

  let callbackFired = false;
  const finishOnce = () => {
    if (seqId !== pastLifeQuestionSequenceId) return;
    if (!callbackFired) {
      callbackFired = true;
      if (pastLifeTtsWatchdog) {
        clearTimeout(pastLifeTtsWatchdog);
        pastLifeTtsWatchdog = null;
      }
      pastLifeStudioState.isDoctorSpeaking = false;
      if (speakingWave) speakingWave.style.display = 'none';
      if (onEndCallback) onEndCallback();
    }
  };

  // Watchdog timer: automatically open mic if speech synthesis takes too long or is blocked
  const words = text.split(/\s+/).filter(Boolean).length;
  const maxSpeakTime = Math.max(2500, Math.min(12000, words * 420 + 1500));
  pastLifeTtsWatchdog = setTimeout(() => {
    if (seqId === pastLifeQuestionSequenceId && pastLifeStudioState.isDoctorSpeaking) {
      console.debug('[PastLife TTS Watchdog] Reading duration reached, opening microphone.');
      finishOnce();
    }
  }, maxSpeakTime);

  // 2. Primary Engine: Studio-Grade Neural Edge TTS via Voicebox
  if (window.VoiceboxPipeline) {
    try {
      const persona = window.VoiceboxPipeline.getPersonaForLanguage(langCode);
      const onEndHandler = () => {
        window.VoiceboxPipeline.onSpeechEndCallbacks.delete(onEndHandler);
        if (seqId === pastLifeQuestionSequenceId) {
          finishOnce();
        }
      };
      window.VoiceboxPipeline.onSpeechEndCallbacks.add(onEndHandler);

      window.VoiceboxPipeline.speak(text, persona)
        .then(() => {
          if (seqId === pastLifeQuestionSequenceId) {
            setTimeout(finishOnce, 100);
          }
        })
        .catch((err) => {
          console.debug('[PastLife] Voicebox primary note:', err);
          window.VoiceboxPipeline.onSpeechEndCallbacks.delete(onEndHandler);
          if (seqId === pastLifeQuestionSequenceId && pastLifeStudioState.isDoctorSpeaking) {
            fallbackNativeTTS(text, langCode, finishOnce);
          }
        });
      return;
    } catch (err) {
      console.debug('[PastLife] Voicebox init note:', err);
    }
  }

  // Instant fallback to native Web Speech (starts in <50ms without network roundtrip delay)
  fallbackNativeTTS(text, langCode, finishOnce);
}

function fallbackNativeTTS(text, langCode, onEndCallback) {
  if (!window.speechSynthesis) {
    if (onEndCallback) onEndCallback();
    return;
  }
  const utterance = new SpeechSynthesisUtterance(text);
  if (langCode === 'bn') utterance.lang = 'bn-IN';
  else if (langCode === 'hi') utterance.lang = 'hi-IN';
  else utterance.lang = 'en-US';

  utterance.rate = 0.94;
  utterance.pitch = 0.98;

  utterance.onend = () => {
    if (onEndCallback) onEndCallback();
  };
  utterance.onerror = () => {
    if (onEndCallback) onEndCallback();
  };

  pastLifeStudioState.speechSynthUtterance = utterance;
  window.speechSynthesis.speak(utterance);
}

let plmAudioContext = null;
let plmScriptProcessor = null;
let plmMediaStreamSource = null;
let plmMediaStream = null;
let plmAudioBuffers = [];
let plmPreRollBuffers = [];
let plmIsSpeaking = false;
let plmSilenceStartTime = 0;
let plmTranscribing = false;
let plmAccumulatedTranscript = '';
let plmNoiseFloor = 0.004;
let plmCalibrationFrames = 0;

function startPastLifeAudioCapture() {
  if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    navigator.mediaDevices.getUserMedia({ 
      audio: { 
        echoCancellation: true, 
        noiseSuppression: true, 
        autoGainControl: true,
        channelCount: 1
      } 
    })
    .then((stream) => {
      plmMediaStream = stream;
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (!AudioContextClass) return;

      if (!plmAudioContext || plmAudioContext.state === 'closed') {
        plmAudioContext = new AudioContextClass();
      }
      if (plmAudioContext.state === 'suspended') {
        plmAudioContext.resume().catch(() => {});
      }

      if (plmMediaStreamSource) {
        try { plmMediaStreamSource.disconnect(); } catch (e) {}
      }
      plmMediaStreamSource = plmAudioContext.createMediaStreamSource(stream);

      if (plmScriptProcessor) {
        try { plmScriptProcessor.disconnect(); } catch (e) {}
      }
      plmAudioBuffers = [];
      plmPreRollBuffers = [];
      plmIsSpeaking = false;
      plmSilenceStartTime = 0;
      plmTranscribing = false;
      plmNoiseFloor = 0.004;
      plmCalibrationFrames = 0;

      // Sensitive buffer processor (4096 samples ≈ 92ms at 44.1kHz)
      plmScriptProcessor = plmAudioContext.createScriptProcessor(4096, 1, 1);
      plmScriptProcessor.onaudioprocess = (e) => {
        if (!pastLifeStudioState.isOpen) return;

        const inputData = e.inputBuffer.getChannelData(0);
        const chunk = new Float32Array(inputData.length);
        chunk.set(inputData);

        let sumSquares = 0;
        for (let i = 0; i < chunk.length; i++) {
          sumSquares += chunk[i] * chunk[i];
        }
        const rms = Math.sqrt(sumSquares / chunk.length);

        // Adaptive noise floor tracking: learn ambient noise baseline
        if (plmCalibrationFrames < 12) {
          plmNoiseFloor = (plmNoiseFloor * plmCalibrationFrames + rms) / (plmCalibrationFrames + 1);
          plmCalibrationFrames++;
        }

        const vadThreshold = Math.max(0.0075, plmNoiseFloor * 2.0);
        const isVoiceActive = rms > vadThreshold;

        // Generous rolling pre-roll buffer (~1.5 seconds / 16 chunks) to NEVER miss initial words
        plmPreRollBuffers.push(chunk);
        if (plmPreRollBuffers.length > 16) {
          plmPreRollBuffers.shift();
        }

        if (isVoiceActive) {
          // If doctor voice was still reading, user voice interrupts immediately!
          if (pastLifeStudioState.isDoctorSpeaking) {
            stopPastLifeDoctorReading();
          }

          if (!plmIsSpeaking) {
            plmIsSpeaking = true;
            // Prepend full pre-roll buffer to capture initial words completely
            while (plmPreRollBuffers.length > 0) {
              plmAudioBuffers.push(plmPreRollBuffers.shift());
            }
          }
          plmSilenceStartTime = 0;
          plmAudioBuffers.push(chunk);
          if (plmAudioBuffers.length > 600) plmAudioBuffers.shift(); // ~55s max buffer

          const micDot = document.getElementById('plmMicStateDot');
          if (micDot) micDot.className = 'plm-mic-state-dot active';
          const micText = document.getElementById('plmMicStateText');
          if (micText && !pastLifeStudioState.isDoctorSpeaking && !plmTranscribing) {
            micText.textContent = (pastLifeStudioState.language === 'bn')
              ? '🎙️ তোমার কথা শুনছি... (রেকর্ডিং চলছে)'
              : (pastLifeStudioState.language === 'hi')
              ? '🎙️ आपकी आवाज़ सुन रहा हूँ... (रिकॉर्डिंग जारी)'
              : '🎙️ Hearing your voice... Speak naturally';
          }

          // Auto-transcribe long continuous monologues (> 8 seconds) so user gets progressive text
          if (plmAudioBuffers.length >= 85 && !plmTranscribing) {
            triggerPastLifeAudioTranscribe();
          }
        } else {
          if (plmIsSpeaking) {
            plmAudioBuffers.push(chunk);

            if (plmSilenceStartTime === 0) {
              plmSilenceStartTime = Date.now();
            } else if (Date.now() - plmSilenceStartTime > 850) {
              // Natural speech pause detected (850ms)
              plmIsSpeaking = false;
              plmSilenceStartTime = 0;

              if (plmAudioBuffers.length >= 2 && !plmTranscribing) {
                triggerPastLifeAudioTranscribe();
              }
            }
          }
        }
      };

      const muteNode = plmAudioContext.createGain();
      muteNode.gain.value = 0; // Prevent feedback
      plmMediaStreamSource.connect(plmScriptProcessor);
      plmScriptProcessor.connect(muteNode);
      muteNode.connect(plmAudioContext.destination);
    })
    .catch((err) => {
      console.debug('[PastLife Audio] Mic access note:', err);
    });
  }
}

function stopPastLifeAudioCapture(shouldTranscribePending = true) {
  // If user spoke and there is pending audio, transcribe before destroying buffers
  if (shouldTranscribePending && plmAudioBuffers && plmAudioBuffers.length >= 2 && !plmTranscribing) {
    triggerPastLifeAudioTranscribe();
  }

  if (plmScriptProcessor) {
    try { plmScriptProcessor.disconnect(); } catch (e) {}
    plmScriptProcessor = null;
  }
  if (plmMediaStreamSource) {
    try { plmMediaStreamSource.disconnect(); } catch (e) {}
    plmMediaStreamSource = null;
  }
  if (plmMediaStream) {
    try { plmMediaStream.getTracks().forEach(t => t.stop()); } catch (e) {}
    plmMediaStream = null;
  }
  if (plmAudioContext && plmAudioContext.state !== 'closed') {
    try { plmAudioContext.close(); } catch (e) {}
    plmAudioContext = null;
  }
  plmPreRollBuffers = [];
  plmIsSpeaking = false;
  plmSilenceStartTime = 0;
}

async function triggerPastLifeAudioTranscribe() {
  if (plmTranscribing || !plmAudioBuffers || plmAudioBuffers.length < 2) {
    return;
  }

  plmTranscribing = true;
  const micText = document.getElementById('plmMicStateText');
  if (micText) micText.textContent = '⚡ Converting voice to text (Voicebox MLX-Audio)...';

  try {
    const sampleRate = plmAudioContext ? plmAudioContext.sampleRate : 44100;
    const buffersToEncode = plmAudioBuffers.slice();
    plmAudioBuffers = []; // Clear for next spoken phrase

    const wavBlob = encodeWAVFromBuffers(buffersToEncode, sampleRate);
    if (!wavBlob || wavBlob.size < 100) {
      if (micText) micText.textContent = 'Listening for your answer... Speak or type below';
      return;
    }

    const currentLang = pastLifeStudioState.language || 'en';
    const currQ = pastLifeStudioState.currentQuestion;
    const qid = currQ ? (currQ.id || currQ.question_id || '') : '';
    const sid = pastLifeStudioState.sessionId || '';

    let transcribed = '';
    let engineUsed = 'Voicebox MLX-Audio STT';

    // 1. Primary Engine: VoiceboxTranscriber (MLX-Audio)
    if (window.VoiceboxTranscriber) {
      try {
        const vbRes = await window.VoiceboxTranscriber.transcribeBlob(wavBlob, currentLang, {
          analyzeTone: true,
          sessionId: sid,
          questionId: qid
        });
        if (vbRes && vbRes.text && vbRes.text.trim()) {
          transcribed = vbRes.text.trim();
          engineUsed = vbRes.engine || engineUsed;
        }
      } catch (vbErr) {
        console.debug('[PastLife VoiceboxTranscriber note]:', vbErr);
      }
    }

    // 2. Direct /api/voicebox/transcribe fallback
    if (!transcribed) {
      try {
        const formData = new FormData();
        formData.append('audio', wavBlob, 'past_life_answer.wav');
        let url = `/api/voicebox/transcribe?language=${encodeURIComponent(currentLang)}&analyze_tone=true`;
        if (sid) url += `&session_id=${encodeURIComponent(sid)}`;
        if (qid) url += `&question_id=${encodeURIComponent(qid)}`;

        const res = await fetch(url, {
          method: 'POST',
          body: formData
        });

        if (res.ok) {
          const data = await res.json();
          if (data.status === 'success' && (data.transcription || data.text)) {
            transcribed = (data.transcription || data.text).trim();
            engineUsed = data.engine_used || engineUsed;
          }
        }
      } catch (e) {
        console.debug('[PastLife /api/voicebox/transcribe fallback]:', e);
      }
    }

    // 3. Fallback Engine: Unified /api/transcribe
    if (!transcribed) {
      try {
        const formData = new FormData();
        formData.append('audio', wavBlob, 'past_life_answer.wav');
        let url = `/api/transcribe?language=${encodeURIComponent(currentLang)}&analyze_tone=true`;
        if (sid) url += `&session_id=${encodeURIComponent(sid)}`;
        if (qid) url += `&question_id=${encodeURIComponent(qid)}`;

        const res = await fetch(url, {
          method: 'POST',
          body: formData
        });

        if (res.ok) {
          const data = await res.json();
          if (data.status === 'success' && (data.transcription || data.text)) {
            transcribed = (data.transcription || data.text).trim();
            engineUsed = data.engine_used || 'Faster-Whisper';
          }
        }
      } catch (e) {
        console.debug('[PastLife /api/transcribe fallback]:', e);
      }
    }

    if (transcribed && transcribed.length > 0) {
      const answerInput = document.getElementById('plmAnswerInput');
      if (answerInput) {
        const existingVal = answerInput.value.trim();
        if (existingVal.length > 0) {
          const needsPunc = !/[.?!,;:]$/.test(existingVal);
          answerInput.value = existingVal + (needsPunc ? '. ' : ' ') + transcribed;
        } else {
          answerInput.value = transcribed;
        }

        // Visual emerald pulse on the answer window
        answerInput.style.borderColor = '#10b981';
        answerInput.style.boxShadow = '0 0 0 2px rgba(16, 185, 129, 0.25)';
        setTimeout(() => {
          if (answerInput) {
            answerInput.style.borderColor = '';
            answerInput.style.boxShadow = '';
          }
        }, 2500);
      }
      if (micText) micText.textContent = `✓ Captured via ${engineUsed}`;
    } else {
      if (micText) micText.textContent = 'Listening for your answer... Speak or type below';
    }
  } catch (err) {
    console.warn('[PastLife] Transcribe error:', err);
    if (micText) micText.textContent = 'Listening for your answer... Speak or type below';
  } finally {
    plmTranscribing = false;
  }
}

function startPastLifeSpeechRecognition() {
  if (pastLifeStudioState.isDoctorSpeaking) return; // Strict gating while question is being read

  pastLifeStudioState.isRecognitionActive = true;
  const micBtn = document.getElementById('plmMicToggleBtn');
  if (micBtn) micBtn.classList.add('active');
  const micLabel = document.getElementById('plmMicToggleLabel');
  if (micLabel) micLabel.textContent = 'Mic Listening';
  const micDot = document.getElementById('plmMicStateDot');
  if (micDot) micDot.className = 'plm-mic-state-dot active';

  // 1. Always start parallel Live Audio Capture & Whisper VAD engine (universal across Brave, Chrome, Firefox, Safari)
  startPastLifeAudioCapture();

  // 2. Clean up any existing Web Speech instance without killing AudioCapture
  if (pastLifeStudioState.recognition) {
    try {
      pastLifeStudioState.recognition.onend = null;
      pastLifeStudioState.recognition.stop();
    } catch(e) {}
    pastLifeStudioState.recognition = null;
  }

  // 3. Start Web Speech API for real-time live typing animation
  const SpeechRecognitionClass = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognitionClass) {
    return;
  }

  try {
    const recognition = new SpeechRecognitionClass();
    recognition.continuous = true;
    recognition.interimResults = true;
    
    const lang = pastLifeStudioState.language;
    if (lang === 'bn') recognition.lang = 'bn-IN';
    else if (lang === 'hi') recognition.lang = 'hi-IN';
    else recognition.lang = 'en-US';

    plmAccumulatedTranscript = '';

    recognition.onresult = (event) => {
      if (pastLifeStudioState.isDoctorSpeaking) return;

      let currentInterim = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const res = event.results[i];
        if (res.isFinal) {
          plmAccumulatedTranscript += (plmAccumulatedTranscript ? ' ' : '') + res[0].transcript.trim();
        } else {
          currentInterim += res[0].transcript;
        }
      }

      const fullText = (plmAccumulatedTranscript + (currentInterim ? ' ' + currentInterim : '')).trim();
      const answerInput = document.getElementById('plmAnswerInput');
      if (answerInput && fullText.length > 0) {
        answerInput.value = fullText;
      }
    };

    recognition.onerror = (event) => {
      console.debug('[PastLife STT] Web Speech notice:', event.error);
    };

    recognition.onend = () => {
      if (pastLifeStudioState.isOpen && !pastLifeStudioState.isDoctorSpeaking && pastLifeStudioState.isRecognitionActive) {
        try {
          recognition.start();
        } catch(e) {}
      }
    };

    recognition.start();
    pastLifeStudioState.recognition = recognition;
  } catch (err) {
    console.debug('Speech recognition init notice:', err);
  }
}

function stopPastLifeSpeechRecognition() {
  stopPastLifeAudioCapture();
  if (pastLifeStudioState.recognition) {
    try {
      pastLifeStudioState.recognition.onend = null;
      pastLifeStudioState.recognition.stop();
    } catch(e) {}
    pastLifeStudioState.recognition = null;
  }
  pastLifeStudioState.isRecognitionActive = false;
}

async function submitCurrentPastLifeAnswer(isSkip = false) {
  const answerInput = document.getElementById('plmAnswerInput');
  
  // If user didn't type and has pending voice buffer, transcribe it first!
  if (!isSkip && (!answerInput || answerInput.value.trim().length === 0) && plmAudioBuffers.length >= 2) {
    const micText = document.getElementById('plmMicStateText');
    if (micText) micText.textContent = 'Transcribing voice answer before submitting...';
    await triggerPastLifeAudioTranscribe();
  }

  let answerText = answerInput ? answerInput.value.trim() : '';

  if (isSkip || answerText.length === 0) {
    answerText = (pastLifeStudioState.language === 'bn') ? 'Skip' : (pastLifeStudioState.language === 'hi') ? 'Skip' : 'Skip';
  }

  // Stop recording & TTS
  stopPastLifeSpeechRecognition();
  if (pastLifeStudioState.activeAudioElement) {
    try { pastLifeStudioState.activeAudioElement.pause(); } catch(e) {}
  }
  if (window.speechSynthesis) window.speechSynthesis.cancel();
  if (window.VoiceboxPipeline) window.VoiceboxPipeline.stop(0.01);

  // Show loading indicator on button
  const submitBtn = document.getElementById('plmSubmitNextBtn');
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<span>Saving...</span> <i data-lucide="loader-2" class="spin"></i>`;
    if (window.lucide) window.lucide.createIcons();
  }

  try {
    const res = await fetch('/api/past-life/answer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: pastLifeStudioState.sessionId,
        user_id: state.userId,
        answer: answerText,
        is_audio: pastLifeStudioState.isRecognitionActive,
        input_mode: 'voice_or_text'
      })
    });

    const data = await res.json();
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.innerHTML = `<span id="plmSubmitBtnLabel">Next Question</span> <i data-lucide="arrow-right"></i>`;
    }

    if (data.status === 'success' && data.result) {
      const result = data.result;

      if (result.is_complete && result.analysis) {
        // Complete! Render Results Stage inside modal
        renderPastLifeResults(result.analysis);
      } else {
        // Advance to next question
        pastLifeStudioState.currentIndex = result.current_index;
        pastLifeStudioState.totalQuestions = result.total_questions;
        pastLifeStudioState.currentQuestion = {
          id: result.question_id,
          question_text: result.question_text,
          gentle_support: result.gentle_support,
          suggested_chips: result.suggested_chips,
          category: 'Life Reflection'
        };
        renderCurrentPastLifeQuestion();
      }
    }
  } catch (err) {
    console.error('Error submitting answer:', err);
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.innerHTML = `<span id="plmSubmitBtnLabel">Next Question</span> <i data-lucide="arrow-right"></i>`;
    }
  }
}

function renderPastLifeResults(analysis) {
  if (!analysis) return;

  // Stop recording & TTS
  stopPastLifeSpeechRecognition();
  if (pastLifeStudioState.activeAudioElement) {
    try { pastLifeStudioState.activeAudioElement.pause(); } catch(e) {}
  }
  if (window.speechSynthesis) window.speechSynthesis.cancel();

  const qStage = document.getElementById('plmQuestionStage');
  const rStage = document.getElementById('plmResultsStage');
  const rContent = document.getElementById('plmResultsContent');

  if (qStage) qStage.style.display = 'none';
  if (rStage) rStage.style.display = 'flex';

  const archetype = analysis.primary_archetype || 'Reflective & Balanced';
  const nostalgia = analysis.nostalgia_index || 65;
  const resilience = analysis.resilience_index || 70;
  const trust = analysis.trust_index || 60;
  const load = analysis.processing_load || 'Balanced Processing';
  const loadColor = analysis.load_color || '#10b981';

  let formattedReport = (analysis.narrative_report || '')
    .replace(/###\s*(.*?)(?=\n|$)/g, '<h3 style="color:#ffffff; margin: 0.5rem 0;">$1</h3>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code style="background: rgba(56,189,248,0.15); color: #38bdf8; padding: 2px 6px; border-radius: 4px;">$1</code>')
    .replace(/•\s*(.*?)(?=\n|$)/g, '<li style="margin-bottom: 0.35rem;">$1</li>')
    .replace(/\n\n/g, '<br><br>')
    .replace(/\n/g, '<br>');

  if (rContent) {
    rContent.innerHTML = `
      <div class="pla-metrics-grid">
        <div class="pla-metric-box">
          <div class="pla-metric-title">Nostalgia & Emotional Warmth</div>
          <div class="pla-metric-value-row">
            <span class="pla-metric-val">${nostalgia}/100</span>
            <span style="font-size: 0.72rem; color: #38bdf8;">Comfort in Memory</span>
          </div>
          <div class="pla-metric-bar">
            <div class="pla-metric-fill" style="width: ${nostalgia}%; background: linear-gradient(90deg, #38bdf8, #0ea5e9);"></div>
          </div>
        </div>

        <div class="pla-metric-box">
          <div class="pla-metric-title">Resilience & Inner Growth</div>
          <div class="pla-metric-value-row">
            <span class="pla-metric-val" style="color: #10b981;">${resilience}/100</span>
            <span style="font-size: 0.72rem; color: #10b981;">Meaning-Making</span>
          </div>
          <div class="pla-metric-bar">
            <div class="pla-metric-fill" style="width: ${resilience}%; background: linear-gradient(90deg, #10b981, #059669);"></div>
          </div>
        </div>

        <div class="pla-metric-box">
          <div class="pla-metric-title">Relational Trust & Openness</div>
          <div class="pla-metric-value-row">
            <span class="pla-metric-val" style="color: #8b5cf6;">${trust}/100</span>
            <span style="font-size: 0.72rem; color: #8b5cf6;">Safe Attachment</span>
          </div>
          <div class="pla-metric-bar">
            <div class="pla-metric-fill" style="width: ${trust}%; background: linear-gradient(90deg, #8b5cf6, #7c3aed);"></div>
          </div>
        </div>

        <div class="pla-metric-box">
          <div class="pla-metric-title">Emotional Processing Load</div>
          <div class="pla-metric-value-row">
            <span class="pla-metric-val" style="color: ${loadColor}; font-size: 1.05rem;">${load}</span>
          </div>
          <div class="pla-metric-bar">
            <div class="pla-metric-fill" style="width: 100%; background: ${loadColor};"></div>
          </div>
        </div>
      </div>

      <div class="pla-narrative-text">
        ${formattedReport}
      </div>
    `;
  }

  // Also append into the main chat stream so it's recorded
  renderPastLifeAnalysisCard(analysis);

  if (window.lucide) window.lucide.createIcons();
}

function closePastLifeModal() {
  pastLifeStudioState.isOpen = false;
  stopPastLifeSpeechRecognition();
  if (pastLifeStudioState.activeAudioElement) {
    try { pastLifeStudioState.activeAudioElement.pause(); } catch(e) {}
  }
  if (window.speechSynthesis) window.speechSynthesis.cancel();

  const modal = document.getElementById('pastLifeModal');
  if (modal) modal.style.display = 'none';
}

function startPastLifeInterview(lang = 'en', mode = 'short') {
  openPastLifeModal(lang, mode);
}

function renderPastLifeAnalysisCard(analysis) {
  if (!analysis || !elements.chatMessages) return;

  const card = document.createElement('div');
  card.className = 'past-life-analysis-card animate-fade-in';

  const archetype = analysis.primary_archetype || 'Reflective & Balanced';
  const nostalgia = analysis.nostalgia_index || 65;
  const resilience = analysis.resilience_index || 70;
  const trust = analysis.trust_index || 60;
  const load = analysis.processing_load || 'Balanced Processing';
  const loadColor = analysis.load_color || '#10b981';

  card.innerHTML = `
    <div class="pla-header">
      <div class="pla-title">
        <i data-lucide="sparkles" style="color: #10b981;"></i>
        <span>Life Reflection & Mental State Synthesis</span>
      </div>
      <div class="pla-archetype-tag">${archetype}</div>
    </div>

    <div class="pla-metrics-grid">
      <div class="pla-metric-box">
        <div class="pla-metric-title">Nostalgia & Emotional Warmth</div>
        <div class="pla-metric-value-row">
          <span class="pla-metric-val">${nostalgia}/100</span>
          <span style="font-size: 0.72rem; color: #38bdf8;">Comfort in Memory</span>
        </div>
        <div class="pla-metric-bar">
          <div class="pla-metric-fill" style="width: ${nostalgia}%; background: linear-gradient(90deg, #38bdf8, #0ea5e9);"></div>
        </div>
      </div>

      <div class="pla-metric-box">
        <div class="pla-metric-title">Resilience & Inner Growth</div>
        <div class="pla-metric-value-row">
          <span class="pla-metric-val" style="color: #10b981;">${resilience}/100</span>
          <span style="font-size: 0.72rem; color: #10b981;">Meaning-Making</span>
        </div>
        <div class="pla-metric-bar">
          <div class="pla-metric-fill" style="width: ${resilience}%; background: linear-gradient(90deg, #10b981, #059669);"></div>
        </div>
      </div>

      <div class="pla-metric-box">
        <div class="pla-metric-title">Relational Trust & Openness</div>
        <div class="pla-metric-value-row">
          <span class="pla-metric-val" style="color: #8b5cf6;">${trust}/100</span>
          <span style="font-size: 0.72rem; color: #8b5cf6;">Safe Attachment</span>
        </div>
        <div class="pla-metric-bar">
          <div class="pla-metric-fill" style="width: ${trust}%; background: linear-gradient(90deg, #8b5cf6, #7c3aed);"></div>
        </div>
      </div>

      <div class="pla-metric-box">
        <div class="pla-metric-title">Emotional Processing Load</div>
        <div class="pla-metric-value-row">
          <span class="pla-metric-val" style="color: ${loadColor}; font-size: 1.05rem;">${load}</span>
        </div>
        <div class="pla-metric-bar">
          <div class="pla-metric-fill" style="width: 100%; background: ${loadColor};"></div>
        </div>
      </div>
    </div>

    <div class="pla-actions-row">
      <button type="button" class="pla-action-btn" onclick="openPastLifeModal(pastLifeStudioState.language, 'full')">
        <i data-lucide="book-open"></i>
        <span>Explore Full 13-Question Journey</span>
      </button>
      <button type="button" class="pla-action-btn" onclick="openBreathingModal()">
        <i data-lucide="wind"></i>
        <span>Calm Integration (4-7-8 Breath)</span>
      </button>
      <button type="button" class="pla-action-btn" onclick="switchTab('providers')">
        <i data-lucide="user-check"></i>
        <span>Speak with a Therapist</span>
      </button>
    </div>
  `;

  elements.chatMessages.appendChild(card);
  elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
  if (window.lucide) window.lucide.createIcons();
}

function initPastLifeTools() {
  const quickPastLifeBtn = document.getElementById('quickPastLifeBtn');
  const pastLifePopupMenu = document.getElementById('pastLifePopupMenu');
  const closeBtn = document.getElementById('closePastLifeModalBtn');
  const submitNextBtn = document.getElementById('plmSubmitNextBtn');
  const skipBtn = document.getElementById('plmSkipBtn');
  const modeSwitchBtn = document.getElementById('plmModeSwitchBtn');
  const micToggleBtn = document.getElementById('plmMicToggleBtn');
  const ttsReplayBtn = document.getElementById('plmTtsReplayBtn');
  const doneReturnBtn = document.getElementById('plmDoneReturnBtn');
  const restartBtn = document.getElementById('plmRestartBtn');

  if (quickPastLifeBtn && pastLifePopupMenu) {
    quickPastLifeBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const isShowing = pastLifePopupMenu.style.display === 'flex' || pastLifePopupMenu.style.display === 'block';
      closeAllConsolePopups();
      if (!isShowing) {
        pastLifePopupMenu.style.display = 'flex';
      }
    });

    pastLifePopupMenu.querySelectorAll('.past-life-opt').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        closeAllConsolePopups();
        const lang = btn.getAttribute('data-lang') || 'en';
        const mode = btn.getAttribute('data-mode') || 'short';
        openPastLifeModal(lang, mode);
      });
    });
  }

  if (closeBtn) {
    closeBtn.addEventListener('click', closePastLifeModal);
  }

  if (submitNextBtn) {
    submitNextBtn.addEventListener('click', () => submitCurrentPastLifeAnswer(false));
  }

  if (skipBtn) {
    skipBtn.addEventListener('click', () => submitCurrentPastLifeAnswer(true));
  }

  if (modeSwitchBtn) {
    modeSwitchBtn.addEventListener('click', () => {
      const newMode = (pastLifeStudioState.mode === 'short') ? 'full' : 'short';
      openPastLifeModal(pastLifeStudioState.language, newMode);
    });
  }

  if (micToggleBtn) {
    micToggleBtn.addEventListener('click', () => {
      // If doctor was reading question, interrupt and immediately start listening to user
      if (pastLifeStudioState.isDoctorSpeaking) {
        pastLifeStudioState.isDoctorSpeaking = false;
        if (pastLifeStudioState.activeAudioElement) {
          try { pastLifeStudioState.activeAudioElement.pause(); } catch(e) {}
        }
        if (window.VoiceboxPipeline) window.VoiceboxPipeline.stop(0.01);
        if (window.speechSynthesis) window.speechSynthesis.cancel();
        stopSpeaking();
        const speakingWave = document.getElementById('plmSpeakingWave');
        if (speakingWave) speakingWave.style.display = 'none';
        const speakingBanner = document.getElementById('plmAiSpeakingBanner');
        if (speakingBanner) speakingBanner.style.display = 'none';
      }

      if (pastLifeStudioState.isRecognitionActive) {
        stopPastLifeSpeechRecognition();
        micToggleBtn.classList.remove('active');
        const micLabel = document.getElementById('plmMicToggleLabel');
        if (micLabel) micLabel.textContent = 'Mic Muted';
        const micDot = document.getElementById('plmMicStateDot');
        if (micDot) micDot.className = 'plm-mic-state-dot';
        const micText = document.getElementById('plmMicStateText');
        if (micText) micText.textContent = 'Mic paused. Click "Mic Muted" or type your answer';
      } else {
        startPastLifeSpeechRecognition();
        micToggleBtn.classList.add('active');
        const micLabel = document.getElementById('plmMicToggleLabel');
        if (micLabel) micLabel.textContent = 'Mic Listening';
        const micDot = document.getElementById('plmMicStateDot');
        if (micDot) micDot.className = 'plm-mic-state-dot active';
        const micText = document.getElementById('plmMicStateText');
        if (micText) micText.textContent = 'Listening for your answer... Speak or type below';
      }
    });
  }

  if (ttsReplayBtn) {
    ttsReplayBtn.addEventListener('click', () => {
      if (pastLifeStudioState.currentQuestion) {
        pastLifeStudioState.isDoctorSpeaking = true;
        stopPastLifeSpeechRecognition();
        const speakingWave = document.getElementById('plmSpeakingWave');
        if (speakingWave) speakingWave.style.display = 'flex';
        speakPastLifeQuestion(pastLifeStudioState.currentQuestion.question_text, pastLifeStudioState.language, () => {
          pastLifeStudioState.isDoctorSpeaking = false;
          if (speakingWave) speakingWave.style.display = 'none';
          startPastLifeSpeechRecognition();
        });
      }
    });
  }

  if (doneReturnBtn) {
    doneReturnBtn.addEventListener('click', closePastLifeModal);
  }

  if (restartBtn) {
    restartBtn.addEventListener('click', () => {
      openPastLifeModal(pastLifeStudioState.language, pastLifeStudioState.mode);
    });
  }

  document.querySelectorAll('.plm-lang-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const lang = btn.getAttribute('data-lang') || 'en';
      openPastLifeModal(lang, pastLifeStudioState.mode);
    });
  });
}

// ==========================================================================
// EMOTION-FOCUSED INTERVIEW CONTROLLER & ZERO-GLITCH VOICE STUDIO
// ==========================================================================


const emotionInterviewState = {
  isOpen: false,
  inviteOpen: false,
  sessionId: null,
  language: 'en',
  currentIndex: 0,
  totalQuestions: 10,
  currentQuestion: null,
  isDoctorSpeaking: false,
  isRecording: false,
  isTranscribing: false,
  isReviewing: false,
  speechSynthUtterance: null,
  activeAudioElement: null
};

let eimAudioContext = null;
let eimScriptProcessor = null;
let eimMediaStreamSource = null;
let eimMediaStream = null;
let eimAudioBuffers = [];
let eimPreRollBuffers = [];
let eimIsSpeaking = false;
let eimSilenceStartTime = 0;
let eimTranscribing = false;
let eimNoiseFloor = 0.004;
let eimCalibrationFrames = 0;
let eimQuestionSequenceId = 0;
let eimTtsWatchdog = null;

function showEmotionInviteModal(detectionData) {
  if (emotionInterviewState.isOpen || pastLifeStudioState.isOpen) return;

  const modal = document.getElementById('emotionInviteModal');
  if (!modal) return;

  emotionInterviewState.inviteOpen = true;
  modal.style.display = 'flex';
  modal.classList.add('active');

  const lang = state.selectedLanguage && state.selectedLanguage.startsWith('bn') ? 'bn' : state.selectedLanguage && state.selectedLanguage.startsWith('hi') ? 'hi' : 'en';
  emotionInterviewState.language = lang;

  const titleElem = document.getElementById('emotionInviteTitle');
  const msgElem = document.getElementById('emotionInviteMessage');

  if (lang === 'bn') {
    if (titleElem) titleElem.textContent = 'চলুন আপনার অনুভূতিগুলো নিয়ে একটু খোলামেলা কথা বলি';
    if (msgElem) msgElem.textContent = 'বোঝা যাচ্ছে আপনি বর্তমানে গভীর মানসিক অনুভূতির মধ্য দিয়ে যাচ্ছেন। আপনি কি আপনার অনুভূতি সম্পর্কে কয়েকটি সহজ ও শান্ত প্রশ্নের উত্তর দিতে চান? আপনি মুখে বলে বা লিখে উত্তর দিতে পারেন এবং যেকোনো প্রশ্ন এড়িয়ে যাওয়ার স্বাধীনতা আপনার রয়েছে।';
  } else if (lang === 'hi') {
    if (titleElem) titleElem.textContent = 'आइए अपनी भावनाओं को थोड़ा और गहराई से समझें';
    if (msgElem) msgElem.textContent = 'ऐसा लगता है कि आप इस समय भावनात्मक रूप से काफी कुछ महसूस कर रहे हैं। क्या आप अपनी भावनाओं के बारे में कुछ सरल और सौम्य सवालों के जवाब देना चाहेंगे? आप बोलकर या लिखकर जवाब दे सकते हैं और किसी भी सवाल को छोड़ भी सकते हैं।';
  } else {
    if (titleElem) titleElem.textContent = 'Let’s explore your feelings a bit more';
    if (msgElem) msgElem.textContent = 'It sounds like you’re going through a lot emotionally right now. Would you be willing to answer a few gentle questions about how you’ve been feeling? You can answer by voice or text, and you can skip any question you don’t feel comfortable answering.';
  }

  if (window.lucide) window.lucide.createIcons();
}

function closeEmotionInviteModal() {
  emotionInterviewState.inviteOpen = false;
  const modal = document.getElementById('emotionInviteModal');
  if (modal) {
    modal.style.display = 'none';
    modal.classList.remove('active');
  }
}

async function startEmotionInterviewFromInvite() {
  closeEmotionInviteModal();
  openEmotionInterviewModal(emotionInterviewState.language);
}

async function openEmotionInterviewModal(lang = 'en', mode = 'normal') {
  emotionInterviewState.isOpen = true;
  emotionInterviewState.language = lang;
  emotionInterviewState.currentIndex = 0;
  emotionInterviewState.isReviewing = false;
  emotionInterviewState.mode = mode;

  const modal = document.getElementById('emotionInterviewModal');
  if (modal) {
    modal.style.display = 'flex';
    modal.classList.add('active');
  }

  // Update inside modal language switcher buttons
  document.querySelectorAll('.eim-lang-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-lang') === lang);
  });

  const qStage = document.getElementById('eimQuestionStage');
  const rStage = document.getElementById('eimResultsStage');
  if (qStage) qStage.style.display = 'flex';
  if (rStage) rStage.style.display = 'none';

  // Request session start from API
  try {
    if (mode === 'fallback') {
      const res = await fetch('/api/start-fallback-emotion-interview', { method: 'POST' });
      const data = await res.json();
      if (data.status === 'success') {
        emotionInterviewState.sessionId = data.session_id;
        emotionInterviewState.fallbackData = data.interview_data;
        emotionInterviewState.totalQuestions = data.interview_data.questions.length;
        emotionInterviewState.fallbackAnswers = [];
        
        const firstQ = data.interview_data.questions[0];
        emotionInterviewState.currentQuestion = {
          id: firstQ.id,
          text: firstQ.question_text[lang] || firstQ.question_text['en']
        };
        renderCurrentEmotionQuestion();
      }
    } else {
      const res = await fetch('/api/emotion-interview/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: state.userId,
          conversation_id: state.conversationId,
          language: lang,
          trigger_reason: 'user_emotional_expression'
        })
      });
      const data = await res.json();
      if (data.status === 'success' && data.session) {
        emotionInterviewState.sessionId = data.session.session_id;
        emotionInterviewState.currentIndex = data.session.current_index;
        emotionInterviewState.totalQuestions = data.session.total_questions;
        emotionInterviewState.currentQuestion = data.session.question;
        renderCurrentEmotionQuestion();
      }
    }
  } catch (err) {
    console.error('Failed to start emotion interview session:', err);
  }
}

function closeEmotionInterviewModal() {
  emotionInterviewState.isOpen = false;
  stopEmotionDoctorReading();
  stopEmotionAudioCapture(false);

  const modal = document.getElementById('emotionInterviewModal');
  if (modal) {
    modal.style.display = 'none';
    modal.classList.remove('active');
  }
}

function renderCurrentEmotionQuestion() {
  const q = emotionInterviewState.currentQuestion;
  if (!q) return;

  // Update question index & progress
  const currNum = emotionInterviewState.currentIndex + 1;
  const total = emotionInterviewState.totalQuestions || 10;
  const pct = Math.round((currNum / total) * 100);

  const progLabel = document.getElementById('eimProgressLabel');
  const themeLabel = document.getElementById('eimThemeLabel');
  const progFill = document.getElementById('eimProgressFill');
  const qBadge = document.getElementById('eimQBadge');
  const qText = document.getElementById('eimQuestionText');
  const qQuote = document.getElementById('eimSupportQuote');
  const chipsContainer = document.getElementById('eimChipsContainer');
  const answerInput = document.getElementById('eimAnswerInput');
  const submitLabel = document.getElementById('eimSubmitBtnLabel');
  const reviewNotice = document.getElementById('eimReviewNotice');
  const rerecordBtn = document.getElementById('eimRerecordBtn');
  const finishBtn = document.getElementById('eimFinishSpeakingBtn');

  if (progLabel) progLabel.textContent = `Question ${currNum} of ${total}`;
  if (themeLabel) themeLabel.textContent = (q.theme || 'Emotional Check-in').replace(/_/g, ' ').toUpperCase();
  if (progFill) progFill.style.width = `${pct}%`;
  if (qBadge) qBadge.textContent = `Question ${currNum}`;
  if (qText) qText.textContent = q.question_text || '';
  if (qQuote) qQuote.textContent = q.gentle_support || '';
  if (answerInput) answerInput.value = '';
  if (submitLabel) submitLabel.textContent = (currNum === total) ? 'Confirm & Synthesize Profile' : 'Confirm Answer & Next';
  if (reviewNotice) reviewNotice.style.display = 'none';
  if (rerecordBtn) rerecordBtn.style.display = 'none';
  if (finishBtn) finishBtn.style.display = 'none';

  // Render Suggested Quick Reply Chips
  if (chipsContainer) {
    chipsContainer.innerHTML = '';
    const chips = q.suggested_chips || [];
    chips.forEach(chipText => {
      const chip = document.createElement('button');
      chip.type = 'button';
      chip.className = 'eim-chip';
      chip.textContent = chipText;
      chip.addEventListener('click', () => {
        stopEmotionDoctorReading();
        if (answerInput) {
          const current = answerInput.value.trim();
          answerInput.value = current ? `${current}. ${chipText}` : chipText;
          enterEmotionReviewState(answerInput.value);
        }
      });
      chipsContainer.appendChild(chip);
    });
  }

  // Question voice read-aloud via Voicebox Studio
  speakEmotionQuestion(q.question_text, emotionInterviewState.language, () => {
    // When read-aloud completes, automatically arm the microphone
    startEmotionAudioCapture();
  });

  if (window.lucide) window.lucide.createIcons();
}

function stopEmotionDoctorReading() {
  emotionInterviewState.isDoctorSpeaking = false;
  if (eimTtsWatchdog) {
    clearTimeout(eimTtsWatchdog);
    eimTtsWatchdog = null;
  }
  if (emotionInterviewState.activeAudioElement) {
    try {
      emotionInterviewState.activeAudioElement.pause();
      emotionInterviewState.activeAudioElement = null;
    } catch(e) {}
  }
  if (window.speechSynthesis) {
    window.speechSynthesis.cancel();
  }
  if (window.VoiceboxPipeline) {
    window.VoiceboxPipeline.stop(0.01);
  }
  const speakingWave = document.getElementById('eimSpeakingWave');
  if (speakingWave) speakingWave.style.display = 'none';
  const speakingBanner = document.getElementById('eimAiSpeakingBanner');
  if (speakingBanner) speakingBanner.style.display = 'none';
}

function speakEmotionQuestion(text, lang, onEndCallback) {
  if (!text) {
    if (onEndCallback) onEndCallback();
    return;
  }

  const seqId = ++eimQuestionSequenceId;
  stopEmotionDoctorReading();
  emotionInterviewState.isDoctorSpeaking = true;

  const speakingBanner = document.getElementById('eimAiSpeakingBanner');
  const speakingWave = document.getElementById('eimSpeakingWave');
  if (speakingBanner) speakingBanner.style.display = 'flex';
  if (speakingWave) speakingWave.style.display = 'flex';

  const langCode = (lang && (lang.startsWith('bn') || lang.startsWith('hi') || lang.startsWith('en'))) ? lang.substring(0, 2) : (lang || 'en');

  let callbackFired = false;
  const finishOnce = () => {
    if (seqId !== eimQuestionSequenceId) return;
    if (!callbackFired) {
      callbackFired = true;
      if (eimTtsWatchdog) {
        clearTimeout(eimTtsWatchdog);
        eimTtsWatchdog = null;
      }
      emotionInterviewState.isDoctorSpeaking = false;
      if (speakingWave) speakingWave.style.display = 'none';
      if (onEndCallback) onEndCallback();
    }
  };

  // Dynamic watchdog timer based on question length (increased safety margin)
  const words = text.split(/\s+/).filter(Boolean).length;
  // Increase time allowance for synthesis latency + speech duration.
  // 500ms per word + 8000ms base latency. No strict upper cap that could cut off long Hindi/Bengali sentences.
  const maxSpeakTime = Math.max(8000, words * 500 + 8000);
  eimTtsWatchdog = setTimeout(() => {
    if (seqId === eimQuestionSequenceId && emotionInterviewState.isDoctorSpeaking) {
      console.debug('[Emotion TTS Watchdog] Reading duration reached, unlocking microphone.');
      finishOnce();
    }
  }, maxSpeakTime);

  // Studio-Grade Neural Edge TTS via Voicebox
  if (window.VoiceboxPipeline) {
    try {
      const persona = window.VoiceboxPipeline.getPersonaForLanguage(langCode);
      const onEndHandler = () => {
        window.VoiceboxPipeline.onSpeechEndCallbacks.delete(onEndHandler);
        if (seqId === eimQuestionSequenceId) {
          finishOnce();
        }
      };
      window.VoiceboxPipeline.onSpeechEndCallbacks.add(onEndHandler);

      window.VoiceboxPipeline.speak(text, persona)
        .then(() => {
          if (seqId === eimQuestionSequenceId) {
            setTimeout(finishOnce, 100);
          }
        })
        .catch((err) => {
          console.debug('[Emotion TTS] Voicebox primary note:', err);
          window.VoiceboxPipeline.onSpeechEndCallbacks.delete(onEndHandler);
          if (seqId === eimQuestionSequenceId && emotionInterviewState.isDoctorSpeaking) {
            fallbackNativeTTS(text, langCode, finishOnce);
          }
        });
      return;
    } catch (err) {
      console.debug('[Emotion TTS] Voicebox init note:', err);
    }
  }

  fallbackNativeTTS(text, langCode, finishOnce);
}

function startEmotionAudioCapture() {
  if (emotionInterviewState.isDoctorSpeaking) return;

  const micBtn = document.getElementById('eimMicRecordBtn');
  const micLabel = document.getElementById('eimMicRecordLabel');
  const finishBtn = document.getElementById('eimFinishSpeakingBtn');
  const micDot = document.getElementById('eimMicStateDot');
  const micText = document.getElementById('eimMicStateText');

  if (micBtn) micBtn.classList.add('recording');
  if (micLabel) micLabel.textContent = 'Recording Voice...';
  if (finishBtn) finishBtn.style.display = 'inline-flex';
  if (micDot) micDot.className = 'eim-mic-state-dot active';
  if (micText) micText.textContent = (emotionInterviewState.language === 'bn')
    ? '🎙️ আপনার কথা শুনছি... বলা শেষ হলে "Finish Speaking" চাপুন'
    : (emotionInterviewState.language === 'hi')
    ? '🎙️ आपकी आवाज़ सुन रहा हूँ... बात पूरी होने पर "Finish Speaking" दबाएं'
    : '🎙️ Listening to your voice... Speak naturally, then finish speaking';

  emotionInterviewState.isRecording = true;

  if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    navigator.mediaDevices.getUserMedia({ 
      audio: { 
        echoCancellation: true, 
        noiseSuppression: true, 
        autoGainControl: true,
        channelCount: 1
      } 
    })
    .then((stream) => {
      eimMediaStream = stream;
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (!AudioContextClass) return;

      if (!eimAudioContext || eimAudioContext.state === 'closed') {
        eimAudioContext = new AudioContextClass();
      }
      if (eimAudioContext.state === 'suspended') {
        eimAudioContext.resume().catch(() => {});
      }

      if (eimMediaStreamSource) {
        try { eimMediaStreamSource.disconnect(); } catch (e) {}
      }
      eimMediaStreamSource = eimAudioContext.createMediaStreamSource(stream);

      if (eimScriptProcessor) {
        try { eimScriptProcessor.disconnect(); } catch (e) {}
      }
      eimAudioBuffers = [];
      eimPreRollBuffers = [];
      eimIsSpeaking = false;
      eimSilenceStartTime = 0;
      eimTranscribing = false;
      eimNoiseFloor = 0.004;
      eimCalibrationFrames = 0;

      // 4096 samples ≈ 92ms buffer slice
      eimScriptProcessor = eimAudioContext.createScriptProcessor(4096, 1, 1);
      eimScriptProcessor.onaudioprocess = (e) => {
        if (!emotionInterviewState.isOpen || !emotionInterviewState.isRecording) return;

        const inputData = e.inputBuffer.getChannelData(0);
        const chunk = new Float32Array(inputData.length);
        chunk.set(inputData);

        let sumSquares = 0;
        for (let i = 0; i < chunk.length; i++) sumSquares += chunk[i] * chunk[i];
        const rms = Math.sqrt(sumSquares / chunk.length);

        if (eimCalibrationFrames < 12) {
          eimNoiseFloor = (eimNoiseFloor * eimCalibrationFrames + rms) / (eimCalibrationFrames + 1);
          eimCalibrationFrames++;
        }

        const vadThreshold = Math.max(0.0075, eimNoiseFloor * 2.0);
        const isVoiceActive = rms > vadThreshold;

        eimPreRollBuffers.push(chunk);
        if (eimPreRollBuffers.length > 16) eimPreRollBuffers.shift(); // ~1.5s rolling pre-roll

        if (isVoiceActive) {
          if (emotionInterviewState.isDoctorSpeaking) {
            stopEmotionDoctorReading();
          }

          if (!eimIsSpeaking) {
            eimIsSpeaking = true;
            while (eimPreRollBuffers.length > 0) {
              eimAudioBuffers.push(eimPreRollBuffers.shift());
            }
          }
          eimSilenceStartTime = 0;
          eimAudioBuffers.push(chunk);
          if (eimAudioBuffers.length > 700) eimAudioBuffers.shift(); // ~60s safety cap
        } else {
          if (eimIsSpeaking) {
            eimAudioBuffers.push(chunk);
            if (eimSilenceStartTime === 0) {
              eimSilenceStartTime = Date.now();
            } else if (Date.now() - eimSilenceStartTime > 1500) {
              // 1.5s snappy pause auto-trigger into Review state
              eimIsSpeaking = false;
              eimSilenceStartTime = 0;
              if (eimAudioBuffers.length >= 2 && !eimTranscribing) {
                triggerEmotionAudioTranscribe();
              }
            }
          }
        }
      };

      const muteNode = eimAudioContext.createGain();
      muteNode.gain.value = 0;
      eimMediaStreamSource.connect(eimScriptProcessor);
      eimScriptProcessor.connect(muteNode);
      muteNode.connect(eimAudioContext.destination);
    })
    .catch((err) => {
      console.debug('[Emotion Audio Capture] Microphone note:', err);
    });
  }
}

function stopEmotionAudioCapture(shouldTranscribe = true) {
  emotionInterviewState.isRecording = false;

  const micBtn = document.getElementById('eimMicRecordBtn');
  const micLabel = document.getElementById('eimMicRecordLabel');
  const finishBtn = document.getElementById('eimFinishSpeakingBtn');

  if (micBtn) micBtn.classList.remove('recording');
  if (micLabel) micLabel.textContent = 'Speak Voice';
  if (finishBtn) finishBtn.style.display = 'none';

  if (shouldTranscribe && eimAudioBuffers && eimAudioBuffers.length >= 2 && !eimTranscribing) {
    triggerEmotionAudioTranscribe();
  }

  if (eimScriptProcessor) {
    try { eimScriptProcessor.disconnect(); } catch(e) {}
    eimScriptProcessor = null;
  }
  if (eimMediaStreamSource) {
    try { eimMediaStreamSource.disconnect(); } catch(e) {}
    eimMediaStreamSource = null;
  }
  if (eimMediaStream) {
    try { eimMediaStream.getTracks().forEach(t => t.stop()); } catch(e) {}
    eimMediaStream = null;
  }
  if (eimAudioContext && eimAudioContext.state !== 'closed') {
    try { eimAudioContext.close(); } catch(e) {}
    eimAudioContext = null;
  }
}

async function triggerEmotionAudioTranscribe() {
  if (eimTranscribing || !eimAudioBuffers || eimAudioBuffers.length < 2) return;

  eimTranscribing = true;
  const micDot = document.getElementById('eimMicStateDot');
  const micText = document.getElementById('eimMicStateText');
  if (micDot) micDot.className = 'eim-mic-state-dot active';
  if (micText) micText.textContent = '⚡ Converting voice to text (Voicebox MLX-Audio)...';

  try {
    const sampleRate = eimAudioContext ? eimAudioContext.sampleRate : 44100;
    const buffersToEncode = eimAudioBuffers.slice();
    eimAudioBuffers = [];

    const wavBlob = encodeWAVFromBuffers(buffersToEncode, sampleRate);
    if (!wavBlob || wavBlob.size < 100) {
      if (micText) micText.textContent = 'Listening for your answer... Speak or type below';
      return;
    }

    const currentLang = emotionInterviewState.language || 'en';
    const sid = emotionInterviewState.sessionId || '';
    let transcribed = '';

    // Primary: VoiceboxTranscriber
    if (window.VoiceboxTranscriber) {
      try {
        const vbRes = await window.VoiceboxTranscriber.transcribeBlob(wavBlob, currentLang, {
          analyzeTone: true,
          sessionId: sid
        });
        if (vbRes && vbRes.text && vbRes.text.trim()) {
          transcribed = vbRes.text.trim();
        }
      } catch(e) {
        console.debug('[Emotion Transcribe note]:', e);
      }
    }

    // Direct /api/voicebox/transcribe fallback
    if (!transcribed) {
      try {
        const formData = new FormData();
        formData.append('audio', wavBlob, 'emotion_answer.wav');
        const url = `/api/voicebox/transcribe?language=${encodeURIComponent(currentLang)}&analyze_tone=true&session_id=${encodeURIComponent(sid)}`;
        const res = await fetch(url, { method: 'POST', body: formData });
        if (res.ok) {
          const data = await res.json();
          if (data.status === 'success' && (data.transcription || data.text)) {
            transcribed = (data.transcription || data.text).trim();
          }
        }
      } catch(e) {}
    }

    if (transcribed && transcribed.length > 0) {
      const answerInput = document.getElementById('eimAnswerInput');
      if (answerInput) {
        const existing = answerInput.value.trim();
        answerInput.value = existing ? `${existing}. ${transcribed}` : transcribed;
        enterEmotionReviewState(answerInput.value);
      }
    } else {
      if (micText) micText.textContent = 'Listening for your answer... Speak or type below';
    }
  } catch (err) {
    console.warn('[Emotion] Transcribe error:', err);
    if (micText) micText.textContent = 'Listening for your answer... Speak or type below';
  } finally {
    eimTranscribing = false;
  }
}

function enterEmotionReviewState(text) {
  emotionInterviewState.isReviewing = true;
  const micDot = document.getElementById('eimMicStateDot');
  const micText = document.getElementById('eimMicStateText');
  const reviewNotice = document.getElementById('eimReviewNotice');
  const rerecordBtn = document.getElementById('eimRerecordBtn');
  const finishBtn = document.getElementById('eimFinishSpeakingBtn');
  const answerInput = document.getElementById('eimAnswerInput');

  if (micDot) micDot.className = 'eim-mic-state-dot review';
  if (micText) micText.textContent = '✓ Voice captured. Review, edit, or confirm below.';
  if (reviewNotice) reviewNotice.style.display = 'flex';
  if (rerecordBtn) rerecordBtn.style.display = 'inline-flex';
  if (finishBtn) finishBtn.style.display = 'none';

  if (answerInput) {
    answerInput.style.borderColor = '#fb7185';
    answerInput.style.boxShadow = '0 0 0 2px rgba(244, 63, 94, 0.25)';
    setTimeout(() => {
      if (answerInput) {
        answerInput.style.borderColor = '';
        answerInput.style.boxShadow = '';
      }
    }, 2500);
  }

  if (window.lucide) window.lucide.createIcons();
}

async function submitCurrentEmotionAnswer(isSkip = false) {
  const answerInput = document.getElementById('eimAnswerInput');

  // If user spoke and buffer is pending, transcribe first
  if (!isSkip && (!answerInput || answerInput.value.trim().length === 0) && eimAudioBuffers.length >= 2) {
    const micText = document.getElementById('eimMicStateText');
    if (micText) micText.textContent = 'Transcribing voice answer before confirming...';
    await triggerEmotionAudioTranscribe();
  }

  let answerText = answerInput ? answerInput.value.trim() : '';
  if (isSkip || answerText.length === 0) {
    answerText = (emotionInterviewState.language === 'bn') ? 'বাদ দেওয়া হয়েছে' : (emotionInterviewState.language === 'hi') ? 'छोड़ दिया' : 'Skipped';
  }

  stopEmotionDoctorReading();
  stopEmotionAudioCapture(false);

  const submitBtn = document.getElementById('eimSubmitNextBtn');
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<span>Saving...</span> <i data-lucide="loader-2" class="spin"></i>`;
    if (window.lucide) window.lucide.createIcons();
  }

  try {
    if (emotionInterviewState.mode === 'fallback') {
      // Single answer risk check
      await fetch('/api/submit-fallback-answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answer: answerText })
      }).then(r => r.json()).then(d => {
        if (d.requires_crisis_flow) {
          closeEmotionInterviewModal();
          openEmergencyModal();
          throw new Error('CRISIS');
        }
      });
      
      // Save answer locally
      emotionInterviewState.fallbackAnswers.push({
        question_id: emotionInterviewState.fallbackData.questions[emotionInterviewState.currentIndex].id,
        text: answerText
      });
      
      if (emotionInterviewState.currentIndex < emotionInterviewState.totalQuestions - 1) {
        emotionInterviewState.currentIndex++;
        const nextQ = emotionInterviewState.fallbackData.questions[emotionInterviewState.currentIndex];
        emotionInterviewState.currentQuestion = {
          id: nextQ.id,
          text: nextQ.question_text[emotionInterviewState.language] || nextQ.question_text['en']
        };
        emotionInterviewState.isReviewing = false;
        if (submitBtn) submitBtn.disabled = false;
        renderCurrentEmotionQuestion();
      } else {
        // Aggregate analysis
        const aggRes = await fetch('/api/analyze-fallback-interview', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            answers: emotionInterviewState.fallbackAnswers,
            language: emotionInterviewState.language
          })
        });
        const aggData = await aggRes.json();
        if (submitBtn) submitBtn.disabled = false;
        renderEmotionResults(aggData);
      }
    } else {
      const res = await fetch('/api/emotion-interview/answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: emotionInterviewState.sessionId,
          user_id: state.userId,
          answer: answerText,
          input_mode: emotionInterviewState.isReviewing ? 'voice' : 'text'
        })
      });

      const data = await res.json();
      if (submitBtn) submitBtn.disabled = false;

      if (data.status === 'success' && data.result) {
        const result = data.result;
        if (result.is_complete && result.analysis) {
          renderEmotionResults(result.analysis);
        } else {
          emotionInterviewState.currentIndex = result.current_index;
          emotionInterviewState.totalQuestions = result.total_questions;
          emotionInterviewState.currentQuestion = result.next_question;
          emotionInterviewState.isReviewing = false;
          renderCurrentEmotionQuestion();
        }
      }
    }
  } catch (err) {
    console.error('Error submitting emotion answer:', err);
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.innerHTML = `<span>Confirm Answer & Next</span> <i data-lucide="arrow-right"></i>`;
    }
  }
}

function renderEmotionResults(analysis) {
  if (!analysis) return;

  stopEmotionDoctorReading();
  stopEmotionAudioCapture(false);

  const qStage = document.getElementById('eimQuestionStage');
  const rStage = document.getElementById('eimResultsStage');
  const rContent = document.getElementById('eimResultsContent');

  if (qStage) qStage.style.display = 'none';
  if (rStage) rStage.style.display = 'flex';

  const domEmotions = (analysis.dominant_emotions || ['reflective', 'calm']).join(', ');
  const intensity = (analysis.overall_intensity || 'moderate').toUpperCase();
  const copingLabel = analysis.coping_label || 'Adaptive Coping';
  const narrative = analysis.emotional_state_summary || '';
  const metrics = analysis.metrics || { emotional_openness: 75, resilience_score: 70, emotional_load: 45 };

  if (rContent) {
    rContent.innerHTML = `
      <div class="eim-profile-grid">
        <div class="eim-profile-card">
          <span class="eim-card-title">Dominant Emotions</span>
          <span class="eim-card-val" style="color: #fb7185;">${domEmotions}</span>
        </div>
        <div class="eim-profile-card">
          <span class="eim-card-title">Emotional Intensity</span>
          <span class="eim-card-val" style="color: ${intensity === 'HIGH' ? '#f43f5e' : intensity === 'MODERATE' ? '#fbbf24' : '#10b981'};">${intensity}</span>
        </div>
        <div class="eim-profile-card">
          <span class="eim-card-title">Coping Style</span>
          <span class="eim-card-val" style="color: #38bdf8;">${copingLabel}</span>
        </div>
        <div class="eim-profile-card">
          <span class="eim-card-title">Emotional Openness</span>
          <span class="eim-card-val" style="color: #a855f7;">${metrics.emotional_openness}/100</span>
        </div>
      </div>

      <div class="eim-narrative-box">
        ${narrative}
      </div>
    `;
  }

  // Also post an emotional profile summary card into the main chat window
  renderEmotionProfileCardInChat(analysis);

  if (window.lucide) window.lucide.createIcons();
}

function renderEmotionProfileCardInChat(analysis) {
  if (!analysis || !elements.chatMessages) return;

  const card = document.createElement('div');
  card.className = 'past-life-analysis-card animate-fade-in';
  card.style.borderColor = 'rgba(244, 63, 94, 0.35)';

  const domEmotions = (analysis.dominant_emotions || ['reflective', 'calm']).join(', ');
  const copingLabel = analysis.coping_label || 'Adaptive Coping';
  const narrative = analysis.emotional_state_summary || '';

  card.innerHTML = `
    <div class="pla-header">
      <div class="pla-title">
        <i data-lucide="heart" style="color: #fb7185;"></i>
        <span>Emotional State Profile & Synthesis</span>
      </div>
      <div class="pla-archetype-tag" style="background: rgba(244, 63, 94, 0.15); color: #fb7185; border-color: rgba(244, 63, 94, 0.35);">${copingLabel}</div>
    </div>

    <div style="font-size: 0.92rem; line-height: 1.55; color: #cbd5e1; margin-bottom: 1rem;">
      ${narrative}
    </div>

    <div class="pla-actions-row">
      <button type="button" class="pla-action-btn" onclick="openBreathingModal()">
        <i data-lucide="wind"></i>
        <span>4-7-8 Calm Breath</span>
      </button>
      <button type="button" class="pla-action-btn" onclick="switchTab('providers')">
        <i data-lucide="user-check"></i>
        <span>Consult a Therapist</span>
      </button>
    </div>
  `;

  elements.chatMessages.appendChild(card);
  elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
  if (window.lucide) window.lucide.createIcons();
}

function initEmotionInterviewTools() {
  const closeInviteBtn = document.getElementById('closeEmotionInviteModalBtn');
  const declineBtn = document.getElementById('declineEmotionInterviewBtn');
  const acceptBtn = document.getElementById('acceptEmotionInterviewBtn');
  const closeStudioBtn = document.getElementById('closeEmotionInterviewModalBtn');
  const ttsReplayBtn = document.getElementById('eimTtsReplayBtn');
  const micRecordBtn = document.getElementById('eimMicRecordBtn');
  const finishBtn = document.getElementById('eimFinishSpeakingBtn');
  const skipBtn = document.getElementById('eimSkipBtn');
  const rerecordBtn = document.getElementById('eimRerecordBtn');
  const submitNextBtn = document.getElementById('eimSubmitNextBtn');
  const doneReturnBtn = document.getElementById('eimDoneReturnBtn');
  const answerInput = document.getElementById('eimAnswerInput');

  if (closeInviteBtn) closeInviteBtn.addEventListener('click', closeEmotionInviteModal);
  if (declineBtn) declineBtn.addEventListener('click', closeEmotionInviteModal);
  if (acceptBtn) acceptBtn.addEventListener('click', startEmotionInterviewFromInvite);
  if (closeStudioBtn) closeStudioBtn.addEventListener('click', closeEmotionInterviewModal);

  if (ttsReplayBtn) {
    ttsReplayBtn.addEventListener('click', () => {
      if (emotionInterviewState.currentQuestion) {
        speakEmotionQuestion(emotionInterviewState.currentQuestion.question_text, emotionInterviewState.language);
      }
    });
  }

  if (micRecordBtn) {
    micRecordBtn.addEventListener('click', () => {
      stopEmotionDoctorReading();
      if (emotionInterviewState.isRecording) {
        stopEmotionAudioCapture(true);
      } else {
        startEmotionAudioCapture();
      }
    });
  }

  if (finishBtn) {
    finishBtn.addEventListener('click', () => {
      stopEmotionAudioCapture(true);
    });
  }

  if (rerecordBtn) {
    rerecordBtn.addEventListener('click', () => {
      if (answerInput) answerInput.value = '';
      emotionInterviewState.isReviewing = false;
      const reviewNotice = document.getElementById('eimReviewNotice');
      if (reviewNotice) reviewNotice.style.display = 'none';
      rerecordBtn.style.display = 'none';
      startEmotionAudioCapture();
    });
  }

  if (skipBtn) {
    skipBtn.addEventListener('click', () => submitCurrentEmotionAnswer(true));
  }

  if (submitNextBtn) {
    submitNextBtn.addEventListener('click', () => submitCurrentEmotionAnswer(false));
  }

  if (doneReturnBtn) {
    doneReturnBtn.addEventListener('click', closeEmotionInterviewModal);
  }

  if (answerInput) {
    // If user starts typing or edits, immediately halt AI speech and enter review mode
    answerInput.addEventListener('input', () => {
      if (emotionInterviewState.isDoctorSpeaking) {
        stopEmotionDoctorReading();
      }
      if (answerInput.value.trim().length > 0) {
        enterEmotionReviewState(answerInput.value);
      }
    });
  }

  // Modal language buttons
  document.querySelectorAll('.eim-lang-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const lang = btn.getAttribute('data-lang') || 'en';
      openEmotionInterviewModal(lang);
    });
  });
}

// Wire screener action buttons

document.addEventListener('DOMContentLoaded', () => {
  const resetBtn = document.getElementById('screenerResetBtn');
  if (resetBtn) resetBtn.addEventListener('click', () => startFreshScreenerSession());

  const researchBtn = document.getElementById('screenerResearchModalBtn');
  if (researchBtn) researchBtn.addEventListener('click', async () => {
    try {
      const res = await fetch('/api/screener/research-papers');
      const data = await res.json();
      alert(`Research Grounding Evidence:\n\nInstruments: PHQ-9 (Depression), GAD-7 (Anxiety), DASS-21 (Stress), WHO-5 (Well-Being), C-SSRS (Suicide Severity), Saini et al. (Primary Care Risk Review).\n\nTotal Research Papers: ${data.data?.scanned_files?.length || 6}\n\nDisclaimer: ${data.disclaimer}`);
    } catch (e) {
      alert('Grounded in: Anxiety.pdf (GAD-7), BASELINE SCREENING.pdf (C-SSRS), Q FOR DEPRESSION,ANXIETY.pdf (DASS-21), WHO WELLBEING.pdf (WHO-5), SUICIDE IDENTATION.pdf (Saini et al., 2024).');
    }
  });
});

// ==========================================================================
// GLOBAL STARTUP LIFECYCLE
// ==========================================================================

function bootMindBridge() {
  initAmbientCanvas();
  initLanguageSystem();
  initThemeSystem();
  initTabs();
  initSoundscapes();
  initEmotionalWeather();
  initSomaticCheckin();
  initVoicePerspectives();
  initChatInput();
  initSpeechRecognition();
  initTTS();
  initModals();
  initBreathingPacer();
  initSiriOrbPhysics();
  initPastLifeTools();
  initEmotionInterviewTools();
  fetchProviders();
  fetchEmergencyResources();
  initEmergencyModeInteractive();

  // Set default booking date to tomorrow
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  if (elements.bookDate) {
    elements.bookDate.value = tomorrow.toISOString().split('T')[0];
    elements.bookDate.min = new Date().toISOString().split('T')[0];
  }

  if (window.lucide) window.lucide.createIcons();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', bootMindBridge);
} else {
  bootMindBridge();
}





// ==========================================================================
// REGISTRATION MENTAL-STATE UNDERSTANDING MODULE
// ==========================================================================

let regSessionId = null;
let regTotalQuestions = 20;
let regCurrentLanguage = 'en';

// Audio tracking for Voice Confirmation requirement
let regAudioContext = null;
let regMediaStreamSource = null;
let regScriptProcessor = null;
let regAudioBuffers = [];
let regIsRecording = false;
let regTranscribing = false;
let regSilenceStartTime = 0;
let regNoiseFloor = 0;
let regCalibrationFrames = 0;
let regPreRollBuffers = [];

function openRegistrationModal(lang = 'en') {
  regCurrentLanguage = lang;
  const modal = document.getElementById('registrationModal');
  if (modal) modal.style.display = 'flex';
  
  document.getElementById('regConsentStage').style.display = 'flex';
  document.getElementById('regQuestionStage').style.display = 'none';
  document.getElementById('regResultsStage').style.display = 'none';
}

function closeRegistrationModal() {
  const modal = document.getElementById('registrationModal');
  if (modal) modal.style.display = 'none';
  stopRegAudioCapture(false);
}

document.getElementById('closeRegistrationModalBtn')?.addEventListener('click', closeRegistrationModal);
document.getElementById('regFinishBtn')?.addEventListener('click', closeRegistrationModal);
document.getElementById('regSkipInitialBtn')?.addEventListener('click', closeRegistrationModal);

document.getElementById('regUrgentHelpBtn')?.addEventListener('click', () => {
  closeRegistrationModal();
  openEmergencyModal();
});
document.getElementById('regUrgentHelpInnerBtn')?.addEventListener('click', () => {
  closeRegistrationModal();
  openEmergencyModal();
});

document.getElementById('regStartBtn')?.addEventListener('click', async () => {
  document.getElementById('regConsentStage').style.display = 'none';
  document.getElementById('regQuestionStage').style.display = 'flex';
  document.getElementById('regQuestionText').textContent = 'Starting registration...';
  
  try {
    const res = await fetch('/api/registration/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ language: regCurrentLanguage, user_id: 'anonymous' })
    });
    const data = await res.json();
    if (data.status === 'success') {
      regSessionId = data.session.session_id;
      regTotalQuestions = data.session.total_questions;
      renderRegQuestion(data.session.question);
    }
  } catch (err) {
    console.error('Error starting registration:', err);
  }
});

function renderRegQuestion(q) {
  if (!q) return;
  const pBar = document.getElementById('regProgressBar');
  if (pBar) {
    const percent = Math.max(5, (1 / regTotalQuestions) * 100);
    pBar.style.width = percent + '%';
  }
  
  const textElem = document.getElementById('regQuestionText');
  const tagElem = document.getElementById('regDomainTag');
  if (textElem) textElem.textContent = q.text;
  if (tagElem) tagElem.textContent = q.domain.replace(/_/g, ' ');
  
  const input = document.getElementById('regAnswerInput');
  if (input) {
    input.value = '';
    input.disabled = false;
  }
  
  document.getElementById('regVoiceConfirmArea').style.display = 'none';
  document.getElementById('regStandardActions').style.display = 'flex';
  
  if (window.speechSynthesis) {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(q.text);
    utterance.lang = regCurrentLanguage === 'en' ? 'en-US' : (regCurrentLanguage === 'hi' ? 'hi-IN' : 'bn-IN');
    utterance.rate = 0.95;
    window.speechSynthesis.speak(utterance);
  }
}

async function fetchNextRegQuestion() {
  if (!regSessionId) return;
  try {
    const res = await fetch(`/api/registration/question?session_id=${regSessionId}`);
    const data = await res.json();
    if (data.status === 'success') {
      renderRegQuestion(data.question);
    }
  } catch(e) {}
}

async function submitRegAnswer(answerText = '', inputMode = 'text', skipped = false) {
  if (!regSessionId) return;
  
  const input = document.getElementById('regAnswerInput');
  if (input) input.disabled = true;
  
  try {
    const res = await fetch('/api/registration/answer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: regSessionId,
        answer_text: answerText,
        input_mode: inputMode,
        skipped: skipped
      })
    });
    
    const data = await res.json();
    
    if (data.status === 'crisis_halted') {
      closeRegistrationModal();
      openEmergencyModal();
      return;
    }
    
    if (data.status === 'completed') {
      showRegResultsStage();
    } else if (data.status === 'in_progress') {
      const pBar = document.getElementById('regProgressBar');
      if (pBar) {
        const percent = Math.max(5, (data.current_index / data.total_questions) * 100);
        pBar.style.width = percent + '%';
      }
      renderRegQuestion(data.next_question);
    }
  } catch(e) {
    console.error("Submit error", e);
    alert("Network error: Could not submit answer. Please ensure your backend is running.");
  }
}

async function showRegResultsStage() {
  document.getElementById('regQuestionStage').style.display = 'none';
  document.getElementById('regResultsStage').style.display = 'flex';
  
  const sumText = document.getElementById('regSummaryText');
  if (sumText) sumText.textContent = 'MindBridge is analyzing your responses...';
  
  try {
    const res = await fetch('/api/registration/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: regSessionId })
    });
    const data = await res.json();
    if (data.status === 'success' && data.analysis) {
      if (data.analysis.risk_flag === 'high' || data.analysis.risk_flag === 'immediate') {
         closeRegistrationModal();
         openEmergencyModal();
      } else {
         if (sumText) sumText.textContent = data.analysis.summary_text || 'Registration complete.';
      }
    }
  } catch(e) {
    if (sumText) sumText.textContent = 'Registration completed successfully.';
  }
  localStorage.setItem('mindbridge_registration_done', 'true');
}

// Text submissions
document.getElementById('regSubmitTextBtn')?.addEventListener('click', () => {
  const text = document.getElementById('regAnswerInput')?.value.trim() || '';
  submitRegAnswer(text, 'text', false);
});
document.getElementById('regSkipBtn')?.addEventListener('click', () => {
  submitRegAnswer('', 'text', true);
});
document.getElementById('regPreferNotBtn')?.addEventListener('click', () => {
  submitRegAnswer('Prefer not to answer', 'text', true);
});

// Voice Integration
document.getElementById('regMicBtn')?.addEventListener('click', () => {
  if (regIsRecording) {
    stopRegAudioCapture(true);
  } else {
    startRegAudioCapture();
  }
});

document.getElementById('regConfirmVoiceBtn')?.addEventListener('click', () => {
  const text = document.getElementById('regAnswerInput')?.value.trim() || '';
  submitRegAnswer(text, 'voice', false);
});

document.getElementById('regDirectConfirmVoiceBtn')?.addEventListener('click', () => {
  const text = document.getElementById('regAnswerInput')?.value.trim() || '';
  // Force stop the microphone, but DO NOT show the secondary confirm area
  stopRegAudioCapture(false);
  // Instantly submit the answer as voice
  submitRegAnswer(text, 'voice', false);
});

document.getElementById('regEditVoiceBtn')?.addEventListener('click', () => {
  document.getElementById('regVoiceConfirmArea').style.display = 'none';
  document.getElementById('regStandardActions').style.display = 'flex';
  const input = document.getElementById('regAnswerInput');
  if (input) {
    input.disabled = false;
    input.focus();
  }
});

document.getElementById('regRecordAgainBtn')?.addEventListener('click', () => {
  document.getElementById('regVoiceConfirmArea').style.display = 'none';
  document.getElementById('regStandardActions').style.display = 'flex';
  const input = document.getElementById('regAnswerInput');
  if (input) input.value = '';
  startRegAudioCapture();
});

document.getElementById('regSkipVoiceBtn')?.addEventListener('click', () => {
  submitRegAnswer('', 'voice', true);
});

let regRecognition = null;

async function startRegAudioCapture() {
  regIsRecording = true;
  const micBtn = document.getElementById('regMicBtn');
  const micLabel = document.getElementById('regMicLabel');
  if (micBtn) micBtn.classList.add('active');
  if (micLabel) micLabel.textContent = 'Listening... (Speak naturally)';
  const directConfirm = document.getElementById('regDirectConfirmVoiceBtn');
  if (directConfirm) directConfirm.style.display = 'inline-block';
  
  const input = document.getElementById('regAnswerInput');
  if (input) {
    input.disabled = false;
    input.value = '';
    input.placeholder = 'Listening to your voice...';
  }

  const SpeechRecognitionClass = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognitionClass) {
    alert("Speech recognition is not supported in this browser.");
    stopRegAudioCapture();
    return;
  }

  try {
    if (regRecognition) {
      try { regRecognition.stop(); } catch(e){}
    }
    
    regRecognition = new SpeechRecognitionClass();
    regRecognition.continuous = true;
    regRecognition.interimResults = true;
    
    if (regCurrentLanguage === 'bn') regRecognition.lang = 'bn-IN';
    else if (regCurrentLanguage === 'hi') regRecognition.lang = 'hi-IN';
    else regRecognition.lang = 'en-US';

    let finalTranscript = '';

    regRecognition.onresult = (event) => {
      let interimTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        } else {
          interimTranscript += event.results[i][0].transcript;
        }
      }
      if (input) {
        input.value = finalTranscript + interimTranscript;
      }
    };

    regRecognition.onerror = (event) => {
      console.log('Registration speech recognition error', event.error);
    };

    regRecognition.onend = () => {
      if (regIsRecording) {
        try { regRecognition.start(); } catch(e){}
      }
    };

    regRecognition.start();
  } catch (err) {
    console.error('Registration speech init error:', err);
  }
}

function stopRegAudioCapture(shouldTranscribe = true) {
  regIsRecording = false;
  const micBtn = document.getElementById('regMicBtn');
  const micLabel = document.getElementById('regMicLabel');
  if (micBtn) micBtn.classList.remove('active');
  if (micLabel) micLabel.textContent = 'Use voice';
  const directConfirm = document.getElementById('regDirectConfirmVoiceBtn');
  if (directConfirm) directConfirm.style.display = 'none';
  
  const input = document.getElementById('regAnswerInput');
  if (input) {
    input.placeholder = 'Type your answer here...';
  }
  
  if (regRecognition) {
    try {
      regRecognition.onend = null;
      regRecognition.stop();
    } catch(e) {}
    regRecognition = null;
  }
  
  if (shouldTranscribe) {
    const text = input ? input.value.trim() : '';
    if (text) {
      input.disabled = true;
      document.getElementById('regStandardActions').style.display = 'none';
      document.getElementById('regVoiceConfirmArea').style.display = 'block';
      document.getElementById('regVoiceTranscript').textContent = `"${text}"`;
    }
  }
}

// Ensure init trigger exists globally
window.openRegistrationModal = openRegistrationModal;


// ==========================================================================
// AUTHENTICATION SYSTEM
// ==========================================================================

function checkAuthStatus() {
  const user = localStorage.getItem('mindbridge_user');
  const overlay = document.getElementById('authOverlay');
  if (!overlay) return;
  
  if (!user) {
    overlay.style.display = 'flex';
  } else {
    overlay.style.display = 'none';
  }
}

document.getElementById('tabLoginBtn')?.addEventListener('click', (e) => {
  e.target.classList.add('active');
  document.getElementById('tabRegisterBtn').classList.remove('active');
  document.getElementById('loginForm').style.display = 'flex';
  document.getElementById('registerForm').style.display = 'none';
  document.getElementById('loginError').textContent = '';
});

document.getElementById('tabRegisterBtn')?.addEventListener('click', (e) => {
  e.target.classList.add('active');
  document.getElementById('tabLoginBtn').classList.remove('active');
  document.getElementById('registerForm').style.display = 'flex';
  document.getElementById('loginForm').style.display = 'none';
  document.getElementById('registerError').textContent = '';
});

document.getElementById('loginForm')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const email = document.getElementById('loginEmail').value;
  const password = document.getElementById('loginPassword').value;
  const errorElem = document.getElementById('loginError');
  const btn = e.target.querySelector('button');
  
  btn.textContent = 'Verifying...';
  errorElem.textContent = '';
  
  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    
    if (data.status === 'success') {
      localStorage.setItem('mindbridge_user', JSON.stringify(data.user));
      document.getElementById('authOverlay').style.display = 'none';
      
      // Trigger registration questions if not done yet
      if (localStorage.getItem('mindbridge_registration_done') !== 'true') {
        if (typeof window.openRegistrationModal === 'function') {
           setTimeout(() => { window.openRegistrationModal(); }, 500);
        }
      }
    } else {
      errorElem.textContent = data.message || 'Login failed.';
    }
  } catch(err) {
    errorElem.textContent = 'Network error. Please try again.';
  } finally {
    btn.textContent = 'Enter Sanctuary';
  }
});

document.getElementById('registerForm')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const name = document.getElementById('registerName').value;
  const email = document.getElementById('registerEmail').value;
  const password = document.getElementById('registerPassword').value;
  const errorElem = document.getElementById('registerError');
  const btn = e.target.querySelector('button');
  
  btn.textContent = 'Creating...';
  errorElem.textContent = '';
  
  try {
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password })
    });
    const data = await res.json();
    
    if (data.status === 'success') {
      localStorage.setItem('mindbridge_user', JSON.stringify({
        id: data.user_id,
        name: data.name,
        email: data.email
      }));
      document.getElementById('authOverlay').style.display = 'none';
      
      // CRITICAL: Trigger the 20-question mental-state interview for newly registered users!
      if (typeof window.openRegistrationModal === 'function') {
         // Add slight delay for smooth transition
         setTimeout(() => {
           window.openRegistrationModal();
         }, 500);
      }
    } else {
      errorElem.textContent = data.message || 'Registration failed.';
    }
  } catch(err) {
    errorElem.textContent = 'Network error. Please try again.';
  } finally {
    btn.textContent = 'Begin Journey';
  }
});

// Run auth check on load
document.addEventListener('DOMContentLoaded', () => {
  checkAuthStatus();
});

