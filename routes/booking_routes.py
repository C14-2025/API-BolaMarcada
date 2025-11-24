from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from schemas.booking_schemas import BookingCreate
from services.booking_service import (
    get_booking_by_id,
    create_booking_service,
    delete_booking_by_id,
)

booking_router = APIRouter(prefix="/bookings", tags=["bookings"])


@booking_router.post("/create", status_code=201)
async def create_booking(
    booking_create: BookingCreate, session: Session = Depends(get_db)
):
    try:
        new_booking_id = create_booking_service(session, booking_create)
        return {"message": "Reserva criada com sucesso.", "id": new_booking_id}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao criar reserva: {str(e)}")


@booking_router.get("/{booking_id}")
async def get_booking(booking_id: int, session: Session = Depends(get_db)):
    # Busca a reserva pelo ID
    booking = get_booking_by_id(session, booking_id)

    # Se não existir, retorna erro 404
    if not booking:
        raise HTTPException(status_code=404, detail="Reserva não encontrada.")

    # Retorna os dados da reserva
    return booking


@booking_router.patch("/{booking_id}")
async def update_booking(
    booking_id: int,
    booking_update: BookingCreate,
    session: Session = Depends(get_db),
):
    try:
        # Tenta buscar a reserva existente
        existing_booking = get_booking_by_id(session, booking_id)
        if not existing_booking:
            raise HTTPException(status_code=404, detail="Reserva não encontrada.")

        # Atualiza os campos da reserva existente
        for key, value in booking_update.dict(exclude_unset=True).items():
            setattr(existing_booking, key, value)

        session.commit()
        session.refresh(existing_booking)
        return {"message": "Reserva atualizada com sucesso."}
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao atualizar reserva: {str(e)}")


@booking_router.delete("/{booking_id}")
async def delete_booking(booking_id: int, session: Session = Depends(get_db)):
    try:
        # Chama o método que tenta deletar a reserva
        delete_booking_by_id(session, booking_id)
        return {"message": "Reserva deletada com sucesso."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=400, detail=f"Erro ao deletar reserva: {str(e)}"
        )
