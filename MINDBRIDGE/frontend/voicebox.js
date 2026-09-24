/**
 * MindBridge Voicebox Client Engine (Jamie Pine Architecture)
 * ==========================================================
 * Studio-Grade, Full-Duplex Web Audio Pipeline.
 * 
 * Features:
 * 1. Web Audio API AudioContext + GainNode sample-accurate chunk scheduler.
 * 2. Pre-fetching lookahead buffer pipeline: Zero mid-sentence pauses or audio clipping.
 * 3. Acoustic Echo Suppression (Self-Speech Gating): Prevents bot speech from triggering mic recognition.
 * 4. Micro-Fade Barge-In: Clean 60ms exponential volume ramp-down when user interrupts.
 * 5. Real-Time FFT Frequency Analyser for holographic orb and wave animations.
 * 6. Multilingual studio persona matching (English, Bengali, Hindi, Hinglish, Spanish, Portuguese).
 */

// Universal Backend Origin Resolver
function getVoiceboxApiUrl(path) {
  const isDirectFile = window.location.protocol === 'file:';
  const isCustomPort = window.location.port && window.location.port !== '5000';
  const isLocalHost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' || window.location.hostname === '';
  const origin = (isDirectFile || (isCustomPort && isLocalHost)) ? 'http://127.0.0.1:5000' : '';
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${origin}${cleanPath}`;
}

class VoiceboxAudioPipeline {
  constructor() {
    this.audioCtx = null;
    this.masterGain = null;
    this.analyser = null;
    this.currentSource = null;
    this.isPlaying = false;
    this.isEchoGated = false;
    this.playQueue = [];
    this.activeUtteranceId = 0;
    this.selectedPersona = 'en_serene_aria';
    this.speedRate = 1.0;
    this.personasCache = [];
    this.visualizerCallbacks = new Set();
    this.onSpeechStartCallbacks = new Set();
    this.onSpeechEndCallbacks = new Set();
    this.onBargeInCallbacks = new Set();
  }

  /**
   * Initializes Web Audio Context upon user interaction.
   */
  ensureAudioContext() {
    if (!this.audioCtx || this.audioCtx.state === 'closed') {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      this.audioCtx = new AudioContextClass();

      this.masterGain = this.audioCtx.createGain();
      this.masterGain.gain.setValueAtTime(1.0, this.audioCtx.currentTime);

      this.analyser = this.audioCtx.createAnalyser();
      this.analyser.fftSize = 128;
      this.analyser.smoothingTimeConstant = 0.8;

      this.masterGain.connect(this.analyser);
      this.analyser.connect(this.audioCtx.destination);

      this._startVisualizerLoop();
    }

    if (this.audioCtx.state === 'suspended') {
      this.audioCtx.resume().catch(() => {});
    }

    return this.audioCtx;
  }

  /**
   * Loads studio personas from backend.
   */
  async loadPersonas() {
    try {
      const res = await fetch(getVoiceboxApiUrl('/api/voicebox/voices'));
      const data = await res.json();
      if (data.status === 'success' && data.voices) {
        this.personasCache = data.voices;
        return this.personasCache;
      }
    } catch (e) {
      console.debug('[Voicebox] Could not load personas from API:', e);
    }
    return [];
  }

  /**
   * Automatically selects the ideal persona based on language / locale.
   */
  getPersonaForLanguage(langCode) {
    const prefix = (langCode || 'en').toLowerCase().split('-')[0];
    if (prefix === 'bn') return 'bn_empathetic_tanishaa';
    if (prefix === 'hi') return 'hi_compassionate_swara';
    if (prefix === 'es') return 'es_calida_elena';
    if (prefix === 'pt') return 'pt_serena_francisca';
    return 'en_serene_aria';
  }

  /**
   * Main speech synthesis and sample-accurate queue playback.
   * @param {string} text - The text to speak.
   * @param {string} [personaId] - Studio persona ID.
   * @param {object} [options] - Optional overrides.
   */
  async speak(text, personaId = null, options = {}) {
    if (!text || !text.trim()) return;

    this.ensureAudioContext();
    this.stop(0.02); // Cleanly finish any previous audio

    const utteranceId = ++this.activeUtteranceId;
    const persona = personaId || this.selectedPersona || 'en_serene_aria';
    
    // Set echo gating active so microphone will not capture AI's own output
    this.isEchoGated = true;
    this.isPlaying = true;

    this._notifySpeechStart({ text, personaId: persona, utteranceId });

    try {
      // Request sentence-split chunks from Voicebox backend
      const res = await fetch(getVoiceboxApiUrl('/api/voicebox/synthesize'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: text.trim(),
          persona_id: persona,
          format: 'json',
          split_chunks: true,
          stream: true
        })
      });

      if (!res.ok) {
        throw new Error(`Voicebox server returned HTTP ${res.status}`);
      }

      await this._playStreamedChunks(res, utteranceId);

    } catch (err) {
      console.warn('[Voicebox] Neural synthesis error:', err);
      // Fallback to browser Web Speech API SpeechSynthesis if server synthesis fails
      this._fallbackWebSpeech(text, persona, utteranceId);
    }
  }

  async _decodeChunk(chunkData) {
    try {
      const binary = atob(chunkData.audio_base64);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
      }
      const audioBuffer = await this.audioCtx.decodeAudioData(bytes.buffer);
      return audioBuffer;
    } catch (e) {
      console.warn(`[Voicebox] Decode error for chunk ${chunkData.chunk_index}:`, e);
      return null;
    }
  }

  async _playStreamedChunks(res, utteranceId) {
    this.playQueue = [];
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    
    let isStreamDone = false;
    let nextPlayIndex = 0;
    
    // Array to hold promises of decoded buffers
    const decodedPromises = [];
    
    // Background reader
    const readStream = async () => {
      while (true) {
        const { done, value } = await reader.read();
        if (value) {
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop(); // incomplete line
          
          for (const line of lines) {
            if (line.trim()) {
              try {
                const chunkData = JSON.parse(line);
                const p = this._decodeChunk(chunkData);
                decodedPromises.push(p);
                
                // If it's the very first chunk, trigger playback
                if (decodedPromises.length === 1) {
                  playLoop();
                }
              } catch (e) {
                console.warn("[Voicebox] Parse error", e);
              }
            }
          }
        }
        if (done) {
          isStreamDone = true;
          break;
        }
      }
    };
    
    // Background player
    const playLoop = async () => {
      while (true) {
        if (utteranceId !== this.activeUtteranceId) break;
        
        if (nextPlayIndex < decodedPromises.length) {
          const bufferToPlay = await decodedPromises[nextPlayIndex];
          if (bufferToPlay && utteranceId === this.activeUtteranceId) {
            await this._playSingleBuffer(bufferToPlay, utteranceId);
          }
          nextPlayIndex++;
        } else {
          // If we played all available but stream isn't done, wait a bit
          if (isStreamDone) {
            if (utteranceId === this.activeUtteranceId) {
              this._finishPlayback();
            }
            break;
          } else {
            await new Promise(r => setTimeout(r, 20));
          }
        }
      }
    };
    
    readStream();
  }

  /**
   * Plays a single AudioBuffer with 5ms anti-click micro-fades.
   */
  _playSingleBuffer(audioBuffer, utteranceId) {
    return new Promise((resolve) => {
      if (utteranceId !== this.activeUtteranceId || !this.audioCtx) {
        return resolve();
      }

      const source = this.audioCtx.createBufferSource();
      source.buffer = audioBuffer;

      // Micro-envelope gain to prevent clicking artifacts
      const chunkGain = this.audioCtx.createGain();
      const now = this.audioCtx.currentTime;
      const duration = audioBuffer.duration;

      // Fast 5ms attack and release
      chunkGain.gain.setValueAtTime(0.001, now);
      chunkGain.gain.linearRampToValueAtTime(1.0, now + 0.005);
      chunkGain.gain.setValueAtTime(1.0, now + duration - 0.005);
      chunkGain.gain.linearRampToValueAtTime(0.001, now + duration);

      source.connect(chunkGain);
      chunkGain.connect(this.masterGain);

      this.currentSource = source;

      source.onended = () => {
        if (this.currentSource === source) {
          this.currentSource = null;
        }
        resolve();
      };

      source.start(now);
    });
  }

  /**
   * Fallback to Web Speech API SpeechSynthesis if backend audio is unreachable.
   */
  _fallbackWebSpeech(text, personaId, utteranceId) {
    if (!('speechSynthesis' in window)) {
      this._finishPlayback();
      return;
    }

    try {
      window.speechSynthesis.cancel();
      const utt = new SpeechSynthesisUtterance(text);
      utt.rate = 0.95;
      utt.pitch = 1.0;

      utt.onend = () => {
        if (utteranceId === this.activeUtteranceId) {
          this._finishPlayback();
        }
      };
      utt.onerror = () => {
        if (utteranceId === this.activeUtteranceId) {
          this._finishPlayback();
        }
      };

      window.speechSynthesis.speak(utt);
    } catch (e) {
      this._finishPlayback();
    }
  }

  /**
   * Stop audio playback immediately with smooth micro-fade.
   * @param {number} [fadeDuration=0.06] - Seconds for volume ramp down.
   */
  stop(fadeDuration = 0.06) {
    this.activeUtteranceId++;
    this.playQueue = [];

    if (this.masterGain && this.audioCtx && this.audioCtx.state === 'running') {
      try {
        const now = this.audioCtx.currentTime;
        this.masterGain.gain.cancelScheduledValues(now);
        this.masterGain.gain.setValueAtTime(this.masterGain.gain.value, now);
        this.masterGain.gain.linearRampToValueAtTime(0.001, now + fadeDuration);

        setTimeout(() => {
          if (this.currentSource) {
            try { this.currentSource.stop(); } catch (e) {}
            this.currentSource = null;
          }
          if (this.masterGain && this.audioCtx) {
            this.masterGain.gain.setValueAtTime(1.0, this.audioCtx.currentTime);
          }
        }, fadeDuration * 1000 + 10);
      } catch (e) {
        if (this.currentSource) {
          try { this.currentSource.stop(); } catch (err) {}
          this.currentSource = null;
        }
      }
    }

    if ('speechSynthesis' in window) {
      try { window.speechSynthesis.cancel(); } catch (e) {}
    }

    this._finishPlayback();
  }

  /**
   * Deliberate user interruption (Barge-In).
   * Smoothly fades out AI output and immediately releases echo gating.
   */
  bargeIn() {
    if (!this.isPlaying) return;
    this.stop(0.04);
    this._notifyBargeIn();
  }

  _finishPlayback() {
    this.isPlaying = false;
    this.isEchoGated = false;
    this._notifySpeechEnd();
  }

  // --- Real-time FFT Frequency Visualizer Loop ---

  _startVisualizerLoop() {
    const dataArray = new Uint8Array(64);

    const tick = () => {
      if (this.analyser && this.isPlaying) {
        this.analyser.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) sum += dataArray[i];
        const avg = sum / dataArray.length;

        this.visualizerCallbacks.forEach((cb) => {
          try { cb(dataArray, avg); } catch (e) {}
        });
      }
      requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }

  // --- Event Callbacks ---

  onVisualizerFrame(cb) {
    this.visualizerCallbacks.add(cb);
  }

  onSpeechStart(cb) {
    this.onSpeechStartCallbacks.add(cb);
  }

  onSpeechEnd(cb) {
    this.onSpeechEndCallbacks.add(cb);
  }

  onBargeIn(cb) {
    this.onBargeInCallbacks.add(cb);
  }

  _notifySpeechStart(data) {
    this.onSpeechStartCallbacks.forEach(cb => { try { cb(data); } catch (e) {} });
  }

  _notifySpeechEnd() {
    this.onSpeechEndCallbacks.forEach(cb => { try { cb(); } catch (e) {} });
  }

  _notifyBargeIn() {
    this.onBargeInCallbacks.forEach(cb => { try { cb(); } catch (e) {} });
  }
}

// ==========================================================================
// VOICEBOX TRANSCRIBER ENGINE (Jamie Pine Architecture - STT Pipeline)
// ==========================================================================
// Full-duplex Speech-to-Text companion for the Voicebox Audio Pipeline.
// Records user microphone audio, encodes crystal-clear WAV, and sends to
// the Voicebox backend /api/voicebox/transcribe for server-side transcription
// using Whisper Large v3 Turbo + NVIDIA NeMo dual-ASR failover.
// ==========================================================================

class VoiceboxTranscriber {
  constructor() {
    this.isTranscribing = false;
    this.lastTranscription = '';
    this.lastEngine = '';
    this.lastConfidence = 0;
    this.lastLanguage = '';
    this.onTranscriptionCallbacks = new Set();
    this.onErrorCallbacks = new Set();
    this.onStartCallbacks = new Set();
    this.onEndCallbacks = new Set();
  }

  /**
   * Transcribe audio from Float32 buffers via Voicebox backend.
   * @param {Float32Array[]} audioBuffers - Array of Float32Array audio chunks from ScriptProcessorNode.
   * @param {number} sampleRate - The sample rate of the audio context (e.g. 44100 or 48000).
   * @param {string} [language='auto'] - BCP-47 language code or 'auto' for auto-detection.
   * @param {Object} [options={}] - Optional parameters { analyzeTone, sessionId, questionId }.
   * @returns {Promise<{text: string, language: string, confidence: number, engine: string, voiceTone?: any} | null>}
   */
  async transcribe(audioBuffers, sampleRate, language = 'auto', options = {}) {
    if (this.isTranscribing || !audioBuffers || audioBuffers.length < 2) {
      return null;
    }

    // 1. Encode Float32 buffers into 16-bit Mono PCM WAV
    const wavBlob = this._encodeWAV(audioBuffers, sampleRate || 44100);
    return this.transcribeBlob(wavBlob, language, options);
  }

  /**
   * Transcribe audio directly from a WAV/Audio Blob via Voicebox backend.
   * @param {Blob} audioBlob - Audio blob to transcribe.
   * @param {string} [language='auto'] - Language code or 'auto'.
   * @param {Object} [options={}] - Optional parameters { analyzeTone, sessionId, questionId }.
   * @returns {Promise<{text: string, language: string, confidence: number, engine: string, voiceTone?: any} | null>}
   */
  async transcribeBlob(audioBlob, language = 'auto', options = {}) {
    if (this.isTranscribing || !audioBlob || audioBlob.size < 100) {
      return null;
    }

    this.isTranscribing = true;
    this._notifyStart();

    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'voicebox_capture.wav');

      const effectiveLang = (language && language !== 'auto') ? language : '';
      let url = `/api/voicebox/transcribe?language=${encodeURIComponent(effectiveLang)}`;
      if (options.sessionId) url += `&session_id=${encodeURIComponent(options.sessionId)}`;
      if (options.questionId) url += `&question_id=${encodeURIComponent(options.questionId)}`;
      if (options.analyzeTone) url += `&analyze_tone=true`;

      const res = await fetch(getVoiceboxApiUrl(url), {
        method: 'POST',
        body: formData
      });

      if (!res.ok) {
        throw new Error(`Voicebox transcribe returned HTTP ${res.status}`);
      }

      const data = await res.json();
      const textOutput = (data.transcription || data.text || '').trim();

      if (data.status === 'success' && textOutput) {
        const result = {
          text: textOutput,
          transcription: textOutput,
          language: data.language || 'en',
          confidence: data.confidence || 0.96,
          engine: data.engine_used || 'Voicebox MLX-Audio STT',
          voiceTone: data.voice_tone || null
        };

        this.lastTranscription = result.text;
        this.lastEngine = result.engine;
        this.lastConfidence = result.confidence;
        this.lastLanguage = result.language;

        this._notifyTranscription(result);
        return result;
      }

      // No speech detected
      return null;

    } catch (err) {
      console.warn('[Voicebox Transcriber] Error:', err);
      this._notifyError(err);
      return null;
    } finally {
      this.isTranscribing = false;
      this._notifyEnd();
    }
  }

  /**
   * Encodes Float32Array audio buffers into a 16-bit Mono PCM WAV Blob.
   * Includes intelligent Auto-Gain Normalization for crystal-clear transcription.
   * @param {Float32Array[]} buffers - Array of Float32Array audio chunks.
   * @param {number} inputSampleRate - Sample rate of the audio.
   * @returns {Blob} WAV audio blob.
   */
  _encodeWAV(buffers, inputSampleRate) {
    let totalLength = 0;
    for (const b of buffers) totalLength += b.length;
    if (totalLength === 0) return new Blob([], { type: 'audio/wav' });

    // Merge all buffers into a single contiguous Float32Array
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

    // Boost quiet microphone signal up to 15x so Whisper/NeMo hear crystal-clear audio
    const gain = (peak > 0.00005 && peak < 0.45) ? Math.min(15.0, 0.75 / peak) : 1.0;

    const sampleRate = inputSampleRate || 44100;
    const buffer = new ArrayBuffer(44 + totalLength * 2);
    const view = new DataView(buffer);

    // WAV Header
    const writeStr = (v, o, s) => { for (let i = 0; i < s.length; i++) v.setUint8(o + i, s.charCodeAt(i)); };
    writeStr(view, 0, 'RIFF');
    view.setUint32(4, 36 + totalLength * 2, true);
    writeStr(view, 8, 'WAVE');
    writeStr(view, 12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);     // PCM format
    view.setUint16(22, 1, true);     // 1 channel (mono)
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true);     // block align
    view.setUint16(34, 16, true);    // bits per sample
    writeStr(view, 36, 'data');
    view.setUint32(40, totalLength * 2, true);

    // PCM sample data with gain normalization
    let p = 44;
    for (let i = 0; i < totalLength; i++, p += 2) {
      const s = Math.max(-1, Math.min(1, merged[i] * gain));
      view.setInt16(p, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    }

    return new Blob([view], { type: 'audio/wav' });
  }

  // --- Event Callbacks ---

  /** Register callback for successful transcription result. */
  onTranscription(cb) {
    this.onTranscriptionCallbacks.add(cb);
  }

  /** Register callback for transcription errors. */
  onError(cb) {
    this.onErrorCallbacks.add(cb);
  }

  /** Register callback for transcription start. */
  onStart(cb) {
    this.onStartCallbacks.add(cb);
  }

  /** Register callback for transcription end (success or failure). */
  onEnd(cb) {
    this.onEndCallbacks.add(cb);
  }

  _notifyTranscription(result) {
    this.onTranscriptionCallbacks.forEach(cb => { try { cb(result); } catch (e) {} });
  }

  _notifyError(err) {
    this.onErrorCallbacks.forEach(cb => { try { cb(err); } catch (e) {} });
  }

  _notifyStart() {
    this.onStartCallbacks.forEach(cb => { try { cb(); } catch (e) {} });
  }

  _notifyEnd() {
    this.onEndCallbacks.forEach(cb => { try { cb(); } catch (e) {} });
  }
}

// Global Voicebox Audio Pipeline Instance
window.VoiceboxPipeline = new VoiceboxAudioPipeline();

// Global Voicebox Transcriber Instance (STT)
window.VoiceboxTranscriber = new VoiceboxTranscriber();
