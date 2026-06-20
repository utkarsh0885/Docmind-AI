import React, { useCallback, useState } from 'react';
import { motion } from 'framer-motion';
import { UploadCloud, Loader2, FileUp } from 'lucide-react';
import type { UploadStatus } from '../../hooks/useDocuments';

interface UploadZoneProps {
  onUpload: (file: File) => Promise<boolean>;
  isUploading: boolean;
  progress: number;
  status: UploadStatus;
}

export const UploadZone: React.FC<UploadZoneProps> = ({ onUpload, progress, status }) => {
  const [isDragActive, setIsDragActive] = useState(false);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    // Disable drag behavior during active ingestion
    const isActiveUpload = status === 'uploading' || status === 'processing' || status === 'embedding';
    if (isActiveUpload) return;

    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragActive(true);
    } else if (e.type === 'dragleave') {
      setIsDragActive(false);
    }
  }, [status]);

  const isActiveUpload = status === 'uploading' || status === 'processing' || status === 'embedding';

  const processFile = async (file: File) => {
    await onUpload(file);
  };

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragActive(false);
      if (isActiveUpload) return;
      const file = e.dataTransfer.files?.[0];
      if (file) await processFile(file);
    },
    [isActiveUpload, onUpload]
  );

  const handleFileInput = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) await processFile(file);
    // Reset so same file can be re-uploaded
    e.target.value = '';
  };

  return (
    <div className="w-full space-y-3">
      {/* Upload progress bar (top of card) */}
      {isActiveUpload && (
        <div className="w-full h-1 rounded-full bg-surface-800 overflow-hidden">
          <motion.div
            className="h-full bg-accent-gradient rounded-full"
            initial={{ width: '0%' }}
            animate={{ width: `${status === 'uploading' ? progress : 100}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>
      )}

      <div
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        className={`relative rounded-xl border-2 border-dashed flex flex-col items-center justify-center p-8 text-center transition-all duration-200
          ${isDragActive
            ? 'border-accent-500 bg-accent-500/5 shadow-glow-sm'
            : isActiveUpload
            ? 'border-surface-700 bg-surface-900/30 cursor-not-allowed'
            : 'border-surface-800 hover:border-surface-600 bg-surface-900/20 hover:bg-surface-900/40'
          }`}
      >
        <input
          type="file"
          id="file-upload-input"
          accept=".pdf,.txt,.md"
          onChange={handleFileInput}
          disabled={isActiveUpload}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
        />

        {isActiveUpload ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-col items-center gap-3"
          >
            <div className="relative">
              <Loader2 className="h-8 w-8 text-accent-400 animate-spin" />
              {status === 'uploading' && (
                <span className="absolute inset-0 flex items-center justify-center text-2xs font-bold text-accent-300">
                  {progress}%
                </span>
              )}
            </div>
            <div>
              <p className="text-sm font-semibold text-surface-200">
                {status === 'uploading' && 'Uploading document...'}
                {status === 'processing' && 'Processing document...'}
                {status === 'embedding' && 'Creating embeddings...'}
              </p>
              <p className="text-xs text-surface-500 mt-1">
                {status === 'uploading' && `Uploading to server (${progress}%)`}
                {status === 'processing' && 'Extracting text and parsing structure'}
                {status === 'embedding' && 'Generating search embeddings'}
              </p>
            </div>
          </motion.div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <motion.div
              className="h-12 w-12 rounded-xl bg-surface-800/80 border border-surface-700 flex items-center justify-center"
              animate={isDragActive ? { scale: 1.1 } : { scale: 1 }}
            >
              {isDragActive ? (
                <FileUp className="h-5 w-5 text-accent-400" />
              ) : (
                <UploadCloud className="h-5 w-5 text-surface-400" />
              )}
            </motion.div>
            <div>
              <p className="text-sm font-medium text-surface-200">
                Drop file here or{' '}
                <span className="text-accent-400 hover:text-accent-300 underline underline-offset-2 decoration-accent-400/30">
                  browse
                </span>
              </p>
              <p className="text-xs text-surface-500 mt-1">
                PDF, TXT, or Markdown &middot; Max 10MB
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

