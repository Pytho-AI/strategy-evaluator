/* Entry-page loader.
 *
 * The supplied artifact was a single bundled file: its boot script rebuilt the
 * document from a JSON manifest and handed every resource to the page as a
 * blob: URL through `window.__resources`. That mechanism is gone. This file
 * does the one thing it was actually needed for — put the `<x-dc>` template and
 * the `class Component extends DCLogic` script into the document — reading them
 * as ordinary static files, then loads the vendored dc-runtime, which compiles
 * the template and mounts it exactly as before.
 *
 * P2 adds one step in front of that: `GET /api/meta` is read before the app
 * mounts, because the product name and the classification marking come from
 * the backend and nowhere else. If that call fails the page shows the error —
 * code, message and the API base it tried — instead of mounting an app that
 * would have nothing behind its numbers.
 *
 * dc-runtime boots itself on load: it reads `document.querySelector('x-dc')`
 * and `document.querySelector('script[data-dc-script]')`, so both must be in
 * place before its <script> is appended.
 */
(async function boot() {
  const text = async (url) => {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`${url}: HTTP ${res.status}`);
    return res.text();
  };

  const B = window.BRANDING;

  const fail = (heading, code, message) => {
    B.error = { code, message };
    const host = document.querySelector('x-dc');
    const box = document.createElement('div');
    box.id = 'boot-error';
    box.setAttribute('role', 'alert');
    box.innerHTML =
      '<h1></h1><p class="code"></p><p class="msg"></p>' +
      '<p class="hint">The workbench renders API responses only. It does not fall ' +
      'back to sample data. Start the API, then reload this page.</p>';
    box.querySelector('h1').textContent = heading;
    box.querySelector('.code').textContent = code;
    box.querySelector('.msg').textContent = message;
    if (host) host.replaceWith(box);
    else document.body.appendChild(box);
    const marking = document.getElementById('classification-marking');
    if (marking) marking.textContent = 'MARKING UNAVAILABLE — /api/meta failed';
  };

  let meta;
  try {
    meta = await window.API.getMeta();
  } catch (e) {
    fail(
      'Cannot reach the evaluation API',
      e.code || 'error',
      `${e.message} — API base ${window.API.base()}`
    );
    return;
  }

  window.API_META = meta;
  B.productName = meta.product_name;
  B.marking = meta.marking;
  document.title = `${B.productName} — ${B.title}`;
  const marking = document.getElementById('classification-marking');
  if (marking) marking.textContent = B.marking;

  const [markup, logic, props] = await Promise.all([
    text('./src/app.dc.html'),
    text('./src/app.logic.js'),
    text('./src/app.props.json'),
  ]);

  const host = document.querySelector('x-dc');
  host.innerHTML = markup;

  // type="text/x-dc" is never executed by the browser; dc-runtime reads its
  // textContent. data-props carries the editor-facing prop schema that
  // componentDidMount() reads (startView / startStep).
  const script = document.createElement('script');
  script.type = 'text/x-dc';
  script.setAttribute('data-dc-script', '');
  script.setAttribute('data-props', props);
  script.textContent = logic;
  host.after(script);

  await new Promise((resolve, reject) => {
    const el = document.createElement('script');
    el.src = './vendor/dc-runtime.js';
    el.onload = resolve;
    el.onerror = () => reject(new Error('failed to load ./vendor/dc-runtime.js'));
    document.head.appendChild(el);
  });
})();
