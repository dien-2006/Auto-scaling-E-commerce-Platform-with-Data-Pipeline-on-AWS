/** Display only decorative sides of the supplied image; its form is never rendered. */
export function ResetReferenceArt(){
  return <svg className="reset-reference-art" viewBox="0 74 1672 774" preserveAspectRatio="none" aria-hidden="true"><defs><clipPath id="reset-reference-sides"><rect x="0" y="74" width="490" height="774"/><rect x="1184" y="74" width="488" height="774"/></clipPath></defs><image href="/images/coco-reset-reference.png" x="0" y="0" width="1672" height="941" clipPath="url(#reset-reference-sides)"/></svg>;
}
