import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  FileSearch,
  BookOpen,
  Lightbulb,
  Shield,
  Database,
  MessageSquare,
  Search,
  Sparkles
} from 'lucide-react';
import { useDocuments } from '../../hooks/useDocuments';
import { DocMindLogo } from '../Branding/DocMindLogo';

interface SuggestedQuestionsProps {
  onSelect: (question: string) => void;
}

const suggestions = [
  {
    icon: FileSearch,
    title: 'Search policies',
    question: 'What are the main policies in the uploaded documents?',
    color: 'text-violet-400',
    bgColor: 'bg-violet-500/10',
    borderColor: 'border-violet-500/20',
  },
  {
    icon: BookOpen,
    title: 'Summarize content',
    question: 'Can you summarize the key points from all uploaded documents?',
    color: 'text-cyan-400',
    bgColor: 'bg-cyan-500/10',
    borderColor: 'border-cyan-500/20',
  },
  {
    icon: Lightbulb,
    title: 'Extract insights',
    question: 'What are the most important deadlines or dates mentioned?',
    color: 'text-amber-400',
    bgColor: 'bg-amber-500/10',
    borderColor: 'border-amber-500/20',
  },
  {
    icon: Shield,
    title: 'Check compliance',
    question: 'What security or compliance requirements are described?',
    color: 'text-emerald-400',
    bgColor: 'bg-emerald-500/10',
    borderColor: 'border-emerald-500/20',
  },
];

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.08 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0 },
};

export const SuggestedQuestions: React.FC<SuggestedQuestionsProps> = ({ onSelect }) => {
  const { documents, fetchDocuments } = useDocuments();
  const [queriesCount, setQueriesCount] = useState(32);
  const [sourcesCount, setSourcesCount] = useState(96);

  useEffect(() => {
    fetchDocuments();

    // Load local storage counters
    try {
      const storedQueries = localStorage.getItem('docmind_queries_count');
      const storedSources = localStorage.getItem('docmind_sources_count');

      if (storedQueries) {
        setQueriesCount(parseInt(storedQueries, 10));
      } else {
        localStorage.setItem('docmind_queries_count', '32');
      }

      if (storedSources) {
        setSourcesCount(parseInt(storedSources, 10));
      } else {
        localStorage.setItem('docmind_sources_count', '96');
      }
    } catch (e) {
      console.warn('LocalStorage reads failed', e);
    }
  }, [fetchDocuments]);

  return (
    <div className="flex flex-col items-center justify-center min-h-full px-6 py-12">
      {/* Badge */}
      <motion.div
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.05 }}
        className="mb-4 inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-accent-500/10 border border-accent-500/25 text-accent-300 text-2xs font-semibold uppercase tracking-wider shadow-glow-sm"
      >
        <Sparkles className="h-3 w-3 text-accent-400" />
        Enterprise AI Knowledge Platform
      </motion.div>

      {/* Hero section */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
        className="text-center mb-8"
      >
        <div className="mx-auto mb-4 h-14 w-14 rounded-2xl bg-surface-900 border border-surface-800/80 flex items-center justify-center shadow-glow-lg">
          <DocMindLogo size={32} gradientId="docmind-gradient-hero" />
        </div>
        <h2 className="text-2xl font-bold text-surface-100 tracking-tight">
          How can I help you today?
        </h2>
        <p className="text-sm text-surface-500 mt-2 max-w-md mx-auto leading-relaxed">
          Ask questions about your uploaded documents. I'll search through your knowledge base and provide answers with citations.
        </p>
      </motion.div>

      {/* Metrics Section */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="grid grid-cols-3 gap-4 w-full max-w-xl mb-8"
      >
        {/* Documents Card */}
        <motion.div
          variants={itemVariants}
          whileHover={{ y: -3, borderColor: 'rgba(139, 92, 246, 0.35)' }}
          className="flex flex-col p-4 rounded-xl border border-surface-800/80 bg-surface-900/40 backdrop-blur-md relative overflow-hidden group transition-all duration-300 shadow-glow-sm"
        >
          <div className="absolute inset-0 bg-gradient-to-br from-violet-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
          <div className="flex items-center gap-2 mb-1.5 relative z-10">
            <Database className="h-3.5 w-3.5 text-violet-400" />
            <span className="text-[10px] text-surface-400 font-semibold uppercase tracking-wider">Indexed</span>
          </div>
          <span className="text-xl font-extrabold text-surface-100 relative z-10 tracking-tight">
            {documents.length}
          </span>
          <span className="text-[10px] text-surface-500 mt-0.5 relative z-10">Documents online</span>
        </motion.div>

        {/* Queries Card */}
        <motion.div
          variants={itemVariants}
          whileHover={{ y: -3, borderColor: 'rgba(34, 211, 238, 0.35)' }}
          className="flex flex-col p-4 rounded-xl border border-surface-800/80 bg-surface-900/40 backdrop-blur-md relative overflow-hidden group transition-all duration-300 shadow-glow-sm"
        >
          <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
          <div className="flex items-center gap-2 mb-1.5 relative z-10">
            <MessageSquare className="h-3.5 w-3.5 text-cyan-400" />
            <span className="text-[10px] text-surface-400 font-semibold uppercase tracking-wider">Queries</span>
          </div>
          <span className="text-xl font-extrabold text-surface-100 relative z-10 tracking-tight">
            {queriesCount}
          </span>
          <span className="text-[10px] text-surface-500 mt-0.5 relative z-10">Total processed</span>
        </motion.div>

        {/* Sources Card */}
        <motion.div
          variants={itemVariants}
          whileHover={{ y: -3, borderColor: 'rgba(245, 158, 11, 0.35)' }}
          className="flex flex-col p-4 rounded-xl border border-surface-800/80 bg-surface-900/40 backdrop-blur-md relative overflow-hidden group group-hover:border-opacity-100 transition-all duration-300 shadow-glow-sm"
        >
          <div className="absolute inset-0 bg-gradient-to-br from-amber-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
          <div className="flex items-center gap-2 mb-1.5 relative z-10">
            <Search className="h-3.5 w-3.5 text-amber-400" />
            <span className="text-[10px] text-surface-400 font-semibold uppercase tracking-wider">Sources</span>
          </div>
          <span className="text-xl font-extrabold text-surface-100 relative z-10 tracking-tight">
            {sourcesCount}
          </span>
          <span className="text-[10px] text-surface-500 mt-0.5 relative z-10">Citations found</span>
        </motion.div>
      </motion.div>

      {/* Suggestion cards */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-xl"
      >
        {suggestions.map((item) => {
          const Icon = item.icon;
          return (
            <motion.button
              key={item.title}
              variants={itemVariants}
              onClick={() => onSelect(item.question)}
              className={`group text-left p-4 rounded-xl border ${item.borderColor} ${item.bgColor} 
                hover:border-opacity-40 hover:shadow-card-hover
                transition-all duration-200 cursor-pointer`}
              whileHover={{ y: -2 }}
              whileTap={{ scale: 0.98 }}
            >
              <div className="flex items-start gap-3">
                <Icon className={`h-5 w-5 ${item.color} shrink-0 mt-0.5`} />
                <div>
                  <p className={`text-sm font-semibold ${item.color} mb-1`}>
                    {item.title}
                  </p>
                  <p className="text-xs text-surface-400 leading-relaxed line-clamp-2 group-hover:text-surface-300 transition-colors">
                    {item.question}
                  </p>
                </div>
              </div>
            </motion.button>
          );
        })}
      </motion.div>
    </div>
  );
};
