import type { Conversation, ConversationMember } from "../types";

export function getOtherUser(
  conversation: Conversation,
  currentUserId: string
): ConversationMember | undefined {
  return conversation.members?.find((member) => member.id !== currentUserId);
}

export function getConversationDisplayName(
  conversation: Conversation,
  currentUserId: string
) {
  if (conversation.type === "group") {
    return conversation.name || "Unnamed group";
  }

  const otherUser = getOtherUser(conversation, currentUserId);

  return otherUser?.display_name || otherUser?.username || "Direct chat";
}