import React, { useRef, useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Sparkles, Database, Send } from 'lucide-react';
import { UploadZone } from '../Documents/UploadZone';
import { FileList } from '../Documents/FileList';
import type { DocumentMetadata } from '../../services/documentService';
import { DocMindLogo } from '../Branding/DocMindLogo';

interface SuggestedQuestionsProps {
  onSelect: (question: string) => void;
  // Upload hooks
  uploadFile: (file: File) => Promise<boolean>;
  isUploading: boolean;
  uploadProgress: number;
  // Document list hooks
  documents: DocumentMetadata[];
  isDocsLoading: boolean;
  deleteDocument: (filename: string) => Promise<boolean>;
  // Chat input
  onSubmitQuestion: (question: string) => void;
  isLoadingQuestion: boolean;
}

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.08 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: { duration: 0.35, ease: 'easeOut' as const } },
};

export const SuggestedQuestions: React.FC<SuggestedQuestionsProps> = ({
  uploadFile,
  isUploading,
  uploadProgress,
  documents,
  isDocsLoading,
  deleteDocument,
  onSubmitQuestion,
  isLoadingQuestion,
}) => {
  const [chatInput, setChatInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }
  }, [chatInput]);

  const handleChatSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || isLoadingQuestion) return;
    onSubmitQuestion(chatInput.trim());
    setChatInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleChatSubmit(e);
    }
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="flex flex-col items-center w-full max-w-4xl mx-auto px-6 py-10 space-y-10"
    >
      {/* 1. Hero / Badge Section */}
      <motion.div variants={itemVariants} className="text-center flex flex-col items-center">
        {/* Badge */}
        <div className="mb-4 inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-accent-500/10 border border-accent-500/25 text-accent-300 text-2xs font-semibold uppercase tracking-wider shadow-glow-sm">
          <Sparkles className="h-3 w-3 text-accent-400" />
          Enterprise Knowledge Assistant
        </div>

        {/* Logo and Titles */}
        <div className="mx-auto mb-4 h-14 w-14 rounded-2xl bg-surface-900 border border-surface-800/80 flex items-center justify-center shadow-glow-lg">
          <DocMindLogo size={32} gradientId="docmind-gradient-hero" />
        </div>
        <h1 className="text-3xl font-extrabold text-surface-100 tracking-tight sm:text-4xl bg-gradient-to-r from-surface-100 via-surface-200 to-surface-400 bg-clip-text text-transparent">
          DocMind AI Assistant
        </h1>
        <p className="text-sm text-surface-500 mt-2 max-w-md mx-auto leading-relaxed">
          Unlock intelligence from your documents using semantically indexed knowledge and Google Gemini logic.
        </p>
      </motion.div>

      {/* 2. Visually Dominant Upload Section Card */}
      <motion.div
        variants={itemVariants}
        className="w-full max-w-[800px] relative p-6 sm:p-8 rounded-xl bg-surface-900/40 border border-surface-800/80 backdrop-blur-xl shadow-glow-md hover:shadow-glow-lg hover:border-surface-700/80 transition-all duration-300 group"
      >
        {/* Hover gradient border overlay */}
        <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-accent-500/5 via-cyan-500/5 to-accent-500/5 opacity-50 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />

        <div className="relative z-10 flex flex-col items-center text-center space-y-6">
          <div className="space-y-1">
            <h2 className="text-lg font-bold text-surface-100">
              Upload Your Knowledge Base
            </h2>
            <p className="text-xs text-surface-400 max-w-lg mx-auto">
              Upload PDFs, TXT files, or Markdown documents and instantly start asking AI-powered questions.
            </p>
          </div>

          <div className="w-full pt-2">
            <UploadZone
              onUpload={uploadFile}
              isUploading={isUploading}
              progress={uploadProgress}
            />
          </div>
        </div>
      </motion.div>

      {/* 3. Recent Documents List Area */}
      <motion.div variants={itemVariants} className="w-full max-w-[800px] space-y-3">
        <div className="flex items-center justify-between border-b border-surface-800/60 pb-2">
          <div className="flex items-center gap-2">
            <Database className="h-4 w-4 text-violet-400" />
            <h3 className="text-xs font-semibold text-surface-400 uppercase tracking-wider">
              Recent Documents ({documents.length})
            </h3>
          </div>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-surface-900 border border-surface-800 text-surface-500 font-semibold uppercase tracking-wider">
            ChromaDB
          </span>
        </div>

        <FileList
          documents={documents}
          isLoading={isDocsLoading}
          onDelete={deleteDocument}
        />
      </motion.div>

      {/* 4. Inline Chat Input Section */}
      <motion.div variants={itemVariants} className="w-full max-w-[800px] space-y-3 pt-4 border-t border-surface-850/60">
        <div className="flex items-center gap-2 mb-1">
          <span className="h-2 w-2 rounded-full bg-cyan-400 animate-pulse-ring" />
          <h3 className="text-xs font-semibold text-surface-400 uppercase tracking-wider">
            Start A Conversation
          </h3>
        </div>

        <form onSubmit={handleChatSubmit} className="relative">
          <div className="flex items-end gap-2 p-2 rounded-2xl bg-surface-900/60 border border-surface-800 focus-within:border-accent-500/40 focus-within:shadow-glow-sm transition-all duration-200 backdrop-blur-xl">
            <textarea
              ref={textareaRef}
              rows={1}
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoadingQuestion}
              placeholder="Ask a question about your uploaded knowledge base..."
              className="flex-1 resize-none bg-transparent px-3 py-2.5 text-sm text-surface-100 placeholder-surface-500 focus:outline-none disabled:opacity-50 max-h-32 scrollbar-thin"
            />
            <div className="pb-1 pr-1">
              <motion.button
                type="submit"
                disabled={!chatInput.trim() || isLoadingQuestion}
                className="p-2.5 rounded-xl bg-accent-600 text-white disabled:opacity-30 disabled:cursor-not-allowed hover:bg-accent-500 transition-all shadow-glow-sm cursor-pointer"
                whileTap={{ scale: 0.95 }}
              >
                <Send className="h-4 w-4" />
              </motion.button>
            </div>
          </div>
        </form>
      </motion.div>
    </motion.div>
  );
};
