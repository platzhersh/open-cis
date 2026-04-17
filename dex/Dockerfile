FROM dexidp/dex:v2.39.1

# Install config as a template — entrypoint substitutes ${VAR} placeholders
# at runtime. Dex's own DEX_EXPAND_ENV has been unreliable on Railway.
COPY dex/config.railway.yaml /etc/dex/config.template.yaml
COPY dex/entrypoint.sh /entrypoint.sh

USER root
RUN chmod +x /entrypoint.sh
USER 1001

ENTRYPOINT ["/entrypoint.sh"]
