# ---------- Frontend Builder ----------
FROM node:20-alpine AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend .
RUN npm run build

# ---------- Backend Builder ----------
FROM node:20-alpine AS backend-builder
WORKDIR /app
COPY ProyectoFinal_Backend/package.json ProyectoFinal_Backend/package-lock.json ./
RUN npm ci
COPY ProyectoFinal_Backend/tsconfig.json ./
COPY ProyectoFinal_Backend/prisma ./prisma
# Generar cliente Prisma antes de compilar TypeScript
RUN npx prisma generate
COPY ProyectoFinal_Backend/src ./src
RUN npm run build

# ---------- Runtime ----------
FROM node:20-alpine AS runtime
WORKDIR /app

# 1) Instala deps de PRODUCCIÓN (incluye prisma y @prisma/client)
COPY ProyectoFinal_Backend/package*.json ./
RUN npm install --omit=dev

# 2) Instala ts-node y typescript para ejecutar el seed
RUN npm install --save-dev ts-node typescript

# 3) Copia el esquema para que 'prisma generate' funcione
COPY ProyectoFinal_Backend/prisma ./prisma

# 4) Copia tsconfig.json necesario para ts-node (usado en prisma:seed)
COPY ProyectoFinal_Backend/tsconfig.json ./

# 5) Copia el código compilado del backend
COPY --from=backend-builder /app/dist ./dist

# 6) Copia el frontend compilado
COPY --from=frontend-builder /frontend/dist ./public

# 7) Genera el cliente (node_modules @ runtime ya tiene prisma)
RUN npx prisma generate

EXPOSE 8080
CMD sh -c "npx prisma migrate deploy || true; node dist/server.js"
