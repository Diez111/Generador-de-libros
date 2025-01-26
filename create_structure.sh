#!/bin/bash

# Crear directorio principal
mkdir -p novel-generator

# Crear estructura de directorios y archivos
mkdir -p novel-generator/core
touch novel-generator/core/__init__.py
touch novel-generator/core/coherence_analyzer.py
touch novel-generator/core/api_handler.py
touch novel-generator/core/story_manager.py

mkdir -p novel-generator/models
touch novel-generator/models/__init__.py
touch novel-generator/models/content_rating.py
touch novel-generator/models/encoder.py

mkdir -p novel-generator/utils
touch novel-generator/utils/__init__.py
touch novel-generator/utils/document_generator.py

touch novel-generator/main.py
touch novel-generator/config.json

echo "Estructura creada exitosamente:"
tree novel-generator