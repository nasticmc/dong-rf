# DongLoRa MeshCore Analyser (MVP)

A Python-first LoRa packet monitor tailored to a **known MeshCore AU narrow preset** near **916 MHz**.

## What it does

- Fixed-profile packet monitoring (no wideband scanning)
- Packet storage in SQLite with metadata (RSSI/SNR/airtime)
- Fingerprint grouping via SHA-256 + payload prefixes
- Local FastAPI JSON API + simple dashboard
- Optional scaffolded `sweep` command for future narrow fallback logic

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cp .env.example .env
python -m analyser.cli init-db
python -m analyser.cli serve
```

Open `http://127.0.0.1:8000`.

## CLI

```bash
python -m analyser.cli init-db
python -m analyser.cli monitor --duration 60
python -m analyser.cli serve
python -m analyser.cli sweep
```

## Default profile

- name: `au_narrow_916`
- freq_hz: `916000000`
- bw: `62.5 kHz`
- sf: `7`
- cr: `8`
- sync_word: `0x12`
- preamble_len: `16`
- cad: `true`

## API endpoints

- `GET /health`
- `GET /api/profile`
- `GET /api/packets/recent?limit=100`
- `GET /api/stats/summary?minutes=60`
- `GET /api/stats/timeseries?minutes=60`
- `GET /api/fingerprints/top?limit=50`

## Notes

- The collector expects a working `donglora` package + compatible USB device.
- If radio connection fails, UI/API still run and status exposes the collector error.
