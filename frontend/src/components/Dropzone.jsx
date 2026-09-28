import { useRef, useState } from 'react'
import { IconUpload, IconCircleCheck, IconPlayerPlay } from '@tabler/icons-react'

/**
 * A single labeled file dropzone. Shows a small image/video preview once a
 * file is chosen so the clinician can visually confirm the right upload
 * went into the right slot (pre vs post, etc) before analyzing.
 */
export default function Dropzone({
  label, sublabel, tag, tagTone = 'gold', accept = 'image/*', file, onChange, kind = 'image',
}) {
  const inputRef = useRef(null)
  const [dragOver, setDragOver] = useState(false)

  const previewUrl = file ? URL.createObjectURL(file) : null

  function handleFiles(files) {
    if (files && files[0]) onChange(files[0])
  }

  const toneClasses = {
    gold: 'bg-gold-bg text-[#8C6B2E]',
    amethyst: 'bg-amethyst-bg text-amethyst',
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-[11.5px] font-semibold text-body">{label}</span>
        {tag && <span className={`text-[9.5px] font-mono uppercase tracking-wide px-2 py-0.5 rounded-full font-bold ${toneClasses[tagTone]}`}>{tag}</span>}
      </div>
      <div
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFiles(e.dataTransfer.files) }}
        className={`relative rounded-lg cursor-pointer transition-all overflow-hidden
          ${file ? 'border-solid border-malachite bg-malachite-bg/40' : 'border-dashed border-border-strong bg-card-alt hover:border-gold-dim'}
          ${dragOver ? 'border-gold bg-gold-bg' : ''}`}
        style={{ borderWidth: '1.5px', minHeight: 108 }}
      >
        <input
          ref={inputRef} type="file" accept={accept} className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
        {file ? (
          <div className="flex items-center gap-3 p-3">
            <div className="w-16 h-16 rounded-md overflow-hidden bg-ink flex-shrink-0 flex items-center justify-center">
              {kind === 'image' ? (
                <img src={previewUrl} alt="" className="w-full h-full object-cover" />
              ) : (
                <IconPlayerPlay size={20} className="text-gold" />
              )}
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-1.5 text-[11.5px] font-medium text-malachite">
                <IconCircleCheck size={13} /> Ready
              </div>
              <div className="text-[11px] text-muted truncate max-w-[160px] mt-0.5">{file.name}</div>
              <div className="text-[10px] text-faint mt-0.5">Click to replace</div>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center text-center py-5 px-3">
            <div className="w-8 h-8 rounded-full bg-white border border-border flex items-center justify-center mb-2 text-muted">
              <IconUpload size={14} />
            </div>
            <div className="text-[11.5px] font-medium text-body">Click or drop a file</div>
            {sublabel && <div className="text-[10px] text-faint mt-1">{sublabel}</div>}
          </div>
        )}
      </div>
    </div>
  )
}
