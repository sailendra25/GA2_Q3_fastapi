import os

import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": True,
    "log_level": "info",
    "api_key": "default-secret-000",
}


def to_bool(v):
    return str(v).lower() in ("true", "1", "yes", "on")


def coerce(key, value):
    if key in ("port", "workers"):
        return int(value)
    if key == "debug":
        return to_bool(value)
    return str(value)


@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):

    config = DEFAULTS.copy()

    # YAML layer
    with open("config.development.yaml") as f:
        yaml_cfg = yaml.safe_load(f)
    config.update(yaml_cfg)

    # .env layer
    env_cfg = dotenv_values(".env")

    if "NUM_WORKERS" in env_cfg:
        config["workers"] = int(env_cfg["NUM_WORKERS"])

    if "APP_API_KEY" in env_cfg:
        config["api_key"] = env_cfg["APP_API_KEY"]

    # OS env layer
    mapping = {
        "APP_PORT": "port",
        "APP_WORKERS": "workers",
        "APP_DEBUG": "debug",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key",
    }

    for env_key, cfg_key in mapping.items():
        if env_key in os.environ:
            config[cfg_key] = coerce(cfg_key, os.environ[env_key])

    # CLI overrides
    for item in set:
        if "=" not in item:
            continue
        k, v = item.split("=", 1)
        config[k] = coerce(k, v)

    # Mask secret
    config["api_key"] = "****"

    return config
