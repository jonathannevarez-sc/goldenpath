import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    status: "ok",
    service: process.env.SERVICE_NAME ?? "{{SERVICE_NAME}}",
    environment: process.env.ENVIRONMENT ?? "unknown",
  });
}