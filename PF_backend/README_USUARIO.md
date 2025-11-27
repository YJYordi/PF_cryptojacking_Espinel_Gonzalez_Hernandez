# Manual de Usuario - IDS Cryptojacking

## 📋 Descripción General

Este sistema es una interfaz de usuario para un **IDS (Sistema de Detección de Intrusiones)** especializado en detectar ataques de **cryptojacking**. Permite monitorear, gestionar reglas de detección, visualizar alertas y simular ataques desde el navegador.

El sistema analiza eventos de red en tiempo real y genera alertas automáticamente cuando detecta patrones relacionados con minería de criptomonedas no autorizada.

## ✅ Requisitos Previos

- **Docker** y **Docker Compose** instalados
- **Navegador web moderno** (Chrome, Firefox, Edge, Safari)
- **4GB de RAM** mínimo recomendado

## 🚀 Inicio Rápido

### 1. Levantar el Sistema

Desde el directorio `ProyectoFinal_Backend`, ejecuta:

```bash
docker compose up --build
```

Esto levantará todos los servicios necesarios:
- **Base de datos PostgreSQL** (puerto 5432)
- **Servidor NATS** (puerto 4222)
- **Aplicación Backend + Frontend unificados** (puerto 8080)
- **Worker de detección**

### 2. Acceder a la Interfaz

Una vez que todos los contenedores estén corriendo (puede tardar 1-2 minutos en la primera ejecución), abre tu navegador en:

```
http://localhost:8080
```

Verás la interfaz principal con el Dashboard.

## 📑 Guía de Uso por Pestañas

### 🏠 Dashboard

**Propósito**: Vista general del estado del sistema

**Información mostrada**:
- **Total de Alertas**: Número total de alertas detectadas en el sistema
- **Reglas Activas**: Cantidad de reglas habilitadas (de total de reglas configuradas)
- **Alertas (24h)**: Alertas generadas en las últimas 24 horas
- **Estado**: Estado operativo del sistema
- **Alertas Recientes**: Lista de las 5 alertas más recientes con:
  - Severidad (high/medium/low) con código de colores
  - Host ID donde se detectó el ataque
  - Tipo de evento (TLS, DNS, Flow)
  - Fecha y hora de detección

**Actualización**: Se actualiza automáticamente cada 30 segundos

**Uso típico**: Revisa el Dashboard para obtener una vista rápida del estado de seguridad del sistema.

---

### 🚨 Alertas

**Propósito**: Visualización detallada y gestión de alertas de seguridad

#### Filtros Disponibles:
- **Host ID**: Filtrar alertas por host específico (ej: `flarevm01`, `remnux01`)
- **Desde (fecha)**: Filtrar alertas desde una fecha/hora específica (formato: YYYY-MM-DD)
- **Limpiar Filtros**: Botón para restablecer todos los filtros

#### Información de cada Alerta:
- **ID de Alerta**: Identificador único de la alerta
- **Severidad**: Nivel de amenaza (high/medium/low) con código de colores:
  - 🔴 **High**: Amenaza crítica
  - 🟡 **Medium**: Amenaza moderada
  - 🟢 **Low**: Amenaza baja
- **Detección de Suricata**:
  - **SID (Signature ID)**: Identificador de la regla que disparó la alerta
  - **Mensaje**: Descripción del ataque detectado
  - **Nombre de Regla**: Nombre descriptivo de la regla que detectó el patrón
- **Información de Red**:
  - **IP y Puerto de Origen**: Origen del tráfico sospechoso
  - **IP y Puerto de Destino**: Destino del tráfico (puede ser un pool de minería)
  - **Protocolo**: TCP, UDP, etc.
- **Detalles TLS/DNS**: Información específica según el tipo de evento:
  - **TLS**: SNI (Server Name Indication), versión TLS, cipher
  - **DNS**: Nombre de dominio resuelto, tipo de registro
- **Información de Detección**:
  - **Confianza**: Porcentaje de confianza de la detección (0-1)
  - **Tipo**: Tipo de ataque detectado (cryptojacking, suspicious_activity, etc.)
  - **Indicadores**: Lista de indicadores de amenaza encontrados

**Acciones**:
- **Botón "Actualizar"**: Recargar la lista de alertas manualmente
- **Click en una alerta**: Expandir para ver todos los detalles técnicos

**Uso típico**: Revisa las alertas para investigar ataques detectados, usa los filtros para encontrar alertas específicas de un host o período de tiempo.

---

### ⚙️ Reglas

**Propósito**: Gestión de reglas de detección de cryptojacking

#### Crear Nueva Regla:
1. Haz clic en el botón **"Nueva Regla"** (arriba a la derecha)
2. Completa el formulario:
   - **Vendor**: Selecciona `Suricata` o `Snort`
   - **SID**: Número de identificación de la regla (debe ser único, ej: 2000001)
   - **Nombre**: Nombre descriptivo de la regla (ej: "Monero Mining Pool Detection")
   - **Cuerpo de la Regla**: Código completo de la regla en formato Suricata/Snort
   - **Tags**: Etiquetas separadas por comas (ej: `cryptojacking, mining, xmr`)
   - **Habilitada**: Checkbox para activar/desactivar la regla al crearla
3. Haz clic en **"Crear Regla"**

#### Ejemplo de Regla:
```suricata
alert tls any any -> any any (
    msg:"Monero mining pool detected";
    tls.sni;
    content:"pool.minexmr.com";
    sid:2000001;
)
```

#### Información de cada Regla:
- **Nombre o patrón**: Nombre descriptivo de la regla
- **Estado**: Activa (verde) o Inactiva (gris)
- **Vendor**: Suricata o Snort
- **SID**: Signature ID único
- **Tags**: Etiquetas asociadas para categorización
- **Cuerpo completo**: Código completo de la regla
- **Fecha de creación**: Cuándo fue creada la regla

#### Acciones:
- **Toggle (Interruptor)**: Botón para habilitar/deshabilitar reglas individuales
  - Solo las reglas **habilitadas** se usan para detectar ataques
  - Puedes deshabilitar temporalmente una regla sin eliminarla
- **Actualizar**: Recargar la lista de reglas

**Uso típico**: Crea reglas personalizadas para detectar nuevos patrones de cryptojacking o modifica el estado de reglas existentes según tus necesidades.

---

### 📤 Ingest

**Propósito**: Simular ataques desde el navegador para probar el sistema

#### Cómo Simular un Ataque:

1. **Ingresa el Host ID**: Identificador del host donde se detecta el evento (ej: `flarevm01`, `remnux01`, `test-host`)

2. **Ingresa los Eventos**: Array JSON de eventos EVE (formato Suricata). Puedes usar el botón **"Cargar Ejemplo"** para ver un ejemplo.

3. **Haz clic en "Ingerir Eventos"**

4. **Resultado**: 
   - Si se detecta un patrón de cryptojacking, el sistema generará alertas automáticamente
   - Verás un mensaje de éxito indicando cuántos eventos se procesaron
   - Ve a la pestaña **"Alertas"** para ver las alertas generadas

#### Ejemplos de Ataques:

**Ataque Monero Pool (TLS)**:
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

**Ataque SupportXMR (DNS)**:
```json
[
  {
    "event_type": "dns",
    "dns": {
      "rrname": "supportxmr.com"
    }
  }
]
```

**Múltiples Ataques**:
```json
[
  {
    "event_type": "dns",
    "dns": { "rrname": "supportxmr.com" }
  },
  {
    "event_type": "tls",
    "tls": { "sni": "pool.minexmr.com" }
  }
]
```

**Ataque con Información de Red Completa**:
```json
[
  {
    "event_type": "tls",
    "src_ip": "192.168.1.100",
    "src_port": 54321,
    "dest_ip": "185.71.65.238",
    "dest_port": 443,
    "proto": "TCP",
    "tls": {
      "sni": "pool.minexmr.com",
      "version": "TLS 1.2"
    }
  }
]
```

#### Patrones Detectados Automáticamente:
- `pool.minexmr.com` → SID 2000001 (Monero Mining Pool)
- `supportxmr.com` → SID 2000002 (SupportXMR Pool)
- `hashvault.pro` → SID 2000003 (HashVault Pool)
- Patrones genéricos de mining → SID 2000005

**Uso típico**: Usa esta pestaña para probar el sistema, simular ataques y verificar que las reglas funcionan correctamente.

---

### 📊 Rendimiento

**Propósito**: Monitoreo en tiempo real de recursos del sistema

**Nota**: Los datos mostrados en esta pestaña son **simulados** para demostración. En una implementación de producción, estos datos provendrían del sistema operativo.

#### Métricas Mostradas:
- **CPU**: Porcentaje de uso del procesador (0-100%)
- **Memoria**: Porcentaje de uso de memoria RAM (0-100%)
- **Red (Entrada)**: Velocidad de datos entrantes (MB/s)
- **Red (Salida)**: Velocidad de datos salientes (MB/s)
- **Disco (Lectura)**: Velocidad de lectura de disco (MB/s)
- **Disco (Escritura)**: Velocidad de escritura de disco (MB/s)

#### Gráficas:
1. **Uso de CPU**: Gráfica de área mostrando el uso de CPU en el tiempo
2. **Uso de Memoria**: Gráfica de área mostrando el uso de memoria
3. **Tráfico de Red**: Gráfica de líneas mostrando entrada y salida simultáneamente
4. **I/O de Disco**: Gráfica de barras mostrando lectura y escritura

**Actualización**: Las métricas se actualizan automáticamente cada 2 segundos

**Uso típico**: Monitorea el rendimiento del sistema para identificar posibles problemas de recursos o actividad inusual.

---

## 🔄 Flujo de Trabajo Típico

### 1. Configurar Reglas
1. Ve a la pestaña **"Reglas"**
2. Revisa las reglas predefinidas o crea nuevas según tus necesidades
3. Verifica que las reglas que quieres usar estén **habilitadas** (toggle activo)

### 2. Simular Ataques
1. Ve a la pestaña **"Ingest"**
2. Ingresa un Host ID (ej: `test-host`)
3. Ingresa eventos que contengan patrones de cryptojacking (usa los ejemplos proporcionados)
4. Envía los eventos haciendo clic en **"Ingerir Eventos"**

### 3. Revisar Alertas
1. Ve a la pestaña **"Alertas"**
2. Las alertas generadas aparecerán automáticamente
3. Usa los filtros para encontrar alertas específicas:
   - Filtra por Host ID para ver alertas de un host específico
   - Filtra por fecha para ver alertas de un período
4. Haz clic en una alerta para ver todos los detalles técnicos

### 4. Monitorear el Sistema
1. Ve al **"Dashboard"** para una vista general del estado
2. Revisa **"Rendimiento"** para monitorear recursos del sistema
3. Verifica que el sistema esté operativo y procesando eventos correctamente

---

## 🔧 Solución de Problemas

### El sistema no inicia
- **Verifica que Docker esté corriendo**: `docker ps`
- **Revisa los logs**: `docker compose logs`
- **Asegúrate de que los puertos no estén en uso**: 8080, 5432, 4222
- **Revisa que tengas suficiente memoria**: El sistema requiere al menos 2GB de RAM disponible

### No aparecen alertas
- **Verifica que las reglas estén habilitadas**: Ve a la pestaña "Reglas" y asegúrate de que al menos una regla tenga el toggle activo
- **Revisa que los eventos contengan patrones detectables**: Usa los ejemplos proporcionados en la pestaña "Ingest"
- **Consulta los logs del detector**: `docker compose logs detector`
- **Verifica que el worker de detección esté corriendo**: `docker compose ps`

### La interfaz no carga
- **Verifica que el contenedor `app` esté corriendo**: `docker compose ps`
- **Revisa que puedas acceder a `http://localhost:8080`**
- **Revisa los logs**: `docker compose logs app`
- **Espera unos minutos**: En la primera ejecución, el sistema puede tardar en compilar

### Las alertas no se actualizan
- **Refresca la página manualmente** (F5)
- **Haz clic en el botón "Actualizar"** en la pestaña de Alertas
- **Verifica la conexión a la base de datos**: `docker compose logs db`

### Error al crear reglas
- **Verifica que el SID sea único**: No puede haber dos reglas con el mismo SID
- **Revisa el formato de la regla**: Debe seguir el formato Suricata/Snort válido
- **Asegúrate de que todos los campos estén completos**

---

## 📝 Notas Importantes

- ✅ El sistema detecta automáticamente patrones de cryptojacking en los eventos enviados
- ✅ Las alertas se generan en tiempo real cuando se detectan ataques
- ⚠️ Las métricas de rendimiento son **simuladas** para demostración
- ⚠️ El sistema está diseñado para un entorno de desarrollo/demostración
- ✅ Todas las demás funcionalidades (Dashboard, Alertas, Reglas, Ingest) usan **datos reales** del backend

---

## 🆘 Soporte

Para más información técnica sobre la arquitectura, configuración avanzada y desarrollo, consulta el **[Manual de Desarrollador](README_DEVELOPER.md)**.

---

## 📚 Recursos Adicionales

- **Formato de Reglas Suricata**: [Documentación oficial de Suricata](https://suricata.readthedocs.io/)
- **Formato EVE**: [Formato de eventos EVE de Suricata](https://suricata.readthedocs.io/en/latest/output/eve/eve-json-output.html)

---

**Última actualización**: 2024
