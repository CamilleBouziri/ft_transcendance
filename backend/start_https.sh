#!/bin/bash

# Attendre que la base de données soit prête
echo "Attente de la disponibilité de la base de données..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c '\q'; do
  echo "Base de données indisponible - nouvelle tentative dans 1 seconde"
  sleep 1
done
echo "Base de données disponible !"

# Démarrer le serveur Django avec HTTPS
python manage.py runsslserver --certificate /app/certs/cert.pem --key /app/certs/key.pem 0.0.0.0:8443