from fastapi import APIRouter, HTTPException
from models.models import User
from schemas.sports_center_schemas import (
    SportsCenterCreate,
    SportsCenterResponse,
    SportsCenterUpdate,
)
from sqlalchemy.orm import Session
from core.database import get_db
from fastapi import Depends
from services.sports_center_service import (
    create_sports_center_service,
    get_all_sports_centers_by_user_id_service,
    get_sports_center_by_id_service,
    delete_sports_center_by_id,
    update_sports_center_service,
    get_sports_center_by_city_service,
)
import requests

sports_center_router = APIRouter(prefix="/sports_center", tags=["sports_center"])


@sports_center_router.post("/create", status_code=201)
async def create_sports_center(
    sports_center_create: SportsCenterCreate,
    session: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user),
):
    try:
        new_id = create_sports_center_service(session, sports_center_create)
        return {"message": "Centro esportivo criado com sucesso.", "id": new_id}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=400, detail=f"Erro ao criar centro esportivo: {str(e)}"
        )


@sports_center_router.get("/{sports_center_id}")
async def get_sports_center(
    sports_center_id: int,
    session: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user),
):

    # Busca o centro esportivo pelo ID
    sports_center = get_sports_center_by_id_service(session, sports_center_id)

    # Se não existir, retorna erro 404
    if not sports_center:
        raise HTTPException(status_code=404, detail="Centro esportivo não encontrado.")

    # Retorna os dados do centro esportivo
    return sports_center


@sports_center_router.get("/all/{user_id}")
async def get_sports_centers_by_user_id(
    owner_id: int,
    session: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user),
):
    # Busca todos os centros esportivos do dono
    sports_centers = get_all_sports_centers_by_user_id_service(session, owner_id)

    # Se não existir nenhum, retorna erro 404
    if not sports_centers:
        raise HTTPException(
            status_code=404, detail="Nenhum centro esportivo encontrado para este dono."
        )

    # Retorna os dados dos centros esportivos
    return sports_centers


@sports_center_router.get("/city/{city_name}")
async def get_sports_centers_by_city(
    city_name: str, session: Session = Depends(get_db)
):
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"city": city_name, "format": "json", "limit": 1}
        response = requests.get(
            url, params=params, headers={"User-Agent": "BolaMarcadaApp/1.0"}
        )
        data = response.json()

        if not data:
            raise HTTPException(status_code=404, detail="Cidade não encontrada.")

        bbox = data[0]["boundingbox"]
        lat_min, lat_max = float(bbox[0]), float(bbox[1])
        lon_min, lon_max = float(bbox[2]), float(bbox[3])

        results = get_sports_center_by_city_service(
            session, lat_min, lat_max, lon_min, lon_max
        )

        if not results:
            raise HTTPException(
                status_code=404, detail="Nenhum centro encontrado nessa cidade."
            )

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar centros: {str(e)}")


@sports_center_router.patch("/update/{sports_center_id}")
async def update_sports_center(
    sports_center_id: int,
    sports_center_update: SportsCenterUpdate,
    session: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user),
):
    try:
        updated = update_sports_center_service(
            session, sports_center_id, sports_center_update
        )
        return updated
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=400, detail=f"Erro ao atualizar centro esportivo: {str(e)}"
        )


@sports_center_router.delete("/{sports_center_id}")
async def delete_sports_center(
    sports_center_id: int,
    session: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user),
):
    try:
        # Chama o método que tenta deletar o centro esportivo
        delete_sports_center_by_id(session, sports_center_id)
        return {"message": "Centro esportivo deletado com sucesso."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=400, detail=f"Erro ao deletar centro esportivo: {str(e)}"
        )
