from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from schemas.review_schemas import ReviewCreate
from core.database import get_db
from services.review_service import (
    create_review_service,
    get_review_by_id,
    delete_review_by_id,
)

review_router = APIRouter(prefix="/review", tags=["review"])


@review_router.post("/create", status_code=201)
async def create_review(
    review_create: ReviewCreate,
    session: Session = Depends(get_db),
):
    try:
        new_id = create_review_service(session, review_create)
        return {"message": "Review criada com sucesso.", "id": new_id}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao criar review: {str(e)}")


@review_router.get("/{review_id}")
async def get_review(review_id: int, session: Session = Depends(get_db)):

    # Busca a review pelo ID
    review = get_review_by_id(session, review_id)

    # Se não existir, retorna erro 404
    if not review:
        raise HTTPException(status_code=404, detail="Review não encontrada.")

    # Retorna os dados da review
    return review


@review_router.delete("/{review_id}")
async def delete_review(review_id: int, session: Session = Depends(get_db)):
    try:
        # Chama o método que tenta deletar a review
        delete_review_by_id(session, review_id)
        return {"message": "Review deletada com sucesso."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao deletar review: {str(e)}")