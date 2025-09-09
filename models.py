from sqlalchemy import (
    DateTime,
    Numeric,
    Text,
    Column,
    String,
    Integer,
    Boolean,
    ForeignKey,
)
from database import Base


# Tabela Usuários
class User(Base):
    __tablename__ = "users"

    # Keys
    id = Column("id", Integer, primary_key=True, autoincrement=True)

    # Campos
    name = Column("name", String, nullable=False)
    email = Column("email", String, nullable=False, unique=True)
    password = Column("password", String, nullable=False)
    cpf = Column("cpf", String, nullable=False)
    phone = Column("phone", String)
    active = Column("active", Boolean, default=True)
    admin = Column("admin", Boolean, default=False)

    def __init__(self, name, email, password, cpf, phone, active=True, admin=False):
        self.name = name
        self.email = email
        self.password = password
        self.cpf = cpf
        self.phone = phone
        self.active = active
        self.admin = admin


# Tabela de Espaço Esportivo
class SportsCenter(Base):
    __tablename__ = "sports_centers"

    # Keys
    id = Column("id", Integer, primary_key=True, autoincrement=True)
    # user_id = Column("user_id", Integer, ForeignKey("users.id"), nullable=False)

    # Campos
    name = Column("name", String, nullable=False)
    cnpj = Column("cnpj", String, unique=True, nullable=False)
    latitude = Column("latitude", Numeric(9, 6), nullable=False)
    longitude = Column("longitude", Numeric(9, 6), nullable=False)
    photo_path = Column("photo_path", String)
    description = Column("description", String)

    def __init__(
        self,
        # user_id,
        name,
        cnpj,
        latitude,
        longitude,
        photo_path=None,
        description=None,
    ):
        # self.user_id = user_id
        self.name = name
        self.cnpj = cnpj
        self.latitude = latitude
        self.longitude = longitude
        self.photo_path = photo_path
        self.description = description


# Tabela de avaliações
class Review(Base):
    __tablename__ = "reviews"

    # Keys
    id = Column("id", Integer, primary_key=True, autoincrement=True)
    field_id = Column("field_id", Integer, ForeignKey("fields.id"), nullable=False)
    user_id = Column("user_id", Integer, ForeignKey("users.id"), nullable=False)

    # Campos
    rating = Column("rating", Integer, nullable=False)
    comment = Column("comment", String)
    created_at = Column("created_at", DateTime)

    def __init__(self, field_id, user_id, rating, comment=None, created_at=None):
        self.field_id = field_id
        self.user_id = user_id
        self.rating = rating
        self.comment = comment
        self.created_at = created_at


# Tabela de campos
class Field(Base):
    __tablename__ = "fields"

    # Keys
    id = Column("id", Integer, primary_key=True, autoincrement=True)
    sports_center_id = Column(
        "sports_center_id", Integer, ForeignKey("sports_centers.id"), nullable=False
    )

    # Campos
    name = Column("name", String, nullable=False)
    field_type = Column("type", String, nullable=False)
    price_per_hour = Column("price_per_hour", Numeric, nullable=False)
    photo_path = Column("photo_path", String)
    description = Column("description", Text)

    def __init__(
        self,
        sports_center_id,
        name,
        field_type,
        price_per_hour,
        photo_path=None,
        description=None,
    ):
        self.sports_center_id = sports_center_id
        self.name = name
        self.field_type = field_type
        self.price_per_hour = price_per_hour
        self.photo_path = photo_path
        self.description = description


# Tabela de Disponibilidades
class Availability(Base):
    __tablename__ = "availabilities"

    # Keys
    id = Column("id", Integer, primary_key=True, autoincrement=True)
    field_id = Column("field_id", Integer, ForeignKey("fields.id"), nullable=False)

    # Campos
    day_of_week = Column(
        "day_of_week", Integer, nullable=False
    )  # 0 = domingo, 1 = segunda, ...
    start_time = Column("start_time", DateTime, nullable=False)
    end_time = Column("end_time", DateTime, nullable=False)

    def __init__(self, field_id, day_of_week, start_time, end_time):
        self.field_id = field_id
        self.day_of_week = day_of_week
        self.start_time = start_time
        self.end_time = end_time


# Tabela de Reservas de campo
class Booking(Base):
    __tablename__ = "bookings"

    # Keys
    id = Column("id", Integer, primary_key=True, autoincrement=True)
    user_id = Column("user_id", Integer, ForeignKey("users.id"), nullable=False)
    field_id = Column("field_id", Integer, ForeignKey("fields.id"), nullable=False)

    # Campos
    day_of_week = Column("day_of_week", Integer, nullable=False)
    start_time = Column("start_time", DateTime, nullable=False)
    status = Column("status", String, default="pending")

    def __init__(self, user_id, field_id, day_of_week, start_time, status="pending"):
        self.user_id = user_id
        self.field_id = field_id
        self.day_of_week = day_of_week
        self.start_time = start_time
        self.status = status


# alembic init alembic
# alterar env.py
# alterar alembic.ini
# alembic revision --autogenerate -m "Initial Migration"
# alembic upgrade head

# se deu erro
# deletar version e .db
# executa novamente alembic revision --autogenerate -m "Initial Migration"

# sempre quando houver alteraçao do banco, é necessario migrar:
# alembic revision --autogenerate -m "remove admin"
# alembic upgrade head
