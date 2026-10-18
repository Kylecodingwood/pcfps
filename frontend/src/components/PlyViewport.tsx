import { useEffect, useRef } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { PLYLoader } from "three/examples/jsm/loaders/PLYLoader.js";

interface PlyViewportProps {
  label: string;
  blobUrl: string | null;
}

/**
 * Renders a single PLY point cloud from a blob URL with orbit controls.
 */
export function PlyViewport({ label, blobUrl }: PlyViewportProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const containerElement = containerRef.current;
    if (!containerElement || !blobUrl) {
      return;
    }

    const width = containerElement.clientWidth || 400;
    const height = 320;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x222222);

    const camera = new THREE.PerspectiveCamera(50, width / height, 0.01, 500);
    camera.position.set(0.3, 0.3, 0.5);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    containerElement.innerHTML = "";
    containerElement.appendChild(renderer.domElement);

    const ambient = new THREE.AmbientLight(0xffffff, 1);
    scene.add(ambient);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.set(0, 0, 0);

    const loader = new PLYLoader();
    let mesh: THREE.Points | null = null;

    loader.load(
      blobUrl,
      (geometry: THREE.BufferGeometry) => {
        geometry.computeVertexNormals();
        const material = new THREE.PointsMaterial({
          size: 0.02,
          vertexColors: geometry.hasAttribute("color"),
        });
        if (!geometry.hasAttribute("color")) {
          material.color = new THREE.Color(0x66ccff);
        }
        mesh = new THREE.Points(geometry, material);
        scene.add(mesh);
        const box = new THREE.Box3().setFromObject(mesh);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());
        const maxDim = Math.max(size.x, size.y, size.z, 0.01);
        camera.position.set(center.x + maxDim, center.y + maxDim * 0.5, center.z + maxDim);
        controls.target.copy(center);
        controls.update();
      },
      undefined,
      (error: unknown) => {
        console.error("PLY load error", error);
      }
    );

    let animationFrameId = 0;
    function animate() {
      animationFrameId = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    }
    animate();

    return () => {
      cancelAnimationFrame(animationFrameId);
      controls.dispose();
      renderer.dispose();
      if (mesh) {
        mesh.geometry.dispose();
        (mesh.material as THREE.Material).dispose();
      }
      containerElement.innerHTML = "";
    };
  }, [blobUrl]);

  return (
    <div style={{ flex: 1, minWidth: 280 }}>
      <h3 style={{ margin: "0 0 8px" }}>{label}</h3>
      {!blobUrl && <p style={{ color: "#888" }}>无可用预览</p>}
      <div ref={containerRef} style={{ width: "100%", minHeight: 320, background: "#111" }} />
    </div>
  );
}
