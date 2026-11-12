"""
Router de Reportes y Estadísticas — REQUERIMIENTO 5 (Trabajo autónomo)
======================================================================
Panel de estadísticas agregadas del helpdesk usando funciones de
agregación de SQLAlchemy (func.count, func.avg, func.sum y group_by):
    - Cantidad de tickets por estado (abierto, en_proceso, cerrado)
    - Cantidad de tickets por prioridad (baja, media, alta, critica)
    - Equipo con mayor cantidad de fallas reportadas y ranking top
    - Tiempo promedio de resolución en horas (fecha_cierre - fecha_creacion)
    - Costo total de mantenimiento (mano de obra + repuestos utilizados)
"""
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/reportes", tags=["Reportes"])


@router.get("/resumen", response_model=schemas.ReporteResumenOut)
def obtener_resumen_reportes(db: Session = Depends(get_db)):
    """
    Calcula y retorna el resumen estadístico agregado del Helpdesk (Requerimiento 5):
    - Total de tickets registrados.
    - Conteo de tickets agrupados por estado y por prioridad (func.count + group_by).
    - Equipo con mayor cantidad de fallas reportadas y top 5 de equipos.
    - Tiempo promedio de resolución en horas (fecha_cierre - fecha_creacion con func.avg).
    - Costo total de mano de obra, repuestos utilizados y mantenimiento general.
    """
    # 1. Total de tickets
    total_tickets = db.query(func.count(models.Ticket.id)).scalar() or 0

    # 2. Cantidad de tickets agrupados por estado (func.count + group_by)
    filas_estado = (
        db.query(models.Ticket.estado, func.count(models.Ticket.id))
        .group_by(models.Ticket.estado)
        .all()
    )
    mapa_estados = {estado: 0 for estado in models.EstadoTicket}
    for estado_db, conteo in filas_estado:
        mapa_estados[estado_db] = int(conteo)

    tickets_por_estado = [
        schemas.TicketsPorEstadoItem(estado=est, cantidad=mapa_estados[est])
        for est in [
            models.EstadoTicket.abierto,
            models.EstadoTicket.en_proceso,
            models.EstadoTicket.cerrado,
        ]
    ]

    # 3. Cantidad de tickets agrupados por prioridad (func.count + group_by)
    filas_prioridad = (
        db.query(models.Ticket.prioridad, func.count(models.Ticket.id))
        .group_by(models.Ticket.prioridad)
        .all()
    )
    mapa_prioridad = {p: 0 for p in models.PrioridadTicket}
    for prio_db, conteo in filas_prioridad:
        mapa_prioridad[prio_db] = int(conteo)

    tickets_por_prioridad = [
        schemas.TicketsPorPrioridadItem(prioridad=p, cantidad=mapa_prioridad[p])
        for p in [
            models.PrioridadTicket.baja,
            models.PrioridadTicket.media,
            models.PrioridadTicket.alta,
            models.PrioridadTicket.critica,
        ]
    ]

    # 4. Equipos con más fallas reportadas (func.count + group_by + order_by)
    filas_equipos = (
        db.query(
            models.Equipo,
            func.count(models.Ticket.id).label("total_tickets"),
        )
        .join(models.Ticket, models.Ticket.equipo_id == models.Equipo.id)
        .group_by(models.Equipo.id)
        .order_by(func.count(models.Ticket.id).desc(), models.Equipo.id.asc())
        .limit(5)
        .all()
    )

    equipos_top_fallas = [
        schemas.EquipoMasFallasOut(
            equipo_id=eq.id,
            nombre=eq.nombre,
            tipo=eq.tipo,
            ubicacion=eq.ubicacion,
            total_tickets=int(total),
        )
        for eq, total in filas_equipos
    ]
    equipo_mas_fallas = equipos_top_fallas[0] if equipos_top_fallas else None

    # 5. Tiempo promedio de resolución en horas (fecha_cierre - fecha_creacion)
    # Se calcula con func.avg() sobre la diferencia en segundos (epoch) en PostgreSQL
    tiempo_promedio_horas = None
    try:
        promedio_segundos = (
            db.query(
                func.avg(
                    func.extract("epoch", models.Ticket.fecha_cierre)
                    - func.extract("epoch", models.Ticket.fecha_creacion)
                )
            )
            .filter(
                models.Ticket.estado == models.EstadoTicket.cerrado,
                models.Ticket.fecha_cierre.isnot(None),
            )
            .scalar()
        )
        if promedio_segundos is not None:
            tiempo_promedio_horas = round(float(promedio_segundos) / 3600.0, 2)
    except Exception:
        # Fallback agnóstico del motor si extract('epoch', ...) no está disponible
        cerrados = (
            db.query(models.Ticket)
            .filter(
                models.Ticket.estado == models.EstadoTicket.cerrado,
                models.Ticket.fecha_cierre.isnot(None),
            )
            .all()
        )
        if cerrados:
            diffs = [
                (t.fecha_cierre - t.fecha_creacion).total_seconds() / 3600.0
                for t in cerrados
                if t.fecha_cierre and t.fecha_creacion
            ]
            if diffs:
                tiempo_promedio_horas = round(sum(diffs) / len(diffs), 2)

    # 6. Costos agregados de mano de obra y repuestos utilizados
    costo_mano_obra = (
        db.query(func.coalesce(func.sum(models.Diagnostico.costo_mano_obra), 0.0)).scalar()
        or 0.0
    )
    costo_repuestos = (
        db.query(
            func.coalesce(
                func.sum(models.DiagnosticoRepuesto.cantidad * models.Repuesto.costo_unitario),
                0.0,
            )
        )
        .join(models.Repuesto, models.Repuesto.id == models.DiagnosticoRepuesto.repuesto_id)
        .scalar()
        or 0.0
    )

    return schemas.ReporteResumenOut(
        total_tickets=int(total_tickets),
        tickets_por_estado=tickets_por_estado,
        tickets_por_prioridad=tickets_por_prioridad,
        equipo_mas_fallas=equipo_mas_fallas,
        equipos_top_fallas=equipos_top_fallas,
        tiempo_promedio_resolucion_horas=tiempo_promedio_horas,
        costo_total_mano_obra=float(costo_mano_obra),
        costo_total_repuestos=float(costo_repuestos),
        costo_total_mantenimiento=float(costo_mano_obra) + float(costo_repuestos),
    )
