# Start with a Python image.
FROM python:latest

ENV PYTHONUNBUFFERED 1

# Install some necessary things.
RUN apt-get update
RUN apt-get install -y netcat

# Copy all our files into the image.
COPY ./src /code
WORKDIR /code

# Install our requirements.
RUN pip install -r requirements-dev.txt
RUN pip install --no-cache-dir -e .
