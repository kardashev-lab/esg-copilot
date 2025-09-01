# Reggie - AI Regulations Co-Pilot - Quick Start Guide

## Prerequisites
- Python 3.9+
- Node.js 18+
- OpenAI API key

## Setup (Already Done)
The setup script has already:
- Created Python virtual environment
- Installed all dependencies
- Created configuration files
- Set up sample data

## Configuration
1. Update `backend/.env` with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_actual_openai_api_key_here
   ```

## Running the Application

### Option 1: Start Both Servers (Recommended)
```bash
./start_dev.sh
```

### Option 2: Start Servers Separately
```bash
# Terminal 1 - Backend
./start_backend.sh

# Terminal 2 - Frontend
./start_frontend.sh
```

## Access Points
- **Frontend Application**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Features Available
- 📊 Dashboard with ESG metrics and trends
- 💬 AI-powered chat for ESG questions
- 📁 Document upload and management
- 📋 Automated report generation
- ✅ Compliance checking and gap analysis
- ⚙️ Settings and configuration

## Next Steps
1. Upload your ESG documents (frameworks, company data, peer reports)
2. Start a chat session to ask ESG questions
3. Generate compliance reports
4. Create sustainability reports with AI assistance

## Support
For issues or questions, check the main README.md file or create an issue in the repository.
