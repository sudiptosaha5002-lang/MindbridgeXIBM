'use client';

import React from 'react';
import { motion, Variants } from 'framer-motion';

interface BreathingOrbProps {
  reducedMotion?: boolean;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const BreathingOrb: React.FC<BreathingOrbProps> = ({
  reducedMotion = false,
  className = '',
  size = 'md',
}) => {
  const dimensionClass = {
    sm: 'w-48 h-48 md:w-56 md:h-56',
    md: 'w-72 h-72 md:w-88 md:h-88 lg:w-96 lg:h-96',
    lg: 'w-80 h-80 md:w-96 md:h-96 lg:w-[440px] lg:h-[440px]',
  }[size];

  // Framer Motion variant for gentle parasympathetic breathing (4-6s cycle)
  const breathingVariants: Variants = {
    animate: {
      scale: [0.95, 1.05, 0.95],
      opacity: [0.72, 0.98, 0.72],
      transition: {
        duration: 5.2, // ~5.2 seconds full respiratory cycle
        ease: 'easeInOut',
        repeat: Infinity,
      },
    },
    static: {
      scale: 1.0,
      opacity: 0.85,
      transition: {
        duration: 0,
      },
    },
  };

  // Subtle outer aura breathing
  const auraVariants: Variants = {
    animate: {
      scale: [0.92, 1.10, 0.92],
      opacity: [0.35, 0.65, 0.35],
      transition: {
        duration: 5.2,
        ease: 'easeInOut',
        repeat: Infinity,
      },
    },
    static: {
      scale: 1.0,
      opacity: 0.45,
      transition: {
        duration: 0,
      },
    },
  };

  return (
    <div 
      className={`relative flex items-center justify-center pointer-events-none select-none ${className}`}
      aria-hidden="true"
    >
      {/* Layer 1: Ambient Outer Glow Aura (Soft Mint & Lavender) */}
      <motion.div
        variants={auraVariants}
        animate={reducedMotion ? 'static' : 'animate'}
        className={`absolute rounded-full blur-3xl ${dimensionClass}`}
        style={{
          background: 'radial-gradient(circle, rgba(223, 245, 236, 0.7) 0%, rgba(233, 226, 255, 0.5) 45%, rgba(220, 238, 255, 0) 75%)',
        }}
      />

      {/* Layer 2: Intermediate Soft Pastel Core (Lavender & Light Blue) */}
      <motion.div
        variants={breathingVariants}
        animate={reducedMotion ? 'static' : 'animate'}
        className={`absolute rounded-full blur-xl ${dimensionClass}`}
        style={{
          background: 'radial-gradient(circle, rgba(220, 238, 255, 0.85) 15%, rgba(233, 226, 255, 0.75) 50%, rgba(248, 243, 234, 0.4) 80%)',
        }}
      />

      {/* Layer 3: Organic Soft Sphere Body */}
      <motion.div
        variants={breathingVariants}
        animate={reducedMotion ? 'static' : 'animate'}
        className={`relative rounded-full shadow-soft-glow border border-white/50 backdrop-blur-md ${dimensionClass}`}
        style={{
          background: 'radial-gradient(circle at 35% 35%, rgba(255, 255, 255, 0.85) 0%, rgba(220, 238, 255, 0.65) 40%, rgba(233, 226, 255, 0.45) 80%, rgba(223, 245, 236, 0.3) 100%)',
        }}
      >
        {/* Soft highlight reflection */}
        <div 
          className="absolute top-6 left-10 w-20 h-10 rounded-full blur-md opacity-70 transform -rotate-12"
          style={{ background: 'rgba(255, 255, 255, 0.8)' }}
        />
      </motion.div>
    </div>
  );
};
