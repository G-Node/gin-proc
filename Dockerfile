FROM python:3

# Create directories
RUN mkdir -p /app/backend
RUN mkdir -p /app/frontend
WORKDIR /app

COPY images /app/images

# Install NPM
RUN apt-get update
RUN apt-get install -y npm

# Copy and install front-end
WORKDIR /app/frontend
COPY front-end/. /app/frontend
RUN npm install npm@latest -g
RUN npm install nuxt -g

RUN npm install
RUN nuxt build

# Install Python dependencies
WORKDIR /app
COPY requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt

# Copy back-end code and images
COPY back-end/. /app/backend

WORKDIR /app

COPY docker/entrypoint.sh /app/
ENTRYPOINT ["/app/entrypoint.sh"]
