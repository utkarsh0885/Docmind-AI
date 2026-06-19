import { apiClient } from './apiClient';

export interface DocumentMetadata {
  id: string;
  filename: string;
  size_bytes: number;
  upload_time: string;
  chunk_count: number;
}

export interface IngestionResponse {
  filename: string;
  status: string;
  chunks_created: number;
  message: string;
}

export interface MessageResponse {
  message: string;
}

export const documentService = {
  async listDocuments(): Promise<DocumentMetadata[]> {
    const response = await apiClient.get<DocumentMetadata[]>('/api/documents');
    return response.data;
  },

  async uploadDocument(file: File, onUploadProgress?: (progressEvent: any) => void): Promise<IngestionResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<IngestionResponse>('/api/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress,
    });
    return response.data;
  },

  async deleteDocument(filename: string): Promise<MessageResponse> {
    const response = await apiClient.delete<MessageResponse>(`/api/documents/${filename}`);
    return response.data;
  },
};
