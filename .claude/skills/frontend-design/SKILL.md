# Skill: frontend-design

## Propósito
Guía para diseñar e implementar componentes Next.js con Tailwind CSS siguiendo las convenciones visuales de TuReel (tema oscuro, centrado en contenido de vídeo).

## Cuándo usar esta skill
- Crear o refactorizar componentes de UI en `frontend/`
- Establecer un sistema de diseño coherente (colores, tipografía, espaciado)
- Revisar accesibilidad (a11y) de elementos interactivos

## Paleta de colores (Tailwind)
| Uso | Clase |
|---|---|
| Fondo de página | `bg-gray-950` |
| Fondo de tarjetas | `bg-gray-900` |
| Borde de tarjetas | `border-gray-800` |
| Texto principal | `text-gray-100` |
| Texto secundario | `text-gray-400` |
| Primario (botones, acentos) | `bg-violet-600` / `hover:bg-violet-700` |
| Error | `text-red-400` |
| Éxito / completado | `text-green-400` |
| Loading / progreso | `text-violet-400` |

## Tipografía
- Fuente: sistema por defecto (Inter vía Tailwind)
- Título de página: `text-3xl font-bold text-gray-100`
- Subtítulo de sección: `text-lg font-semibold text-gray-300`
- Cuerpo: `text-sm text-gray-400`
- Labels de escenas: `text-xs font-medium text-gray-500 uppercase tracking-wide`

## Espaciado y layout
- Contenedor máximo: `max-w-2xl mx-auto px-6`
- Gap entre secciones: `space-y-8`
- Padding de tarjetas: `p-6`
- Radio de bordes: `rounded-xl` para tarjetas, `rounded-lg` para inputs y botones

## Componentes base reutilizables

```tsx
// Botón primario
<button className="bg-violet-600 hover:bg-violet-700 text-white font-medium px-6 py-3 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
  Generar vídeo
</button>

// Tarjeta
<div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
  {children}
</div>

// Textarea de idea
<textarea className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-violet-500 resize-none" />

// Badge de escena
<span className="bg-violet-900/50 text-violet-300 text-xs font-medium px-2 py-1 rounded">
  Escena 1
</span>
```

## Estado de carga

```tsx
// Spinner inline
<div className="h-5 w-5 rounded-full border-2 border-violet-500 border-t-transparent animate-spin" />

// Texto de estado
<p className="text-violet-400 text-sm animate-pulse">Generando guión con IA...</p>
```

## Checklist antes de entregar un componente
- [ ] Funciona con el tema oscuro (sin fondos blancos hardcodeados)
- [ ] Estado `disabled` visible cuando `isLoading=true`
- [ ] Estados focus visibles (accesibilidad)
- [ ] Sin colores hardcodeados fuera de las clases Tailwind
