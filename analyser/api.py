from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from analyser.collector import Collector
from analyser.config import get_settings
from analyser.profiles import get_profile
from analyser.radio import DongLoRaRadio
from analyser.storage import Storage

templates = Jinja2Templates(directory="analyser/templates")


def build_runtime(start_collector: bool = True):
    settings = get_settings()
    storage = Storage(settings.db_path)
    profile = get_profile(settings.profile_name)
    radio = DongLoRaRadio(settings.device_port)
    collector = Collector(storage=storage, radio=radio, profile=profile)
    return settings, storage, profile, collector


def create_app(start_collector: bool = True) -> FastAPI:
    settings, storage, profile, collector = build_runtime(start_collector=start_collector)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        storage.init_db()
        storage.upsert_profile(profile)
        if start_collector:
            collector.start()
        try:
            yield
        finally:
            if start_collector:
                collector.stop()

    app = FastAPI(title="MeshCore Analyser", lifespan=lifespan)

    @app.get("/health")
    def health():
        return {"status": "ok", "collector": collector.status.as_dict()}

    @app.get("/api/profile")
    def api_profile():
        return storage.get_profile(profile.name)

    @app.get("/api/packets/recent")
    def api_recent_packets(limit: int = Query(default=100, ge=1, le=500)):
        return storage.recent_packets(limit=limit)

    @app.get("/api/stats/summary")
    def api_stats_summary(minutes: int = Query(default=60, ge=1, le=1440)):
        return storage.stats_summary(minutes=minutes)

    @app.get("/api/stats/timeseries")
    def api_stats_timeseries(minutes: int = Query(default=60, ge=1, le=1440)):
        return storage.stats_timeseries(minutes=minutes)

    @app.get("/api/fingerprints/top")
    def api_fingerprints(limit: int = Query(default=50, ge=1, le=200)):
        return storage.top_fingerprints(limit=limit)

    @app.get("/", response_class=HTMLResponse)
    def dashboard(request: Request):
        context = {
            "request": request,
            "collector": collector.status.as_dict(),
            "profile": storage.get_profile(profile.name),
            "recent_packets": storage.recent_packets(limit=50),
            "summary": storage.stats_summary(minutes=60),
            "fingerprints": storage.top_fingerprints(limit=20),
        }
        return templates.TemplateResponse("index.html", context)

    app.state.settings = settings
    app.state.storage = storage
    app.state.profile = profile
    app.state.collector = collector
    return app


app = create_app(start_collector=True)
