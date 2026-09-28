import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { IconFileReport, IconDownload, IconLoader2, IconChevronRight } from '@tabler/icons-react'
import Layout from '../components/Layout'
import StatusBadge from '../components/StatusBadge'
import EmptyState from '../components/EmptyState'
import { SkeletonRows } from '../components/Skeleton'
import { useToast } from '../context/ToastContext'
import * as endpoints from '../api/endpoints'
import { initials, errMsg, fmtNum, formatDate } from '../lib/format'

export default function Reports() {
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [downloadingId, setDownloadingId] = useState(null)
  const toast = useToast()

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const pRes = await endpoints.listPatients()
        const patients = pRes.data
        const entries = await Promise.all(
          patients.map(async (p) => {
            try {
              const cRes = await endpoints.listCoriRecords(p.id)
              const records = cRes.data
              return { patient: p, cori: records.length ? records[records.length - 1] : null }
            } catch {
              return { patient: p, cori: null }
            }
          }),
        )
        if (!cancelled) setRows(entries.filter((e) => e.cori))
      } catch (err) {
        if (!cancelled) toast.error(errMsg(err, 'Could not load reports.'))
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function handleDownload(row) {
    setDownloadingId(row.cori.id)
    try {
      await endpoints.generateReport(row.cori.id)
      const res = await endpoints.downloadReport(row.cori.id)
      const blobUrl = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
      const a = document.createElement('a')
      a.href = blobUrl
      a.download = `${row.patient.name.replace(/\s+/g, '_')}_recovery_report.pdf`
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(blobUrl)
    } catch (err) {
      toast.error(errMsg(err, 'Could not generate the report.'))
    } finally {
      setDownloadingId(null)
    }
  }

  return (
    <Layout>
      <div className="mb-6">
        <div className="label-eyebrow mb-1">Reports</div>
        <div className="font-display text-[24px] text-body font-semibold leading-tight">Recovery reports</div>
        <div className="text-[12.5px] text-muted mt-1">
          Every patient with at least one CORI assessment — generate and download a full explainable PDF report.
        </div>
      </div>

      {loading ? (
        <SkeletonRows count={6} />
      ) : rows.length === 0 ? (
        <div className="bg-card border border-border rounded-xl">
          <EmptyState
            icon={IconFileReport}
            title="No reports yet"
            sub="Once a patient has a structural and/or functional assessment, their CORI report will appear here."
            action={<Link to="/patients" className="btn-primary inline-flex">View patients <IconChevronRight size={13} /></Link>}
          />
        </div>
      ) : (
        <div className="bg-card border border-border rounded-xl overflow-hidden">
          <div className="hidden sm:grid grid-cols-[2fr_1fr_1fr_1fr_1fr_auto] gap-3 px-5 py-3 text-[10px] text-faint uppercase tracking-wide font-mono border-b border-border">
            <span>Patient</span><span>Structural</span><span>Functional</span><span>CORI</span><span>Last assessed</span><span />
          </div>
          <div className="divide-y divide-border">
            {rows.map(({ patient, cori }) => (
              <div key={patient.id} className="grid grid-cols-2 sm:grid-cols-[2fr_1fr_1fr_1fr_1fr_auto] items-center gap-3 px-4 sm:px-5 py-3.5">
                <Link to={`/patients/${patient.id}`} className="flex items-center gap-2.5 min-w-0 col-span-2 sm:col-span-1">
                  <div className="w-8 h-8 rounded-full bg-ink flex items-center justify-center text-[10.5px] text-gold font-mono font-semibold flex-shrink-0">
                    {initials(patient.name)}
                  </div>
                  <div className="min-w-0">
                    <div className="text-[12.5px] text-body font-medium truncate hover:underline">{patient.name}</div>
                    <div className="text-[10.5px] text-muted">{patient.bone_type}</div>
                  </div>
                </Link>
                <div className="text-[12px] font-mono font-semibold text-[#8C6B2E]">{fmtNum(cori.structural_score, 1, '%')}</div>
                <div className="text-[12px] font-mono font-semibold text-amethyst">
                  {cori.functional_score != null ? fmtNum(cori.functional_score, 1, '%') : '—'}
                </div>
                <div><StatusBadge score={cori.cori_score} /></div>
                <div className="text-[11px] text-muted">{formatDate(cori.created_at)}</div>
                <button
                  onClick={() => handleDownload({ patient, cori })}
                  disabled={downloadingId === cori.id}
                  className="btn-outline !px-3 !py-2 justify-self-end"
                >
                  {downloadingId === cori.id ? <IconLoader2 size={14} className="animate-spin" /> : <IconDownload size={14} />}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </Layout>
  )
}
