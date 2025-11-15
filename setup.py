from setuptools import setup, find_packages

setup(
    name="api-bolamarcada",
    version="0.1.0",
    description="API do projeto Bola Marcada",
    author="Thomas Victor Dias Carvalho",
    author_email="thomasvictordias@outlook.com",
    packages=find_packages(include=["core", "models", "routes", "schemas", "services", "alembic"]),
    install_requires=[
        "fastapi",
        "uvicorn"
    ],
)