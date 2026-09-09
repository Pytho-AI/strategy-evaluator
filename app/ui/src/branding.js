/* Branding holder. It carries no product identity of its own.
 *
 * `productName` and `marking` have exactly one source: `GET /api/meta`
 * (`app/backend/branding.py`). `boot.js` fills them in before the app mounts
 * and shows a visible error instead of the app if `/api/meta` fails — the UI
 * never invents a product name or a classification marking.
 *
 * `teamMark` and `title` are the two chrome strings the recovered artifact
 * draws in the command bar and workflow header. They are not product identity
 * and the API does not serve them; they stay here so a rename still touches
 * one file only.
 */
window.BRANDING = {
  productName: null,                 // from /api/meta product_name
  marking: null,                     // from /api/meta marking
  teamName: 'Pytho',                 // project/team name
  teamMark: '【Pytho】',              // the team mark in the command bar
  title: 'Strategy Adjudicator',     // product title on the workflow header
  error: null,                       // {code, message} when /api/meta failed
};
