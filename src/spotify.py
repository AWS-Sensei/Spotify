from __future__ import annotations

from base64 import b64encode, b64decode
from io import BytesIO
from pathlib import Path
import json
import os
import random
import requests

import boto3
from botocore.exceptions import ClientError
from colorthief import ColorThief
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Spotify scopes:
#   user-read-currently-playing
#   user-read-recently-played
PLACEHOLDER_IMAGE = (
    "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"
)
PLACEHOLDER_URL = "https://source.unsplash.com/random/300x300/?aerial"
SPOTIFY_SECRET_NAME = os.getenv("SPOTIFY_SECRET_NAME")
SPOTIFY_TOKEN = ""
_SPOTIFY_SECRET_CACHE: dict | None = None

FALLBACK_THEME = "spotify.html.j2"

REFRESH_TOKEN_URL = "https://accounts.spotify.com/api/token"
NOW_PLAYING_URL = "https://api.spotify.com/v1/me/player/currently-playing"
RECENTLY_PLAYING_URL = (
    "https://api.spotify.com/v1/me/player/recently-played?limit=10"
)

DEFAULT_TEMPLATE = """\
<svg xmlns="http://www.w3.org/2000/svg" width="600" height="200">
  <style>
    .title { font: 700 20px 'Arial'; fill: #ffffff; }
    .subtitle { font: 400 14px 'Arial'; fill: #c7c7c7; }
    .frame { fill: #{{ background_color }}; stroke: #{{ border_color }}; stroke-width: 2; }
  </style>
  <rect class="frame" x="1" y="1" width="598" height="198" rx="16"/>
  <image href="data:image/jpeg;base64,{{ image }}" x="16" y="16" width="168" height="168"/>
  <text class="subtitle" x="200" y="52">{{ status }}</text>
  <text class="title" x="200" y="86">{{ songName }}</text>
  <text class="subtitle" x="200" y="116">{{ artistName }}</text>
  <a href="{{ songURI }}"><text class="subtitle" x="200" y="148">Open in Spotify</text></a>
</svg>
"""


def _env() -> Environment:
    templates_dir = Path(__file__).parent / "templates"
    if templates_dir.exists():
        loader = FileSystemLoader(str(templates_dir))
        return Environment(
            loader=loader,
            autoescape=select_autoescape(enabled_extensions=("html", "svg", "j2")),
        )
    return Environment(autoescape=select_autoescape(default=True))


def _load_spotify_secret() -> dict:
    if not SPOTIFY_SECRET_NAME:
        raise RuntimeError("SPOTIFY_SECRET_NAME env var is required.")

    client = boto3.client("secretsmanager")
    try:
        response = client.get_secret_value(SecretId=SPOTIFY_SECRET_NAME)
    except ClientError as exc:
        raise RuntimeError(f"Failed to load secret {SPOTIFY_SECRET_NAME}") from exc

    if "SecretString" in response:
        return json.loads(response["SecretString"])
    if "SecretBinary" in response:
        decoded = b64decode(response["SecretBinary"]).decode("utf-8")
        return json.loads(decoded)

    raise RuntimeError(f"Secret {SPOTIFY_SECRET_NAME} has no SecretString/SecretBinary.")


def _get_spotify_secret() -> dict:
    global _SPOTIFY_SECRET_CACHE
    if _SPOTIFY_SECRET_CACHE is None:
        _SPOTIFY_SECRET_CACHE = _load_spotify_secret()
    return _SPOTIFY_SECRET_CACHE


def get_auth() -> str:
    secret = _get_spotify_secret()
    client_id = secret["SPOTIFY_CLIENT_ID"]
    secret_id = secret["SPOTIFY_SECRET_ID"]
    return b64encode(f"{client_id}:{secret_id}".encode()).decode("ascii")


def refresh_token() -> str:
    secret = _get_spotify_secret()
    data = {
        "grant_type": "refresh_token",
        "refresh_token": secret["SPOTIFY_REFRESH_TOKEN"],
    }
    headers = {"Authorization": f"Basic {get_auth()}"}
    response = requests.post(REFRESH_TOKEN_URL, data=data, headers=headers).json()

    try:
        return response["access_token"]
    except KeyError as exc:
        raise KeyError(json.dumps(response)) from exc


def get(url: str) -> dict:
    global SPOTIFY_TOKEN

    if SPOTIFY_TOKEN == "":
        SPOTIFY_TOKEN = refresh_token()

    response = requests.get(url, headers={"Authorization": f"Bearer {SPOTIFY_TOKEN}"})

    if response.status_code == 401:
        SPOTIFY_TOKEN = refresh_token()
        response = requests.get(url, headers={"Authorization": f"Bearer {SPOTIFY_TOKEN}"})
    if response.status_code == 204:
        raise ValueError(f"{url} returned no data.")

    return response.json()


def bar_gen(bar_count: int) -> str:
    bar_css = ""
    left = 1
    for i in range(1, bar_count + 1):
        anim = random.randint(500, 1000)
        # below code generates random cubic-bezier values
        x1 = random.random()
        y1 = random.random() * 2
        x2 = random.random()
        y2 = random.random() * 2
        bar_css += (
            ".bar:nth-child({})  {{ left: {}px; animation-duration: 15s, {}ms; "
            "animation-timing-function: ease, cubic-bezier({},{},{},{}); }}"
        ).format(i, left, anim, x1, y1, x2, y2)
        left += 4
    return bar_css


def gradient_gen(album_art_url: str, color_count: int) -> list[tuple[int, int, int]]:
    colortheif = ColorThief(BytesIO(requests.get(album_art_url).content))
    return colortheif.get_palette(color_count)


def _templates_config_path() -> Path:
    return Path(__file__).parent / "templates.json"


def get_template_name() -> str:
    try:
        templates_json = _templates_config_path()
        if not templates_json.exists():
            return FALLBACK_THEME
        templates = json.loads(templates_json.read_text(encoding="utf-8"))
        return templates["templates"][templates["current-theme"]]
    except Exception:
        return FALLBACK_THEME


def load_image_b64(url: str) -> str:
    response = requests.get(url)
    response.raise_for_status()
    return b64encode(response.content).decode("ascii")


def make_svg(data: dict, background_color: str, border_color: str) -> str:
    bar_count = 84
    content_bar = "".join(["<div class='bar'></div>" for _ in range(bar_count)])
    bar_css = bar_gen(bar_count)

    if "is_playing" not in data:
        current_status = "Recently played:"
        recent_plays = get(RECENTLY_PLAYING_URL)
        recent_plays_length = len(recent_plays["items"])
        item_index = random.randint(0, recent_plays_length - 1)
        item = recent_plays["items"][item_index]["track"]
    else:
        item = data["item"]
        current_status = "Vibing to:"

    if item["album"]["images"] == []:
        image = PLACEHOLDER_IMAGE
        bar_palette = gradient_gen(PLACEHOLDER_URL, 4)
        song_palette = gradient_gen(PLACEHOLDER_URL, 2)
    else:
        image_url = item["album"]["images"][1]["url"]
        image = load_image_b64(image_url)
        bar_palette = gradient_gen(image_url, 4)
        song_palette = gradient_gen(image_url, 2)

    artist_name = item["artists"][0]["name"].replace("&", "&amp;")
    song_name = item["name"].replace("&", "&amp;")
    song_uri = item["external_urls"]["spotify"]
    artist_uri = item["artists"][0]["external_urls"]["spotify"]

    data_dict = {
        "contentBar": content_bar,
        "barCSS": bar_css,
        "artistName": artist_name,
        "songName": song_name,
        "songURI": song_uri,
        "artistURI": artist_uri,
        "image": image,
        "status": current_status,
        "background_color": background_color,
        "border_color": border_color,
        "barPalette": bar_palette,
        "songPalette": song_palette,
    }

    env = _env()
    template_name = get_template_name()
    if env.loader and template_name != FALLBACK_THEME:
        template = env.get_template(template_name)
    else:
        template = env.from_string(DEFAULT_TEMPLATE)
    return template.render(**data_dict)


def lambda_handler(event, context):
    params = (event or {}).get("queryStringParameters") or {}
    background_color = params.get("background_color") or "181414"
    border_color = params.get("border_color") or "181414"

    try:
        data = get(NOW_PLAYING_URL)
    except Exception:
        data = get(RECENTLY_PLAYING_URL)

    svg = make_svg(data, background_color, border_color)
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "image/svg+xml", "Cache-Control": "s-maxage=1"},
        "body": svg,
        "isBase64Encoded": False,
    }
