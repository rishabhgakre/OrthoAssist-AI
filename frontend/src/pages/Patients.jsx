import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { IconPlus, IconSearch, IconChevronRight, IconUsers } from '@tabler/icons-react'
import Layout from '../components/Layout'
import StatusBadge from '../components/StatusBadge'
import EmptyState from '../components/EmptyState'
import { SkeletonRows } from '../components/Skeleton'
import { useToast } from '../context/ToastContext'
import * as endpoints from '../api/endpoints'
import { initials, errMsg, fmtNum } from '../lib/format'

export default function Patients() {
  const [patients, setPatients] = useState([])
  const [coriByPatient, setCoriByPatient] = useState({})
  const [search, setSearch] = useState('')
  const [boneFilter, setBoneFilter] = useState('All')
  const [loading, setLoading] = useState(true)
  const toast = useToast()

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const res = await endpoints.listPatients()
        if (cancelled) return
        setPatients(res.data)
        const entries = await Promise.all(
          res.data.map(async (p) => {
            try {
              const coriRes = await endpoints.listCoriRecords(p.id)
              const records = coriRes.data
              return [p.id, records.length ? records[records.length - 1] : null]
            } catch {
              return [p.id, null]
            }
          }),
        )
        if (!cancelled) setCoriByPatient(Object.fromEntries(entries))
      } catch (err) {
        if (!cancelled) toast.error(errMsg(err, 'Could not load patients.'))
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const boneTypes = useMemo(() => {
    const set = new Set(patients.map((p) => p.bone_type).filter(Boolean))
    return ['All', ...Array.from(set)]
  }, [patients])

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    return patients.filter((p) => {
      const matchesSearch = !q || p.name.toLowerCase().includes(q) || p.bone_type?.toLowerCase().includes(q)
      const matchesBone = boneFilter === 'All' || p.bone_type === boneFilter
      return matchesSearch && matchesBone
    })
  }, [patients, search, boneFilter])

  return (
    <Layout>
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-5">
        <div>
          <div className="label-eyebrow mb-1">Patients</div>
          <div className="font-display text-[24px] text-body font-semibold leading-tight">All patients</div>
          <div className="text-[12.5px] text-muted mt-1">{patients.length} patients under your care</div>
        </div>
        <Link to="/patients/new" className="btn-gold self-start sm:self-auto">
          <IconPlus size={14} /> New patient
        </Link>
      </div>

      <div className="flex flex-col sm:flex-row gap-2.5 mb-5">
        <div className="flex-1 bg-card border border-border rounded-lg px-3.5 py-2.5 flex items-center gap-2">
          <IconSearch size={14} className="text-muted flex-shrink-0" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search patients by name…"
            className="flex-1 bg-transparent text-[12.5px] outline-none placeholder:text-faint min-w-0"
          />
        </div>
        <div className="flex gap-1.5 overflow-x-auto pb-1 sm:pb-0 -mx-1 px-1 sm:mx-0 sm:px-0">
          {boneTypes.map((b) => (
            <button
              key={b}
              onClick={() => setBoneFilter(b)}
              className={`flex-shrink-0 text-[11.5px] font-semibold px-3.5 py-2 rounded-full border transition-colors whitespace-nowrap ${
                boneFilter === b
                  ? 'bg-ink text-gold-bright border-ink'
                  : 'bg-card text-muted border-border hover:border-border-strong'
              }`}
            >
              {b}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <SkeletonRows count={6} />
      ) : filtered.length === 0 ? (
        <div className="bg-card border border-border rounded-xl">
          {patients.length === 0 ? (
            <EmptyState
              icon={IconUsers}
              title="No patients yet"
              sub="Add your first patient to start tracking structural and functional recovery."
              action={<Link to="/patients/new" className="btn-primary inline-flex"><IconPlus size={13} /> Add patient</Link>}
            />
          ) : (
            <EmptyState icon={IconSearch} title="No matches" sub="Try a different name or bone type filter." />
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3.5">
          {filtered.map((p) => {
            const cori = coriByPatient[p.id]
            return (
              <Link
                to={`/patients/${p.id}`}
                key={p.id}
                className="bg-card border border-border rounded-xl p-4 hover:border-gold-dim hover:shadow-card-hover transition-all group"
              >
                <div className="flex items-center justify-between mb-3.5">
                  <div className="flex items-center gap-2.5 min-w-0">
                    <div className="w-9 h-9 rounded-full bg-ink flex items-center justify-center text-[11px] text-gold font-mono font-semibold flex-shrink-0">
                      {initials(p.name)}
                    </div>
                    <div className="min-w-0">
                      <div className="text-[13.5px] text-body font-semibold truncate">{p.name}</div>
                      <div className="text-[11px] text-muted">Age {p.age} · {p.gender}</div>
                    </div>
                  </div>
                  <IconChevronRight size={16} className="text-faint group-hover:text-body group-hover:translate-x-0.5 transition-all flex-shrink-0" />
                </div>

                <div className="flex items-center justify-between bg-card-alt rounded-lg px-3 py-2 mb-3">
                  <span className="text-[11px] text-muted">Bone type</span>
                  <span className="text-[11.5px] font-semibold text-body capitalize">{p.bone_type}</span>
                </div>

                {p.injury_notes && (
                  <p className="text-[11.5px] text-muted leading-relaxed line-clamp-2 mb-3">{p.injury_notes}</p>
                )}

                <div className="flex items-center justify-between pt-3 border-t border-border">
                  <div className="flex items-center gap-3">
                    <div>
                      <div className="text-[9px] text-faint uppercase tracking-wide">Structural</div>
                      <div className="text-[12px] font-mono font-semibold text-[#8C6B2E]">
                        {cori?.structural_score != null ? `${fmtNum(cori.structural_score, 1)}%` : '—'}
                      </div>
                    </div>
                    <div>
                      <div className="text-[9px] text-faint uppercase tracking-wide">Functional</div>
                      <div className="text-[12px] font-mono font-semibold text-amethyst">
                        {cori?.functional_score != null ? `${fmtNum(cori.functional_score, 1)}%` : '—'}
                      </div>
                    </div>
                  </div>
                  {cori ? <StatusBadge score={cori.cori_score} /> : <span className="text-[10px] text-faint">Pending</span>}
                </div>
              </Link>
            )
          })}
        </div>
      )}

      {!loading && patients.length > 0 && (
        <div className="text-center text-[11px] text-faint mt-5">
          Showing {filtered.length} of {patients.length} patients
        </div>
      )}
    </Layout>
  )
}
