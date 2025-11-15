from sqlalchemy.orm import Session
from models import Booking
from schemas.booking_schemas import BookingCreate


def create_booking_service(db: Session, booking_data: BookingCreate):
    # Verifica se já existe uma reserva para o mesmo campo e horário
    existing_booking = (
        db.query(Booking)
        .filter(
            Booking.field_id == booking_data.field_id,
            Booking.booking_date == booking_data.booking_date,
            Booking.start_time == booking_data.start_time,
            Booking.end_time == booking_data.end_time,
        )
        .first()
    )
    if existing_booking:
        raise ValueError("Já existe uma reserva para esse campo e horário.")

    new_booking = Booking(**booking_data.dict())
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    return new_booking.id

def get_booking_by_id(db: Session, booking_id: int) -> Booking:
    return db.query(Booking).filter(Booking.id == booking_id).first()
  
def delete_booking_by_id(db: Session, booking_id: int) -> None:
    """Deleta uma reserva pelo ID."""
    booking = get_booking_by_id(db, booking_id)
    if not booking:
        raise ValueError("Reserva não encontrada.")
    db.delete(booking)
    db.commit()
