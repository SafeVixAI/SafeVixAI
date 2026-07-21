'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';


import { useState, useEffect, useRef, useCallback } from 'react';
import Link from 'next/link';
import { Menu, X } from 'lucide-react';
import { useGSAP } from '@gsap/react';
import { gsap } from '@/lib/gsap';

/* ────────────────────────────────────────────────────────────
   SafeVixAI Landing — Floating Glassmorphism Navbar
   ──────────────────────────────────────────────────────────── */

interface NavLink {
  label: string;
  href: string;
}

const NAVBAR_SCROLL_OFFSET = 80;

const NAV_LINKS: NavLink[] = [
  { label: 'Platform', href: '#platform' },
  { label: 'Modules', href: '#modules' },
  { label: 'Intelligence', href: '#intelligence' },
  { label: 'Mission', href: '#mission' },
];

function ShieldLogo() {
  return (
    <svg
      width="28"
      height="32"
      viewBox="0 0 28 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      className="flex-shrink-0"
    >
      {/* Shield body */}
      <path
        d="M14 1L2 6V14.5C2 22.5 7 28.5 14 31C21 28.5 26 22.5 26 14.5V6L14 1Z"
        stroke="var(--brand-light)"
        strokeWidth="1.5"
        fill="rgba(0,200,150,0.08)"
        strokeLinejoin="round"
      />
      {/* Inner glyph — AI node */}
      <circle cx="14" cy="14" r="3" fill="var(--brand-light)" opacity="0.9" />
      <circle cx="14" cy="14" r="5.5" stroke="var(--brand-light)" strokeWidth="0.8" opacity="0.4" />
      {/* Pulse lines */}
      <line x1="14" y1="8" x2="14" y2="5" stroke="var(--brand-light)" strokeWidth="0.8" opacity="0.5" />
      <line x1="14" y1="20" x2="14" y2="23" stroke="var(--brand-light)" strokeWidth="0.8" opacity="0.5" />
      <line x1="8" y1="14" x2="5" y2="14" stroke="var(--brand-light)" strokeWidth="0.8" opacity="0.5" />
      <line x1="20" y1="14" x2="23" y2="14" stroke="var(--brand-light)" strokeWidth="0.8" opacity="0.5" />
    </svg>
  );
}

export default function LandingNavbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const navRef = useRef<HTMLElement>(null);
  const mobileMenuRef = useRef<HTMLDivElement>(null);

  /* ── Scroll listener ── */
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 32);
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  /* ── Lock body scroll when mobile menu open ── */
  useEffect(() => {
    if (mobileOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [mobileOpen]);

  /* ── GSAP mount animation ── */
  useGSAP(
    () => {
      if (!navRef.current) return;
      const prefersReducedMotion = window.matchMedia(
        '(prefers-reduced-motion: reduce)'
      ).matches;
      if (prefersReducedMotion) return;

      gsap.fromTo(
        navRef.current,
        { opacity: 0, y: -16 },
        { opacity: 1, y: 0, duration: 0.7, ease: 'power3.out', delay: 0.1 }
      );
    },
    { scope: navRef }
  );

  /* ── Smooth scroll handler ── */
  const handleNavClick = useCallback(
    (e: React.MouseEvent<HTMLAnchorElement>, href: string) => {
      e.preventDefault();
      setMobileOpen(false);
      const target = document.querySelector(href);
      if (target) {
        const top =
          target.getBoundingClientRect().top + window.scrollY - NAVBAR_SCROLL_OFFSET;
        window.scrollTo({ top, behavior: 'smooth' });
      }
    },
    []
  );

  return (
    <>
      <nav
        ref={navRef}
        className={`
          fixed top-0 left-0 right-0 z-50
          navbar-glass transition-all duration-300
          ${scrolled ? 'navbar-glass-scrolled' : ''}
        `}
        role="navigation"
        aria-label="Main navigation"
      >
        <div className="landing-container flex items-center justify-between h-16">
          {/* ── Logo ── */}
          <Link
            href="/"
            className="flex items-center gap-2.5 group"
            aria-label="SafeVixAI home"
          >
            <ShieldLogo />
            <span className="font-space text-lg font-bold text-text-1 tracking-tight group-hover:text-brand-light transition-colors duration-200">
              SafeVixAI
            </span>
          </Link>

          {/* ── Center Nav (desktop) ── */}
          <div className="hidden md:flex items-center gap-8">
            {NAV_LINKS.map((link) => (
              <a
                key={link.href}
                href={link.href}
                onClick={(e) => handleNavClick(e, link.href)}
                className="
                  font-sans text-sm text-text-2
                  hover:text-text-1 transition-colors duration-200
                  relative after:absolute after:bottom-0 after:left-0 after:w-0 after:h-px
                  after:bg-brand-light after:transition-all after:duration-300
                  hover:after:w-full
                "
              >
                {link.label}
              </a>
            ))}
          </div>

          {/* ── Right actions ── */}
          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="
                hidden sm:inline-flex items-center
                bg-brand hover:bg-brand-hover text-white
                px-5 py-2.5 rounded-md text-sm font-semibold
                transition-all duration-200
                hover:shadow-brand
              "
            >
              Launch Platform
            </Link>

            {/* ── Mobile hamburger ── */}
            <button
              type="button"
              onClick={() => setMobileOpen((v) => !v)}
              className="
                md:hidden flex items-center justify-center
                w-10 h-10 rounded-md
                text-text-2 hover:text-text-1 hover:bg-white/[0.06]
                transition-colors duration-200
              "
              aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
              aria-expanded={mobileOpen}
            >
              {mobileOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </div>
      </nav>

      {/* ── Mobile slide-in overlay ── */}
      {/* Backdrop */}
      <div
        className={`
          fixed inset-0 z-40 bg-black/60 backdrop-blur-sm
          transition-opacity duration-300 md:hidden
          ${mobileOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}
        `}
        onClick={() => setMobileOpen(false)}
        aria-hidden="true"
      />

      {/* Panel */}
      <div
        ref={mobileMenuRef}
        className={`
          fixed top-0 right-0 z-50 h-dvh w-[min(320px,85vw)]
          bg-surface-1 border-l border-white/[0.07]
          transform transition-transform duration-300 ease-out md:hidden
          ${mobileOpen ? 'translate-x-0' : 'translate-x-full'}
          flex flex-col
        `}
        role="dialog"
        aria-modal="true"
        aria-label="Mobile navigation"
      >
        {/* Panel header */}
        <div className="flex items-center justify-between px-6 h-16 border-b border-white/[0.07]">
          <span className="font-space text-sm font-bold text-text-1">
            Navigation
          </span>
          <button
            type="button"
            onClick={() => setMobileOpen(false)}
            className="
              flex items-center justify-center w-9 h-9 rounded-md
              text-text-2 hover:text-text-1 hover:bg-white/[0.06]
              transition-colors duration-200
            "
            aria-label="Close menu"
          >
            <X size={18} />
          </button>
        </div>

        {/* Nav links */}
        <nav className="flex-1 flex flex-col gap-1 px-4 py-6">
          {NAV_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              onClick={(e) => handleNavClick(e, link.href)}
              className="
                flex items-center px-3 py-3 rounded-lg
                font-sans text-sm text-text-2
                hover:text-text-1 hover:bg-white/[0.04]
                transition-all duration-200
              "
            >
              {link.label}
            </a>
          ))}
        </nav>

        {/* CTA */}
        <div className="px-4 pb-8">
          <Link
            href="/login"
            className="
              flex items-center justify-center w-full
              bg-brand hover:bg-brand-hover text-white
              px-5 py-3 rounded-md text-sm font-semibold
              transition-all duration-200
            "
            onClick={() => setMobileOpen(false)}
          >
            Launch Platform
          </Link>
        </div>
      </div>
    </>
  );
}