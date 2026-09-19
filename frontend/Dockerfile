FROM node:22-alpine

WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ARG NEXT_PUBLIC_API_URL=https://ai4society-hackathon.onrender.com
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

RUN npm run build

ENV PORT=3000
EXPOSE 3000
CMD ["sh", "-c", "npx next start --hostname 0.0.0.0 --port ${PORT}"]
