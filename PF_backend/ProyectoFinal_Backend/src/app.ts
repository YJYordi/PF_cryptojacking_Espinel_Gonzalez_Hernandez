import express from "express";
import helmet from "helmet";
import morgan from "morgan";
import path from "path";
import fs from "fs";
import ingestRouter from "./interfaces/http/routes/ingest.router";
import rulesRouter from "./interfaces/http/routes/rules.router";
import alertsRouter from "./interfaces/http/routes/alert.router";
import performanceRouter from "./interfaces/http/routes/performance.router";

const app = express();
app.use(helmet());
app.use(express.json({ limit: "10mb" }));
app.use(morgan("dev"));

// API Routes
app.use("/ingest", ingestRouter);
app.use("/rulesets", rulesRouter);
app.use("/alerts", alertsRouter);
app.use("/performance", performanceRouter);

app.get("/healthz", (_req, res) => res.json({ ok: true }));

// Servir archivos estáticos del frontend (si existe la carpeta public)
// __dirname será /app/dist cuando se ejecute, entonces public está en /app/public
const publicPath = path.resolve(__dirname, "../public");
const publicExists = fs.existsSync(publicPath);

if (publicExists) {
  app.use(express.static(publicPath));
}

// SPA fallback: todas las rutas no-API van al index.html (solo si existe)
// IMPORTANTE: Debe ir después de las rutas de API y archivos estáticos
// En Express 5, usar middleware en lugar de app.get("/*") que causa error con path-to-regexp
app.use((req, res, next) => {
  // No servir index.html para rutas de API
  if (req.path.startsWith("/ingest") || 
      req.path.startsWith("/rulesets") || 
      req.path.startsWith("/alerts") || 
      req.path.startsWith("/performance") ||
      req.path.startsWith("/healthz")) {
    return next();
  }
  // Si ya se manejó la petición (archivo estático encontrado), no hacer nada
  if (res.headersSent) {
    return;
  }
  // Si existe la carpeta public y el index.html, servir el SPA
  if (publicExists) {
    const indexPath = path.join(publicPath, "index.html");
    if (fs.existsSync(indexPath)) {
      return res.sendFile(indexPath, (err) => {
        if (err) {
          next(err);
        }
      });
    }
  }
  // Si no hay frontend, devolver 404 para rutas no-API
  res.status(404).json({ error: "Not found" });
});

export default app;
