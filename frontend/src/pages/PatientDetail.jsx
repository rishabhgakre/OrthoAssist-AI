import { useCallback, useEffect, useRef, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  IconArrowLeft, IconBone, IconActivity, IconUpload, IconFileDownload, IconRefresh,
  IconAlertTriangle, IconSparkles, IconClock, IconFlag, IconLoader2, IconTimeline,
  IconSearch,
} from '@tabler/icons-react'
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RTooltip,
} from 'recharts'
import Layout from '../components/Layout'
import ScoreRing from '../components/ScoreRing'
import Dropzone from '../components/Dropzone'
import StatusBadge from '../components/StatusBadge'
import ProcessFlow from '../components/ProcessFlow'
import { Skeleton } from '../components/Skeleton'
import { useToast } from '../context/ToastContext'
import * as endpoints from '../api/endpoints'
import { assetUrl } from '../api/client'
import { isGaitRelevant } from '../lib/boneClassification'
import { fmtNum, formatDate, formatDateTime, errMsg, statusFromScore, STATUS_STYLES } from '../lib/format'

const XRAY_STEPS = [
  { icon: IconSearch, label: 'Detecting fracture region (YOLOv8)' },
  { icon: IconBone, label: 'Segmenting bone mask' },
  { icon: IconTimeline, label: 'Measuring gap, alignment & continuity' },
  { icon: IconSparkles, label: 'Calculating structural recovery score' },
]

const GAIT_STEPS = [
  { icon: IconActivity, label: 'Extracting pose landmarks (MediaPipe)' },
  { icon: IconRefresh, label: 'Detecting steps & gait cycle' },
  { icon: IconTimeline, label: 'Computing speed, cadence & symmetry' },
  { icon: IconSparkles, label: 'Calculating functional recovery score' },
]


function Metric({ label, value, className = '' }) {
  return (
    <div>
      <div className="text-[9.5px] text-faint uppercase tracking-wide mb-0.5">{label}</div>
      <div className={`text-[13.5px] font-mono font-semibold ${className}`}>{value}</div>
    </div>
  )
}

function SubScoreBar({ label, value }) {
  const status = statusFromScore(value)
  const styles = STATUS_STYLES[status]
  return (
    <div>
      <div className="flex items-center justify-between text-[11px] mb-1">
        <span className="text-muted">{label}</span>
        <span className="font-mono font-semibold text-body">{fmtNum(value, 1, '%')}</span>
      </div>
      <div className="h-1.5 rounded-full bg-card-alt overflow-hidden">
        <div className={`h-full rounded-full ${styles.bar}`} style={{ width: `${Math.max(2, Math.min(100, value ?? 0))}%` }} />
      </div>
    </div>
  )
}

function ImprovementPill({ value }) {
  if (value === null || value === undefined) return <span className="text-faint text-[11px]">—</span>
  const positive = value >= 0
  return (
    <span className={`text-[10.5px] font-mono font-semibold px-2 py-0.5 rounded-full ${positive ? 'bg-malachite-bg text-malachite' : 'bg-garnet-bg text-garnet'}`}>
      {positive ? '+' : ''}{fmtNum(value, 0)}%
    </span>
  )
}

function MeasurementRow({ label, pre, post, unit, improvement }) {
  return (
    <div className="grid grid-cols-[1fr_auto_auto_auto] sm:grid-cols-[1.2fr_1fr_auto_1fr_auto] items-center gap-2 sm:gap-3 py-2.5 border-b border-border last:border-0">
      <div className="text-[12px] text-body font-medium col-span-4 sm:col-span-1">{label}</div>
      <div className="text-[12px] font-mono text-muted text-right sm:text-left">{pre}{unit}</div>
      <div className="text-faint text-[11px] hidden sm:block">→</div>
      <div className="text-[12px] font-mono font-semibold text-body text-right sm:text-left">{post}{unit}</div>
      <div className="flex justify-end">
        <ImprovementPill value={improvement} />
      </div>
    </div>
  )
}

function HistoryList({ records, activeId, onSelect, scoreKey }) {
  if (!records.length) {
    return <div className="text-[11.5px] text-faint py-3">No assessments yet.</div>
  }
  return (
    <div className="space-y-1.5">
      {[...records].reverse().map((r) => (
        <button
          key={r.id}
          onClick={() => onSelect(r.id)}
          className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-left transition-colors ${
            activeId === r.id ? 'bg-ink text-page' : 'bg-card-alt hover:bg-border/60 text-body'
          }`}
        >
          <span className={`text-[11.5px] flex items-center gap-1.5 ${activeId === r.id ? 'text-[#B9C4B5]' : 'text-muted'}`}>
            <IconClock size={12} /> {formatDateTime(r.created_at)}
          </span>
          <span className={`text-[12px] font-mono font-semibold ${activeId === r.id ? 'text-gold-bright' : 'text-body'}`}>
            {fmtNum(r[scoreKey], 1, '%')}
          </span>
        </button>
      ))}
    </div>
  )
}

function TrendTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-ink border border-ink-line rounded-lg px-3 py-2.5 shadow-panel">
      <div className="text-[10px] text-[#8FA095] font-mono mb-1.5">{label}</div>
      <div className="space-y-1">
        {payload.map((p) => (
          <div key={p.dataKey} className="flex items-center gap-2 text-[11px]">
            <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: p.color }} />
            <span className="text-[#B9C4B5]">{p.name}</span>
            <span className="text-page font-mono font-semibold ml-auto">
              {p.value != null ? `${fmtNum(p.value, 1)}%` : '—'}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function PatientDetail() {
  const { id } = useParams()
  const toast = useToast()

  const [patient, setPatient] = useState(null)
  const [xrayRecords, setXrayRecords] = useState([])
  const [gaitRecords, setGaitRecords] = useState([])
  const [coriRecords, setCoriRecords] = useState([])
  const [coriExplain, setCoriExplain] = useState(null)
  const [loading, setLoading] = useState(true)

  const [activeXrayId, setActiveXrayId] = useState(null)
  const [activeGaitId, setActiveGaitId] = useState(null)

  const [preFile, setPreFile] = useState(null)
  const [postFile, setPostFile] = useState(null)
  const [xrayBusy, setXrayBusy] = useState(false)
  const [xrayStep, setXrayStep] = useState(-1)
  const xrayTimerRef = useRef(null)

  const [videoFile, setVideoFile] = useState(null)
  const [heightM, setHeightM] = useState('')
  const [gaitBusy, setGaitBusy] = useState(false)
  const [gaitStep, setGaitStep] = useState(-1)
  const gaitTimerRef = useRef(null)

  const [structuralWeightPct, setStructuralWeightPct] = useState(50)
  const [coriBusy, setCoriBusy] = useState(false)
  const [reportBusy, setReportBusy] = useState(false)

  const gaitApplies = patient ? isGaitRelevant(patient.bone_type) : true

  // Stop any running step-flow timers if the clinician navigates away
  // mid-analysis, so they don't keep ticking against an unmounted page.
  useEffect(() => () => {
    clearInterval(xrayTimerRef.current)
    clearInterval(gaitTimerRef.current)
  }, [])

  const loadAll = useCallback(async () => {
    const [pRes, xRes, gRes, cRes] = await Promise.all([
      endpoints.getPatient(id),
      endpoints.listXrayRecords(id),
      endpoints.listGaitRecords(id),
      endpoints.listCoriRecords(id),
    ])
    setPatient(pRes.data)
    setXrayRecords(xRes.data)
    setGaitRecords(gRes.data)
    setCoriRecords(cRes.data)
    if (xRes.data.length) setActiveXrayId((prev) => prev ?? xRes.data[xRes.data.length - 1].id)
    if (gRes.data.length) setActiveGaitId((prev) => prev ?? gRes.data[gRes.data.length - 1].id)

    if (cRes.data.length) {
      const latest = cRes.data[cRes.data.length - 1]
      setStructuralWeightPct(Math.round((latest.weight_structural ?? 0.5) * 100))
      try {
        const explainRes = await endpoints.explainCori(latest.id)
        setCoriExplain({ ...explainRes.data, id: explainRes.data.cori_id })
      } catch {
        setCoriExplain(null)
      }
    }
    return { xray: xRes.data, gait: gRes.data }
  }, [id])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    loadAll()
      .catch((err) => toast.error(errMsg(err, 'Could not load patient.')))
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  async function maybeAutoComputeCori(xrayList, gaitList) {
    if (!xrayList.length) return
    if (gaitApplies && !gaitList.length) return
    const latestXray = xrayList[xrayList.length - 1]
    const latestGait = gaitList.length ? gaitList[gaitList.length - 1] : null
    try {
      setCoriBusy(true)
      const payload = {
        patient_id: Number(id),
        xray_record_id: latestXray.id,
        weight_structural: structuralWeightPct / 100,
        weight_functional: 1 - structuralWeightPct / 100,
      }
      if (gaitApplies && latestGait) payload.gait_record_id = latestGait.id
      await endpoints.computeCori(payload)
      const cRes = await endpoints.listCoriRecords(id)
      setCoriRecords(cRes.data)
      const latest = cRes.data[cRes.data.length - 1]
      const explainRes = await endpoints.explainCori(latest.id)
      setCoriExplain({ ...explainRes.data, id: explainRes.data.cori_id })
    } catch {
      // Non-fatal — CORI can be computed manually from the card below.
    } finally {
      setCoriBusy(false)
    }
  }

  async function handleAnalyzeXray(e) {
    e.preventDefault()
    if (!preFile || !postFile) return
    setXrayBusy(true)
    setXrayStep(0)
    xrayTimerRef.current = setInterval(() => {
      // Advances every ~1.1s but holds on the last step — it never claims
      // "done" before the real API response actually arrives.
      setXrayStep((s) => (s < XRAY_STEPS.length - 1 ? s + 1 : s))
    }, 1100)
    try {
      const fd = new FormData()
      fd.append('patient_id', id)
      fd.append('pre_image', preFile)
      fd.append('post_image', postFile)
      await endpoints.analyzeXray(fd)
      clearInterval(xrayTimerRef.current)
      setXrayStep(XRAY_STEPS.length)
      await new Promise((r) => setTimeout(r, 450))
      toast.success('X-ray assessment complete.')
      setPreFile(null)
      setPostFile(null)
      const xRes = await endpoints.listXrayRecords(id)
      setXrayRecords(xRes.data)
      setActiveXrayId(xRes.data[xRes.data.length - 1].id)
      await maybeAutoComputeCori(xRes.data, gaitRecords)
    } catch (err) {
      clearInterval(xrayTimerRef.current)
      toast.error(errMsg(err, 'X-ray analysis failed.'))
    } finally {
      setXrayBusy(false)
      setXrayStep(-1)
    }
  }

  async function handleAnalyzeGait(e) {
    e.preventDefault()
    if (!videoFile) return
    setGaitBusy(true)
    setGaitStep(0)
    gaitTimerRef.current = setInterval(() => {
      // Video processing (frame-by-frame pose extraction) tends to run
      // longer than the X-ray pipeline, hence the slightly slower pace.
      setGaitStep((s) => (s < GAIT_STEPS.length - 1 ? s + 1 : s))
    }, 1400)
    try {
      const fd = new FormData()
      fd.append('patient_id', id)
      if (heightM) fd.append('patient_height_m', heightM)
      fd.append('video', videoFile)
      await endpoints.analyzeGait(fd)
      clearInterval(gaitTimerRef.current)
      setGaitStep(GAIT_STEPS.length)
      await new Promise((r) => setTimeout(r, 450))
      toast.success('Gait assessment complete.')
      setVideoFile(null)
      const gRes = await endpoints.listGaitRecords(id)
      setGaitRecords(gRes.data)
      setActiveGaitId(gRes.data[gRes.data.length - 1].id)
      await maybeAutoComputeCori(xrayRecords, gRes.data)
    } catch (err) {
      clearInterval(gaitTimerRef.current)
      toast.error(errMsg(err, 'Gait analysis failed.'))
    } finally {
      setGaitBusy(false)
      setGaitStep(-1)
    }
  }

  async function handleRecalculateCori() {
    if (!xrayRecords.length) return
    setCoriBusy(true)
    try {
      const latestXray = xrayRecords[xrayRecords.length - 1]
      const latestGait = gaitRecords.length ? gaitRecords[gaitRecords.length - 1] : null
      const payload = {
        patient_id: Number(id),
        xray_record_id: latestXray.id,
        weight_structural: structuralWeightPct / 100,
        weight_functional: 1 - structuralWeightPct / 100,
      }
      if (gaitApplies && latestGait) payload.gait_record_id = latestGait.id
      await endpoints.computeCori(payload)
      const cRes = await endpoints.listCoriRecords(id)
      setCoriRecords(cRes.data)
      const latest = cRes.data[cRes.data.length - 1]
      const explainRes = await endpoints.explainCori(latest.id)
      setCoriExplain({ ...explainRes.data, id: explainRes.data.cori_id })
      toast.success('CORI recalculated.')
    } catch (err) {
      toast.error(errMsg(err, 'Could not compute CORI yet.'))
    } finally {
      setCoriBusy(false)
    }
  }

  async function handleDownloadReport() {
    const latestCori = coriRecords[coriRecords.length - 1]
    if (!latestCori) return
    setReportBusy(true)
    try {
      await endpoints.generateReport(latestCori.id)
      const res = await endpoints.downloadReport(latestCori.id)
      const blobUrl = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
      const a = document.createElement('a')
      a.href = blobUrl
      a.download = `${patient.name.replace(/\s+/g, '_')}_recovery_report.pdf`
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(blobUrl)
      toast.success('Report downloaded.')
    } catch (err) {
      toast.error(errMsg(err, 'Could not generate the report.'))
    } finally {
      setReportBusy(false)
    }
  }

  if (loading) {
    return (
      <Layout>
        <Skeleton className="h-6 w-40 mb-2" />
        <Skeleton className="h-3 w-64 mb-6" />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <Skeleton className="h-96 rounded-xl" />
          <Skeleton className="h-96 rounded-xl" />
        </div>
      </Layout>
    )
  }

  if (!patient) {
    return (
      <Layout>
        <div className="text-center py-20 text-muted">Patient not found.</div>
      </Layout>
    )
  }

  const activeXray = xrayRecords.find((r) => r.id === activeXrayId) || xrayRecords[xrayRecords.length - 1]
  const activeGait = gaitRecords.find((r) => r.id === activeGaitId) || gaitRecords[gaitRecords.length - 1]
  const latestCori = coriRecords[coriRecords.length - 1]
  const gaitScores = activeGait?.raw_measurements || {}

  const trendData = coriRecords.map((r) => ({
    label: formatDate(r.created_at, { day: 'numeric', month: 'short' }),
    cori: r.cori_score,
    structural: r.structural_score,
    functional: r.functional_score,
  }))

  return (
    <Layout>
      <div className="flex items-start justify-between gap-3 mb-6">
        <div>
          <div className="label-eyebrow mb-1">
            Patient · {patient.bone_type} · Age {patient.age} · {patient.gender}
          </div>
          <div className="font-display text-[26px] text-body font-semibold leading-tight">{patient.name}</div>
          {patient.injury_notes && <div className="text-[12px] text-muted mt-1.5 max-w-xl">{patient.injury_notes}</div>}
        </div>
        <Link to="/patients" className="btn-outline flex-shrink-0">
          <IconArrowLeft size={14} /> <span className="hidden sm:inline">Back to patients</span>
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 items-start">
        {/* ============ STRUCTURAL ============ */}
        <div className="bg-card border border-border rounded-xl p-5 sm:p-6">
          <div className="flex items-center gap-2 mb-5">
            <div className="w-7 h-7 rounded-lg bg-gold-bg flex items-center justify-center text-[#8C6B2E]">
              <IconBone size={15} />
            </div>
            <div className="font-display text-[16px] font-semibold text-body">Structural recovery</div>
          </div>

          {activeXray ? (
            <>
              <div className="flex flex-col sm:flex-row items-center sm:items-start gap-5 mb-5">
                <ScoreRing value={activeXray.structural_recovery_score !== null ?activeXray.structural_recovery_score : null} color="#C9A66B" />
                <div className="flex-1 w-full grid grid-cols-3 gap-3">
                  <div>
                    <ImprovementPill value={activeXray.gap_improvement_pct} />
                    <div className="text-[10px] text-faint mt-1.5 leading-snug">Reduction in fracture gap</div>
                  </div>
                  <div>
                    <ImprovementPill value={activeXray.alignment_improvement_pct} />
                    <div className="text-[10px] text-faint mt-1.5 leading-snug">Bone axis alignment gain</div>
                  </div>
                  <div>
                    <ImprovementPill value={activeXray.continuity_improvement_pct} />
                    <div className="text-[10px] text-faint mt-1.5 leading-snug">Bone contour continuity gain</div>
                  </div>
                </div>
              </div>

              <div className="bg-card-alt rounded-lg px-3.5 mb-5">
                <div className="grid grid-cols-[1.2fr_1fr_auto_1fr_auto] gap-3 py-2 text-[9.5px] text-faint uppercase tracking-wide font-mono border-b border-border">
                  <span>Measurement</span><span>Pre-op</span><span /><span>Post-op</span><span className="text-right">Δ</span>
                </div>
                <MeasurementRow label="Fracture gap" pre={fmtNum(activeXray.pre_gap_mm, 2)} post={fmtNum(activeXray.post_gap_mm, 2)} unit=" mm" improvement={activeXray.gap_improvement_pct} />
                <MeasurementRow label="Alignment" pre={fmtNum(activeXray.pre_alignment_pct, 1)} post={fmtNum(activeXray.post_alignment_pct, 1)} unit="%" improvement={activeXray.alignment_improvement_pct} />
                <MeasurementRow label="Continuity" pre={fmtNum(activeXray.pre_continuity_pct, 1)} post={fmtNum(activeXray.post_continuity_pct, 1)} unit="%" improvement={activeXray.continuity_improvement_pct} />
                <MeasurementRow label="Bone axis angle" pre={fmtNum(activeXray.pre_bone_angle_deg, 1)} post={fmtNum(activeXray.post_bone_angle_deg, 1)} unit="°" improvement={null} />
                <MeasurementRow
                  label="Detection confidence"
                  pre={activeXray.pre_detection_confidence != null ? Math.round(activeXray.pre_detection_confidence * 100) : '—'}
                  post={activeXray.post_detection_confidence != null ? Math.round(activeXray.post_detection_confidence * 100) : '—'}
                  unit="%" improvement={null}
                />
              </div>

              <div className="grid grid-cols-2 gap-3 mb-5">
                <div className="rounded-lg overflow-hidden border border-border">
                  <div className="bg-gold-bg text-[#8C6B2E] text-[10px] font-mono font-bold uppercase tracking-wide px-2.5 py-1.5">Pre-operative X-ray</div>
                  <div className="w-full aspect-[4/3] bg-ink flex items-center justify-center overflow-hidden">
                    <img src={assetUrl(activeXray.pre_image_path)} alt="Pre-operative X-ray" className="w-full h-full object-contain" />
                  </div>
                </div>
                <div className="rounded-lg overflow-hidden border border-border">
                  <div className="bg-malachite-bg text-malachite text-[10px] font-mono font-bold uppercase tracking-wide px-2.5 py-1.5">Post-operative X-ray</div>
                  <div className="w-full aspect-[4/3] bg-ink flex items-center justify-center overflow-hidden">
                    <img src={assetUrl(activeXray.post_image_path)} alt="Post-operative X-ray" className="w-full h-full object-contain" />
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="text-center py-8 mb-5 bg-card-alt rounded-lg">
              <div className="text-[12.5px] text-muted">No X-ray assessment yet — upload one below to begin.</div>
            </div>
          )}

          <div className="border-t border-border pt-5">
            <div className="text-[12.5px] font-semibold text-body mb-3">New X-ray assessment</div>
            <form onSubmit={handleAnalyzeXray} className="grid grid-cols-2 gap-3 mb-3">
              <Dropzone label="Pre-operative X-ray" sublabel="Before treatment" tag="Pre" tagTone="gold" file={preFile} onChange={setPreFile} />
              <Dropzone label="Post-operative X-ray" sublabel="After treatment / follow-up" tag="Post" tagTone="gold" file={postFile} onChange={setPostFile} />
              <button type="submit" disabled={!preFile || !postFile || xrayBusy} className="btn-gold col-span-2">
                {xrayBusy ? (<><IconLoader2 size={14} className="animate-spin" /> Analyzing X-rays…</>) : (<><IconUpload size={14} /> Analyze X-rays</>)}
              </button>
            </form>
            {xrayBusy && (
              <div className="mb-3">
                <ProcessFlow steps={XRAY_STEPS} activeIndex={xrayStep} accent="gold" />
              </div>
            )}

            <div className="text-[10.5px] text-faint uppercase tracking-wide font-mono mt-4 mb-2">Assessment history</div>
            <HistoryList records={xrayRecords} activeId={activeXray?.id} onSelect={setActiveXrayId} scoreKey="structural_recovery_score" />
          </div>
        </div>

        {/* ============ FUNCTIONAL ============ */}
        <div className="bg-card border border-border rounded-xl p-5 sm:p-6">
          <div className="flex items-center gap-2 mb-5">
            <div className="w-7 h-7 rounded-lg bg-amethyst-bg flex items-center justify-center text-amethyst">
              <IconActivity size={15} />
            </div>
            <div className="font-display text-[16px] font-semibold text-body">Functional recovery</div>
          </div>

          {!gaitApplies ? (
            <div className="text-center py-10 mb-2 bg-card-alt rounded-lg px-4">
              <IconAlertTriangle size={20} className="text-topaz mx-auto mb-2" />
              <div className="text-[12.5px] text-body font-medium mb-1">Structural-only tracking</div>
              <div className="text-[11.5px] text-muted max-w-[260px] mx-auto leading-relaxed">
                Gait analysis isn't clinically meaningful for a {patient.bone_type.toLowerCase()} injury,
                since walking gait has no bearing on upper-limb recovery.
              </div>
            </div>
          ) : (
            <>
              {activeGait ? (
                <>
                  <div className="flex flex-col sm:flex-row items-center sm:items-start gap-5 mb-5">
                    <ScoreRing value={activeGait.functional_recovery_score !== null ? activeGait.functional_recovery_score : null} color="#6B4C9A" />
                    <div className="flex-1 w-full grid grid-cols-2 gap-x-4 gap-y-3">
                      <SubScoreBar label="Walking speed" value={gaitScores.walking_speed_score} />
                      <SubScoreBar label="Cadence" value={gaitScores.cadence_score} />
                      <SubScoreBar label="Step symmetry" value={gaitScores.symmetry_score} />
                      <SubScoreBar label="Balance" value={gaitScores.balance_score} />
                      <SubScoreBar label="Knee flexion" value={gaitScores.knee_flexion_score} />
                    </div>
                  </div>

                  <div className="bg-card-alt rounded-lg px-3.5 py-3.5 mb-5 grid grid-cols-2 sm:grid-cols-3 gap-y-3.5 gap-x-2">
                    <Metric label="Walking speed" value={`${fmtNum(activeGait.walking_speed, 2)} m/s`} />
                    <Metric label="Cadence" value={`${fmtNum(activeGait.cadence, 1)} steps/min`} />
                    <Metric label="Stride length" value={`${fmtNum(activeGait.stride_length, 2)} m`} />
                    <Metric label="Step length" value={`${fmtNum(activeGait.step_length, 2)} m`} />
                    <Metric label="Step symmetry" value={fmtNum(activeGait.step_symmetry, 1, '%')} />
                    <Metric label="Knee flexion" value={`${fmtNum(activeGait.knee_flexion, 1)}°`} />
                    <Metric label="Hip movement" value={`${fmtNum(activeGait.hip_movement, 1)}°`} />
                    <Metric label="Balance" value={fmtNum(activeGait.balance_score, 1, '%')} />
                    {gaitScores.frames_processed != null && <Metric label="Frames processed" value={gaitScores.frames_processed} />}
                  </div>
                </>
              ) : (
                <div className="text-center py-8 mb-5 bg-card-alt rounded-lg">
                  <div className="text-[12.5px] text-muted">No gait assessment yet — upload a walking video below.</div>
                </div>
              )}

              <div className="border-t border-border pt-5">
                <div className="text-[12.5px] font-semibold text-body mb-3">New gait assessment</div>
                <form onSubmit={handleAnalyzeGait} className="space-y-3 mb-3">
                  <Dropzone label="Walking video" sublabel="Short clip, side view preferred" tag="Video" tagTone="amethyst" accept="video/*" kind="video" file={videoFile} onChange={setVideoFile} />
                  <div>
                    <label className="field-label">Patient height (optional, meters — improves speed accuracy)</label>
                    <input
                      type="number" step="0.01" min="0.5" max="2.5"
                      value={heightM} onChange={(e) => setHeightM(e.target.value)}
                      placeholder="e.g. 1.75" className="input-base"
                    />
                  </div>
                  <button type="submit" disabled={!videoFile || gaitBusy} className="btn-amethyst w-full">
                    {gaitBusy ? (<><IconLoader2 size={14} className="animate-spin" /> Analyzing gait…</>) : (<><IconUpload size={14} /> Analyze gait</>)}
                  </button>
                </form>
                {gaitBusy && (
                  <div className="mb-3">
                    <ProcessFlow steps={GAIT_STEPS} activeIndex={gaitStep} accent="amethyst" />
                  </div>
                )}

                <div className="text-[10.5px] text-faint uppercase tracking-wide font-mono mt-4 mb-2">Assessment history</div>
                <HistoryList records={gaitRecords} activeId={activeGait?.id} onSelect={setActiveGaitId} scoreKey="functional_recovery_score" />
              </div>
            </>
          )}
        </div>
      </div>

      {/* ============ RECOVERY TREND ============ */}
      {coriRecords.length > 0 && (
        <div className="mt-5 bg-card border border-border rounded-xl p-5 sm:p-6">
          <div className="flex items-center justify-between mb-1">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-card-alt flex items-center justify-center text-body">
                <IconTimeline size={15} />
              </div>
              <div className="font-display text-[16px] font-semibold text-body">Recovery trend</div>
            </div>
            <div className="flex items-center gap-3.5 text-[10.5px]">
              <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-[#1C231F]" /> CORI</span>
              <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-[#8C6B2E]" /> Structural</span>
              {gaitApplies && (
                <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-amethyst" /> Functional</span>
              )}
            </div>
          </div>
          <div className="text-[11.5px] text-muted mb-4">
            {coriRecords.length} assessment{coriRecords.length === 1 ? '' : 's'} recorded
            {coriRecords.length === 1 ? ' — trend builds as more assessments are added.' : ''}
          </div>
          <div style={{ width: '100%', height: 220 }}>
            <ResponsiveContainer>
              <LineChart data={trendData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                <CartesianGrid stroke="#E2DED2" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="label" tick={{ fontSize: 10.5, fill: '#8A8478' }} axisLine={{ stroke: '#E2DED2' }} tickLine={false} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 10.5, fill: '#8A8478' }} axisLine={false} tickLine={false} width={32} />
                <RTooltip content={<TrendTooltip />} />
                <Line type="monotone" dataKey="cori" name="CORI" stroke="#1C231F" strokeWidth={2.25} dot={{ r: 3.5 }} activeDot={{ r: 5 }} connectNulls />
                <Line type="monotone" dataKey="structural" name="Structural" stroke="#8C6B2E" strokeWidth={2} dot={{ r: 3 }} activeDot={{ r: 5 }} connectNulls />
                {gaitApplies && (
                  <Line type="monotone" dataKey="functional" name="Functional" stroke="#6B4C9A" strokeWidth={2} dot={{ r: 3 }} activeDot={{ r: 5 }} connectNulls />
                )}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* ============ CORI ============ */}
      <div className="mt-5 bg-ink rounded-xl p-5 sm:p-7 text-page">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <div className="label-eyebrow mb-1 !text-[#6E7D74]">Composite Orthopedic Recovery Index</div>
            <div className="font-display text-[18px] font-semibold">Overall recovery — CORI</div>
          </div>
          {latestCori && (
            <button onClick={handleDownloadReport} disabled={reportBusy} className="btn-gold">
              {reportBusy ? (<><IconLoader2 size={14} className="animate-spin" /> Preparing…</>) : (<><IconFileDownload size={14} /> Download report</>)}
            </button>
          )}
        </div>

        {!xrayRecords.length || (gaitApplies && !gaitRecords.length) ? (
          <div className="flex items-center gap-3 bg-ink-raised rounded-lg px-4 py-4 text-[12.5px] text-[#B9C4B5]">
            <IconAlertTriangle size={16} className="text-topaz-bright flex-shrink-0" />
            {!xrayRecords.length && !gaitRecords.length && gaitApplies
              ? 'Upload an X-ray assessment and a gait assessment to compute CORI.'
              : !xrayRecords.length
                ? 'Upload an X-ray assessment to compute CORI.'
                : 'Upload a gait assessment to compute CORI.'}
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-[auto_1fr] gap-7 items-start">
            <div className="flex flex-col items-center">
              <ScoreRing
                value={latestCori ? latestCori.cori_score: null}
                size={132} strokeWidth={11} onDark
                color={
                  !latestCori ? '#C9A66B'
                  : statusFromScore(latestCori.cori_score) === 'malachite' ? '#3FAF8A'
                  : statusFromScore(latestCori.cori_score) === 'topaz' ? '#D9A857' : '#C85E6E'
                }
              />
              {latestCori && (
                <div className="mt-3">
                  <StatusBadge score={latestCori.cori_score} />
                </div>
              )}
            </div>

            <div>
              {coriExplain?.summary && (
                <p className="text-[13px] text-[#D7DED2] leading-relaxed mb-4">{coriExplain.summary}</p>
              )}

              <div className="grid grid-cols-2 gap-3 mb-5">
                <div className="bg-ink-raised rounded-lg px-3.5 py-3">
                  <div className="text-[9.5px] text-[#6E7D74] uppercase tracking-wide font-mono mb-1">Structural</div>
                  <div className="text-[15px] font-mono font-semibold text-gold-bright">{fmtNum(latestCori?.structural_score, 1, '%')}</div>
                  <div className="text-[10px] text-[#6E7D74] mt-0.5">weight {Math.round((latestCori?.weight_structural ?? 0) * 100)}%</div>
                </div>
                <div className="bg-ink-raised rounded-lg px-3.5 py-3">
                  <div className="text-[9.5px] text-[#6E7D74] uppercase tracking-wide font-mono mb-1">Functional</div>
                  <div className="text-[15px] font-mono font-semibold text-amethyst-bright">
                    {latestCori?.functional_score != null ? fmtNum(latestCori.functional_score, 1, '%') : 'N/A'}
                  </div>
                  <div className="text-[10px] text-[#6E7D74] mt-0.5">weight {Math.round((latestCori?.weight_functional ?? 0) * 100)}%</div>
                </div>
              </div>

              {coriExplain?.recommendation && (
                <div className="flex items-start gap-2.5 bg-gold/10 border border-gold/25 rounded-lg px-3.5 py-3 mb-4">
                  <IconSparkles size={14} className="text-gold-bright flex-shrink-0 mt-0.5" />
                  <div className="text-[12px] text-[#EFE7D2] leading-relaxed">
                    <span className="font-semibold text-gold-bright">Recommendation — </span>
                    {coriExplain.recommendation}
                  </div>
                </div>
              )}

              {coriExplain?.flags?.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-5">
                  {coriExplain.flags.map((f, i) => (
                    <span key={i} className="flex items-center gap-1 text-[10.5px] bg-garnet-bright/15 text-garnet-bright px-2.5 py-1 rounded-full">
                      <IconFlag size={10} /> {f}
                    </span>
                  ))}
                </div>
              )}

              {gaitApplies && gaitRecords.length > 0 && (
                <div className="border-t border-ink-line pt-4">
                  <div className="flex items-center justify-between text-[11px] text-[#8FA095] mb-2">
                    <span>Structural weight</span>
                    <span className="font-mono">{structuralWeightPct}% / {100 - structuralWeightPct}%</span>
                  </div>
                  <input
                    type="range" min="0" max="100" value={structuralWeightPct}
                    onChange={(e) => setStructuralWeightPct(Number(e.target.value))}
                    className="w-full accent-gold h-1.5"
                  />
                  <button onClick={handleRecalculateCori} disabled={coriBusy} className="btn-outline-gold mt-3 !border-gold/40 !text-gold-bright hover:!bg-gold/10">
                    {coriBusy ? (<><IconLoader2 size={13} className="animate-spin" /> Recalculating…</>) : (<><IconRefresh size={13} /> Recalculate CORI</>)}
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </Layout>
  )
}
