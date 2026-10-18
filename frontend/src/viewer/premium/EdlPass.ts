import * as THREE from "three";
import { Pass } from "three/examples/jsm/postprocessing/Pass.js";
import { FullScreenQuad } from "three/examples/jsm/postprocessing/Pass.js";
import { edlFragmentShaderSource } from "./shaders/edlFragment.glsl";
import { edlVertexShaderSource } from "./shaders/edlVertex.glsl";

/**
 * Eye-Dome Lighting post pass: darkens pixels where depth discontinuities occur (point cloud edges).
 */
export class EdlPass extends Pass {
  private readonly fullScreenQuad: FullScreenQuad;
  private readonly edlMaterial: THREE.ShaderMaterial;

  constructor() {
    super();
    this.fullScreenQuad = new FullScreenQuad(
      new THREE.ShaderMaterial({
        uniforms: {
          tDiffuse: { value: null },
          tDepth: { value: null },
          uResolution: { value: new THREE.Vector2(1, 1) },
          uEdlStrength: { value: 1.2 },
          uKernelRadius: { value: 1 },
        },
        vertexShader: edlVertexShaderSource,
        fragmentShader: edlFragmentShaderSource,
        depthWrite: false,
        depthTest: false,
      })
    );
    this.edlMaterial = this.fullScreenQuad.material as THREE.ShaderMaterial;
  }

  get strength(): number {
    return this.edlMaterial.uniforms.uEdlStrength.value as number;
  }

  set strength(value: number) {
    this.edlMaterial.uniforms.uEdlStrength.value = value;
  }

  get kernelRadius(): number {
    return this.edlMaterial.uniforms.uKernelRadius.value as number;
  }

  set kernelRadius(value: number) {
    this.edlMaterial.uniforms.uKernelRadius.value = value;
  }

  setSize(width: number, height: number): void {
    (this.edlMaterial.uniforms.uResolution.value as THREE.Vector2).set(width, height);
  }

  render(
    renderer: THREE.WebGLRenderer,
    writeBuffer: THREE.WebGLRenderTarget,
    readBuffer: THREE.WebGLRenderTarget
  ): void {
    const colorTexture = readBuffer.texture;
    const depthTexture = readBuffer.depthTexture ?? writeBuffer.depthTexture;
    this.edlMaterial.uniforms.tDiffuse.value = colorTexture;
    this.edlMaterial.uniforms.tDepth.value = depthTexture ?? colorTexture;
    this.edlMaterial.uniforms.uEdlStrength.value = depthTexture ? this.strength : 0;

    renderer.setRenderTarget(this.renderToScreen ? null : writeBuffer);
    if (this.clear) {
      renderer.clear();
    }
    this.fullScreenQuad.render(renderer);
  }

  dispose(): void {
    this.edlMaterial.dispose();
    this.fullScreenQuad.dispose();
  }
}
