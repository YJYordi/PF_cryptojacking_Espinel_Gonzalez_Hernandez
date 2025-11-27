import { connect, NatsConnection, StringCodec } from "nats";
import { NATS_URL } from "../config";

let nc: NatsConnection;
export const sc = StringCodec();

export async function connectNats() {
  nc = await connect({ servers: NATS_URL });
  console.log("NATS connected");
}

export function getNats() { 
  return nc; 
}

