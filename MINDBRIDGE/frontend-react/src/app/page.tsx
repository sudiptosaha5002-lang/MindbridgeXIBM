'use client';

import React, { useState } from 'react';
import { WelcomeAnimation } from '../components/WelcomeAnimation';
import { EmergencyButton } from '../components/EmergencyButton';
import { EmergencyModal } from '../components/EmergencyModal';
import { CalmAudioController } from '../components/CalmAudioController';
import { SupportedLanguage } from '../lib/types';
import { TRANSLATIONS } from '../lib/translations';
import { ShieldCheck, Heart, ArrowLeft, Mic, Send, RefreshCw, Info } from 'lucide-react';

import { TWENTY_QUESTIONS } from '../lib/twentyQuestions';

export default function MindBridgeHomePage() {
  const [currentScreen, setCurrentScreen] = useState<'welcome' | 'screening'>('welcome');
  const [language, setLanguage] = useState<SupportedLanguage>('en');
  const [isEmergencyModalOpen, setIsEmergencyModalOpen] = useState<boolean>(false);
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState<number>(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [currentAnswer, setCurrentAnswer] = useState<string>('');

  const t = TRANSLATIONS[language];
  const currentQ = TWENTY_QUESTIONS[currentQuestionIndex] || TWENTY_QUESTIONS[0];

  const handleStartScreening = () => {
    setCurrentQuestionIndex(0);
    setCurrentAnswer(answers[1] || '');
    setCurrentScreen('screening');
  };

  const handleNextInquiry = () => {
    if (currentAnswer.trim()) {
      setAnswers(prev => ({ ...prev, [currentQ.id]: currentAnswer.trim() }));
    }
    if (currentQuestionIndex < TWENTY_QUESTIONS.length - 1) {
      const nextIdx = currentQuestionIndex + 1;
      setCurrentQuestionIndex(nextIdx);
      setCurrentAnswer(answers[TWENTY_QUESTIONS[nextIdx].id] || '');
    } else {
      alert('20-Question Reflections completed! Switch to the MindBridge main web application at http://127.0.0.1:5000 for your full dynamic mental state analysis.');
    }
  };

  const handlePrevInquiry = () => {
    if (currentQuestionIndex > 0) {
      const prevIdx = currentQuestionIndex - 1;
      setCurrentQuestionIndex(prevIdx);
      setCurrentAnswer(answers[TWENTY_QUESTIONS[prevIdx].id] || '');
    }
  };

  const handleBackToWelcome = () => {
    setCurrentScreen('welcome');
  };

  const toggleMockRecording = () => {
    setIsRecording(prev => !prev);
  };

  return (
    <div className="min-h-screen w-full relative bg-[#F8F3EA]">
      {currentScreen === 'welcome' ? (
        <WelcomeAnimation
          initialLanguage={language}
          onStartScreening={handleStartScreening}
          onEmergencyClick={() => setIsEmergencyModalOpen(true)}
        />
      ) : (
        /* Seamless Screening Demonstration Screen (Grounded in Ethical Principles) */
        <main className="min-h-screen w-full flex flex-col justify-between p-4 md:p-8 bg-gradient-to-b from-[#DCEEFF]/40 via-white to-[#DFF5EC]/30">
          
          {/* Header */}
          <header className="w-full max-w-4xl mx-auto flex items-center justify-between pb-6 border-b border-slate-200">
            <button
              onClick={handleBackToWelcome}
              className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 transition-colors text-sm font-medium shadow-sm focus:ring-2 focus:ring-indigo-400 outline-none"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Welcome</span>
            </button>

            <div className="flex items-center gap-3">
              <span className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 text-emerald-800 text-xs font-semibold border border-emerald-200">
                <ShieldCheck className="w-3.5 h-3.5" />
                Non-Diagnostic Research Screener
              </span>
              <EmergencyButton
                variant="inline"
                language={language}
                onOpenEmergency={() => setIsEmergencyModalOpen(true)}
                className="!py-2 !px-4 !text-xs !rounded-full shadow-sm"
              />
            </div>
          </header>

          {/* Screening Interaction Area */}
          <section className="w-full max-w-2xl mx-auto my-8 bg-white/90 backdrop-blur-md rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-calm-card">
            
            {/* Non-Diagnostic Disclaimer Banner */}
            <div className="flex items-start gap-3 p-3.5 rounded-2xl bg-sky-50/70 border border-sky-100 text-xs text-sky-900 mb-6">
              <Info className="w-4 h-4 text-sky-600 shrink-0 mt-0.5" />
              <p>
                <strong>Ethical Guarantee:</strong> Take your time. You can skip this inquiry, take a pause at any moment, or switch between speaking and typing.
              </p>
            </div>

            {/* Question Card */}
            <div className="space-y-4">
              <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
                <span>Inquiry {currentQuestionIndex + 1} of 20 • Dynamic Psychological Screening</span>
                <span className="text-sky-700 bg-sky-50 px-2 py-0.5 rounded-md font-semibold">{Math.round(((currentQuestionIndex + 1) / 20) * 100)}% Completed</span>
              </div>

              <h2 className="text-xl sm:text-2xl font-bold text-slate-800 leading-relaxed">
                {currentQ.question}
              </h2>
              <p className="text-xs text-slate-500">{currentQ.hint}</p>

              {/* Dual Input: Voice or Text */}
              <div className="pt-4 space-y-4">
                
                {/* Voice Input with Simulated Audio Ducking */}
                <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <button
                      type="button"
                      onClick={toggleMockRecording}
                      className={`w-12 h-12 rounded-full flex items-center justify-center transition-all ${
                        isRecording 
                          ? 'bg-rose-600 text-white animate-pulse shadow-lg shadow-rose-200' 
                          : 'bg-indigo-600 text-white hover:bg-indigo-700 shadow-md'
                      }`}
                      aria-label={isRecording ? "Stop voice reflection" : "Speak your response"}
                    >
                      <Mic className="w-6 h-6" />
                    </button>
                    <div>
                      <h3 className="font-semibold text-sm text-slate-800">
                        {isRecording ? "Listening softly... (Audio ducked)" : "Speak your reflection (Optional)"}
                      </h3>
                      <p className="text-xs text-slate-500">
                        {isRecording ? "Calm background audio is paused automatically." : "You may speak naturally in your own cadence."}
                      </p>
                    </div>
                  </div>
                  {isRecording && (
                    <span className="text-xs font-semibold text-rose-600 bg-rose-50 px-3 py-1 rounded-full border border-rose-200">
                      Recording Active
                    </span>
                  )}
                </div>

                {/* Text Input */}
                <div className="relative">
                  <textarea
                    rows={3}
                    value={currentAnswer}
                    onChange={(e) => setCurrentAnswer(e.target.value)}
                    placeholder="Or express your thoughts in writing at your own pace..."
                    className="w-full p-4 rounded-2xl bg-slate-50 border border-slate-200 text-slate-800 text-sm focus:ring-2 focus:ring-indigo-400 focus:bg-white outline-none transition-all resize-none"
                  />
                  <div className="flex items-center justify-between pt-2">
                    <button
                      type="button"
                      disabled={currentQuestionIndex === 0}
                      onClick={handlePrevInquiry}
                      className="px-3.5 py-1.5 rounded-xl border border-slate-300 text-slate-600 text-xs font-medium hover:bg-slate-100 disabled:opacity-40 transition-colors"
                    >
                      Previous
                    </button>
                    <button
                      type="button"
                      onClick={handleNextInquiry}
                      className="px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-700 shadow transition-colors flex items-center gap-1.5"
                    >
                      <span>{currentQuestionIndex === 19 ? 'Complete Reflections' : 'Next Inquiry'}</span>
                      <Send className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

              </div>

            </div>

          </section>

          {/* Footer Controls */}
          <footer className="w-full max-w-4xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-slate-200 text-xs text-slate-500">
            <div className="flex items-center gap-2">
              <Heart className="w-4 h-4 text-rose-500" />
              <span>You are safe. Professional, verified assistance is always accessible.</span>
            </div>
            <CalmAudioController
              language={language}
              onVoiceRecordingActive={isRecording}
              isEmergencyActive={isEmergencyModalOpen}
            />
          </footer>

          <EmergencyModal
            isOpen={isEmergencyModalOpen}
            onClose={() => setIsEmergencyModalOpen(false)}
            language={language}
          />
        </main>
      )}
    </div>
  );
}
