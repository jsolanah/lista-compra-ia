# Skill: Security Auditor — Supabase/RLS & API Keys

## Propósito
Auditoría de seguridad obligatoria: Row Level Security (RLS) en Supabase, protección de API Keys, Zero Trust architecture.

---

## 1. Row Level Security (RLS) — Obligatorio en TODAS las Tablas

### Política Base: Usuario solo ve/edita sus datos
```sql
-- Habilitar RLS
ALTER TABLE public.listas_compra ENABLE ROW LEVEL SECURITY;

-- SELECT: usuario ve solo sus listas
CREATE POLICY "Usuario ve sus listas"
ON public.listas_compra FOR SELECT
USING (auth.uid() = usuario_id);

-- INSERT: usuario crea solo sus listas
CREATE POLICY "Usuario crea sus listas"
ON public.listas_compra FOR INSERT
WITH CHECK (auth.uid() = usuario_id);

-- UPDATE: usuario actualiza solo sus listas
CREATE POLICY "Usuario actualiza sus listas"
ON public.listas_compra FOR UPDATE
USING (auth.uid() = usuario_id)
WITH CHECK (auth.uid() = usuario_id);

-- DELETE: usuario borra solo sus listas
CREATE POLICY "Usuario borra sus listas"
ON public.listas_compra FOR DELETE
USING (auth.uid() = usuario_id);
```

### Verificación Automatizada (CI)
```sql
-- tests/security/rls_policies.sql
-- Ejecutar en pipeline: todas las tablas deben tener RLS + al menos 1 policy
SELECT
  schemaname,
  tablename,
  rowsecurity as rls_enabled,
  (SELECT count(*) FROM pg_policies WHERE tablename = t.tablename) as policy_count
FROM pg_tables t
WHERE schemaname = 'public'
  AND tablename NOT IN ('schema_migrations', 'spatial_ref_sys')
  AND (rowsecurity = false OR (SELECT count(*) FROM pg_policies WHERE tablename = t.tablename) = 0);
-- Debe devolver 0 filas
```

---

## 2. Separación Estricta de Clientes Supabase

### Server-Only (Service Role Key) — **NUNCA en cliente**
```typescript
// lib/server/supabase.ts
import { createClient } from "@supabase/supabase-js"

export function createServerSupabaseClient() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL!
  const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY!
  if (!url || !serviceRoleKey) throw new Error("Missing Supabase server env vars")
  return createClient(url, serviceRoleKey, {
    auth: { autoRefreshToken: false, persistSession: false },
  })
}

// Uso exclusivo en Server Actions / Route Handlers
// app/actions/lists.ts
const supabase = createServerSupabaseClient()
const { data } = await supabase.from("listas_compra").select("*").eq("usuario_id", user.id)
```

### Browser-Only (Anon Key) — **Solo en componentes Client**
```typescript
// lib/client/supabase.ts
import { createBrowserClient } from "@supabase/ssr"

export function createBrowserSupabaseClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  )
}

// Uso en hooks/components
// hooks/useLists.ts
const supabase = createBrowserSupabaseClient()
const { data } = await supabase.from("listas_compra").select("*")
```

### Verificación: No Service Role en Bundle Cliente
```bash
# En CI: buscar Service Role Key en build output
grep -r "SUPABASE_SERVICE_ROLE_KEY" .next/ && exit 1 || echo "OK: Service Role no en bundle cliente"
```

---

## 3. Protección de API Keys (Gemini, etc.)

### Solo en Server Actions / lib/server/
```typescript
// lib/server/gemini.ts
import { GoogleGenerativeAI } from "@google/generative-ai"

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY!)

export async function generateShoppingList(prompt: string) {
  const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" })
  const result = await model.generateContent(prompt)
  return result.response.text()
}

// app/actions/pdf.ts
"use server"
import { generateShoppingList } from "@/lib/server/gemini"
import { parsePdfBuffer } from "@/lib/server/pdf"

export async function processPdfAction(formData: FormData) {
  const file = formData.get("pdf") as File
  const buffer = Buffer.from(await file.arrayBuffer())
  const text = await parsePdfBuffer(buffer)
  const result = await generateShoppingList(buildPrompt(text))
  return parseGeminiResponse(result)
}
```

### Cliente: Cero Acceso a Secrets
```typescript
// ❌ PROHIBIDO en componentes client
// import { GoogleGenerativeAI } from "@google/generative-ai"
// const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY!) // EXPONE LA KEY

// ✅ CORRECTO: llama a Server Action
// components/forms/upload-pdf.tsx
"use client"
import { processPdfAction } from "@/app/actions/pdf"

export function UploadForm() {
  const handleSubmit = async (formData: FormData) => {
    const result = await processPdfAction(formData) // Server Action
    // handle result
  }
}
```

---

## 4. Variables de Entorno: Clasificación Estricta

| Variable | Prefijo | Dónde | Ejemplo |
|---|---|---|---|
| Supabase URL | `NEXT_PUBLIC_` | Client + Server | `NEXT_PUBLIC_SUPABASE_URL` |
| Supabase Anon Key | `NEXT_PUBLIC_` | Client + Server | `NEXT_PUBLIC_SUPABASE_ANON_KEY` |
| Supabase Service Role | **SIN prefijo** | **Solo Server** | `SUPABASE_SERVICE_ROLE_KEY` |
| Gemini API Key | **SIN prefijo** | **Solo Server** | `GEMINI_API_KEY` |
| Context7 API Key | **SIN prefijo** | **Solo Server** | `CONTEXT7_API_KEY` |
| Encryption Keys | **SIN prefijo** | **Solo Server** | `ENCRYPTION_KEY` |

### Validación en Build (lib/env.ts)
```typescript
// lib/env.ts
import { z } from "zod"

const ServerEnvSchema = z.object({
  SUPABASE_SERVICE_ROLE_KEY: z.string().min(100),
  GEMINI_API_KEY: z.string().startsWith("AIza").min(35),
  CONTEXT7_API_KEY: z.string().optional(),
})

const ClientEnvSchema = z.object({
  NEXT_PUBLIC_SUPABASE_URL: z.string().url(),
  NEXT_PUBLIC_SUPABASE_ANON_KEY: z.string().min(100),
})

// Top-level await: falla en build si falta variable
export const serverEnv = ServerEnvSchema.parse(process.env)
export const clientEnv = ClientEnvSchema.parse(process.env)
```

---

## 5. Content Security Policy (CSP) Estricto

```javascript
// next.config.js
const cspHeader = `
  default-src 'self';
  script-src 'self' 'nonce-{NONCE}' 'strict-dynamic';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: blob: https:;
  font-src 'self' data:;
  connect-src 'self' 
    https://*.supabase.co 
    https://generativelanguage.googleapis.com
    https://api.context7.com;
  frame-ancestors 'none';
  base-uri 'self';
  form-action 'self';
`.replace(/\s{2,}/g, " ").trim()

module.exports = {
  async headers() {
    return [{
      source: "/:path*",
      headers: [
        { key: "Content-Security-Policy", value: cspHeader },
        { key: "X-Content-Type-Options", value: "nosniff" },
        { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
        { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
        { key: "X-Frame-Options", value: "DENY" },
        { key: "Strict-Transport-Security", value: "max-age=31536000; includeSubDomains" },
      ],
    }]
  },
}
```

### Nonce para Scripts Inline (middleware.ts)
```typescript
// middleware.ts
import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"

export function middleware(request: NextRequest) {
  const nonce = Buffer.from(crypto.randomUUID()).toString("base64")
  const csp = request.headers.get("Content-Security-Policy")?.replace("{NONCE}", nonce)
  
  const response = NextResponse.next()
  if (csp) response.headers.set("Content-Security-Policy", csp)
  response.headers.set("x-nonce", nonce)
  return response
}

export const config = { matcher: ["/:path*"] }
```

---

## 6. Rate Limiting en Server Actions

```typescript
// lib/server/rate-limit.ts
import { Ratelimit } from "@upstash/ratelimit"
import { Redis } from "@upstash/redis"

const ratelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(10, "1 m"), // 10 req/min
  analytics: true,
})

export async function checkRateLimit(identifier: string) {
  const { success, limit, reset, remaining } = await ratelimit.limit(identifier)
  return { success, limit, reset, remaining }
}

// app/actions/pdf.ts
export async function processPdfAction(formData: FormData) {
  const supabase = createServerSupabaseClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return { ok: false, error: "Unauthorized", code: "UNAUTHORIZED" }

  const { success } = await checkRateLimit(`pdf:${user.id}`)
  if (!success) return { ok: false, error: "Rate limit exceeded", code: "RATE_LIMITED" }
  
  // ... procesar PDF
}
```

---

## 7. Sanitización de Entrada Usuario

```typescript
// lib/utils/sanitize.ts
import DOMPurify from "isomorphic-dompurify"

export function sanitizeHtml(input: string): string {
  return DOMPurify.sanitize(input, { ALLOWED_TAGS: [], ALLOWED_ATTR: [] })
}

export function sanitizeMarkdown(input: string): string {
  return DOMPurify.sanitize(input, { 
    ALLOWED_TAGS: ["b", "i", "em", "strong", "p", "br", "ul", "ol", "li"],
    ALLOWED_ATTR: [],
  })
}

// Uso en Server Action antes de guardar
export async function saveListAction(formData: FormData) {
  const nombreArchivo = sanitizeHtml(formData.get("nombreArchivo") as string)
  // ...
}
```

---

## 8. Auditoría de Seguridad (Checklist CI)

```yaml
# .github/workflows/security.yml
name: Security Audit
on: [push, pull_request]
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check RLS policies
        run: psql $DATABASE_URL -f tests/security/rls_policies.sql
      - name: Check Service Role not in client bundle
        run: grep -r "SUPABASE_SERVICE_ROLE_KEY" .next/ && exit 1 || echo "OK"
      - name: Check no 'any' in TypeScript
        run: pnpm typecheck 2>&1 | grep -q "any" && exit 1 || echo "OK"
      - name: Run npm audit
        run: pnpm audit --audit-level=high
      - name: Check CSP headers
        run: curl -I http://localhost:3000 | grep -i "content-security-policy"
```

---

## Context7: Consulta Obligatoria

```bash
# Antes de configurar Supabase Auth/RLS:
context7.resolve-library-id("supabase")
context7.query-docs(<id>, "/docs/guides/row-level-security")
context7.query-docs(<id>, "/docs/guides/auth/server-side-auth")
context7.query-docs(<id>, "/docs/guides/auth/row-level-security")

# Antes de configurar CSP/Headers:
context7.resolve-library-id("next@latest")
context7.query-docs(<id>, "/docs/app-router/building-your-application/optimizing/security-headers")
```

---

## Checklist de Auditoría

- [ ] RLS habilitado en **TODAS** las tablas públicas
- [ ] Políticas SELECT/INSERT/UPDATE/DELETE por usuario (`auth.uid()`)
- [ ] Service Role Key **solo** en `lib/server/supabase.ts`
- [ ] Anon Key **solo** en `lib/client/supabase.ts` + `NEXT_PUBLIC_`
- [ ] Gemini API Key **solo** en `lib/server/gemini.ts` + Server Actions
- [ ] `lib/env.ts` valida y falla en build si falta variable server
- [ ] CSP estricto con nonces, `connect-src` restringido
- [ ] Rate limiting en Server Actions (Upstash Redis)
- [ ] Sanitización DOMPurify en inputs user-generated
- [ ] CI: tests de RLS, búsqueda Service Role en bundle, npm audit
- [ ] Context7 consultado para Supabase Auth/RLS y Next.js Security Headers