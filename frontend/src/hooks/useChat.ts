import { useState, useCallback } from 'react';
import { chatService } from '../services/chatService';
import type { ChatMessage, SourceCitation } from '../services/chatService';

export interface ChatUILevelMessage extends ChatMessage {
  id: string;
  timestamp: Date;
  sources?: SourceCitation[];
}

export const useChat = () => {
  const [messages, setMessages] = useState<ChatUILevelMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim()) return;

    const userMessageId = Math.random().toString(36).substring(2, 9);
    const userMessage: ChatUILevelMessage = {
      id: userMessageId,
      role: 'user',
      content,
      timestamp: new Date(),
    };

    // Update conversation state with user message
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    // Format chat history for LangChain
    const apiHistory = messages.map(({ role, content }) => ({ role, content }));

    try {
      const response = await chatService.queryKnowledgeBase(content, apiHistory);
      
      const assistantMessageId = Math.random().toString(36).substring(2, 9);
      const assistantMessage: ChatUILevelMessage = {
        id: assistantMessageId,
        role: 'assistant',
        content: response.response,
        sources: response.sources,
        timestamp: new Date(),
      };
      
      try {
        const storedQueries = localStorage.getItem('docmind_queries_count');
        const storedSources = localStorage.getItem('docmind_sources_count');
        const currentQueries = storedQueries ? parseInt(storedQueries, 10) : 32;
        const currentSources = storedSources ? parseInt(storedSources, 10) : 96;
        const sourcesCount = response.sources ? response.sources.length : 0;
        
        localStorage.setItem('docmind_queries_count', (currentQueries + 1).toString());
        localStorage.setItem('docmind_sources_count', (currentSources + sourcesCount).toString());
      } catch (e) {
        console.warn('Failed to update dashboard metrics in localStorage', e);
      }

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      setError(err.message || 'An error occurred while communicating with the assistant.');
    } finally {
      setIsLoading(false);
    }
  }, [messages]);

  const clearChat = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearChat,
  };
};
