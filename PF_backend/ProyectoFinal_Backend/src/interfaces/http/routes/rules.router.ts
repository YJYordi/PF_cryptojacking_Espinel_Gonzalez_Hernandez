import { Router } from "express";
import { PrismaClient } from "@prisma/client";
import { z } from "zod";
const prisma = new PrismaClient();
const router = Router();

const RuleBody = z.object({
  vendor: z.enum(["suricata","snort"]),
  sid: z.number(),
  name: z.string(),
  body: z.string(),
  tags: z.array(z.string()).default([]),
  enabled: z.boolean().default(true),
});

router.get("/", async (_req, res) => {
  const rules = await prisma.rule.findMany({
    orderBy: { createdAt: 'desc' },
  });
  // Serializar fechas explícitamente para asegurar compatibilidad con el frontend
  const serializedRules = rules.map(rule => ({
    ...rule,
    createdAt: rule.createdAt.toISOString(),
  }));
  res.json(serializedRules);
});

router.post('/rules', async (req, res) => {
  const { vendor, sid, name, body, tags, pattern } = req.body;

  const data = {
    vendor,
    sid,
    name,
    body,
    tags,
    enabled: true,
    type: 'DOMAIN_IOC',                   // obligatorio en Prisma
    pattern: pattern ?? name ?? body ?? 'unknown',   // Usar pattern si está presente, sino name o body
  };

  const rule = await prisma.rule.create({ data });
  // Serializar fecha explícitamente
  res.json({
    ...rule,
    createdAt: rule.createdAt.toISOString(),
  });
});


router.patch("/:id/toggle", async (req, res) => {
  const { id } = req.params;
  // Obtener el estado actual y alternarlo
  const current = await prisma.rule.findUnique({ where: { id }, select: { enabled: true } });
  if (!current) {
    return res.status(404).json({ error: "Rule not found" });
  }
  const r = await prisma.rule.update({ 
    where: { id }, 
    data: { enabled: !current.enabled }
  });
  // Serializar fecha explícitamente
  res.json({
    ...r,
    createdAt: r.createdAt.toISOString(),
  });
});

// Eliminar reglas generadas automáticamente (con tag 'auto-generated')
router.delete("/auto-generated", async (_req, res) => {
  try {
    const result = await prisma.rule.deleteMany({
      where: {
        tags: {
          has: 'auto-generated'
        }
      }
    });
    res.json({ 
      ok: true, 
      deleted: result.count,
      message: `Se eliminaron ${result.count} reglas generadas automáticamente`
    });
  } catch (error) {
    res.status(500).json({ error: "Error al eliminar reglas", details: String(error) });
  }
});

// Eliminar una regla específica por ID
router.delete("/:id", async (req, res) => {
  const { id } = req.params;
  try {
    await prisma.rule.delete({ where: { id } });
    res.json({ ok: true, message: "Regla eliminada exitosamente" });
  } catch (error) {
    res.status(404).json({ error: "Regla no encontrada" });
  }
});

export default router;

