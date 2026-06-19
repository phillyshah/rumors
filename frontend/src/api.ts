export interface Note {
  id: number
  raw_text: string
  created_at: string
  competitors: string[]
  distributors: string[]
  regions: string[]
  states: string[]
  geo_scope: string
  topics: string[]
  entities: { name?: string; [k: string]: unknown }[]
  source_confidence: string | null
  summary: string | null
  extraction_method: string
  enriched_at: string | null
}

export interface NoteDetail extends Note {
  author_display_name: string
}

export interface SearchResponse {
  notes: Note[]
  synthesis: string | null
  total: number
}

export interface User {
  id: number
  email: string
  display_name: string
  region: string | null
  is_admin: boolean
  created_at: string
}

export interface TokenResponse {
  token: string
  user: User
}

function authHeader(): Record<string, string> {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...authHeader(),
      ...(init?.headers as Record<string, string> | undefined),
    },
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  return apiRequest<TokenResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export async function register(
  email: string,
  password: string,
  display_name: string,
): Promise<TokenResponse> {
  return apiRequest<TokenResponse>('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password, display_name }),
  })
}

export async function getMe(): Promise<User> {
  return apiRequest<User>('/auth/me')
}

export async function captureNote(rawText: string): Promise<Note> {
  return apiRequest<Note>('/notes', {
    method: 'POST',
    body: JSON.stringify({ raw_text: rawText }),
  })
}

export async function getFeed(limit = 20, offset = 0): Promise<Note[]> {
  return apiRequest<Note[]>(`/feed?limit=${limit}&offset=${offset}`)
}

export async function getNote(id: number): Promise<NoteDetail> {
  return apiRequest<NoteDetail>(`/notes/${id}`)
}

export interface SearchParams {
  q?: string
  state?: string
  region?: string
  scope?: string
  competitor?: string
  topic?: string
  synthesize?: boolean
  limit?: number
  offset?: number
}

export async function searchNotes(params: SearchParams): Promise<SearchResponse> {
  const qs = new URLSearchParams()
  if (params.q) qs.set('q', params.q)
  if (params.state) qs.set('state', params.state)
  if (params.region) qs.set('region', params.region)
  if (params.scope) qs.set('scope', params.scope)
  if (params.competitor) qs.set('competitor', params.competitor)
  if (params.topic) qs.set('topic', params.topic)
  if (params.synthesize) qs.set('synthesize', 'true')
  if (params.limit) qs.set('limit', String(params.limit))
  if (params.offset) qs.set('offset', String(params.offset))
  return apiRequest<SearchResponse>(`/search?${qs.toString()}`)
}

// Admin APIs
export async function getAdminCompetitors() {
  return apiRequest<any[]>('/admin/competitors')
}

export async function createCompetitor(canonical: string, aliases: string[]) {
  return apiRequest('/admin/competitors', {
    method: 'POST',
    body: JSON.stringify({ canonical, aliases }),
  })
}

export async function deleteCompetitor(id: number) {
  return fetch(`/admin/competitors/${id}`, {
    method: 'DELETE',
    headers: authHeader(),
  })
}

export async function getAdminDistributors() {
  return apiRequest<any[]>('/admin/distributors')
}

export async function createDistributor(canonical: string, aliases: string[], region?: string) {
  return apiRequest('/admin/distributors', {
    method: 'POST',
    body: JSON.stringify({ canonical, aliases, region }),
  })
}

export async function deleteDistributor(id: number) {
  return fetch(`/admin/distributors/${id}`, {
    method: 'DELETE',
    headers: authHeader(),
  })
}

export async function getAdminTopics() {
  return apiRequest<any[]>('/admin/topics')
}

export async function createTopicKeyword(topic: string, keyword: string) {
  return apiRequest('/admin/topics', {
    method: 'POST',
    body: JSON.stringify({ topic, keyword }),
  })
}

export async function deleteTopicKeyword(topic: string, keyword: string) {
  return fetch(`/admin/topics/${encodeURIComponent(topic)}/${encodeURIComponent(keyword)}`, {
    method: 'DELETE',
    headers: authHeader(),
  })
}

export function formatRelativeTime(isoString: string): string {
  const date = new Date(isoString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

export function formatFullTime(isoString: string): string {
  return new Date(isoString).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  })
}
