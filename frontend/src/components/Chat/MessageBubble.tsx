import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Copy, Check, ChevronDown, FileText, BookOpen, Quote, Database } from 'lucide-react';
import type { ChatUILevelMessage } from '../../hooks/useChat';
import { Markdown } from '../Common/Markdown';

interface MessageBubbleProps {
  message: ChatUILevelMessage;
  index: number;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message, index }) => {
  const isUser = message.role === 'user';
  const [copied, setCopied] = useState(false);
  const [expandedCitations, setExpandedCitations] = useState<Record<number, boolean>>({});

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const toggleCitation = (idx: number) => {
    setExpandedCitations((prev) => ({
      ...prev,
      [idx]: !prev[idx],
    }));
  };

  const getRelevanceBadgeStyles = (score: number) => {
    const pct = score <= 1 ? score * 100 : score;
    if (pct >= 80) {
      return 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20';
    } else if (pct >= 60) {
      return 'bg-blue-500/10 text-blue-400 border border-blue-500/20';
    } else if (pct >= 40) {
      return 'bg-amber-500/15 text-amber-400 border border-amber-550/20';
    } else {
      return 'bg-red-500/10 text-red-400 border border-red-500/20';
    }
  };

  const formatScore = (score: number) => {
    const pct = score <= 1 ? score * 100 : score;
    return `${pct.toFixed(1)}%`;
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
      <div className={`flex flex-col gap-1.5 max-w-[85%] min-w-0 ${isUser ? 'items-end' : 'items-start'}`}>
        {/* Bubble */}
        <div
          className={`relative px-5 py-4 rounded-2xl leading-relaxed w-full transition-all duration-200 ${
            isUser
              ? 'bg-accent-600 text-white rounded-br-md shadow-glow-sm text-[14px]'
              : 'bg-surface-900/40 border border-surface-800/80 text-surface-200 rounded-bl-md shadow-card space-y-4'
          }`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap break-words">{message.content}</p>
          ) : (
            <div className="space-y-4">
              {/* Message text with Markdown parser */}
              <Markdown content={message.content} />

              {/* Copy button — assistant only */}
              <button
                onClick={handleCopy}
                className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity duration-200 p-1.5 rounded-md bg-surface-800 border border-surface-700 hover:border-surface-600 shadow-card cursor-pointer"
                title="Copy response"
              >
                {copied ? (
                  <Check className="h-3 w-3 text-emerald-400" />
                ) : (
                  <Copy className="h-3 w-3 text-surface-400" />
                )}
              </button>

              {/* Sources Section */}
              {message.sources && message.sources.length > 0 && (
                <div className="pt-3 border-t border-surface-800/60 space-y-2">
                  <div className="flex items-center gap-1.5 text-2xs font-semibold text-surface-400 uppercase tracking-wider">
                    <BookOpen className="h-3.5 w-3.5 text-cyan-400" />
                    <span>Sources</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {message.sources.map((src, idx) => (
                      <div
                        key={idx}
                        className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-surface-950/60 border border-surface-850 text-xs text-surface-300 font-medium"
                      >
                        <FileText className="h-3.5 w-3.5 text-surface-500 shrink-0" />
                        <span className="truncate max-w-[150px]" title={src.file_path}>
                          {src.file_path}
                        </span>
                        <span className={`px-2 py-0.5 rounded-md text-[10px] font-semibold ${getRelevanceBadgeStyles(src.score)}`}>
                          {formatScore(src.score)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Collapsible Citations Section */}
              {message.citations && message.citations.length > 0 && (
                <div className="pt-3 border-t border-surface-800/60 space-y-2">
                  <div className="flex items-center gap-1.5 text-2xs font-semibold text-surface-400 uppercase tracking-wider">
                    <Quote className="h-3.5 w-3.5 text-violet-400" />
                    <span>Citations</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {message.citations.map((cite, idx) => {
                      const isExpanded = !!expandedCitations[idx];
                      return (
                        <div
                          key={idx}
                          className="flex flex-col rounded-xl bg-surface-950/40 border border-surface-850 overflow-hidden"
                        >
                          <button
                            onClick={() => toggleCitation(idx)}
                            className="w-full flex items-center justify-between p-3 text-left hover:bg-surface-800/20 transition-colors cursor-pointer"
                          >
                            <div className="min-w-0 pr-2">
                              <span className="text-2xs font-bold text-accent-400 block uppercase tracking-wider">
                                Citation {idx + 1}
                              </span>
                              <span className="text-xs text-surface-200 font-semibold truncate block max-w-[200px]" title={cite.source}>
                                Source: {cite.source}
                              </span>
                              <span className="text-[10px] text-surface-500 font-medium">
                                Page: {cite.page ?? 1}
                              </span>
                            </div>
                            <ChevronDown
                              className={`h-4 w-4 text-surface-500 transition-transform duration-200 shrink-0 ${
                                isExpanded ? 'rotate-180' : ''
                              }`}
                            />
                          </button>

                          <AnimatePresence initial={false}>
                            {isExpanded && (
                              <motion.div
                                initial={{ height: 0, opacity: 0 }}
                                animate={{ height: 'auto', opacity: 1 }}
                                exit={{ height: 0, opacity: 0 }}
                                transition={{ duration: 0.2 }}
                                className="overflow-hidden border-t border-surface-850"
                              >
                                <div className="p-3 bg-surface-950/60 text-xs text-surface-400 leading-relaxed italic border-l-2 border-accent-500/50">
                                  &ldquo;{cite.snippet}&rdquo;
                                </div>
                              </motion.div>
                            )}
                          </AnimatePresence>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Retrieved Documents Section */}
              {message.sources && message.sources.length > 0 && (
                <div className="pt-3 border-t border-surface-800/60 space-y-2">
                  <div className="flex items-center gap-1.5 text-2xs font-semibold text-surface-400 uppercase tracking-wider">
                    <Database className="h-3.5 w-3.5 text-emerald-400" />
                    <span>Top Retrieved Documents</span>
                  </div>
                  <ol className="space-y-2">
                    {message.sources.map((src, idx) => (
                      <li
                        key={idx}
                        className="flex items-center justify-between text-xs text-surface-300 pl-1"
                      >
                        <div className="flex items-center gap-2">
                          <span className="text-surface-550 font-bold">{idx + 1}.</span>
                          <span className="font-semibold text-surface-200 truncate max-w-[250px]" title={src.file_path}>
                            {src.file_path}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                          <span className="text-2xs text-surface-550">Score:</span>
                          <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold ${getRelevanceBadgeStyles(src.score)}`}>
                            {formatScore(src.score)}
                          </span>
                        </div>
                      </li>
                    ))}
                  </ol>
                </div>
              )}
            </div>
          )}
        </div>

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

