FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy API code
COPY . .

# Copy the agent code from the parent directory
COPY ../pr_review_agent.py .
COPY ../adapters ./adapters
COPY ../analyzers ./analyzers
COPY ../models ./models
COPY ../utils ./utils

# Create a directory for logs
RUN mkdir logs

# Expose the port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Run the application
CMD ["python", "run.py"]