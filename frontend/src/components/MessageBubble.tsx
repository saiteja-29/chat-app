import type { Message } from "../types";

type Props = {
  message: Message;
  currentUserId: string;
};

export function MessageBubble({ message, currentUserId }: Props) {
  const isMine = message.sender_id === currentUserId;

  function getStatus() {
    if (!isMine) return null;

    if (message.read) return "✓✓ (read)";
    if (message.delivered) return "✓✓";
    return "✓";
  }

  return (
    <div className={`flex ${isMine ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-md p-3 rounded-2xl ${
          isMine
            ? "bg-blue-600 text-white"
            : "bg-slate-800 text-slate-100"
        }`}
      >
        <p>{message.content}</p>

        <div className="text-xs opacity-70 mt-1 flex justify-between">
          <span>
            {new Date(message.created_at).toLocaleTimeString()}
          </span>

          {isMine && (
            <span className="ml-2 text-blue-200">
              {getStatus()}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}