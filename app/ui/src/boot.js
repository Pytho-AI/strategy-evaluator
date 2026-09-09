/* Entry-page loader for the recovered artifact.
 *
 * The supplied bundle rebuilt the document from a JSON manifest and handed every
 * resource to the page as a blob: URL through `window.__resources`. That mechanism
 * is gone. This file does the one thing it was needed for: put the `<x-dc>` template
 * and the `class Component extends DCLogic` script into the document, reading them as
 * ordinary static files, then load the vendored dc-runtime, which compiles the
 * template and mounts it exactly as before.
 */
(async function boot() {
  const text = async (url) => {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`${url}: HTTP ${res.status}`);
    return res.text();
  };
  // Cache-busted: a redeployed build must never be shadowed by a cached script.
  // These are three small local files, so refetching them costs nothing.
  const v = "?v=" + Date.now();
  const [markup, logic, props] = await Promise.all([
    text("./src/app.dc.html" + v),
    text("./src/app.logic.js" + v),
    text("./src/app.props.json" + v).catch(() => "{}"),
  ]);
  // The API client is a module; the logic script is evaluated by dc-runtime as a
  // classic script and cannot `import`. Load it here and hand it over on `window`.
  window.WorkbenchApi = await import("./api.js" + v);
  const host = document.querySelector("x-dc");
  host.innerHTML = markup;
  try { host.setAttribute("props", props.trim()); } catch (_) {}
  const script = document.createElement("script");
  script.type = "text/x-dc";
  script.setAttribute("data-dc-script", "");
  script.textContent = logic;
  document.head.appendChild(script);
  const runtime = document.createElement("script");
  runtime.src = "./vendor/dc-runtime.js";
  document.head.appendChild(runtime);
})();
