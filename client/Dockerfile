FROM node:20-alpine

WORKDIR /app

COPY package.json ./
COPY client/package.json ./client/package.json

RUN npm install

COPY client ./client

EXPOSE 5173

CMD ["npm", "run", "dev", "-w", "@knb/client"]

