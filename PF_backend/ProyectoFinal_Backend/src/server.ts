import app from "./app";
import { PORT } from "./infrastructure/config";
import { connectNats } from "./infrastructure/messaging/nats-client";
import { execSync } from "child_process";
import path from "path";

async function runSeed() {
  try {
    console.log("Running database seed...");
    // Resolver paths absolutos desde el directorio raíz de la app
    const appRoot = path.resolve(__dirname, "..");
    const seedPath = path.join(appRoot, "prisma", "seed.ts");
    const tsConfigPath = path.join(appRoot, "prisma", "tsconfig.prisma.json");
    
    // Ejecutar desde el directorio raíz para que los paths relativos funcionen
    execSync(`npx ts-node --project ${tsConfigPath} ${seedPath}`, {
      stdio: "inherit",
      cwd: appRoot, // Cambiar al directorio raíz
      env: { ...process.env, DATABASE_URL: process.env.DATABASE_URL || "postgresql://postgres:postgres@localhost:5432/ids" },
    });
    console.log("Seed completed successfully");
  } catch (error) {
    console.warn("Seed failed or already executed:", error);
    // No fallar el servidor si el seed falla
  }
}

(async () => {
  // Ejecutar seed solo en desarrollo o si está configurado
  if (process.env.NODE_ENV !== "production" || process.env.RUN_SEED === "true") {
    await runSeed();
  }
  await connectNats();
  app.listen(PORT, () => console.log(`API on :${PORT}`));
})();
