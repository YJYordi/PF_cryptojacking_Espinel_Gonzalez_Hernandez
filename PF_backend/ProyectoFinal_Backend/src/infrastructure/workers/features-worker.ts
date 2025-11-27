import { connectNats, getNats } from "../messaging/nats-client";
import { buildFeaturesFromEveBatch } from "../database/feature-extractor";
import { StringCodec } from "nats";

(async () => {
  await connectNats();
  const sc = StringCodec();
  const sub = getNats().subscribe("eve.suricata");
  console.log("features.worker listening on eve.suricata");

  for await (const m of sub) {
    const payload = JSON.parse(sc.decode(m.data));
    const feats = await buildFeaturesFromEveBatch(payload);
    // opcional: publicar features a otro subject
    getNats().publish("features.flow", sc.encode(JSON.stringify(feats)));
  }
})();

