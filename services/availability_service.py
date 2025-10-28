from sqlalchemy.orm import Session
from models import Availability
from schemas.availability_schemas import AvailabilityCreate


def create_availability_service(db: Session, availability_data: AvailabilityCreate):
    # Verifica se a disponibilidade já existe para o campo e horário especificados
    existing_availability = (
        db.query(Availability)
        .filter(
            Availability.field_id == availability_data.field_id,
            Availability.start_time == availability_data.start_time,
            Availability.end_time == availability_data.end_time,
        )
        .first()
    )
    if existing_availability:
        raise ValueError("Disponibilidade já existe para esse campo e horário.")

    new_availability = Availability(**availability_data.dict())
    db.add(new_availability)
    db.commit()
    db.refresh(new_availability)
    return new_availability.id


def get_availability_by_id(db: Session, availability_id: int) -> Availability:
    return db.query(Availability).filter(Availability.id == availability_id).first()


def delete_availability_by_id(db: Session, availability_id: int) -> None:
    """Deleta um campo pelo ID."""
    availability = get_availability_by_id(db, availability_id)
    if not availability:
        raise ValueError("Disponibilidade não encontrada.")
    db.delete(availability)
    db.commit()
