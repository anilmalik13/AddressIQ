export interface ChatMessage {
    id?: string;
    content: string;
    sender: 'user' | 'bot';
    timestamp?: Date;
}

export interface User {
    id: string;
    name: string;
}

export interface ApiResponse {
    choices: {
        message: {
            content: string;
            role: string;
        };
    }[];
}