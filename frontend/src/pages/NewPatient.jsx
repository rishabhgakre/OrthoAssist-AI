import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import {
  IconArrowLeft, IconBone, IconActivity, IconTimeline, IconAlertTriangle, IconCircleCheck,
} from '@tabler/icons-react'
import Layout from '../components/Layout'
import { useToast } from '../context/ToastContext'
import * as endpoints from '../api/endpoints'
import { BONE_TYPE_GROUPS, isGaitRelevant } from '../lib/boneClassification'
import { errMsg } from '../lib/format'

const STEPS = [
  {
    icon: IconBone,
    title: 'Upload X-rays',
    body: 'A pre-operative and a post-operative/follow-up X-ray are compared to produce a structural recovery score.',
  },
  {
    icon: IconActivity,
    title: 'Upload a walking video',
    body: 'For lower-limb injuries, a short walking clip is analyzed for gait quality and a functional recovery score.',
  },
  {
    icon: IconTimeline,
    title: 'Track over time',
    body: "Every assessment is saved to the patient's timeline so recovery can be tracked visit over visit.",
  },
]

export default function NewPatient() {
  const [form, setForm] = useState({ name: '', age: '', gender: 'Male', bone_type: 'Tibia', injury_notes: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const toast = useToast()

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }))
  }

  const gaitApplies = isGaitRelevant(form.bone_type)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await endpoints.createPatient({ ...form, age: Number(form.age) })
      toast.success(`${form.name} was added.`)
      navigate(`/patients/${res.data.id}`)
    } catch (err) {
      setError(errMsg(err, 'Could not create patient.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Layout>
      <div className="flex items-center justify-between mb-6 gap-3">
        <div>
          <div className="label-eyebrow mb-1">Patients</div>
          <div className="font-display text-[24px] text-body font-semibold leading-tight">New patient</div>
          <div className="text-[12.5px] text-muted mt-1">Create a patient record to begin structural and functional recovery tracking.</div>
        </div>
        <Link to="/patients" className="btn-outline flex-shrink-0 hidden sm:flex">
          <IconArrowLeft size={14} /> Back to patients
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-5 items-start">
        <form onSubmit={handleSubmit} className="bg-card border border-border rounded-xl p-5 sm:p-6 space-y-4.5">
          <div>
            <label className="field-label">Full name</label>
            <input
              required
              value={form.name}
              onChange={(e) => update('name', e.target.value)}
              placeholder="Patient's full name"
              className="input-base"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="field-label relative top-1">Age</label>
              <input
                required type="number" min="0" max="130"
                value={form.age}
                onChange={(e) => update('age', e.target.value)}
                placeholder="e.g. 28"
                className="input-base focus:outline-none focus:ring-0"
              />
            </div>
            <div>
              <label className="field-label relative top-1">Gender</label>
              <select value={form.gender} onChange={(e) => update('gender', e.target.value)} className="input-base">
                <option>Male</option>
                <option>Female</option>
                <option>Other</option>
              </select>
            </div>
          </div>

          <div>
            <label className="field-label">Bone type</label>
            <div className="space-y-2.5">
              {BONE_TYPE_GROUPS.map((group) => (
                <div key={group.label}>
                  <div className="text-[10px] text-faint uppercase tracking-wide mb-1.5">{group.label}</div>
                  <div className="flex flex-wrap gap-1.5">
                    {group.types.map((b) => (
                      <button
                        type="button"
                        key={b}
                        onClick={() => update('bone_type', b)}
                        className={`text-[12px] font-medium px-3 py-1.5 rounded-full border transition-colors ${
                          form.bone_type === b
                            ? 'bg-ink text-gold-bright border-ink'
                            : 'bg-card text-muted border-border hover:border-border-strong'
                        }`}
                      >
                        {b}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
            <div
              className={`flex items-center gap-2 mt-3 text-[11.5px] px-3 py-2 rounded-lg ${
                gaitApplies ? 'bg-amethyst-bg text-amethyst' : 'bg-card-alt text-muted'
              }`}
            >
              {gaitApplies ? <IconCircleCheck size={14} className="flex-shrink-0" /> : <IconAlertTriangle size={14} className="flex-shrink-0" />}
              {gaitApplies
                ? 'Gait assessment available — CORI will combine structural + functional recovery.'
                : 'Upper-limb injury — CORI will use structural recovery only (no gait assessment).'}
            </div>
          </div>

          <div>
            <label className="field-label">Injury notes (optional)</label>
            <textarea
              value={form.injury_notes}
              onChange={(e) => update('injury_notes', e.target.value)}
              rows={3}
              placeholder="Mechanism of injury, surgical fixation used, relevant history…"
              className="input-base resize-none"
            />
          </div>

          {error && (
            <div className="text-[12px] text-garnet bg-garnet-bg rounded-lg px-3.5 py-2.5">{error}</div>
          )}

          <div className="flex items-center gap-3 pt-1">
            <button type="submit" disabled={loading} className="btn-gold">
              {loading ? 'Creating…' : 'Create patient'}
            </button>
            <Link to="/patients" className="btn-outline">Cancel</Link>
          </div>
        </form>

        <div className="bg-ink rounded-xl p-5 sm:p-6 text-page">
          <div className="font-display text-[15px] font-semibold mb-4">What happens next</div>
          <div className="space-y-4">
            {STEPS.map(({ icon: Icon, title, body }, i) => (
              <div key={title} className="flex gap-3">
                <div className="w-7 h-7 rounded-full bg-ink-raised flex items-center justify-center flex-shrink-0 text-gold">
                  <Icon size={14} />
                </div>
                <div>
                  <div className="text-[12.5px] font-semibold text-page mb-0.5">{title}</div>
                  <div className="text-[11.5px] text-[#8FA095] leading-relaxed">{body}</div>
                </div>
              </div>
            ))}
          </div>
          <div
            className={`mt-5 pt-4 border-t border-ink-line text-[11.5px] px-3 py-2.5 rounded-lg ${
              gaitApplies ? 'bg-malachite/15 text-malachite-bright' : 'bg-topaz/15 text-topaz-bright'
            }`}
          >
            {gaitApplies ? 'Gait assessment available for this bone type.' : 'Structural-only tracking for this bone type.'}
          </div>
        </div>
      </div>
    </Layout>
  )
}
