import { SoundTrackId } from './types';

export const DEFAULT_VOLUME = 0.08; // 8% initial volume when enabled
export const MAX_VOLUME = 0.20;     // 20% maximum in-app volume limit

export class MindBridgeAudioEngine {
  private ctx: AudioContext | null = null;
  private masterGain: GainNode | null = null;
  private currentTrack: SoundTrackId = 'none';
  private isPlaying: boolean = false;
  private isMuted: boolean = false;
  private currentVolumeLevel: number = DEFAULT_VOLUME; // internal volume (0.0 to 0.20)
  private userEnabledMusic: boolean = false;
  private activeGenerators: (() => void)[] = [];
  private loopTimer: any = null;

  constructor() {
    // AudioContext will be initialized on first user gesture
  }

  private initContext() {
    if (!this.ctx) {
      const AudioCtxClass = window.AudioContext || (window as any).webkitAudioContext;
      this.ctx = new AudioCtxClass();
      this.masterGain = this.ctx.createGain();
      this.masterGain.gain.setValueAtTime(0, this.ctx.currentTime);
      this.masterGain.connect(this.ctx.destination);
    }
    if (this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  }

  public getTrack(): SoundTrackId {
    return this.currentTrack;
  }

  public getIsPlaying(): boolean {
    return this.isPlaying;
  }

  public getIsMuted(): boolean {
    return this.isMuted;
  }

  public getVolumePercentage(): number {
    // Map internal volume (0 to 0.20) to 0-100 UI percentage
    return Math.round((this.currentVolumeLevel / MAX_VOLUME) * 100);
  }

  public setVolumeFromSlider(sliderValue: number) {
    // sliderValue is 0 to 100
    const normalized = Math.max(0, Math.min(100, sliderValue)) / 100;
    this.currentVolumeLevel = normalized * MAX_VOLUME;
    
    if (this.masterGain && this.ctx && !this.isMuted && this.isPlaying) {
      const now = this.ctx.currentTime;
      this.masterGain.gain.cancelScheduledValues(now);
      this.masterGain.gain.setTargetAtTime(this.currentVolumeLevel, now, 0.1);
    }
  }

  public toggleMute(): boolean {
    this.isMuted = !this.isMuted;
    if (this.masterGain && this.ctx) {
      const now = this.ctx.currentTime;
      this.masterGain.gain.cancelScheduledValues(now);
      if (this.isMuted) {
        this.masterGain.gain.setTargetAtTime(0, now, 0.1);
      } else if (this.isPlaying) {
        this.masterGain.gain.setTargetAtTime(this.currentVolumeLevel, now, 0.2);
      }
    }
    return this.isMuted;
  }

  public async playTrack(trackId: SoundTrackId) {
    if (trackId === 'none') {
      this.stop();
      return;
    }

    this.initContext();
    if (!this.ctx || !this.masterGain) return;

    this.userEnabledMusic = true;
    this.stopActiveSoundGenerators();

    this.currentTrack = trackId;
    this.isPlaying = true;

    // Start synthesizing the requested sound
    this.startSoundSynthesis(trackId);

    // Fade-in over 3.5 seconds to safe level
    const now = this.ctx.currentTime;
    this.masterGain.gain.cancelScheduledValues(now);
    this.masterGain.gain.setValueAtTime(0.0001, now);
    const target = this.isMuted ? 0 : this.currentVolumeLevel;
    this.masterGain.gain.linearRampToValueAtTime(target, now + 3.5);
  }

  public pause() {
    if (!this.isPlaying || !this.ctx || !this.masterGain) return;
    const now = this.ctx.currentTime;
    this.masterGain.gain.cancelScheduledValues(now);
    // Smooth 1.5s fade out before pausing
    this.masterGain.gain.linearRampToValueAtTime(0.0001, now + 1.5);
    setTimeout(() => {
      this.isPlaying = false;
      this.stopActiveSoundGenerators();
    }, 1500);
  }

  public resume() {
    if (this.currentTrack !== 'none') {
      this.playTrack(this.currentTrack);
    }
  }

  public stop() {
    if (this.ctx && this.masterGain) {
      const now = this.ctx.currentTime;
      this.masterGain.gain.cancelScheduledValues(now);
      this.masterGain.gain.linearRampToValueAtTime(0, now + 1.0);
    }
    setTimeout(() => {
      this.stopActiveSoundGenerators();
      this.isPlaying = false;
      this.currentTrack = 'none';
      this.userEnabledMusic = false;
    }, 1000);
  }

  // ---------------------------------------------------------
  // ETHICAL & CLINICAL EVENT HOOKS
  // ---------------------------------------------------------

  /**
   * Called when voice recording begins (microphone active).
   * Prevents audio collision and microphone interference.
   */
  public onVoiceRecordingStart() {
    if (this.isPlaying && this.masterGain && this.ctx) {
      const now = this.ctx.currentTime;
      this.masterGain.gain.cancelScheduledValues(now);
      // Fast duck/fade-out
      this.masterGain.gain.linearRampToValueAtTime(0.0001, now + 0.3);
    }
  }

  /**
   * Called when voice recording ends.
   * Smoothly restores calm background sound ONLY if user had enabled it.
   */
  public onVoiceRecordingEnd() {
    if (this.userEnabledMusic && this.isPlaying && this.masterGain && this.ctx && !this.isMuted) {
      const now = this.ctx.currentTime;
      this.masterGain.gain.cancelScheduledValues(now);
      this.masterGain.gain.linearRampToValueAtTime(this.currentVolumeLevel, now + 3.0);
    }
  }

  /**
   * IMMEDIATE CRISIS MODE CUTOFF
   * Stops all music immediately so user has full cognitive clarity.
   */
  public onEmergencyModeStart() {
    if (this.masterGain && this.ctx) {
      const now = this.ctx.currentTime;
      this.masterGain.gain.cancelScheduledValues(now);
      this.masterGain.gain.setValueAtTime(0, now);
    }
    this.stopActiveSoundGenerators();
    this.isPlaying = false;
  }

  // ---------------------------------------------------------
  // PROCEDURAL SOUND SYNTHESIS ENGINES
  // (Pure Web Audio API - zero latency, zero dependencies)
  // ---------------------------------------------------------

  private stopActiveSoundGenerators() {
    if (this.loopTimer) {
      clearInterval(this.loopTimer);
      this.loopTimer = null;
    }
    for (const stopFn of this.activeGenerators) {
      try { stopFn(); } catch (e) {}
    }
    this.activeGenerators = [];
  }

  private startSoundSynthesis(track: SoundTrackId) {
    if (!this.ctx || !this.masterGain) return;

    switch (track) {
      case 'piano':
        this.synthesizeSoftPiano();
        break;
      case 'pad':
        this.synthesizeWarmPad();
        break;
      case 'rain':
        this.synthesizeLightRain();
        break;
      case 'waves':
        this.synthesizeOceanWaves();
        break;
      case 'stream':
        this.synthesizeGentleStream();
        break;
      case 'forest':
        this.synthesizeQuietForest();
        break;
      default:
        break;
    }
  }

  /**
   * Soft Meditative Piano & Chimes:
   * 68 BPM target cadence (matches resting parasympathetic heart rate).
   * Pentatonic / Major 9 gentle chord progressions.
   */
  private synthesizeSoftPiano() {
    if (!this.ctx || !this.masterGain) return;
    const ctx = this.ctx;
    const dest = this.masterGain;

    // Filter to warm, mellow frequencies (soft tone, no harsh brightness)
    const filter = ctx.createBiquadFilter();
    filter.type = 'lowpass';
    filter.frequency.setValueAtTime(750, ctx.currentTime);
    filter.Q.setValueAtTime(1.2, ctx.currentTime);
    filter.connect(dest);

    // Warm chords in F Major 7 / C Major 9: frequencies in Hz
    const chords = [
      [174.61, 220.00, 261.63, 329.63], // Fmaj7 (F3, A3, C4, E4)
      [130.81, 164.81, 196.00, 246.94], // Cmaj7 (C3, E3, G3, B3)
      [146.83, 174.61, 220.00, 261.63], // Dm7 (D3, F3, A3, C4)
      [116.54, 146.83, 174.61, 220.00], // Bbmaj7 (Bb2, D3, F3, A3)
    ];

    let chordIndex = 0;
    // 68 BPM = 0.882 seconds per beat. 4 beats per bar = ~3.53 seconds per chord.
    const beatInterval = (60 / 68) * 4 * 1000;

    const playChord = () => {
      if (!this.isPlaying || ctx.state === 'closed') return;
      const notes = chords[chordIndex % chords.length];
      chordIndex++;

      notes.forEach((freq, noteIdx) => {
        // Slight arpeggiation delay (100ms) for human touch
        const noteTime = ctx.currentTime + (noteIdx * 0.12);
        const osc = ctx.createOscillator();
        const noteGain = ctx.createGain();

        osc.type = 'sine';
        osc.frequency.setValueAtTime(freq, noteTime);

        // Gentle envelope
        noteGain.gain.setValueAtTime(0.0001, noteTime);
        noteGain.gain.linearRampToValueAtTime(0.04, noteTime + 0.15);
        noteGain.gain.exponentialRampToValueAtTime(0.0001, noteTime + 3.8);

        osc.connect(noteGain);
        noteGain.connect(filter);

        osc.start(noteTime);
        osc.stop(noteTime + 4.0);
      });
    };

    // Play first chord immediately
    playChord();
    this.loopTimer = setInterval(playChord, beatInterval);

    this.activeGenerators.push(() => {
      try { filter.disconnect(); } catch (e) {}
    });
  }

  /**
   * Warm Ambient Pad:
   * Dual detuned sine/triangle waves with slow 0.08Hz LFO filter breathing.
   */
  private synthesizeWarmPad() {
    if (!this.ctx || !this.masterGain) return;
    const ctx = this.ctx;

    const padGain = ctx.createGain();
    padGain.gain.setValueAtTime(0.05, ctx.currentTime);
    padGain.connect(this.masterGain);

    const filter = ctx.createBiquadFilter();
    filter.type = 'lowpass';
    filter.frequency.setValueAtTime(450, ctx.currentTime);
    filter.connect(padGain);

    // LFO for slow breathing filter sweep (12 second period = 0.08 Hz)
    const lfo = ctx.createOscillator();
    const lfoGain = ctx.createGain();
    lfo.frequency.setValueAtTime(0.08, ctx.currentTime);
    lfoGain.gain.setValueAtTime(150, ctx.currentTime);
    lfo.connect(lfoGain);
    lfoGain.connect(filter.frequency);
    lfo.start();

    // Harmonic triad: D2, A2, F#3
    const freqs = [73.42, 110.00, 185.00];
    const oscs: OscillatorNode[] = [];

    freqs.forEach((f) => {
      const osc = ctx.createOscillator();
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(f, ctx.currentTime);
      osc.connect(filter);
      osc.start();
      oscs.push(osc);
    });

    this.activeGenerators.push(() => {
      try {
        lfo.stop();
        oscs.forEach(o => o.stop());
        padGain.disconnect();
      } catch (e) {}
    });
  }

  /**
   * Light Rainfall:
   * Pink noise filtered down to soft droplet frequencies (no thunder).
   */
  private synthesizeLightRain() {
    if (!this.ctx || !this.masterGain) return;
    const ctx = this.ctx;

    const bufferSize = ctx.sampleRate * 2;
    const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
    const data = buffer.getChannelData(0);
    let b0 = 0, b1 = 0, b2 = 0;

    // Pink noise generation
    for (let i = 0; i < bufferSize; i++) {
      const white = Math.random() * 2 - 1;
      b0 = 0.99886 * b0 + white * 0.0555179;
      b1 = 0.99332 * b1 + white * 0.0750759;
      b2 = 0.96900 * b2 + white * 0.1538520;
      data[i] = (b0 + b1 + b2) * 0.11;
    }

    const noiseSource = ctx.createBufferSource();
    noiseSource.buffer = buffer;
    noiseSource.loop = true;

    const filter = ctx.createBiquadFilter();
    filter.type = 'lowpass';
    filter.frequency.setValueAtTime(1200, ctx.currentTime);

    const rainGain = ctx.createGain();
    rainGain.gain.setValueAtTime(0.04, ctx.currentTime);

    noiseSource.connect(filter);
    filter.connect(rainGain);
    rainGain.connect(this.masterGain);

    noiseSource.start();

    this.activeGenerators.push(() => {
      try {
        noiseSource.stop();
        rainGain.disconnect();
      } catch (e) {}
    });
  }

  /**
   * Gentle Ocean Waves:
   * Periodic 8-10s cyclic swell filter simulating relaxed respiration waves.
   */
  private synthesizeOceanWaves() {
    if (!this.ctx || !this.masterGain) return;
    const ctx = this.ctx;

    const bufferSize = ctx.sampleRate * 2;
    const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) {
      data[i] = (Math.random() * 2 - 1) * 0.2;
    }

    const noiseSource = ctx.createBufferSource();
    noiseSource.buffer = buffer;
    noiseSource.loop = true;

    const filter = ctx.createBiquadFilter();
    filter.type = 'bandpass';
    filter.frequency.setValueAtTime(320, ctx.currentTime);
    filter.Q.setValueAtTime(2.5, ctx.currentTime);

    const waveGain = ctx.createGain();
    waveGain.gain.setValueAtTime(0.03, ctx.currentTime);

    // LFO for wave ebb and flow (~9 seconds per wave)
    const lfo = ctx.createOscillator();
    const lfoGain = ctx.createGain();
    lfo.frequency.setValueAtTime(0.11, ctx.currentTime);
    lfoGain.gain.setValueAtTime(200, ctx.currentTime);
    lfo.connect(lfoGain);
    lfoGain.connect(filter.frequency);

    noiseSource.connect(filter);
    filter.connect(waveGain);
    waveGain.connect(this.masterGain);

    lfo.start();
    noiseSource.start();

    this.activeGenerators.push(() => {
      try {
        lfo.stop();
        noiseSource.stop();
        waveGain.disconnect();
      } catch (e) {}
    });
  }

  /**
   * Gentle Mountain Stream:
   * High-pass modulated soothing water trickle.
   */
  private synthesizeGentleStream() {
    if (!this.ctx || !this.masterGain) return;
    const ctx = this.ctx;

    const bufferSize = ctx.sampleRate * 2;
    const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) {
      data[i] = (Math.random() * 2 - 1) * 0.15;
    }

    const noiseSource = ctx.createBufferSource();
    noiseSource.buffer = buffer;
    noiseSource.loop = true;

    const filter = ctx.createBiquadFilter();
    filter.type = 'bandpass';
    filter.frequency.setValueAtTime(800, ctx.currentTime);
    filter.Q.setValueAtTime(3.0, ctx.currentTime);

    const streamGain = ctx.createGain();
    streamGain.gain.setValueAtTime(0.03, ctx.currentTime);

    noiseSource.connect(filter);
    filter.connect(streamGain);
    streamGain.connect(this.masterGain);

    noiseSource.start();

    this.activeGenerators.push(() => {
      try {
        noiseSource.stop();
        streamGain.disconnect();
      } catch (e) {}
    });
  }

  /**
   * Quiet Forest Ambience:
   * Deep low-frequency rustle and gentle acoustic warmth.
   */
  private synthesizeQuietForest() {
    if (!this.ctx || !this.masterGain) return;
    const ctx = this.ctx;

    const osc = ctx.createOscillator();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(95, ctx.currentTime);

    const forestGain = ctx.createGain();
    forestGain.gain.setValueAtTime(0.02, ctx.currentTime);

    osc.connect(forestGain);
    forestGain.connect(this.masterGain);
    osc.start();

    this.activeGenerators.push(() => {
      try {
        osc.stop();
        forestGain.disconnect();
      } catch (e) {}
    });
  }
}

// Global Singleton for seamless coordination across components
export const audioController = typeof window !== 'undefined' ? new MindBridgeAudioEngine() : (null as any);
