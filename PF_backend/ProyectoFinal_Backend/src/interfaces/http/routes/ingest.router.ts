import { Router } from "express";
import { z } from "zod";
import { PrismaClient } from "@prisma/client";
import { getNats, sc } from "../../../infrastructure/messaging/nats-client";
import { appendFile, mkdir } from "fs/promises";
import { dirname } from "path";

const prisma = new PrismaClient();
const router = Router();

// Ruta del eve.json (configurable por variable de entorno)
const EVE_JSON_PATH = process.env.EVE_JSON_PATH || "/var/log/suricata/eve.json";

/**
 * Escribe eventos en formato eve.json (una línea JSON por evento)
 * Formato compatible con Suricata para que el pipeline ML los pueda leer
 */
async function writeToEveJson(events: any[]): Promise<void> {
  try {
    // Crear directorio si no existe
    await mkdir(dirname(EVE_JSON_PATH), { recursive: true });

    // Escribir cada evento como una línea JSON (formato eve.json)
    for (const event of events) {
      const jsonLine = JSON.stringify(event) + "\n";
      await appendFile(EVE_JSON_PATH, jsonLine, "utf-8");
    }
  } catch (error) {
    // No fallar si no se puede escribir en eve.json (puede no estar montado)
    console.warn(`[WARNING] No se pudo escribir en ${EVE_JSON_PATH}:`, error);
  }
}

const EveSchema = z.object({
  host_id: z.string(),
  events: z.array(z.record(z.string(), z.unknown())),
});

router.post("/eve", async (req, res, next) => {
  try {
    const data = EveSchema.parse(req.body);
    const hostId = data.host_id;

    
    await prisma.host.upsert({
  where: { id: hostId },
  update: {},
  create: { id: hostId, name: hostId, labels: {} },
});

    
    // Primero guardar los eventos para obtener sus IDs
    const savedEvents = await prisma.$transaction(
      data.events.map((ev: any) =>
        prisma.event.create({
          data: {
            hostId,
            kind: typeof ev.event_type === "string" ? ev.event_type : "eve",
            payload: ev,
          },
        })
      )
    );

    // Publicar a NATS con los IDs de los eventos guardados
    const eventsWithIds = savedEvents.map((savedEvent, index) => ({
      id: savedEvent.id,
      ...data.events[index],
    }));
    
    await getNats().publish("eve.suricata", sc.encode(JSON.stringify({
      host_id: hostId,
      events: eventsWithIds,
    })));

    // Escribir eventos en eve.json para que el pipeline ML los pueda leer
    await writeToEveJson(data.events);

    res.json({ ok: true, n: data.events.length });
  } catch (e) {
    next(e);
  }
});

export default router;

