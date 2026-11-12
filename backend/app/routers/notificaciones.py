"""
Router de Notificaciones — REQUERIMIENTO 6 (Trabajo autónomo)
=============================================================
Consulta y gestión de las notificaciones generadas automáticamente
para el solicitante cuando cambia el estado de su ticket (asignación
de técnico, cierre o reapertura del ticket).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/notificaciones", tags=["Notificaciones"])


def _cargar_relaciones(query):
    """
    Función auxiliar que incluye la información del usuario destinatario
    mediante joinedload en las consultas de notificaciones.
    """
    return query.options(joinedload(models.Notificacion.usuario))


@router.get("/", response_model=list[schemas.NotificacionOut])
def listar_notificaciones(
    usuario_id: int | None = None,
    solo_no_leidas: bool = False,
    db: Session = Depends(get_db),
):
    """
    Lista las notificaciones del sistema ordenadas de la más reciente a la
    más antigua. Permite filtrar opcionalmente por usuario_id y por estado
    de lectura (solo_no_leidas=True).
    """
    query = _cargar_relaciones(db.query(models.Notificacion))
    if usuario_id is not None:
        query = query.filter(models.Notificacion.usuario_id == usuario_id)
    if solo_no_leidas:
        query = query.filter(models.Notificacion.leida.is_(False))
    return query.order_by(models.Notificacion.fecha.desc(), models.Notificacion.id.desc()).all()


@router.get("/usuario/{usuario_id}", response_model=list[schemas.NotificacionOut])
def listar_notificaciones_usuario(
    usuario_id: int,
    solo_no_leidas: bool = False,
    db: Session = Depends(get_db),
):
    """
    Obtiene todas las notificaciones dirigidas a un usuario solicitante específico,
    utilizado para el polling periódico desde la app móvil (Requerimiento 6).
    """
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    query = _cargar_relaciones(db.query(models.Notificacion)).filter(
        models.Notificacion.usuario_id == usuario_id
    )
    if solo_no_leidas:
        query = query.filter(models.Notificacion.leida.is_(False))
    return query.order_by(models.Notificacion.fecha.desc(), models.Notificacion.id.desc()).all()


@router.patch("/{notificacion_id}/leer", response_model=schemas.NotificacionOut)
def marcar_notificacion_leida(notificacion_id: int, db: Session = Depends(get_db)):
    """
    Marca una notificación específica como leída (leida=True) cuando el
    usuario la toca en el centro de notificaciones.
    """
    notificacion = (
        _cargar_relaciones(db.query(models.Notificacion))
        .filter(models.Notificacion.id == notificacion_id)
        .first()
    )
    if not notificacion:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    notificacion.leida = True
    db.commit()
    db.refresh(notificacion)
    return notificacion


@router.patch("/usuario/{usuario_id}/leer-todas")
def marcar_todas_leidas_usuario(usuario_id: int, db: Session = Depends(get_db)):
    """
    Marca de forma masiva todas las notificaciones pendientes de lectura
    de un usuario específico como leídas y retorna la cantidad actualizada.
    """
    actualizadas = (
        db.query(models.Notificacion)
        .filter(
            models.Notificacion.usuario_id == usuario_id,
            models.Notificacion.leida.is_(False),
        )
        .update({"leida": True}, synchronize_session=False)
    )
    db.commit()
    return {"usuario_id": usuario_id, "marcadas_leidas": actualizadas}
