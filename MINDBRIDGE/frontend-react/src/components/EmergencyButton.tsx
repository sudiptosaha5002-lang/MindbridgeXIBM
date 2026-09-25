'use client';

import React from 'react';
import { AlertCircle, LifeBuoy } from 'lucide-react';
import { SupportedLanguage } from '../lib/types';
import { TRANSLATIONS } from '../lib/translations';

interface EmergencyButtonProps {
  onOpenEmergency: () => void;
  language: SupportedLanguage;
  variant?: 'floating' | 'inline';
  className?: string;
}

export const EmergencyButton: React.FC<EmergencyButtonProps> = ({
  onOpenEmergency,
  language,
  variant = 'floating',
  className = '',
}) => {
  const t = TRANSLATIONS[language];

  if (variant === 'floating') {
    return (
      <aside 
        aria-label="Immediate Emergency Crisis Assistance"
        className={`fixed top-4 right-4 z-40 ${className}`}
      >
        <button
          type="button"
          onClick={onOpenEmergency}
          className="flex items-center gap-2 px-4 py-2.5 rounded-full bg-rose-600/90 hover:bg-rose-700 text-white font-medium text-xs md:text-sm tracking-wide shadow-lg hover:shadow-xl backdrop-blur-md transition-all duration-200 transform hover:scale-105 active:scale-95 focus:ring-2 focus:ring-rose-400 focus:ring-offset-2 outline-none border border-rose-400/40"
          title="Immediate Emergency Hotline & Crisis Assistance (Always Accessible)"
        >
          <LifeBuoy className="w-4 h-4 text-white animate-pulse" aria-hidden="true" />
          <span>{t.emergencyHelp}</span>
          <span className="w-2 h-2 rounded-full bg-white/90 shrink-0" />
        </button>
      </aside>
    );
  }

  return (
    <button
      type="button"
      onClick={onOpenEmergency}
      className={`flex items-center justify-center gap-2.5 px-6 py-3.5 rounded-2xl bg-rose-50 hover:bg-rose-100 text-rose-800 border border-rose-200 font-semibold text-sm md:text-base transition-all duration-200 hover:shadow-md active:scale-95 focus:ring-2 focus:ring-rose-400 focus:ring-offset-1 outline-none ${className}`}
    >
      <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" aria-hidden="true" />
      <span>{t.emergencyHelp}</span>
    </button>
  );
};
