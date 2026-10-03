import os

# Discord OAuth2
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "")
DISCORD_REDIRECT_URI = os.getenv(
    "DISCORD_REDIRECT_URI",
    "http://127.0.0.1:5000/callback"
)

# Bot / administrador
OWNER_ID = os.getenv("OWNER_ID", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Flask
FLASK_SECRET_KEY = os.getenv(
    "FLASK_SECRET_KEY",
    "development-only-change-this"
)

PORT = int(os.getenv("PORT", "5000"))

# Servidor Discord
DISCORD_GUILD_ID = os.getenv(
    "DISCORD_GUILD_ID",
    "1548006118683320501"
)

STAFF_ROLE_ID = os.getenv(
    "STAFF_ROLE_ID",
    "1555851596875960330"
)
