# Utiliser une image Python légère
FROM python:3.11-slim

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DB_PATH=/data/business.db

# Dossier de travail
WORKDIR /app

# Créer un utilisateur non-root
RUN addgroup --system app && adduser --system --ingroup app app

# Installer les dépendances système (curl pour health check)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Créer le dossier de données et donner les droits
RUN mkdir -p /data && chown app:app /data

# Copier les dépendances Python (optimise le cache Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir --disable-pip-version-check -r requirements.txt

# Copier le code source
COPY . .

# Donner les droits à l'utilisateur non-root
RUN chown -R app:app /app
USER app

# Exposer le port
EXPOSE 5000

# Health check (utilise /health de votre app)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1

# Lancer l'application avec Gunicorn (production)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]