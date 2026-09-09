/* The only place product/team naming lives.
 *
 * `app.dc.html` renders `{{ brandMark }}` and `{{ brandTitle }}`; `renderVals()`
 * in `app.logic.js` copies them off this object. Renaming the product therefore
 * never touches markup or logic.
 *
 * The values below are the strings the supplied artifact ships today. Only
 * `productName` and `classification` are new: the artifact contains no
 * occurrence of "Stratistics" (it exists only in the download filename) and no
 * classification marking at all.
 */
window.BRANDING = {
  productName: 'Stratistics',        // product name (placeholder, per handoff)
  teamName: 'Pytho',                 // project/team name
  teamMark: '【Pytho】',              // the team mark as drawn in the left nav
  title: 'Strategy Adjudicator',     // product title on the workflow header
  classification: 'UNCLASSIFIED — SYNTHETIC',
};
