export type User = {
  id: string;
  username: string;
  email: string;
  display_name: string | null;
  is_active: boolean;
  created_at: string;
};

export type ConversationMember = {
  id: string;
  username: string;
  display_name: string | null;
};

export type Conversation = {
  id: string;
  type: "direct" | "group";
  name: string | null;
  created_by: string;
  created_at: string;
  unread_count?: number;
  members?: ConversationMember[];
};

export type Message = {
  id: string;
  conversation_id: string;
  sender_id: string;
  content: string;
  message_type: string;
  created_at: string;
  delivered?: boolean;
  read?: boolean;
};