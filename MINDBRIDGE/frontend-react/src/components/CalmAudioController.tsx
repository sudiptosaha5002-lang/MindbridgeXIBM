'use client';

import React, { useState, useEffect } from 'react';
import { Volume2, VolumeX, Play, Pause, Music, Sparkles, Sliders, ChevronDown } from 'lucide-react';
import { SupportedLanguage, SoundTrackId } from '../lib/types';
import { TRANSLATIONS, SOUND_TRACK_OPTIONS } from '../lib/translations';
import { audioController, DEFAULT_VOLUME, MAX_VOLUME } from '../lib/audioEngine';

interface CalmAudioControllerProps {
  language: SupportedLanguage;
  onVoiceRecordingActive?: boolean;
  isEmergencyActive?: boolean;
  className?: string;
}

export const CalmAudioController: React.FC<CalmAudioControllerProps> = ({
  language,
  onVoiceRecordingActive = false,
  isEmergencyActive = false,
  className = '',
}) => {
  const t = TRANSLATIONS[language];
  const [selectedTrack, setSelectedTrack] = useState<SoundTrackId>('none');
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [isMuted, setIsMuted] = useState<boolean>(false);
  const [sliderValue, setSliderValue] = useState<number>(40); // 40% of 20% cap = 8% volume
  const [isMenuOpen, setIsMenuOpen] = useState<boolean>(false);

  // Sync state with audio engine
  useEffect(() => {
    if (!audioController) return;
    setIsPlaying(audioController.getIsPlaying());
    setIsMuted(audioController.getIsMuted());
    setSelectedTrack(audioController.getTrack());
  }, []);

  // Handle voice recording active changes (Microphone Ducking)
  useEffect(() => {
    if (!audioController) return;
    if (onVoiceRecordingActive) {
      audioController.onVoiceRecordingStart();
    } else {
      audioController.onVoiceRecordingEnd();
    }
  }, [onVoiceRecordingActive]);

  // Handle emergency active changes (Crisis Mode Immediate Stop)
  useEffect(() => {
    if (!audioController) return;
    if (isEmergencyActive) {
      audioController.onEmergencyModeStart();
      setIsPlaying(false);
      setSelectedTrack('none');
    }
  }, [isEmergencyActive]);

  const handleSelectTrack = (trackId: SoundTrackId) => {
    if (!audioController) return;
    if (trackId === 'none') {
      audioController.stop();
      setSelectedTrack('none');
      setIsPlaying(false);
    } else {
      audioController.playTrack(trackId);
      setSelectedTrack(trackId);
      setIsPlaying(true);
      setIsMuted(false);
    }
    setIsMenuOpen(false);
  };

  const handleTogglePlayPause = () => {
    if (!audioController) return;
    if (isPlaying) {
      audioController.pause();
      setIsPlaying(false);
    } else {
      if (selectedTrack === 'none') {
        handleSelectTrack('piano'); // Default recommended: Soft ambient piano
      } else {
        audioController.resume();
        setIsPlaying(true);
      }
    }
  };

  const handleToggleMute = () => {
    if (!audioController) return;
    const muted = audioController.toggleMute();
    setIsMuted(muted);
  };

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = Number(e.target.value);
    setSliderValue(val);
    if (audioController) {
      audioController.setVolumeFromSlider(val);
    }
  };

  const currentOption = SOUND_TRACK_OPTIONS.find(o => o.id === selectedTrack) || SOUND_TRACK_OPTIONS[6];

  return (
    <div className={`relative ${className}`}>
      {/* Floating Pill / Audio Widget Bar */}
      <div className="flex items-center gap-2 px-3 py-2 rounded-2xl bg-white/85 hover:bg-white backdrop-blur-md border border-slate-200 shadow-sm transition-all text-xs font-medium text-slate-700">
        
        {/* Track Selection Trigger */}
        <button
          type="button"
          onClick={() => setIsMenuOpen(!isMenuOpen)}
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 transition-colors focus:ring-2 focus:ring-indigo-400 outline-none"
          title="Select optional calming sound or silence"
          aria-expanded={isMenuOpen}
          aria-haspopup="true"
        >
          <Music className={`w-3.5 h-3.5 ${isPlaying ? 'text-indigo-600 animate-pulse' : 'text-slate-500'}`} />
          <span className="truncate max-w-[130px] font-semibold">{currentOption.label[language]}</span>
          <ChevronDown className={`w-3.5 h-3.5 transition-transform ${isMenuOpen ? 'rotate-180' : ''}`} />
        </button>

        {/* Play/Pause Button */}
        <button
          type="button"
          onClick={handleTogglePlayPause}
          className={`p-1.5 rounded-xl border transition-all focus:ring-2 focus:ring-indigo-400 outline-none ${
            isPlaying 
              ? 'bg-indigo-50 border-indigo-200 text-indigo-600 hover:bg-indigo-100' 
              : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
          }`}
          title={isPlaying ? "Pause music" : "Play calming music"}
          aria-label={isPlaying ? "Pause audio" : "Play audio"}
        >
          {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
        </button>

        {/* Mute Button */}
        {isPlaying && (
          <button
            type="button"
            onClick={handleToggleMute}
            className={`p-1.5 rounded-xl border transition-all focus:ring-2 focus:ring-indigo-400 outline-none ${
              isMuted 
                ? 'bg-rose-50 border-rose-200 text-rose-600' 
                : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
            }`}
            title={isMuted ? "Unmute audio" : "Mute audio"}
            aria-label={isMuted ? "Unmute sound" : "Mute sound"}
          >
            {isMuted ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
          </button>
        )}

        {/* Volume Slider (safely capped between 0% and 20%) */}
        {isPlaying && !isMuted && (
          <div className="flex items-center gap-1.5 px-1.5 py-0.5">
            <span className="text-[10px] text-slate-500 sr-only">{t.volumeLabel}</span>
            <input
              type="range"
              min="0"
              max="100"
              value={sliderValue}
              onChange={handleVolumeChange}
              className="w-16 h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-indigo-600 focus:ring-2 focus:ring-indigo-400 outline-none"
              title={`Volume: ${Math.round((sliderValue / 100) * MAX_VOLUME * 100)}% (Capped at 20% safe maximum)`}
              aria-label={t.volumeLabel}
            />
          </div>
        )}
      </div>

      {/* Dropdown Menu for Track Selection */}
      {isMenuOpen && (
        <div 
          className="absolute bottom-full mb-2 left-0 w-80 p-3 rounded-2xl bg-white shadow-xl border border-slate-200 z-50 animate-in fade-in zoom-in-95 duration-150"
          role="menu"
          aria-label="Sound Track Selection"
        >
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-100">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-800">
              <Sparkles className="w-3.5 h-3.5 text-indigo-500" />
              <span>{t.soundPrompt}</span>
            </div>
            <span className="text-[10px] bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded-full font-medium">
              Capped ≤ 20%
            </span>
          </div>

          <div className="space-y-1 max-h-60 overflow-y-auto pr-1">
            {SOUND_TRACK_OPTIONS.map((track) => {
              const isSelected = selectedTrack === track.id;
              return (
                <button
                  key={track.id}
                  type="button"
                  onClick={() => handleSelectTrack(track.id)}
                  className={`w-full text-left p-2.5 rounded-xl text-xs transition-all flex items-start justify-between gap-2 ${
                    isSelected 
                      ? 'bg-indigo-50 text-indigo-950 font-semibold border border-indigo-200' 
                      : 'hover:bg-slate-50 text-slate-700'
                  }`}
                  role="menuitem"
                >
                  <div>
                    <div className="flex items-center gap-1.5">
                      <span>{track.label[language]}</span>
                      {track.id === 'piano' && (
                        <span className="text-[9px] bg-emerald-100 text-emerald-800 px-1.5 py-0.2 rounded font-medium">
                          Recommended
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-slate-500 font-normal mt-0.5 leading-snug">
                      {track.description[language]}
                    </p>
                  </div>
                  {isSelected && (
                    <span className="w-2 h-2 rounded-full bg-indigo-600 shrink-0 mt-1" />
                  )}
                </button>
              );
            })}
          </div>

          <div className="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
            <span>Non-intrusive • Zero autoplay</span>
            <button
              type="button"
              onClick={() => handleSelectTrack('none')}
              className="text-indigo-600 hover:text-indigo-800 font-medium"
            >
              {t.noSound}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
