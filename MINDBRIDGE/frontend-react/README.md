# MindBridge Calm Welcome Experience

> **An ethical, accessible, and compassionate opening animation for the MindBridge mental-health screening and crisis-support platform.**

---

## 🌸 Philosophical & Ethical Manifesto

Traditional digital applications frequently rely on predatory behavioral psychology (streaks, countdown timers, artificial urgency, reward loops, and forced engagement). In a **mental health context**, these dark patterns are unacceptable and dangerous; someone in psychological vulnerability or crisis requires:
- **Calm** rather than adrenaline.
- **Dignity & Autonomy** rather than behavioral conditioning.
- **Unconditional Safety** rather than paywalls or mandatory registration before emergency help.

### Strict Ethical Guardrails Adhered To:
1. **Zero Gamification & Dark Patterns:** No streaks, no arbitrary badges, no scoreboards, and no social comparison metrics.
2. **Zero Countdown Pressure:** Users are never rushed with timers ("Only 10 seconds remaining"), nor warned with manipulative retention dialogs ("Don't leave now or lose progress").
3. **Unauthenticated Immediate Emergency Access:** The **Emergency Help** button is visible from millisecond zero. It is never hidden behind an animation sequence or gated behind authentication.
4. **Autonomous Sensory Control:** Audio **never autoplays** on page load. All audio is opt-in, strictly capped at a 20% safe decibel threshold, and automatically ducks/mutes when voice recording starts or during an emergency.
5. **Radical User Agency:** The user can skip the opening animation at any millisecond, toggle reduced motion, change languages dynamically, or pause their session without penalty.

---

## 🎨 Visual Design & Neuro-Aesthetics

- **Soft Low-Contrast Chromatic Palette:**
  - Light Sky Blue (`#DCEEFF`)
  - Soft Lavender (`#E9E2FF`)
  - Light Mint Green (`#DFF5EC`)
  - Warm Beige (`#F8F3EA`)
- **Parasympathetic Breathing Orb:**
  - Scale begins at `0.95` and expands gently to `1.05`.
  - 5.2-second complete respiratory cycle matching human vagal nerve parasympathetic down-regulation.
  - Organic multi-layered auras with zero high-frequency particle jitter, zero strobe, and zero sharp rotations.
- **Minimal Compassionate Logo:**
  - Supportive bridge arch spanning across two shores.
  - Blooming heart motif representing resilience and empathetic connection.

---

## ♿ Accessibility Compliance (WCAG 2.2 AAA Standards)

1. **System & Manual Reduced Motion:**
   - Detects CSS `prefers-reduced-motion: reduce`.
   - Freezes orb scaling into an inert, calming gradient sphere.
   - Bypasses multi-second sequential fades to present the core options immediately.
   - Dedicated toggle button available in the top bar for users with vestibular or sensory sensitivities.
2. **Keyboard Navigation & Focus Management:**
   - Semantic HTML5 structure (`<main>`, `<header>`, `<footer>`, `<aside>`, `<nav>`, `<button>`).
   - High-contrast 3px focus rings (`focus-visible`).
   - Modal focus trapping and `Escape` key listeners for rapid dismissal.
3. **Screen Reader (ARIA) Optimization:**
   - Decorative visual auras and breathing orbs are flagged with `aria-hidden="true"`.
   - Interactive buttons have descriptive, localized ARIA labels.
   - Emergency hotlines are declared with clear semantic links (`tel:112`, `tel:108`, `tel:14416`).

---

## 🎵 Calm Audio Engineering (`audioEngine.ts`)

- **Synthesizer Architecture:** Built using the native Web Audio API (zero audio file dependencies, zero network buffering, zero latency).
- **Target Cadence:** 68 BPM (resting heart rate synchronization).
- **Available Soundscapes:**
  1. *Soft Ambient Piano:* Pentatonic & Major 9 progressions filtered at 750 Hz.
  2. *Warm Ambient Pad:* Dual detuned oscillators with a 0.08 Hz LFO filter sweep.
  3. *Light Rainfall:* Pink noise generator filtered at 1200 Hz (completely free of thunder or loud transients).
  4. *Gentle Ocean Waves:* 9-second periodic tidal bandpass filter simulating slow deep respiration.
  5. *Gentle Mountain Stream:* Mid-register clear water trickle.
  6. *Quiet Forest Ambience:* Warm, low-frequency atmospheric rustle.
  7. *Silence / No Sound:* Zero sensory stimulation.
- **Clinical Event Hooks:**
  - `onVoiceRecordingStart()`: Immediately ducks audio to `0.0001` to eliminate mic bleed and acoustic interference.
  - `onVoiceRecordingEnd()`: Gently ramps audio back to the user's chosen volume level over 3.0 seconds.
  - `onEmergencyModeStart()`: Immediately terminates all audio with zero ramp delay for complete mental clarity.
- **Safe Volume Envelopes:**
  - Initial volume: **8%** (`0.08`)
  - Hard application cap: **20%** (`0.20`)

---

## 🌍 Multilingual Inclusivity

MindBridge provides authentic, human-reviewed translations for:
- **English** (`en`)
- **Bengali** (`bn` - বাংলা)
- **Hindi** (`hi` - हिंदी)

Typography is backed by Google Fonts (`Inter`, `Noto Sans Bengali`, and `Noto Sans Devanagari`).

---

## 📂 Component Hierarchy

```
src/
├── app/
│   ├── globals.css                # Tailwind imports, font definitions, reduced-motion rules
│   ├── layout.tsx                 # Root layout with responsive viewport & meta tags
│   └── page.tsx                   # Interactive demonstration container
├── components/
│   ├── WelcomeAnimation.tsx       # Core orchestrator: 2-4s timed choreography & state
│   ├── BreathingOrb.tsx           # Organic Framer Motion breathing orb & reduced-motion fallback
│   ├── MindBridgeLogo.tsx         # SVG bridge + heart compassionate insignia
│   ├── WelcomeActions.tsx         # Primary [Start Screening], [Emergency Help], & language chips
│   ├── CalmAudioController.tsx    # Audio dropdown, volume slider (0-20% cap), and playback controls
│   ├── EmergencyButton.tsx        # High-visibility, unauthenticated crisis entry point
│   ├── EmergencyModal.tsx         # Hotlines, ambulance dispatch, SOS SMS, & crisis hospital maps
│   └── AccessibilityControls.tsx  # Skip animation, reduced motion toggle, & audio mute
└── lib/
    ├── audioEngine.ts             # Web Audio API procedural synthesizer & clinical ducking engine
    ├── translations.ts            # Multilingual copy for English, Bengali, and Hindi
    └── types.ts                   # Strongly-typed TypeScript interfaces
```

---

## 🚀 Running the Project

### Installation
```bash
cd MINDBRIDGE/frontend-react
npm install
```

### Development Server
```bash
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) to experience the full interactive React / Next.js implementation.

### Production Build
```bash
npm run build
npm run start
```
