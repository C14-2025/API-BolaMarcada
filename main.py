try:
    import bcrypt

    if not hasattr(bcrypt, "__about__"):

        class _About:
            __version__ = getattr(bcrypt, "__version__", "4")

        bcrypt.__about__ = _About()
except Exception:
    pass

import logging

logging.getLogger("passlib").setLevel(logging.ERROR)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from starlette.middleware.sessions import SessionMiddleware  # <- corrigido

from core.config import settings

from routes.availability_routes import availability_router
from routes.booking_routes import booking_router
from routes.field_routes import field_router
from routes.review_routes import review_router
from routes.sports_center_routes import sports_center_router
from routes.user_routes import user_router
# (depois que criarmos as rotas OAuth, vamos importar aqui:)
# from routes.oauth_routes import oauth_router

app = FastAPI(title=settings.PROJECT_NAME)

# CORS p/ dev (ajuste origens conforme seu front)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SessionMiddleware para fluxos OAuth (state/nonce na sessão)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    max_age=60 * 60 * 4,  # 4 horas
)

API_PREFIX = settings.API_V1_STR  # "/api/v1"

# Monte TODOS os routers com o prefixo
app.include_router(availability_router, prefix=API_PREFIX)
app.include_router(booking_router, prefix=API_PREFIX)
app.include_router(field_router, prefix=API_PREFIX)
app.include_router(review_router, prefix=API_PREFIX)
app.include_router(sports_center_router, prefix=API_PREFIX)
app.include_router(user_router, prefix=API_PREFIX)
# (quando criarmos oauth_routes.py:)
# app.include_router(oauth_router, prefix=API_PREFIX)

if __name__ == "__main__":
    # no Docker, exponha em 0.0.0.0
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
