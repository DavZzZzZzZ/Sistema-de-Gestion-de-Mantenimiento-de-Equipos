"""
Sistema de Gestión de Mantenimiento de Equipos (Helpdesk Técnico)
Universidad Piloto de Colombia — Programación para Dispositivos Convergentes
Docente: Edicson Pineda Cadena

Punto de entrada de la API FastAPI.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models
from .database import engine
from .routers import (
    usuarios,
    equipos,
    tickets,
    repuestos,
    diagnosticos,
    notificaciones,
    reportes,
)

# Crea las tablas en PostgreSQL si aún no existen (para un laboratorio de
# clase esto es suficiente; en un proyecto productivo se usaría Alembic
# para versionar migraciones).
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Helpdesk Técnico — Universidad Piloto de Colombia",
    description=(
        "API REST del Sistema de Gestión de Mantenimiento de Equipos. "
        "Asignatura: Programación para Dispositivos Convergentes. "
        "Docente: Edicson Pineda Cadena."
    ),
    version="1.0.0",
)

# En clase el app móvil React Native (Expo web) corre en otro puerto (http://localhost:8081
# o el puerto que asigne Vite), por lo que se habilita CORS abierto.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(usuarios.router)
app.include_router(equipos.router)
app.include_router(tickets.router)
app.include_router(repuestos.router)
app.include_router(diagnosticos.router)
app.include_router(notificaciones.router)
app.include_router(reportes.router)


@app.get("/", tags=["Estado del servicio"])
def raiz():
    """
    Endpoint raíz de verificación de la API.
    Retorna un mensaje informativo indicando que el servicio está en ejecución
    y la ruta hacia la documentación interactiva Swagger (/docs).
    """
    return {
        "mensaje": "API Helpdesk Técnico UPiloto en ejecución",
        "documentacion": "/docs",
    }


@app.get("/health", tags=["Estado del servicio"])
def salud():
    """
    Endpoint de chequeo de salud (healthcheck) del contenedor o servidor.
    Retorna el estado operativo {"status": "ok"}.
    """
    return {"status": "ok"}
