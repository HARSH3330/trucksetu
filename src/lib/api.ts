const API_BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1').replace(/\/$/, '')
const API_TIMEOUT_MS = 15_000
let rotation: Promise<boolean> | null = null

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
  }
}

function refreshToken(): string | null {
  const legacy = localStorage.getItem('transivox_refresh_token')
  if (legacy) {
    sessionStorage.setItem('transivox_refresh_token', legacy)
    localStorage.removeItem('transivox_refresh_token')
  }
  return sessionStorage.getItem('transivox_refresh_token')
}

export function migrateLegacySession(): void {
  refreshToken()
}

export function saveSession(data: {access_token: string; refresh_token: string}): void {
  sessionStorage.setItem('transivox_access_token', data.access_token)
  sessionStorage.setItem('transivox_refresh_token', data.refresh_token)
  localStorage.removeItem('transivox_refresh_token')
}

export function clearSession(): void {
  sessionStorage.removeItem('transivox_access_token')
  sessionStorage.removeItem('transivox_refresh_token')
  localStorage.removeItem('transivox_refresh_token')
}

async function parse<T>(response: Response): Promise<T> {
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    const detail = data?.detail
    const message = typeof detail === 'string' ? detail : detail?.message || 'Unable to complete the request'
    throw new ApiError(response.status, message)
  }
  return data as T
}

async function request(url: string, init: RequestInit, retryTransient = true): Promise<Response> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), API_TIMEOUT_MS)
  const abort = () => controller.abort()
  init.signal?.addEventListener('abort', abort, {once: true})
  try {
    const response = await fetch(url, {...init, signal: controller.signal})
    if (retryTransient && (!init.method || init.method === 'GET') && [502, 503, 504].includes(response.status)) {
      return request(url, init, false)
    }
    return response
  } catch (error) {
    if (retryTransient && (!init.method || init.method === 'GET') && !controller.signal.aborted) {
      return request(url, init, false)
    }
    if (controller.signal.aborted && !init.signal?.aborted) throw new ApiError(408, 'The request took too long. Please try again.')
    if (error instanceof ApiError) throw error
    throw new ApiError(0, 'Unable to reach TransivoX. Check your connection and try again.')
  } finally {
    clearTimeout(timer)
    init.signal?.removeEventListener('abort', abort)
  }
}

async function rotateSession(): Promise<boolean> {
  const token = refreshToken()
  if (!token) return false
  const response = await request(`${API_BASE}/auth/refresh`, {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({refresh_token: token}),
  }, false)
  if (!response.ok) {
    clearSession()
    return false
  }
  saveSession(await response.json())
  return true
}

async function rotateSessionOnce(): Promise<boolean> {
  if (!rotation) rotation = rotateSession().finally(() => { rotation = null })
  return rotation
}

export async function apiFetch<T>(path: string, init: RequestInit = {}, retry = true): Promise<T> {
  const token = sessionStorage.getItem('transivox_access_token')
  const headers = new Headers(init.headers)
  if (!headers.has('Content-Type') && init.body) headers.set('Content-Type', 'application/json')
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const response = await request(`${API_BASE}${path}`, {...init, headers})
  if (response.status === 401 && retry && await rotateSessionOnce()) return apiFetch<T>(path, init, false)
  if (response.status === 401) clearSession()
  return parse<T>(response)
}

export async function publicFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  if (!headers.has('Content-Type') && init.body) headers.set('Content-Type', 'application/json')
  return parse<T>(await request(`${API_BASE}${path}`, {...init, headers}))
}

export type MarketplaceRequest = {
  id: string; public_id: string; status: string; pickup_address: string; destination_address: string;
  pickup_date: string; pickup_time: string | null; cargo_category: string;
  cargo_weight_tonnes: string; vehicle_count: number; budget_amount: string | null;
}

export type Quote = {
  id: string; service_mode: string; provider_name: string; verified: boolean;
  rating: string; completed_trips: number; cancellation_percent: string;
  vehicle_name: string; final_price: string; vehicles_offered: number;
  status: string; version: number; notes: string | null;
}

export type BookingResult = {
  id: string; public_id: string; trucks_allocated: number;
  total_amount: string; request_allocation: string;
}

export type ProviderProfile = {
  id: string; display_name: string; provider_type: string;
  kyc_status: string; active: boolean;
}

export type VehicleCategory = {
  id: string; name: string; body_type: string;
  min_capacity_tonnes: string; max_capacity_tonnes: string;
}

export type AvailableRoute = {
  id: string; origin: string; destination: string; route_cities: string[];
  departure_at: string; departure_window_end: string | null; expected_arrival_at: string | null;
  remaining_capacity_tonnes: string; remaining_volume_m3: string;
  minimum_booking_tonnes: string; price_amount: string; price_basis: string;
  allowed_cargo_types: string[]; match_score: number;
  provider_name: string | null; provider_rating: string | null; provider_verified: boolean;
  vehicle_name: string | null;
}

export type CurrentUser = {id: string; full_name: string; roles: string[]}

export type Conversation = {
  id: string; booking_id: string; booking_public_id: string;
  status: string; role: string; last_read_at: string | null;
}
export type ChatMessage = {id: string; sender_id: string; body: string; created_at: string}
export type NotificationItem = {id: string; event_type: string; title: string; body: string; read: boolean; created_at: string}
export type NotificationFeed = {unread_count: number; items: NotificationItem[]}
export type NotificationPreferences = {
  in_app: boolean; email: boolean; sms: boolean; whatsapp: boolean;
  quiet_hours_start: string | null; quiet_hours_end: string | null;
}
