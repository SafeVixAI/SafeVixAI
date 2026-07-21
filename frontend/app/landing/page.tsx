'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';


import { useSmoothScroll } from './hooks/useSmoothScroll';
import { useBackendPrewarm } from './hooks/useBackendPrewarm';

import LandingNavbar from './components/LandingNavbar';
import HeroSection from './components/HeroSection';
import dynamic from 'next/dynamic';

const CrisisSection = dynamic(() => import('./components/CrisisSection'), { ssr: false });
const CommandCenter = dynamic(() => import('./components/CommandCenter'), { ssr: false });
const AIInfrastructure = dynamic(() => import('./components/AIInfrastructure'), { ssr: false });
const NationalNetwork = dynamic(() => import('./components/NationalNetwork'), { ssr: false });
const TechStack = dynamic(() => import('./components/TechStack'), { ssr: false });
import HowItWorks from './components/HowItWorks';
import CoreModules from './components/CoreModules';
import MissionSection from './components/MissionSection';
import CTASection from './components/CTASection';
import LandingFooter from './components/LandingFooter';

export default function LandingPage() {
  useSmoothScroll();
  useBackendPrewarm();
  return (
    <main className="bg-bg text-text-1 min-h-dvh overflow-x-hidden">
      <h1 className="sr-only">SafeVixAI - Road Safety Platform</h1>
      <LandingNavbar />
      <HeroSection />
      <CrisisSection />
      <HowItWorks />
      <CoreModules />
      <CommandCenter />
      <AIInfrastructure />
      <NationalNetwork />
      <TechStack />
      <MissionSection />
      <CTASection />
      <LandingFooter />
    </main>
  );
}