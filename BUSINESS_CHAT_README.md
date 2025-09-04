# Business Chat System

A comprehensive business chat system that integrates with OpenAI to provide intelligent, context-aware responses about businesses. Built with Django, AJAX, and Tailwind CSS.

## 🌟 Features

### Core Functionality
- **Smart Business Assistant**: AI-powered chat that answers questions about businesses
- **Conversation History**: Maintains context across chat sessions
- **Fallback System**: Works without OpenAI using intelligent fallback responses
- **Real-time Chat**: AJAX-powered interface for seamless user experience
- **Mobile Responsive**: Beautiful UI that works on all devices

### Technical Features
- **Django Models**: Business, UserBusinessInquiry, BusinessAIIquiryResponse
- **OpenAI Integration**: Uses GPT-4o-mini for intelligent responses
- **Admin Interface**: Manage businesses and chat interactions
- **User Authentication**: Secure login system
- **Database Storage**: All conversations are stored and retrievable

## 🏗️ Architecture

### Models

#### Business Model
```python
class Business(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    industry = models.CharField(max_length=100)
    company_size = models.CharField(max_length=50)
    website = models.URLField(blank=True, null=True)
    location = models.CharField(max_length=200)
    phone = models.CharField(max_length=30)
    email = models.EmailField()
    whatsapp_number = models.CharField(max_length=30, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### UserBusinessInquiry Model
```python
class UserBusinessInquiry(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    user = models.ForeignKey('users.MyUser', on_delete=models.CASCADE)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### BusinessAIIquiryResponse Model
```python
class BusinessAIIquiryResponse(models.Model):
    inquiry = models.OneToOneField(UserBusinessInquiry, on_delete=models.CASCADE)
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
```

### Views

#### BusinessChatService (TemplateView)
- Renders the main chat interface
- Loads business context data
- Handles business not found errors

#### web_chat_assistant Function
- Processes user queries
- Manages conversation history
- Calls OpenAI API or fallback responses
- Saves inquiries and responses

#### business_chat_ajax (AJAX Endpoint)
- Handles real-time chat messages
- Returns JSON responses
- Manages authentication

## 🚀 Quick Start

### 1. Database Setup
```bash
# Create and run migrations
python manage.py makemigrations listings
python manage.py migrate
```

### 2. Create Sample Data
```bash
# Run the demo script
python demo_business_chat.py
```

### 3. Start the Server
```bash
python manage.py runserver
```

### 4. Access the Interface
- **Chat Interface**: `http://localhost:8000/business/1/chat/`
- **Admin Panel**: `http://localhost:8000/admin/`
- **Login**: admin@example.com / admin123

## 💻 Usage Examples

### Creating a Business
```python
from listings.models import Business

business = Business.objects.create(
    name="TechCorp Solutions",
    description="A leading technology company providing innovative software solutions.",
    industry="Technology",
    company_size="50-100 employees",
    website="https://techcorp.example.com",
    location="Nairobi, Kenya",
    phone="+254712345678",
    email="info@techcorp.example.com",
    whatsapp_number="+254712345678"
)
```

### Programmatic Chat Interaction
```python
from listings.views import web_chat_assistant
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.get(email='demo@example.com')
business_id = 1
query = "What services do you offer?"

response = web_chat_assistant(business_id, user, query)
print(response)
```

## 🎨 Frontend Features

### Chat Interface
- **Modern Design**: Clean, professional interface using Tailwind CSS
- **Real-time Messaging**: AJAX-powered for smooth user experience
- **Message History**: Displays previous conversations
- **Loading States**: Visual feedback during API calls
- **Error Handling**: Graceful error messages

### Business Information Panel
- **Company Details**: Name, industry, location, contact info
- **Contact Links**: Clickable phone, email, and website links
- **WhatsApp Integration**: Direct WhatsApp contact option
- **Responsive Layout**: Works on desktop, tablet, and mobile

## 🔧 Configuration

### OpenAI Setup (Optional)
1. Get an OpenAI API key from https://platform.openai.com/
2. Add it through Django admin: `/admin/core/openaiapikey/`
3. The system will automatically use OpenAI when available

### URL Configuration
Add to your main `urls.py`:
```python
# Business Chat URLs
path('business/<int:id>/chat/', views.BusinessChatService.as_view(), name='business_chat'),
path('business/<int:business_id>/chat/ajax/', views.business_chat_ajax, name='business_chat_ajax'),
```

## 🛡️ Security Features

### Authentication
- User must be logged in to access chat
- CSRF protection on AJAX endpoints
- XSS prevention with HTML escaping

### Data Validation
- Input sanitization
- SQL injection protection
- Rate limiting ready (can be added)

## 📊 Analytics & Monitoring

### Admin Interface
- View all businesses
- Monitor chat interactions
- Track user inquiries
- Manage AI responses

### Database Queries
```python
# Get chat statistics
from listings.models import UserBusinessInquiry, BusinessAIIquiryResponse

total_inquiries = UserBusinessInquiry.objects.count()
total_responses = BusinessAIIquiryResponse.objects.count()

# Get conversations for a specific business
business_chats = UserBusinessInquiry.objects.filter(
    business_id=1
).order_by('-created_at')
```

## 🚀 Advanced Features

### Conversation Context
The system maintains conversation history, allowing for contextual responses:
- Previous messages are included in OpenAI prompts
- Natural conversation flow
- Reference to earlier topics

### Fallback System
When OpenAI is unavailable:
- Intelligent fallback responses
- Uses business information
- Provides contact details
- Maintains professional tone

### Extensibility
- Easy to add new business fields
- Customizable AI prompts
- Pluggable response systems
- API-ready architecture

## 🔄 API Endpoints

### Chat AJAX Endpoint
```
POST /business/<business_id>/chat/ajax/
Content-Type: application/json

{
    "message": "Your question here"
}
```

Response:
```json
{
    "success": true,
    "response": "AI generated response"
}
```

## 🧪 Testing

### Run Demo Script
```bash
python demo_business_chat.py
```

### Manual Testing
1. Visit the chat interface
2. Log in with test credentials
3. Send various types of questions
4. Verify responses are appropriate
5. Check admin panel for stored data

## 🎯 Use Cases

### Business Customer Service
- Answer common questions automatically
- Provide business information 24/7
- Reduce support ticket volume
- Improve customer experience

### Lead Generation
- Capture customer inquiries
- Qualify potential clients
- Collect contact information
- Track engagement metrics

### Information Hub
- Company directory
- Service descriptions
- Contact information
- Business hours and policies

## 🔮 Future Enhancements

### Planned Features
- [ ] File upload support
- [ ] Voice message integration
- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] Integration with CRM systems
- [ ] Automated follow-up emails
- [ ] Chat export functionality
- [ ] Custom AI training on business data

### Scalability
- Redis caching for chat history
- Celery for async processing
- Database optimization
- CDN for static assets
- Load balancing support

## 📝 License

This business chat system is part of the TravelSke platform and follows the same licensing terms.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation

---

**Built with ❤️ using Django, OpenAI, and Tailwind CSS**