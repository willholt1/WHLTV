# Use a lightweight Python image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy your script into the container
COPY scrapeTeamRankings.py .

# Install required Python libraries
RUN pip install requests beautifulsoup4 psycopg2-binary

# Set the default command to run the script
CMD ["python", "scrapeTeamRankings.py"]
