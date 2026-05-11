import { useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type { Conversation, Message } from "../types";
import {
  getConversationDisplayName,
  getOtherUser,
} from "../utils/conversation";
import { MessageBubble } from "./MessageBubble";

type Props = {
  conversation: Conversation | null;
  currentUserId: string;
  socket: WebSocket | null;
  incomingMessages: Message[];
  typingUsers: string[];
  onlineUserIds: Set<string>;
  onMessagesRead: (conversationId: string) => void;
};

export function ChatWindow({
  conversation,
  currentUserId,
  socket,
  incomingMessages,
  typingUsers,
  onlineUserIds,
  onMessagesRead,
}: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [content, setContent] = useState("");
  const [typingTimeout, setTypingTimeout] = useState<number | null>(null);
  const [showMembers, setShowMembers] = useState(false);

  const bottomRef = useRef<HTMLDivElement | null>(null);
  const displayedMessageIdsRef = useRef<Set<string>>(new Set());

  function scrollToBottom() {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }

  function mergeMessages(newMessages: Message[]) {
    setMessages((prev) => {
      const byId = new Map<string, Message>();

      for (const message of prev) {
        byId.set(message.id, message);
      }

      for (const message of newMessages) {
        const existing = byId.get(message.id);

        byId.set(message.id, {
          ...existing,
          ...message,
          delivered: message.delivered ?? existing?.delivered,
          read: message.read ?? existing?.read,
        });

        displayedMessageIdsRef.current.add(message.id);
      }

      return Array.from(byId.values()).sort(
        (a, b) =>
          new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
      );
    });
  }

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    async function loadMessages() {
      if (!conversation) {
        setMessages([]);
        displayedMessageIdsRef.current = new Set();
        setShowMembers(false);
        return;
      }

      setShowMembers(false);

      const response = await api.get(
        `/conversations/${conversation.id}/messages`
      );

      displayedMessageIdsRef.current = new Set(
        response.data.items.map((message: Message) => message.id)
      );

      setMessages(response.data.items);

      for (const message of response.data.items) {
        if (
          message.sender_id !== currentUserId &&
          socket?.readyState === WebSocket.OPEN
        ) {
          socket.send(
            JSON.stringify({
              type: "message.read",
              message_id: message.id,
            })
          );
        }
      }

      onMessagesRead(conversation.id);
    }

    loadMessages();
  }, [conversation?.id]);

  useEffect(() => {
    if (!conversation) return;

    const relevant = incomingMessages.filter(
      (message) => message.conversation_id === conversation.id
    );

    if (relevant.length === 0) return;

    mergeMessages(relevant);

    for (const message of relevant) {
      if (
        message.sender_id !== currentUserId &&
        socket?.readyState === WebSocket.OPEN
      ) {
        socket.send(
          JSON.stringify({
            type: "message.read",
            message_id: message.id,
          })
        );
      }
    }

    onMessagesRead(conversation.id);
  }, [incomingMessages, conversation?.id]);

  function sendMessage() {
    if (!socket || !conversation || !content.trim()) return;

    socket.send(
      JSON.stringify({
        type: "message.send",
        conversation_id: conversation.id,
        content,
        message_type: "text",
        client_message_id: crypto.randomUUID(),
      })
    );

    setContent("");
  }

  function handleTyping(value: string) {
    setContent(value);

    if (!socket || !conversation) return;

    socket.send(
      JSON.stringify({
        type: "typing.start",
        conversation_id: conversation.id,
      })
    );

    if (typingTimeout) {
      window.clearTimeout(typingTimeout);
    }

    const timeout = window.setTimeout(() => {
      socket.send(
        JSON.stringify({
          type: "typing.stop",
          conversation_id: conversation.id,
        })
      );
    }, 1500);

    setTypingTimeout(timeout);
  }

  if (!conversation) {
    return (
      <div className="flex-1 h-full flex items-center justify-center text-slate-400 bg-slate-900">
        Select a conversation
      </div>
    );
  }

  const otherUser = getOtherUser(conversation, currentUserId);
  const directOnline =
    conversation.type === "direct" &&
    otherUser &&
    onlineUserIds.has(otherUser.id);

  const filteredTypingUsers =
    conversation.type === "group"
      ? typingUsers
      : typingUsers.filter((name) => name !== currentUserId);

  return (
    <div className="flex-1 h-full flex flex-col bg-slate-900 min-w-0 relative">
      <button
        type="button"
        onClick={() => {
          if (conversation.type === "group") {
            setShowMembers((prev) => !prev);
          }
        }}
        className={`p-4 border-b border-slate-800 text-white text-left shrink-0 ${
          conversation.type === "group" ? "hover:bg-slate-800" : ""
        }`}
      >
        <div className="flex items-center gap-2">
          {conversation.type === "direct" && (
            <span
              className={`w-2.5 h-2.5 rounded-full ${
                directOnline ? "bg-green-500" : "bg-slate-500"
              }`}
            />
          )}

          <h2 className="font-bold">
            {getConversationDisplayName(conversation, currentUserId)}
          </h2>
        </div>

        {conversation.type === "direct" && (
          <p className="text-xs text-slate-400 mt-1">
            {directOnline ? "Online" : "Offline"}
          </p>
        )}

        {conversation.type === "group" && (
          <p className="text-xs text-slate-400 mt-1">
            {conversation.members?.length || 0} members · click to view
          </p>
        )}

        {filteredTypingUsers.length > 0 && (
          <p className="text-sm text-blue-400 mt-1">
            {filteredTypingUsers.join(", ")} typing...
          </p>
        )}
      </button>

      {showMembers && conversation.type === "group" && (
        <div className="absolute right-4 top-20 w-80 bg-slate-950 border border-slate-700 rounded-xl shadow-2xl z-40 overflow-hidden">
          <div className="p-4 border-b border-slate-800 flex justify-between items-center">
            <div>
              <p className="font-semibold">Group members</p>
              <p className="text-xs text-slate-400">
                {conversation.members?.length || 0} members
              </p>
            </div>

            <button
              onClick={() => setShowMembers(false)}
              className="text-slate-400 hover:text-white"
            >
              ✕
            </button>
          </div>

          <div className="max-h-80 overflow-y-auto">
            {conversation.members?.map((member) => (
              <div
                key={member.id}
                className="p-4 border-b border-slate-800 flex items-center gap-3"
              >
                <div className="w-9 h-9 rounded-full bg-blue-600 flex items-center justify-center font-semibold">
                  {(member.display_name || member.username)
                    .slice(0, 1)
                    .toUpperCase()}
                </div>

                <div>
                  <p className="text-white">
                    {member.display_name || member.username}
                    {member.id === currentUserId && (
                      <span className="text-slate-400"> {" "}(You)</span>
                    )}
                  </p>
                  <p className="text-xs text-slate-400">@{member.username}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="flex-1 min-h-0 p-4 space-y-3 overflow-y-auto">
        {messages.map((message) => (
          <MessageBubble
            key={message.id}
            message={message}
            currentUserId={currentUserId}
          />
        ))}

        <div ref={bottomRef} />
      </div>

      <div className="p-4 border-t border-slate-800 flex gap-2 shrink-0">
        <input
          className="flex-1 p-3 rounded bg-slate-800 text-white outline-none focus:ring-2 focus:ring-blue-600"
          placeholder="Type a message..."
          value={content}
          onChange={(e) => handleTyping(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") sendMessage();
          }}
        />

        <button
          onClick={sendMessage}
          className="bg-blue-600 hover:bg-blue-700 text-white px-6 rounded font-semibold"
        >
          Send
        </button>
      </div>
    </div>
  );
}