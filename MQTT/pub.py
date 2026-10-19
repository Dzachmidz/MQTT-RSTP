#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import paho.mqtt.client as mqtt
import os
import time
import sys
import json
import csv
import certifi
from datetime import datetime, timezone

# ============================================================
# 1. MEMUAT KREDENSIAL DARI FILE .env
# ============================================================

def load_dotenv(path=None):
    path = path or os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        ".env"
    )

    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()

                if not line or line.startswith("#") or "=" not in line:
                    continue

                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())


load_dotenv()

# ============================================================
# 2. KONFIGURASI BROKER MQTT
# ============================================================

broker = "b32e12fd.ala.eu-central-1.emqxsl.com"
port = 8883

username = os.environ.get("MQTT_USERNAME")
password = os.environ.get("MQTT_PASSWORD")

if not username or not password:
    print("Set MQTT_USERNAME dan MQTT_PASSWORD di file .env.")
    sys.exit(1)

# ============================================================
# 3. IDENTITAS PUBLISHER
# ============================================================

# Ubah node_id sesuai laptop:
# Laptop 1: windows-01
# Laptop 2: windows-02
# Laptop 3: windows-03

node_id = "device-04"

topic = "sister/temp"
suhu = 28
sequence_no = 0

# ============================================================
# 4. KONFIGURASI CSV PUBLISHER
# ============================================================

base_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(base_dir, "mqtt_pub_log.csv")

csv_columns = [
    "timestamp_iso",
    "node_id",
    "protocol",
    "t_send_ms",
    "payload_bytes",
    "suhu",
    "sequence_no",
    "publish_status"
]

# Gunakan append agar data sebelumnya tidak tertimpa.
csv_file = open(
    csv_path,
    "a",
    newline="",
    encoding="utf-8"
)

csv_writer = csv.writer(csv_file)

# Tulis header hanya jika file masih kosong.
if os.path.getsize(csv_path) == 0:
    csv_writer.writerow(csv_columns)
    csv_file.flush()

print(f"CSV publisher: {csv_path}")

# ============================================================
# 5. CALLBACK KONEKSI MQTT
# ============================================================

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"Berhasil terhubung ke broker MQTT {broker}")
        print(f"Publisher ID: {node_id}")
        print(f"Topik: {topic}")
    else:
        print(f"Gagal terhubung ke broker, kode: {reason_code}")


# ============================================================
# 6. INISIALISASI KLIEN MQTT
# ============================================================

client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2
)

client.username_pw_set(username, password)

# TLS menggunakan sertifikat CA dari certifi.
client.tls_set(ca_certs=certifi.where())

client.on_connect = on_connect

# ============================================================
# 7. MENGHUBUNGKAN KE BROKER
# ============================================================

try:
    print(f"Menghubungkan ke {broker}...")
    client.connect(broker, port, keepalive=60)

except Exception as e:
    print(f"Gagal menghubungkan ke broker: {e}")
    csv_file.close()
    sys.exit(1)

# Mulai loop jaringan MQTT.
client.loop_start()

# ============================================================
# 8. LOOP PENGIRIMAN PESAN
# ============================================================

try:
    while True:
        sequence_no += 1

        # Timestamp pengiriman dalam epoch milliseconds.
        t_send_ms = int(time.time() * 1000)

        # Payload JSON.
        payload = {
            "node_id": node_id,
            "t_send_ms": t_send_ms,
            "sequence_no": sequence_no,
            "suhu": suhu
        }

        message = json.dumps(payload)
        payload_bytes = len(message.encode("utf-8"))

        # Publikasikan pesan menggunakan QoS 0.
        info = client.publish(
            topic,
            message,
            qos=0
        )

        # Status ini hanya menunjukkan hasil pemanggilan publish().
        if info.rc == mqtt.MQTT_ERR_SUCCESS:
            publish_status = "publish_accepted"
            print(f"Published: {message}")
        else:
            publish_status = f"error_{info.rc}"
            print(f"Gagal mengirim pesan, kode: {info.rc}")

        # Catat aktivitas publisher ke CSV.
        timestamp_iso = datetime.now(
            timezone.utc
        ).isoformat()

        csv_writer.writerow([
            timestamp_iso,
            node_id,
            "mqtt",
            t_send_ms,
            payload_bytes,
            suhu,
            sequence_no,
            publish_status
        ])

        csv_file.flush()

        # Interval pengiriman satu detik.
        time.sleep(1)

except KeyboardInterrupt:
    print("\nPublisher dihentikan.")

except Exception as e:
    print(f"Terjadi kesalahan: {e}")

finally:
    client.loop_stop()
    client.disconnect()
    csv_file.close()

    print("CSV publisher berhasil ditutup.")