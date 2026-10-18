export const edlFragmentShaderSource = /* glsl */ `
uniform sampler2D tDiffuse;
uniform sampler2D tDepth;
uniform vec2 uResolution;
uniform float uEdlStrength;
uniform float uKernelRadius;

varying vec2 vUv;

float readDepth(vec2 uvSample) {
  float rawDepth = texture2D(tDepth, uvSample).x;
  if (rawDepth >= 1.0) {
    return 0.0;
  }
  return rawDepth;
}

void main() {
  vec4 sceneColor = texture2D(tDiffuse, vUv);
  if (uEdlStrength <= 0.0) {
    gl_FragColor = sceneColor;
    return;
  }
  float centerDepth = readDepth(vUv);
  if (centerDepth <= 0.0) {
    gl_FragColor = sceneColor;
    return;
  }

  vec2 pixelStep = uKernelRadius / uResolution;
  float depthDifferenceSum = 0.0;
  depthDifferenceSum += max(0.0, readDepth(vUv + vec2(pixelStep.x, 0.0)) - centerDepth);
  depthDifferenceSum += max(0.0, readDepth(vUv - vec2(pixelStep.x, 0.0)) - centerDepth);
  depthDifferenceSum += max(0.0, readDepth(vUv + vec2(0.0, pixelStep.y)) - centerDepth);
  depthDifferenceSum += max(0.0, readDepth(vUv - vec2(0.0, pixelStep.y)) - centerDepth);
  depthDifferenceSum += max(0.0, readDepth(vUv + pixelStep) - centerDepth);
  depthDifferenceSum += max(0.0, readDepth(vUv - pixelStep) - centerDepth);
  depthDifferenceSum += max(0.0, readDepth(vUv + vec2(pixelStep.x, -pixelStep.y)) - centerDepth);
  depthDifferenceSum += max(0.0, readDepth(vUv + vec2(-pixelStep.x, pixelStep.y)) - centerDepth);

  float shadingFactor = exp(-depthDifferenceSum * uEdlStrength * 55.0);
  shadingFactor = mix(0.72, 1.0, shadingFactor);
  gl_FragColor = vec4(sceneColor.rgb * shadingFactor, sceneColor.a);
}
`;
