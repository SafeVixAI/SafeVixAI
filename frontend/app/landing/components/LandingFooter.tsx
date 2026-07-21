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
                className="text-sm text-text-3 hover:text-text-1 transition-colors block py-1"
              >
                {link.label}
              </a>
            ) : (
              <Link
                href={link.href}
                className="text-sm text-text-3 hover:text-text-1 transition-colors block py-1"
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
    <footer className="bg-surface-1 border-t border-white/[0.06]">
      <div className="landing-container py-16">
        {/* ── Top grid ── */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12">
          {/* Brand column */}
          <div>
            <span className="font-space text-xl font-bold text-text-1">
              SafeVixAI
            </span>
            <p className="text-sm text-text-3 mt-2">
              AI-Powered Road Safety Intelligence
            </p>
            <span className="text-xs font-mono text-text-3 mt-4 bg-surface-2 px-3 py-1 rounded-md inline-block">
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
          <span className="text-xs font-mono text-text-3">v2.4.0-SVA</span>
        </div>
      </div>
    </footer>
  );
}