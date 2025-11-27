import { connect, StringCodec } from "nats";

const sc = StringCodec();
const IOC_SNIS = [
  "minexmr", "miningpoolhub", "pool", "xmr", "nanopool",
  "hashvault", "supportxmr", "monero", "stratum"
];

(async () => {
  const nc = await connect({ servers: "nats://nats:4222" });
  console.log("[detector] conectado a NATS, escuchando eve.suricata");

  const sub = nc.subscribe("eve.suricata");
  for await (const m of sub) {
    const data = JSON.parse(sc.decode(m.data)); // { host_id, events: [...] }
    const alerts: any[] = [];

    for (const ev of data.events) {
      const sni = ev?.tls?.sni?.toLowerCase?.() || "";
      const hit = IOC_SNIS.find(k => sni.includes(k));
      if (hit) {
        const alert = {
          host_id: data.host_id,
          kind: ev.event_type || "eve",
          reason: `SNI sospechoso (${sni}) por IOC="${hit}"`,
          ts: new Date().toISOString()
        };
        alerts.push(alert);
        // publica alerta
        nc.publish("alerts.detector", sc.encode(JSON.stringify(alert)));
      }
    }

    if (alerts.length) {
      console.log(`[detector] ${alerts.length} alerta(s) emitidas`);
    }
  }
})();

