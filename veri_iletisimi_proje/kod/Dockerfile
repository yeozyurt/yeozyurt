# Alpine 3.22, OpenSSL 3.5 serisini (X25519MLKEM768 destekli) içerir.
FROM alpine:3.22
RUN apk add --no-cache openssl python3 ca-certificates py3-matplotlib \
    && openssl list -tls-groups | grep -q X25519MLKEM768
WORKDIR /olcum
COPY olcum.py analiz.py siteler.csv ./
# Sonuçlar /veri klasörüne yazılır (docker run -v ile bilgisayarınıza bağlayın)
ENTRYPOINT ["python3", "olcum.py", "--cikti", "/veri/sonuclar.csv"]
