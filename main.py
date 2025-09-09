from fastapi import FastAPI
import uvicorn

app = FastAPI()

from routes.availability_routes import availability_router
from routes.booking_routes import booking_router
from routes.field_routes import field_router
from routes.review_routes import review_router
from routes.sports_center_routes import sports_center_router
from routes.user_routes import user_router

app.include_router(availability_router)
app.include_router(booking_router)
app.include_router(field_router)
app.include_router(review_router)
app.include_router(sports_center_router)
app.include_router(user_router)

if __name__ == "__main__":
  uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)