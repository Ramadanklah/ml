# Multi-stage build for React frontend
FROM node:18-alpine as base

# Set work directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production && npm cache clean --force

# Copy source code
COPY . .

# Development stage
FROM base as development

# Install development dependencies
RUN npm install

# Expose port
EXPOSE 3000

# Start development server
CMD ["npm", "start"]

# Build stage
FROM base as build

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine as production

# Copy built application
COPY --from=build /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

# Development with hot reload
FROM base as dev-server

# Install development dependencies
RUN npm install

# Expose port
EXPOSE 3000

# Start development server with host binding
CMD ["npm", "start", "--", "--host", "0.0.0.0"]