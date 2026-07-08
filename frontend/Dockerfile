# Stage 1: Build the React app
FROM node:18-alpine AS build

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm install

# Copy the rest of the code and build
COPY . .
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine

# Copy built assets from the build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy a custom nginx config if you want to handle React Router (SPA routing)
# If not, the default nginx config might return 404 for subpaths. Let's create a minimal config inline:
RUN echo $'server {\n\
    listen 80;\n\
    location / {\n\
        root   /usr/share/nginx/html;\n\
        index  index.html index.htm;\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
}' > /etc/nginx/conf.d/default.conf

# Expose port (Railway will map this automatically if we use PORT env var, but nginx default is 80)
# To support Railway's dynamic PORT we can use a script to replace the port at runtime, 
# or just expose 80 and let Railway route to it. Nginx uses 80 by default.
# For Railway Docker support:
CMD sed -i -e 's/listen 80;/listen '"${PORT:-80}"';/g' /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'
