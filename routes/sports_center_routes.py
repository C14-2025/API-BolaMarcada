from fastapi import APIRouter, HTTPException
from schemas.sports_center_schemas import SportsCenterCreate, SportsCenterResponse
from sqlalchemy.orm import Session
from core.database import get_db
from fastapi import Depends
from services.sports_center_service import (
    create_sports_center_service,
    get_sports_center_by_id,
    delete_sports_center_by_id,
)

sports_center_router = APIRouter(prefix="/sports_center", tags=["sports_center"])


@sports_center_router.post("/create", status_code=201)
async def create_sports_center(
    sports_center_create: SportsCenterCreate,
    session: Session = Depends(get_db),
):
    try:
        new_id = create_sports_center_service(session, sports_center_create)
        return {"message": "Centro esportivo criado com sucesso.","id": new_id}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao criar centro esportivo: {str(e)}")


@sports_center_router.get("/{sports_center_id}", response_model=SportsCenterResponse)
async def get_sports_center(sports_center_id: int, session: Session = Depends(get_db)):

    # Busca o centro esportivo pelo ID
    sports_center = get_sports_center_by_id(session, sports_center_id)

    # Se não existir, retorna erro 404
    if not sports_center:
        raise HTTPException(status_code=404, detail="Centro esportivo não encontrado.")

    # Retorna os dados do centro esportivo
    return sports_center


@sports_center_router.delete("/{sports_center_id}")
async def delete_sports_center(sports_center_id: int, session: Session = Depends(get_db)):
    try:
        # Chama o método que tenta deletar o centro esportivo
        delete_sports_center_by_id(session, sports_center_id)
        return {"message": "Centro esportivo deletado com sucesso."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao deletar centro esportivo: {str(e)}")
