/** CSS/SVG clipping uses only the decorative sides of the supplied reference, never its form. */
export function LoginReferenceArt() {
  return <svg className="login-reference-art" viewBox="0 75 1672 866" preserveAspectRatio="none" aria-hidden="true">
    <defs><clipPath id="login-reference-sides"><rect x="0" y="75" width="550" height="866"/><rect x="1182" y="75" width="490" height="866"/><rect x="0" y="860" width="1672" height="81"/></clipPath></defs>
    <image href="/images/coco-login-reference.png" x="0" y="0" width="1672" height="941" clipPath="url(#login-reference-sides)"/>
  </svg>;
}
