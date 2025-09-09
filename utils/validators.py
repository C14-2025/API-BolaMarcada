import re

def validate_password(value: str) -> str:
    if len(value) < 8 or len(value) > 50:
        raise ValueError("Senha deve ter entre 8 e 50 caracteres")
    if not re.search(r"[A-Z]", value):
        raise ValueError("Senha deve ter ao menos uma letra maiúscula")
    if not re.search(r"[a-z]", value):
        raise ValueError("Senha deve ter ao menos uma letra minúscula")
    if not re.search(r"\d", value):
        raise ValueError("Senha deve ter ao menos um número")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
        raise ValueError("Senha deve ter ao menos um caractere especial")
    return value

def validate_cpf(value: str) -> str:
    if not re.match(r"^\d{11}$", value):
        raise ValueError("CPF deve ter exatamente 11 dígitos")
    return value