'use client'

import dynamic from 'next/dynamic'
import { useState } from 'react'
import { Box, Grid3X3, Loader2, Maximize2, MousePointer2, RotateCw, ScanLine } from 'lucide-react'
import type { Representation } from './scene'

const Scene = dynamic(() => import('./scene'), {
  ssr: false,
  loading: () => (
    <div className="three-loading">
      <Loader2 size={18} />
      <span>Three.jsを初期化中…</span>
    </div>
  ),
})

type ViewportProps = {
  paneIndex: number
  compact?: boolean
  onObjectSelect?: (name: string, additive?: boolean) => void
}

export function Viewport({ paneIndex, compact = false, onObjectSelect }: ViewportProps) {
  const [representation, setRepresentation] = useState<Representation>('surface-edges')
  const [rotate, setRotate] = useState(false)
  const [resetKey, setResetKey] = useState(0)
  const [selection, setSelection] = useState('選択なし')

  return (
    <div className={`three-viewport ${compact ? 'compact' : ''}`}>
      <Scene
        key={resetKey}
        representation={representation}
        rotate={rotate}
        onSelect={(name, additive) => {
          setSelection(name)
          onObjectSelect?.(name, additive)
        }}
      />

      {/* One mock label per pane. The pane carried two - this badge and a separate status footer that
          repeated it - and 11_ui.md asks for neither the footer nor the repetition: the in-viewport
          mock label is sufficient. The clicked part's identity belongs here because clicking a part
          identifies only the mock part. */}
      <div className="viewport-badges" aria-label="ビュー情報">
        <span>ペイン {paneIndex + 1}</span>
        <span className="viewport-badge-secondary">Three.js仮形状・解析値なし</span>
        <span className="viewport-badge-selection"><MousePointer2 size={10} /> {selection}</span>
      </div>

      <div className="viewport-rail viewport-rail-left" aria-label="カメラ操作">
        <ViewportButton
          label="全体表示"
          onClick={() => setResetKey((value) => value + 1)}
          icon={<Maximize2 size={14} />}
        />
        <ViewportButton
          label={rotate ? '自動回転を停止' : '自動回転'}
          active={rotate}
          onClick={() => setRotate((value) => !value)}
          icon={<RotateCw size={14} />}
        />
      </div>

      <div className="viewport-rail viewport-rail-right" aria-label="表示方式">
        <ViewportButton
          label="サーフェス"
          active={representation === 'surface'}
          onClick={() => setRepresentation('surface')}
          icon={<Box size={14} />}
        />
        <ViewportButton
          label="サーフェスとエッジ"
          active={representation === 'surface-edges'}
          onClick={() => setRepresentation('surface-edges')}
          icon={<ScanLine size={14} />}
        />
        <ViewportButton
          label="ワイヤーフレーム"
          active={representation === 'wireframe'}
          onClick={() => setRepresentation('wireframe')}
          icon={<Grid3X3 size={14} />}
        />
      </div>
    </div>
  )
}

function ViewportButton({
  label,
  icon,
  active = false,
  onClick,
}: {
  label: string
  icon: React.ReactNode
  active?: boolean
  onClick: () => void
}) {
  return (
    <button type="button" aria-label={label} aria-pressed={active} onClick={onClick}>
      {icon}
    </button>
  )
}
