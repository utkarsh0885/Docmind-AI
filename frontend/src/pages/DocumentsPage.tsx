import React, { useEffect } from 'react';
import { motion } from 'framer-motion';
import { UploadZone } from '../components/Documents/UploadZone';
import { FileList } from '../components/Documents/FileList';
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
  } = useDocuments();

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const totalChunks = documents.reduce((total, doc) => total + doc.chunk_count, 0);

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
          {error && (
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
          <section>
            <div className="flex items-center gap-2 mb-3">
              <h2 className="text-xs font-semibold text-surface-400 uppercase tracking-wider">Upload</h2>
            </div>
            <UploadZone
              onUpload={uploadFile}
              isUploading={isUploading}
              progress={uploadProgress}
            />
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
            />
          </section>
        </div>
      </div>
    </div>
  );
};
