import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Trash2, FileText, FolderOpen, X, Check, Loader2 } from 'lucide-react';
import type { DocumentMetadata } from '../../services/documentService';
import type { UploadStatus } from '../../hooks/useDocuments';

interface FileListProps {
  documents: DocumentMetadata[];
  isLoading: boolean;
  onDelete: (filename: string) => void;
  activeFileName?: string | null;
  activeStatus?: UploadStatus;
  activeError?: string | null;
}

// Skeleton loading cards
const SkeletonCard: React.FC = () => (
  <div className="flex items-center gap-4 px-4 py-4 rounded-xl bg-surface-900/40 border border-surface-800/40">
    <div className="h-10 w-10 rounded-lg skeleton" />
    <div className="flex-1 space-y-2">
      <div className="h-3.5 w-40 rounded skeleton" />
      <div className="h-2.5 w-24 rounded skeleton" />
    </div>
    <div className="h-6 w-16 rounded-md skeleton" />
  </div>
);

export const FileList: React.FC<FileListProps> = ({
  documents,
  isLoading,
  onDelete,
  activeFileName,
  activeStatus,
  activeError,
}) => {
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);

  const formatBytes = (bytes: number, decimals = 1) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(decimals)) + ' ' + sizes[i];
  };

  const formatDate = (isoString: string) => {
    try {
      const date = new Date(isoString);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMs / 3600000);
      const diffDays = Math.floor(diffMs / 86400000);

      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins}m ago`;
      if (diffHours < 24) return `${diffHours}h ago`;
      if (diffDays < 7) return `${diffDays}d ago`;
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    } catch {
      return isoString;
    }
  };

  const getFileIcon = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'pdf':
        return 'text-red-400 bg-red-500/10 border-red-500/20';
      case 'md':
        return 'text-blue-400 bg-blue-500/10 border-blue-500/20';
      default:
        return 'text-surface-400 bg-surface-800 border-surface-700';
    }
  };

  const getStatusBadge = (status: UploadStatus) => {
    switch (status) {
      case 'ready':
        return {
          text: 'Ready',
          classes: 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded-md text-[10px] font-semibold uppercase tracking-wider',
        };
      case 'embedding':
        return {
          text: 'Embedding',
          classes: 'bg-purple-500/10 text-purple-400 border border-purple-500/20 px-2 py-0.5 rounded-md text-[10px] font-semibold uppercase tracking-wider',
        };
      case 'processing':
        return {
          text: 'Processing',
          classes: 'bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2 py-0.5 rounded-md text-[10px] font-semibold uppercase tracking-wider',
        };
      case 'uploading':
        return {
          text: 'Uploading',
          classes: 'bg-amber-500/10 text-amber-400 border border-amber-500/20 px-2 py-0.5 rounded-md text-[10px] font-semibold uppercase tracking-wider',
        };
      case 'failed':
        return {
          text: 'Failed',
          classes: 'bg-red-500/10 text-red-400 border border-red-500/20 px-2 py-0.5 rounded-md text-[10px] font-semibold uppercase tracking-wider',
        };
      default:
        return {
          text: 'Ready',
          classes: 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded-md text-[10px] font-semibold uppercase tracking-wider',
        };
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3, 4].map((i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    );
  }

  // Determine if we should show a virtual loading document
  const showVirtual = activeFileName && activeStatus && activeStatus !== 'idle' && activeStatus !== 'ready' && !documents.some(d => d.filename === activeFileName);

  const virtualDoc = showVirtual
    ? {
        id: 'virtual-upload-id',
        filename: activeFileName!,
        size_bytes: 0,
        upload_time: new Date().toISOString(),
        chunk_count: 0,
        isVirtual: true,
        status: activeStatus!,
      }
    : null;

  const displayDocs = virtualDoc ? [virtualDoc, ...documents] : documents;

  // Empty state
  if (displayDocs.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex flex-col items-center justify-center py-16 text-center"
      >
        <div className="h-14 w-14 rounded-2xl bg-surface-900 border border-surface-800 flex items-center justify-center mb-4">
          <FolderOpen className="h-6 w-6 text-surface-500" />
        </div>
        <h4 className="text-sm font-semibold text-surface-300 mb-1">
          No documents yet
        </h4>
        <p className="text-xs text-surface-500 max-w-xs leading-relaxed">
          Upload documents above to build your knowledge base. They'll be chunked, embedded, and indexed for semantic search.
        </p>
      </motion.div>
    );
  }

  const handleDelete = (filename: string) => {
    if (confirmDelete === filename) {
      onDelete(filename);
      setConfirmDelete(null);
    } else {
      setConfirmDelete(filename);
      // Auto-reset after 3s
      setTimeout(() => setConfirmDelete(null), 3000);
    }
  };

  return (
    <div className="space-y-2">
      <AnimatePresence>
        {displayDocs.map((doc, idx) => {
          const iconClasses = getFileIcon(doc.filename);
          const isConfirming = confirmDelete === doc.filename;
          const isVirtual = 'isVirtual' in doc;
          const status = isVirtual ? (doc as any).status as UploadStatus : 'ready';
          const badge = getStatusBadge(status);

          return (
            <motion.div
              key={doc.id}
              layout
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2, delay: idx * 0.04 }}
              className={`group flex items-center gap-4 px-4 py-3.5 rounded-xl bg-surface-900/40 border transition-all duration-150
                ${isVirtual 
                  ? 'border-dashed border-surface-700 bg-surface-900/20' 
                  : 'border-surface-800/60 hover:border-surface-700 hover:bg-surface-900/60'
                }`}
            >
              {/* File icon */}
              <div className={`h-10 w-10 rounded-lg border flex items-center justify-center shrink-0 ${iconClasses}`}>
                {isVirtual && status !== 'failed' ? (
                  <Loader2 className="h-4.5 w-4.5 animate-spin text-accent-400" />
                ) : (
                  <FileText className="h-4.5 w-4.5" />
                )}
              </div>

              {/* File info */}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-surface-200 truncate" title={doc.filename}>
                  {doc.filename}
                </p>
                <div className="flex items-center gap-2 mt-0.5">
                  {isVirtual ? (
                    <span className="text-2xs text-surface-500">
                      {status === 'failed' ? activeError || 'Upload failed' : 'Indexing in progress...'}
                    </span>
                  ) : (
                    <>
                      <span className="text-2xs text-surface-500">{formatBytes(doc.size_bytes)}</span>
                      <span className="text-2xs text-surface-700">&middot;</span>
                      <span className="text-2xs text-surface-500">{formatDate(doc.upload_time)}</span>
                    </>
                  )}
                </div>
              </div>

              {/* Badges Container */}
              <div className="flex items-center gap-2 shrink-0">
                <span className={badge.classes}>
                  {badge.text}
                </span>

                {!isVirtual && (
                  <span className="badge-accent shrink-0">
                    {doc.chunk_count} chunks
                  </span>
                )}
              </div>

              {/* Delete button (or empty space placeholder for virtual item) */}
              <div className="w-8 flex items-center justify-end shrink-0">
                {!isVirtual ? (
                  <AnimatePresence mode="wait">
                    {isConfirming ? (
                      <motion.div
                        key="confirm"
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.9 }}
                        className="flex items-center gap-1"
                      >
                        <button
                          onClick={() => handleDelete(doc.filename)}
                          className="p-1.5 rounded-md bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors cursor-pointer"
                          title="Confirm delete"
                        >
                          <Check className="h-3.5 w-3.5" />
                        </button>
                        <button
                          onClick={() => setConfirmDelete(null)}
                          className="p-1.5 rounded-md bg-surface-800 text-surface-400 hover:bg-surface-700 transition-colors cursor-pointer"
                          title="Cancel"
                        >
                          <X className="h-3.5 w-3.5" />
                        </button>
                      </motion.div>
                    ) : (
                      <motion.button
                        key="delete"
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.9 }}
                        onClick={() => handleDelete(doc.filename)}
                        className="p-2 rounded-lg text-surface-500 opacity-0 group-hover:opacity-100 hover:text-red-400 hover:bg-red-500/10 transition-all cursor-pointer"
                        title="Delete document"
                      >
                        <Trash2 className="h-4 w-4" />
                      </motion.button>
                    )}
                  </AnimatePresence>
                ) : null}
              </div>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
};

