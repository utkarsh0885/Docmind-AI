import React from 'react';
import { motion } from 'framer-motion';

export const TypingIndicator: React.FC = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.2 }}
      className="flex items-start gap-3 max-w-3xl"
    >
      {/* AI Avatar */}
      <div className="h-8 w-8 rounded-lg bg-accent-gradient flex items-center justify-center shrink-0 shadow-glow-sm mt-0.5">
        <svg className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
        </svg>
      </div>

      {/* Dots */}
      <div className="flex flex-col gap-1.5">
        <div className="flex items-center gap-1 px-4 py-3 rounded-2xl rounded-tl-md bg-surface-850 border border-surface-800/60">
          {[0, 1, 2].map((i) => (
            <motion.span
              key={i}
              className="h-2 w-2 rounded-full bg-accent-400"
              animate={{
                scale: [0.6, 1, 0.6],
                opacity: [0.4, 1, 0.4],
              }}
              transition={{
                duration: 1.4,
                repeat: Infinity,
                ease: 'easeInOut',
                delay: i * 0.2,
              }}
            />
          ))}
        </div>
        <span className="text-2xs text-surface-500 px-1 font-medium">
          DocMind is thinking...
        </span>
      </div>
    </motion.div>
  );
};
