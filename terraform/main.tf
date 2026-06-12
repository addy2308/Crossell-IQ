provider "kubernetes" {
  config_path = "~/.kube/config"
}

resource "kubernetes_namespace" "crosssell" {
  metadata {
    name = "crosssell-iq"
  }
}

resource "kubernetes_deployment" "api" {
  metadata {
    name      = "crosssell-api"
    namespace = kubernetes_namespace.crosssell.metadata[0].name
  }
  spec {
    replicas = 3
    selector {
      match_labels = { app = "crosssell-api" }
    }
    template {
      metadata {
        labels = { app = "crosssell-api" }
      }
      spec {
        container {
          name  = "api"
          image = "crosssell-iq:latest"
          port {
            container_port = 8000
          }
        }
      }
    }
  }
}

resource "kubernetes_horizontal_pod_autoscaler" "api_hpa" {
  metadata {
    name      = "crosssell-api-hpa"
    namespace = kubernetes_namespace.crosssell.metadata[0].name
  }
  spec {
    scale_target_ref {
      api_version = "apps/v1"
      kind        = "Deployment"
      name        = kubernetes_deployment.api.metadata[0].name
    }
    min_replicas = 3
    max_replicas = 10
    target_cpu_utilization_percentage = 70
  }
}
