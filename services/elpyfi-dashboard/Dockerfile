FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm install --omit=dev

# Copy application code
COPY . .

# Build Next.js app
RUN npm run build

# Create non-root user
RUN adduser -D -u 1000 elpyfi && chown -R elpyfi:elpyfi /app
USER elpyfi

# Expose port
EXPOSE 8080

# Run production server
CMD ["npm", "start"]