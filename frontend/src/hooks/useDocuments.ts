import { useState, useCallback } from 'react';
import { documentService } from '../services/documentService';
import type { DocumentMetadata } from '../services/documentService';

export const useDocuments = () => {
  const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);

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

  const uploadFile = useCallback(async (file: File) => {
    setIsUploading(true);
    setUploadProgress(0);
    setError(null);
    try {
      await documentService.uploadDocument(file, (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        setUploadProgress(percentCompleted);
      });
      await fetchDocuments();
      return true;
    } catch (err: any) {
      setError(err.message || `Failed to upload document: ${file.name}`);
      return false;
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
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
  };
};
