# IDS Cryptojacking - Sistema de Detección de Intrusiones

## 📋 Descripción del Proyecto

**IDS Cryptojacking** es un Sistema de Detección de Intrusiones (IDS) especializado en la detección de ataques de cryptojacking. El sistema monitorea eventos de red en tiempo real, analiza patrones sospechosos relacionados con minería de criptomonedas y genera alertas automáticas cuando detecta actividad maliciosa.

### Características Principales

- 🔍 **Detección en Tiempo Real**: Analiza eventos de red (TLS, DNS, Flow) para identificar patrones de cryptojacking
- 📊 **Interfaz Web Moderna**: Dashboard interactivo con visualización de alertas, gestión de reglas y monitoreo del sistema
- ⚙️ **Gestión de Reglas**: Sistema flexible para crear, habilitar y deshabilitar reglas de detección (compatible con Suricata/Snort)
- 🚨 **Sistema de Alertas**: Generación automática de alertas con información detallada sobre ataques detectados
- 🏗️ **Arquitectura Limpia**: Implementado siguiendo principios de Clean Architecture para mantenibilidad y escalabilidad
- 🐳 **Dockerizado**: Todo el sistema está containerizado para fácil despliegue y desarrollo

## 🏗️ Arquitectura

El proyecto utiliza **Clean Architecture** con las siguientes capas:

```
ProyectoFinal_Backend/
├── domain/           # Entidades y lógica de negocio pura
├── application/      # Casos de uso y servicios de aplicación
├── infrastructure/   # Implementaciones técnicas (Prisma, NATS)
├── interfaces/       # API HTTP, DTOs, controladores
└── frontend/         # Interfaz de usuario React
```

### Flujo de Datos

1. **Ingest**: Los eventos EVE (Suricata) se envían al sistema vía API REST
2. **Procesamiento**: Los eventos se almacenan en PostgreSQL y se publican en NATS
3. **Detección**: Un worker suscrito a NATS analiza los eventos contra reglas activas
4. **Alertas**: Cuando se detecta un patrón, se genera una alerta y se almacena en la base de datos
5. **Visualización**: La interfaz web muestra las alertas en tiempo real

## 🛠️ Stack Tecnológico

### Backend
- **Node.js 20** con TypeScript
- **Express** para la API REST
- **NestJS** para inyección de dependencias y módulos
- **Prisma** como ORM
- **PostgreSQL** como base de datos
- **NATS** como message broker para procesamiento asíncrono

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

## 🚀 Inicio Rápido

### Requisitos Previos

- Docker y Docker Compose instalados
- Navegador web moderno

### Instalación y Ejecución

1. **Clonar el repositorio** (si aplica)

2. **Levantar el sistema completo**:
```bash
cd ProyectoFinal_Backend
docker compose up --build
```

3. **Acceder a la interfaz web**:
```
http://localhost:8080
```

El sistema levantará automáticamente:
- **PostgreSQL** (puerto 5432)
- **NATS** (puerto 4222)
- **Aplicación Backend + Frontend** (puerto 8080)
- **Worker de Detección**

## 📖 Documentación

- **[Manual de Usuario](README_USUARIO.md)**: Guía completa para usuarios finales
- **[Manual de Desarrollador](README_DEVELOPER.md)**: Documentación técnica para desarrolladores

## 🎯 Funcionalidades

### Dashboard
Vista general del sistema con estadísticas en tiempo real:
- Total de alertas
- Reglas activas
- Alertas de las últimas 24 horas
- Lista de alertas recientes

### Gestión de Alertas
- Visualización detallada de alertas
- Filtros por host y fecha
- Información técnica completa (SID, mensajes Suricata, detalles de red)

### Gestión de Reglas
- Crear nuevas reglas de detección
- Habilitar/deshabilitar reglas existentes
- Compatible con formato Suricata/Snort

### Ingest de Eventos
- Formulario para enviar eventos EVE
- Simulación de ataques desde el navegador
- Soporte para múltiples eventos en una sola petición

### Monitoreo de Rendimiento
- Gráficas de CPU, memoria, red y disco
- Actualización en tiempo real

## 🔧 Desarrollo

Para más información sobre desarrollo, configuración del entorno, estructura del código y API endpoints, consulta el [Manual de Desarrollador](README_DEVELOPER.md).

## 📝 Ejemplo de Uso

### Simular un Ataque de Cryptojacking

1. Accede a la pestaña **Ingest** en la interfaz web
2. Ingresa un Host ID (ej: `flarevm01`)
3. Ingresa un evento EVE con un patrón de cryptojacking:

```json
[
  {
    "event_type": "tls",
    "tls": {
      "sni": "pool.minexmr.com"
    }
  }
]
```

4. Haz clic en "Ingerir Eventos"
5. Ve a la pestaña **Alertas** para ver la alerta generada automáticamente

## 🧪 Pruebas

### Prueba con cURL

```bash
# Ingerir evento de cryptojacking
curl -X POST http://localhost:8080/ingest/eve \
  -H "Content-Type: application/json" \
  -d '{
    "host_id": "flarevm01",
    "events": [{
      "event_type": "tls",
      "tls": {"sni": "pool.minexmr.com"}
    }]
  }'

# Listar alertas
curl http://localhost:8080/alerts/

# Listar reglas
curl http://localhost:8080/rulesets/
```

## 🏛️ Estructura del Proyecto

```
PF_backend/
├── ProyectoFinal_Backend/
│   ├── src/
│   │   ├── domain/              # Entidades y lógica de negocio
│   │   ├── application/          # Casos de uso
│   │   ├── infrastructure/       # Prisma, NATS, repositorios
│   │   ├── interfaces/           # API HTTP, controladores
│   │   ├── workers/              # Workers de procesamiento
│   │   └── app.ts                # Configuración Express
│   ├── prisma/
│   │   ├── schema.prisma         # Esquema de base de datos
│   │   └── migrations/           # Migraciones
│   ├── frontend/                 # Aplicación React
│   ├── Dockerfile                # Build unificado
│   └── docker-compose.yml        # Orquestación
├── README.md                      # Este archivo
├── README_USUARIO.md             # Manual de usuario
└── README_DEVELOPER.md           # Manual de desarrollador
```

## 🔒 Seguridad

- El sistema está diseñado para entornos de desarrollo y demostración
- Las alertas se generan automáticamente cuando se detectan patrones de cryptojacking
- Las reglas de detección son configurables y pueden ser habilitadas/deshabilitadas según necesidad

## 📊 Patrones Detectados

El sistema puede detectar:
- Conexiones a pools de minería conocidos (Monero, etc.)
- Patrones DNS sospechosos relacionados con cryptojacking
- Tráfico TLS hacia dominios de minería
- Patrones genéricos de actividad de minería

## 🤝 Contribución

Para contribuir al proyecto:
1. Revisa la arquitectura en el [Manual de Desarrollador](README_DEVELOPER.md)
2. Sigue los principios de Clean Architecture
3. Asegúrate de que los tests pasen
4. Documenta tus cambios

## 📄 Licencia

[Especificar licencia del proyecto]

## 👥 Autores

[Especificar autores del proyecto]

---

**Nota**: Este proyecto es un sistema de detección de intrusiones especializado en cryptojacking, diseñado para demostración y desarrollo. Para uso en producción, se recomienda implementar medidas de seguridad adicionales.

