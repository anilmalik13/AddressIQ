from flask import Flask, request, jsonify
from flask_cors import CORS
from .services.azure_openai import get_access_token, connect_wso2

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message')
    system_prompt = data.get('system_prompt')
    
    if not user_message:
        return jsonify({'error': 'Message is required'}), 400

    try:
        access_token = get_access_token()
        response = connect_wso2(access_token, user_message, system_prompt)
        return jsonify(response), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)