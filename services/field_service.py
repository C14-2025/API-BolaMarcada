from sqlalchemy.orm import Session
from models import Field
from schemas.field_schemas import FieldCreate


# CRUD para campos
def create_field_service(db: Session, field_data: FieldCreate) -> int:
    """Cria um novo campo no banco."""
    # Verifica se o campo já existe no centro esportivo
    existing_field = (
        db.query(Field)
        .filter(
            Field.sports_center_id == field_data.sports_center_id,
            Field.name == field_data.name,
        )
        .first()
    )
    if existing_field:
        raise ValueError("Campo com esse nome já existe nesse centro esportivo.")

    new_field = Field(**field_data.dict())
    db.add(new_field)
    db.commit()
    db.refresh(new_field)
    return new_field.id

def get_field_by_id(db: Session, field_id: int) -> Field:
    """Busca um campo pelo ID."""
    return db.query(Field).filter(Field.id == field_id).first()

def delete_field_by_id(db: Session, field_id: int) -> None:
    """Deleta um campo pelo ID."""
    field = get_field_by_id(db, field_id)
    if not field:
        raise ValueError("Campo não encontrado.")
    db.delete(field)
    db.commit()