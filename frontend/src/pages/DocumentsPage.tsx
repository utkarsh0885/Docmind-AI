import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { UploadZone } from '../components/Documents/UploadZone';
import { FileList } from '../components/Documents/FileList';
import { IngestionStatusCard } from '../components/Documents/IngestionStatusCard';
import { useDocuments } from '../hooks/useDocuments';
import { Database, Layers, AlertTriangle } from 'lucide-react';

export const DocumentsPage: React.FC = () => {
  const {
    documents,
    isLoading,
    isUploading,
    uploadProgress,
    error,
    fetchDocuments,
    uploadFile,
    deleteDocument,
    uploadStatus,
    activeFileName,
    chunksCreated,
    uploadError,
    resetUploadState,
  } = useDocuments();

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const totalChunks = documents.reduce((total, doc) => total + doc.chunk_count, 0);

  const isActiveIngestion = uploadStatus === 'uploading' || uploadStatus === 'processing' || uploadStatus === 'embedding';

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden">
      {/* Page header */}
      <div className="flex items-center justify-between px-6 sm:px-8 h-14 border-b border-surface-800/60 shrink-0">
        <div>
          <h1 className="text-sm font-semibold text-surface-100">Documents</h1>
          <p className="text-2xs text-surface-500 -mt-0.5">Manage your knowledge base</p>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-6 space-y-6">
          {/* Error banner */}
          {error && uploadStatus !== 'failed' && (
            <motion.div
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center gap-3 p-3.5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm"
            >
              <AlertTriangle className="h-4 w-4 shrink-0" />
              <span className="text-xs font-medium">{error}</span>
            </motion.div>
          )}

          {/* Upload section */}
          <section className="space-y-4">
            <div className="flex items-center gap-2 mb-1">
              <h2 className="text-xs font-semibold text-surface-400 uppercase tracking-wider">Upload</h2>
            </div>

            {isActiveIngestion ? (
              <div className="p-6 rounded-xl border border-dashed border-surface-700 bg-surface-900/20 flex flex-col items-center justify-center text-center space-y-2">
                <span className="text-xs font-semibold text-accent-400 animate-pulse uppercase tracking-wider">
                  Ingestion in progress
                </span>
                <p className="text-2xs text-surface-500">
                  Please wait while your document is being ingested.
                </p>
              </div>
            ) : (
              <UploadZone
                onUpload={uploadFile}
                isUploading={isUploading}
                progress={uploadProgress}
                status={uploadStatus}
              />
            )}

            <AnimatePresence>
              {uploadStatus !== 'idle' && (
                <motion.div
                  initial={{ opacity: 0, height: 0, y: -10 }}
                  animate={{ opacity: 1, height: 'auto', y: 0 }}
                  exit={{ opacity: 0, height: 0, y: -10 }}
                  className="overflow-hidden"
                >
                  <IngestionStatusCard
                    status={uploadStatus}
                    fileName={activeFileName}
                    progress={uploadProgress}
                    chunksCreated={chunksCreated}
                    error={uploadError}
                    onDismiss={resetUploadState}
                  />
                </motion.div>
              )}
            </AnimatePresence>
          </section>

          {/* Stats row */}
          <div className="grid grid-cols-2 gap-3">
            <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-surface-900/40 border border-surface-800/60">
              <div className="h-9 w-9 rounded-lg bg-accent-500/10 border border-accent-500/20 flex items-center justify-center">
                <Database className="h-4 w-4 text-accent-400" />
              </div>
              <div>
                <p className="text-2xs text-surface-500 font-medium uppercase tracking-wider">Documents</p>
                <p className="text-lg font-bold text-surface-100 -mt-0.5">{documents.length}</p>
              </div>
            </div>

            <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-surface-900/40 border border-surface-800/60">
              <div className="h-9 w-9 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
                <Layers className="h-4 w-4 text-cyan-400" />
              </div>
              <div>
                <p className="text-2xs text-surface-500 font-medium uppercase tracking-wider">Vectors</p>
                <p className="text-lg font-bold text-surface-100 -mt-0.5">{totalChunks}</p>
              </div>
            </div>
          </div>

          {/* Document list */}
          <section>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-xs font-semibold text-surface-400 uppercase tracking-wider">Knowledge Base</h2>
              <span className="badge-neutral">
                ChromaDB
              </span>
            </div>

            <FileList
              documents={documents}
              isLoading={isLoading}
              onDelete={deleteDocument}
              activeFileName={activeFileName}
              activeStatus={uploadStatus}
              activeError={uploadError}
            />
          </section>
        </div>
      </div>
    </div>
  );
};

