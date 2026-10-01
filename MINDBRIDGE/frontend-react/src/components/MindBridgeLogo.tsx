'use client';

import React from 'react';
import { motion } from 'framer-motion';

interface MindBridgeLogoProps {
  reducedMotion?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const MindBridgeLogo: React.FC<MindBridgeLogoProps> = ({
  reducedMotion = false,
  size = 'md',
  className = '',
}) => {
  const sizeClasses = {
    sm: 'w-10 h-10',
    md: 'w-16 h-16',
    lg: 'w-24 h-24',
  }[size];

  const iconSizes = {
    sm: 40,
    md: 64,
    lg: 96,
  }[size];

  return (
    <div className={`relative flex items-center justify-center ${className}`} role="img" aria-label="MindBridge Logo: A compassionate bridge and heart symbol">
      {/* Subtle background glow */}
      <div 
        className="absolute inset-0 rounded-full blur-xl bg-gradient-to-tr from-sky-200 via-indigo-100 to-emerald-100 opacity-60 pointer-events-none" 
        aria-hidden="true" 
      />

      <motion.svg
        width={iconSizes}
        height={iconSizes}
        viewBox="0 0 100 100"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className={`relative z-10 ${sizeClasses}`}
        initial={reducedMotion ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: reducedMotion ? 0 : 0.8, ease: 'easeOut' }}
      >
        <defs>
          {/* Calming gradient for bridge arch */}
          <linearGradient id="mbBridgeGrad" x1="15" y1="75" x2="85" y2="75" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#0D9488" stopOpacity="0.85" />
            <stop offset="50%" stopColor="#4F46E5" stopOpacity="0.9" />
            <stop offset="100%" stopColor="#0284C7" stopOpacity="0.85" />
          </linearGradient>

          {/* Compassionate heart glow */}
          <linearGradient id="mbHeartGrad" x1="50" y1="20" x2="50" y2="55" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#F472B6" stopOpacity="0.85" />
            <stop offset="100%" stopColor="#818CF8" stopOpacity="0.9" />
          </linearGradient>

          {/* Soft base water reflection line */}
          <linearGradient id="mbWaterGrad" x1="20" y1="85" x2="80" y2="85" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#BAE6FD" stopOpacity="0" />
            <stop offset="50%" stopColor="#7DD3FC" stopOpacity="0.7" />
            <stop offset="100%" stopColor="#BAE6FD" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* Gentle Sanctuary Outer Circle */}
        <circle
          cx="50"
          cy="50"
          r="45"
          stroke="url(#mbBridgeGrad)"
          strokeWidth="2.5"
          strokeDasharray="4 2"
          className="opacity-40"
        />

        {/* Supportive Bridge Arch: Connects both banks safely */}
        <path
          d="M 22 72 C 32 46, 68 46, 78 72"
          stroke="url(#mbBridgeGrad)"
          strokeWidth="4"
          strokeLinecap="round"
        />

        {/* Bridge Suspension Rays: Symbolic of pillars of safety */}
        <line x1="38" y1="56" x2="38" y2="70" stroke="url(#mbBridgeGrad)" strokeWidth="1.8" strokeLinecap="round" opacity="0.6" />
        <line x1="50" y1="52" x2="50" y2="70" stroke="url(#mbBridgeGrad)" strokeWidth="2.0" strokeLinecap="round" opacity="0.7" />
        <line x1="62" y1="56" x2="62" y2="70" stroke="url(#mbBridgeGrad)" strokeWidth="1.8" strokeLinecap="round" opacity="0.6" />

        {/* Heart / Emergent Bloom: Symbolic of emotional recovery and human empathy */}
        <path
          d="M 50 36 C 47 28, 35 28, 35 38 C 35 46, 47 52, 50 56 C 53 52, 65 46, 65 38 C 65 28, 53 28, 50 36 Z"
          fill="url(#mbHeartGrad)"
        />

        {/* Base Water Horizon Line: Grounded stillness */}
        <path
          d="M 18 78 Q 50 82 82 78"
          stroke="url(#mbWaterGrad)"
          strokeWidth="2.5"
          strokeLinecap="round"
        />
      </motion.svg>
    </div>
  );
};
