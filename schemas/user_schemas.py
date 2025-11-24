from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
import uuid
from utils.validators import validate_password, validate_cpf
from pydantic import ConfigDict


class UserBase(BaseModel):
    name: str
    email: EmailStr
    cpf: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True
    is_admin: bool = False
    avatar: Optional[str] = None    

    model_config = ConfigDict(from_attributes=True)

    _validate_cpf = field_validator("cpf", mode="before")(validate_cpf)


class UserSignUp(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(..., json_schema_extra={"example": "Abcd1234!"})
    cpf: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None

    @field_validator("password")
    @classmethod
    def _password_ok(cls, v: Optional[str]):
        if v is None:
            return v
        validate_password(v)
        return v

    @field_validator("cpf")
    @classmethod
    def _cpf_ok(cls, v: Optional[str]):
        if v is None:
            return v
        v = v.strip()
        if not v:
            return None
        validate_cpf(v)
        return v


class UserSignIn(BaseModel):
    email: EmailStr
    password: str = Field(..., json_schema_extra={"example": "Abcd1234!"})


class UserResponseToken(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: uuid.UUID
    is_active: bool
    is_admin: bool


class UserUpdateMe(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    cpf: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None

    @field_validator("password")
    @classmethod
    def _password_ok_update(cls, v: Optional[str]):
        if v is None:
            return v
        validate_password(v)
        return v

    @field_validator("cpf")
    @classmethod
    def _cpf_ok_update(cls, v: Optional[str]):
        if v is None:
            return v
        v = v.strip()
        if not v:
            return None
        validate_cpf(v)
        return v


class UserPublic(UserBase):
    id: uuid.UUID
