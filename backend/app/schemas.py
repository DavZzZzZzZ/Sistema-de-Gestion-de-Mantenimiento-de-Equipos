"""
Esquemas Pydantic (entrada/salida de la API) para las 6 entidades.
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, ConfigDict

from .models import RolUsuario, EstadoTicket, PrioridadTicket, EstadoEquipo


# ---------------------------------------------------------------------------
# Usuario
# ---------------------------------------------------------------------------
class UsuarioBase(BaseModel):
    """Atributos comunes de un usuario del sistema."""
    nombre: str
    email: EmailStr
    rol: RolUsuario = RolUsuario.solicitante
    activo: bool = True


class UsuarioCreate(UsuarioBase):
    """Esquema de entrada para registrar un nuevo usuario."""
    pass


class UsuarioOut(UsuarioBase):
    """Esquema de salida con el identificador y fecha de registro del usuario."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    fecha_registro: datetime


# ---------------------------------------------------------------------------
# Equipo
# ---------------------------------------------------------------------------
class EquipoBase(BaseModel):
    """Atributos comunes de un equipo tecnológico."""
    nombre: str
    tipo: str
    marca: Optional[str] = None
    modelo: Optional[str] = None
    numero_serie: Optional[str] = None
    ubicacion: Optional[str] = None
    estado: EstadoEquipo = EstadoEquipo.operativo


class EquipoCreate(EquipoBase):
    """Esquema de entrada para registrar un nuevo equipo (Requerimiento 1)."""
    pass


class EquipoUpdate(BaseModel):
    """Esquema de entrada con campos opcionales para actualizar un equipo existente."""
    nombre: Optional[str] = None
    tipo: Optional[str] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    numero_serie: Optional[str] = None
    ubicacion: Optional[str] = None
    estado: Optional[EstadoEquipo] = None


class EquipoOut(EquipoBase):
    """Esquema de salida de un equipo registrado."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    fecha_registro: datetime


# ---------------------------------------------------------------------------
# Ticket
# ---------------------------------------------------------------------------
class TicketBase(BaseModel):
    """Atributos base para la solicitud de mantenimiento de un equipo."""
    titulo: str
    descripcion: str
    prioridad: PrioridadTicket = PrioridadTicket.media
    equipo_id: int
    solicitante_id: int


class TicketCreate(TicketBase):
    """Esquema de entrada para la creación de un ticket (Requerimiento 2)."""
    pass


class TicketAsignar(BaseModel):
    """Esquema de entrada para asignar un técnico a un ticket (Requerimiento 3)."""
    tecnico_id: int


class TicketCambiarEstado(BaseModel):
    """Esquema de entrada para cambiar el estado de un ticket (Requerimiento 3)."""
    estado: EstadoTicket


class TicketOut(BaseModel):
    """Esquema de salida básico de un ticket."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    titulo: str
    descripcion: str
    estado: EstadoTicket
    prioridad: PrioridadTicket
    fecha_creacion: datetime
    fecha_cierre: Optional[datetime] = None
    equipo_id: int
    solicitante_id: int
    tecnico_id: Optional[int] = None


class TicketDetalleOut(TicketOut):
    """Incluye los objetos relacionados completos (equipo, solicitante, técnico)."""
    equipo: EquipoOut
    solicitante: UsuarioOut
    tecnico: Optional[UsuarioOut] = None


# ---------------------------------------------------------------------------
# Repuesto
# ---------------------------------------------------------------------------
class RepuestoBase(BaseModel):
    """Atributos base de un repuesto en inventario."""
    nombre: str
    descripcion: Optional[str] = None
    stock: int = 0
    costo_unitario: float = 0.0


class RepuestoCreate(RepuestoBase):
    """Esquema de entrada para crear un repuesto en inventario."""
    pass


class RepuestoOut(RepuestoBase):
    """Esquema de salida de un repuesto."""
    model_config = ConfigDict(from_attributes=True)
    id: int


# ---------------------------------------------------------------------------
# Diagnostico + detalle de repuestos usados
# ---------------------------------------------------------------------------
class DiagnosticoRepuestoIn(BaseModel):
    """Ítem de entrada que indica un repuesto y la cantidad usada en un diagnóstico."""
    repuesto_id: int
    cantidad: int = 1


class DiagnosticoRepuestoOut(BaseModel):
    """Esquema de salida del detalle de repuesto utilizado en un diagnóstico."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    repuesto_id: int
    cantidad: int
    repuesto: RepuestoOut


class DiagnosticoCreate(BaseModel):
    """Esquema de entrada para registrar un diagnóstico con sus repuestos (Requerimiento 4)."""
    ticket_id: int
    tecnico_id: int
    descripcion: str
    costo_mano_obra: float = 0.0
    repuestos: List[DiagnosticoRepuestoIn] = []


class DiagnosticoOut(BaseModel):
    """Esquema de salida de un diagnóstico técnico completo."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    ticket_id: int
    tecnico_id: int
    descripcion: str
    costo_mano_obra: float
    fecha: datetime
    repuestos_usados: List[DiagnosticoRepuestoOut] = []


# ---------------------------------------------------------------------------
# Requerimiento 6: Notificaciones
# ---------------------------------------------------------------------------
class NotificacionOut(BaseModel):
    """Esquema de salida de una notificación enviada al solicitante (Requerimiento 6)."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    usuario_id: int
    ticket_id: int
    titulo: str
    mensaje: str
    leida: bool
    fecha: datetime
    usuario: Optional[UsuarioOut] = None


# ---------------------------------------------------------------------------
# Requerimiento 7: Historial de estados (auditoría)
# ---------------------------------------------------------------------------
class TicketHistorialOut(BaseModel):
    """Esquema de salida de un evento en la línea de tiempo de un ticket (Requerimiento 7)."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    ticket_id: int
    estado_anterior: Optional[EstadoTicket] = None
    estado_nuevo: EstadoTicket
    usuario_id: Optional[int] = None
    comentario: Optional[str] = None
    fecha: datetime
    usuario: Optional[UsuarioOut] = None


# ---------------------------------------------------------------------------
# Requerimiento 5: Reportes y estadísticas
# ---------------------------------------------------------------------------
class TicketsPorEstadoItem(BaseModel):
    """Conteo de tickets agrupados por un estado específico."""
    estado: EstadoTicket
    cantidad: int


class TicketsPorPrioridadItem(BaseModel):
    """Conteo de tickets agrupados por un nivel de prioridad específico."""
    prioridad: PrioridadTicket
    cantidad: int


class EquipoMasFallasOut(BaseModel):
    """Resumen de un equipo con el total de tickets/fallas reportadas."""
    equipo_id: int
    nombre: str
    tipo: str
    ubicacion: Optional[str] = None
    total_tickets: int


class ReporteResumenOut(BaseModel):
    """Esquema de salida del panel de reportes y estadísticas agregadas (Requerimiento 5)."""
    total_tickets: int
    tickets_por_estado: List[TicketsPorEstadoItem]
    tickets_por_prioridad: List[TicketsPorPrioridadItem]
    equipo_mas_fallas: Optional[EquipoMasFallasOut] = None
    equipos_top_fallas: List[EquipoMasFallasOut] = []
    tiempo_promedio_resolucion_horas: Optional[float] = None
    costo_total_mano_obra: float = 0.0
    costo_total_repuestos: float = 0.0
    costo_total_mantenimiento: float = 0.0

