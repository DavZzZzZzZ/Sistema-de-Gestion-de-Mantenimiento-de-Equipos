import React from "react";
import { StatusBar } from "expo-status-bar";
import { NavigationContainer } from "@react-navigation/native";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { createNativeStackNavigator } from "@react-navigation/native-stack";

import EquiposScreen from "./src/screens/EquiposScreen";
import TicketsScreen from "./src/screens/TicketsScreen";
import TicketDetalleScreen from "./src/screens/TicketDetalleScreen";
import PorCompletarListaScreen from "./src/screens/PorCompletarListaScreen";
import ReportesScreen from "./src/screens/ReportesScreen";
import NotificacionesScreen from "./src/screens/NotificacionesScreen";
import HistorialScreen from "./src/screens/HistorialScreen";
import BusquedaScreen from "./src/screens/BusquedaScreen";
import { COLORS } from "./src/theme/colors";
import { TicketsStackParamList, PorCompletarStackParamList } from "./src/navigation/types";

const Tab = createBottomTabNavigator();
const TicketsStack = createNativeStackNavigator<TicketsStackParamList>();
const PorCompletarStack = createNativeStackNavigator<PorCompletarStackParamList>();

/**
 * Navegador de pila (Stack Navigator) para el módulo de Tickets.
 * Permite navegar entre el listado general de tickets (TicketsScreen)
 * y la vista detallada de un ticket específico (TicketDetalleScreen).
 */
function TicketsStackNavigator() {
  return (
    <TicketsStack.Navigator screenOptions={{ headerShown: false }}>
      <TicketsStack.Screen name="TicketsLista" component={TicketsScreen} />
      <TicketsStack.Screen name="TicketDetalle" component={TicketDetalleScreen} />
    </TicketsStack.Navigator>
  );
}

/**
 * Navegador de pila (Stack Navigator) para los Requerimientos 5 a 8.
 * Conecta el menú de selección (PorCompletarListaScreen) con las pantallas
 * de Reportes, Notificaciones, Historial de Estados y Búsqueda Avanzada.
 */
function PorCompletarStackNavigator() {
  return (
    <PorCompletarStack.Navigator screenOptions={{ headerShown: false }}>
      <PorCompletarStack.Screen name="PorCompletarLista" component={PorCompletarListaScreen} />
      <PorCompletarStack.Screen name="Reportes" component={ReportesScreen} />
      <PorCompletarStack.Screen name="Notificaciones" component={NotificacionesScreen} />
      <PorCompletarStack.Screen name="Historial" component={HistorialScreen} />
      <PorCompletarStack.Screen name="Busqueda" component={BusquedaScreen} />
    </PorCompletarStack.Navigator>
  );
}

/**
 * Componente raíz de la aplicación móvil Helpdesk Técnico.
 * Configura el contenedor de navegación y la barra inferior de pestañas (Bottom Tabs).
 */
export default function App() {
  return (
    <NavigationContainer>
      <StatusBar style="light" />
      <Tab.Navigator
        screenOptions={{
          headerShown: false,
          tabBarActiveTintColor: COLORS.primary,
          tabBarInactiveTintColor: COLORS.textGray,
          tabBarStyle: { paddingBottom: 6, paddingTop: 6, height: 58 },
          tabBarLabelStyle: { fontSize: 11, fontWeight: "600" },
        }}
      >
        <Tab.Screen name="Equipos" component={EquiposScreen} />
        <Tab.Screen name="Tickets" component={TicketsStackNavigator} />
        <Tab.Screen name="Por completar" component={PorCompletarStackNavigator} />
      </Tab.Navigator>
    </NavigationContainer>
  );
}
