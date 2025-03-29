##################################################################################
### Nous utilisons l'image de base Python et nous installons les dépendances   ###
### définies dans le fichier requirements.txt. Le serveur Django est configuré ###
### pour être accessible depuis l'extérieur du conteneur sur le port 8000.     ###
##################################################################################

FROM python:3.11-slim

WORKDIR /app

# Installer gettext et autres dépendances système nécessaires
RUN apt-get update && apt-get install -y postgresql-client \
    gettext \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY ./backend/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt
RUN pip install daphne channels channels-redis
RUN pip install whitenoise

COPY ./backend /app/

# Copier les certificats SSL
COPY backend/certs /app/certs

# Copier le script de démarrage
COPY backend/start_https.sh /app/
RUN chmod +x /app/start_https.sh

COPY ./backend/wait-for-it.sh /app/wait-for-it.sh
RUN chmod +x /app/wait-for-it.sh

# Définir explicitement la variable d'environnement
ENV DJANGO_SETTINGS_MODULE=project.settings
ENV PYTHONPATH=/app

EXPOSE 8000

# CMD ["/app/wait-for-it.sh", "/app/start_https.sh", "database:5432", "--", "daphne", "-b", "0.0.0.0", "-p", "8000", "project.asgi:application"]
# CMD ["/app/wait-for-it.sh", "database:5432", "--", "/app/start_https.sh", "daphne", "-b", "0.0.0.0", "-p", "8000", "project.asgi:application"]
CMD ["/app/wait-for-it.sh", "database:5432", "--", "daphne", "-e", "ssl:8443:privateKey=/app/certs/key.pem:certKey=/app/certs/cert.pem", "-b", "0.0.0.0", "project.asgi:application"]

