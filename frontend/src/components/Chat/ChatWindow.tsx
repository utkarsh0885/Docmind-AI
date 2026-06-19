import React, { useRef, useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Send, ArrowDown, Trash2 } from 'lucide-react';
import { MessageBubble } from './MessageBubble';
import { TypingIndicator } from './TypingIndicator';
import { SuggestedQuestions } from './SuggestedQuestions';
import { useChat } from '../../hooks/useChat';

export const ChatWindow: React.FC = () => {
  const { messages, isLoading, error, sendMessage, clearChat } = useChat();
  const [input, setInput] = useState('');
  const [showScrollBtn, setShowScrollBtn] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Track scroll position for "scroll to bottom" pill
  useEffect(() => {
    const container = scrollContainerRef.current;
    if (!container) return;

    const handleScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = container;
      const isNearBottom = scrollHeight - scrollTop - clientHeight < 100;
      setShowScrollBtn(!isNearBottom);
    };

    container.addEventListener('scroll', handleScroll);
    return () => container.removeEventListener('scroll', handleScroll);
  }, []);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 160) + 'px';
    }
  }, [input]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    sendMessage(input);
    setInput('');
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleSuggestionSelect = (question: string) => {
    sendMessage(question);
  };

  const hasMessages = messages.length > 0;

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden relative">
      {/* Messages / Empty State */}
      <div
        ref={scrollContainerRef}
        className="flex-1 overflow-y-auto scrollbar-thin"
      >
        {!hasMessages ? (
          <SuggestedQuestions onSelect={handleSuggestionSelect} />
        ) : (
          <div className="max-w-3xl mx-auto px-4 sm:px-6 py-6 space-y-6">
            {messages.map((message, idx) => (
              <MessageBubble key={message.id} message={message} index={idx} />
            ))}

            {/* Typing indicator */}
            <AnimatePresence>
              {isLoading && <TypingIndicator />}
            </AnimatePresence>

            {/* Error notice */}
            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="flex items-center gap-3 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm"
                >
                  <div className="h-2 w-2 rounded-full bg-red-400 shrink-0" />
                  {error}
                </motion.div>
              )}
            </AnimatePresence>

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Scroll to bottom pill */}
      <AnimatePresence>
        {showScrollBtn && hasMessages && (
          <motion.button
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
            onClick={scrollToBottom}
            className="absolute bottom-28 left-1/2 -translate-x-1/2 z-10 flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-surface-800 border border-surface-700 text-surface-300 text-xs font-medium shadow-card hover:bg-surface-700 transition-colors cursor-pointer"
          >
            <ArrowDown className="h-3 w-3" />
            Scroll to bottom
          </motion.button>
        )}
      </AnimatePresence>

      {/* Input Area */}
      <div className="shrink-0 border-t border-surface-800/60 bg-surface-950/80 backdrop-blur-xl">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-4">
          <form onSubmit={handleSubmit} className="relative">
            <div className="flex items-end gap-2 p-2 rounded-2xl bg-surface-900/80 border border-surface-800/80 focus-within:border-accent-500/40 focus-within:shadow-glow-sm transition-all duration-200">
              <textarea
                ref={textareaRef}
                id="chat-input"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={isLoading}
                placeholder={
                  isLoading
                    ? 'Waiting for response...'
                    : 'Ask a question about your knowledge base...'
                }
                rows={1}
                className="flex-1 resize-none bg-transparent px-3 py-2.5 text-sm text-surface-100 placeholder-surface-500 focus:outline-none disabled:opacity-50 max-h-40 scrollbar-thin"
              />

              <div className="flex items-center gap-1.5 pb-1 pr-1">
                {/* Clear button */}
                {hasMessages && (
                  <button
                    type="button"
                    onClick={clearChat}
                    className="p-2 rounded-lg text-surface-500 hover:text-surface-300 hover:bg-surface-800 transition-all cursor-pointer"
                    title="Clear conversation"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}

                {/* Send button */}
                <motion.button
                  type="submit"
                  disabled={!input.trim() || isLoading}
                  className="p-2.5 rounded-xl bg-accent-600 text-white disabled:opacity-30 disabled:cursor-not-allowed hover:bg-accent-500 transition-all shadow-glow-sm cursor-pointer"
                  whileTap={{ scale: 0.95 }}
                >
                  <Send className="h-4 w-4" />
                </motion.button>
              </div>
            </div>
          </form>

          <p className="text-center text-2xs text-surface-600 mt-2.5">
            Powered by Google Gemini, ChromaDB and Retrieval-Augmented Generation (RAG)
          </p>
        </div>
      </div>
    </div>
  );
};
