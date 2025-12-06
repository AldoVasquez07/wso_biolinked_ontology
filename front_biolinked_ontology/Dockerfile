# =================================================================
# Dockerfile para Frontend Vue.js + Nginx
# Ubicación: front_biolinked_ontology/Dockerfile
# Multi-stage build para imagen ultra ligera
# =================================================================

# ============================================
# ETAPA 1: BUILD (Construcción)
# ============================================
FROM node:18-alpine AS build

# Metadatos
LABEL maintainer="tu-email@ejemplo.com"
LABEL stage=builder

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY package*.json ./

# Instalar TODAS las dependencias (incluyendo devDependencies necesarias para el build)
RUN npm ci --silent

# Copiar código fuente
COPY . .

# Configurar URL de API (se puede sobrescribir con variable de entorno)
ARG API_URL=http://localhost:5000/api
ENV VUE_APP_API_URL=$API_URL

# Build optimizado para producción
RUN npm run build

# ============================================
# ETAPA 2: PRODUCTION (Servir con Nginx)
# ============================================
FROM nginx:alpine

# Metadatos
LABEL maintainer="tu-email@ejemplo.com"
LABEL description="BioLinkedCatalog Frontend"

# Copiar archivos construidos desde la etapa anterior
COPY --from=build /app/dist /usr/share/nginx/html

# Copiar configuración personalizada de nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Crear usuario nginx si no existe y ajustar permisos
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chmod -R 755 /usr/share/nginx/html

# Exponer puerto 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# Usuario no-root por seguridad
USER nginx

# Nginx se ejecuta en foreground
CMD ["nginx", "-g", "daemon off;"]