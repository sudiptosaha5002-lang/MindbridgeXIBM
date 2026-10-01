export type SupportedLanguage = 'en' | 'bn' | 'hi';

export type SoundTrackId = 'piano' | 'pad' | 'rain' | 'waves' | 'stream' | 'forest' | 'none';

export interface SoundTrackOption {
  id: SoundTrackId;
  label: Record<SupportedLanguage, string>;
  category: 'instrumental' | 'nature' | 'none';
  bpm?: number;
  description: Record<SupportedLanguage, string>;
}

export interface WelcomeTranslations {
  title: string;
  subtitle: string;
  supportiveMessage: string;
  startScreening: string;
  emergencyHelp: string;
  selectLanguage: string;
  skipAnimation: string;
  soundPrompt: string;
  softInstrumental: string;
  natureSounds: string;
  noSound: string;
  enableSound: string;
  continueWithoutSound: string;
  soundPlaying: string;
  soundPaused: string;
  soundMuted: string;
  volumeLabel: string;
  reducedMotionActive: string;
  reducedMotionToggle: string;
  ethicalNotice1: string; // Take a break anytime
  ethicalNotice2: string; // Answer by voice or text
  ethicalNotice3: string; // Skip any question
  ethicalNotice4: string; // Your privacy matters
  ethicalNotice5: string; // Emergency help available
  ethicalNotice6: string; // Continue when you feel ready
  emergencyModalTitle: string;
  emergencyModalDesc: string;
  emergencyOption1: string; // Call emergency number
  emergencyOption2: string; // Request ambulance
  emergencyOption3: string; // Call mental-health helpline
  emergencyOption4: string; // Contact trusted person
  emergencyOption5: string; // Find nearest emergency hospital
  closeModal: string;
}
