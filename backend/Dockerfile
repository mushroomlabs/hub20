# Start with a Python image.
FROM python:latest

ENV PYTHONUNBUFFERED 1

# Install some necessary things.
RUN apt-get update
RUN apt-get install -y netcat

# Copy all relevant files into the image.
COPY ./hub20 /app/hub20
COPY ./requirements.txt /app
COPY ./README.md /app
COPY ./setup.py /app
WORKDIR /app

# Install our requirements.
RUN pip install --no-cache-dir -e /app
