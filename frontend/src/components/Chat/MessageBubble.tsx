import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Copy, Check, ChevronDown, FileText } from 'lucide-react';
import type { ChatUILevelMessage } from '../../hooks/useChat';

interface MessageBubbleProps {
  message: ChatUILevelMessage;
  index: number;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message, index }) => {
  const isUser = message.role === 'user';
  const [copied, setCopied] = useState(false);
  const [expandedCitation, setExpandedCitation] = useState<number | null>(null);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
      className={`group flex w-full gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      {/* AI Avatar */}
      {!isUser && (
        <div className="h-8 w-8 rounded-lg bg-accent-gradient flex items-center justify-center shrink-0 shadow-glow-sm mt-0.5">
          <svg className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
          </svg>
        </div>
      )}

      {/* Message content */}
      <div className={`flex flex-col gap-1.5 max-w-[75%] min-w-0 ${isUser ? 'items-end' : 'items-start'}`}>
        {/* Bubble */}
        <div
          className={`relative px-4 py-3 rounded-2xl text-[14px] leading-relaxed ${
            isUser
              ? 'bg-accent-600 text-white rounded-br-md shadow-glow-sm'
              : 'bg-surface-850 border border-surface-800/60 text-surface-200 rounded-bl-md'
          }`}
        >
          {/* Message text */}
          <p className="whitespace-pre-wrap break-words">{message.content}</p>

          {/* Copy button — assistant only */}
          {!isUser && (
            <button
              onClick={handleCopy}
              className="absolute -bottom-3 right-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 p-1.5 rounded-md bg-surface-800 border border-surface-700 hover:border-surface-600 shadow-card cursor-pointer"
              title="Copy response"
            >
              {copied ? (
                <Check className="h-3 w-3 text-emerald-400" />
              ) : (
                <Copy className="h-3 w-3 text-surface-400" />
              )}
            </button>
          )}
        </div>

        {/* Citation cards — Perplexity style */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="w-full mt-2 space-y-1.5">
            <span className="text-2xs font-semibold text-surface-500 uppercase tracking-wider px-1">
              Sources
            </span>

            <div className="flex gap-2 overflow-x-auto scrollbar-none pb-1">
              {message.sources.map((source, idx) => {
                const isExpanded = expandedCitation === idx;
                return (
                  <motion.button
                    key={idx}
                    onClick={() => setExpandedCitation(isExpanded ? null : idx)}
                    className={`group/cite shrink-0 flex items-start gap-2.5 px-3 py-2.5 rounded-xl border transition-all duration-200 text-left cursor-pointer
                      ${isExpanded
                        ? 'bg-accent-500/10 border-accent-500/25 shadow-glow-sm'
                        : 'bg-surface-900/60 border-surface-800/60 hover:border-surface-700 hover:bg-surface-800/40'
                      }
                    `}
                    whileTap={{ scale: 0.98 }}
                  >
                    <div className={`flex items-center justify-center h-6 w-6 rounded-md shrink-0 text-xs font-bold ${
                      isExpanded ? 'bg-accent-500/20 text-accent-400' : 'bg-surface-800 text-surface-400'
                    }`}>
                      {idx + 1}
                    </div>
                    <div className="min-w-0">
                      <p className={`text-xs font-medium truncate max-w-[160px] ${
                        isExpanded ? 'text-accent-300' : 'text-surface-300'
                      }`}>
                        {source.source}
                      </p>
                      {source.page && (
                        <p className="text-2xs text-surface-500 mt-0.5">
                          Page {source.page}
                        </p>
                      )}
                    </div>
                    <ChevronDown className={`h-3 w-3 text-surface-500 shrink-0 mt-1 transition-transform duration-200 ${
                      isExpanded ? 'rotate-180' : ''
                    }`} />
                  </motion.button>
                );
              })}
            </div>

            {/* Expanded citation snippet */}
            <AnimatePresence>
              {expandedCitation !== null && message.sources[expandedCitation] && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.2 }}
                  className="overflow-hidden"
                >
                  <div className="px-4 py-3 rounded-xl bg-surface-900/80 border border-surface-800/60 text-xs text-surface-400 leading-relaxed mt-1">
                    <div className="flex items-center gap-2 mb-2">
                      <FileText className="h-3.5 w-3.5 text-accent-400" />
                      <span className="font-semibold text-surface-300">
                        {message.sources[expandedCitation].source}
                      </span>
                    </div>
                    <p className="italic text-surface-400 line-clamp-3">
                      &ldquo;{message.sources[expandedCitation].snippet}&rdquo;
                    </p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}

        {/* Timestamp */}
        <span className="text-2xs text-surface-600 px-1 font-medium">
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>

      {/* User Avatar */}
      {isUser && (
        <div className="h-8 w-8 rounded-lg bg-surface-800 border border-surface-700 flex items-center justify-center shrink-0 text-xs font-bold text-surface-400 mt-0.5">
          U
        </div>
      )}
    </motion.div>
  );
};
