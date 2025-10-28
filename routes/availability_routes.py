from fastapi import APIRouter, HTTPException
from schemas.availability_schemas import AvailabilityCreate
from services.availability_service import (
    create_availability_service,
    delete_availability_by_id,
    get_availability_by_id,
)
from fastapi import Depends
from core.database import get_db
from sqlalchemy.orm import Session

availability_router = APIRouter(prefix="/availability", tags=["availability"])


@availability_router.post("/create", status_code=201)
async def create_availability(
    availability_create: AvailabilityCreate,
    session: Session = Depends(get_db),
):
    try:
        new_id = create_availability_service(session, availability_create)
        return {"message": "Disponibilidade criada com sucesso.", "id": new_id}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=400, detail=f"Erro ao criar disponibilidade: {str(e)}"
        )


@availability_router.get("/{availability_id}")
async def get_availability(availability_id: int, session: Session = Depends(get_db)):
    # Busca a disponibilidade pelo ID
    availability = get_availability_by_id(session, availability_id)

    # Se não existir, retorna erro 404
    if not availability:
        raise HTTPException(status_code=404, detail="Disponibilidade não encontrada.")

    # Retorna os dados da disponibilidade
    return availability


@availability_router.delete("/{availability_id}")
async def delete_availability(availability_id: int, session: Session = Depends(get_db)):
    try:
        # Chama o método que tenta deletar a disponibilidade
        delete_availability_by_id(session, availability_id)
        return {"message": "Disponibilidade deletada com sucesso."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=400, detail=f"Erro ao deletar disponibilidade: {str(e)}"
        )
