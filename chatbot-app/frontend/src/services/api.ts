import axios from 'axios';

const API_BASE_URL = '/api';

export const sendMessage = async (userContent: string, systemPrompt?: string) => {
    try {
        const response = await axios.post(`${API_BASE_URL}/chat`, {
            message: userContent,
            system_prompt: systemPrompt
        }, {
            headers: {
                'Content-Type': 'application/json'
            }
        });

        return response.data;
    } catch (error) {
        console.error('Error sending message:', error);
        throw error;
    }
};