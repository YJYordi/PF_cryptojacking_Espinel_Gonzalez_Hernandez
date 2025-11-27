import { PrismaClient } from "@prisma/client";
const prisma = new PrismaClient();

export async function buildFeaturesFromEveBatch(batch: any) {
  // ejemplo mínimo: extraer JA3, SNI, bytes, 5-tuple, timestamps
  const feats = [];
  for (const e of batch.events) {
    if (e.event_type === "flow" || e.event_type === "tls" || e.event_type === "http") {
      const five = `${e.src_ip}:${e.src_port}-${e.dest_ip}:${e.dest_port}-${e.proto}`;
      const flow = await prisma.flow.upsert({
        where: { id: `${batch.host_id}-${five}-${e.flow_id || e.flow?.id || Date.now()}` },
        update: {
          sni: e.tls?.sni ?? undefined,
          ja3: e.tls?.ja3 ?? undefined,
          bytesIn: e.flow?.bytes_toserver ?? undefined,
          bytesOut: e.flow?.bytes_toclient ?? undefined,
          tsEnd: new Date(e.timestamp || Date.now()),
        },
        create: {
          id: `${batch.host_id}-${five}-${e.flow_id || e.flow?.id || Date.now()}`,
          hostId: batch.host_id,
          fiveTuple: five,
          sni: e.tls?.sni,
          ja3: e.tls?.ja3,
          tsStart: new Date(e.timestamp || Date.now()),
          bytesIn: e.flow?.bytes_toserver || 0,
          bytesOut: e.flow?.bytes_toclient || 0,
        }
      });

      const v = {
        dur: e.flow?.duration || 0,
        pkts_toserver: e.flow?.pkts_toserver || 0,
        pkts_toclient: e.flow?.pkts_toclient || 0,
        ja3: e.tls?.ja3 || null,
        sni: e.tls?.sni || null,
      };

      await prisma.feature.upsert({
        where: { flowId: flow.id },
        update: { v },
        create: { flowId: flow.id, v },
      });
      feats.push({ flowId: flow.id, v });
    }
  }
  return feats;
}

