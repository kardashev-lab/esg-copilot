#!/bin/bash
# Start both backend and frontend in development mode

echo "Starting Reggie - AI Regulations Co-Pilot in development mode..."

# Start backend in background
echo "Starting backend server..."
cd backend
source venv/bin/activate
python main.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend
echo "Starting frontend development server..."
cd ../frontend
npm start &
FRONTEND_PID=$!

echo "Development servers started!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for user to stop
wait

# Cleanup on exit
echo "Stopping servers..."
kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
echo "Servers stopped"
