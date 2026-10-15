#!/usr/bin/env bash
# prep_demo.sh: Prepares and resets the OpenShift environment for a clean demonstration run.
set -euo pipefail

OC_BIN="${OC_BIN:-$(which oc 2>/dev/null || echo "$HOME/.local/bin/oc")}"

if ! command -v "$OC_BIN" &>/dev/null; then
  echo "Error: 'oc' CLI not found. Please ensure oc is in PATH or set OC_BIN."
  exit 1
fi

PROJECT="$("$OC_BIN" project -q 2>/dev/null || echo "")"
if [ -z "$PROJECT" ]; then
  echo "Error: No active OpenShift project. Please run: oc project <your-project>"
  exit 1
fi

echo "================================================================================"
echo " Preparing Enterprise Edge Data Triage Demo"
echo " OpenShift Project: $PROJECT"
echo "================================================================================"

echo "[1/4] Cleaning previous simulator job..."
"$OC_BIN" delete job fleet-telemetry-simulator --ignore-not-found 2>/dev/null || true

echo "[2/4] Resetting raw ingest and curated storage pools..."
WORKER_POD="$("$OC_BIN" get pods -l app.kubernetes.io/component=triage-worker -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")"

if [ -n "$WORKER_POD" ]; then
  "$OC_BIN" exec "$WORKER_POD" -- sh -c "rm -rf /mnt/raw_ingest/* /mnt/gds_curated/*" 2>/dev/null || true
  echo "      Cleared /mnt/raw_ingest and /mnt/gds_curated on $WORKER_POD."
else
  echo "      Warning: No worker pod found yet. Storage reset skipped."
fi

echo "[3/4] Resetting triage engine metrics and restarting worker..."
"$OC_BIN" rollout restart deployment/edge-triage-worker
"$OC_BIN" rollout status deployment/edge-triage-worker --timeout=60s

echo "[4/4] Retrieving live Web Dashboard URL..."
ROUTE_HOST="$("$OC_BIN" get route edge-triage-dashboard -o jsonpath='{.spec.host}' 2>/dev/null || echo "")"
if [ -n "$ROUTE_HOST" ]; then
  DASH_URL="https://$ROUTE_HOST"
else
  DASH_URL="http://localhost:8080 (via oc port-forward svc/edge-triage-metrics 8080:8080)"
fi

echo "================================================================================"
echo " Environment Ready for Live Demonstration!"
echo ""
echo " Live Web Dashboard: $DASH_URL"
echo ""
echo " Next Steps for Presenter:"
echo " 1. Open the dashboard in your web browser side-by-side with your terminal:"
echo "    $DASH_URL"
echo ""
echo " 2. Start the live dual-stream log viewer:"
echo "    python3 demo/scripts/stream_demo.py"
echo ""
echo " 3. In another terminal window, launch the 100-event haul truck simulator:"
echo "    oc apply -f demo/k8s/05_simulator_job.yaml"
echo "================================================================================"
