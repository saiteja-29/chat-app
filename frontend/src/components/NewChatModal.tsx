import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Conversation, User } from "../types";

type Props = {
  open: boolean;
  onClose: () => void;
  onCreated: (conversation: Conversation) => void;
};

export function NewChatModal({ open, onClose, onCreated }: Props) {
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUserIds, setSelectedUserIds] = useState<string[]>([]);
  const [chatType, setChatType] = useState<"direct" | "group">("direct");
  const [groupName, setGroupName] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) return;

    async function loadUsers() {
      const response = await api.get("/users");
      setUsers(response.data);
    }

    loadUsers();
  }, [open]);

  function toggleUser(userId: string) {
    if (chatType === "direct") {
      setSelectedUserIds([userId]);
      return;
    }

    setSelectedUserIds((prev) =>
      prev.includes(userId)
        ? prev.filter((id) => id !== userId)
        : [...prev, userId]
    );
  }

  async function createChat() {
    setError("");

    if (chatType === "direct" && selectedUserIds.length !== 1) {
      setError("Select exactly one user for direct chat.");
      return;
    }

    if (chatType === "group" && selectedUserIds.length < 1) {
      setError("Select at least one user for group chat.");
      return;
    }

    if (chatType === "group" && !groupName.trim()) {
      setError("Group name is required.");
      return;
    }

    const response = await api.post("/conversations", {
      type: chatType,
      name: chatType === "group" ? groupName : null,
      member_ids: selectedUserIds,
    });

    onCreated(response.data);
    setSelectedUserIds([]);
    setGroupName("");
    setChatType("direct");
    onClose();
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-slate-900 text-white w-full max-w-lg rounded-2xl shadow-xl p-6 space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-bold">New Chat</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white">
            ✕
          </button>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500 text-red-300 p-3 rounded">
            {error}
          </div>
        )}

        <div className="flex gap-2">
          <button
            onClick={() => {
              setChatType("direct");
              setSelectedUserIds([]);
            }}
            className={`flex-1 p-2 rounded ${
              chatType === "direct" ? "bg-blue-600" : "bg-slate-800"
            }`}
          >
            Direct
          </button>

          <button
            onClick={() => {
              setChatType("group");
              setSelectedUserIds([]);
            }}
            className={`flex-1 p-2 rounded ${
              chatType === "group" ? "bg-blue-600" : "bg-slate-800"
            }`}
          >
            Group
          </button>
        </div>

        {chatType === "group" && (
          <input
            className="w-full p-3 rounded bg-slate-800 border border-slate-700"
            placeholder="Group name"
            value={groupName}
            onChange={(e) => setGroupName(e.target.value)}
          />
        )}

        <div className="max-h-72 overflow-y-auto border border-slate-800 rounded">
          {users.map((user) => {
            const selected = selectedUserIds.includes(user.id);

            return (
              <button
                key={user.id}
                onClick={() => toggleUser(user.id)}
                className={`w-full text-left p-3 border-b border-slate-800 hover:bg-slate-800 ${
                  selected ? "bg-slate-800" : ""
                }`}
              >
                <p className="font-medium">{user.display_name || user.username}</p>
                <p className="text-sm text-slate-400">{user.email}</p>
              </button>
            );
          })}
        </div>

        <button
          onClick={createChat}
          className="w-full bg-blue-600 hover:bg-blue-700 p-3 rounded font-semibold"
        >
          Create Chat
        </button>
      </div>
    </div>
  );
}