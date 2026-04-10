from __future__ import annotations

import argparse
import json
import time

import uvicorn

from analyser.api import create_app
from analyser.collector import Collector
from analyser.config import get_settings
from analyser.profiles import get_profile
from analyser.radio import DongLoRaRadio
from analyser.storage import Storage


def cmd_init_db() -> None:
    settings = get_settings()
    storage = Storage(settings.db_path)
    storage.init_db()
    profile = get_profile(settings.profile_name)
    profile_id = storage.upsert_profile(profile)
    print(f"database initialized at {settings.db_path}; profile id={profile_id}")


def cmd_monitor(duration: int | None = None) -> None:
    settings = get_settings()
    storage = Storage(settings.db_path)
    profile = get_profile(settings.profile_name)
    collector = Collector(storage=storage, radio=DongLoRaRadio(settings.device_port), profile=profile)
    collector.start()
    print("collector started")
    try:
        if duration:
            time.sleep(duration)
        else:
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        collector.stop()
        print(json.dumps(collector.status.as_dict(), indent=2))


def cmd_serve() -> None:
    settings = get_settings()
    uvicorn.run("analyser.api:app", host=settings.host, port=settings.port, reload=False)


def cmd_sweep() -> None:
    print("Sweep scaffold only: narrow fallback sweep not implemented in MVP.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MeshCore-focused DongLoRa analyser")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init-db", help="Initialize SQLite schema and profile row")

    p_monitor = sub.add_parser("monitor", help="Run packet collector loop")
    p_monitor.add_argument("--duration", type=int, default=None, help="optional run time in seconds")

    sub.add_parser("serve", help="Run FastAPI web server")
    sub.add_parser("sweep", help="Scaffolded narrow sweep command")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "init-db":
        cmd_init_db()
    elif args.command == "monitor":
        cmd_monitor(duration=args.duration)
    elif args.command == "serve":
        cmd_serve()
    elif args.command == "sweep":
        cmd_sweep()
    else:
        parser.error(f"Unknown command {args.command}")


if __name__ == "__main__":
    main()
