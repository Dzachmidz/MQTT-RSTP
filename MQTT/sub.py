#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import paho.mqtt.client as mqtt
import os
import sys
import certifi
import json
import csv
import time
from datetime import datetime, timezone

# Memuat kredensial dari file .env di folder yang sama
def load_dotenv(path=None):
    path = path or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), ".env"
    )

    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()

                if not line or line.startswith("#") or "=" not in line:
                    continue

                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())


load_dotenv()

# Konfigurasi broker EMQX Cloud
broker = "b32e12fd.ala.eu-central-1.emqxsl.com"
port = 8883
topic = "sister/temp"

# Kredensial MQTT
username = os.environ.get("MQTT_USERNAME")
password = os.environ.get("MQTT_PASSWORD")

if not username or not password:
    print("Set MQTT_USERNAME dan MQTT_PASSWORD di file .env.")
    sys.exit(1)

# Lokasi file CSV di folder MQTT
base_dir = os.path.dirname(os.path.abspath(__file__))
csv_file = os.path.join(base_dir, "mqtt_log.csv")

# Kolom log sesuai LKM 2
fieldnames = [
    "timestamp_iso",
    "node_id",
    "protocol",
    "t_send_ms",
    "t_recv_ms",
    "payload_bytes",
    "suhu",
    "sequence_no"
]

# Membuat CSV baru dengan header jika file belum ada atau masih kosong
if not os.path.exists(csv_file) or os.path.getsize(csv_file) == 0:
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()


# Callback saat koneksi berhasil
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"Berhasil terhubung ke broker MQTT {broker}")
        client.subscribe(topic)
        print(f"Berlangganan topik: {topic}")
    else:
        print(f"Gagal terhubung ke broker, kode: {reason_code}")


# Callback saat pesan diterima
def on_message(client, userdata, message):
    # Waktu penerimaan dalam epoch milliseconds
    t_recv_ms = int(time.time() * 1000)

    # Ukuran payload dalam byte
    payload_bytes = len(message.payload)

    try:
        payload = json.loads(message.payload.decode("utf-8"))

        node_id = payload["node_id"]
        t_send_ms = payload["t_send_ms"]
        suhu = payload["suhu"]
        sequence_no = payload["sequence_no"]

    except (json.JSONDecodeError, UnicodeDecodeError, KeyError, TypeError) as e:
        print(f"Pesan tidak sesuai format JSON LKM: {e}")
        print(f"Payload: {message.payload!r}")
        return

    # Waktu penerimaan dalam format ISO 8601 UTC
    timestamp_iso = datetime.now(timezone.utc).isoformat()

    # Data yang akan disimpan
    row = {
        "timestamp_iso": timestamp_iso,
        "node_id": node_id,
        "protocol": "mqtt",
        "t_send_ms": t_send_ms,
        "t_recv_ms": t_recv_ms,
        "payload_bytes": payload_bytes,
        "suhu": suhu,
        "sequence_no": sequence_no
    }

    # Simpan satu baris setiap kali pesan diterima
    with open(csv_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writerow(row)

    print(
        f"Received: node={node_id}, "
        f"seq={sequence_no}, suhu={suhu}°C, "
        f"bytes={payload_bytes}"
    )


# Inisialisasi klien MQTT
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(username, password)
client.tls_set(ca_certs=certifi.where())

client.on_connect = on_connect
client.on_message = on_message


# Menghubungkan ke broker
try:
    print(f"Menghubungkan ke {broker}...")
    client.connect(broker, port, keepalive=60)

except Exception as e:
    print(f"Gagal menghubungkan ke broker: {e}")
    sys.exit(1)


# Menjaga koneksi tetap berjalan
try:
    print("Menunggu pesan... (Tekan Ctrl+C untuk keluar)")
    print(f"Log CSV: {csv_file}")
    client.loop_forever()

except KeyboardInterrupt:
    print("\nSubscriber dihentikan.")
    client.disconnect()