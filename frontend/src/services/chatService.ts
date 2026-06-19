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

export interface ChatResponse {
  response: string;
  sources: SourceCitation[];
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
