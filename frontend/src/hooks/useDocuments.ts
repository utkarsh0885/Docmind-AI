import { useState, useCallback } from 'react';
import { documentService } from '../services/documentService';
import type { DocumentMetadata } from '../services/documentService';

export type UploadStatus = 'idle' | 'uploading' | 'processing' | 'embedding' | 'ready' | 'failed';

export const useDocuments = () => {
  const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);

  // Status tracking states
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>('idle');
  const [activeFileName, setActiveFileName] = useState<string | null>(null);
  const [chunksCreated, setChunksCreated] = useState<number | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const fetchDocuments = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await documentService.listDocuments();
      setDocuments(data);
    } catch (err: any) {
      setError(err.message || 'Failed to retrieve documents list.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const resetUploadState = useCallback(() => {
    setUploadStatus('idle');
    setActiveFileName(null);
    setChunksCreated(null);
    setUploadError(null);
    setUploadProgress(0);
  }, []);

  const uploadFile = useCallback(async (file: File) => {
    setIsUploading(true);
    setUploadProgress(0);
    setError(null);
    setUploadStatus('uploading');
    setActiveFileName(file.name);
    setChunksCreated(null);
    setUploadError(null);

    let embeddingTimeoutId: any = null;

    try {
      const response = await documentService.uploadDocument(file, (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        setUploadProgress(percentCompleted);
        
        // Once Axios reaches 100%, transition to processing
        if (percentCompleted >= 100) {
          setUploadStatus('processing');
          
          // If response is still pending after 1.5s, transition to embedding
          if (!embeddingTimeoutId) {
            embeddingTimeoutId = setTimeout(() => {
              setUploadStatus('embedding');
            }, 1500);
          }
        }
      });

      if (embeddingTimeoutId) {
        clearTimeout(embeddingTimeoutId);
      }

      setUploadStatus('ready');
      setChunksCreated(response.chunks_created);
      setUploadProgress(100);

      await fetchDocuments();

      // Automatically reset status card after 6 seconds
      setTimeout(() => {
        setUploadStatus((current) => (current === 'ready' ? 'idle' : current));
        setActiveFileName((current) => (current === file.name ? null : current));
        setChunksCreated(null);
      }, 6000);

      return true;
    } catch (err: any) {
      if (embeddingTimeoutId) {
        clearTimeout(embeddingTimeoutId);
      }
      setUploadStatus('failed');
      const msg = err.response?.data?.detail || err.message || `Failed to upload document: ${file.name}`;
      setUploadError(msg);
      setError(msg);
      return false;
    } finally {
      setIsUploading(false);
    }
  }, [fetchDocuments]);

  const deleteDocument = useCallback(async (filename: string) => {
    setIsLoading(true);
    setError(null);
    try {
      await documentService.deleteDocument(filename);
      await fetchDocuments();
      return true;
    } catch (err: any) {
      setError(err.message || `Failed to delete document: ${filename}`);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [fetchDocuments]);

  return {
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
  };
};

