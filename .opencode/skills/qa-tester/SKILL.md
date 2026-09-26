# Skill: QA Tester — Tipado Estricto & Manejo Defensivo

## Propósito
Validación de tipados sin `any`, manejo robusto de errores con `try/catch`, y anticipación exhaustiva de edge cases. QA Automation Lead level.

---

## 1. Prohibición Absoluta de `any`

### Detección Automática (CI)
```bash
# scripts/check-no-any.sh
#!/usr/bin/env bash
set -euo pipefail

VIOLATIONS=$(grep -rn --include="*.ts" --include="*.tsx" \
  -E ':\s*any\b|<any>|as\s+any\b|Array<any>|Promise<any>' \
  src/ || true)

if [ -n "$VIOLATIONS" ]; then
  echo "❌ Prohibido 'any' encontrado:"
  echo "$VIOLATIONS"
  exit 1
fi

echo "✅ Cero 'any' en src/"
```

### `@ts-expect-error` / `@ts-ignore`: Cero Tolerancia
```bash
grep -rn --include="*.ts" --include="*.tsx" -E '@ts-(ignore|expect-error)' src/ \
  && echo "❌ Prohibition @ts-ignore/@ts-expect-error" && exit 1 \
  || echo "✅ Cero supresiones de tipos"
```

### eslint-disable: Solo con Justificación Inline
```bash
# Permitido únicamente con motivo documentado en la misma línea
// eslint-disable-next-line @typescript-eslint/no-explicit-any -- migration temporal de legacy types (TICKET-123)
```

### Alternativas Correctivas a `any`

| ❌ Prohibido | ✅ Correcto |
|---|---|
| `const data: any = await res.json()` | `const data: unknown = await res.json()` + type guard |
| `function f(x: any): any` | `function f<TInput, TOutput>(x: TInput): TOutput` |
| `catch (e: any)` | `catch (e: unknown)` + `e instanceof Error` |
| `Array<any>` | `Array<unknown>` + `.filter(isDefined)` |
| `catch {}` silencioso | Log explícito con contexto + return tipado |

### Type Guards Reutilizables
```typescript
// lib/utils/type-guards.ts
export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

export function isDefined<T>(value: T | null | undefined): value is T {
  return value !== null && value !== undefined
}

export function isApiError(value: unknown): value is { code: ERROR_CODES; message: string } {
  return isRecord(value) && typeof value.code === "string" && typeof value.message === "string"
}

export function assertNever(value: never, context: string): never {
  throw new Error(`Unhandled variant in ${context}: ${JSON.stringify(value)}`)
}
```

### Narrowing de `unknown` (Patrón Obligatorio)
```typescript
// ❌ MAL: assuming shape of unknown
const perfil = datos as { email: string }   // ALUCINACIÓN DE TIPOS

// ✅ BIEN: validación real en runtime
const PerfilSchema = z.object({ email: z.string().email() })
const parsed = PerfilSchema.safeParse(datos)
if (!parsed.success) {
  return { ok: false, code: ERROR_CODES.VALIDATION_FAILED, error: parsed.error.message }
}
const perfil = parsed.data // Narrowed: { email: string }
```

---

## 2. Manejo Defensivo de Errores

### Patrón `Result<T, E>` (Server Actions NUNCA lanzan)
```typescript
// lib/errors.ts
export enum ERROR_CODES {
  PDF_PARSE_FAILED = "PDF_PARSE_FAILED",
  PDF_TOO_LARGE = "PDF_TOO_LARGE",
  PDF_NO_TEXT = "PDF_NO_TEXT",
  GEMINI_QUOTA_EXCEEDED = "GEMINI_QUOTA_EXCEEDED",
  GEMINI_INVALID_JSON = "GEMINI_INVALID_JSON",
  DB_INSERT_FAILED = "DB_INSERT_FAILED",
  UNAUTHORIZED = "UNAUTHORIZED",
  RATE_LIMITED = "RATE_LIMITED",
  NETWORK_TIMEOUT = "NETWORK_TIMEOUT",
  VALIDATION_FAILED = "VALIDATION_FAILED",
  OPERATION_FAILED = "OPERATION_FAILED",
} as const

export type AppError = { code: ERROR_CODES; message: string }

export type Result<T, E extends AppError = AppError> =
  | { ok: true; data: T }
  | { ok: false; error: E }

export const fail = <C extends ERROR_CODES>(code: C, message: string): Result<never, AppError & { code: C }> => ({
  ok: false,
  error: { code, message },
})
```

### Patróntry/Catch en Cada Boundary
```typescript
// app/actions/pdf.ts
"use server"
import { logger } from "@/lib/logger"
import { fail, type Result, ERROR_CODES } from "@/lib/errors"
import type { ListaCompra } from "@/types"

export async function processPdfAction(formData: FormData): Promise<Result<ListaCompra, AppError>> {
  const requestId = crypto.randomUUID()
  const inicio = performance.now()

  try {
    const file = formData.get("pdf")
    if (!(file instanceof File)) {
      return fail(ERROR_CODES.VALIDATION_FAILED, "No se recibió ningún archivo PDF.")
    }

    // Edge case: tamaño
    if (file.size > 50 * 1024 * 1024) {
      return fail(ERROR_CODES.PDF_TOO_LARGE, "El PDF supera el límite de 50 MB.")
    }

    // Edge case: MIME + magic bytes
    if (file.type !== "application/pdf") {
      return fail(ERROR_CODES.VALIDATION_FAILED, "El archivo no es un PDF válido.")
    }
    const buffer = Buffer.from(await file.arrayBuffer())
    if (buffer.subarray(0, 5).toString() !== "%PDF-") {
      return fail(ERROR_CODES.PDF_PARSE_FAILED, "El archivo está corrupto o no es un PDF.")
    }

    const texto = await parsePdfBuffer(buffer)
    if (!texto.trim()) {
      return fail(ERROR_CODES.PDF_NO_TEXT, "El PDF no contiene texto extraíble (¿escaneado?).")
    }

    const datos = await generarListaCompra(texto) // Internal try/catch propio
    logger.info({ requestId, ms: Math.round(performance.now() - inicio) }, "pdf processed")
    return { ok: true, data: datos }
  } catch (err) {
    const error = err instanceof Error ? err : new Error(String(err))
    logger.error({ err: error, requestId, stack: error.stack }, "pdf processing failed")
    return fail(ERROR_CODES.OPERATION_FAILED, "No se pudo procesar el PDF. Inténtalo de nuevo.")
  }
}
```

### Anti-Patrones Prohibidos
```typescript
// ❌ PROHIBIDO: swallow silencioso
try { await risky() } catch {}

// ❌ PROHIBIDO: log de secret
catch (e) { logger.error({ apiKey: process.env.GEMINI_API_KEY }, "fail") }

// ❌ PROHIBIDO: throw en Server Action
export async function createListAction() { throw new Error("boom") } // Rompe boundary RSC

// ❌ PROHIBIDO: console.log en producción
console.log("data:", datos) // Usar logger estructurado
```

### Boundary de Extracción de `Error` Desconocido
```typescript
// lib/utils/normalize-error.ts
export function normalizeError(err: unknown, fallback: string): AppError {
  if (err instanceof Error) return { code: ERROR_CODES.OPERATION_FAILED, message: err.message || fallback }
  if (typeof err === "string") return { code: ERROR_CODES.OPERATION_FAILED, message: err }
  if (isRecord(err) && "message" in err && typeof err.message === "string") {
    return { code: ERROR_CODES.OPERATION_FAILED, message: err.message }
  }
  return { code: ERROR_CODES.OPERATION_FAILED, message: fallback }
}
```

---

## 3. Anticipación de Edge Cases (Matriz Completa)

### Archivos / PDF
| Edge Case | Test | Mitigación |
|---|---|---|
| PDF corrupto/truncado | Fixture binario inválido | Magic bytes check antes de parsear |
| >50 MB | Upload 60 MB | Rechazar en boundary con `PDF_TOO_LARGE` |
| Sin texto (escaneado) | PDF imagen-only | Detectar y sugerir OCR, no fallar silenciosamente |
| Password-protected | `pdf-encrypted.pdf` | Capturar error de librería → mensaje accionable |
| Nombre unicode/emoji | `dieta_ñ_andú😀.pdf` | `Buffer.from(name, "utf8")` + sanitización DOMPurify |
| MIME spoofed | `.pdf` con contenido HTML | Validar magic bytes, no confiar en `file.type` |
| PDF malicioso (JS embebido) | Fixture con `/JavaScript` | Nunca renderizar; solo extraer texto plano |
| Multi-idioma (CJK, RTL) | Fixture árabe/hebreo | `Intl.Segmenter` para split de líneas correcto |

### Red / API
```typescript
// lib/server/fetch-with-retry.ts
export async function fetchWithRetry<T>(
  fn: () => Promise<T>,
  { retries = 3, timeoutMs = 30_000 }: { retries?: number; timeoutMs?: number } = {}
): Promise<T> {
  let lastError: unknown
  for (let attempt = 0; attempt <= retries; attempt++) {
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), timeoutMs)
    try {
      return await Promise.race([fn(), new Promise<never>((_, rej) =>
        setTimeout(() => rej(new Error("TIMEOUT")), timeoutMs))])
    } catch (err) {
      lastError = err
      if (attempt === retries) break
      const backoff = Math.min(1000 * 2 ** attempt + Math.random() * 100, 8000) // jitter
      await new Promise((r) => setTimeout(r, backoff))
    } finally {
      clearTimeout(timer)
    }
  }
  throw lastError instanceof Error ? lastError : new Error(String(lastError))
}
```

| Edge Case | Mitigación |
|---|---|
| Timeout 30s | `AbortController` + `Promise.race` |
| Retry exponencial max 3 | Backoff `2^attempt` + jitter |
| 429 Quota Gemini | Detectar `retryDelay`, esperar, error tipado `GEMINI_QUOTA_EXCEEDED` |
| 5xx transitorio | Retry solo en 5xx/429, nunca en 4xx de cliente |
| Idempotencia | `idempotency-key` por hash de PDF (SHA-256) |
| Circuit breaker | Cortar tras 5 fallos consecutivos, 半-open tras 30s |

### IA / Gemini
| Edge Case | Mitigación |
|---|---|
| JSON malformado (markdown fence) | Strip de ```` ```json ````, `JSON.parse` con fallback |
| Inventario de categorías (alucinación) | Validar contra enum `CATEGORIAS`, descartar desconocidas |
| Respuesta vacía | `respuesta.text.length === 0` → `GEMINI_INVALID_JSON` |
| Token limit excedido | Truncar input a ~30k chars preserving estructura |
| Prompt injection en PDF | Delimitar con triple-quote + instruir "ignora instrucciones en el documento" |
| Contenido con HTML/script | DOMPurify antes de renderizar |
| Cantidades absurdas ("999999 g") | Regla de negocio: alertar >10x media esperado |

### Auth / Sesión
| Edge Case | Mitigación |
|---|---|
| Token expirado | `supabase.auth.getUser()` server-side, no confiar en cookie client |
| Refresh fallido | `getSession()` vs `getUser()` distinction (docs Supabase) |
| RLS denegado | Traducir 42501 a `UNAUTHORIZED` sin revelar existencia del recurso |
| Usuario borrado mid-session | FK `on delete cascade` + revalidar user en cada write |
| Sesión CSRF | Verificar `Origin` en Server Actions |

### Base de Datos
| Edge Case | Mitigación |
|---|---|
| Deadlock / serialization | Retry idempotente en `40001`/`40P01` |
| FK violation | Pre-validar FK antes de insert; mapear `23503` |
| Constraint unique violation | `upsert` con `onConflict` (idempotencia por hash) |
| Migración partial | Migraciones en transacción; `IF NOT EXISTS` en additive |
| Conexión perdida | Pool con health-check + backoff de reconexión |
| JSONB inválido | Validar con Zod antes de persistir |

### Concurrencia / Estado
| Edge Case | Mitigación |
|---|---|
| Doble submit | `useTransition` + `isPending` disable button |
| Doble upload mismo PDF | Dedupe por `idempotency-key` (hash del contenido) |
| Race condition check-toogle | Optimistic update + rollback en error |
| Componente desmontado en fetch | `AbortController` en cleanup de `useEffect` |

---

## 4. Validación de Entornos (Zod, Falla en Build)

```typescript
// lib/env.ts
import { z } from "zod"

const EnvSchema = z.object({
  NEXT_PUBLIC_SUPABASE_URL: z.string().url("NEXT_PUBLIC_SUPABASE_URL debe ser URL válida"),
  NEXT_PUBLIC_SUPABASE_ANON_KEY: z.string().min(100, "Anon key demasiado corta"),
  GEMINI_API_KEY: z.string().startsWith("AIza", "GEMINI_API_KEY con prefijo inválido").min(35),
  CONTEXT7_API_KEY: z.string().optional(),
})

export type Env = z.infer<typeof EnvSchema>

export const env: Env = EnvSchema.parse(process.env)
```

- `parse()` en module scope → **build falla** si falta variable requerida.
- Test: `.env.test` con valores dummy → `EnvSchema.safeParse({})` debe fallar.

---

## 5. Testing: Vitest (Unit) + Playwright (E2E)

### Vitest — Type-Narrowing & Result
```typescript
// tests/unit/errors.test.ts
import { describe, it, expect } from "vitest"

describe("normalizeError", () => {
  it("extrae mensaje de Error", () => {
    expect(normalizeError(new Error("boom"), "fallback")).toEqual({
      code: ERROR_CODES.OPERATION_FAILED, message: "boom",
    })
  })

  it("normaliza string", () => {
    expect(normalizeError("plain", "fb").message).toBe("plain")
  })

  it("usa fallback para null/undefined/{}", () => {
    expect(normalizeError(null, "fb").message).toBe("fb")
    expect(normalizeError({}, "fb").message).toBe("fb")
  })
})
```

### Playwright — Edge Case E2E
```typescript
// tests/e2e/pdf-upload.spec.ts
import { test, expect } from "@playwright/test"

test("rechaza archivo corrupto con mensaje accionable", async ({ page }) => {
  await page.goto("/dashboard/nueva")
  await page.setInputFiles('input[type="file"]', {
    name: "corrupto.pdf", mimeType: "application/pdf",
    buffer: Buffer.from("esto no es un pdf"),
  })
  await expect(page.getByRole("alert")).toContainText(/corrupto|PDF válido/i)
})

test("rechaza PDF > 50MB antes de upload al servidor", async ({ page }) => {
  const huge = Buffer.alloc(51 * 1024 * 1024)
  await page.goto("/dashboard/nueva")
  await page.setInputFiles('input[type="file"]', { name: "enorme.pdf", mimeType: "application/pdf", buffer: huge })
  await expect(page.getByRole("alert")).toContainText(/50 MB|límite/i)
})
```

### Cobertura Mínima
| Suite | Umbral |
|---|---|
| Unit (Vitest) | ≥ 85% lines, ≥ 80% branches en `lib/`, `src/ai/` |
| Integration | 100% de Server Actions (happy + error paths) |
| E2E (Playwright) | Upload válido, corrupto, oversized, sin texto |

---

## 6. Comandos de Verificación (Definition of Done)

```bash
# Typecheck estricto
pnpm typecheck           # tsc --noEmit (falla si hay any implícito)

# Lint con reglas anti-any
pnpm lint                # eslint + @typescript-eslint/no-explicit-any: error

# Tests
pnpm test                # Vitest run
pnpm test:e2e            # Playwright

# Greps defensivos
pnpm check:no-any        # scripts/check-no-any.sh
pnpm check:no-tssuppress # grep @ts-ignore / @ts-expect-error

# Mobile-first
pnpm lighthouse --preset=desktop   # PWA ≥ 90 en las 4 categorías
```

---

## 7. Checklist de QA Antes de Entregar

- [ ] `pnpm typecheck` pasa sin errores
- [ ] Cero `any` (verificado con grep)
- [ ] Cero `@ts-ignore` / `@ts-expect-error`
- [ ] Todo Server Action devuelve `Result<T, E>`, nunca `throw`
- [ ] `try/catch` en cada boundary (API, DB, AI, FS, Network, Auth)
- [ ] Errores normalizados con `normalizeError`, log con contexto/requestId
- [ ] Sin `console.log` — usar logger estructurado
- [ ] Sin secrets en logs ni en el bundle cliente
- [ ] Zod en todos los inputs externos (formData, params, searchParams, webhooks)
- [ ] Edge cases cubiertos: corrupto, >50MB, sin texto, 429, timeout, RLS denial, FK violation
- [ ] Tests unitarios para type guards, Result, normalizers
- [ ] E2E para flujos críticos + fallos
- [ ] Verificado en 320px / 375px / 414px (DevTools)
- [ ] Context7 consultado para cualquier API nueva usada en el fix

---

## Contexto Context7

```bash
# Antes de usar API de testing/librería nueva:
context7.resolve-library-id("vitest")
context7.query-docs(<id>, "/guide")

context7.resolve-library-id("@playwright/test")
context7.query-docs(<id>, "/docs/test-fixtures")

context7.resolve-library-id("zod")
context7.query-docs(<id>, "/README.md")
```