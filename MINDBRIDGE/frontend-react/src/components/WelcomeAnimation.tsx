'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BreathingOrb } from './BreathingOrb';
import { MindBridgeLogo } from './MindBridgeLogo';
import { WelcomeActions } from './WelcomeActions';
import { EmergencyButton } from './EmergencyButton';
import { EmergencyModal } from './EmergencyModal';
import { AccessibilityControls } from './AccessibilityControls';
import { CalmAudioController } from './CalmAudioController';
import { SupportedLanguage } from '../lib/types';
import { TRANSLATIONS } from '../lib/translations';
import { audioController } from '../lib/audioEngine';

interface WelcomeAnimationProps {
  onStartScreening?: () => void;
  onEmergencyClick?: () => void;
  onAnimationComplete?: () => void;
  initialLanguage?: SupportedLanguage;
  className?: string;
}

export const WelcomeAnimation: React.FC<WelcomeAnimationProps> = ({
  onStartScreening,
  onEmergencyClick,
  onAnimationComplete,
  initialLanguage = 'en',
  className = '',
}) => {
  const [language, setLanguage] = useState<SupportedLanguage>(initialLanguage);
  const [reducedMotion, setReducedMotion] = useState<boolean>(false);
  const [animationStep, setAnimationStep] = useState<'orb' | 'logo' | 'text' | 'actions'>('orb');
  const [hasSkipped, setHasSkipped] = useState<boolean>(false);
  const [isEmergencyModalOpen, setIsEmergencyModalOpen] = useState<boolean>(false);
  const [soundEnabled, setSoundEnabled] = useState<boolean>(false);

  // 1. Detect prefers-reduced-motion media query
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
      setReducedMotion(mediaQuery.matches);

      const handleChange = (e: MediaQueryListEvent) => {
        setReducedMotion(e.matches);
      };
      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    }
  }, []);

  // 2. Timed Choreography (2-4 seconds total sequence)
  useEffect(() => {
    if (reducedMotion || hasSkipped) {
      // Immediate presentation for reduced motion or skipped state
      setAnimationStep('actions');
      if (onAnimationComplete) onAnimationComplete();
      return;
    }

    // Step 1 (0ms): Gradient background and breathing orb appear
    setAnimationStep('orb');

    // Step 2 (1000ms): Logo fades in smoothly (0.8 - 1.2s target)
    const tLogo = setTimeout(() => {
      setAnimationStep('logo');
    }, 1000);

    // Step 3 (1600ms): Welcome text fades in
    const tText = setTimeout(() => {
      setAnimationStep('text');
    }, 1600);

    // Step 4 (2200ms): Welcome actions appear
    const tActions = setTimeout(() => {
      setAnimationStep('actions');
      if (onAnimationComplete) onAnimationComplete();
    }, 2200);

    return () => {
      clearTimeout(tLogo);
      clearTimeout(tText);
      clearTimeout(tActions);
    };
  }, [reducedMotion, hasSkipped, onAnimationComplete]);

  const handleSkipAnimation = () => {
    setHasSkipped(true);
    setAnimationStep('actions');
    if (onAnimationComplete) onAnimationComplete();
  };

  const handleToggleReducedMotion = () => {
    setReducedMotion(prev => !prev);
  };

  const handleOpenEmergency = () => {
    setIsEmergencyModalOpen(true);
    if (onEmergencyClick) onEmergencyClick();
  };

  const handleStartScreening = () => {
    if (onStartScreening) {
      onStartScreening();
    } else {
      // Default fallback: direct to screening tab or route
      if (typeof window !== 'undefined') {
        const switchTab = (window as any).switchTab;
        if (typeof switchTab === 'function') {
          switchTab('screener');
        } else {
          window.location.hash = '#screener';
        }
      }
    }
  };

  const handleEnableCalmSound = () => {
    setSoundEnabled(true);
    if (typeof window !== 'undefined' && audioController) {
      audioController.playTrack('piano'); // Default recommended soft ambient piano
    }
  };

  const handleContinueWithoutSound = () => {
    setSoundEnabled(true); // mark chosen so banner dismisses
    if (typeof window !== 'undefined' && audioController) {
      audioController.stop();
    }
  };

  const t = TRANSLATIONS[language];
  const isLogoVisible = animationStep !== 'orb';
  const isTextVisible = animationStep === 'text' || animationStep === 'actions';
  const areActionsVisible = animationStep === 'actions';

  return (
    <main 
      className={`relative min-h-screen w-full flex flex-col items-center justify-between p-4 md:p-8 overflow-hidden select-none ${className}`}
      style={{
        // Soft calming gradient background using palette: #DCEEFF, #E9E2FF, #DFF5EC, #F8F3EA
        background: 'radial-gradient(ellipse at 50% 30%, #E9E2FF 0%, #DCEEFF 40%, #DFF5EC 75%, #F8F3EA 100%)',
      }}
      aria-label="MindBridge Calm Welcome Experience"
    >
      {/* Subtle organic light reflections */}
      <div 
        className="absolute -top-40 -left-40 w-96 h-96 rounded-full blur-3xl pointer-events-none opacity-50"
        style={{ background: '#DCEEFF' }}
        aria-hidden="true"
      />
      <div 
        className="absolute -bottom-40 -right-40 w-96 h-96 rounded-full blur-3xl pointer-events-none opacity-50"
        style={{ background: '#DFF5EC' }}
        aria-hidden="true"
      />

      {/* TOP HEADER: Accessibility Controls & Emergency Button (ALWAYS VISIBLE) */}
      <header className="w-full max-w-6xl mx-auto flex items-center justify-between z-30 pt-2 pb-4">
        {/* Left: Accessibility toolbar */}
        <AccessibilityControls
          reducedMotion={reducedMotion}
          onToggleReducedMotion={handleToggleReducedMotion}
          onSkipAnimation={handleSkipAnimation}
          canSkip={!areActionsVisible}
          language={language}
        />

        {/* Right: Emergency Help Button (Never hidden behind animation) */}
        <div className="flex items-center gap-3">
          <EmergencyButton
            onOpenEmergency={handleOpenEmergency}
            language={language}
            variant="inline"
            className="!py-2 !px-4 !text-xs !rounded-full shadow-sm"
          />
        </div>
      </header>

      {/* CENTERPIECE: Breathing Orb + Logo + Welcome Typography */}
      <div className="relative w-full max-w-4xl my-auto flex flex-col items-center justify-center text-center z-20 py-4">
        
        {/* Gentle Breathing Orb Backdrop */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-0">
          <BreathingOrb 
            reducedMotion={reducedMotion} 
            size="lg" 
          />
        </div>

        {/* Content Container (Layered above Orb) */}
        <div className="relative z-10 flex flex-col items-center">
          
          {/* 1. MindBridge Compassionate Logo */}
          <div className="mb-4">
            <AnimatePresence>
              {isLogoVisible && (
                <motion.div
                  initial={reducedMotion ? { opacity: 1 } : { opacity: 0, scale: 0.9, y: 10 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  transition={{ duration: reducedMotion ? 0 : 0.8, ease: 'easeOut' }}
                >
                  <MindBridgeLogo size="md" reducedMotion={reducedMotion} />
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* 2. Welcome Typography */}
          <AnimatePresence>
            {isTextVisible && (
              <motion.div
                initial={reducedMotion ? { opacity: 1 } : { opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: reducedMotion ? 0 : 0.7, ease: 'easeOut' }}
                className="space-y-3 px-4 max-w-2xl"
              >
                {/* Main Title */}
                <h1 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-slate-800 tracking-tight leading-tight">
                  {t.title}
                </h1>

                {/* Subtitle */}
                <p className="text-base sm:text-lg md:text-xl font-medium text-slate-700 leading-relaxed">
                  {t.subtitle}
                </p>

                {/* Supportive Message (Empowering & Non-Pressuring) */}
                <p className="text-xs sm:text-sm md:text-base text-slate-600 font-normal leading-relaxed pt-1 max-w-xl mx-auto">
                  {t.supportiveMessage}
                </p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* 3. Welcome Actions (Buttons, Language Switcher, Audio Consent) */}
          <div className="mt-8 w-full">
            <AnimatePresence>
              {areActionsVisible && (
                <WelcomeActions
                  language={language}
                  onSelectLanguage={setLanguage}
                  onStartScreening={handleStartScreening}
                  onOpenEmergency={handleOpenEmergency}
                  onEnableCalmSound={handleEnableCalmSound}
                  onContinueWithoutSound={handleContinueWithoutSound}
                  soundEnabled={soundEnabled}
                  reducedMotion={reducedMotion}
                />
              )}
            </AnimatePresence>
          </div>

        </div>
      </div>

      {/* FOOTER BAR: Audio Controller & Ethical Dignity Statement */}
      <footer className="w-full max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3 z-30 pt-4 pb-2 border-t border-slate-300/40 text-xs text-slate-500">
        <div className="flex items-center gap-2">
          <span>MindBridge Ethical AI Sanctuary</span>
          <span>•</span>
          <span>Non-Diagnostic</span>
          <span>•</span>
          <span>Confidential</span>
        </div>

        {/* Calm Audio Controller (Zero autoplay, user-driven) */}
        <CalmAudioController
          language={language}
          isEmergencyActive={isEmergencyModalOpen}
        />
      </footer>

      {/* EMERGENCY CRISIS MODAL (Works unauthenticated, stops audio) */}
      <EmergencyModal
        isOpen={isEmergencyModalOpen}
        onClose={() => setIsEmergencyModalOpen(false)}
        language={language}
      />
    </main>
  );
};
