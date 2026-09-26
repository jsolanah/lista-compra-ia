# Skill: Next.js 15 App Router Architect

## Propósito
Estándares obligatorios para desarrollar en Next.js 15 (App Router, Turbopack, React Server Components, Server Actions, Streaming).

---

## Reglas de Arquitectura

### 1. Server Components por Defecto
- **Todo componente es Server Component** salvo que necesite interactividad (`use client`).
- `use client` solo en hojas del árbol: botones, inputs, modales, charts.
- Props serializables entre Server → Client (nada de funciones, clases, Date, Symbol).

### 2. Server Actions = Único Acceso a Secrets/DB Write
```typescript
// app/actions/lists.ts
"use server"

import { createServerSupabaseClient } from "@/lib/server/supabase"
import { z } from "zod"

const CreateListSchema = z.object({
  nombrePdf: z.string().min(1).max(255),
  datos: z.object({ categorias: z.array(z.any()), planSemanal: z.array(z.any()) }),
  nombreArchivo: z.string().optional(),
})

export async function createListAction(formData: FormData) {
  const parsed = CreateListSchema.safeParse(Object.fromEntries(formData))
  if (!parsed.success) return { ok: false, error: parsed.error.flatten() }

  const supabase = createServerSupabaseClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return { ok: false, error: "Unauthorized", code: "UNAUTHORIZED" }

  const { error } = await supabase.from("listas_compra").insert({
    usuario_id: user.id,
    nombre_pdf: parsed.data.nombrePdf,
    nombre_archivo: parsed.data.nombreArchivo,
    datos_json: parsed.data.datos,
  })
  if (error) return { ok: false, error: error.message, code: "DB_INSERT_FAILED" }

  revalidatePath("/dashboard")
  return { ok: true }
}
```

### 3. Route Handlers Solo Para Webhooks/Cron
- `app/api/webhooks/stripe/route.ts` ✓
- `app/api/lists/route.ts` ✗ (usa Server Action)

### 4. Data Fetching: `fetch` + `next: { tags, revalidate }`
```typescript
// lib/server/queries.ts
export async function getUserLists(userId: string) {
  const res = await fetch(`${process.env.NEXT_PUBLIC_SUPABASE_URL}/rest/v1/listas_compra?usuario_id=eq.${userId}`, {
    headers: { apikey: process.env.SUPABASE_SERVICE_ROLE_KEY!, Authorization: `Bearer ${process.env.SUPABASE_SERVICE_ROLE_KEY!}` },
    next: { tags: [`lists:${userId}`], revalidate: 60 },
  })
  if (!res.ok) throw new Error("Failed to fetch lists")
  return res.json()
}
```

### 5. Caching & Revalidation
- `fetch(..., { next: { tags: ['key'], revalidate: 3600 } })` para ISR.
- `revalidateTag('key')` en Server Actions tras mutación.
- `noStore()` solo cuando sea estrictamente necesario (datos ultra-sensibles).

### 6. Streaming & Suspense
```tsx
// app/dashboard/page.tsx
import { Suspense } from "react"
import { ListsSkeleton } from "@/components/ui/skeleton"
import { ListsContent } from "./_components/lists-content"

export default function DashboardPage() {
  return (
    <Suspense fallback={<ListsSkeleton />}>
      <ListsContent />
    </Suspense>
  )
}
```

---

## TypeScript Estricto (Obligatorio)

```json
// tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitOverride": true,
    "noPropertyAccessFromIndexSignature": true
  }
}
```

- **Nunca `any`**. Usa `unknown` + type guards.
- Tipado nominal para IDs:
  ```typescript
  type UserId = string & { readonly __brand: unique symbol }
  type ListId = string & { readonly __brand: unique symbol }
  const toUserId = (s: string) => s as UserId
  ```

---

## Zod en Todos los Boundaries

```typescript
// lib/schemas.ts
export const CreateListSchema = z.object({
  nombrePdf: z.string().min(1).max(255),
  nombreArchivo: z.string().max(255).optional(),
  datosJson: z.object({
    categorias: z.array(z.object({
      nombre: z.string(),
      items: z.array(z.object({ ingrediente: z.string(), cantidad: z.string() })),
    })),
    planSemanal: z.array(z.any()),
  }),
})

export type CreateListInput = z.infer<typeof CreateListSchema>
```

---

## Mobile-First / PWA (Capacitor-Ready)

### Breakpoints (Tailwind CSS 4)
```css
/* globals.css */
@theme {
  --breakpoint-xs: 320px;
  --breakpoint-sm: 640px;
  --breakpoint-md: 768px;
  --breakpoint-lg: 1024px;
  --breakpoint-xl: 1280px;
}
```

### Touch Targets
```tsx
// components/ui/button.tsx
export function Button({ children, ...props }: ButtonProps) {
  return (
    <button
      className="min-h-[44px] min-w-[44px] touch-manipulation ..."
      {...props}
    >
      {children}
    </button>
  )
}
```

### PWA Manifest (app/manifest.ts)
```typescript
export default function manifest(): MetadataManifest {
  return {
    name: "Lista de la Compra IA",
    short_name: "ListaCompra",
    start_url: "/dashboard",
    display: "standalone",
    background_color: "#ffffff",
    theme_color: "#3ECF8E",
    icons: [
      { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png", purpose: "any maskable" },
      { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png", purpose: "any maskable" },
    ],
    screenshots: [],
    shortcuts: [],
  }
}
```

### Service Worker (next-pwa)
```javascript
// next.config.js
const withPWA = require("next-pwa")({
  dest: "public",
  register: true,
  skipWaiting: true,
  disable: process.env.NODE_ENV === "development",
  runtimeCaching: [
    { urlPattern: /^https:\/\/.*\.supabase\.co\/.*/i, handler: "NetworkFirst", options: { cacheName: "supabase-api", expiration: { maxEntries: 100, maxAgeSeconds: 60 * 60 * 24 } } },
    { urlPattern: /^https:\/\/generativelanguage\.googleapis\.com\/.*/i, handler: "NetworkFirst", options: { cacheName: "gemini-api", expiration: { maxEntries: 50, maxAgeSeconds: 60 * 60 } } },
  ],
})
module.exports = withPWA(nextConfig)
```

---

## Estructura de Archivos Obligatoria

```
src/
├── app/
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   ├── register/page.tsx
│   │   └── layout.tsx
│   ├── (dashboard)/
│   │   ├── layout.tsx          # Server Component con nav + getUser()
│   │   ├── page.tsx            # Redirect a /dashboard/listas
│   │   ├── listas/
│   │   │   ├── page.tsx        # ListsContent (Suspense)
│   │   │   ├── _components/
│   │   │   │   ├── lists-content.tsx
│   │   │   │   ├── list-card.tsx
│   │   │   │   └── list-skeleton.tsx
│   │   │   ├── nueva/page.tsx  # Upload PDF → Server Action
│   │   │   └── [id]/page.tsx   # Detalle + checks + export
│   │   ├── historial/page.tsx
│   │   └── perfil/page.tsx
│   ├── actions/
│   │   ├── lists.ts
│   │   ├── auth.ts
│   │   └── pdf.ts
│   ├── api/
│   │   └── webhooks/
│   ├── layout.tsx              # Providers: Session, Query, Theme
│   ├── page.tsx                # Landing → redirect (auth) ? dashboard : login
│   ├── globals.css
│   └── manifest.ts
├── components/
│   ├── ui/                     # Radix + Tailwind primitives
│   ├── forms/                  # react-hook-form + Zod resolvers
│   ├── lists/
│   └── mobile/
├── lib/
│   ├── server/
│   │   ├── supabase.ts         # createServerSupabaseClient (Service Role)
│   │   ├── gemini.ts           # generateShoppingList (API Key)
│   │   └── pdf.ts              # parsePdfBuffer (pdf-parse)
│   ├── client/
│   │   ├── supabase.ts         # createBrowserSupabaseClient (Anon Key)
│   │   └── hooks/              # useAuth, useLists, useOffline
│   ├── utils/
│   │   ├── cn.ts               # clsx + tailwind-merge
│   │   ├── format.ts           # formatDate, formatCurrency
│   │   └── validation.ts       # zod schemas export
│   ├── env.ts                  # Zod parse process.env (top-level await)
│   └── errors.ts               # ERROR_CODES, AppError, Result<T,E>
├── hooks/
├── types/
│   └── database.ts             # Generado: npx supabase gen types typescript
├── middleware.ts               # Auth guard + security headers
└── instrumentation.ts          # Sentry + OpenTelemetry init
```

---

## Context7: Consulta Obligatoria Antes de Código Complejo

```bash
# Antes de implementar cualquier feature Next.js/Supabase:
# 1. Resolve library ID
context7.resolve-library-id("next@latest")
context7.resolve-library-id("@supabase/supabase-js@2")

# 2. Get specific docs
context7.query-docs(<next-id>, "/docs/app-router/server-actions")
context7.query-docs(<supabase-id>, "/docs/guides/row-level-security")
context7.query-docs(<supabase-id>, "/docs/guides/auth/server-side-auth")
```

**No escribir código sin consultar Context7 primero.**

---

## Checklist de Implementación

- [ ] `tsconfig.json` con flags estrictos
- [ ] `next.config.js` con PWA, CSP, headers de seguridad
- [ ] `middleware.ts` con auth guard + security headers
- [ ] `lib/env.ts` con validación Zod (falla en build si falta variable)
- [ ] `lib/errors.ts` con `Result<T,E>` discriminado + `ERROR_CODES`
- [ ] Server Actions en `app/actions/` con Zod validation
- [ ] Componentes Server por defecto, `use client` solo en hojas
- [ ] `fetch` con `next: { tags, revalidate }` + `revalidateTag` en mutaciones
- [ ] Mobile-first: 320px breakpoint, touch targets 44px, safe-area
- [ ] PWA: manifest.ts, SW, icons, offline fallback
- [ ] Context7 consultado para cada librería/config nueva