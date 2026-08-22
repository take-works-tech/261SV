'use client'

import { useState } from 'react'
import { Canvas } from '@react-three/fiber'
import { ContactShadows, OrbitControls } from '@react-three/drei'
import { Box, ChartNoAxesCombined, Circle, CircleDashed, Cylinder, Gauge, Grid2X2, Palette, Square, Waypoints } from 'lucide-react'
import { MaterialSphereIcon } from '@/components/icons/material-sphere-icon'

type PreviewShape = 'sphere' | 'cube' | 'plane' | 'cylinder' | 'plane2d'
type PreviewChannel = 'material' | 'base-color' | 'roughness' | 'metalness' | 'normal' | 'analysis-color'

const previewShapes: { id: PreviewShape; label: string; icon: typeof Circle }[] = [
  { id: 'sphere', label: '球', icon: Circle },
  { id: 'cube', label: '立方体', icon: Box },
  { id: 'plane', label: '平面', icon: Square },
  { id: 'cylinder', label: '円柱', icon: Cylinder },
  { id: 'plane2d', label: '2D面', icon: Grid2X2 },
]

const previewChannels: { id: PreviewChannel; label: string; icon: typeof Circle }[] = [
  { id: 'material', label: 'マテリアル', icon: MaterialSphereIcon },
  { id: 'base-color', label: 'Base Color', icon: Palette },
  { id: 'roughness', label: 'Roughness', icon: Gauge },
  { id: 'metalness', label: 'Metalness', icon: CircleDashed },
  { id: 'normal', label: 'Normal', icon: Waypoints },
  { id: 'analysis-color', label: '解析カラー', icon: ChartNoAxesCombined },
]

const channelAppearance: Record<PreviewChannel, { color: string; metalness: number; roughness: number }> = {
  material: { color: '#78858b', metalness: 0.72, roughness: 0.28 },
  'base-color': { color: '#78858b', metalness: 0, roughness: 0.72 },
  roughness: { color: '#737373', metalness: 0, roughness: 1 },
  metalness: { color: '#b8b8b8', metalness: 1, roughness: 0.24 },
  normal: { color: '#818aff', metalness: 0, roughness: 0.78 },
  'analysis-color': { color: '#e3b83f', metalness: 0, roughness: 0.68 },
}

function PreviewGeometry({ shape, channel, failed }: { shape: PreviewShape; channel: PreviewChannel; failed: boolean }) {
  const rotation: [number, number, number] = shape === 'plane' ? [-0.32, 0.28, 0] : shape === 'plane2d' ? [0, 0, 0] : [0, 0.35, 0]
  const appearance = channelAppearance[channel]

  return (
    <mesh castShadow receiveShadow rotation={rotation}>
      {shape === 'sphere' && <sphereGeometry args={[0.9, 64, 40]} />}
      {shape === 'cube' && <boxGeometry args={[1.45, 1.45, 1.45, 4, 4, 4]} />}
      {shape === 'plane' && <planeGeometry args={[1.9, 1.9, 24, 24]} />}
      {shape === 'cylinder' && <cylinderGeometry args={[0.72, 0.72, 1.65, 64, 8]} />}
      {shape === 'plane2d' && <planeGeometry args={[2.15, 2.15, 1, 1]} />}
      <meshPhysicalMaterial
        color={failed ? '#ff00ff' : appearance.color}
        metalness={failed ? 0 : appearance.metalness}
        roughness={failed ? 0.62 : appearance.roughness}
        clearcoat={failed ? 0 : 0.24}
        clearcoatRoughness={0.2}
      />
    </mesh>
  )
}

export function MaterialPreview({ available = true, failed = false, sampleData = false, bindingLabel, empty = false, resultOutput = false }: { available?: boolean; failed?: boolean; sampleData?: boolean; bindingLabel?: string; empty?: boolean; resultOutput?: boolean }) {
  const [shape, setShape] = useState<PreviewShape>('sphere')
  const [channel, setChannel] = useState<PreviewChannel>('material')
  const isTwoDimensional = shape === 'plane2d'
  const cameraPosition: [number, number, number] = isTwoDimensional ? [0, 0, 3.35] : [2.35, 1.65, 2.65]
  const availableChannels = resultOutput ? previewChannels : previewChannels.filter((item) => item.id !== 'analysis-color')
  const activeChannel = !resultOutput && channel === 'analysis-color' ? 'material' : channel
  const stateLabel = failed ? 'マテリアル表示失敗' : sampleData ? 'サンプルデータ' : bindingLabel ?? '外観プレビュー'
  const channelLabel = previewChannels.find((item) => item.id === activeChannel)?.label

  return (
    <section className={`material-preview-panel ${failed ? 'failed' : ''}`} aria-label="マテリアル外観プレビュー">
      {available ? (
        <div className="material-preview-canvas">
          <Canvas key={isTwoDimensional ? '2d' : '3d'} aria-label={`${previewShapes.find((item) => item.id === shape)?.label}で${channelLabel}を確認`} dpr={[1, 1.5]} camera={{ position: cameraPosition, fov: 34 }} shadows>
            <color attach="background" args={[failed ? '#f3d9ee' : '#e9eef1']} />
            <hemisphereLight intensity={1.05} color="#ffffff" groundColor="#b8c4ca" />
            <directionalLight castShadow intensity={2.1} color="#ffffff" position={[3.5, 4.5, 3]} shadow-mapSize={[512, 512]} />
            <directionalLight intensity={0.55} color="#8fb1c5" position={[-3, 1.5, -2]} />
            <PreviewGeometry shape={shape} channel={activeChannel} failed={failed} />
            {!isTwoDimensional && <ContactShadows position={[0, -1.06, 0]} opacity={0.42} scale={5} blur={2.6} far={3.5} />}
            {!isTwoDimensional && <OrbitControls makeDefault enableDamping dampingFactor={0.08} enablePan={false} minDistance={2.4} maxDistance={5.5} autoRotate autoRotateSpeed={0.55} />}
          </Canvas>
          <div className="material-preview-channels" role="group" aria-label="表示するマテリアル出力">
            {availableChannels.map((item) => {
              const Icon = item.icon
              return <button type="button" title={item.label} aria-label={`${item.label}を表示`} aria-pressed={activeChannel === item.id} className={activeChannel === item.id ? 'active' : ''} onClick={() => setChannel(item.id)} key={item.id}><Icon size={14} strokeWidth={1.7} aria-hidden="true" /></button>
            })}
          </div>
          <div className="material-preview-shapes" role="group" aria-label="プレビュー形状">
            {previewShapes.map((item) => {
              const Icon = item.icon
              return <button type="button" title={item.label} aria-label={item.id === 'plane2d' ? '2D面で固定プレビュー' : `${item.label}でプレビュー`} aria-pressed={shape === item.id} className={shape === item.id ? 'active' : ''} onClick={() => setShape(item.id)} key={item.id}><Icon size={14} strokeWidth={1.7} aria-hidden="true" /></button>
            })}
          </div>
          <span className="material-preview-label">{stateLabel} · {channelLabel}</span>
          <span className="material-preview-hint">{isTwoDimensional ? '固定表示' : 'ドラッグで回転'}</span>
        </div>
      ) : (
        <div className="material-preview-unavailable">
          <b>{empty ? 'マテリアル未選択' : 'マテリアルプレビュー対象外'}</b>
          <small>{empty ? '＋でマテリアルスロットを追加します。' : 'このオブジェクト種類では専用の表示設定を使用します。'}</small>
        </div>
      )}
    </section>
  )
}
