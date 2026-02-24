/**
 * DigitalTwin — 3D WebGL data center wireframe using React Three Fiber.
 *
 * Renders a 4×5 grid of server racks with energy connections.
 * Click-to-inspect: clicking a rack selects it in the store.
 * Memory-safe: ConnectionLines uses useMemo for geometry.
 */

import { useRef, useMemo, useState, useCallback } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Grid, Text, Float } from "@react-three/drei";
import * as THREE from "three";
import { useAgentStore } from "../../stores/agentStore";
import type { SceneNode } from "../../lib/types";

// ── Floating particles ────────────────────────────────────────────

function Particles({ count = 80 }: { count?: number }) {
  const mesh = useRef<THREE.Points>(null);
  const positions = useMemo(() => {
    const arr = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      arr[i * 3] = (Math.random() - 0.5) * 30;
      arr[i * 3 + 1] = Math.random() * 8;
      arr[i * 3 + 2] = (Math.random() - 0.5) * 30;
    }
    return arr;
  }, [count]);

  useFrame(({ clock }) => {
    if (!mesh.current) return;
    const t = clock.getElapsedTime() * 0.1;
    const pos = mesh.current.geometry.attributes.position.array as Float32Array;
    for (let i = 0; i < count; i++) {
      pos[i * 3 + 1] = (pos[i * 3 + 1] + 0.003) % 8;
    }
    mesh.current.geometry.attributes.position.needsUpdate = true;
    mesh.current.rotation.y = t * 0.05;
  });

  return (
    <points ref={mesh}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          args={[positions, 3]}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.04}
        color="#00ff88"
        transparent
        opacity={0.3}
        sizeAttenuation
        depthWrite={false}
      />
    </points>
  );
}

// ── Individual rack mesh ──────────────────────────────────────────

function RackNode({ node, onSelect }: { node: SceneNode; onSelect?: (id: string) => void }) {
  const meshRef = useRef<THREE.Mesh>(null);
  const glowRef = useRef<THREE.Mesh>(null);
  const isAnomaly = node.status === "anomaly";
  const baseColor = new THREE.Color(node.color);
  const [hovered, setHovered] = useState(false);

  const handleClick = useCallback(() => {
    onSelect?.(node.id);
  }, [node.id, onSelect]);

  useFrame(({ clock }) => {
    if (!meshRef.current) return;
    const mat = meshRef.current.material as THREE.MeshStandardMaterial;
    const t = clock.getElapsedTime();

    if (isAnomaly) {
      const pulse = 0.5 + 0.5 * Math.sin(t * 4);
      mat.emissiveIntensity = 0.8 + pulse * 1.2;
      meshRef.current.scale.setScalar(1 + pulse * 0.04);
      meshRef.current.position.y = node.position.y + 0.6 + Math.sin(t * 2) * 0.03;
    } else {
      mat.emissiveIntensity = 0.2 + node.energy_level * 0.4 + (hovered ? 0.3 : 0);
      meshRef.current.position.y = node.position.y + 0.6 + Math.sin(t * 0.5 + node.position.x) * 0.01;
    }

    // Ground glow disc
    if (glowRef.current) {
      const gmat = glowRef.current.material as THREE.MeshBasicMaterial;
      gmat.opacity = isAnomaly ? 0.15 + 0.1 * Math.sin(t * 4) : 0.04 + node.energy_level * 0.03;
    }
  });

  return (
    <group>
      {/* Main rack cube */}
      <mesh
        ref={meshRef}
        position={[node.position.x, node.position.y + 0.6, node.position.z]}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
        onClick={handleClick}
      >
        <boxGeometry args={[1.0, 1.2, 1.0]} />
        <meshStandardMaterial
          color={baseColor}
          emissive={baseColor}
          emissiveIntensity={0.3}
          transparent
          opacity={0.9}
          roughness={0.2}
          metalness={0.8}
        />
      </mesh>

      {/* Top indicator light */}
      <mesh position={[node.position.x, node.position.y + 1.25, node.position.z]}>
        <sphereGeometry args={[0.06, 8, 8]} />
        <meshBasicMaterial color={isAnomaly ? "#ff3366" : "#00ff88"} />
      </mesh>

      {/* Ground glow disc */}
      <mesh ref={glowRef} position={[node.position.x, 0.02, node.position.z]} rotation={[-Math.PI / 2, 0, 0]}>
        <circleGeometry args={[0.8, 32]} />
        <meshBasicMaterial color={node.color} transparent opacity={0.05} depthWrite={false} />
      </mesh>
    </group>
  );
}

// ── Connection lines ──────────────────────────────────────────────

function ConnectionLines({ nodes }: { nodes: SceneNode[] }) {
  const nodeMap = useMemo(() => {
    const map = new Map<string, SceneNode>();
    nodes.forEach((n) => map.set(n.id, n));
    return map;
  }, [nodes]);

  const geometries = useMemo(() => {
    const result: { geometry: THREE.BufferGeometry; hot: boolean }[] = [];
    for (let row = 0; row < 4; row++) {
      for (let col = 0; col < 5; col++) {
        const current = nodeMap.get(`rack-${row}-${col}`);
        if (!current) continue;
        const isAnom = current.status === "anomaly";
        const right = nodeMap.get(`rack-${row}-${col + 1}`);
        const below = nodeMap.get(`rack-${row + 1}-${col}`);
        if (right) {
          const g = new THREE.BufferGeometry().setFromPoints([
            new THREE.Vector3(current.position.x, 0.6, current.position.z),
            new THREE.Vector3(right.position.x, 0.6, right.position.z),
          ]);
          result.push({ geometry: g, hot: isAnom || right.status === "anomaly" });
        }
        if (below) {
          const g = new THREE.BufferGeometry().setFromPoints([
            new THREE.Vector3(current.position.x, 0.6, current.position.z),
            new THREE.Vector3(below.position.x, 0.6, below.position.z),
          ]);
          result.push({ geometry: g, hot: isAnom || below.status === "anomaly" });
        }
      }
    }
    return result;
  }, [nodeMap]);

  return (
    <>
      {geometries.map(({ geometry, hot }, i) => {
        const line = new THREE.Line(
          geometry,
          new THREE.LineBasicMaterial({
            color: hot ? "#ff336640" : "#0a2a3a",
            transparent: true,
            opacity: hot ? 0.5 : 0.3,
          })
        );
        return <primitive key={i} object={line} />;
      })}
    </>
  );
}

// ── Default scene (before data arrives) ───────────────────────────

function generateDefaultNodes(): SceneNode[] {
  const nodes: SceneNode[] = [];
  for (let row = 0; row < 4; row++) {
    for (let col = 0; col < 5; col++) {
      nodes.push({
        id: `rack-${row}-${col}`,
        position: { x: (col - 2) * 3, y: 0, z: (row - 1.5) * 3 },
        energy_level: 0.3 + Math.random() * 0.3,
        status: "normal",
        color: "#00ff88",
      });
    }
  }
  return nodes;
}

// ── Scene content ─────────────────────────────────────────────────

function SceneContent() {
  const sceneData = useAgentStore((s) => s.sceneData);
  const setSelectedRackId = useAgentStore((s) => s.setSelectedRackId);
  const nodes = sceneData?.nodes ?? generateDefaultNodes();

  return (
    <>
      {/* Lighting */}
      <ambientLight intensity={0.08} />
      <pointLight position={[10, 15, 10]} intensity={0.6} color="#3b82f6" distance={40} decay={2} />
      <pointLight position={[-10, 10, -10]} intensity={0.3} color="#00ff88" distance={35} decay={2} />
      <pointLight position={[0, 8, 0]} intensity={0.2} color="#a855f7" distance={20} decay={2} />

      {/* Fog for depth */}
      <fog attach="fog" args={["#000000", 15, 35]} />

      {/* Floor grid */}
      <Grid
        args={[40, 40]}
        position={[0, -0.01, 0]}
        cellSize={1}
        cellThickness={0.3}
        cellColor="#071525"
        sectionSize={5}
        sectionThickness={0.5}
        sectionColor="#0f2d52"
        fadeDistance={30}
        infiniteGrid
      />

      {/* Floating particles */}
      <Particles count={100} />

      {/* Rack nodes */}
      {nodes.map((node) => (
        <RackNode key={node.id} node={node} onSelect={setSelectedRackId} />
      ))}

      {/* Connection lines */}
      <ConnectionLines nodes={nodes} />

      {/* Header label */}
      <Float speed={0.5} rotationIntensity={0} floatIntensity={0.3}>
        <Text
          position={[0, 4.5, 0]}
          fontSize={0.35}
          color="#1a2a3a"
          anchorX="center"
          anchorY="middle"
          font={undefined}
          letterSpacing={0.15}
        >
          ECOVERIFY DIGITAL TWIN
        </Text>
      </Float>

      {/* Subtitle */}
      <Text
        position={[0, 4.0, 0]}
        fontSize={0.15}
        color="#0f1a25"
        anchorX="center"
        anchorY="middle"
        font={undefined}
        letterSpacing={0.2}
      >
        BUILDING HQ-01 · REAL-TIME
      </Text>

      {/* Controls */}
      <OrbitControls
        enablePan={true}
        enableZoom={true}
        enableRotate={true}
        autoRotate
        autoRotateSpeed={0.2}
        maxPolarAngle={Math.PI / 2.2}
        minDistance={6}
        maxDistance={22}
        target={[0, 0.5, 0]}
      />
    </>
  );
}

// ── Main component ────────────────────────────────────────────────

export default function DigitalTwin() {
  return (
    <div style={{ width: "100%", height: "360px" }} className="rounded-xl overflow-hidden">
      <Canvas
        camera={{ position: [10, 7, 10], fov: 45 }}
        gl={{ antialias: true, alpha: true, powerPreference: "high-performance" }}
        style={{ background: "transparent" }}
        dpr={[1, 2]}
      >
        <SceneContent />
      </Canvas>
    </div>
  );
}
