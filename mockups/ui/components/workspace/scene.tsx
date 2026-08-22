'use client'

import { useState } from 'react'
import { Canvas } from '@react-three/fiber'
import { Bounds, Edges, GizmoHelper, GizmoViewport, Grid, OrbitControls } from '@react-three/drei'

export type Representation = 'surface' | 'surface-edges' | 'wireframe'

type SceneProps = {
  representation: Representation
  rotate: boolean
  onSelect: (name: string, additive?: boolean) => void
}

type PartProps = {
  id: string
  label: string
  position: [number, number, number]
  scale: [number, number, number]
  color: string
  representation: Representation
  selected: string | null
  onSelect: (id: string, label: string, additive?: boolean) => void
}

function BoxPart({ id, label, position, scale, color, representation, selected, onSelect }: PartProps) {
  return (
    <mesh
      castShadow
      receiveShadow
      position={position}
      scale={scale}
      onPointerDown={(event) => {
        event.stopPropagation()
        onSelect(id, label, event.shiftKey)
      }}
    >
      <boxGeometry />
      <meshStandardMaterial
        color={selected === id ? '#f0b45d' : color}
        metalness={0.22}
        roughness={0.52}
        wireframe={representation === 'wireframe'}
      />
      {representation === 'surface-edges' && <Edges color="#1a2a33" threshold={15} />}
    </mesh>
  )
}

function Bolt({
  id,
  label,
  position,
  representation,
  selected,
  onSelect,
}: Omit<PartProps, 'scale' | 'color'>) {
  return (
    <mesh
      castShadow
      position={position}
      onPointerDown={(event) => {
        event.stopPropagation()
        onSelect(id, label, event.shiftKey)
      }}
    >
      <cylinderGeometry args={[0.16, 0.16, 0.48, 24]} />
      <meshStandardMaterial
        color={selected === id ? '#f0b45d' : '#81919a'}
        metalness={0.42}
        roughness={0.38}
        wireframe={representation === 'wireframe'}
      />
      {representation === 'surface-edges' && <Edges color="#26363f" threshold={15} />}
    </mesh>
  )
}

function MockAssembly({ representation, onSelect }: Pick<SceneProps, 'representation' | 'onSelect'>) {
  const [selected, setSelected] = useState<string | null>(null)
  const select = (id: string, label: string, additive?: boolean) => {
    setSelected(id)
    onSelect(label, additive)
  }
  const common = { representation, selected, onSelect: select }

  return (
    <group rotation={[0, -0.28, 0]}>
      <BoxPart id="base" label="ベース（仮）" position={[0, -0.76, 0]} scale={[3.4, 0.34, 2.35]} color="#577f92" {...common} />
      <BoxPart id="left-support" label="左支持部（仮）" position={[-1.22, 0.35, 0]} scale={[0.42, 2.25, 0.5]} color="#6e9cb0" {...common} />
      <BoxPart id="right-support" label="右支持部（仮）" position={[1.22, 0.35, 0]} scale={[0.42, 2.25, 0.5]} color="#6e9cb0" {...common} />
      <BoxPart id="bridge" label="上部連結（仮）" position={[0, 1.48, 0]} scale={[2.85, 0.42, 0.5]} color="#618c9f" {...common} />
      <BoxPart id="rear-rib" label="補強リブ（仮）" position={[0, 0.12, -0.86]} scale={[2.4, 1.35, 0.18]} color="#4f7383" {...common} />
      {[
        [-1.1, -0.5, -0.76],
        [1.1, -0.5, -0.76],
        [-1.1, -0.5, 0.76],
        [1.1, -0.5, 0.76],
      ].map((position, index) => (
        <Bolt
          key={index}
          id={`bolt-${index}`}
          label={`固定具 ${index + 1}（仮）`}
          position={position as [number, number, number]}
          {...common}
        />
      ))}
    </group>
  )
}

export default function Scene({ representation, rotate, onSelect }: SceneProps) {
  return (
    <Canvas
      aria-label="操作可能なThree.js仮形状"
      shadows
      dpr={[1, 2]}
      camera={{ position: [5.2, 3.3, 5.8], fov: 38 }}
      onPointerMissed={() => onSelect('選択なし')}
    >
      <color attach="background" args={['#151b20']} />
      <hemisphereLight intensity={0.72} groundColor="#10161a" color="#d8e8ef" />
      <directionalLight position={[4, 7, 5]} intensity={1.7} castShadow shadow-mapSize={[1024, 1024]} />
      <directionalLight position={[-4, 2, -3]} intensity={0.45} color="#91b8ca" />

      <Bounds fit clip margin={1.2}>
        <MockAssembly representation={representation} onSelect={onSelect} />
      </Bounds>

      <Grid
        position={[0, -0.96, 0]}
        args={[24, 24]}
        cellSize={0.5}
        cellThickness={0.55}
        cellColor="#34434b"
        sectionSize={2.5}
        sectionThickness={1}
        sectionColor="#50616a"
        fadeDistance={24}
        fadeStrength={1.3}
        infiniteGrid
      />

      <OrbitControls
        makeDefault
        autoRotate={rotate}
        autoRotateSpeed={0.8}
        enableDamping
        dampingFactor={0.08}
        minDistance={2.5}
        maxDistance={16}
      />
      <GizmoHelper alignment="top-right" margin={[54, 102]}>
        <GizmoViewport
          scale={36}
          axisHeadScale={1.1}
          font="600 22px Inter, Arial, sans-serif"
          axisColors={['#d35a5a', '#55a56a', '#5c86d6']}
          labelColor="#f2f5f6"
        />
      </GizmoHelper>
    </Canvas>
  )
}
