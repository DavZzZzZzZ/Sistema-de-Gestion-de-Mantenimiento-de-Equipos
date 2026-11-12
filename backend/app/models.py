"""
Modelos SQLAlchemy del Sistema de Gestión de Mantenimiento de Equipos
(Helpdesk Técnico) — Universidad Piloto de Colombia
Asignatura: Programación para Dispositivos Convergentes
Docente: Edicson Pineda Cadena

Seis entidades del modelo de datos:
    1. Usuario                 (solicitantes, técnicos y administradores)
    2. Equipo                  (activos que pueden requerir mantenimiento)
    3. Ticket                  (solicitud de mantenimiento sobre un equipo)
    4. Diagnostico              (informe técnico asociado a un ticket)
    5. Repuesto                 (inventario de repuestos disponibles)
    6. DiagnosticoRepuesto      (detalle: repuestos usados en un diagnóstico)
"""
import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime, ForeignKey, Enum, Boolean
)
from sqlalchemy.orm import relationship

from .database import Base


class RolUsuario(str, enum.Enum):
    """Roles permitidos para los usuarios del sistema Helpdesk."""
    admin = "admin"
    tecnico = "tecnico"
    solicitante = "solicitante"


class EstadoTicket(str, enum.Enum):
    """Estados posibles en el ciclo de vida de un ticket de mantenimiento."""
    abierto = "abierto"
    en_proceso = "en_proceso"
    cerrado = "cerrado"


class PrioridadTicket(str, enum.Enum):
    """Niveles de prioridad asignables a una solicitud de mantenimiento."""
    baja = "baja"
    media = "media"
    alta = "alta"
    critica = "critica"


class EstadoEquipo(str, enum.Enum):
    """Estados operativos de un activo o equipo en el inventario."""
    operativo = "operativo"
    en_mantenimiento = "en_mantenimiento"
    de_baja = "de_baja"


# ---------------------------------------------------------------------------
# 1. Usuario
# ---------------------------------------------------------------------------
class Usuario(Base):
    """Entidad que representa a los solicitantes, técnicos y administradores."""
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(120), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    rol = Column(Enum(RolUsuario), nullable=False, default=RolUsuario.solicitante)
    activo = Column(Boolean, default=True)
    fecha_registro = Column(DateTime, default=datetime.utcnow)

    tickets_solicitados = relationship(
        "Ticket", foreign_keys="Ticket.solicitante_id", back_populates="solicitante"
    )
    tickets_asignados = relationship(
        "Ticket", foreign_keys="Ticket.tecnico_id", back_populates="tecnico"
    )
    diagnosticos = relationship("Diagnostico", back_populates="tecnico")
    notificaciones = relationship(
        "Notificacion", back_populates="usuario", cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------------
# 2. Equipo
# ---------------------------------------------------------------------------
class Equipo(Base):
    """Entidad que representa un equipo tecnológico sujeto a mantenimiento (Requerimiento 1)."""
    __tablename__ = "equipos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(120), nullable=False)
    tipo = Column(String(80), nullable=False)  # ej. "Computador", "Impresora", "Router"
    marca = Column(String(80))
    modelo = Column(String(80))
    numero_serie = Column(String(100), unique=True)
    ubicacion = Column(String(120))
    estado = Column(Enum(EstadoEquipo), default=EstadoEquipo.operativo)
    fecha_registro = Column(DateTime, default=datetime.utcnow)

    tickets = relationship("Ticket", back_populates="equipo")


# ---------------------------------------------------------------------------
# 3. Ticket
# ---------------------------------------------------------------------------
class Ticket(Base):
    """Entidad de solicitud de mantenimiento asociada a un equipo, solicitante y técnico (Requerimientos 2 y 3)."""
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(150), nullable=False)
    descripcion = Column(Text, nullable=False)
    estado = Column(Enum(EstadoTicket), default=EstadoTicket.abierto, nullable=False)
    prioridad = Column(Enum(PrioridadTicket), default=PrioridadTicket.media)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_cierre = Column(DateTime, nullable=True)

    equipo_id = Column(Integer, ForeignKey("equipos.id"), nullable=False)
    solicitante_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    tecnico_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)

    equipo = relationship("Equipo", back_populates="tickets")
    solicitante = relationship(
        "Usuario", foreign_keys=[solicitante_id], back_populates="tickets_solicitados"
    )
    tecnico = relationship(
        "Usuario", foreign_keys=[tecnico_id], back_populates="tickets_asignados"
    )
    diagnosticos = relationship("Diagnostico", back_populates="ticket")
    notificaciones = relationship(
        "Notificacion", back_populates="ticket", cascade="all, delete-orphan"
    )
    historial = relationship(
        "TicketHistorial",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="TicketHistorial.fecha.asc()",
    )


# ---------------------------------------------------------------------------
# 4. Diagnostico
# ---------------------------------------------------------------------------
class Diagnostico(Base):
    """Entidad de informe técnico emitido sobre un ticket con mano de obra y repuestos (Requerimiento 4)."""
    __tablename__ = "diagnosticos"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    tecnico_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    descripcion = Column(Text, nullable=False)
    costo_mano_obra = Column(Float, default=0.0)
    fecha = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="diagnosticos")
    tecnico = relationship("Usuario", back_populates="diagnosticos")
    repuestos_usados = relationship(
        "DiagnosticoRepuesto", back_populates="diagnostico", cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------------
# 5. Repuesto
# ---------------------------------------------------------------------------
class Repuesto(Base):
    """Entidad del catálogo de repuestos disponibles en inventario (Requerimiento 4)."""
    __tablename__ = "repuestos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(120), nullable=False)
    descripcion = Column(String(255))
    stock = Column(Integer, default=0)
    costo_unitario = Column(Float, default=0.0)

    usos = relationship("DiagnosticoRepuesto", back_populates="repuesto")


# ---------------------------------------------------------------------------
# 6. DiagnosticoRepuesto (tabla de detalle / relación muchos a muchos)
# ---------------------------------------------------------------------------
class DiagnosticoRepuesto(Base):
    """Entidad asociativa que vincula un diagnóstico con cada repuesto utilizado y su cantidad (Requerimiento 4)."""
    __tablename__ = "diagnostico_repuestos"

    id = Column(Integer, primary_key=True, index=True)
    diagnostico_id = Column(Integer, ForeignKey("diagnosticos.id"), nullable=False)
    repuesto_id = Column(Integer, ForeignKey("repuestos.id"), nullable=False)
    cantidad = Column(Integer, nullable=False, default=1)

    diagnostico = relationship("Diagnostico", back_populates="repuestos_usados")
    repuesto = relationship("Repuesto", back_populates="usos")


# ---------------------------------------------------------------------------
# 7. Notificacion (Requerimiento 6 — avisos al solicitante)
# ---------------------------------------------------------------------------
class Notificacion(Base):
    """Entidad que almacena las notificaciones enviadas al solicitante cuando cambia el estado de su ticket (Requerimiento 6)."""
    __tablename__ = "notificaciones"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    titulo = Column(String(150), nullable=False)
    mensaje = Column(Text, nullable=False)
    leida = Column(Boolean, default=False, nullable=False)
    fecha = Column(DateTime, default=datetime.utcnow)

    usuario = relationship("Usuario", back_populates="notificaciones")
    ticket = relationship("Ticket", back_populates="notificaciones")


# ---------------------------------------------------------------------------
# 8. TicketHistorial (Requerimiento 7 — auditoría y línea de tiempo)
# ---------------------------------------------------------------------------
class TicketHistorial(Base):
    """Entidad de auditoría que registra cada transición de estado de un ticket para construir su línea de tiempo (Requerimiento 7)."""
    __tablename__ = "ticket_historial"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    estado_anterior = Column(Enum(EstadoTicket), nullable=True)
    estado_nuevo = Column(Enum(EstadoTicket), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    comentario = Column(String(255), nullable=True)
    fecha = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="historial")
    usuario = relationship("Usuario")

