import { apiClient } from './apiClient';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface SourceCitation {
  source: string;
  page?: number;
  snippet: string;
}

export interface SourceScore {
  file_path: string;
  score: number;
}

export interface ChatResponse {
  answer: string;
  response: string;
  sources: SourceScore[];
  citations: SourceCitation[];
}

export const chatService = {
  async queryKnowledgeBase(message: string, history: ChatMessage[]): Promise<ChatResponse> {
    const response = await apiClient.post<ChatResponse>('/api/chat/query', {
      message,
      history,
    });
    return response.data;
  },
};
