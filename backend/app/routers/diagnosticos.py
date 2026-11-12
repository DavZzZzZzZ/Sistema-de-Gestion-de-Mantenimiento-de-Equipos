"""
Router de Diagnósticos — REQUERIMIENTO 4 (Sesión 3)
=====================================================
Registro del diagnóstico técnico de un ticket: descripción del
problema encontrado, mano de obra y los repuestos utilizados
(relación diagnóstico-repuestos). Al registrar el diagnóstico se
descuenta automáticamente el stock de cada repuesto usado y, si el
ticket estaba "en_proceso", se dan por finalizadas las labores
técnicas (el cierre formal del ticket sigue siendo una acción aparte
mediante el endpoint de cambio de estado).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/diagnosticos", tags=["Diagnósticos"])


def _cargar_relaciones(query):
    """
    Función auxiliar que configura la carga ansiosa (eager loading con joinedload)
    de los repuestos utilizados y el detalle de cada repuesto asociado al diagnóstico.
    """
    return query.options(
        joinedload(models.Diagnostico.repuestos_usados).joinedload(
            models.DiagnosticoRepuesto.repuesto
        )
    )


@router.get("/", response_model=list[schemas.DiagnosticoOut])
def listar_diagnosticos(db: Session = Depends(get_db)):
    """
    Lista todos los diagnósticos técnicos registrados en el sistema,
    incluyendo el detalle de repuestos usados, del más reciente al más antiguo.
    """
    return _cargar_relaciones(db.query(models.Diagnostico)).order_by(
        models.Diagnostico.id.desc()
    ).all()


@router.get("/ticket/{ticket_id}", response_model=list[schemas.DiagnosticoOut])
def listar_diagnosticos_por_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """
    Obtiene todos los diagnósticos técnicos asociados a un ticket específico
    junto con la lista de repuestos utilizados en cada intervención.
    """
    return _cargar_relaciones(db.query(models.Diagnostico)).filter(
        models.Diagnostico.ticket_id == ticket_id
    ).all()


@router.post("/", response_model=schemas.DiagnosticoOut, status_code=201)
def crear_diagnostico(datos: schemas.DiagnosticoCreate, db: Session = Depends(get_db)):
    """
    Registra un diagnóstico técnico para un ticket y descuenta en una única
    transacción el stock de cada repuesto utilizado (Requerimiento 4).
    Si algún repuesto no existe o no cuenta con stock suficiente, se revierte
    toda la operación (db.rollback) y se responde con error HTTP 400/404.
    """
    ticket = db.query(models.Ticket).filter(models.Ticket.id == datos.ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="El ticket indicado no existe")

    tecnico = db.query(models.Usuario).filter(
        models.Usuario.id == datos.tecnico_id,
        models.Usuario.rol == models.RolUsuario.tecnico,
    ).first()
    if not tecnico:
        raise HTTPException(status_code=400, detail="El usuario indicado no es un técnico válido")

    nuevo = models.Diagnostico(
        ticket_id=datos.ticket_id,
        tecnico_id=datos.tecnico_id,
        descripcion=datos.descripcion,
        costo_mano_obra=datos.costo_mano_obra,
    )
    db.add(nuevo)
    db.flush()  # para obtener nuevo.id antes del commit

    for item in datos.repuestos:
        repuesto = db.query(models.Repuesto).filter(models.Repuesto.id == item.repuesto_id).first()
        if not repuesto:
            db.rollback()
            raise HTTPException(status_code=404, detail=f"Repuesto {item.repuesto_id} no existe")
        if repuesto.stock < item.cantidad:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuficiente de '{repuesto.nombre}' (disponible: {repuesto.stock})",
            )
        repuesto.stock -= item.cantidad
        detalle = models.DiagnosticoRepuesto(
            diagnostico_id=nuevo.id, repuesto_id=item.repuesto_id, cantidad=item.cantidad
        )
        db.add(detalle)

    db.commit()
    db.refresh(nuevo)
    return _cargar_relaciones(db.query(models.Diagnostico)).filter(
        models.Diagnostico.id == nuevo.id
    ).first()


# ---------------------------------------------------------------------------
# Nota (Requerimiento 5 — Reportes y Estadísticas):
# El endpoint GET /api/reportes/resumen fue implementado en el router dedicado
# `backend/app/routers/reportes.py` usando func.count(), func.avg(),
# func.sum() y group_by() de SQLAlchemy.
# ---------------------------------------------------------------------------

