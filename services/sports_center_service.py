from sqlalchemy.orm import Session
from models import SportsCenter
from schemas.sports_center_schemas import SportsCenterCreate


# CRUD
def create_sports_center_service(db: Session, data: SportsCenterCreate) -> int:
    """Cria um novo centro esportivo no banco."""

    # Verifica se já existe um centro esportivo com o mesmo CNPJ
    sports_center = db.query(SportsCenter).filter_by(cnpj=data.cnpj).first()

    # Se existir, lança um erro
    if sports_center:
        raise ValueError("CNPJ já cadastrado")

    # Cria o novo centro esportivo
    new_sports_center = SportsCenter(**data.dict())
    db.add(new_sports_center)
    db.commit()
    db.refresh(new_sports_center)
    return new_sports_center.id


def get_sports_center_by_id(db: Session, sports_center_id: int) -> SportsCenter | None:
    """Retorna um centro esportivo pelo ID, ou None se não existir."""
    return db.query(SportsCenter).filter_by(id=sports_center_id).first()


def delete_sports_center_by_id(db: Session, sports_center_id: int) -> None:
    """Deleta um centro esportivo pelo ID. Lança ValueError se não existir."""
    sports_center = get_sports_center_by_id(db, sports_center_id)
    if not sports_center:
        raise ValueError("Centro esportivo não encontrado")

    db.delete(sports_center)
    db.commit()
