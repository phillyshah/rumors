import { BrowserRouter, Navigate, NavLink, Route, Routes, useLocation } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { getMe, type User } from './api'
import Capture from './screens/Capture'
import Search from './screens/Search'
import NoteDetail from './screens/NoteDetail'
import Login from './screens/Login'
import Admin from './screens/Admin'

function AuthGuard({ user, children }: { user: User | null; children: React.ReactNode }) {
  if (!user) return <Navigate to="/login" replace />
  return <>{children}</>
}

function BottomNav({ user }: { user: User | null }) {
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

export default function App() {
  const [user, setUser] = useState<User | null | undefined>(undefined)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) { setUser(null); return }
    getMe().then(setUser).catch(() => {
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

  return (
    <BrowserRouter>
      <BottomNav user={user} />
      <Routes>
        <Route path="/login" element={<Login onLogin={setUser} />} />
        <Route path="/" element={<AuthGuard user={user}><Capture user={user!} onLogout={handleLogout} /></AuthGuard>} />
        <Route path="/search" element={<AuthGuard user={user}><Search user={user!} onLogout={handleLogout} /></AuthGuard>} />
        <Route path="/notes/:id" element={<AuthGuard user={user}><NoteDetail /></AuthGuard>} />
        <Route path="/admin" element={<AuthGuard user={user}><Admin user={user!} /></AuthGuard>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
