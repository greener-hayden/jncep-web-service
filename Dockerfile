# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /app

# Install Flask and jncep
RUN pip install Flask jncep requests

# Copy the current directory contents into the container at /app
COPY . /app

# Set the default directory for jncep output
ENV JNCEP_OUTPUT_DIR /app/downloads

# Make directory for jncep downloads
RUN mkdir -p ${JNCEP_OUTPUT_DIR}

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable for Discord webhook
# Replace YourDiscordWebhookHere with the actual webhook URL if you want to set it by default
ENV DISCORD_WEBHOOK_URL YourDiscordWebhookHere

# Set the default command to execute
# when creating a new container
CMD ["flask", "run", "--host=0.0.0.0"]
