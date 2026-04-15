FROM python:3.11-slim

# On définit le dossier de travail
WORKDIR /app/ingestion

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# On copie le requirements.txt (chemin relatif au contexte de build)
COPY ingestion/requirements.txt /app/ingestion/
RUN pip install --no-cache-dir -r requirements.txt

# ON COPIE TOUT LE DOSSIER INGESTION DANS LE WORKDIR
# Le point (.) après COPY signifie "tout le contenu du contexte"
# Mais comme on lance le build depuis la racine, on précise bien la source
COPY ingestion/ /app/ingestion/

# On s'assure que le chemin est dans le PYTHONPATH
ENV PYTHONPATH="/app/ingestion:$PYTHONPATH"

# Par défaut, on liste les spiders pour vérifier que ça marche
CMD ["c", "list"]