# Dockerfile
# Use a lightweight Python image
FROM python:3.8-slim

# Set working directory
WORKDIR /app

# Copy only requirements.txt first for layer caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Add a script to create a .env file from environment variables
COPY create_env_file.sh /app/

# Run the script to create .env file and then start the server
CMD ["sh", "-c", "./create_env_file.sh && gunicorn -w 4 -b 0.0.0.0:5000 app:app"]
