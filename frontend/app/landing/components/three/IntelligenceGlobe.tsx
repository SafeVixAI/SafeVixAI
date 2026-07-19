// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

'use client';

import { useRef, useMemo, useState, useEffect, Suspense } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { Stars, Line } from '@react-three/drei';
import * as THREE from 'three';

/* ────────────────────────────────────────────────────────────
   SafeVixAI Landing — 3D Intelligence Globe
   A wireframe globe with Indian city markers and data lines
   ──────────────────────────────────────────────────────────── */

/* ── City data positioned on globe surface using spherical coords ── */
interface CityMarker {
  name: string;
  /** phi: polar angle from top (0..π) */
  phi: number;
  /** theta: azimuthal angle around Y axis (0..2π) */
  theta: number;
  type: 'emergency' | 'monitoring';
}

// Indian cities mapped to approximate spherical coordinates on the globe
const CITIES: CityMarker[] = [
  // Emergency hotspots (red)
  { name: 'Delhi', phi: 1.12, theta: 1.35, type: 'emergency' },
  { name: 'Mumbai', phi: 1.42, theta: 1.08, type: 'emergency' },
  { name: 'Chennai', phi: 1.60, theta: 1.48, type: 'emergency' },
  { name: 'Kolkata', phi: 1.28, theta: 1.70, type: 'emergency' },
  { name: 'Bangalore', phi: 1.55, theta: 1.28, type: 'emergency' },
  // Monitoring cities (green)
  { name: 'Hyderabad', phi: 1.45, theta: 1.32, type: 'monitoring' },
  { name: 'Ahmedabad', phi: 1.28, theta: 0.98, type: 'monitoring' },
  { name: 'Pune', phi: 1.43, theta: 1.12, type: 'monitoring' },
  { name: 'Jaipur', phi: 1.18, theta: 1.15, type: 'monitoring' },
  { name: 'Lucknow', phi: 1.18, theta: 1.45, type: 'monitoring' },
  { name: 'Kochi', phi: 1.65, theta: 1.18, type: 'monitoring' },
  { name: 'Bhopal', phi: 1.32, theta: 1.25, type: 'monitoring' },
  { name: 'Nagpur', phi: 1.38, theta: 1.30, type: 'monitoring' },
  { name: 'Chandigarh', phi: 1.05, theta: 1.28, type: 'monitoring' },
  { name: 'Guwahati', phi: 1.18, theta: 1.88, type: 'monitoring' },
  { name: 'Patna', phi: 1.22, theta: 1.58, type: 'monitoring' },
  { name: 'Varanasi', phi: 1.22, theta: 1.50, type: 'monitoring' },
];

/** Convert spherical coords to cartesian on globe surface */
function sphericalToCartesian(
  phi: number,
  theta: number,
  radius: number
): [number, number, number] {
  return [
    radius * Math.sin(phi) * Math.cos(theta),
    radius * Math.cos(phi),
    radius * Math.sin(phi) * Math.sin(theta),
  ];
}

/* ── Connection lines between cities ── */
const CONNECTIONS: [number, number][] = [
  [0, 1], // Delhi → Mumbai
  [1, 4], // Mumbai → Bangalore
  [4, 2], // Bangalore → Chennai
  [0, 3], // Delhi → Kolkata
  [0, 8], // Delhi → Jaipur
  [1, 7], // Mumbai → Pune
];

function generateCurvedLine(
  start: [number, number, number],
  end: [number, number, number],
  segments: number = 32
): THREE.Vector3[] {
  const points: THREE.Vector3[] = [];
  const startV = new THREE.Vector3(...start);
  const endV = new THREE.Vector3(...end);
  const mid = startV.clone().add(endV).multiplyScalar(0.5);
  // Push the midpoint outward to create a curve above the surface
  mid.normalize().multiplyScalar(2.6);

  for (let i = 0; i <= segments; i++) {
    const t = i / segments;
    // Quadratic Bezier curve
    const p = new THREE.Vector3()
      .copy(startV)
      .multiplyScalar((1 - t) * (1 - t))
      .add(mid.clone().multiplyScalar(2 * (1 - t) * t))
      .add(endV.clone().multiplyScalar(t * t));
    points.push(p);
  }
  return points;
}

/* ── City Dot Mesh ── */
function CityDot({
  position,
  type,
}: {
  position: [number, number, number];
  type: 'emergency' | 'monitoring';
}) {
  const isEmergency = type === 'emergency';
  const color = isEmergency ? '#DC2626' : '#00C896';
  const radius = isEmergency ? 0.03 : 0.025;
  const emissiveIntensity = isEmergency ? 2 : 1.5;

  return (
    <mesh position={position}>
      <sphereGeometry args={[radius, 12, 12]} />
      <meshStandardMaterial
        color={color}
        emissive={color}
        emissiveIntensity={emissiveIntensity}
        toneMapped={false}
      />
    </mesh>
  );
}

/* ── Connection Lines ── */
function ConnectionLines() {
  const lines = useMemo(() => {
    return CONNECTIONS.map(([from, to]) => {
      const startCity = CITIES[from];
      const endCity = CITIES[to];
      const startPos = sphericalToCartesian(startCity.phi, startCity.theta, 2);
      const endPos = sphericalToCartesian(endCity.phi, endCity.theta, 2);
      return generateCurvedLine(startPos, endPos);
    });
  }, []);

  return (
    <>
      {lines.map((points, i) => (
        <Line
          key={i}
          points={points}
          color="#00C896"
          lineWidth={1}
          transparent
          opacity={0.3}
        />
      ))}
    </>
  );
}

/* ── Globe Group (auto-rotating + pointer offset) ── */
function GlobeGroup({ reducedMotion }: { reducedMotion: boolean }) {
  const groupRef = useRef<THREE.Group>(null);
  const { pointer } = useThree();

  // City positions
  const cityPositions = useMemo(() => {
    return CITIES.map((city) => ({
      position: sphericalToCartesian(city.phi, city.theta, 2) as [number, number, number],
      type: city.type,
      name: city.name,
    }));
  }, []);

  useFrame((_state, delta) => {
    if (!groupRef.current) return;
    if (reducedMotion) return;

    // Auto rotation
    groupRef.current.rotation.y += 0.001;

    // Subtle pointer-based tilt
    const targetRotX = pointer.y * 0.08;
    const targetRotZ = pointer.x * -0.04;
    groupRef.current.rotation.x = THREE.MathUtils.lerp(
      groupRef.current.rotation.x,
      targetRotX,
      delta * 2
    );
    groupRef.current.rotation.z = THREE.MathUtils.lerp(
      groupRef.current.rotation.z,
      targetRotZ,
      delta * 2
    );
  });

  return (
    <group ref={groupRef}>
      {/* Wireframe globe */}
      <mesh>
        <sphereGeometry args={[2, 64, 64]} />
        <meshStandardMaterial
          color="#0a3d1f"
          wireframe
          transparent
          opacity={0.15}
        />
      </mesh>

      {/* Solid inner glow sphere */}
      <mesh>
        <sphereGeometry args={[2.02, 64, 64]} />
        <meshStandardMaterial
          color="#1A5C38"
          transparent
          opacity={0.05}
          side={THREE.BackSide}
        />
      </mesh>

      {/* City markers */}
      {cityPositions.map((city) => (
        <CityDot
          key={city.name}
          position={city.position}
          type={city.type}
        />
      ))}

      {/* Connection lines */}
      <ConnectionLines />
    </group>
  );
}

/* ── Scene Internals ── */
function Scene({ reducedMotion }: { reducedMotion: boolean }) {
  return (
    <>
      {/* Lighting */}
      <ambientLight intensity={0.3} />
      <pointLight position={[5, 5, 5]} color="#00C896" intensity={0.6} />
      <pointLight position={[-3, -3, -5]} color="#3B82F6" intensity={0.3} />

      {/* Stars background */}
      <Stars
        radius={50}
        count={800}
        depth={50}
        fade
        saturation={0}
        factor={2}
      />

      {/* Globe */}
      <GlobeGroup reducedMotion={reducedMotion} />
    </>
  );
}

/* ── Exported Canvas Component ── */
export default function IntelligenceGlobe() {
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    setReducedMotion(mq.matches);
    const handler = (e: MediaQueryListEvent) => setReducedMotion(e.matches);
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, []);

  return (
    <Suspense fallback={null}>
      <Canvas
        camera={{ position: [0, 0, 5], fov: 45 }}
        dpr={[1, 1.5]}
        frameloop={reducedMotion ? 'demand' : 'always'}
        gl={{ alpha: true, antialias: true }}
        style={{ width: '100%', height: '100%' }}
      >
        <Scene reducedMotion={reducedMotion} />
      </Canvas>
    </Suspense>
  );
}
