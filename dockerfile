# python base image 
FROM python:3.10-slim-bullseye

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc python3-dev \
    && rm -rf /var/lib/apt/lists/*

# set working directory
WORKDIR /code

# copy requirements to working directory
COPY ./requirements.txt /code/requirements.txt

# install newest version of pip
RUN python -m pip install --upgrade pip

# install app packages from requirements
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# copy the application code to working directory
COPY ./app /code/app

# expose an arbitrary port (it won't be used for incoming connections)
# EXPOSE 8080

# execute run api command
CMD ["python", "app/main.py", "prod"]