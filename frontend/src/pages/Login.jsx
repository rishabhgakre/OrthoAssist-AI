import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { IconArrowRight, IconAlertTriangle } from '@tabler/icons-react'
import { useAuth } from '../context/AuthContext'
import { errMsg } from '../lib/format'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { loginUser } = useAuth()
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await loginUser(email, password)
      navigate('/')
    } catch (err) {
      setError(errMsg(err, 'Could not sign in — check your email and password.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-page px-4 py-8">
      <div className="w-full max-w-4xl flex flex-col md:flex-row rounded-2xl overflow-hidden shadow-panel">
        {/* Brand panel — logo centered, composition reads as one balanced block */}
        <div className="md:flex flex-col items-center justify-center flex-none md:w-[44%] bg-ink px-8 py-12 relative overflow-hidden hidden">
          <div
            className="absolute inset-0 opacity-[0.05]"
            style={{
              backgroundImage: 'radial-gradient(circle at 1px 1px, #C9A66B 1px, transparent 0)',
              backgroundSize: '18px 18px',
            }}
          />
          <div className="relative flex flex-col items-center text-center max-w-[260px]">
            <img
              src="/brand/logo-lockup.png"
              alt="OrthoAssist AI"
              className="w-full max-w-[220px] h-auto object-contain mb-7 select-none"
              draggable={false}
            />
            <p className="text-[12.5px] text-[#93A099] leading-relaxed">
              An AI-powered clinical decision support system with gait-integrated
              orthopedic recovery scoring.
            </p>
            <div className="flex items-center gap-4 mt-8 pt-6 border-t border-ink-line w-full justify-center">
              <div className="text-center">
                <div className="text-gold font-mono text-[15px] font-semibold">SRS</div>
                <div className="text-[9.5px] text-[#6E7D74] mt-0.5">Structural</div>
              </div>
              <div className="w-px h-7 bg-ink-line" />
              <div className="text-center">
                <div className="text-amethyst-bright font-mono text-[15px] font-semibold">FRS</div>
                <div className="text-[9.5px] text-[#6E7D74] mt-0.5">Functional</div>
              </div>
              <div className="w-px h-7 bg-ink-line" />
              <div className="text-center">
                <div className="text-gold-bright font-mono text-[15px] font-semibold">CORI</div>
                <div className="text-[9.5px] text-[#6E7D74] mt-0.5">Composite</div>
              </div>
            </div>
          </div>
        </div>

        {/* Mobile brand strip */}
        <div className="md:hidden bg-ink flex items-center justify-center py-7">
          <img src="/brand/logo-lockup.png" alt="OrthoAssist AI" className="h-14 w-auto object-contain" draggable={false} />
        </div>

        {/* Form panel */}
        <div className="flex-1 bg-card px-7 py-10 sm:px-12 sm:py-14 flex items-center">
          <form onSubmit={handleSubmit} className="w-full max-w-[320px] mx-auto">
            <div className="font-display text-[22px] text-body font-semibold mb-1.5">
              Welcome back
            </div>
            <p className="text-[12.5px] text-muted mb-7">Sign in to your clinician account</p>

            <div className="mb-4">
              <label className="field-label">Email</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="dr.sharma@orthoassist.ai"
                className="input-base"
                autoComplete="email"
              />
            </div>

            <div className="mb-5">
              <label className="field-label">Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••"
                className="input-base"
                autoComplete="current-password"
              />
            </div>

            {error && (
              <div className="flex items-start gap-2 text-[12px] text-garnet bg-garnet-bg rounded-lg px-3.5 py-2.5 mb-4">
                <IconAlertTriangle size={14} className="flex-shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            <button type="submit" disabled={loading} className="btn-primary w-full py-3">
              {loading ? 'Signing in…' : (<>Sign in <IconArrowRight size={14} /></>)}
            </button>

            <p className="text-center text-[12px] text-muted mt-5">
              New here?{' '}
              <Link to="/signup" className="text-[#8C6B2E] font-semibold hover:underline">
                Create an account
              </Link>
            </p>
          </form>
        </div>
      </div>
    </div>
  )
}
