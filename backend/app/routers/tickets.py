"""
Router de Tickets.

REQUERIMIENTO 2 (Sesión 2): creación de una solicitud de mantenimiento
(ticket) por parte de un usuario solicitante, asociada a un equipo.

REQUERIMIENTO 3 (Sesión 2): asignación de un técnico al ticket y
cambio controlado de estado (abierto -> en_proceso -> cerrado).

REQUERIMIENTO 6 (Trabajo autónomo): generación de notificaciones al
solicitante cuando se asigna técnico o cambia el estado del ticket.

REQUERIMIENTO 7 (Trabajo autónomo): registro de auditoría en
TicketHistorial en cada cambio de estado y endpoint de línea de tiempo.

REQUERIMIENTO 8 (Trabajo autónomo): búsqueda avanzada con filtros
combinados y exportación a CSV con StreamingResponse.
"""
import csv
import io
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/tickets", tags=["Tickets"])


def _cargar_relaciones(query):
    """
    Función auxiliar que aplica carga ansiosa (joinedload) sobre las relaciones
    equipo, solicitante y técnico de la entidad Ticket para evitar consultas N+1.
    """
    return query.options(
        joinedload(models.Ticket.equipo),
        joinedload(models.Ticket.solicitante),
        joinedload(models.Ticket.tecnico),
    )


def _aplicar_filtros_tickets(
    query,
    estado: models.EstadoTicket | None = None,
    prioridad: models.PrioridadTicket | None = None,
    tecnico_id: int | None = None,
    equipo_id: int | None = None,
    solicitante_id: int | None = None,
    q: str | None = None,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
):
    """
    Aplica dinámicamente los filtros combinados de búsqueda avanzada (Requerimiento 8)
    sobre una consulta SQLAlchemy de Ticket: estado, prioridad, técnico asignado,
    equipo, solicitante, texto libre (ilike en título, descripción o equipo) y rango de fechas.
    """
    if estado:
        query = query.filter(models.Ticket.estado == estado)
    if prioridad:
        query = query.filter(models.Ticket.prioridad == prioridad)
    if tecnico_id:
        query = query.filter(models.Ticket.tecnico_id == tecnico_id)
    if equipo_id:
        query = query.filter(models.Ticket.equipo_id == equipo_id)
    if solicitante_id:
        query = query.filter(models.Ticket.solicitante_id == solicitante_id)
    if q and q.strip():
        termino = f"%{q.strip()}%"
        query = query.join(models.Ticket.equipo).filter(
            or_(
                models.Ticket.titulo.ilike(termino),
                models.Ticket.descripcion.ilike(termino),
                models.Equipo.nombre.ilike(termino),
                models.Equipo.tipo.ilike(termino),
            )
        )
    if fecha_desde:
        dt_desde = datetime.combine(fecha_desde, datetime.min.time())
        query = query.filter(models.Ticket.fecha_creacion >= dt_desde)
    if fecha_hasta:
        dt_hasta = datetime.combine(fecha_hasta, datetime.max.time())
        query = query.filter(models.Ticket.fecha_creacion <= dt_hasta)
    return query


# --- Requerimiento 2 y Requerimiento 8: consulta y búsqueda avanzada ---------
@router.get("/", response_model=list[schemas.TicketDetalleOut])
def listar_tickets(
    estado: models.EstadoTicket | None = None,
    prioridad: models.PrioridadTicket | None = None,
    tecnico_id: int | None = None,
    equipo_id: int | None = None,
    solicitante_id: int | None = None,
    q: str | None = None,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    db: Session = Depends(get_db),
):
    """
    Lista los tickets registrados junto con sus objetos relacionados (equipo,
    solicitante y técnico). Soporta tanto el filtro simple por estado (Req. 2)
    como los filtros combinados de búsqueda avanzada (Req. 8).
    """
    query = _cargar_relaciones(db.query(models.Ticket))
    query = _aplicar_filtros_tickets(
        query,
        estado=estado,
        prioridad=prioridad,
        tecnico_id=tecnico_id,
        equipo_id=equipo_id,
        solicitante_id=solicitante_id,
        q=q,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )
    return query.order_by(models.Ticket.id.desc()).all()


# --- Requerimiento 8: exportación de resultados a CSV ------------------------
@router.get("/exportar/csv")
def exportar_tickets_csv(
    estado: models.EstadoTicket | None = None,
    prioridad: models.PrioridadTicket | None = None,
    tecnico_id: int | None = None,
    equipo_id: int | None = None,
    solicitante_id: int | None = None,
    q: str | None = None,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    db: Session = Depends(get_db),
):
    """
    Genera y transmite en flujo (StreamingResponse) un archivo CSV con los
    tickets que cumplen los criterios de búsqueda avanzada indicados (Requerimiento 8).
    Incluye BOM UTF-8 para visualización directa de tildes en Microsoft Excel.
    """
    query = _cargar_relaciones(db.query(models.Ticket))
    query = _aplicar_filtros_tickets(
        query,
        estado=estado,
        prioridad=prioridad,
        tecnico_id=tecnico_id,
        equipo_id=equipo_id,
        solicitante_id=solicitante_id,
        q=q,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )
    tickets = query.order_by(models.Ticket.id.desc()).all()

    buffer = io.StringIO()
    buffer.write("\ufeff")  # BOM UTF-8 para compatibilidad con Excel
    writer = csv.writer(buffer)
    writer.writerow([
        "ID",
        "Titulo",
        "Estado",
        "Prioridad",
        "Equipo",
        "Tipo_Equipo",
        "Solicitante",
        "Tecnico_Asignado",
        "Fecha_Creacion",
        "Fecha_Cierre",
        "Descripcion",
    ])
    for t in tickets:
        writer.writerow([
            t.id,
            t.titulo,
            t.estado.value if hasattr(t.estado, "value") else t.estado,
            t.prioridad.value if hasattr(t.prioridad, "value") else t.prioridad,
            t.equipo.nombre if t.equipo else "",
            t.equipo.tipo if t.equipo else "",
            t.solicitante.nombre if t.solicitante else "",
            t.tecnico.nombre if t.tecnico else "Sin asignar",
            t.fecha_creacion.strftime("%Y-%m-%d %H:%M:%S") if t.fecha_creacion else "",
            t.fecha_cierre.strftime("%Y-%m-%d %H:%M:%S") if t.fecha_cierre else "",
            t.descripcion,
        ])

    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="tickets_helpdesk.csv"'
        },
    )


@router.post("/", response_model=schemas.TicketDetalleOut, status_code=201)
def crear_ticket(ticket: schemas.TicketCreate, db: Session = Depends(get_db)):
    """
    Crea una nueva solicitud de mantenimiento (ticket) en estado 'abierto'
    verificando que el equipo y el solicitante existan (Requerimiento 2), y
    registra el evento inicial en el historial de auditoría (Requerimiento 7).
    """
    equipo = db.query(models.Equipo).filter(models.Equipo.id == ticket.equipo_id).first()
    if not equipo:
        raise HTTPException(status_code=404, detail="El equipo indicado no existe")
    solicitante = db.query(models.Usuario).filter(models.Usuario.id == ticket.solicitante_id).first()
    if not solicitante:
        raise HTTPException(status_code=404, detail="El usuario solicitante no existe")

    nuevo = models.Ticket(**ticket.model_dump(), estado=models.EstadoTicket.abierto)
    db.add(nuevo)
    db.flush()

    # Requerimiento 7: registrar el evento inicial de creación en el historial
    historial_inicial = models.TicketHistorial(
        ticket_id=nuevo.id,
        estado_anterior=None,
        estado_nuevo=models.EstadoTicket.abierto,
        usuario_id=solicitante.id,
        comentario=f"Ticket creado por {solicitante.nombre}",
        fecha=nuevo.fecha_creacion or datetime.utcnow(),
    )
    db.add(historial_inicial)

    db.commit()
    db.refresh(nuevo)
    return _cargar_relaciones(db.query(models.Ticket)).filter(models.Ticket.id == nuevo.id).first()


@router.get("/{ticket_id}", response_model=schemas.TicketDetalleOut)
def obtener_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """
    Obtiene el detalle completo de un ticket específico por su ID, incluyendo
    los datos del equipo, solicitante y técnico asignado.
    """
    ticket = _cargar_relaciones(db.query(models.Ticket)).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    return ticket


# --- Requerimiento 7: línea de tiempo / auditoría de estados -----------------
@router.get("/{ticket_id}/historial", response_model=list[schemas.TicketHistorialOut])
def obtener_historial_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """
    Devuelve la línea de tiempo cronológica (TicketHistorial) con todos los
    cambios de estado que ha tenido un ticket (Requerimiento 7). Si el ticket
    fue creado antes de habilitar la tabla de historial, genera el evento inicial.
    """
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    eventos = (
        db.query(models.TicketHistorial)
        .options(joinedload(models.TicketHistorial.usuario))
        .filter(models.TicketHistorial.ticket_id == ticket_id)
        .order_by(models.TicketHistorial.fecha.asc(), models.TicketHistorial.id.asc())
        .all()
    )
    if not eventos:
        inicial = models.TicketHistorial(
            ticket_id=ticket.id,
            estado_anterior=None,
            estado_nuevo=models.EstadoTicket.abierto,
            usuario_id=ticket.solicitante_id,
            comentario="Ticket creado inicialmente",
            fecha=ticket.fecha_creacion or datetime.utcnow(),
        )
        db.add(inicial)
        db.commit()
        eventos = (
            db.query(models.TicketHistorial)
            .options(joinedload(models.TicketHistorial.usuario))
            .filter(models.TicketHistorial.ticket_id == ticket_id)
            .order_by(models.TicketHistorial.fecha.asc(), models.TicketHistorial.id.asc())
            .all()
        )
    return eventos


# --- Requerimiento 3: asignación de técnico y cambio de estado -------------
@router.patch("/{ticket_id}/asignar", response_model=schemas.TicketDetalleOut)
def asignar_tecnico(ticket_id: int, datos: schemas.TicketAsignar, db: Session = Depends(get_db)):
    """
    Asigna un usuario con rol 'tecnico' al ticket y pasa automáticamente su
    estado a 'en_proceso' si estaba 'abierto' (Requerimiento 3). Además,
    registra el evento en el historial (Requerimiento 7) y crea una
    notificación para el solicitante (Requerimiento 6).
    """
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    tecnico = db.query(models.Usuario).filter(
        models.Usuario.id == datos.tecnico_id,
        models.Usuario.rol == models.RolUsuario.tecnico,
    ).first()
    if not tecnico:
        raise HTTPException(status_code=400, detail="El usuario indicado no es un técnico válido")

    estado_anterior = ticket.estado
    ticket.tecnico_id = tecnico.id
    if ticket.estado == models.EstadoTicket.abierto:
        ticket.estado = models.EstadoTicket.en_proceso

    # Requerimiento 7: registrar auditoría del cambio de estado al asignar técnico
    historial = models.TicketHistorial(
        ticket_id=ticket.id,
        estado_anterior=estado_anterior,
        estado_nuevo=ticket.estado,
        usuario_id=tecnico.id,
        comentario=f"Técnico asignado: {tecnico.nombre}",
        fecha=datetime.utcnow(),
    )
    db.add(historial)

    # Requerimiento 6: notificar al solicitante que su ticket tiene técnico asignado
    notificacion = models.Notificacion(
        usuario_id=ticket.solicitante_id,
        ticket_id=ticket.id,
        titulo=f"Técnico asignado · Ticket #{ticket.id}",
        mensaje=(
            f"Se asignó al técnico {tecnico.nombre} para atender tu solicitud "
            f"'{ticket.titulo}'. El estado ahora es '{ticket.estado.value}'."
        ),
        leida=False,
        fecha=datetime.utcnow(),
    )
    db.add(notificacion)

    db.commit()
    return _cargar_relaciones(db.query(models.Ticket)).filter(models.Ticket.id == ticket_id).first()


TRANSICIONES_VALIDAS = {
    models.EstadoTicket.abierto: {models.EstadoTicket.en_proceso},
    models.EstadoTicket.en_proceso: {models.EstadoTicket.cerrado, models.EstadoTicket.abierto},
    models.EstadoTicket.cerrado: set(),  # un ticket cerrado no cambia de estado
}


@router.patch("/{ticket_id}/estado", response_model=schemas.TicketDetalleOut)
def cambiar_estado_ticket(ticket_id: int, datos: schemas.TicketCambiarEstado, db: Session = Depends(get_db)):
    """
    Cambia el estado de un ticket validando la máquina de estados definida en
    TRANSICIONES_VALIDAS (Requerimiento 3). Registra la transición en
    TicketHistorial (Requerimiento 7), genera una notificación para el
    solicitante (Requerimiento 6) y actualiza fecha_cierre cuando se cierra.
    """
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    if datos.estado not in TRANSICIONES_VALIDAS[ticket.estado]:
        raise HTTPException(
            status_code=400,
            detail=f"No es válido pasar de '{ticket.estado.value}' a '{datos.estado.value}'",
        )

    estado_anterior = ticket.estado
    ahora = datetime.utcnow()

    # Requerimiento 7: registrar el cambio en la tabla de historial/auditoría
    historial = models.TicketHistorial(
        ticket_id=ticket.id,
        estado_anterior=estado_anterior,
        estado_nuevo=datos.estado,
        usuario_id=ticket.tecnico_id or ticket.solicitante_id,
        comentario=(
            "Ticket cerrado tras atención técnica"
            if datos.estado == models.EstadoTicket.cerrado
            else f"Cambio de estado de '{estado_anterior.value}' a '{datos.estado.value}'"
        ),
        fecha=ahora,
    )
    db.add(historial)

    # Requerimiento 6: generar una notificación para el solicitante
    etiqueta_accion = (
        "ha sido cerrado"
        if datos.estado == models.EstadoTicket.cerrado
        else f"cambió a estado '{datos.estado.value}'"
    )
    notificacion = models.Notificacion(
        usuario_id=ticket.solicitante_id,
        ticket_id=ticket.id,
        titulo=f"Estado actualizado · Ticket #{ticket.id}",
        mensaje=(
            f"Tu solicitud '{ticket.titulo}' {etiqueta_accion} "
            f"(estado anterior: '{estado_anterior.value}')."
        ),
        leida=False,
        fecha=ahora,
    )
    db.add(notificacion)

    ticket.estado = datos.estado
    if datos.estado == models.EstadoTicket.cerrado:
        ticket.fecha_cierre = ahora
    elif datos.estado == models.EstadoTicket.abierto:
        ticket.fecha_cierre = None
    db.commit()
    return _cargar_relaciones(db.query(models.Ticket)).filter(models.Ticket.id == ticket_id).first()

