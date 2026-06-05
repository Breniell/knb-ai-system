FROM node:20-alpine

WORKDIR /app

COPY package.json ./
COPY server/package.json ./server/package.json

RUN npm install

COPY server ./server

WORKDIR /app/server
RUN npx prisma generate

EXPOSE 8080

CMD ["npm", "run", "dev"]

