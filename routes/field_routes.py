from fastapi import APIRouter, HTTPException
from schemas.field_schemas import FieldCreate, FieldUpdate
from sqlalchemy.orm import Session
from core.database import get_db
from fastapi import Depends
from services.field_service import (
    create_field_service,
    get_field_by_id,
    delete_field_by_id,
)

field_router = APIRouter(prefix="/field", tags=["field"])

@field_router.post("/create", status_code=201)
async def create_field(
    field_create: FieldCreate,
    session: Session = Depends(get_db),
):
    try:
        new_id = create_field_service(session, field_create)
        return {"message": "Campo criado com sucesso.","id": new_id}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao criar campo: {str(e)}")
    
@field_router.get("/{field_id}")
async def get_field(field_id: int, session: Session = Depends(get_db)):
    # Busca o campo pelo ID
    field = get_field_by_id(session, field_id)

    # Se não existir, retorna erro 404
    if not field:
        raise HTTPException(status_code=404, detail="Campo não encontrado.")

    # Retorna os dados do campo
    return field

@field_router.delete("/{field_id}")
async def delete_field(field_id: int, session: Session = Depends(get_db)):
    try:
        # Chama o método que tenta deletar o campo
        delete_field_by_id(session, field_id)
        return {"message": "Campo deletado com sucesso."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao deletar campo: {str(e)}")
    
@field_router.patch("/{field_id}")
async def update_field(field_id: int, field_update: FieldUpdate, session: Session = Depends(get_db)):
    try:
        # Busca o campo pelo ID
        field = get_field_by_id(session, field_id)
        if not field:
            raise HTTPException(status_code=404, detail="Campo não encontrado.")

        # Atualiza os campos fornecidos
        for key, value in field_update.dict(exclude_unset=True).items():
            setattr(field, key, value)

        session.commit()
        session.refresh(field)
        return {"message": "Campo atualizado com sucesso.", "field": field}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao atualizar campo: {str(e)}")