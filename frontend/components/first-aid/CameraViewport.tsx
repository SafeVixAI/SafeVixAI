// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

'use client';

import { useEffect, useRef, useState } from 'react';
import { CameraOff } from 'lucide-react';
import { logClientError } from '@/lib/client-logger';

interface CameraViewportProps {
  onError: (_err: string | null) => void;
}

export default function CameraViewport({ onError }: CameraViewportProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function startCamera() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'environment' },
          audio: false,
        });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
        onError(null);
      } catch (err) {
        logClientError('Camera access denied:', err);
        setError('Camera Access Denied');
        onError('Camera Access Denied');
      }
    }
    startCamera();
    const currentVideo = videoRef.current;
    return () => {
      if (currentVideo?.srcObject) {
        (currentVideo.srcObject as MediaStream).getTracks().forEach((track) => track.stop());
      }
    };
  }, [onError]);

  if (error)
    return (
      <div className="absolute inset-0 flex flex-col items-center justify-center bg-bg/40 backdrop-blur-sm text-text-3 font-bold uppercase tracking-widest text-[10px] px-12 text-center gap-3">
        <div className="p-3 rounded-full bg-surface-2/50 border border-white/5">
          <CameraOff size={24} className="text-text-3" />
        </div>
        <span>{error} — Enable permissions in settings to activate AI diagnostics</span>
      </div>
    );

  return (
    <div className="absolute inset-0 overflow-hidden bg-black">
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className="absolute inset-0 w-full h-full object-cover grayscale opacity-40 mix-blend-screen"
      />
      <div className="absolute inset-0 border-[1px] border-white/10 pointer-events-none"></div>
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-32 h-32 border border-brand/20 rounded-full animate-pulse"></div>
      <div className="absolute top-4 left-4 flex items-center gap-2">
        <div className="w-1.5 h-1.5 rounded-full bg-brand-light animate-pulse" />
        <span className="text-[9px] font-mono text-brand-light tracking-widest uppercase">Sentinel-X Active</span>
      </div>
    </div>
  );
}
