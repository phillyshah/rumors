import { BrowserRouter, Navigate, NavLink, Route, Routes, useLocation } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { getMe, type User } from './api'
import Capture from './screens/Capture'
import Search from './screens/Search'
import NoteDetail from './screens/NoteDetail'
import Login from './screens/Login'
import Admin from './screens/Admin'
import WhatsNewModal from './components/WhatsNewModal'
import { CURRENT_VERSION } from './releaseNotes'

function AuthGuard({ user, children }: { user: User | null; children: React.ReactNode }) {
  if (!user) return <Navigate to="/login" replace />
  return <>{children}</>
}

function BottomNav({ user, onWhatsNew }: { user: User | null; onWhatsNew: () => void }) {
  const { pathname } = useLocation()
  if (!user || pathname === '/login') return null

  return (
    <nav className="bottom-nav">
      <NavLink to="/" className={({ isActive }) => `nav-btn ${isActive ? 'active' : ''}`} end>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 20h9" /><path d="M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z" />
        </svg>
        Log
      </NavLink>
      <NavLink to="/search" className={({ isActive }) => `nav-btn ${isActive ? 'active' : ''}`}>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        Search
      </NavLink>
      <button className="nav-btn" onClick={onWhatsNew}>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9" />
          <path d="M13.73 21a2 2 0 01-3.46 0" />
        </svg>
        What's New
      </button>
      {user.is_admin && (
        <NavLink to="/admin" className={({ isActive }) => `nav-btn ${isActive ? 'active' : ''}`}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 2l9 4.5V12c0 5.5-3.8 10.7-9 12C3.8 22.7 3 17.5 3 12V6.5L12 2z" />
          </svg>
          Admin
        </NavLink>
      )}
    </nav>
  )
}

function checkAndShowWhatsNew(setShowWhatsNew: (v: boolean) => void) {
  const seen = localStorage.getItem('field_intel_seen_version')
  if (seen !== CURRENT_VERSION) {
    localStorage.setItem('field_intel_seen_version', CURRENT_VERSION)
    setShowWhatsNew(true)
  }
}

export default function App() {
  const [user, setUser] = useState<User | null | undefined>(undefined)
  const [showWhatsNew, setShowWhatsNew] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) { setUser(null); return }
    getMe().then(u => {
      setUser(u)
      checkAndShowWhatsNew(setShowWhatsNew)
    }).catch(() => {
      localStorage.removeItem('token')
      setUser(null)
    })
  }, [])

  if (user === undefined) {
    return (
      <div className="loading-center" style={{ minHeight: '100vh' }}>
        <div className="spinner" />
      </div>
    )
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    setUser(null)
  }

  const handleLogin = (u: User) => {
    setUser(u)
    checkAndShowWhatsNew(setShowWhatsNew)
  }

  return (
    <BrowserRouter>
      {showWhatsNew && <WhatsNewModal onClose={() => setShowWhatsNew(false)} />}
      <BottomNav user={user} onWhatsNew={() => setShowWhatsNew(true)} />
      <Routes>
        <Route path="/login" element={<Login onLogin={handleLogin} />} />
        <Route path="/" element={<AuthGuard user={user}><Capture user={user!} onLogout={handleLogout} /></AuthGuard>} />
        <Route path="/search" element={<AuthGuard user={user}><Search user={user!} onLogout={handleLogout} /></AuthGuard>} />
        <Route path="/notes/:id" element={<AuthGuard user={user}><NoteDetail /></AuthGuard>} />
        <Route path="/admin" element={<AuthGuard user={user}><Admin user={user!} /></AuthGuard>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
