# Manual de Desarrollador - IDS Cryptojacking

## Arquitectura del Proyecto

Este proyecto utiliza **Arquitectura Limpia (Clean Architecture)** y está estructurado en las siguientes capas:

```
ProyectoFinal_Backend/
├── domain/           # Entidades y lógica de negocio pura
├── application/      # Casos de uso y servicios de aplicación
├── infrastructure/   # Implementaciones técnicas (Prisma, NATS)
├── interfaces/       # API HTTP, DTOs, controladores
└── frontend/        # Interfaz de usuario React
```

### Capas

1. **Domain**: Entidades del IDS (Host, Event, Rule, Alert) y lógica pura de detección
2. **Application**: Casos de uso y servicios que definen las reglas de negocio
3. **Infrastructure**: Prisma ORM, conexión con NATS, repositorios, persistencia
4. **Interfaces**: API HTTP (Express), controladores, validaciones, workers

## Stack Tecnológico

### Backend
- **Node.js 20** con TypeScript
- **Express** para la API REST
- **Prisma** como ORM
- **PostgreSQL** como base de datos
- **NATS** como message broker
- **NestJS** (parcialmente) para algunos controladores

### Frontend
- **React 18** con TypeScript
- **Vite** como bundler
- **Tailwind CSS** para estilos
- **React Router** para navegación
- **Recharts** para gráficas
- **Axios** para peticiones HTTP

### DevOps
- **Docker** y **Docker Compose**
- **Multi-stage builds** para optimización

## Estructura del Proyecto

```
ProyectoFinal_Backend/
├── src/
│   ├── domain/
│   │   ├── entities/        # Entidades del dominio
│   │   ├── repositories/    # Interfaces de repositorios
│   │   └── services/        # Servicios de dominio
│   ├── application/
│   │   ├── use-cases/      # Casos de uso
│   │   └── token.ts        # Tokens de inyección
│   ├── infrastructure/
│   │   ├── prisma/         # Cliente Prisma
│   │   ├── nats/           # Cliente NATS
│   │   └── repositories/   # Implementaciones de repositorios
│   ├── interfaces/
│   │   ├── http/           # Controladores NestJS
│   │   ├── dto/            # Data Transfer Objects
│   │   ├── filters/        # Filtros de errores
│   │   └── routes/        # Rutas Express
│   ├── services/           # Servicios auxiliares
│   ├── workers/            # Workers de procesamiento
│   ├── app.ts              # Configuración Express
│   ├── app.module.ts       # Módulo NestJS
│   ├── server.ts            # Servidor Express
│   └── main.ts             # Servidor NestJS
├── prisma/
│   ├── schema.prisma       # Esquema de base de datos
│   └── migrations/         # Migraciones
├── frontend/               # Aplicación React
│   └── src/
│       ├── components/     # Componentes React
│       ├── pages/          # Páginas de la aplicación
│       ├── services/       # Servicios API
│       └── App.tsx          # Componente principal
├── Dockerfile              # Build del contenedor unificado
└── docker-compose.yml      # Orquestación de servicios
```

## Configuración del Entorno

### Variables de Entorno

Crea un archivo `.env` en `ProyectoFinal_Backend/`:

```env
# Base de datos
DATABASE_URL="postgresql://postgres:postgres@db:5432/ids?schema=public"

# NATS
NATS_URL="nats://nats:4222"

# Puerto del servidor
PORT=8080

# Entorno
NODE_ENV=production
```

### Base de Datos

El esquema de Prisma define las siguientes entidades:

- **Host**: Hosts monitoreados
- **Event**: Eventos capturados
- **Flow**: Flujos de red
- **Rule**: Reglas de detección
- **Alert**: Alertas generadas
- **Feature**: Características extraídas
- **Score**: Puntuaciones de detección

## Desarrollo Local

### Prerrequisitos

```bash
# Instalar Node.js 20+
# Instalar Docker y Docker Compose
# Instalar Prisma CLI globalmente (opcional)
npm install -g prisma
```

### Setup Inicial

1. **Clonar y configurar**:
```bash
cd ProyectoFinal_Backend
cp .env.example .env  # Si existe
```

2. **Instalar dependencias del backend**:
```bash
npm install
```

3. **Instalar dependencias del frontend**:
```bash
cd ../frontend
npm install
cd ..
```

4. **Configurar base de datos**:
```bash
cd ProyectoFinal_Backend
npx prisma generate
npx prisma migrate dev
```

### Desarrollo con Docker

**Levantar todo el stack**:
```bash
docker compose up --build
```

**Solo servicios de infraestructura** (para desarrollo local):
```bash
docker compose up db nats
```

**Ver logs**:
```bash
docker compose logs -f app
docker compose logs -f detector
```

### Desarrollo sin Docker

1. **Levantar servicios de infraestructura**:
```bash
docker compose up db nats
```

2. **Ejecutar backend**:
```bash
cd ProyectoFinal_Backend
npm run dev
```

3. **Ejecutar frontend** (en otra terminal):
```bash
cd frontend
npm run dev
```

## API Endpoints

### Health Check
```
GET /healthz
```

### Ingest
```
POST /ingest/eve
Body: { host_id: string, events: Array<Event> }
```

### Rules
```
GET /rulesets/                    # Listar todas las reglas
POST /rulesets/rules              # Crear nueva regla
PATCH /rulesets/:id/toggle        # Habilitar/deshabilitar regla
```

### Alerts
```
GET /alerts/?host_id=xxx&since=yyyy-mm-dd  # Listar alertas con filtros
```

## Flujo de Datos

### 1. Ingest de Eventos
```
Cliente → POST /ingest/eve → IngestController
  → IngestEventsUseCase
    → Guarda eventos en DB
    → Publica en NATS (eve.suricata)
```

### 2. Detección
```
NATS (eve.suricata) → DetectorSubscriber
  → DetectCryptojackingUseCase
    → CryptoDetectionService
      → FeatureExtractor
      → Scorer
    → Genera Alertas
    → Guarda en DB
```

### 3. Visualización
```
Frontend → GET /alerts → AlertRouter
  → Prisma → Alertas
```

## Construcción del Contenedor

El Dockerfile utiliza multi-stage build:

1. **Frontend Builder**: Construye la aplicación React
2. **Backend Builder**: Compila TypeScript del backend
3. **Runtime**: Combina ambos y sirve desde Express

### Build Manual

```bash
docker build -t ids-cryptojacking .
```

### Estructura del Contenedor

```
/app
├── dist/          # Backend compilado
├── public/        # Frontend compilado (servido estáticamente)
├── prisma/        # Esquema y migraciones
└── node_modules/  # Dependencias
```

## Testing

### Pruebas Manuales

**Ingest de evento**:
```bash
curl -X POST http://localhost:8080/ingest/eve \
  -H "Content-Type: application/json" \
  -d '{
    "host_id": "test01",
    "events": [{
      "event_type": "tls",
      "tls": {"sni": "pool.minexmr.com"}
    }]
  }'
```

**Listar alertas**:
```bash
curl http://localhost:8080/alerts/
```

**Crear regla**:
```bash
curl -X POST http://localhost:8080/rulesets/rules \
  -H "Content-Type: application/json" \
  -d '{
    "vendor": "suricata",
    "sid": 2000001,
    "name": "Test Rule",
    "body": "alert tls any any -> any any (msg:\"Test\"; sid:2000001;)",
    "tags": ["test"],
    "enabled": true
  }'
```

## Migraciones de Base de Datos

### Crear nueva migración
```bash
npx prisma migrate dev --name nombre_migracion
```

### Aplicar migraciones en producción
```bash
npx prisma migrate deploy
```

### Generar cliente Prisma
```bash
npx prisma generate
```

## Debugging

### Logs del Sistema

```bash
# Todos los servicios
docker compose logs -f

# Servicio específico
docker compose logs -f app
docker compose logs -f detector
docker compose logs -f db
```

### Debug en Desarrollo

**Backend con debugger**:
```json
// .vscode/launch.json
{
  "type": "node",
  "request": "launch",
  "name": "Debug Backend",
  "runtimeExecutable": "npm",
  "runtimeArgs": ["run", "dev"],
  "skipFiles": ["<node_internals>/**"]
}
```

### Inspeccionar Base de Datos

```bash
# Conectar a PostgreSQL
docker compose exec db psql -U postgres -d ids

# O usar Prisma Studio
npx prisma studio
```

## Estructura de Reglas

Las reglas siguen el formato de Suricata/Snort:

```suricata
alert tls any any -> any any (
    msg:"Monero mining pool detected";
    tls.sni;
    content:"pool.minexmr.com";
    sid:2000001;
)
```

## NATS Topics

- `eve.suricata`: Eventos EVE para procesamiento
- Otros topics según la configuración del detector

## Mejoras Futuras

- [ ] Tests unitarios y de integración
- [ ] Autenticación y autorización
- [ ] WebSockets para actualizaciones en tiempo real
- [ ] Exportación de alertas (CSV, JSON)
- [ ] Dashboard con más métricas
- [ ] Integración con Suricata real
- [ ] Sistema de notificaciones

## Troubleshooting

### Error: "Cannot connect to database"
- Verifica que el contenedor `db` esté corriendo
- Revisa `DATABASE_URL` en `.env`
- Verifica que las migraciones se hayan aplicado

### Error: "NATS connection failed"
- Verifica que el contenedor `nats` esté corriendo
- Revisa `NATS_URL` en `.env`

### Frontend no carga
- Verifica que el build del frontend se haya completado
- Revisa que `public/` contenga `index.html`
- Revisa los logs del contenedor `app`

### Alertas no se generan
- Verifica que el worker `detector` esté corriendo
- Revisa los logs: `docker compose logs detector`
- Verifica que las reglas estén habilitadas
- Revisa la conexión a NATS

## Contribuir

1. Crear una rama para la feature
2. Hacer cambios siguiendo la arquitectura limpia
3. Probar localmente
4. Crear Pull Request con descripción clara

## Licencia

[Especificar licencia del proyecto]

