## AI Chat Feature

The application includes an AI-powered chat assistant that can answer questions about agencies and places using OpenAI's GPT models.

### Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   
   **Note**: The chat feature works without OpenAI! It will use intelligent fallback responses.

2. **Enhanced AI Responses (Optional)**
   
   For enhanced AI responses using OpenAI GPT models, install the OpenAI package:
   ```bash
   pip install openai>=1.0.0
   ```
   
   Then add your OpenAI API key to your Django settings:
   
   ```python
   # settings.py
   OPENAI_API_KEY = 'your-openai-api-key-here'
   ```
   
   Or set it as an environment variable:
   ```bash
   export OPENAI_API_KEY='your-openai-api-key-here'
   ```

3. **Usage**
   
   Users can ask questions about agencies on the agency detail page. The AI will:
   - Answer questions based on agency information stored in the database
   - Provide helpful responses about services, pricing, location, etc.
   - Fall back to basic responses if OpenAI is not configured
   
   **Example Questions:**
   - "What services do you offer?"
   - "What are your prices?"
   - "Where are you located?"
   - "What is your cancellation policy?"

### Features

- **Real-time Chat**: Interactive chat interface with instant responses
- **Context-Aware**: Responses are based on actual agency data from your database
- **Smart Fallback System**: Works perfectly without OpenAI - uses intelligent keyword matching
- **Enhanced AI (Optional)**: OpenAI integration for more natural, conversational responses
- **User-Friendly**: Sample questions and helpful prompts to get started
- **Responsive Design**: Works beautifully on all devices
- **No External Dependencies**: Core functionality works out of the box

### Security

- CSRF protection enabled
- Input validation and sanitization
- Rate limiting recommended for production use
