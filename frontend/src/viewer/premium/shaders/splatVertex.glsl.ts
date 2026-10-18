export const splatVertexShaderSource = /* glsl */ `
attribute vec3 color;
uniform float uBaseSize;
uniform float uSizeScale;
uniform float uUseVertexColor;
uniform vec3 uSolidColor;

varying vec3 vColor;
varying float vAlphaDiscardGuard;

void main() {
  vColor = uUseVertexColor > 0.5 ? color : uSolidColor;
  vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
  float distanceToCamera = max(-mvPosition.z, 1e-3);
  float perspectiveSize = uBaseSize * uSizeScale * (140.0 / distanceToCamera);
  gl_PointSize = clamp(perspectiveSize, 0.75, 18.0);
  gl_Position = projectionMatrix * mvPosition;
  vAlphaDiscardGuard = 1.0;
}
`;
