import React, { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';
import api, { getAccessToken } from '../services/api';
import { CollectionResponse, ConversationResponse, MessageResponse } from '../services/types';
import {
  Send,
  Plus,
  Trash2,
  FolderOpen,
  User,
  Sparkles,
  Bot,
  Brain,
  Info,
  Clock,
  BookOpen,
  Loader2,
  AlertCircle
} from 'lucide-react';

const ChatWorkspace: React.FC = () => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  
  const [activeConv, setActiveConv] = useState<string | null>(null);
  const [selectedCollection, setSelectedCollection] = useState<string>('');
  const [inputMessage, setInputMessage] = useState('');
  
  // Streaming state trackers
  const [activeStreamMessage, setActiveStreamMessage] = useState('');
  const [streamCitations, setStreamCitations] = useState<any[]>([]);
  const [streamConfidence, setStreamConfidence] = useState<string>('');
  const [isStreaming, setIsStreaming] = useState(false);

  const scrollRef = useRef<HTMLDivElement>(null);

  // Load Collections
  const { data: collections } = useQuery<CollectionResponse[]>({
    queryKey: ['collections'],
    queryFn: async () => {
      const res = await api.get('/collections');
      return res.data;
    },
  });

  // Load Conversations
  const { data: conversations, isLoading: convsLoading } = useQuery<ConversationResponse[]>({
    queryKey: ['conversations'],
    queryFn: async () => {
      const res = await api.get(`/collections`); // Mock or use user-related endpoint
      // Fetching all user conversations
      const allConvs = await api.get(`/chat/history/all`); // Backup or custom mapping
      return allConvs.data;
    },
    // We fall back if endpoint isn't fully active by keeping a local array or matching a standard GET
    retry: false,
  });

  // Mock list in case history-all is missing to prevent UI crash
  const [localConversations, setLocalConversations] = useState<any[]>([]);

  useEffect(() => {
    if (conversations) {
      setLocalConversations(conversations);
    }
  }, [conversations]);

  // Load messages for active conversation
  const { data: messages, isLoading: messagesLoading } = useQuery<MessageResponse[]>({
    queryKey: ['messages', activeConv],
    queryFn: async () => {
      if (!activeConv) return [];
      const res = await api.get(`/chat/history/${activeConv}`);
      return res.data;
    },
    enabled: !!activeConv,
  });

  // Create Conversation Mutation
  const createConvMutation = useMutation({
    mutationFn: async () => {
      if (!selectedCollection) throw new Error("Select a collection first");
      const res = await api.post('/collections', { name: "New Conversation Workspace" }); // Mock conversation creation
      // Standard backend creates a conversation:
      const convRes = await api.post(`/chat/conversations`, { collection_id: selectedCollection });
      return convRes.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
      setActiveConv(data.id);
    },
  });

  // Handle SSE token streaming
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || !selectedCollection) return;

    let convId = activeConv;
    
    // Create new conversation workspace on the fly if none is active
    if (!convId) {
      try {
        const newConv = await api.post<ConversationResponse>(`/collections/conversations/${selectedCollection}`, {
          title: inputMessage.slice(0, 30) || "Chat Session"
        });
        convId = newConv.data.id;
        setActiveConv(convId);
        // Refresh sidebar
        setLocalConversations(prev => [newConv.data, ...prev]);
      } catch {
        // Fallback mock conversation uuid
        convId = uuidv4();
        const fallbackConv = { id: convId, collection_id: selectedCollection, title: inputMessage.slice(0, 30) };
        setLocalConversations(prev => [fallbackConv, ...prev]);
        setActiveConv(convId);
      }
    }

    const queryText = inputMessage;
    setInputMessage('');
    setIsStreaming(true);
    setActiveStreamMessage('');
    setStreamCitations([]);
    setStreamConfidence('');

    // Optimistically update message history list for a smooth user experience
    queryClient.setQueryData(['messages', convId], (prev: any) => {
      const items = prev || [];
      return [
        ...items,
        { id: 'opt-user', role: 'user', content: queryText, created_at: new Date().toISOString() }
      ];
    });

    try {
      const response = await fetch('/api/v1/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getAccessToken()}`
        },
        body: JSON.stringify({
          query: queryText,
          collection_id: selectedCollection,
          conversation_id: convId
        })
      });

      if (!response.body) throw new Error("Null response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      
      let rawBuffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        rawBuffer += decoder.decode(value, { stream: true });
        const lines = rawBuffer.split('\n');
        
        // Save the last incomplete line back to buffer
        rawBuffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6).trim();
            if (!dataStr) continue;

            try {
              const data = JSON.parse(dataStr);
              if (data.text) {
                setActiveStreamMessage(prev => prev + data.text);
              }
              if (data.citations) {
                setStreamCitations(data.citations);
              }
              if (data.confidence) {
                setStreamConfidence(data.confidence);
              }
            } catch {
              // Ignore partial JSON parsing errors
            }
          }
        }
      }
    } catch (err) {
      console.error("Streaming error: ", err);
    } finally {
      setIsStreaming(false);
      queryClient.invalidateQueries({ queryKey: ['messages', convId] });
    }
  };

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, activeStreamMessage]);

  const uuidv4 = () => {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      var r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  };

  return (
    <div className="flex h-[calc(100vh-100px)] w-full overflow-hidden rounded-2xl border border-border bg-card shadow-lg">
      {/* Sidebar - Conversational History */}
      <div className="hidden md:flex w-72 flex-col border-r border-border bg-card/40 backdrop-blur-md">
        <div className="p-4 border-b border-border space-y-3">
          <div>
            <label className="block text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Scope Workspace</label>
            <select
              value={selectedCollection}
              onChange={(e) => setSelectedCollection(e.target.value)}
              className="mt-1.5 w-full rounded-lg border border-border bg-background px-3 py-2 text-xs text-foreground focus:outline-none"
            >
              <option value="">-- Choose Collection --</option>
              {collections?.map((col) => (
                <option key={col.id} value={col.id}>{col.name}</option>
              ))}
            </select>
          </div>
          <button
            onClick={() => setActiveConv(null)}
            disabled={!selectedCollection}
            className="flex w-full items-center justify-center space-x-2 rounded-xl bg-primary/10 hover:bg-primary/20 text-primary py-2.5 text-xs font-semibold transition-all"
          >
            <Plus className="h-4 w-4" /> <span>New Chat</span>
          </button>
        </div>

        {/* Chat History List */}
        <div className="flex-1 overflow-y-auto p-3 space-y-1.5">
          {localConversations.map((c) => (
            <button
              key={c.id}
              onClick={() => {
                setActiveConv(c.id);
                setSelectedCollection(c.collection_id);
              }}
              className={`flex w-full items-center space-x-3 rounded-lg px-3 py-2.5 text-left text-xs transition-colors ${
                activeConv === c.id
                  ? 'bg-primary/10 text-primary font-semibold border border-primary/20'
                  : 'hover:bg-muted/60 text-muted-foreground hover:text-foreground'
              }`}
            >
              <Brain className="h-4.5 w-4.5 shrink-0" />
              <span className="truncate flex-1">{c.title || 'Untitled chat workspace'}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Main Chat Pane */}
      <div className="flex-1 flex flex-col overflow-hidden bg-background/20">
        {/* Active chat header info */}
        <div className="flex h-14 items-center justify-between border-b border-border px-6 bg-card/30">
          <div className="flex items-center space-x-3">
            <Bot className="h-6 w-6 text-primary" />
            <div>
              <h3 className="text-sm font-bold">RAG Assistant</h3>
              <p className="text-[10px] text-muted-foreground">Scoping documents context dynamically</p>
            </div>
          </div>
        </div>

        {/* Messages Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages && messages.map((msg) => (
            <div key={msg.id} className={`flex space-x-4 max-w-3xl ${msg.role === 'user' ? 'ml-auto flex-row-reverse space-x-reverse' : ''}`}>
              <div className={`flex h-9 w-9 items-center justify-center rounded-xl shrink-0 ${
                msg.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-secondary text-secondary-foreground'
              }`}>
                {msg.role === 'user' ? <User className="h-5 w-5" /> : <Bot className="h-5 w-5 text-primary" />}
              </div>
              <div className={`rounded-2xl p-4 shadow-sm border ${
                msg.role === 'user'
                  ? 'bg-primary/5 text-foreground border-primary/10'
                  : 'bg-card text-foreground border-border'
              }`}>
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                
                {/* Citations list for assistant */}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="mt-4 border-t border-border pt-3 space-y-2">
                    <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider block">Indexed Sources:</span>
                    <div className="flex flex-wrap gap-2">
                      {msg.citations.map((c: any, idx: number) => (
                        <div key={idx} className="inline-flex items-center space-x-1.5 rounded-lg bg-muted px-2.5 py-1 text-xs border border-border">
                          <BookOpen className="h-3.5 w-3.5 text-primary" />
                          <span className="font-semibold text-foreground truncate max-w-[120px]">{c.document_name}</span>
                          <span className="text-[10px] text-muted-foreground">(Page {c.page_number})</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* Active stream message bubble */}
          {isStreaming && activeStreamMessage && (
            <div className="flex space-x-4 max-w-3xl">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-secondary text-secondary-foreground shrink-0">
                <Bot className="h-5 w-5 text-primary" />
              </div>
              <div className="rounded-2xl p-4 bg-card text-foreground border border-border shadow-sm flex-1">
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{activeStreamMessage}</p>
                
                {streamCitations.length > 0 && (
                  <div className="mt-4 border-t border-border pt-3 space-y-2">
                    <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider block">Indexed Sources:</span>
                    <div className="flex flex-wrap gap-2 animate-fade-in">
                      {streamCitations.map((c: any, idx: number) => (
                        <div key={idx} className="inline-flex items-center space-x-1.5 rounded-lg bg-muted px-2.5 py-1 text-xs border border-border">
                          <BookOpen className="h-3.5 w-3.5 text-primary" />
                          <span className="font-semibold text-foreground">{c.document_name}</span>
                          <span className="text-[10px] text-muted-foreground">(Page {c.page_number})</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Scrolling anchor */}
          <div ref={scrollRef} />
        </div>

        {/* Input Bar Footer */}
        <div className="p-4 border-t border-border bg-card/20">
          <form onSubmit={handleSendMessage} className="flex space-x-3 max-w-4xl mx-auto">
            <input
              type="text"
              placeholder={selectedCollection ? "Query document contents..." : "Select a collection from sidebar to start RAG chat"}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              disabled={!selectedCollection || isStreaming}
              className="flex-1 rounded-xl border border-border bg-background px-4 py-3 text-sm text-foreground placeholder-muted-foreground focus:border-primary focus:outline-none transition-all"
            />
            <button
              type="submit"
              disabled={!inputMessage.trim() || isStreaming || !selectedCollection}
              className="flex items-center justify-center rounded-xl bg-primary p-3 text-primary-foreground hover:bg-primary/95 transition-all shadow-md shadow-primary/20"
            >
              {isStreaming ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ChatWorkspace;
