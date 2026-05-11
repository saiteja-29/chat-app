import type { Conversation } from "../types";
import {
  getConversationDisplayName,
  getOtherUser,
} from "../utils/conversation";

type Props = {
  conversations: Conversation[];
  selectedId: string | null;
  currentUserId: string;
  onlineUserIds: Set<string>;
  onSelect: (conversation: Conversation) => void;
  onNewChat: () => void;
};

export function ConversationList({
  conversations,
  selectedId,
  currentUserId,
  onlineUserIds,
  onSelect,
  onNewChat,
}: Props) {
  return (
    <div className="w-80 shrink-0 bg-slate-950 border-r border-slate-800 h-full overflow-y-auto">
      <div className="p-4 border-b border-slate-800 flex items-center justify-between sticky top-0 bg-slate-950 z-10">
        <h2 className="text-xl font-bold text-white">Chats</h2>

        <button
          onClick={onNewChat}
          className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded"
        >
          +
        </button>
      </div>

      {conversations.map((conversation) => {
        const otherUser = getOtherUser(conversation, currentUserId);
        const isDirectOnline =
          conversation.type === "direct" &&
          otherUser &&
          onlineUserIds.has(otherUser.id);

        return (
          <button
            key={conversation.id}
            onClick={() => onSelect(conversation)}
            className={`w-full text-left p-4 border-b border-slate-800 hover:bg-slate-800 ${
              selectedId === conversation.id ? "bg-slate-800" : ""
            }`}
          >
            <div className="flex justify-between items-center gap-3">
              <div className="flex items-center gap-2 min-w-0">
                {conversation.type === "direct" && (
                  <span
                    className={`w-2.5 h-2.5 rounded-full shrink-0 ${
                      isDirectOnline ? "bg-green-500" : "bg-slate-500"
                    }`}
                    title={isDirectOnline ? "Online" : "Offline"}
                  />
                )}

                <p className="text-white font-medium truncate">
                  {getConversationDisplayName(conversation, currentUserId)}
                </p>
              </div>

              {!!conversation.unread_count && (
                <span className="bg-blue-600 text-white text-xs px-2 py-1 rounded-full shrink-0">
                  {conversation.unread_count}
                </span>
              )}
            </div>

            <p className="text-slate-400 text-sm mt-1">
              {conversation.type === "group"
                ? `${conversation.members?.length || 0} members`
                : isDirectOnline
                ? "Online"
                : "Offline"}
            </p>
          </button>
        );
      })}
    </div>
  );
}