FROM dexidp/dex:v2.39.1

COPY dex/config.railway.yaml /etc/dex/config.yaml

EXPOSE 5556

CMD ["dex", "serve", "/etc/dex/config.yaml"]
