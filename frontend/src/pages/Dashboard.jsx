import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  IconPlus, IconUsers, IconBone, IconActivity, IconAlertTriangle, IconChevronRight,
  IconCircleCheck,
} from '@tabler/icons-react'
import Layout from '../components/Layout'
import StatCard from '../components/StatCard'
import StatusBadge from '../components/StatusBadge'
import EmptyState from '../components/EmptyState'
import { SkeletonStatCards, SkeletonRows } from '../components/Skeleton'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import * as endpoints from '../api/endpoints'
import { initials, errMsg, fmtNum } from '../lib/format'

export default function Dashboard() {
  const [patients, setPatients] = useState([])
  const [coriByPatient, setCoriByPatient] = useState({})
  const [loading, setLoading] = useState(true)
  const { doctor } = useAuth()
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
        if (!cancelled) toast.error(errMsg(err, 'Could not load dashboard data.'))
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const withScores = patients
    .map((p) => ({ ...p, cori: coriByPatient[p.id] }))
    .filter((p) => p.cori)

  const avgStructural = withScores.filter((p) => p.cori.structural_score != null)
  const avgFunctional = withScores.filter((p) => p.cori.functional_score != null)

  const structuralAvg = avgStructural.length
    ? avgStructural.reduce((s, p) => s + p.cori.structural_score, 0) / avgStructural.length
    : null
  const functionalAvg = avgFunctional.length
    ? avgFunctional.reduce((s, p) => s + p.cori.functional_score, 0) / avgFunctional.length
    : null

  const needsAttention = withScores
    .filter((p) => p.cori.cori_score < 50)
    .sort((a, b) => a.cori.cori_score - b.cori.cori_score)

  const recentPatients = [...patients].reverse().slice(0, 6)

  const firstName = doctor?.name ? doctor.name.split(' ')[0].replace(/^Dr\.?\s*/i, '') : ''
  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening'

  return (
    <Layout>
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-6">
        <div>
          <div className="label-eyebrow mb-1">
            {new Date().toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
          </div>
          <div className="font-display text-[24px] text-body font-semibold leading-tight">
            {greeting}{firstName ? `, Dr. ${firstName}` : ''}
          </div>
          <div className="text-[12.5px] text-muted mt-1">Here's how your patients are recovering.</div>
        </div>
        <Link to="/patients/new" className="btn-gold self-start sm:self-auto">
          <IconPlus size={14} /> New patient
        </Link>
      </div>

      {loading ? (
        <>
          <SkeletonStatCards />
          <div className="mt-6"><SkeletonRows count={5} /></div>
        </>
      ) : (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
            <StatCard label="Active Patients" value={patients.length} icon={IconUsers} />
            <StatCard
              label="Avg. Structural Recovery"
              value={structuralAvg !== null ? `${fmtNum(structuralAvg, 1)}%` : '—'}
              icon={IconBone}
              valueClassName="text-[#8C6B2E]"
            />
            <StatCard
              label="Avg. Functional Recovery"
              value={functionalAvg !== null ? `${fmtNum(functionalAvg, 1)}%` : '—'}
              icon={IconActivity}
              valueClassName="text-amethyst"
            />
            <StatCard
              label="Needs Attention"
              value={needsAttention.length}
              icon={IconAlertTriangle}
              valueClassName={needsAttention.length > 0 ? 'text-garnet' : 'text-body'}
              sub="CORI below 50%"
            />
          </div>

          <div className="bg-card border border-border rounded-xl overflow-hidden mb-5">
            <div className={`flex items-center justify-between px-4 sm:px-5 py-3.5 border-b border-border ${needsAttention.length > 0 ? 'bg-garnet-bg/40' : ''}`}>
              <div className="flex items-center gap-2">
                <IconAlertTriangle size={15} className={needsAttention.length > 0 ? 'text-garnet' : 'text-muted'} />
                <div className="font-display text-[15px] font-semibold text-body">Needs attention</div>
                {needsAttention.length > 0 && (
                  <span className="text-[10.5px] font-mono font-bold bg-garnet text-white px-2 py-0.5 rounded-full">
                    {needsAttention.length}
                  </span>
                )}
              </div>
              <span className="text-[10.5px] text-muted font-mono">CORI below 50%</span>
            </div>

            {needsAttention.length === 0 ? (
              <div className="flex items-center gap-3 px-4 sm:px-5 py-5">
                <div className="w-8 h-8 rounded-full bg-malachite-bg flex items-center justify-center text-malachite flex-shrink-0">
                  <IconCircleCheck size={16} />
                </div>
                <div className="text-[12.5px] text-muted">
                  No patients currently below 50% CORI — everyone under your care is trending at or above moderate recovery.
                </div>
              </div>
            ) : (
              <div className="divide-y divide-border">
                {needsAttention.slice(0, 5).map(({ cori, ...p }) => {
                  const struct = cori.structural_score
                  const func = cori.functional_score
                  let reason = 'Composite recovery below target'
                  if (func == null && struct != null) reason = 'Structural recovery below target'
                  else if (struct != null && func != null) {
                    if (struct - func >= 20) reason = 'Functional recovery lagging behind structural'
                    else if (func - struct >= 20) reason = 'Structural recovery lagging behind functional'
                  }
                  return (
                    <Link
                      to={`/patients/${p.id}`}
                      key={p.id}
                      className="flex items-center justify-between gap-3 px-4 sm:px-5 py-3.5 hover:bg-garnet-bg/20 transition-colors"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <div className="w-9 h-9 rounded-full bg-garnet-bg flex items-center justify-center text-[11px] text-garnet font-mono font-semibold flex-shrink-0">
                          {initials(p.name)}
                        </div>
                        <div className="min-w-0">
                          <div className="text-[13px] text-body font-medium truncate">{p.name}</div>
                          <div className="text-[11px] text-muted truncate">{reason}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-4 flex-shrink-0">
                        <div className="text-right">
                          <div className="text-[9.5px] text-faint uppercase tracking-wide">CORI</div>
                          <div className="text-[13px] font-mono font-bold text-garnet">{fmtNum(cori.cori_score, 1)}%</div>
                        </div>
                        <span className="btn-outline !border-garnet/30 !text-garnet !py-1.5 !px-3 !text-[11px] hidden sm:flex">
                          Review <IconChevronRight size={12} />
                        </span>
                      </div>
                    </Link>
                  )
                })}
                {needsAttention.length > 5 && (
                  <div className="text-center py-2.5 text-[11px] text-muted">
                    +{needsAttention.length - 5} more patient{needsAttention.length - 5 === 1 ? '' : 's'} need review
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="bg-card border border-border rounded-xl overflow-hidden">
            <div className="flex items-center justify-between px-4 sm:px-5 py-3.5 border-b border-border">
              <div className="font-display text-[15px] font-semibold text-body">Recent patients</div>
              <Link to="/patients" className="text-[11.5px] font-semibold text-[#8C6B2E] hover:underline flex items-center gap-0.5">
                View all <IconChevronRight size={13} />
              </Link>
            </div>

            {patients.length === 0 ? (
              <EmptyState
                icon={IconUsers}
                title="No patients yet"
                sub="Add your first patient to start tracking structural and functional recovery."
                action={
                  <Link to="/patients/new" className="btn-primary inline-flex">
                    <IconPlus size={13} /> Add patient
                  </Link>
                }
              />
            ) : (
              <div className="divide-y divide-border">
                {recentPatients.map((p) => {
                  const cori = coriByPatient[p.id]
                  return (
                    <Link
                      to={`/patients/${p.id}`}
                      key={p.id}
                      className="flex items-center justify-between gap-3 px-4 sm:px-5 py-3.5 hover:bg-card-alt/60 transition-colors"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <div className="w-9 h-9 rounded-full bg-ink flex items-center justify-center text-[11px] text-gold font-mono font-semibold flex-shrink-0">
                          {initials(p.name)}
                        </div>
                        <div className="min-w-0">
                          <div className="text-[13px] text-body font-medium truncate">{p.name}</div>
                          <div className="text-[11px] text-muted">{p.bone_type} · Age {p.age}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-4 sm:gap-6 flex-shrink-0">
                        <div className="hidden sm:block text-right">
                          <div className="text-[9.5px] text-faint uppercase tracking-wide">Structural</div>
                          <div className="text-[12.5px] font-mono font-medium text-[#8C6B2E]">
                            {cori?.structural_score != null ? `${fmtNum(cori.structural_score, 1)}%` : '—'}
                          </div>
                        </div>
                        <div className="hidden sm:block text-right">
                          <div className="text-[9.5px] text-faint uppercase tracking-wide">Functional</div>
                          <div className="text-[12.5px] font-mono font-medium text-amethyst">
                            {cori?.functional_score != null ? `${fmtNum(cori.functional_score, 1)}%` : '—'}
                          </div>
                        </div>
                        {cori ? <StatusBadge score={cori.cori_score} /> : (
                          <span className="text-[10.5px] text-faint">No assessment</span>
                        )}
                        <IconChevronRight size={15} className="text-faint hidden sm:block" />
                      </div>
                    </Link>
                  )
                })}
              </div>
            )}
          </div>
        </>
      )}
    </Layout>
  )
}
