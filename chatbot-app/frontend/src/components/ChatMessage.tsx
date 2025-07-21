import React from 'react';
import { ChatMessage as ChatMessageType } from '../types';

interface ChatMessageProps {
    message: ChatMessageType;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
    return (
        <div className={`chat-message ${message.sender === 'user' ? 'user-message' : 'bot-message'}`}>
            <strong>{message.sender}:</strong> {message.content}
        </div>
    );
};

export default ChatMessage;