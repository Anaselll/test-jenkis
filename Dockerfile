# Utiliser une image de base Python
FROM python:3.9-slim
# Définir le répertoire de travail
WORKDIR /app
# Copier les fichiers nécessaires dans le conteneur
COPY . .
# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt
# Exécuter les tests avec pytest
CMD ["pytest"]
