"""
Script opcional de datos de ejemplo (seed) para pruebas en clase.

Ejecutar dentro del contenedor del backend, una vez que la API ya
haya creado las tablas:

    docker compose exec backend python seed.py
"""
from datetime import datetime, timedelta
from app.database import SessionLocal, engine
from app import models

models.Base.metadata.create_all(bind=engine)
db = SessionLocal()

if db.query(models.Usuario).count() == 0:
    usuarios = [
        models.Usuario(nombre="Edicson Pineda", email="admin@unipiloto.edu.co", rol=models.RolUsuario.admin),
        models.Usuario(nombre="Laura Gómez", email="laura.gomez@unipiloto.edu.co", rol=models.RolUsuario.tecnico),
        models.Usuario(nombre="Camilo Rojas", email="camilo.rojas@unipiloto.edu.co", rol=models.RolUsuario.tecnico),
        models.Usuario(nombre="Diana Sánchez", email="diana.sanchez@unipiloto.edu.co", rol=models.RolUsuario.solicitante),
    ]
    db.add_all(usuarios)
    db.commit()

if db.query(models.Equipo).count() == 0:
    equipos = [
        models.Equipo(nombre="Computador Sala 301", tipo="Computador", marca="HP", modelo="ProDesk 400",
                      numero_serie="HP-301-001", ubicacion="Sala de sistemas 301"),
        models.Equipo(nombre="Impresora Secretaría", tipo="Impresora", marca="Epson", modelo="L3250",
                      numero_serie="EP-SEC-002", ubicacion="Secretaría académica"),
        models.Equipo(nombre="Router Bloque B", tipo="Red", marca="TP-Link", modelo="AX3000",
                      numero_serie="TPL-B-003", ubicacion="Bloque B, piso 2"),
    ]
    db.add_all(equipos)
    db.commit()

if db.query(models.Repuesto).count() == 0:
    repuestos = [
        models.Repuesto(nombre="Fuente de poder 500W", descripcion="Fuente ATX genérica", stock=10, costo_unitario=120000),
        models.Repuesto(nombre="Cartucho de tinta negro", descripcion="Compatible Epson L3250", stock=15, costo_unitario=45000),
        models.Repuesto(nombre="Memoria RAM 8GB DDR4", descripcion="Kingston 2666MHz", stock=8, costo_unitario=150000),
    ]
    db.add_all(repuestos)
    db.commit()

if db.query(models.Ticket).count() == 0:
    laura = db.query(models.Usuario).filter(models.Usuario.email == "laura.gomez@unipiloto.edu.co").first()
    camilo = db.query(models.Usuario).filter(models.Usuario.email == "camilo.rojas@unipiloto.edu.co").first()
    diana = db.query(models.Usuario).filter(models.Usuario.email == "diana.sanchez@unipiloto.edu.co").first()

    pc = db.query(models.Equipo).filter(models.Equipo.numero_serie == "HP-301-001").first()
    impresora = db.query(models.Equipo).filter(models.Equipo.numero_serie == "EP-SEC-002").first()
    router_eq = db.query(models.Equipo).filter(models.Equipo.numero_serie == "TPL-B-003").first()

    fuente = db.query(models.Repuesto).filter(models.Repuesto.nombre == "Fuente de poder 500W").first()
    cartucho = db.query(models.Repuesto).filter(models.Repuesto.nombre == "Cartucho de tinta negro").first()

    ahora = datetime.utcnow()
    t1_creacion = ahora - timedelta(hours=6)
    t1_asignacion = ahora - timedelta(hours=5)
    t1_cierre = ahora - timedelta(hours=2)

    t1 = models.Ticket(
        titulo="El computador no enciende",
        descripcion="Al presionar el botón de encendido no da video ni gira el ventilador.",
        estado=models.EstadoTicket.cerrado,
        prioridad=models.PrioridadTicket.alta,
        fecha_creacion=t1_creacion,
        fecha_cierre=t1_cierre,
        equipo_id=pc.id,
        solicitante_id=diana.id,
        tecnico_id=laura.id,
    )
    t2_creacion = ahora - timedelta(hours=4)
    t2_asignacion = ahora - timedelta(hours=3)
    t2 = models.Ticket(
        titulo="El mouse no responde",
        descripcion="El mouse inalámbrico no responde al moverlo en la estación 4.",
        estado=models.EstadoTicket.en_proceso,
        prioridad=models.PrioridadTicket.media,
        fecha_creacion=t2_creacion,
        equipo_id=pc.id,
        solicitante_id=diana.id,
        tecnico_id=laura.id,
    )
    t3_creacion = ahora - timedelta(hours=1)
    t3 = models.Ticket(
        titulo="Impresora mancha las hojas",
        descripcion="Las impresiones salen con líneas horizontales y falta tinta negra.",
        estado=models.EstadoTicket.abierto,
        prioridad=models.PrioridadTicket.baja,
        fecha_creacion=t3_creacion,
        equipo_id=impresora.id,
        solicitante_id=diana.id,
        tecnico_id=None,
    )
    t4_creacion = ahora - timedelta(hours=8)
    t4_cierre = ahora - timedelta(hours=5, minutes=30)
    t4 = models.Ticket(
        titulo="Caída intermitente de red WiFi",
        descripcion="Los equipos del segundo piso pierden conexión cada 20 minutos.",
        estado=models.EstadoTicket.cerrado,
        prioridad=models.PrioridadTicket.critica,
        fecha_creacion=t4_creacion,
        fecha_cierre=t4_cierre,
        equipo_id=router_eq.id,
        solicitante_id=diana.id,
        tecnico_id=camilo.id,
    )
    db.add_all([t1, t2, t3, t4])
    db.flush()

    # Diagnósticos de ejemplo
    dx1 = models.Diagnostico(
        ticket_id=t1.id,
        tecnico_id=laura.id,
        descripcion="Fuente de poder dañada por sobretensión. Se reemplaza por fuente ATX 500W nueva.",
        costo_mano_obra=35000,
        fecha=t1_cierre - timedelta(minutes=20),
    )
    db.add(dx1)
    db.flush()
    if fuente and fuente.stock >= 1:
        fuente.stock -= 1
        db.add(models.DiagnosticoRepuesto(diagnostico_id=dx1.id, repuesto_id=fuente.id, cantidad=1))

    dx2 = models.Diagnostico(
        ticket_id=t4.id,
        tecnico_id=camilo.id,
        descripcion="Se actualiza firmware del router AX3000 y se reconfigura el canal WiFi.",
        costo_mano_obra=25000,
        fecha=t4_cierre - timedelta(minutes=15),
    )
    db.add(dx2)

    # Historial de estados (Requerimiento 7)
    db.add_all([
        models.TicketHistorial(
            ticket_id=t1.id,
            estado_anterior=None,
            estado_nuevo=models.EstadoTicket.abierto,
            usuario_id=diana.id,
            comentario=f"Ticket creado por {diana.nombre}",
            fecha=t1_creacion,
        ),
        models.TicketHistorial(
            ticket_id=t1.id,
            estado_anterior=models.EstadoTicket.abierto,
            estado_nuevo=models.EstadoTicket.en_proceso,
            usuario_id=laura.id,
            comentario=f"Técnico asignado: {laura.nombre}",
            fecha=t1_asignacion,
        ),
        models.TicketHistorial(
            ticket_id=t1.id,
            estado_anterior=models.EstadoTicket.en_proceso,
            estado_nuevo=models.EstadoTicket.cerrado,
            usuario_id=laura.id,
            comentario="Ticket cerrado tras atención técnica",
            fecha=t1_cierre,
        ),
        models.TicketHistorial(
            ticket_id=t2.id,
            estado_anterior=None,
            estado_nuevo=models.EstadoTicket.abierto,
            usuario_id=diana.id,
            comentario=f"Ticket creado por {diana.nombre}",
            fecha=t2_creacion,
        ),
        models.TicketHistorial(
            ticket_id=t2.id,
            estado_anterior=models.EstadoTicket.abierto,
            estado_nuevo=models.EstadoTicket.en_proceso,
            usuario_id=laura.id,
            comentario=f"Técnico asignado: {laura.nombre}",
            fecha=t2_asignacion,
        ),
        models.TicketHistorial(
            ticket_id=t3.id,
            estado_anterior=None,
            estado_nuevo=models.EstadoTicket.abierto,
            usuario_id=diana.id,
            comentario=f"Ticket creado por {diana.nombre}",
            fecha=t3_creacion,
        ),
        models.TicketHistorial(
            ticket_id=t4.id,
            estado_anterior=None,
            estado_nuevo=models.EstadoTicket.abierto,
            usuario_id=diana.id,
            comentario=f"Ticket creado por {diana.nombre}",
            fecha=t4_creacion,
        ),
        models.TicketHistorial(
            ticket_id=t4.id,
            estado_anterior=models.EstadoTicket.abierto,
            estado_nuevo=models.EstadoTicket.en_proceso,
            usuario_id=camilo.id,
            comentario=f"Técnico asignado: {camilo.nombre}",
            fecha=t4_creacion + timedelta(minutes=30),
        ),
        models.TicketHistorial(
            ticket_id=t4.id,
            estado_anterior=models.EstadoTicket.en_proceso,
            estado_nuevo=models.EstadoTicket.cerrado,
            usuario_id=camilo.id,
            comentario="Ticket cerrado tras atención técnica",
            fecha=t4_cierre,
        ),
    ])

    # Notificaciones (Requerimiento 6)
    db.add_all([
        models.Notificacion(
            usuario_id=diana.id,
            ticket_id=t1.id,
            titulo=f"Técnico asignado · Ticket #{t1.id}",
            mensaje=f"Se asignó al técnico {laura.nombre} para atender tu solicitud '{t1.titulo}'. El estado ahora es 'en_proceso'.",
            leida=True,
            fecha=t1_asignacion,
        ),
        models.Notificacion(
            usuario_id=diana.id,
            ticket_id=t1.id,
            titulo=f"Estado actualizado · Ticket #{t1.id}",
            mensaje=f"Tu solicitud '{t1.titulo}' ha sido cerrado (estado anterior: 'en_proceso').",
            leida=False,
            fecha=t1_cierre,
        ),
        models.Notificacion(
            usuario_id=diana.id,
            ticket_id=t2.id,
            titulo=f"Técnico asignado · Ticket #{t2.id}",
            mensaje=f"Se asignó al técnico {laura.nombre} para atender tu solicitud '{t2.titulo}'. El estado ahora es 'en_proceso'.",
            leida=False,
            fecha=t2_asignacion,
        ),
        models.Notificacion(
            usuario_id=diana.id,
            ticket_id=t4.id,
            titulo=f"Estado actualizado · Ticket #{t4.id}",
            mensaje=f"Tu solicitud '{t4.titulo}' ha sido cerrado (estado anterior: 'en_proceso').",
            leida=False,
            fecha=t4_cierre,
        ),
    ])
    db.commit()
elif db.query(models.TicketHistorial).count() == 0:
    # Si ya existían tickets de sesiones previas, inicializar su historial
    for t in db.query(models.Ticket).all():
        db.add(
            models.TicketHistorial(
                ticket_id=t.id,
                estado_anterior=None,
                estado_nuevo=models.EstadoTicket.abierto,
                usuario_id=t.solicitante_id,
                comentario="Ticket registrado en el sistema",
                fecha=t.fecha_creacion or datetime.utcnow(),
            )
        )
        if t.estado in (models.EstadoTicket.en_proceso, models.EstadoTicket.cerrado) and t.tecnico_id:
            db.add(
                models.TicketHistorial(
                    ticket_id=t.id,
                    estado_anterior=models.EstadoTicket.abierto,
                    estado_nuevo=models.EstadoTicket.en_proceso,
                    usuario_id=t.tecnico_id,
                    comentario="Asignación de técnico",
                    fecha=t.fecha_creacion + timedelta(minutes=15) if t.fecha_creacion else datetime.utcnow(),
                )
            )
            db.add(
                models.Notificacion(
                    usuario_id=t.solicitante_id,
                    ticket_id=t.id,
                    titulo=f"Técnico asignado · Ticket #{t.id}",
                    mensaje=f"Tu solicitud '{t.titulo}' pasó a estado 'en_proceso'.",
                    leida=False,
                    fecha=t.fecha_creacion + timedelta(minutes=15) if t.fecha_creacion else datetime.utcnow(),
                )
            )
        if t.estado == models.EstadoTicket.cerrado:
            db.add(
                models.TicketHistorial(
                    ticket_id=t.id,
                    estado_anterior=models.EstadoTicket.en_proceso,
                    estado_nuevo=models.EstadoTicket.cerrado,
                    usuario_id=t.tecnico_id or t.solicitante_id,
                    comentario="Ticket cerrado tras atención técnica",
                    fecha=t.fecha_cierre or datetime.utcnow(),
                )
            )
            db.add(
                models.Notificacion(
                    usuario_id=t.solicitante_id,
                    ticket_id=t.id,
                    titulo=f"Estado actualizado · Ticket #{t.id}",
                    mensaje=f"Tu solicitud '{t.titulo}' ha sido cerrada.",
                    leida=False,
                    fecha=t.fecha_cierre or datetime.utcnow(),
                )
            )
    db.commit()

db.close()
print("Datos de ejemplo insertados correctamente.")

