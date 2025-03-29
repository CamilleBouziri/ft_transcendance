##################################################################################
### Nous utilisons Nginx comme serveur web pour servir les fichiers statiques  ### 
### du frontend (HTML, CSS, JS). Les fichiers sont copiés dans le répertoire   ###
### par défaut de Nginx. 													   ###
##################################################################################

# Utilise l'image officielle de Nginx basée sur Alpine Linux pour la légèreté
FROM nginx:alpine

# Copier les fichiers statiques du frontend depuis le répertoire `frontend/` local vers le répertoire par défaut de Nginx pour les fichiers HTML/CSS
COPY ./frontend/ /usr/share/nginx/html/

# Exposer le port 80, utilisé par Nginx pour servir les pages web
EXPOSE 80

