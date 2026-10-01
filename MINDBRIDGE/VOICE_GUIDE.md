# MindBridge Voice-Answer Module & Speech-to-Text Architecture Guide

## Overview

The **MindBridge Voice-Answer Module** provides a robust, clinical-grade speech-to-text pipeline engineered for 2026 browsers and mobile devices. It enables users to answer clinical screening questions naturally using voice, displays real-time audio waveforms and recording status, transcribes speech with high accuracy across English and Indian languages (Hindi, Bengali, Tamil, Telugu, Spanish, Portuguese), and presents the transcription in an editable textbox for user review before confirmation.

---

## 1. System Architecture & Flow

```
[User Clicks Mic Button]
          │
          ▼
[Check Microphone Permissions] ──(Denied/Blocked)──► [Show Friendly Error Banner with Guidance]
          │ (Granted)
          ▼
[Detect Engine Preference]
    ├─── If Web Speech API Enabled & Supported:
    │         └──► Web Speech API (en-IN / locale)
    │                   │ (On success)
    │                   ▼
    │         [Populate Editable Textbox]
    │                   │ (If fails or blocked by shields)
    │                   ▼
    └─── Default / MediaRecorder Flow:
              │
              ▼
    [MediaRecorder: audio/webm;codecs=opus (or mp4/ogg)]
              │
              ▼ (Max 60s / Auto-silence / Manual Stop)
    [Collect Audio Chunks -> Blob -> FormData]
              │
              ▼ POST /api/transcribe
    [Backend AudioConverter (PyAV)]: Decodes to 16kHz Mono 16-bit PCM WAV
              │
              ▼
    [Tier 1: Self-Hosted Faster-Whisper (Int8 CPU/GPU)]
              │ (If silence or confidence low)
              ▼
    [Tier 2: Google Acoustic Bridge (en-IN, hi-IN, bn-IN, etc.)]
              │ (If configured)
              ▼
    [Tier 3: OpenAI Cloud Whisper API]
              │
              ▼
    [JSON Response: { status: "success", text: "...", detected_language: "..." }]
              │
              ▼
    [Frontend: Displays Text in Textarea for Editing]
    [User Reviews -> Confirms Answer or Re-records]
```

---

## 2. Running Locally & HTTPS Setup

### Local Development (localhost)
Modern browsers (Chrome, Edge, Firefox, Brave) treat `http://localhost` and `http://127.0.0.1` as **secure contexts** (`window.isSecureContext === true`). Microphone permissions can be granted and remembered directly without SSL certificates:

```bash
# Start backend server from project root
python run.py

# Access application in your browser
http://127.0.0.1:5000
```

### Local Network / Mobile Testing with HTTPS
When testing from a mobile phone on the same Wi-Fi network (e.g. `http://192.168.x.x:5000`), modern mobile browsers (Chrome Android, Safari iOS) **block microphone access** on insecure HTTP. You must serve over HTTPS.

#### Option A: Self-Signed SSL with Python (Recommended for dev)
1. Generate a self-signed certificate:
   ```bash
   openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365 -subj "/CN=localhost"
   ```
2. Start Flask with SSL:
   ```python
   # In run.py:
   app.run(host="0.0.0.0", port=5000, ssl_context=("cert.pem", "key.pem"))
   ```

#### Option B: Cloudflare Tunnel / Ngrok (Zero-config HTTPS for Mobile)
```bash
# Using Cloudflare Tunnel
cloudflared tunnel --url http://127.0.0.1:5000

# Or using ngrok
ngrok http 5000
```
Open the provided `https://xxxx.trycloudflare.com` URL on your mobile phone to test native microphone permissions.

---

## 3. Configuring the Speech-to-Text Engine

The system supports multiple interchangeable and tiered STT backends configured via environment variables:

| Variable | Default | Options | Description |
| :--- | :--- | :--- | :--- |
| `WHISPER_MODEL` | `tiny` | `tiny`, `base`, `small`, `medium`, `large-v3` | Model size for self-hosted `faster-whisper`. `tiny` runs in ~150ms on CPU. |
| `WHISPER_DEVICE` | `cpu` | `cpu`, `cuda` | Hardware accelerator. Set to `cuda` if an NVIDIA GPU with cuDNN is available. |
| `WHISPER_COMPUTE` | `int8` | `int8`, `float16`, `float32` | Quantization precision. `int8` offers 4x memory reduction on CPU. |
| `OPENAI_API_KEY` | *(empty)* | `sk-...` | Optional. If present, activates Cloud Whisper API as an extra failover tier. |

### Upgrading to Higher Precision Whisper:
```bash
# Windows PowerShell
$env:WHISPER_MODEL="base"
python run.py
```

---

## 4. Browser Compatibility Matrix (2026)

| Browser | Platform | Primary Pipeline (MediaRecorder + Backend) | Web Speech API Fallback | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Google Chrome** | Desktop & Android | Full Support (`audio/webm;codecs=opus`) | Full Support (`webkitSpeechRecognition`) | Automatic permission persistence on HTTPS/localhost. |
| **Microsoft Edge** | Desktop & Mobile | Full Support (`audio/webm;codecs=opus`) | Full Support (`SpeechRecognition`) | Native Chromium speech stack. |
| **Mozilla Firefox** | Desktop & Android | Full Support (`audio/webm;codecs=opus`, `audio/ogg`) | Disabled by default in Firefox config | MediaRecorder pipeline works reliably. |
| **Apple Safari** | macOS & iOS 14.3+ | Full Support (`audio/mp4`, `audio/webm`) | Supported on iOS 14.5+ | `getBestMediaRecorderMimeType()` detects `audio/mp4` on iOS smoothly. |
| **Brave Browser** | Desktop & Android | Full Support | Blocked by default (Shields) | Frontend automatically catches shields error and seamlessly falls back to MediaRecorder. |

---

## 5. Microphone Troubleshooting & Permissions

If the microphone does not catch speech, check the following:

1. **Permission Denied (`NotAllowedError`)**:
   - The user previously clicked "Block".
   - **Resolution**: Click the lock/settings icon in the browser address bar, set "Microphone" to **Allow**, and reload the page.
2. **No Input Device (`NotFoundError`)**:
   - No microphone is plugged in or enabled in Windows/macOS sound settings.
   - **Resolution**: Plug in a headset or microphone and verify default recording device in Windows Settings > System > Sound.
3. **Hardware Mute / Mic Busy (`NotReadableError`)**:
   - Another app (Teams, Zoom, Discord) has exclusive access to the microphone.
   - **Resolution**: Close the competing app and retry.
4. **Site Served Over Plain IP (Non-localhost HTTP)**:
   - Browsers disable `getUserMedia` over unencrypted LAN IP addresses (`http://192.168.x.x`).
   - **Resolution**: Use `localhost` on the host machine or use an HTTPS tunnel for external devices.

---

## 6. Security, Privacy & Compliance

- **Audio Ephemerality**: Voice recordings are processed in memory and written only to temporary files with unique session UUIDs. All temporary audio artifacts are **deleted immediately** (`finally:` block) after transcription finishes.
- **In-Transit Encryption**: All audio payloads sent to `/api/transcribe` require TLS/HTTPS in production.
- **User Informed Consent & Transparency**:
  - The UI displays the notice: *"Your voice is recorded only to convert it to text. You can review and edit the transcript before submitting."*
  - The user has full control to edit, correct typos, re-record, or type their answer before confirming.
  - A user-controlled opt-in toggle is provided for Voice-Tone analysis: *"Include non-diagnostic voice tone analysis (observed speech cadence & pitch patterns)"*.

---

## 7. Voice-Tone & Emotion Analysis Architecture

The **MindBridge Voice-Tone Module** (`backend/voice_tone_analyzer.py`) captures prosodic and acoustic dynamics from speech during screening responses to provide empathetic, contextual reflections of vocal cadence, pitch variability, and situational tension.

### 7.1 Acoustic & Prosodic Feature Extraction Pipeline

When an audio clip is recorded, the in-memory decoder (`AcousticProsodicExtractor`) computes four primary acoustic dimensions:

```
[Raw Audio WebM/WAV]
        │
        ▼ (PyAV In-Memory 16kHz Mono Float32)
  ┌─────────────────────────────────────────────────────────────┐
  │ 1. Pitch F0 Tracking (Autocorrelation 50-400Hz Windowing)   │
  │    - Mean F0, F0 Standard Deviation, Pitch Range (Hz)       │
  │                                                             │
  │ 2. Energy / Loudness Dynamics                               │
  │    - RMS Energy in dBFS, Dynamic Energy Range               │
  │                                                             │
  │ 3. Temporal Cadence & Speaking Rate                         │
  │    - Voiced/Unvoiced Ratio, Syllabic Peak Rate (syllables/s)│
  │                                                             │
  │ 4. Spectral Timbre & Mel Frequency Cepstral Coefficients    │
  │    - 13 MFCCs + Delta Coefficients interpolated to (26, 64) │
  └─────────────────────────────────────────────────────────────┘
```

### 7.2 Deep Learning Speech Emotion Recognition (SER) Model

The extracted 26-channel feature map is evaluated by a PyTorch neural network (`SER_CNN_BiLSTM_Net`):

```
Input: Tensor (Batch, 26, 64)
   │
   ├──► Conv1D (Filters: 32, Kernel: 5, ReLU) + MaxPool1D
   ├──► Conv1D (Filters: 64, Kernel: 3, ReLU) + MaxPool1D
   ├──► Dropout (0.25)
   │
   ├──► 2-Layer Bidirectional LSTM (Hidden: 64, Bidirectional -> 128)
   ├──► Temporal Self-Attention Pooling (Weights time steps by salience)
   │
   ├──► Dense Classifier Layer (128 -> 64 -> 5)
   └──► Softmax Layer -> Class Probabilities:
          • neutral_calm
          • tense_anxious
          • sad_low_energy
          • flat_monotone
          • energetic_positive
```

### 7.3 Multi-Answer Session Aggregator

Rather than making conclusions based on a single response, the `VoiceToneSessionAggregator` pools distributions across all voice answers in a screening session:
- **Mean Probability Distribution**: Average probability vector across answered questions.
- **Dominant Pattern**: Tone class exhibiting the highest aggregate score.
- **Tone Variability**: Variance in tone distribution across questions (measures vocal stability vs fluctuation).
- **Acoustic Averages**: Mean pitch, pitch variance, RMS energy, and syllable rate across the entire session.

### 7.4 Non-Diagnostic Ethical Guardrails & Framing

> [!IMPORTANT]
> **Clinical Non-Diagnostic Mandate:**
> Voice-tone analysis in MindBridge is strictly informational and empathetic. It is **NOT** a diagnosis of depression, anxiety, or any psychiatric disorder. It is framed transparently as *"observed situational voice-tone patterns"* that reflect current speaking energy, stress, or tiredness.

Every analysis response and UI view includes the clinical disclaimer:
*"Observed voice-tone patterns reflect situational vocal dynamics (e.g. fatigue, cadence, or tension) and are NOT a psychological or medical diagnosis."*

### 7.5 API Endpoints

#### 1. POST `/api/transcribe` (Unified STT + Tone Analysis)
- **Parameters**: `audio` (file/bytes), `language` (e.g. `en-IN`), `session_id`, `question_id`, `analyze_tone=true`.
- **Response**:
```json
{
  "status": "success",
  "text": "I feel tired and a bit overwhelmed lately.",
  "detected_language": "en",
  "engine_used": "faster-whisper",
  "voice_tone": {
    "dominant_tone": "sad_low_energy",
    "probabilities": {
      "neutral_calm": 0.15,
      "tense_anxious": 0.22,
      "sad_low_energy": 0.48,
      "flat_monotone": 0.10,
      "energetic_positive": 0.05
    },
    "prosodic_features": {
      "mean_f0_hz": 162.4,
      "pitch_std_hz": 18.2,
      "energy_rms_db": -24.6,
      "speaking_rate_syllables_sec": 2.8,
      "voiced_ratio": 0.54
    },
    "interpretation": "Vocal pitch and pace indicate lower energy and subdued cadence."
  }
}
```

#### 2. POST `/api/analyze_voice_tone` (Standalone Tone Analysis)
- **Parameters**: `audio` (file/bytes), `session_id`, `question_id`.
- **Response**: Returns acoustic telemetry, probabilities, dominant tone, and disclaimer.

#### 3. GET `/api/screener/session/<session_id>/voice-tone`
- **Response**: Returns the session-level aggregated summary across all voice responses.

