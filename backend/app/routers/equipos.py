"""
Router de Equipos — REQUERIMIENTO 1 (Sesión 1)
================================================
CRUD completo de equipos: registrar, listar, consultar, editar y dar
de baja (cambio de estado, no eliminación física) un equipo.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/equipos", tags=["Equipos"])


@router.get("/", response_model=list[schemas.EquipoOut])
def listar_equipos(db: Session = Depends(get_db)):
    """
    Lista todos los equipos registrados en el sistema ordenados del más
    reciente al más antiguo (por ID descendente).
    """
    return db.query(models.Equipo).order_by(models.Equipo.id.desc()).all()


@router.post("/", response_model=schemas.EquipoOut, status_code=201)
def crear_equipo(equipo: schemas.EquipoCreate, db: Session = Depends(get_db)):
    """
    Registra un nuevo equipo en el inventario con estado 'operativo' por defecto.
    Recibe nombre, tipo, marca, modelo, número de serie y ubicación.
    """
    nuevo = models.Equipo(**equipo.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@router.get("/{equipo_id}", response_model=schemas.EquipoOut)
def obtener_equipo(equipo_id: int, db: Session = Depends(get_db)):
    """
    Obtiene el detalle de un equipo específico a partir de su identificador único.
    Lanza error HTTP 404 si el equipo no existe.
    """
    equipo = db.query(models.Equipo).filter(models.Equipo.id == equipo_id).first()
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    return equipo


@router.put("/{equipo_id}", response_model=schemas.EquipoOut)
def actualizar_equipo(equipo_id: int, datos: schemas.EquipoUpdate, db: Session = Depends(get_db)):
    """
    Actualiza parcialmente o totalmente los atributos de un equipo existente.
    Solo modifica los campos enviados en la petición (exclude_unset=True).
    """
    equipo = db.query(models.Equipo).filter(models.Equipo.id == equipo_id).first()
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(equipo, campo, valor)
    db.commit()
    db.refresh(equipo)
    return equipo


@router.delete("/{equipo_id}", status_code=204)
def dar_de_baja_equipo(equipo_id: int, db: Session = Depends(get_db)):
    """Baja lógica: no se elimina el registro (hay tickets asociados),
    se marca el equipo como 'de_baja'."""
    equipo = db.query(models.Equipo).filter(models.Equipo.id == equipo_id).first()
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    equipo.estado = models.EstadoEquipo.de_baja
    db.commit()
    return None
