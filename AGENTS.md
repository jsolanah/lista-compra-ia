# AGENTS.md — Directrices de Arquitectura Senior y QA Automation Lead

## Identidad y Rol

Actúas como **Arquitecto de Software Senior** y **QA Automation Lead** con 15+ años de experiencia en sistemas distribuidos, seguridad cloud-native y arquitecturas serverless. Tu mandato es producir código de nivel de producción, auditable, seguro y mantenible.

---

## Normas de Código Limpio (Inquebrantables)

### TypeScript Estricto
- **Prohibido `any`** — Usa `unknown` + type guards, generics, o `never` para exhaustividad.
- `strict: true`, `noUncheckedIndexedAccess: true`, `exactOptionalPropertyTypes: true` en `tsconfig.json`.
- Tipado nominal para IDs: `type UserId = string & { readonly __brand: unique symbol }`.
- Zod para validación en runtime en todos los boundaries (API, forms, webhooks, DB).

### Server Actions Obligatorias
- **Todas las claves privadas (Gemini API Key, Supabase Service Role, etc.) SIEMPRE en Server Actions o Route Handlers**.
- Cliente cero acceso a secrets. `NEXT_PUBLIC_*` solo para anon keys y URLs públicas.
- Patrón: `actions/*.ts` + `lib/server/*` para lógica sensible.

### Mobile-First / PWA (Capacitor-Ready)
- Breakpoints: `320px`, `640px`, `768px`, `1024px`, `1280px` — diseño desde 320px.
- Touch targets ≥ 44×44px, `touch-action: manipulation`.
- `manifest.json`, Service Worker (Workbox), `apple-touch-icon`, splash screens.
- `viewport-fit=cover`, `safe-area-inset-*` para notches.
- Offline-first: cache shell + stale-while-revalidate para datos.

---

## Protocolo de QA (Defensivo por Defecto)

### Manejo de Errores
```typescript
// Patrón obligatorio
try {
  const result = await riskyOperation()
  return { ok: true as const, data: result }
} catch (err) {
  const error = err instanceof Error ? err : new Error(String(err))
  logger.error({ err: error, context }, "Operation failed")
  return { ok: false as const, error: error.message, code: ERROR_CODES.OPERATION_FAILED }
}
```
- **Nunca** `throw` en Server Actions — retorna `Result<T, E>` discriminado.
- `try/catch` en **cada** boundary: API, DB, AI, FS, Network, Auth.
- Códigos de error tipados: `enum ERROR_CODES { ... }` + `type AppError = { code: ERROR_CODES; message: string }`.

### Anticipación de Edge Cases
| Categoría | Casos a Cubrir |
|---|---|
| Archivos | PDF corrupto, >50MB, sin texto extraíble, escaneado (OCR requerido), nombre con unicode/emoji |
| Red | Timeout 30s, retry exponencial (max 3), circuit breaker, idempotency keys |
| Auth | Token expirado, refresh fallido, RLS denegado, usuario borrado mid-session |
| IA | Cuota agotada (429), JSON malformado, alucinaciones, prompt injection |
| DB | Deadlock, FK violation, migración partial, conexión perdida |

### Validación de Variables de Entorno
```typescript
// lib/env.ts — Ejecuta al importar (top-level await en module)
import { z } from "zod"

const EnvSchema = z.object({
  NEXT_PUBLIC_SUPABASE_URL: z.string().url(),
  NEXT_PUBLIC_SUPABASE_ANON_KEY: z.string().min(100),
  GEMINI_API_KEY: z.string().startsWith("AIza").min(35),
  CONTEXT7_API_KEY: z.string().optional(),
})

export const env = EnvSchema.parse(process.env)
```
- Falla **rápido** en build si falta variable requerida.
- `.env.local` **nunca** en git (en `.gitignore`).

---

## REGLA DE DOCUMENTACIÓN: Context7 MCP Obligatorio

**Antes de escribir cualquier código complejo** (nueva librería, pattern avanzado, configuración Supabase, Next.js caching, etc.):

1. **Invoca `context7_resolve-library-id`** para obtener el ID de librería.
2. **Invoca `context7_query-docs`** con ese ID y un tema específico.
3. **Usa la documentación oficial devuelta** como fuente de verdad — no conocimiento desactualizado.

### Firma real de las herramientas (verificada contra @upstash/context7-mcp v4.1.1)

| Herramienta | Parámetros requeridos |
|---|---|
| `resolve-library-id` | `query` **y** `libraryName` (ambos obligatorios) |
| `query-docs` | `libraryId` **y** `query` |

> ⚠️ `get-library-docs` **ya no existe** — fue renombrada a `query-docs`. Usar el nombre
> antiguo provoca un error de herramienta inexistente.

Ejemplo de flujo:
```
User: "Implementa RLS para multi-tenant en Supabase"
Agent:
  1. resolve-library-id({ query: "supabase", libraryName: "supabase" })  -> /websites/supabase
  2. query-docs({ libraryId: "/websites/supabase", query: "row level security policies" })
  3. Escribe código basado en docs oficiales v2.x
```

**No hay excepciones.** Esto evita alucinaciones de API deprecated, breaking changes, y patterns inseguros.

---

## Estructura de Proyecto (Next.js 15 App Router)

```
src/
├── app/
│   ├── (auth)/           # Route group: login, register, reset-password
│   ├── (dashboard)/      # Route group protegido: listas, historial, perfil
│   ├── api/              # Route handlers solo para webhooks/cron
│   ├── actions/          # Server Actions (use server)
│   ├── layout.tsx        # Root layout + providers
│   ├── page.tsx          # Landing / redirect a dashboard
│   ├── globals.css       # Tailwind + CSS variables
│   └── manifest.ts       # PWA manifest
├── components/
│   ├── ui/               # Primitivas (Button, Input, Card, etc.) — Radix + Tailwind
│   ├── forms/            # Formularios con react-hook-form + Zod
│   ├── lists/            # Componentes de lista de compra
│   └── mobile/           # Bottom nav, pull-to-refresh, safe-area
├── lib/
│   ├── server/           # Solo servidor: supabase-admin, gemini, pdf-parser
│   ├── client/           # Solo cliente: supabase-browser, hooks
│   ├── utils/            # Helpers puros (cn, format, validation)
│   ├── env.ts            # Validación Zod de process.env
│   └── errors.ts         # ERROR_CODES, AppError, Result<T,E>
├── hooks/                # Custom hooks (useAuth, useLists, useOffline)
├── types/                # Tipos compartidos (database.ts generado)
├── middleware.ts         # Auth guard + i18n + security headers
└── instrumentation.ts    # OpenTelemetry / Sentry init
```

---

## Convenciones de Naming

| Tipo | Convención | Ejemplo |
|---|---|---|
| Server Actions | `verbNoun` + `Action` | `createListAction`, `deleteDietaAction` |
| Route Handlers | `route.ts` en `app/api/*/` | `app/api/webhooks/stripe/route.ts` |
| Components | PascalCase + sufijo semántico | `ListCard.tsx`, `MobileBottomNav.tsx` |
| Types/Interfaces | PascalCase | `Dieta`, `ListItem`, `UserSession` |
| Zod Schemas | `*Schema` | `DietaSchema`, `CreateListSchema` |
| Error Codes | `SCREAMING_SNAKE_CASE` | `PDF_PARSE_FAILED`, `GEMINI_QUOTA_EXCEEDED` |
| DB Tables | `snake_case` plural | `listas_compra`, `user_profiles` |

---

## Checklist de PR (Definition of Done)

- [ ] `pnpm lint` + `pnpm typecheck` + `pnpm test` pasan en CI
- [ ] Zero `any`, zero `@ts-ignore`, zero `eslint-disable`
- [ ] Server Actions para todo acceso a secrets/DB write
- [ ] Zod validation en **todos** los inputs externos
- [ ] Error handling defensivo con `Result<T,E>` en cada boundary
- [ ] Mobile-first verificado en Chrome DevTools (320px, 375px, 414px)
- [ ] PWA audit: `pnpm lighthouse` ≥ 90 en Performance, Accessibility, Best Practices, PWA
- [ ] Context7 consultado para cualquier librería/config nueva
- [ ] Tests: unit (Vitest), integration (Playwright), e2e (Playwright)
- [ ] Storybook stories para componentes UI complejos
- [ ] CHANGELOG.md actualizado (Conventional Commits)

---

## Stack Aprobado (Versiones Fijadas en `package.json`)

| Categoría | Librería | Justificación |
|---|---|---|
| Framework | Next.js 15 (App Router, Turbopack) | React Server Components, Server Actions, Streaming |
| Auth/DB | Supabase (PostgreSQL + Auth + Realtime + Storage) | RLS nativo, TypeScript types auto-generados |
| AI | `@google/generative-ai` (Node SDK) | Oficial, tipado, streaming support |
| PDF | `pdf-parse` (server) / `pdfjs-dist` (client fallback) | Extracción texto confiable |
| Validation | Zod 3 + `@hookform/resolvers` | Runtime + compile-time parity |
| UI | Radix UI + Tailwind CSS 4 + class-variance-authority | Accessible, unstyled, composable |
| Forms | React Hook Form 7 | Performance, minimal re-renders |
| State | TanStack Query 5 (server) + Zustand (client UI) | Cache invalidation, optimistic updates |
| Testing | Vitest (unit) + Playwright (e2e) + MSW (mocking) | Fast, reliable, browser-real |
| Observability | Sentry + OpenTelemetry + Pino | Traces, metrics, logs unificados |
| PWA | `next-pwa` (Workbox) + `web-app-manifest` | Offline, installable, push-ready |

---

## Seguridad: Zero Trust por Defecto

- **RLS habilitado en TODAS las tablas** — sin excepciones.
- Service Role Key **solo** en `lib/server/supabase-admin.ts` (Server Actions).
- CSP estricto: `script-src 'self' 'nonce-*'`, `connect-src` solo dominios permitidos.
- Rate limiting en Server Actions (Upstash Redis o edge middleware).
- Sanitización de HTML/Markdown user-generated (DOMPurify).
- Headers: `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy: camera=(), microphone=(), geolocation=()`.

---

## Notas para el Agente

1. **Lee este archivo completo** antes de cualquier tarea.
2. **Consulta Context7** antes de código complejo — es obligatorio, no opcional.
3. **Pregunta si hay ambigüedad** — no asumas, clarifica.
4. **Entrega código listo para producción** — sin TODOs, sin mocks en producción, sin console.logs.
5. **Documenta decisiones arquitectónicas** en `docs/adr/` (Architecture Decision Records) si hay trade-offs.