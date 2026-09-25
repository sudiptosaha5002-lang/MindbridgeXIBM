'use client';

import React from 'react';
import { Eye, FastForward, Volume2, VolumeX, Pause, Play, Sparkles } from 'lucide-react';
import { SupportedLanguage } from '../lib/types';
import { TRANSLATIONS } from '../lib/translations';

interface AccessibilityControlsProps {
  reducedMotion: boolean;
  onToggleReducedMotion: () => void;
  onSkipAnimation?: () => void;
  canSkip?: boolean;
  language: SupportedLanguage;
  isAudioPlaying?: boolean;
  isAudioMuted?: boolean;
  onToggleAudioPlay?: () => void;
  onToggleAudioMute?: () => void;
  className?: string;
}

export const AccessibilityControls: React.FC<AccessibilityControlsProps> = ({
  reducedMotion,
  onToggleReducedMotion,
  onSkipAnimation,
  canSkip = true,
  language,
  isAudioPlaying = false,
  isAudioMuted = false,
  onToggleAudioPlay,
  onToggleAudioMute,
  className = '',
}) => {
  const t = TRANSLATIONS[language];

  return (
    <nav 
      aria-label="Accessibility & Animation Controls"
      className={`flex items-center gap-2 flex-wrap ${className}`}
    >
      {/* Skip Animation Button (Keyboard-accessible & prominent) */}
      {canSkip && onSkipAnimation && (
        <button
          type="button"
          onClick={onSkipAnimation}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium text-slate-700 bg-white/80 hover:bg-white border border-slate-200 shadow-sm hover:shadow transition-all focus:ring-2 focus:ring-indigo-400 outline-none active:scale-95"
          title="Skip opening animation and proceed directly to options"
        >
          <FastForward className="w-3.5 h-3.5 text-slate-600" aria-hidden="true" />
          <span>{t.skipAnimation}</span>
        </button>
      )}

      {/* Reduced Motion Toggle Button */}
      <button
        type="button"
        onClick={onToggleReducedMotion}
        aria-pressed={reducedMotion}
        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border shadow-sm transition-all focus:ring-2 focus:ring-indigo-400 outline-none active:scale-95 ${
          reducedMotion 
            ? 'bg-indigo-50 text-indigo-800 border-indigo-300' 
            : 'bg-white/80 hover:bg-white text-slate-700 border-slate-200'
        }`}
        title={reducedMotion ? t.reducedMotionActive : t.reducedMotionToggle}
      >
        <Eye className={`w-3.5 h-3.5 ${reducedMotion ? 'text-indigo-600' : 'text-slate-500'}`} aria-hidden="true" />
        <span>{reducedMotion ? t.reducedMotionActive : t.reducedMotionToggle}</span>
      </button>

      {/* Optional Audio Controls (when audio is active) */}
      {isAudioPlaying && onToggleAudioPlay && (
        <button
          type="button"
          onClick={onToggleAudioPlay}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium bg-white/80 hover:bg-white text-slate-700 border border-slate-200 shadow-sm transition-all focus:ring-2 focus:ring-indigo-400 outline-none active:scale-95"
          title={isAudioPlaying ? t.soundPlaying : t.soundPaused}
          aria-label={isAudioPlaying ? "Pause calm background sound" : "Resume calm background sound"}
        >
          {isAudioPlaying ? (
            <Pause className="w-3.5 h-3.5 text-indigo-600" aria-hidden="true" />
          ) : (
            <Play className="w-3.5 h-3.5 text-slate-600" aria-hidden="true" />
          )}
          <span>{isAudioPlaying ? "Pause Audio" : "Play Audio"}</span>
        </button>
      )}

      {isAudioPlaying && onToggleAudioMute && (
        <button
          type="button"
          onClick={onToggleAudioMute}
          aria-pressed={isAudioMuted}
          className={`p-1.5 rounded-full text-xs font-medium border shadow-sm transition-all focus:ring-2 focus:ring-indigo-400 outline-none active:scale-95 ${
            isAudioMuted
              ? 'bg-amber-50 text-amber-800 border-amber-300'
              : 'bg-white/80 hover:bg-white text-slate-700 border-slate-200'
          }`}
          title={isAudioMuted ? t.soundMuted : "Mute background audio"}
          aria-label={isAudioMuted ? "Unmute background sound" : "Mute background sound"}
        >
          {isAudioMuted ? (
            <VolumeX className="w-4 h-4 text-amber-600" aria-hidden="true" />
          ) : (
            <Volume2 className="w-4 h-4 text-slate-600" aria-hidden="true" />
          )}
        </button>
      )}
    </nav>
  );
};
