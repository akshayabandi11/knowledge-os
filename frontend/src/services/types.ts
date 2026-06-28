export interface UserResponse {
  id: string;
  email: string;
  full_name: string | null;
  role: 'USER' | 'ADMIN';
  email_verified: boolean;
  created_at: string;
}

export interface UserLoginRequest {
  email: string;
  password: string;
  device_name?: string;
  browser?: string;
  operating_system?: string;
}

export interface UserRegisterRequest {
  email: string;
  password: string;
  full_name?: string;
}

export interface SessionResponse {
  id: string;
  device_name: string | null;
  browser: string | null;
  operating_system: string | null;
  ip_address: string;
  login_time: string;
  last_activity: string;
}

export interface MessageResponse {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant';
  content: string;
  citations: Array<{
    document_name: string;
    page_number: number;
    chunk_index: number;
    confidence: number;
  }> | null;
  created_at: string;
}

export interface ConversationResponse {
  id: string;
  collection_id: string;
  user_id: string;
  title: string | null;
  created_at: string;
}

export interface CollectionResponse {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentResponse {
  id: string;
  collection_id: string;
  name: string;
  file_type: string;
  file_size: number;
  status: 'PENDING' | 'PARSED' | 'EMBEDDED' | 'FAILED';
  error_message: string | null;
  page_count: number | null;
  language: string | null;
  mime_type: string | null;
  chunk_count: number | null;
  created_at: string;
}
