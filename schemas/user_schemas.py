from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
import uuid
from utils.validators import validate_password, validate_cpf


class UserBase(BaseModel):
    name: str
    email: EmailStr
    cpf: str = Field(..., example="12345678901")
    phone: Optional[str] = None
    is_active: bool = True
    is_admin: bool = False
    avatar: Optional[str] = None

    model_config = {"from_attributes": True}

    # Aplica a validação CPF chamando a função externa
    _validate_cpf = field_validator("cpf", mode="before")(validate_cpf)


class UserSignUp(UserBase):
    password: str = Field(..., example="Abcd1234!")

    # Aplica a validação senha chamando a função externa
    _validate_password = field_validator("password", mode="before")(validate_password)


class UserSignIn(BaseModel):
    email: EmailStr
    password: str = Field(..., example="Abcd1234!")


class UserResponseToken(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: uuid.UUID
    is_active: bool
    is_admin: bool


class UserUpdateMe(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
