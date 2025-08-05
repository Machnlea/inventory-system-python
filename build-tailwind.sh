#!/bin/bash

# 构建Tailwind CSS
echo "Building Tailwind CSS..."
npx tailwindcss -i ./app/static/css/tailwind.css -o ./app/static/css/style.css --watch

echo "Tailwind CSS build complete!"