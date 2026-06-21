import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login, register, type User } from '../api'
import { CURRENT_VERSION } from '../releaseNotes'

interface LoginProps {
  onLogin: (user: User) => void
  onWhatsNew: () => void
}

export default function Login({ onLogin, onWhatsNew }: LoginProps) {
  const navigate = useNavigate()
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      let result
      if (mode === 'login') {
        result = await login(email, password)
      } else {
        if (!displayName.trim()) { setError('Display name is required'); setLoading(false); return }
        result = await register(email, password, displayName)
      }
      localStorage.setItem('token', result.token)
      onLogin(result.user)
      navigate('/', { replace: true })
    } catch (err: any) {
      setError(err.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-wrap">
      <div className="auth-card">
        <div className="auth-logo">
          <h1>Field Intel</h1>
          <p>Orthopedic sales intelligence</p>
        </div>

        {error && <div className="error-msg">{error}</div>}

        <form onSubmit={handleSubmit}>
          {mode === 'register' && (
            <div className="form-group">
              <label className="form-label">Full Name</label>
              <input
                className="form-input"
                type="text"
                placeholder="Alex Johnson"
                value={displayName}
                onChange={e => setDisplayName(e.target.value)}
                required
              />
            </div>
          )}
          <div className="form-group">
            <label className="form-label">Email</label>
            <input
              className="form-input"
              type="email"
              placeholder="you@company.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
              autoFocus
            />
          </div>
          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              className="form-input"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
            />
          </div>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? <span className="spinner" /> : mode === 'login' ? 'Sign In' : 'Create Account'}
          </button>
        </form>

        <div className="auth-switch">
          {mode === 'login' ? (
            <>New here? <a href="#" onClick={e => { e.preventDefault(); setMode('register') }}>Create account</a></>
          ) : (
            <>Already have an account? <a href="#" onClick={e => { e.preventDefault(); setMode('login') }}>Sign in</a></>
          )}
        </div>
      </div>

      <div className="login-footer">
        <a href="#" className="login-footer-link" onClick={e => { e.preventDefault(); onWhatsNew() }}>What's New</a>
        <span className="login-footer-sep">·</span>
        <span className="login-footer-version">{CURRENT_VERSION}</span>
      </div>
    </div>
  )
}
