# ESG AI Co-Pilot

An AI-powered co-pilot for ESG and sustainability professionals, designed to help companies navigate complex ESG reporting requirements, compliance frameworks, and sustainability best practices.

## Features

- 🤖 **AI-Powered Chat**: Get instant answers to ESG questions using advanced AI
- 📊 **Compliance Analysis**: Automated compliance checking across major ESG frameworks
- 📁 **Document Management**: Upload and analyze ESG documents and frameworks
- 📋 **Report Generation**: Create professional sustainability reports with AI assistance
- 🔍 **Supply Chain Analysis**: Analyze supply chain sustainability and risks
- 📈 **Dashboard & Analytics**: Track ESG performance and compliance metrics

## Supported Frameworks

- **GRI Standards** (Global Reporting Initiative)
- **SASB Standards** (Sustainability Accounting Standards Board)
- **TCFD Framework** (Task Force on Climate-related Financial Disclosures)
- **CSRD Directive** (Corporate Sustainability Reporting Directive)
- **IFRS Sustainability Standards**

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd new-esg-copilot
   ```

2. **Run the setup script**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Configure environment**
   ```bash
   # Update OpenAI API key in backend/.env
   nano backend/.env
   ```

4. **Start the application**
   ```bash
   # Start backend
   ./start_backend.sh
   
   # Start frontend (in new terminal)
   ./start_frontend.sh
   ```

5. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Production Deployment

For production deployment instructions, see [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md).

## Architecture

### Backend (Python/FastAPI)

- **FastAPI**: Modern, fast web framework
- **LangChain**: AI/LLM integration
- **ChromaDB**: Vector database for document storage
- **OpenAI**: GPT-4 integration for AI responses
- **Pydantic**: Data validation and serialization

### Frontend (React/TypeScript)

- **React 18**: Modern UI framework
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **Recharts**: Data visualization
- **React Router**: Client-side routing

## API Endpoints

### Core Endpoints

- `POST /api/v1/chat/message` - Send message to AI
- `POST /api/v1/compliance/check` - Check compliance with frameworks
- `POST /api/v1/documents/upload` - Upload documents
- `GET /api/v1/reports/generate` - Generate reports
- `GET /api/v1/health` - Health check

### Framework-Specific Endpoints

- `GET /api/v1/chat/frameworks` - List available frameworks
- `GET /api/v1/compliance/frameworks/{framework}/requirements` - Get framework requirements
- `GET /api/v1/compliance/benchmark` - Benchmark compliance

## Configuration

### Environment Variables

#### Backend (.env)

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Security
SECRET_KEY=your-secret-key-here

# API Configuration
DEBUG=False
LOG_LEVEL=INFO

# File Upload
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=52428800
```

#### Frontend (.env)

```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_NAME=ESG AI Co-Pilot
REACT_APP_VERSION=1.0.0
```

## Usage

### 1. Upload Documents

Upload your ESG documents, frameworks, and company data through the Documents page.

### 2. Start AI Chat

Ask questions about ESG frameworks, compliance requirements, or sustainability best practices.

### 3. Check Compliance

Run compliance checks against major ESG frameworks to identify gaps and get recommendations.

### 4. Generate Reports

Create professional sustainability reports with AI assistance.

### 5. Monitor Progress

Track your ESG performance and compliance metrics through the dashboard.

## Development

### Backend Development

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Development

```bash
cd frontend
npm install
npm start
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Security

- All API keys and secrets should be stored in environment variables
- HTTPS is required for production deployments
- Input validation is implemented throughout the application
- CORS is properly configured for security

## Support

For support and questions:

1. Check the [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) for deployment issues
2. Review the API documentation at `/docs` when running locally
3. Check application logs for error details
4. Create an issue in the repository

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- OpenAI for providing the GPT-4 API
- The ESG and sustainability community for frameworks and best practices
- Contributors and users of this project
