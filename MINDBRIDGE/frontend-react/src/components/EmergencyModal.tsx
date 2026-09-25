'use client';

import React, { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { PhoneCall, Truck, HeartHandshake, UserPlus, MapPin, X, AlertTriangle } from 'lucide-react';
import { SupportedLanguage } from '../lib/types';
import { TRANSLATIONS } from '../lib/translations';
import { audioController } from '../lib/audioEngine';

interface EmergencyModalProps {
  isOpen: boolean;
  onClose: () => void;
  language: SupportedLanguage;
}

export const EmergencyModal: React.FC<EmergencyModalProps> = ({
  isOpen,
  onClose,
  language,
}) => {
  const t = TRANSLATIONS[language];
  const dialogRef = useRef<HTMLDivElement>(null);

  // Immediately stop all music when emergency view is invoked
  useEffect(() => {
    if (isOpen) {
      if (typeof window !== 'undefined' && audioController) {
        audioController.onEmergencyModeStart();
      }
      // Focus modal for keyboard accessibility
      setTimeout(() => dialogRef.current?.focus(), 50);
    }
  }, [isOpen]);

  // Handle ESC key to dismiss
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  return (
    <AnimatePresence>
      {isOpen && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm"
          role="dialog"
          aria-modal="true"
          aria-labelledby="emergency-modal-title"
          aria-describedby="emergency-modal-description"
        >
          <motion.div
            ref={dialogRef}
            tabIndex={-1}
            initial={{ opacity: 0, scale: 0.96, y: 15 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: 15 }}
            transition={{ duration: 0.25, ease: 'easeOut' }}
            className="relative w-full max-w-2xl bg-white rounded-3xl shadow-2xl border border-red-100 overflow-hidden outline-none"
          >
            {/* Urgent Red Accent Banner */}
            <div className="bg-gradient-to-r from-red-600 via-rose-600 to-red-500 text-white px-6 py-5 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-full bg-white/20 backdrop-blur-md">
                  <AlertTriangle className="w-6 h-6 text-white" aria-hidden="true" />
                </div>
                <div>
                  <h2 id="emergency-modal-title" className="text-xl font-bold tracking-tight">
                    {t.emergencyModalTitle}
                  </h2>
                  <span className="text-xs uppercase tracking-wider font-semibold text-red-100">
                    24/7 Confidential Crisis Gateway • Direct Access
                  </span>
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-2 rounded-full hover:bg-white/20 text-white/90 hover:text-white transition-colors focus:ring-2 focus:ring-white outline-none"
                aria-label={t.closeModal}
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Supportive Context */}
            <div className="p-6 md:p-8 space-y-6 max-h-[75vh] overflow-y-auto">
              <p id="emergency-modal-description" className="text-slate-700 leading-relaxed text-sm md:text-base bg-rose-50/80 p-4 rounded-2xl border border-rose-100">
                {t.emergencyModalDesc}
              </p>

              {/* Emergency Options Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                
                {/* 1. Call Emergency Services */}
                <a
                  href="tel:112"
                  className="flex items-center gap-4 p-4 rounded-2xl bg-red-50 hover:bg-red-100 text-red-900 border border-red-200 transition-all hover:scale-[1.02] focus:ring-2 focus:ring-red-500 outline-none group"
                >
                  <div className="w-12 h-12 rounded-xl bg-red-600 text-white flex items-center justify-center shrink-0 shadow-md group-hover:bg-red-700">
                    <PhoneCall className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="font-bold text-sm md:text-base leading-snug">{t.emergencyOption1}</h3>
                    <p className="text-xs text-red-700 mt-0.5">Direct link to 112 (National) / 988 (Suicide Hotline)</p>
                  </div>
                </a>

                {/* 2. Request Ambulance */}
                <a
                  href="tel:108"
                  className="flex items-center gap-4 p-4 rounded-2xl bg-amber-50 hover:bg-amber-100 text-amber-950 border border-amber-200 transition-all hover:scale-[1.02] focus:ring-2 focus:ring-amber-500 outline-none group"
                >
                  <div className="w-12 h-12 rounded-xl bg-amber-600 text-white flex items-center justify-center shrink-0 shadow-md group-hover:bg-amber-700">
                    <Truck className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="font-bold text-sm md:text-base leading-snug">{t.emergencyOption2}</h3>
                    <p className="text-xs text-amber-800 mt-0.5">Dial 108 Emergency Medical Services</p>
                  </div>
                </a>

                {/* 3. Mental Health Helpline */}
                <a
                  href="tel:14416"
                  className="flex items-center gap-4 p-4 rounded-2xl bg-indigo-50 hover:bg-indigo-100 text-indigo-950 border border-indigo-200 transition-all hover:scale-[1.02] focus:ring-2 focus:ring-indigo-500 outline-none group"
                >
                  <div className="w-12 h-12 rounded-xl bg-indigo-600 text-white flex items-center justify-center shrink-0 shadow-md group-hover:bg-indigo-700">
                    <HeartHandshake className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="font-bold text-sm md:text-base leading-snug">{t.emergencyOption3}</h3>
                    <p className="text-xs text-indigo-700 mt-0.5">Tele-MANAS (14416) / Vandrevala (9999 666 555)</p>
                  </div>
                </a>

                {/* 4. Contact Trusted Person */}
                <button
                  type="button"
                  onClick={() => {
                    const msg = encodeURIComponent("I am currently experiencing significant emotional distress and need someone to talk to or be with me right now.");
                    window.open(`sms:?body=${msg}`, '_blank');
                  }}
                  className="flex items-center gap-4 p-4 rounded-2xl bg-teal-50 hover:bg-teal-100 text-teal-950 border border-teal-200 transition-all hover:scale-[1.02] focus:ring-2 focus:ring-teal-500 outline-none group text-left"
                >
                  <div className="w-12 h-12 rounded-xl bg-teal-600 text-white flex items-center justify-center shrink-0 shadow-md group-hover:bg-teal-700">
                    <UserPlus className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="font-bold text-sm md:text-base leading-snug">{t.emergencyOption4}</h3>
                    <p className="text-xs text-teal-700 mt-0.5">Send immediate pre-composed SOS SMS to family/friend</p>
                  </div>
                </button>

                {/* 5. Nearest Emergency Hospital */}
                <a
                  href="https://www.google.com/maps/search/nearest+emergency+hospital+mental+health"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-4 p-4 rounded-2xl bg-slate-50 hover:bg-slate-100 text-slate-900 border border-slate-200 transition-all hover:scale-[1.02] focus:ring-2 focus:ring-slate-500 outline-none group md:col-span-2"
                >
                  <div className="w-12 h-12 rounded-xl bg-slate-700 text-white flex items-center justify-center shrink-0 shadow-md group-hover:bg-slate-800">
                    <MapPin className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="font-bold text-sm md:text-base leading-snug">{t.emergencyOption5}</h3>
                    <p className="text-xs text-slate-600 mt-0.5">Open interactive map of verified acute psychiatric and 24/7 trauma emergency rooms</p>
                  </div>
                </a>

              </div>

              {/* Ethical Assurance Footer */}
              <div className="pt-2 text-center border-t border-slate-100 text-xs text-slate-500">
                MindBridge never stores or exposes emergency calls. Your safety is our absolute priority.
              </div>
            </div>

            {/* Modal Bottom Bar */}
            <div className="bg-slate-50 px-6 py-4 border-t border-slate-100 flex justify-end">
              <button
                type="button"
                onClick={onClose}
                className="px-5 py-2.5 rounded-xl font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-200 transition-colors focus:ring-2 focus:ring-slate-400 outline-none"
              >
                {t.closeModal}
              </button>
            </div>

          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
