# App móvil — Sistema de Gestión de Mantenimiento de Equipos (Helpdesk Técnico)

Universidad Piloto de Colombia · Programación para Dispositivos Convergentes

Aplicación construida con **React Native + Expo + TypeScript**.

## Ejecución

```bash
npm install
cp .env.example .env
npx expo start
```

- Presiona `a` para abrir en un emulador Android, `i` para iOS (requiere macOS), o escanea el QR con **Expo Go** en tu celular.
- Para desarrollo rápido en el navegador: `npx expo start --web`.

## Conexión con el backend

Por defecto la app apunta a `http://localhost:8000`. Ajusta `EXPO_PUBLIC_API_URL`
en `.env` según el caso:

| Entorno | URL recomendada |
|---|---|
| Web (`expo start --web`) | `http://localhost:8000` |
| Emulador Android | `http://10.0.2.2:8000` |
| Dispositivo físico con Expo Go | `http://<IP-de-tu-computador-en-la-red>:8000` |

## Estructura

```
App.tsx                          # navegación (bottom tabs + stacks)
src/
  theme/colors.ts                # paleta institucional (rojo Unipiloto)
  services/api.ts                # cliente axios + tipos + funciones por entidad
  components/
    EncabezadoInstitucional.tsx
    EtiquetaEstado.tsx
    PantallaPorCompletar.tsx     # plantilla para los requerimientos propuestos
  screens/
    EquiposScreen.tsx            # Requerimiento 1
    TicketsScreen.tsx            # Requerimiento 2
    TicketDetalleScreen.tsx      # Requerimientos 3 y 4 (asignación, estados, diagnóstico + repuestos)
    PorCompletarListaScreen.tsx
    ReportesScreen.tsx           # Requerimiento 5 (propuesto)
    NotificacionesScreen.tsx     # Requerimiento 6 (propuesto)
    HistorialScreen.tsx          # Requerimiento 7 (propuesto)
    BusquedaScreen.tsx           # Requerimiento 8 (propuesto)
  navigation/types.ts
```
