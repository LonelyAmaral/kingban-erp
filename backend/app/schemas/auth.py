"""Auth schemas."""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    username: str
    full_name: str
    email: str | None
    role: str
    tenant_id: int
    is_active: bool

    model_config = {"from_attributes": True}


class RegisterRequest(BaseModel):
    username: str
    password: str
    full_name: str
    email: str | None = None
    role: str = "vendedor"
