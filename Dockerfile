# PlaylistDrop — run on a home server / NAS / Raspberry Pi and use it from your phone.
FROM python:3.12-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg ca-certificates curl unzip \
 && curl -fsSL https://deno.land/install.sh | DENO_INSTALL=/usr/local sh -s -- -y \
 && apt-get purge -y curl unzip && apt-get autoremove -y \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir .

ENV PLAYLISTDROP_DIR=/downloads PLAYLISTDROP_PORT=8765 PYTHONUNBUFFERED=1
VOLUME ["/downloads"]
EXPOSE 8765
# Set PLAYLISTDROP_HOST_IP to your machine's LAN IP so the QR code points at it, not the container.
CMD ["playlistdrop", "serve", "--host", "0.0.0.0"]
