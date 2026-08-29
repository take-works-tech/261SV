/* Missing-data style (11_ui.md): the one way an absent value looks, everywhere.
 * Stated, with its reason - a blank reads as zero to some readers and "not applicable" to others,
 * and it is neither (XC-001). One implementation, so the style cannot drift between screens. */

export function MissingDataStyle(props: { because: string }) {
  return <span className="missing-value">値なし（{props.because}）</span>;
}
