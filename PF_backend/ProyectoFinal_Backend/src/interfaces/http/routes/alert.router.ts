// src/interfaces/http/routes/alert.router.ts
import { Router } from "express";
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();
const router = Router();

router.get("/", async (req, res) => {
  const { host_id, since } = req.query as { host_id?: string; since?: string };
  const where: any = {};

  if (since) {
    where.createdAt = { gte: new Date(String(since)) };
  }

  // Filtrar por host_id a través de la relación con Event
  if (host_id) {
    where.event = {
      hostId: String(host_id),
    };
  }

  const alerts = await prisma.alert.findMany({
    where,
    orderBy: { createdAt: "desc" },
    take: 100,
    include: { event: true },   // 👈 nombre correcto de la relación
  });

  // Serializar fechas explícitamente
  const serializedAlerts = alerts.map(alert => ({
    ...alert,
    createdAt: alert.createdAt.toISOString(),
    event: alert.event ? {
      ...alert.event,
      ts: alert.event.ts.toISOString(),
    } : null,
  }));
  res.json(serializedAlerts);
});

export default router;

