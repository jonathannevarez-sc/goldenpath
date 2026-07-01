output "url" {
  description = "Cloud Run service base URL (health at /health; MCP clients use mcp_url)"
  value       = module.cloud_run.uri
}

output "mcp_url" {
  description = "MCP streamable-http endpoint for remote clients (Cloud Run)"
  value       = "${module.cloud_run.uri}/mcp"
}

output "sse_url" {
  description = "Legacy SSE path (may return 421 behind Cloud Run LB — prefer mcp_url)"
  value       = "${module.cloud_run.uri}/sse"
}

output "health_url" {
  value = "${module.cloud_run.uri}/health"
}

output "mcp_api_key" {
  description = "Bearer token or X-MCP-API-Key for MCP clients (save securely)"
  value       = data.google_secret_manager_secret_version.mcp_api_key.secret_data
  sensitive   = true
}

output "service_account" {
  value = module.identity.email
}