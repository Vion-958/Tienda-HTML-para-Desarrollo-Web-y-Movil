# Imagen comun; cada contenedor elige su servicio con "command".
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY servicios ./servicios
COPY vault-local ./vault-local
# Carpetas de datos creadas aqui para que los volumenes hereden el dueno.
RUN useradd --create-home app \
    && for s in auth-service inventory orders clients payments; do mkdir -p servicios/$s/data; done \
    && chown -R app /app
USER app
