'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import React, { memo } from 'react';

/**
 * MessageBubbleSkeleton — Shimmer placeholder for chat message bubbles
 */
const MessageBubbleSkeleton = memo(function MessageBubbleSkeleton({ isUser = false }: { isUser?: boolean }) {
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-3`}>
      <div className={`max-w-[75%] rounded-2xl p-4 space-y-2 ${isUser ? 'bg-brand/10' : 'bg-surface-2'}`}>
        <div className="h-3 w-40 skeleton rounded-full" />
        <div className="h-3 w-32 skeleton rounded-full" />
        <div className="h-3 w-24 skeleton rounded-full" />
      </div>
    </div>
  );
});

export function ChatSkeleton() {
  return (
    <div className="flex flex-col gap-2 p-4">
      <MessageBubbleSkeleton isUser={false} />
      <MessageBubbleSkeleton isUser={true} />
      <MessageBubbleSkeleton isUser={false} />
    </div>
  );
}

export default MessageBubbleSkeleton;