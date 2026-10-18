export const splatFragmentShaderSource = /* glsl */ `
varying vec3 vColor;

void main() {
  vec2 centeredCoord = gl_PointCoord - vec2(0.5);
  float distanceFromCenter = length(centeredCoord);
  float alpha = exp(-distanceFromCenter * distanceFromCenter * 18.0);
  alpha = smoothstep(0.38, 0.14, distanceFromCenter);
  if (alpha < 0.04) {
    discard;
  }
  gl_FragColor = vec4(vColor, alpha);
}
`;
