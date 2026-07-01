import express from "express";

const app = express();
const port = Number(process.env.PORT || 3000);

app.get("/api/health", (_req, res) => {
  res.json({
    status: "ok",
    service: process.env.SERVICE_NAME || "{{SERVICE_NAME}}",
    environment: process.env.ENVIRONMENT || "unknown",
  });
});

app.get("/", (_req, res) => {
  res.json({ message: "Hello from Golden Path Express" });
});

app.listen(port, () => {
  console.log(`listening on ${port}`);
});