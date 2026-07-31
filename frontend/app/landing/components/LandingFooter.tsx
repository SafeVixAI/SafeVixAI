'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';


import Link from 'next/link';

/* ── Footer link data ── */
interface FooterLink {
  label: string;
  href: string;
  external?: boolean;
}

const PLATFORM_LINKS: FooterLink[] = [
  { label: 'Dashboard', href: '/' },
  { label: 'Emergency SOS', href: '/sos' },
  { label: 'Challan Calculator', href: '/challan' },
  { label: 'Hazard Reports', href: '/report' },
];

const RESOURCE_LINKS: FooterLink[] = [
  { label: 'Documentation', href: '#' },
  {
    label: 'GitHub',
    href: 'https://github.com/SafeVixAI/SafeVixAI',
    external: true,
  },
  {
    label: 'Dataset Hub',
    href: 'https://huggingface.co/datasets/SafeVixAI/SafeVixAI-Dataset-Hub',
    external: true,
  },
  { label: 'API Reference', href: '#' },
];

const LEGAL_LINKS: FooterLink[] = [
  { label: 'Privacy Policy', href: '/privacy' },
  { label: 'Terms of Service', href: '/terms' },
];

/* ── Link Column ── */
function FooterColumn({
  title,
  links,
}: {
  title: string;
  links: FooterLink[];
}) {
  return (
    <div>
      <h4 className="text-xs font-semibold uppercase tracking-wider text-text-2 mb-4">
        {title}
      </h4>
      <ul className="space-y-0.5">
        {links.map((link) => (
          <li key={link.label}>
            {link.external ? (
              <a
                href={link.href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-text-3 hover:text-brand-light transition-colors duration-200 block py-1 hover:translate-x-0.5 transform"
              >
                {link.label}
              </a>
            ) : (
              <Link
                href={link.href}
                className="text-sm text-text-3 hover:text-brand-light transition-colors duration-200 block py-1 hover:translate-x-0.5 transform"
              >
                {link.label}
              </Link>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

/* ── Main Component ── */
export default function LandingFooter() {
  return (
    <footer className="bg-surface-1 border-t border-white/[0.06] relative overflow-hidden">
      {/* ── Subtle top glow ── */}
      <div
        className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[1px] pointer-events-none"
        style={{
          background: 'linear-gradient(90deg, transparent, rgba(0,200,150,0.3), transparent)',
        }}
        aria-hidden="true"
      />

      <div className="landing-container py-16">
        {/* ── Top grid ── */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12">
          {/* Brand column */}
          <div>
            <span className="font-space text-xl font-bold text-text-1 inline-flex items-center gap-2">
              {/* Mini shield */}
              <svg
                width="20"
                height="23"
                viewBox="0 0 28 32"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                aria-hidden="true"
                className="shield-glow"
              >
                <path
                  d="M14 1L2 6V14.5C2 22.5 7 28.5 14 31C21 28.5 26 22.5 26 14.5V6L14 1Z"
                  stroke="#00C896"
                  strokeWidth="1.5"
                  fill="rgba(0,200,150,0.08)"
                  strokeLinejoin="round"
                />
                <circle cx="14" cy="14" r="2.5" fill="#00C896" opacity="0.8" />
              </svg>
              SafeVixAI
            </span>
            <p className="text-sm text-text-3 mt-2">
              AI-Powered Road Safety Intelligence
            </p>
            <span className="text-xs font-mono text-text-3 mt-4 bg-surface-2 px-3 py-1 rounded-md inline-block border border-white/[0.04] shimmer-on-hover">
              IIT Madras Hackathon 2026
            </span>
          </div>

          {/* Platform */}
          <FooterColumn title="Platform" links={PLATFORM_LINKS} />

          {/* Resources */}
          <FooterColumn title="Resources" links={RESOURCE_LINKS} />

          {/* Legal */}
          <FooterColumn title="Legal" links={LEGAL_LINKS} />
        </div>

        {/* ── Bottom bar ── */}
        <div className="border-t border-white/[0.06] mt-12 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
          <span className="text-xs text-text-3">
            © 2026 SafeVixAI. Built for India.
          </span>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <span className="relative flex h-1.5 w-1.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-light opacity-75" />
                <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-brand-light" />
              </span>
              <span className="text-[10px] font-mono text-brand-light">
                All Systems Operational
              </span>
            </div>
            <span className="text-xs font-mono text-text-3">v2.4.0-SVA</span>
          </div>
        </div>
      </div>
    </footer>
  );
}