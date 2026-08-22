/**
 * JarvisBrain — Animated 3D "AI Core" using React Three Fiber.
 * States: idle | listening | thinking | executing | speaking | error
 *
 * Visual design:
 *   - Central glowing orb with energy rings
 *   - Pulsing particles that react to state
 *   - Color-coded by state (cyan=idle, green=listening, purple=thinking, etc.)
 */
import { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Sphere, MeshDistortMaterial, Ring } from '@react-three/drei';
import * as THREE from 'three';
import type { JarvisBrainState } from '../stores/jarvisStore.js';

// ─── State Configs ─────────────────────────────────────────────────────────

interface StateConfig {
  color: string;
  emissive: string;
  distort: number;
  speed: number;
  ringColor: string;
  scale: number;
}

const STATE_CONFIGS: Record<JarvisBrainState, StateConfig> = {
  idle: {
    color: '#0891b2',
    emissive: '#0e7490',
    distort: 0.25,
    speed: 0.8,
    ringColor: '#22d3ee',
    scale: 1.0,
  },
  listening: {
    color: '#059669',
    emissive: '#047857',
    distort: 0.5,
    speed: 2.0,
    ringColor: '#10b981',
    scale: 1.08,
  },
  thinking: {
    color: '#7c3aed',
    emissive: '#6d28d9',
    distort: 0.65,
    speed: 3.5,
    ringColor: '#a855f7',
    scale: 1.05,
  },
  executing: {
    color: '#b45309',
    emissive: '#92400e',
    distort: 0.7,
    speed: 4.5,
    ringColor: '#f59e0b',
    scale: 1.12,
  },
  speaking: {
    color: '#1d4ed8',
    emissive: '#1e40af',
    distort: 0.45,
    speed: 1.5,
    ringColor: '#3b82f6',
    scale: 1.04,
  },
  error: {
    color: '#b91c1c',
    emissive: '#991b1b',
    distort: 0.8,
    speed: 5.0,
    ringColor: '#ef4444',
    scale: 0.95,
  },
};

// ─── Animated Orb ─────────────────────────────────────────────────────────

function BrainOrb({ brainState }: { brainState: JarvisBrainState }) {
  const meshRef = useRef<THREE.Mesh>(null!);
  const config = STATE_CONFIGS[brainState];

  // Lerp scale toward target
  const targetScale = useRef(config.scale);
  const currentScale = useRef(1.0);

  useFrame((_, delta) => {
    targetScale.current = STATE_CONFIGS[brainState].scale;
    currentScale.current = THREE.MathUtils.lerp(
      currentScale.current,
      targetScale.current,
      delta * 3
    );
    if (meshRef.current) {
      meshRef.current.scale.setScalar(currentScale.current);
      meshRef.current.rotation.y += delta * 0.3;
      meshRef.current.rotation.z += delta * 0.1;
    }
  });

  return (
    <Sphere ref={meshRef} args={[1, 128, 128]}>
      <MeshDistortMaterial
        color={config.color}
        emissive={config.emissive}
        emissiveIntensity={0.6}
        distort={config.distort}
        speed={config.speed}
        roughness={0.1}
        metalness={0.4}
        transparent
        opacity={0.9}
      />
    </Sphere>
  );
}

// ─── Energy Rings ──────────────────────────────────────────────────────────

function EnergyRings({ brainState }: { brainState: JarvisBrainState }) {
  const ring1 = useRef<THREE.Mesh>(null!);
  const ring2 = useRef<THREE.Mesh>(null!);
  const ring3 = useRef<THREE.Mesh>(null!);
  const config = STATE_CONFIGS[brainState];
  const color = new THREE.Color(config.ringColor);

  useFrame((_, delta) => {
    const speed = config.speed * 0.25;
    if (ring1.current) ring1.current.rotation.z += delta * speed;
    if (ring2.current) ring2.current.rotation.x += delta * speed * 0.7;
    if (ring3.current) {
      ring3.current.rotation.y += delta * speed * 0.5;
      ring3.current.rotation.z -= delta * speed * 0.3;
    }
  });

  return (
    <>
      <Ring ref={ring1} args={[1.3, 1.35, 64]} rotation={[Math.PI / 2, 0, 0]}>
        <meshBasicMaterial color={color} transparent opacity={0.6} side={THREE.DoubleSide} />
      </Ring>
      <Ring ref={ring2} args={[1.5, 1.52, 64]} rotation={[Math.PI / 3, Math.PI / 4, 0]}>
        <meshBasicMaterial color={color} transparent opacity={0.35} side={THREE.DoubleSide} />
      </Ring>
      <Ring ref={ring3} args={[1.8, 1.82, 64]} rotation={[0, Math.PI / 4, Math.PI / 6]}>
        <meshBasicMaterial color={color} transparent opacity={0.2} side={THREE.DoubleSide} />
      </Ring>
    </>
  );
}

// ─── Orbiting Particles ────────────────────────────────────────────────────

function OrbitParticles({ brainState }: { brainState: JarvisBrainState }) {
  const config = STATE_CONFIGS[brainState];
  const count = 60;
  const color = new THREE.Color(config.ringColor);

  const { positions, radii, speeds, phases } = useMemo(() => {
    const positions: [number, number, number][] = [];
    const radii: number[] = [];
    const speeds: number[] = [];
    const phases: number[] = [];
    for (let i = 0; i < count; i++) {
      const r = 1.6 + Math.random() * 1.2;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      positions.push([
        r * Math.sin(phi) * Math.cos(theta),
        r * Math.sin(phi) * Math.sin(theta),
        r * Math.cos(phi),
      ]);
      radii.push(r);
      speeds.push(0.3 + Math.random() * 0.7);
      phases.push(Math.random() * Math.PI * 2);
    }
    return { positions, radii, speeds, phases };
  }, []);

  const refs = useRef<THREE.Mesh[]>([]);

  useFrame(({ clock }) => {
    const t = clock.elapsedTime;
    refs.current.forEach((mesh, i) => {
      if (!mesh) return;
      const r = radii[i];
      const speed = speeds[i] * config.speed * 0.15;
      const phi = phases[i] + t * speed;
      const theta = phases[i] * 1.3 + t * speed * 0.5;
      mesh.position.x = r * Math.sin(phi) * Math.cos(theta);
      mesh.position.y = r * Math.sin(phi) * Math.sin(theta);
      mesh.position.z = r * Math.cos(phi);
    });
  });

  return (
    <>
      {positions.map((_, i) => (
        <mesh
          key={i}
          ref={(el) => {
            if (el) refs.current[i] = el;
          }}
        >
          <sphereGeometry args={[0.02 + Math.random() * 0.03, 4, 4]} />
          <meshBasicMaterial color={color} transparent opacity={0.5 + Math.random() * 0.4} />
        </mesh>
      ))}
    </>
  );
}

// ─── Point Light ──────────────────────────────────────────────────────────

function BrainLight({ brainState }: { brainState: JarvisBrainState }) {
  const lightRef = useRef<THREE.PointLight>(null!);
  const config = STATE_CONFIGS[brainState];

  useFrame(({ clock }) => {
    if (lightRef.current) {
      lightRef.current.intensity = 2 + Math.sin(clock.elapsedTime * 2) * 0.5;
    }
  });

  return (
    <pointLight
      ref={lightRef}
      color={config.ringColor}
      intensity={2.5}
      distance={8}
    />
  );
}

// ─── Main Scene ────────────────────────────────────────────────────────────

function BrainScene({ brainState }: { brainState: JarvisBrainState }) {
  return (
    <>
      <ambientLight intensity={0.2} />
      <BrainLight brainState={brainState} />
      <BrainOrb brainState={brainState} />
      <EnergyRings brainState={brainState} />
      <OrbitParticles brainState={brainState} />
    </>
  );
}

// ─── Exported Component ────────────────────────────────────────────────────

interface JarvisBrainProps {
  brainState: JarvisBrainState;
  size?: number;
}

export function JarvisBrain({ brainState, size = 280 }: JarvisBrainProps) {
  return (
    <div
      className="relative select-none"
      style={{ width: size, height: size }}
      aria-label={`Jarvis brain — state: ${brainState}`}
    >
      {/* Outer glow ring (CSS) */}
      <div
        className="absolute inset-0 rounded-full pointer-events-none"
        style={{
          boxShadow: `0 0 60px 8px ${STATE_CONFIGS[brainState].ringColor}30`,
          borderRadius: '50%',
          transition: 'box-shadow 0.8s ease',
        }}
      />

      <Canvas
        camera={{ position: [0, 0, 3.5], fov: 50 }}
        style={{ borderRadius: '50%', background: 'transparent' }}
        gl={{ alpha: true, antialias: true }}
      >
        <BrainScene brainState={brainState} />
      </Canvas>
    </div>
  );
}
