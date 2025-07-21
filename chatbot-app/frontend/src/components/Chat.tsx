import React, { useState, useEffect } from 'react';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import { sendMessage } from '../services/api';
import { ChatMessage as ChatMessageType, ApiResponse } from '../types';

const Chat: React.FC = () => {
    const [messages, setMessages] = useState<ChatMessageType[]>([]);
    const [loading, setLoading] = useState<boolean>(false);

    const handleSendMessage = async (content: string) => {
        const userMessage: ChatMessageType = { 
            sender: 'user', 
            content,
            id: Date.now().toString(),
            timestamp: new Date()
        };
        setMessages((prevMessages) => [...prevMessages, userMessage]);
        setLoading(true);

        try {
            const response: ApiResponse = await sendMessage(content);
            const botContent = response.choices?.[0]?.message?.content || 'No response received';
            const botMessage: ChatMessageType = { 
                sender: 'bot', 
                content: botContent,
                id: (Date.now() + 1).toString(),
                timestamp: new Date()
            };
            setMessages((prevMessages) => [...prevMessages, botMessage]);
        } catch (error) {
            console.error('Error sending message:', error);
            const errorMessage: ChatMessageType = {
                sender: 'bot',
                content: 'Sorry, I encountered an error. Please try again.',
                id: (Date.now() + 1).toString(),
                timestamp: new Date()
            };
            setMessages((prevMessages) => [...prevMessages, errorMessage]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="chat-container">
            <div className="chat-messages">
                {messages.map((message) => (
                    <ChatMessage key={message.id} message={message} />
                ))}
                {loading && (
                    <ChatMessage 
                        message={{ 
                            sender: 'bot', 
                            content: 'Typing...',
                            id: 'loading',
                            timestamp: new Date()
                        }} 
                    />
                )}
            </div>
            <ChatInput onSendMessage={handleSendMessage} />
        </div>
    );
};

export default Chat;