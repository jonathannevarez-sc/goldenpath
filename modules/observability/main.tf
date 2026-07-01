locals {
  display_name = "${var.service_name} ${var.environment}"
}

resource "google_monitoring_dashboard" "service" {
  project = var.project_id

  dashboard_json = jsonencode({
    displayName = "${local.display_name} — Golden Path"
    mosaicLayout = {
      columns = 12
      tiles = [
        {
          width  = 6
          height = 4
          widget = {
            title = "Cloud Run request count"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"cloud_run_revision\" resource.label.service_name=\"${var.cloud_run_service_name}\" metric.type=\"run.googleapis.com/request_count\""
                  }
                }
              }]
            }
          }
        },
        {
          xPos   = 6
          width  = 6
          height = 4
          widget = {
            title = "Cloud Run request latencies (p95)"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"cloud_run_revision\" resource.label.service_name=\"${var.cloud_run_service_name}\" metric.type=\"run.googleapis.com/request_latencies\""
                  }
                }
              }]
            }
          }
        }
      ]
    }
  })
}

resource "google_monitoring_alert_policy" "high_error_rate" {
  project      = var.project_id
  display_name = "${local.display_name} — high 5xx rate"
  combiner     = "OR"

  conditions {
    display_name = "5xx ratio > 5% for 5 min"
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" resource.label.service_name=\"${var.cloud_run_service_name}\" metric.type=\"run.googleapis.com/request_count\" metric.label.response_code_class=\"5xx\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 10
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  notification_channels = []

  alert_strategy {
    auto_close = "1800s"
  }
}