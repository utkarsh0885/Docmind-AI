import React from 'react';
import { Loader2, CheckCircle2, XCircle, FileText, X } from 'lucide-react';
import type { UploadStatus } from '../../hooks/useDocuments';

interface IngestionStatusCardProps {
  status: UploadStatus;
  fileName: string | null;
  progress: number;
  chunksCreated: number | null;
  error: string | null;
  onDismiss: () => void;
}

export const IngestionStatusCard: React.FC<IngestionStatusCardProps> = ({
  status,
  fileName,
  progress,
  chunksCreated,
  error,
  onDismiss,
}) => {
  if (status === 'idle') return null;

  return (
    <div className="w-full relative p-5 rounded-xl border bg-surface-900/50 border-surface-800/80 backdrop-blur-xl shadow-glow-sm overflow-hidden">
      {/* Glow effect based on state */}
      <div className={`absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${
        status === 'failed' 
          ? 'from-red-500 via-red-600 to-red-500' 
          : status === 'ready' 
          ? 'from-emerald-500 via-emerald-600 to-emerald-500' 
          : 'from-accent-500 via-cyan-500 to-accent-500 animate-pulse'
      }`} />

      <div className="flex items-start gap-4">
        {/* Icon */}
        <div className={`h-10 w-10 rounded-lg border flex items-center justify-center shrink-0 ${
          status === 'failed'
            ? 'bg-red-500/10 border-red-500/20 text-red-400'
            : status === 'ready'
            ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
            : 'bg-accent-500/10 border-accent-500/20 text-accent-400'
        }`}>
          <FileText className="h-5 w-5" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-surface-400">
              Document Status
            </h4>
            {/* Dismiss button */}
            {(status === 'ready' || status === 'failed') && (
              <button 
                onClick={onDismiss}
                className="text-surface-500 hover:text-surface-300 p-1 rounded-md hover:bg-surface-800 transition-colors cursor-pointer"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </div>

          <p className="text-sm font-medium text-surface-200 mt-1 truncate" title={fileName || ''}>
            {fileName || 'Unknown file'}
          </p>

          {/* Stage descriptions */}
          <div className="mt-3">
            {status === 'uploading' && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2 text-surface-300">
                    <Loader2 className="h-3.5 w-3.5 animate-spin text-accent-400" />
                    <span>Uploading document...</span>
                  </div>
                  <span className="font-semibold text-accent-400">{progress}%</span>
                </div>
                <div className="w-full h-1.5 rounded-full bg-surface-800 overflow-hidden">
                  <div className="h-full bg-accent-gradient rounded-full animate-pulse" style={{ width: `${progress}%` }} />
                </div>
              </div>
            )}

            {status === 'processing' && (
              <div className="flex items-center gap-2 text-xs text-surface-300">
                <Loader2 className="h-3.5 w-3.5 animate-spin text-accent-400" />
                <span>Processing document...</span>
              </div>
            )}

            {status === 'embedding' && (
              <div className="flex items-center gap-2 text-xs text-surface-300">
                <Loader2 className="h-3.5 w-3.5 animate-spin text-purple-400" />
                <span>Creating embeddings...</span>
              </div>
            )}

            {status === 'ready' && (
              <div className="space-y-1">
                <div className="flex items-center gap-2 text-xs text-emerald-400 font-semibold animate-fade-in-fast">
                  <CheckCircle2 className="h-4 w-4 shrink-0" />
                  <span>Document Ready</span>
                </div>
                <p className="text-2xs text-surface-400 leading-relaxed pl-6">
                  Chunks Created: <span className="font-semibold text-surface-200">{chunksCreated ?? 0}</span>
                  <br />
                  Indexed Successfully
                </p>
              </div>
            )}

            {status === 'failed' && (
              <div className="space-y-1">
                <div className="flex items-center gap-2 text-xs text-red-400 font-semibold animate-fade-in-fast">
                  <XCircle className="h-4 w-4 shrink-0" />
                  <span>Upload Failed</span>
                </div>
                <div className="text-2xs text-surface-400 pl-6 leading-relaxed">
                  <span className="font-medium text-red-400">Reason: </span>
                  <p className="mt-0.5 text-surface-300 whitespace-pre-wrap">{error || 'Unknown error occurred.'}</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
