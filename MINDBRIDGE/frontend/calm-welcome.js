/**
 * MindBridge Calm Welcome Experience
 * Ethical, accessible, neuro-aesthetic opening animation and audio controller.
 */

(function () {
  'use strict';

  // -------------------------------------------------------------
  // MULTILINGUAL STRINGS
  // -------------------------------------------------------------
  const TRANSLATIONS = {
    en: {
      title: "Welcome to MindBridge",
      subtitle: "A safe first step toward professional support.",
      supportive: "Share how you feel through voice or text. Take your time — you are in control.",
      startScreening: "Start Screening",
      emergencyHelp: "Emergency Help",
      skipAnimation: "Skip animation",
      reduceMotion: "Reduce motion",
      reducedMotionActive: "Reduced motion active",
      soundPrompt: "Would you like an optional calm background sound?",
      enableSound: "Enable calm sound",
      continueWithoutSound: "Continue without sound",
      pauseSound: "Pause sound",
      playSound: "Play calm sound",
      ethical1: "You can take a break anytime.",
      ethical2: "Answer by voice or text.",
      ethical3: "Your privacy matters."
    },
    bn: {
      title: "MindBridge-এ স্বাগতম",
      subtitle: "পেশাদার সহায়তার দিকে একটি নিরাপদ প্রথম পদক্ষেপ।",
      supportive: "তুমি ভয়েস বা টেক্সটের মাধ্যমে নিজের অনুভূতি জানাতে পারো। সময় নাও — নিয়ন্ত্রণ তোমার হাতে।",
      startScreening: "স্ক্রিনিং শুরু করুন",
      emergencyHelp: "জরুরি সহায়তা",
      skipAnimation: "অ্যানিমেশন এড়িয়ে যান",
      reduceMotion: "অ্যানিমেশন কমান",
      reducedMotionActive: "কম অ্যানিমেশন সক্রিয়",
      soundPrompt: "আপনি কি একটি শান্ত ব্যাকগ্রাউন্ড সাউন্ড চান?",
      enableSound: "শান্ত শব্দ চালু করুন",
      continueWithoutSound: "শব্দ ছাড়া চলুন",
      pauseSound: "শব্দ থামান",
      playSound: "শান্ত শব্দ বাজান",
      ethical1: "যেকোনো সময় বিরতি নিতে পারেন।",
      ethical2: "ভয়েস বা টেক্সটে উত্তর দিন।",
      ethical3: "আপনার গোপনীয়তা সুরক্ষিত।"
    },
    hi: {
      title: "MindBridge में आपका स्वागत है",
      subtitle: "पेशेवर सहायता की ओर एक सुरक्षित पहला कदम।",
      supportive: "आप आवाज़ या टेक्स्ट के माध्यम से अपनी भावनाएँ साझा कर सकते हैं। अपना समय लें — नियंत्रण आपके हाथ में है।",
      startScreening: "स्क्रीनिंग शुरू करें",
      emergencyHelp: "आपातकालीन सहायता",
      skipAnimation: "एनिमेशन छोड़ें",
      reduceMotion: "गति कम करें",
      reducedMotionActive: "कम गति सक्रिय",
      soundPrompt: "क्या आप एक शांत पृष्ठभूमि ध्वनि चाहते हैं?",
      enableSound: "शांत ध्वनि चालू करें",
      continueWithoutSound: "ध्वनि के बिना आगे बढ़ें",
      pauseSound: "ध्वनि रोकें",
      playSound: "शांत ध्वनि चलाएं",
      ethical1: "आप कभी भी ब्रेक ले सकते हैं।",
      ethical2: "आवाज़ या टेक्स्ट से उत्तर दें।",
      ethical3: "आपकी गोपनीयता सुरक्षित है।"
    }
  };

  let currentLang = 'en';
  let isReducedMotion = false;
  let audioCtx = null;
  let masterGain = null;
  let isAudioPlaying = false;
  let pianoLoopTimer = null;
  const DEFAULT_VOL = 0.08; // 8% initial
  const MAX_VOL = 0.20;     // 20% safe cap

  // -------------------------------------------------------------
  // AUDIO SYNTHESIS ENGINE (Web Audio API - 68 BPM Soft Piano)
  // -------------------------------------------------------------
  function initAudioEngine() {
    if (!audioCtx) {
      const AudioCtxClass = window.AudioContext || window.webkitAudioContext;
      audioCtx = new AudioCtxClass();
      masterGain = audioCtx.createGain();
      masterGain.gain.setValueAtTime(0, audioCtx.currentTime);
      masterGain.connect(audioCtx.destination);
    }
    if (audioCtx.state === 'suspended') {
      audioCtx.resume();
    }
  }

  function startSoftPiano() {
    initAudioEngine();
    if (!audioCtx || !masterGain) return;

    isAudioPlaying = true;
    updateAudioWidgetState();

    // Fade-in over 3.5 seconds
    const now = audioCtx.currentTime;
    masterGain.gain.cancelScheduledValues(now);
    masterGain.gain.setValueAtTime(0.0001, now);
    masterGain.gain.linearRampToValueAtTime(DEFAULT_VOL, now + 3.5);

    // Warm chords in Fmaj7 / Cmaj9 (68 BPM cadence = ~3.5s per chord)
    const chords = [
      [174.61, 220.00, 261.63, 329.63], // Fmaj7
      [130.81, 164.81, 196.00, 246.94], // Cmaj7
      [146.83, 174.61, 220.00, 261.63], // Dm7
      [116.54, 146.83, 174.61, 220.00]  // Bbmaj7
    ];
    let idx = 0;

    function playChord() {
      if (!isAudioPlaying || !audioCtx) return;
      const notes = chords[idx % chords.length];
      idx++;

      const filter = audioCtx.createBiquadFilter();
      filter.type = 'lowpass';
      filter.frequency.setValueAtTime(750, audioCtx.currentTime);
      filter.connect(masterGain);

      notes.forEach((freq, i) => {
        const noteTime = audioCtx.currentTime + (i * 0.12);
        const osc = audioCtx.createOscillator();
        const g = audioCtx.createGain();

        osc.type = 'sine';
        osc.frequency.setValueAtTime(freq, noteTime);

        g.gain.setValueAtTime(0.0001, noteTime);
        g.gain.linearRampToValueAtTime(0.045, noteTime + 0.15);
        g.gain.exponentialRampToValueAtTime(0.0001, noteTime + 3.8);

        osc.connect(g);
        g.connect(filter);

        osc.start(noteTime);
        osc.stop(noteTime + 4.0);
      });
    }

    playChord();
    if (pianoLoopTimer) clearInterval(pianoLoopTimer);
    pianoLoopTimer = setInterval(playChord, (60 / 68) * 4 * 1000);
  }

  function pauseAudio() {
    if (!audioCtx || !masterGain || !isAudioPlaying) return;
    const now = audioCtx.currentTime;
    masterGain.gain.linearRampToValueAtTime(0.0001, now + 1.2);
    setTimeout(() => {
      isAudioPlaying = false;
      if (pianoLoopTimer) {
        clearInterval(pianoLoopTimer);
        pianoLoopTimer = null;
      }
      updateAudioWidgetState();
    }, 1200);
  }

  function stopAudioImmediate() {
    if (audioCtx && masterGain) {
      const now = audioCtx.currentTime;
      masterGain.gain.cancelScheduledValues(now);
      masterGain.gain.setValueAtTime(0, now);
    }
    if (pianoLoopTimer) {
      clearInterval(pianoLoopTimer);
      pianoLoopTimer = null;
    }
    isAudioPlaying = false;
    updateAudioWidgetState();
  }

  function setAudioVolume(pct) {
    if (!masterGain || !audioCtx) return;
    const gainVal = (pct / 100) * MAX_VOL;
    masterGain.gain.setTargetAtTime(gainVal, audioCtx.currentTime, 0.1);
  }

  // -------------------------------------------------------------
  // DOM CREATION & INJECTION
  // -------------------------------------------------------------
  function buildWelcomeOverlay() {
    if (document.getElementById('mindbridgeWelcomeOverlay')) return;

    // Check system prefers-reduced-motion
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      isReducedMotion = true;
      document.body.classList.add('reduce-motion');
    }

    const overlay = document.createElement('aside');
    overlay.id = 'mindbridgeWelcomeOverlay';
    overlay.className = 'calm-welcome-overlay';
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.setAttribute('aria-label', 'MindBridge Calm Welcome Experience');

    overlay.innerHTML = `
      <!-- Ambient light reflections -->
      <div class="calm-ambient-glow calm-glow-1" aria-hidden="true"></div>
      <div class="calm-ambient-glow calm-glow-2" aria-hidden="true"></div>

      <!-- Top Header Toolbar: Accessibility + Emergency SOS -->
      <header class="calm-header-bar">
        <div class="calm-access-group">
          <button type="button" id="calmSkipBtn" class="calm-pill-btn" title="Skip opening animation directly to options">
            <span>⏩</span>
            <span id="calmSkipText">Skip animation</span>
          </button>
          <button type="button" id="calmMotionBtn" class="calm-pill-btn" aria-pressed="false" title="Toggle reduced motion mode">
            <span>👁️</span>
            <span id="calmMotionText">Reduce motion</span>
          </button>
        </div>

        <div>
          <button type="button" id="calmEmergencyHeaderBtn" class="calm-emergency-btn" title="Immediate 24/7 Crisis Hotline & Assistance">
            <span class="pulse-dot"></span>
            <span id="calmEmergencyHeaderText">Emergency Help</span>
          </button>
        </div>
      </header>

      <!-- Centerpiece: Breathing Orb + Logo + Typography + Actions -->
      <div class="calm-center-stage">
        
        <!-- Breathing Orb Visual Anchor -->
        <div class="calm-orb-wrapper" aria-hidden="true">
          <div class="calm-orb-aura"></div>
          <div class="calm-orb-core"></div>
        </div>

        <div class="calm-content-layer">
          
          <!-- Logo with soft heart & bridge motif -->
          <div class="calm-logo-box" id="calmLogoBox">
            <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" style="width: 100%; height: 100%;">
              <defs>
                <linearGradient id="bridgeGradient" x1="15" y1="75" x2="85" y2="75" gradientUnits="userSpaceOnUse">
                  <stop offset="0%" stop-color="#0D9488" />
                  <stop offset="50%" stop-color="#4F46E5" />
                  <stop offset="100%" stop-color="#0284C7" />
                </linearGradient>
                <linearGradient id="heartGradient" x1="50" y1="25" x2="50" y2="55" gradientUnits="userSpaceOnUse">
                  <stop offset="0%" stop-color="#F472B6" />
                  <stop offset="100%" stop-color="#818CF8" />
                </linearGradient>
              </defs>
              <circle cx="50" cy="50" r="44" stroke="url(#bridgeGradient)" stroke-width="2.5" stroke-dasharray="4 2" opacity="0.4" />
              <path d="M 22 72 C 32 46, 68 46, 78 72" stroke="url(#bridgeGradient)" stroke-width="4.5" stroke-linecap="round" />
              <line x1="38" y1="56" x2="38" y2="70" stroke="url(#bridgeGradient)" stroke-width="2" stroke-linecap="round" opacity="0.6" />
              <line x1="50" y1="52" x2="50" y2="70" stroke="url(#bridgeGradient)" stroke-width="2" stroke-linecap="round" opacity="0.7" />
              <line x1="62" y1="56" x2="62" y2="70" stroke="url(#bridgeGradient)" stroke-width="2" stroke-linecap="round" opacity="0.6" />
              <path d="M 50 36 C 47 28, 35 28, 35 38 C 35 46, 47 52, 50 56 C 53 52, 65 46, 65 38 C 65 28, 53 28, 50 36 Z" fill="url(#heartGradient)" />
            </svg>
          </div>

          <!-- Welcome Typography -->
          <div class="calm-text-box" id="calmTextBox">
            <h1 class="calm-title" id="calmMainTitle">Welcome to MindBridge</h1>
            <p class="calm-subtitle" id="calmMainSubtitle">A safe first step toward professional support.</p>
            <p class="calm-supportive-msg" id="calmMainSupportive">Share how you feel through voice or text. Take your time — you are in control.</p>
          </div>

          <!-- Welcome Action Controls -->
          <div class="calm-actions-box" id="calmActionsBox">
            
            <!-- Language Selector -->
            <div class="calm-lang-row" role="radiogroup" aria-label="Language selection">
              <button type="button" class="calm-lang-btn active" data-lang="en">English</button>
              <button type="button" class="calm-lang-btn" data-lang="bn">বাংলা</button>
              <button type="button" class="calm-lang-btn" data-lang="hi">हिंदी</button>
            </div>

            <!-- Primary and Secondary Buttons -->
            <div class="calm-buttons-row">
              <button type="button" class="calm-btn-primary" id="calmStartScreeningBtn">
                <span id="calmStartScreeningText">Start Screening</span>
                <span>→</span>
              </button>
              <button type="button" class="calm-btn-secondary" id="calmEmergencyMainBtn">
                <span>🛡️</span>
                <span id="calmEmergencyMainText">Emergency Help</span>
              </button>
            </div>

            <!-- Optional Calm Audio Prompt -->
            <div class="calm-audio-banner" id="calmAudioBanner">
              <span id="calmAudioPromptText">Would you like an optional calm background sound?</span>
              <button type="button" class="calm-audio-optin" id="calmAudioOptInBtn">Enable sound</button>
              <button type="button" class="calm-audio-dismiss" id="calmAudioDismissBtn">No sound</button>
            </div>

            <!-- Ethical Reassurance Indicators -->
            <div class="calm-ethical-row">
              <span class="calm-ethical-tag">✓ <span id="calmEthical1">You can take a break anytime.</span></span>
              <span class="calm-ethical-tag">🎙️ <span id="calmEthical2">Answer by voice or text.</span></span>
              <span class="calm-ethical-tag">🔒 <span id="calmEthical3">Your privacy matters.</span></span>
            </div>

          </div>

        </div>

      </div>

      <!-- Footer Bar: Sanctuary Status & Audio Widget -->
      <footer class="calm-footer-bar">
        <div>
          <span>MindBridge Sanctuary</span> • <span>Ethical & Non-Diagnostic</span>
        </div>

        <div class="calm-sound-widget" id="calmSoundWidget" style="display: none;">
          <button type="button" id="calmAudioToggleBtn" style="border:none; background:transparent; cursor:pointer;" title="Toggle Play/Pause">
            <span id="calmAudioPlayIcon">▶</span>
          </button>
          <span style="font-size: 0.72rem; font-weight:600;">68 BPM Piano</span>
          <input type="range" id="calmVolumeSlider" min="0" max="100" value="40" title="Safe volume slider (capped at 20%)" aria-label="Audio volume">
        </div>
      </footer>
    `;

    document.body.prepend(overlay);
    setupEventListeners(overlay);

    // Run timed sequence or immediate for reduced motion
    runAnimationSequence();
  }

  function applyLanguage(lang) {
    currentLang = lang;
    const t = TRANSLATIONS[lang] || TRANSLATIONS.en;

    document.getElementById('calmMainTitle').textContent = t.title;
    document.getElementById('calmMainSubtitle').textContent = t.subtitle;
    document.getElementById('calmMainSupportive').textContent = t.supportive;
    document.getElementById('calmStartScreeningText').textContent = t.startScreening;
    document.getElementById('calmEmergencyMainText').textContent = t.emergencyHelp;
    document.getElementById('calmEmergencyHeaderText').textContent = t.emergencyHelp;
    document.getElementById('calmSkipText').textContent = t.skipAnimation;
    document.getElementById('calmMotionText').textContent = isReducedMotion ? t.reducedMotionActive : t.reduceMotion;
    document.getElementById('calmAudioPromptText').textContent = t.soundPrompt;
    document.getElementById('calmAudioOptInBtn').textContent = t.enableSound;
    document.getElementById('calmAudioDismissBtn').textContent = t.continueWithoutSound;
    document.getElementById('calmEthical1').textContent = t.ethical1;
    document.getElementById('calmEthical2').textContent = t.ethical2;
    document.getElementById('calmEthical3').textContent = t.ethical3;

    // Update active class on buttons
    document.querySelectorAll('.calm-lang-btn').forEach(btn => {
      btn.classList.toggle('active', btn.getAttribute('data-lang') === lang);
    });
  }

  function runAnimationSequence() {
    const logoBox = document.getElementById('calmLogoBox');
    const textBox = document.getElementById('calmTextBox');
    const actionsBox = document.getElementById('calmActionsBox');

    if (isReducedMotion) {
      if (logoBox) logoBox.classList.add('visible');
      if (textBox) textBox.classList.add('visible');
      if (actionsBox) actionsBox.classList.add('visible');
      return;
    }

    // Step 1: 0ms - Background and breathing orb already rendering
    // Step 2: 1000ms - Logo fades in
    setTimeout(() => {
      if (logoBox) logoBox.classList.add('visible');
    }, 1000);

    // Step 3: 1600ms - Welcome message appears
    setTimeout(() => {
      if (textBox) textBox.classList.add('visible');
    }, 1600);

    // Step 4: 2200ms - Actions become interactive
    setTimeout(() => {
      if (actionsBox) actionsBox.classList.add('visible');
    }, 2200);
  }

  function skipAnimation() {
    const logoBox = document.getElementById('calmLogoBox');
    const textBox = document.getElementById('calmTextBox');
    const actionsBox = document.getElementById('calmActionsBox');
    if (logoBox) logoBox.classList.add('visible');
    if (textBox) textBox.classList.add('visible');
    if (actionsBox) actionsBox.classList.add('visible');
  }

  function closeWelcomeOverlay(destinationTab) {
    const overlay = document.getElementById('mindbridgeWelcomeOverlay');
    if (overlay) {
      overlay.classList.add('fade-out');
      setTimeout(() => {
        overlay.style.display = 'none';
      }, 800);
    }
    if (destinationTab && typeof window.switchTab === 'function') {
      window.switchTab(destinationTab);
    }
  }

  function updateAudioWidgetState() {
    const widget = document.getElementById('calmSoundWidget');
    const icon = document.getElementById('calmAudioPlayIcon');
    if (widget) widget.style.display = isAudioPlaying ? 'inline-flex' : 'none';
    if (icon) icon.textContent = isAudioPlaying ? '⏸' : '▶';
  }

  function setupEventListeners(overlay) {
    // Skip animation button
    document.getElementById('calmSkipBtn')?.addEventListener('click', skipAnimation);

    // Reduced motion toggle
    const motionBtn = document.getElementById('calmMotionBtn');
    motionBtn?.addEventListener('click', function () {
      isReducedMotion = !isReducedMotion;
      document.body.classList.toggle('reduce-motion', isReducedMotion);
      motionBtn.classList.toggle('active', isReducedMotion);
      motionBtn.setAttribute('aria-pressed', isReducedMotion ? 'true' : 'false');
      applyLanguage(currentLang);
      if (isReducedMotion) skipAnimation();
    });

    // Language switcher
    overlay.querySelectorAll('.calm-lang-btn').forEach(btn => {
      btn.addEventListener('click', function () {
        const lang = this.getAttribute('data-lang');
        applyLanguage(lang);
      });
    });

    // Start Screening button -> Opens 20-question dynamic screening window on Chatbot screen
    document.getElementById('calmStartScreeningBtn')?.addEventListener('click', function () {
      closeWelcomeOverlay('chat');
      if (typeof window.openChatScreeningWindow === 'function') {
        setTimeout(() => window.openChatScreeningWindow(), 350);
      }
    });

    // Emergency Buttons (Header + Main)
    const triggerEmergency = () => {
      stopAudioImmediate();
      closeWelcomeOverlay('emergency');
    };
    document.getElementById('calmEmergencyHeaderBtn')?.addEventListener('click', triggerEmergency);
    document.getElementById('calmEmergencyMainBtn')?.addEventListener('click', triggerEmergency);

    // Audio opt-in / dismiss
    document.getElementById('calmAudioOptInBtn')?.addEventListener('click', function () {
      startSoftPiano();
      document.getElementById('calmAudioBanner').style.display = 'none';
    });
    document.getElementById('calmAudioDismissBtn')?.addEventListener('click', function () {
      document.getElementById('calmAudioBanner').style.display = 'none';
    });

    // Audio widget controls
    document.getElementById('calmAudioToggleBtn')?.addEventListener('click', function () {
      if (isAudioPlaying) {
        pauseAudio();
      } else {
        startSoftPiano();
      }
    });

    document.getElementById('calmVolumeSlider')?.addEventListener('input', function (e) {
      setAudioVolume(Number(e.target.value));
    });

    // Voice ducking integration with existing screener mic button
    const origToggleMic = window.toggleScreenerVoiceDoctor;
    if (typeof origToggleMic === 'function') {
      window.toggleScreenerVoiceDoctor = function () {
        if (isAudioPlaying && masterGain && audioCtx) {
          // Temporarily duck audio
          masterGain.gain.setTargetAtTime(0.0001, audioCtx.currentTime, 0.1);
        }
        return origToggleMic.apply(this, arguments);
      };
    }
  }

  // Self-initialize on DOMContentLoaded or immediately if already loaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', buildWelcomeOverlay);
  } else {
    buildWelcomeOverlay();
  }

  // Expose global controller
  window.MindBridgeCalmWelcome = {
    open: buildWelcomeOverlay,
    close: closeWelcomeOverlay,
    skip: skipAnimation,
    pauseAudio: pauseAudio,
    stopAudio: stopAudioImmediate
  };

})();
