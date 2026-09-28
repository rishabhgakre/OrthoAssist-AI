import { NavLink } from 'react-router-dom'
import {
  IconLayoutDashboard, IconUsers, IconFileReport, IconLogout, IconX,
} from '@tabler/icons-react'
import { useAuth } from '../context/AuthContext'
import { initials } from '../lib/format'

const navItems = [
  { to: '/', label: 'Dashboard', icon: IconLayoutDashboard },
  { to: '/patients', label: 'Patients', icon: IconUsers },
  { to: '/reports', label: 'Reports', icon: IconFileReport },
]

export default function Sidebar({ onNavigate, onClose }) {
  const { logout, doctor } = useAuth()

  return (
    <div className="flex flex-col justify-between h-full bg-ink px-4 py-5">
      <div>
        <div className="flex items-center justify-between mb-8 px-1">
          <img
            src="/brand/logo-lockup.png"
            alt="OrthoAssist AI"
            className="h-9 w-auto object-contain object-left select-none"
            draggable={false}
          />
          {onClose && (
            <button
              onClick={onClose}
              className="lg:hidden text-[#8FA095] hover:text-page p-1 -mr-1"
              aria-label="Close menu"
            >
              <IconX size={18} />
            </button>
          )}
        </div>

        <nav className="space-y-1">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              onClick={onNavigate}
              className={({ isActive }) =>
                `flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-[13px] transition-colors ${
                  isActive
                    ? 'bg-ink-raised text-gold-bright font-semibold'
                    : 'text-[#8FA095] hover:text-page hover:bg-ink-raised/70'
                }`
              }
            >
              <Icon size={16} stroke={1.8} />
              {label}
            </NavLink>
          ))}
        </nav>
      </div>

      <div className="border-t border-ink-line pt-3">
        <div className="flex items-center gap-2.5 px-1 mb-2">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gold-bright to-gold flex items-center justify-center text-[11px] text-ink font-mono font-bold flex-shrink-0">
            {doctor ? initials(doctor.name) : '··'}
          </div>
          <div className="min-w-0">
            <div className="text-[12px] text-page font-medium truncate">
              {doctor ? doctor.name : 'Loading…'}
            </div>
            <div className="text-[10.5px] text-[#71816F]">Clinician</div>
          </div>
        </div>
        <button
          onClick={logout}
          className="w-full flex items-center gap-2.5 px-1 py-1.5 text-[11.5px] text-[#8FA095] hover:text-page transition-colors"
        >
          <IconLogout size={14} />
          Sign out
        </button>
      </div>
    </div>
  )
}
