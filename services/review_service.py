from sqlalchemy.orm import Session
from models.models import Review
from schemas.review_schemas import ReviewCreate


def create_review_service(db: Session, data: ReviewCreate) -> int:
    """Cria uma nova review no banco."""

    # Cria a nova review
    new_review = Review(**data.dict())
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    return new_review.id


def get_review_by_id(db: Session, review_id: int) -> Review | None:
    """Retorna uma review pelo ID, ou None se não existir."""
    return db.query(Review).filter_by(id=review_id).first()


def delete_review_by_id(db: Session, review_id: int) -> None:
    """Deleta uma review pelo ID. Lança ValueError se não existir."""
    review = get_review_by_id(db, review_id)
    if not review:
        raise ValueError("Review não encontrada")

    db.delete(review)
    db.commit()
