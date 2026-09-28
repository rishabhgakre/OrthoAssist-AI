import { useState } from 'react'
import { IconMenu2 } from '@tabler/icons-react'
import Sidebar from './Sidebar'

export default function Layout({ children }) {
  const [drawerOpen, setDrawerOpen] = useState(false)

  return (
    <div className="min-h-screen bg-page">
      {/* Desktop sidebar — fixed */}
      <div className="hidden lg:block fixed inset-y-0 left-0 w-[248px] z-30">
        <Sidebar />
      </div>

      {/* Mobile top bar */}
      <div className="lg:hidden sticky top-0 z-40 bg-ink flex items-center justify-between px-4 py-3">
        <img src="/brand/logo-lockup.png" alt="OrthoAssist AI" className="h-7 w-auto object-contain" draggable={false} />
        <button
          onClick={() => setDrawerOpen(true)}
          className="text-page p-1.5 -mr-1.5"
          aria-label="Open menu"
        >
          <IconMenu2 size={20} />
        </button>
      </div>

      {/* Mobile drawer */}
      {drawerOpen && (
        <div className="lg:hidden fixed inset-0 z-50 animate-fade-in">
          <div className="absolute inset-0 bg-black/50" onClick={() => setDrawerOpen(false)} />
          <div className="absolute inset-y-0 left-0 w-[260px] shadow-panel">
            <Sidebar onNavigate={() => setDrawerOpen(false)} onClose={() => setDrawerOpen(false)} />
          </div>
        </div>
      )}

      <main className="lg:ml-[248px] px-4 py-5 sm:px-6 sm:py-7 lg:px-9 lg:py-8 max-w-[1400px]">
        {children}
      </main>
    </div>
  )
}
