#!/bin/bash
# Test Roboflow API directly
# Usage: ./test_roboflow.sh [image_path]

IMAGE="${1:-test.jpg}"
API_KEY="9bV8sIpOxb79beiXxskn"
MODEL="residuos-reciclaje"
VERSION="1"

if [ ! -f "$IMAGE" ]; then
    echo "Error: No se encuentra la imagen $IMAGE"
    echo "Proporciona una ruta a una imagen JPG: ./test_roboflow.sh /ruta/a/imagen.jpg"
    exit 1
fi

echo "Enviando $IMAGE a Roboflow..."
curl -s -X POST \
    "https://detect.roboflow.com/${MODEL}/${VERSION}?api_key=${API_KEY}" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    --data-urlencode "image@${IMAGE}" | jq . 2>/dev/null || \
    curl -s -X POST \
    "https://detect.roboflow.com/${MODEL}/${VERSION}?api_key=${API_KEY}" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    --data-urlencode "image@${IMAGE}"
