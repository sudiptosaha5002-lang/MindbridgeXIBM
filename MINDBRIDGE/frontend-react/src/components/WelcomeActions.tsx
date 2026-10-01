'use client';

import React from 'react';
import { motion, Variants } from 'framer-motion';
import { ArrowRight, LifeBuoy, Volume2, Globe, Shield, Mic, CheckCircle2 } from 'lucide-react';
import { SupportedLanguage } from '../lib/types';
import { TRANSLATIONS } from '../lib/translations';

interface WelcomeActionsProps {
  language: SupportedLanguage;
  onSelectLanguage: (lang: SupportedLanguage) => void;
  onStartScreening: () => void;
  onOpenEmergency: () => void;
  onEnableCalmSound: () => void;
  onContinueWithoutSound: () => void;
  soundEnabled: boolean;
  reducedMotion?: boolean;
  className?: string;
}

export const WelcomeActions: React.FC<WelcomeActionsProps> = ({
  language,
  onSelectLanguage,
  onStartScreening,
  onOpenEmergency,
  onEnableCalmSound,
  onContinueWithoutSound,
  soundEnabled,
  reducedMotion = false,
  className = '',
}) => {
  const t = TRANSLATIONS[language];

  const languages: { code: SupportedLanguage; label: string; nativeName: string }[] = [
    { code: 'en', label: 'English', nativeName: 'English' },
    { code: 'bn', label: 'Bengali', nativeName: 'বাংলা' },
    { code: 'hi', label: 'Hindi', nativeName: 'हिंदी' },
  ];

  const containerVariants: Variants = {
    hidden: { opacity: 0, y: reducedMotion ? 0 : 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: reducedMotion ? 0 : 0.6,
        staggerChildren: reducedMotion ? 0 : 0.1,
      },
    },
  };

  const itemVariants: Variants = {
    hidden: { opacity: 0, y: reducedMotion ? 0 : 10 },
    visible: { opacity: 1, y: 0, transition: { duration: reducedMotion ? 0 : 0.4 } },
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className={`w-full max-w-xl mx-auto flex flex-col items-center gap-6 ${className}`}
    >
      {/* Language Selector Chips */}
      <motion.div variants={itemVariants} className="flex items-center gap-2 p-1.5 rounded-full bg-white/75 backdrop-blur-md border border-slate-200 shadow-sm">
        <Globe className="w-4 h-4 ml-2.5 text-slate-400" aria-hidden="true" />
        <span className="text-xs font-medium text-slate-500 sr-only">{t.selectLanguage}:</span>
        <div className="flex items-center gap-1">
          {languages.map((item) => (
            <button
              key={item.code}
              type="button"
              onClick={() => onSelectLanguage(item.code)}
              aria-pressed={language === item.code}
              className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all duration-200 outline-none focus:ring-2 focus:ring-indigo-400 ${
                language === item.code
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              {item.nativeName}
            </button>
          ))}
        </div>
      </motion.div>

      {/* Primary & Secondary Action Buttons */}
      <motion.div variants={itemVariants} className="w-full flex flex-col sm:flex-row items-center justify-center gap-3.5 px-4">
        
        {/* Primary: Start Screening */}
        <button
          type="button"
          onClick={onStartScreening}
          className="w-full sm:w-auto flex-1 min-w-[200px] flex items-center justify-center gap-3 px-8 py-4 rounded-2xl bg-gradient-to-r from-teal-600 via-indigo-600 to-sky-600 text-white font-semibold text-base shadow-lg shadow-indigo-200/50 hover:shadow-xl hover:scale-[1.02] active:scale-[0.98] transition-all duration-200 focus:ring-4 focus:ring-indigo-300 outline-none group"
        >
          <span>{t.startScreening}</span>
          <ArrowRight className="w-5 h-5 transition-transform group-hover:translate-x-1" aria-hidden="true" />
        </button>

        {/* Secondary: Emergency Help (Prominently styled, always available) */}
        <button
          type="button"
          onClick={onOpenEmergency}
          className="w-full sm:w-auto flex items-center justify-center gap-2.5 px-7 py-4 rounded-2xl bg-rose-50 hover:bg-rose-100 text-rose-800 border-2 border-rose-200 font-semibold text-base transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] focus:ring-4 focus:ring-rose-200 outline-none"
        >
          <LifeBuoy className="w-5 h-5 text-rose-600" aria-hidden="true" />
          <span>{t.emergencyHelp}</span>
        </button>

      </motion.div>

      {/* Optional Audio Consent Prompt */}
      {!soundEnabled && (
        <motion.div variants={itemVariants} className="flex flex-col sm:flex-row items-center gap-3 text-xs text-slate-600 bg-white/60 backdrop-blur-md px-4 py-2.5 rounded-2xl border border-slate-200/80 shadow-sm">
          <span className="font-medium text-slate-700">{t.soundPrompt}</span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onEnableCalmSound}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-teal-50 hover:bg-teal-100 text-teal-800 font-medium border border-teal-200 transition-colors focus:ring-2 focus:ring-teal-400 outline-none"
            >
              <Volume2 className="w-3.5 h-3.5 text-teal-600" />
              <span>{t.enableSound}</span>
            </button>
            <button
              type="button"
              onClick={onContinueWithoutSound}
              className="px-3 py-1.5 rounded-xl hover:bg-slate-100 text-slate-500 hover:text-slate-800 transition-colors focus:ring-2 focus:ring-slate-400 outline-none"
            >
              {t.continueWithoutSound}
            </button>
          </div>
        </motion.div>
      )}

      {/* Ethical Reassurance Pills */}
      <motion.div variants={itemVariants} className="flex flex-wrap items-center justify-center gap-2 pt-2 px-2">
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-medium text-slate-600 bg-white/50 border border-slate-200">
          <Shield className="w-3 h-3 text-emerald-600" />
          {t.ethicalNotice4}
        </span>
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-medium text-slate-600 bg-white/50 border border-slate-200">
          <Mic className="w-3 h-3 text-indigo-600" />
          {t.ethicalNotice2}
        </span>
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-medium text-slate-600 bg-white/50 border border-slate-200">
          <CheckCircle2 className="w-3 h-3 text-sky-600" />
          {t.ethicalNotice1}
        </span>
      </motion.div>

    </motion.div>
  );
};
