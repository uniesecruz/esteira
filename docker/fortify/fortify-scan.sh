#!/bin/bash
# Fortify SCA scan script
# Falls back to Bandit if Fortify is not installed

set -e

echo "============================================================"
echo "Security Static Analysis"
echo "============================================================"

if command -v sourceanalyzer &> /dev/null; then
    echo "[Fortify SCA] Running static analysis..."
    sourceanalyzer -b esteira -clean
    sourceanalyzer -b esteira src/**/*.py
    sourceanalyzer -b esteira -scan -f /opt/fortify/data/fortify-results.fpr

    echo "[Fortify SCA] Results saved to /opt/fortify/data/fortify-results.fpr"

    if [ -n "$FORTIFY_SSC_URL" ] && [ -n "$FORTIFY_SSC_TOKEN" ]; then
        echo "[Fortify SSC] Uploading results..."
        fortifyclient \
            -url "$FORTIFY_SSC_URL" \
            -authtoken "$FORTIFY_SSC_TOKEN" \
            uploadFPR \
            -file /opt/fortify/data/fortify-results.fpr \
            -project "esteira-ml-pipeline" \
            -version "1.0"
    fi
else
    echo "[Fortify SCA] Not installed. Running Bandit as fallback..."
    echo ""
    echo "To use Fortify SCA:"
    echo "  1. Obtain a license from OpenText"
    echo "  2. Install Fortify SCA in the container"
    echo "  3. Rebuild: docker compose build fortify"
    echo ""

    echo "[Bandit] Running Python security analysis..."
    bandit -r src/ -f json -o /opt/fortify/data/bandit-report.json || true
    bandit -r src/ --severity-level medium

    echo ""
    echo "[Bandit] JSON report: /opt/fortify/data/bandit-report.json"
fi

echo "============================================================"
echo "Security analysis complete"
echo "============================================================"
