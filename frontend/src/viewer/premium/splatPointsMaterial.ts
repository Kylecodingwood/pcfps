import * as THREE from "three";
import { splatFragmentShaderSource } from "./shaders/splatFragment.glsl";
import { splatVertexShaderSource } from "./shaders/splatVertex.glsl";

export interface CreateSplatPointsMaterialOptions {
  basePointSize: number;
  pointSizeScale: number;
  solidColorHex: number;
  useVertexColors: boolean;
}

/**
 * ShaderMaterial for soft circular point splats with perspective sizing.
 */
export function createSplatPointsMaterial(options: CreateSplatPointsMaterialOptions): THREE.ShaderMaterial {
  const solidColor = new THREE.Color(options.solidColorHex);
  return new THREE.ShaderMaterial({
    uniforms: {
      uBaseSize: { value: options.basePointSize },
      uSizeScale: { value: options.pointSizeScale },
      uUseVertexColor: { value: options.useVertexColors ? 1 : 0 },
      uSolidColor: { value: solidColor },
    },
    vertexShader: splatVertexShaderSource,
    fragmentShader: splatFragmentShaderSource,
    transparent: true,
    depthWrite: true,
    depthTest: true,
    blending: THREE.NormalBlending,
  });
}

export function updateSplatPointsMaterialUniforms(
  material: THREE.ShaderMaterial,
  basePointSize: number,
  pointSizeScale: number
): void {
  material.uniforms.uBaseSize.value = basePointSize;
  material.uniforms.uSizeScale.value = pointSizeScale;
}
