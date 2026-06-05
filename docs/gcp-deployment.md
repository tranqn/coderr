# Coderr auf Google Cloud deployen

Schritt-für-Schritt-Anleitung, um den Coderr-Production-Stack (Caddy + Django/Gunicorn + PostgreSQL) auf einer Google-Cloud-VM mit automatischem HTTPS bereitzustellen.

Die Anleitung ist auf das **kostenlose `e2-micro`-Always-Free-Tier** ausgelegt – sie läuft also auch nach Ablauf des 300-$-Trials weiter, ohne Kosten zu verursachen (in den dafür vorgesehenen US-Regionen).

---

## 0. Überblick

```
Internet ── :443 HTTPS ──> Caddy (Let's Encrypt) ──> coderr (nginx → gunicorn) ──> PostgreSQL
                                                          │
                                                          └─ Volumes: coderr-data (media), pg-data (db)
```

Was du brauchst:
- Ein Google-Konto + aktiviertes Billing (Trial reicht; das Always-Free-Tier verbraucht praktisch kein Guthaben).
- Optional eine **Domain**. Ohne Domain nutzen wir `sslip.io` (Wildcard-DNS auf deine IP) – damit funktioniert Let's Encrypt trotzdem.
- Lokal installiertes [`gcloud` CLI](https://cloud.google.com/sdk/docs/install) **oder** die GCP-Web-Console.

> **Kostenhinweis:** `e2-micro` hat nur **1 GB RAM**. Caddy + Gunicorn + Postgres + der Image-Build passen da rein, aber knapp – deshalb richten wir weiter unten **Swap** ein und reduzieren die Gunicorn-Worker. Für mehr Last später `e2-small` (2 GB, ~13 $/Monat, zehrt am Guthaben).

---

## 1. Projekt & API vorbereiten

In der [Cloud Console](https://console.cloud.google.com/) ein Projekt wählen/anlegen und die Compute Engine API aktivieren. Mit CLI:

```bash
gcloud auth login
gcloud projects create coderr-prod --name="Coderr"          # oder bestehendes Projekt nutzen
gcloud config set project coderr-prod
# Billing-Konto verknüpfen (ID aus `gcloud billing accounts list`)
gcloud billing projects link coderr-prod --billing-account=XXXXXX-XXXXXX-XXXXXX
gcloud services enable compute.googleapis.com
```

---

## 2. Statische IP reservieren (empfohlen)

Damit deine IP über Neustarts hinweg stabil bleibt (wichtig für DNS). Eine **an eine laufende VM angehängte** statische IP ist kostenlos.

```bash
gcloud compute addresses create coderr-ip --region=us-central1
gcloud compute addresses describe coderr-ip --region=us-central1 --format='value(address)'
# -> z. B. 34.123.45.67  (notieren!)
```

---

## 3. VM erstellen (Always-Free `e2-micro`)

Das kostenlose Tier gilt nur in **`us-west1`, `us-central1` oder `us-east1`**.

```bash
gcloud compute instances create coderr \
  --zone=us-central1-a \
  --machine-type=e2-micro \
  --image-family=debian-12 --image-project=debian-cloud \
  --boot-disk-size=30GB --boot-disk-type=pd-standard \
  --address=coderr-ip \
  --tags=http-server,https-server
```

> Über die Console: **Compute Engine → VM-Instanz erstellen**, Maschinentyp `e2-micro`, Region `us-central1`, Boot-Disk „Debian 12", unter „Firewall" **HTTP- und HTTPS-Traffic zulassen** anhaken, externe IP = `coderr-ip`.

### Firewall für Ports 80/443

Falls die Regeln nicht schon durch die Tags/Checkbox existieren, explizit anlegen:

```bash
gcloud compute firewall-rules create default-allow-http \
  --direction=INGRESS --action=ALLOW --rules=tcp:80 --target-tags=http-server
gcloud compute firewall-rules create default-allow-https \
  --direction=INGRESS --action=ALLOW --rules=tcp:443 --target-tags=https-server
```

---

## 4. DNS einrichten

**Mit eigener Domain:** Beim Domain-Anbieter einen **A-Record** anlegen, der auf deine externe IP zeigt:

```
coderr.example.com.   A   34.123.45.67
```

**Ohne Domain (sslip.io):** Du brauchst nichts einzurichten – `sslip.io` löst automatisch auf. Aus IP `34.123.45.67` wird der Hostname:

```
34-123-45-67.sslip.io
```

Diesen Hostnamen verwendest du unten als `SITE_ADDRESS`. Caddy holt sich dafür ein echtes Let's-Encrypt-Zertifikat.

> Prüfen, dass DNS sitzt (vom Laptop): `ping 34-123-45-67.sslip.io` bzw. `dig +short coderr.example.com`.

---

## 5. Auf die VM verbinden

```bash
gcloud compute ssh coderr --zone=us-central1-a
```

Alle folgenden Schritte laufen **auf der VM**.

---

## 6. Swap einrichten (wichtig bei 1 GB RAM)

Verhindert OOM-Abbrüche beim Image-Build und unter Last:

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
free -h        # SWAP sollte jetzt 2 GB zeigen
```

---

## 7. Docker installieren

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo systemctl enable --now docker
# eigenen User in die docker-Gruppe (danach einmal neu einloggen):
sudo usermod -aG docker "$USER"
exit
```

Erneut verbinden (`gcloud compute ssh coderr --zone=us-central1-a`) und prüfen:

```bash
docker version
docker compose version
```

---

## 8. Projekt klonen

```bash
sudo apt-get update && sudo apt-get install -y git
git clone https://github.com/tranqn/coderr.git
cd coderr
```

---

## 9. `.env` konfigurieren

```bash
cp .env.example .env
nano .env
```

Werte setzen (Beispiel mit `sslip.io`; bei eigener Domain den Hostnamen entsprechend ersetzen):

```ini
# Langen Zufallswert erzeugen:  openssl rand -hex 48
DJANGO_SECRET_KEY=<hier-ein-langer-zufallswert>
DJANGO_DEBUG=False

# Hostname aus Schritt 4 (Domain ODER sslip.io):
DJANGO_ALLOWED_HOSTS=34-123-45-67.sslip.io
DJANGO_CSRF_TRUSTED_ORIGINS=https://34-123-45-67.sslip.io
SITE_ADDRESS=34-123-45-67.sslip.io

# PostgreSQL:
POSTGRES_DB=coderr
POSTGRES_USER=coderr
POSTGRES_PASSWORD=<starkes-passwort>

# Optional Demo-Daten beim ersten Start:
SEED_DEMO_DATA=1
```

> **RAM sparen:** Bei `e2-micro` zusätzlich `GUNICORN_WORKERS=2` in die `.env` aufnehmen (Standard ist 3).

`openssl rand -hex 48` erzeugt dir direkt einen Secret-Key.

---

## 10. Stack starten

```bash
docker compose -f compose.prod.yml up -d --build
```

Der erste Build dauert auf `e2-micro` einige Minuten. Danach:

```bash
docker compose -f compose.prod.yml ps          # alle Services „Up"/„healthy"?
docker compose -f compose.prod.yml logs -f      # Logs verfolgen (Strg+C zum Lösen)
```

Caddy holt sich beim ersten Aufruf automatisch ein TLS-Zertifikat (kann 10–30 s dauern).

---

## 11. Admin-User anlegen

```bash
docker compose -f compose.prod.yml exec coderr python manage.py createsuperuser
```

---

## 12. Funktioniert es?

Im Browser:
- **App:** `https://34-123-45-67.sslip.io/`
- **Admin:** `https://34-123-45-67.sslip.io/admin/`

Oder vom Laptop:

```bash
curl -s https://34-123-45-67.sslip.io/api/base-info/
```

Demo-Logins (falls `SEED_DEMO_DATA=1`): Business `b_designer`, Customer `c_anna`, Passwort `demo-pw-12345`.

---

## 13. Betrieb & Wartung

**Update einspielen** (neuer Code aus Git):

```bash
cd ~/coderr
git pull
docker compose -f compose.prod.yml up -d --build
```

**Logs / Management:**

```bash
docker compose -f compose.prod.yml logs -f coderr
docker compose -f compose.prod.yml exec coderr python manage.py seed_demo_data --reset
docker compose -f compose.prod.yml restart coderr
```

**Datenbank-Backup** (das `pg-data`-Volume ist die Wahrheit):

```bash
docker compose -f compose.prod.yml exec db \
  pg_dump -U coderr coderr > ~/coderr-backup-$(date +%F).sql
```

**Wiederherstellen:**

```bash
cat ~/coderr-backup-2026-06-05.sql | \
  docker compose -f compose.prod.yml exec -T db psql -U coderr -d coderr
```

**Stoppen / komplett entfernen:**

```bash
docker compose -f compose.prod.yml down       # stoppen, Daten bleiben
docker compose -f compose.prod.yml down -v    # inkl. Volumes löschen (Datenverlust!)
```

---

## 14. Kosten im Blick behalten

- **`e2-micro` in `us-west1`/`us-central1`/`us-east1`** + 30 GB Standard-Disk + 1 GB Egress/Monat = **Always-Free**, läuft auch nach dem Trial weiter.
- Eine **an die laufende VM angehängte** statische IP ist kostenlos – eine *reservierte, aber nicht genutzte* IP kostet. Also nicht ungenutzt liegen lassen.
- VM nicht gebraucht? `gcloud compute instances stop coderr` (gestoppte VM kostet nur die Disk).
- Budget-Alarm setzen: **Billing → Budgets & alerts** (z. B. Warnung bei 1 $).

> Größere Maschinen (`e2-small` aufwärts), zusätzliche Disks, hoher Egress und ungenutzte statische IPs zehren am 300-$-Guthaben – für Coderr als Demo nicht nötig.

---

## 15. Härtung (optional, empfohlen)

- **SSH nur per Key** – GCP nutzt standardmäßig schon Key-basiertes SSH; Passwort-Login ist aus.
- **OS-Login aktivieren** für zentrale Schlüsselverwaltung: `gcloud compute instances add-metadata coderr --metadata enable-oslogin=TRUE`.
- **Automatische Sicherheitsupdates:** `sudo apt-get install -y unattended-upgrades`.
- **Firewall minimal halten:** nur 22 (SSH), 80, 443 offen. Den SSH-Zugang ggf. auf deine IP einschränken.

---

## Troubleshooting

| Symptom | Ursache / Lösung |
|---|---|
| Zertifikat kommt nicht | Port 80 muss von außen erreichbar sein (Firewall-Tags `http-server`!), DNS muss auf die IP zeigen. `docker compose -f compose.prod.yml logs caddy` prüfen. |
| `Bad Request (400)` im Browser | `DJANGO_ALLOWED_HOSTS` enthält den Hostnamen nicht. In `.env` korrigieren, dann `up -d`. |
| Admin-Login schlägt fehl (CSRF) | `DJANGO_CSRF_TRUSTED_ORIGINS=https://<host>` setzen. |
| Build/Start bricht mit „Killed" ab | Zu wenig RAM → Swap aus Schritt 6 einrichten, `GUNICORN_WORKERS=2`. |
| `coderr` startet nicht | Wartet auf `db` (healthy). `docker compose -f compose.prod.yml logs db` prüfen, Passwort in `.env` gesetzt? |
