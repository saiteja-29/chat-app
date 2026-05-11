import { useEffect, useRef, useState } from "react";
import { API_BASE_URL, api } from "../api/client";
import { ChatWindow } from "../components/ChatWindow";
import { ConversationList } from "../components/ConversationList";
import { NewChatModal } from "../components/NewChatModal";
import type { Conversation, Message, User } from "../types";

export function ChatPage() {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const currentUserRef = useRef<User | null>(null);

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] =
    useState<Conversation | null>(null);

  const selectedConversationRef = useRef<Conversation | null>(null);

  const [socket, setSocket] = useState<WebSocket | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const heartbeatRef = useRef<number | null>(null);

  const [incomingMessages, setIncomingMessages] = useState<Message[]>([]);
  const [typingUsers, setTypingUsers] = useState<string[]>([]);
  const [onlineUserIds, setOnlineUserIds] = useState<Set<string>>(new Set());
  const [newChatOpen, setNewChatOpen] = useState(false);

  useEffect(() => {
    selectedConversationRef.current = selectedConversation;

    if (selectedConversation) {
      localStorage.setItem("selected_conversation_id", selectedConversation.id);
    }
  }, [selectedConversation]);

  useEffect(() => {
    async function init() {
      try {
        const token = localStorage.getItem("access_token");

        if (!token) {
          window.location.href = "/login";
          return;
        }

        const meResponse = await api.get("/users/me");
        const user: User = meResponse.data;

        setCurrentUser(user);
        currentUserRef.current = user;

        const convResponse = await api.get("/conversations/with-unread");
        const loadedConversations: Conversation[] = convResponse.data;

        setConversations(loadedConversations);

        const savedConversationId = localStorage.getItem(
          "selected_conversation_id"
        );

        if (savedConversationId) {
          const savedConversation = loadedConversations.find(
            (item) => item.id === savedConversationId
          );

          if (savedConversation) {
            setSelectedConversation(savedConversation);
            selectedConversationRef.current = savedConversation;
          }
        }

        connectWebSocket();
      } catch (error) {
        console.error("Failed to initialize chat:", error);
        localStorage.removeItem("access_token");
        window.location.href = "/login";
      }
    }

    init();

    return () => {
      if (heartbeatRef.current) {
        window.clearInterval(heartbeatRef.current);
      }

      socketRef.current?.close();
    };
  }, []);

  function connectWebSocket() {
    const token = localStorage.getItem("access_token");
    if (!token) return;

    if (
      socketRef.current &&
      socketRef.current.readyState !== WebSocket.CLOSED
    ) {
      return;
    }

    const wsUrl = API_BASE_URL.replace("http", "ws");
    const ws = new WebSocket(`${wsUrl}/ws?token=${token}`);

    socketRef.current = ws;
    setSocket(ws);

    ws.onopen = () => {
      console.log("WebSocket connected");

      if (heartbeatRef.current) {
        window.clearInterval(heartbeatRef.current);
      }

      heartbeatRef.current = window.setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: "heartbeat" }));
        }
      }, 30000);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "message.new") {
        const message: Message = {
          ...data.message,
          delivered: true,
          read: false,
        };

        setIncomingMessages((prev) => {
          const exists = prev.some((m) => m.id === message.id);
          return exists ? prev : [...prev, message];
        });

        const selected = selectedConversationRef.current;
        const user = currentUserRef.current;

        setConversations((prev) =>
          prev.map((conversation) => {
            if (conversation.id !== message.conversation_id) {
              return conversation;
            }

            const isCurrentOpen = selected?.id === message.conversation_id;
            const isMine = message.sender_id === user?.id;

            return {
              ...conversation,
              unread_count:
                isCurrentOpen || isMine
                  ? 0
                  : (conversation.unread_count || 0) + 1,
            };
          })
        );

        if (
          selected?.id === message.conversation_id &&
          message.sender_id !== user?.id &&
          ws.readyState === WebSocket.OPEN
        ) {
          ws.send(
            JSON.stringify({
              type: "message.read",
              message_id: message.id,
            })
          );
        }
      }

      if (data.type === "messages.sync") {
        const messages: Message[] = data.messages;

        setIncomingMessages((prev) => {
          const existingIds = new Set(prev.map((m) => m.id));
          const newMessages = messages.filter((m) => !existingIds.has(m.id));
          return [...prev, ...newMessages];
        });
      }

      if (data.type === "message.read") {
        setIncomingMessages((prev) =>
          prev.map((msg) =>
            msg.id === data.message_id
              ? { ...msg, read: true, delivered: true }
              : msg
          )
        );
      }

      if (data.type === "presence.update") {
        setOnlineUserIds((prev) => {
          const updated = new Set(prev);

          if (data.status === "online") {
            updated.add(data.user_id);
          } else {
            updated.delete(data.user_id);
          }

          return updated;
        });
      }

      if (data.type === "typing.start") {
        setTypingUsers((prev) =>
          prev.includes(data.username) ? prev : [...prev, data.username]
        );
      }

      if (data.type === "typing.stop") {
        setTypingUsers((prev) => prev.filter((u) => u !== data.username));
      }
    };

    ws.onclose = () => {
      console.log("WebSocket disconnected");

      if (heartbeatRef.current) {
        window.clearInterval(heartbeatRef.current);
        heartbeatRef.current = null;
      }

      socketRef.current = null;
      setSocket(null);
    };
  }

  function handleSelectConversation(conversation: Conversation) {
    setSelectedConversation(conversation);
    selectedConversationRef.current = conversation;

    setConversations((prev) =>
      prev.map((item) =>
        item.id === conversation.id ? { ...item, unread_count: 0 } : item
      )
    );
  }

  async function handleConversationCreated(conversation: Conversation) {
    const convResponse = await api.get("/conversations/with-unread");
    const updatedConversations: Conversation[] = convResponse.data;

    setConversations(updatedConversations);

    const created = updatedConversations.find(
      (item) => item.id === conversation.id
    );

    if (created) {
      setSelectedConversation(created);
      selectedConversationRef.current = created;
    }
  }

  function handleLogout() {
    if (heartbeatRef.current) {
      window.clearInterval(heartbeatRef.current);
    }

    socketRef.current?.close();

    localStorage.removeItem("access_token");
    localStorage.removeItem("selected_conversation_id");

    window.location.href = "/login";
  }

  if (!currentUser) {
    return (
      <div className="min-h-screen flex items-center justify-center text-white bg-slate-950">
        Loading chat...
      </div>
    );
  }

  return (
    <div className="h-screen text-white bg-slate-950 overflow-hidden flex flex-col">
      <div className="h-16 shrink-0 flex justify-between items-center px-4 bg-slate-900 border-b border-slate-800 z-50">
        <div>
          <p className="font-semibold">
            {currentUser.display_name || currentUser.username}
          </p>
          <p className="text-xs text-slate-400">{currentUser.email}</p>
        </div>

        <button
          onClick={handleLogout}
          className="bg-red-600 hover:bg-red-700 px-4 py-1 rounded text-white"
        >
          Logout
        </button>
      </div>

      <div className="flex flex-1 min-h-0 overflow-hidden">
        <ConversationList
          conversations={conversations}
          selectedId={selectedConversation?.id || null}
          currentUserId={currentUser.id}
          onlineUserIds={onlineUserIds}
          onSelect={handleSelectConversation}
          onNewChat={() => setNewChatOpen(true)}
        />

        <ChatWindow
          conversation={selectedConversation}
          currentUserId={currentUser.id}
          socket={socket}
          incomingMessages={incomingMessages}
          typingUsers={typingUsers}
          onlineUserIds={onlineUserIds}
          onMessagesRead={(conversationId) => {
            setConversations((prev) =>
              prev.map((item) =>
                item.id === conversationId
                  ? { ...item, unread_count: 0 }
                  : item
              )
            );
          }}
        />
      </div>

      <NewChatModal
        open={newChatOpen}
        onClose={() => setNewChatOpen(false)}
        onCreated={handleConversationCreated}
      />
    </div>
  );
}