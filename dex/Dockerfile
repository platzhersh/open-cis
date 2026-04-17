FROM dexidp/dex:v2.39.1

COPY dex/config.railway.yaml /etc/dex/config.yaml

# Enable ${VAR} substitution for DEX_ISSUER and DEX_REDIRECT_URI at startup.
# Without this, Dex reads placeholders literally and fails with cryptic errors
# like "malformed bcrypt hash: hashedSecret too short".
ENV DEX_EXPAND_ENV=true

EXPOSE 5556

CMD ["dex", "serve", "/etc/dex/config.yaml"]
