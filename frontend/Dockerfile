FROM node:20-alpine

WORKDIR /workspace

COPY frontend/package.json ./package.json
COPY frontend/tsconfig.json ./tsconfig.json
COPY frontend/tsconfig.node.json ./tsconfig.node.json
COPY frontend/vite.config.ts ./vite.config.ts
COPY frontend/tailwind.config.ts ./tailwind.config.ts
COPY frontend/postcss.config.js ./postcss.config.js
COPY frontend/index.html ./index.html

RUN npm install

COPY frontend/src ./src

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

