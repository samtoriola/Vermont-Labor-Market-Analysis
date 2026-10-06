/**
 * PNG export for a panel's charts. Client-side only — the image is built in a
 * canvas in the browser and nothing leaves the page.
 *
 * Charts are inline SVG that leans on the document: colors are `var(--token)`,
 * text is styled by class, and the type comes from a web font. None of that
 * survives serialisation, because an SVG drawn into a canvas is rendered in
 * isolation with no access to the page's stylesheets, fonts, or custom
 * properties. So before serialising we copy the computed value of every property
 * that affects the drawing onto each node, and inline the font faces themselves.
 */

/* Properties that change what the drawing looks like. Computed values are read
   from the live node, which is what resolves var(--token) and the class rules. */
const PAINT = [
  'fill',
  'fill-opacity',
  'fill-rule',
  'stroke',
  'stroke-width',
  'stroke-opacity',
  'stroke-dasharray',
  'stroke-linecap',
  'stroke-linejoin',
  'paint-order',
  'opacity',
  'font-family',
  'font-size',
  'font-weight',
  'font-style',
  'font-variant-numeric',
  'letter-spacing',
  'text-anchor',
  'dominant-baseline',
  'display',
  'visibility',
];

/* The faces the charts actually draw with. Asking for fewer weights keeps the
   embedded payload small; anything not listed falls back to the system stack. */
const FONT_CSS_URL =
  'https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&display=swap';

let fontCssPromise = null;

/** Reads a blob as a data URL. */
function asDataUrl(blob) {
  return new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(r.result);
    r.onerror = () => reject(new Error('font read failed'));
    r.readAsDataURL(blob);
  });
}

/**
 * Builds @font-face rules with the font binary inlined, so serialised SVG draws
 * in DM Sans rather than falling back to a system face.
 *
 * Only the Latin subset is kept. Google returns one face per unicode range, and
 * embedding all of them would add several hundred kilobytes of base64 to every
 * export for glyphs these charts never use.
 *
 * Resolves to '' if anything fails. A PNG in the fallback face is a worse export
 * than one in DM Sans, but it is far better than no export at all, so this never
 * rejects.
 */
function embeddedFontCss() {
  if (fontCssPromise) return fontCssPromise;
  fontCssPromise = (async () => {
    try {
      const css = await (await fetch(FONT_CSS_URL)).text();
      const faces = css.split('@font-face').slice(1);
      const latin = faces.filter(
        (f) => !/unicode-range:/.test(f) || /U\+0000-00FF/i.test(f)
      );
      const out = [];
      for (const face of latin) {
        const m = face.match(/src:\s*url\((https:\/\/[^)]+)\)\s*format\('([^']+)'\)/);
        if (!m) continue;
        const weight = (face.match(/font-weight:\s*([^;]+);/) || [])[1] || '400';
        const style = (face.match(/font-style:\s*([^;]+);/) || [])[1] || 'normal';
        const data = await asDataUrl(await (await fetch(m[1])).blob());
        out.push(
          `@font-face{font-family:'DM Sans';font-style:${style.trim()};` +
            `font-weight:${weight.trim()};src:url(${data}) format('${m[2]}');}`
        );
      }
      return out.join('');
    } catch (e) {
      return '';
    }
  })();
  return fontCssPromise;
}

/**
 * Copies computed paint and type onto a clone. The clone is a deep copy, so the
 * two trees have the same nodes in the same order and can be walked in step.
 */
function inlineComputedStyle(live, clone) {
  const a = [live].concat(Array.from(live.querySelectorAll('*')));
  const b = [clone].concat(Array.from(clone.querySelectorAll('*')));
  for (let i = 0; i < a.length; i += 1) {
    const cs = window.getComputedStyle(a[i]);
    let decl = '';
    for (const prop of PAINT) {
      const v = cs.getPropertyValue(prop);
      if (v && v !== 'normal' && v !== 'none' && v !== 'auto') decl += `${prop}:${v};`;
      // `none` is meaningful for fill and stroke, where it means "do not paint".
      else if (v === 'none' && (prop === 'fill' || prop === 'stroke')) decl += `${prop}:none;`;
    }
    b[i].setAttribute('style', decl);
    // Class names refer to stylesheets the serialised copy cannot see, and the
    // values they carried are now inline.
    b[i].removeAttribute('class');
  }
}

/** One SVG, as an <img> sized the way it is laid out on the page. */
async function svgImage(svg, fontCss) {
  const rect = svg.getBoundingClientRect();
  const vb = svg.viewBox.baseVal;
  const w = Math.round(rect.width) || vb.width || 600;
  const h = Math.round(rect.height) || vb.height || 300;

  const clone = svg.cloneNode(true);
  inlineComputedStyle(svg, clone);
  clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
  clone.setAttribute('width', String(w));
  clone.setAttribute('height', String(h));
  if (vb.width) clone.setAttribute('viewBox', `0 0 ${vb.width} ${vb.height}`);

  if (fontCss) {
    const style = document.createElementNS('http://www.w3.org/2000/svg', 'style');
    style.textContent = fontCss;
    clone.insertBefore(style, clone.firstChild);
  }

  const markup = new XMLSerializer().serializeToString(clone);
  // encodeURIComponent rather than btoa: the labels carry ×, — and $ and btoa
  // throws on anything outside Latin-1.
  const url = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(markup)}`;

  const img = new Image();
  img.decoding = 'sync';
  await new Promise((resolve, reject) => {
    img.onload = resolve;
    img.onerror = () => reject(new Error('svg render failed'));
    img.src = url;
  });
  return { img, w, h };
}

function css(token) {
  return window.getComputedStyle(document.documentElement).getPropertyValue(token).trim();
}

/** Wraps text to a pixel width using the canvas' own measurement. */
function wrap(ctx, text, maxW) {
  const words = String(text).split(/\s+/);
  const lines = [];
  let line = '';
  for (const word of words) {
    const next = line ? `${line} ${word}` : word;
    if (ctx.measureText(next).width > maxW && line) {
      lines.push(line);
      line = word;
    } else {
      line = next;
    }
  }
  if (line) lines.push(line);
  return lines;
}

/**
 * Renders a panel's charts to a PNG and downloads it.
 *
 * The title and the source line are drawn onto the canvas rather than captured
 * from the DOM, so the image carries what it is and where it came from. These
 * exports get pasted into decks, where a chart that has been separated from its
 * caption is a chart nobody can source.
 *
 * Returns false if there was nothing to draw or the browser refused the canvas,
 * so the caller can leave the page alone rather than surface an exception.
 */
export async function downloadPanelPng(panel, { title, note, src, filename, scale = 2 }) {
  if (!panel) return false;
  const svgs = Array.from(panel.querySelectorAll('svg.chart')).filter(
    (s) => s.getBoundingClientRect().width > 0
  );
  if (!svgs.length) return false;

  try {
    const fontCss = await embeddedFontCss();
    const parts = [];
    for (const svg of svgs) parts.push(await svgImage(svg, fontCss));

    const pad = 20;
    const gap = 10;
    const body = Math.max(...parts.map((p) => p.w));
    const width = body + pad * 2;

    // Measured against a scratch context, because the heights depend on how the
    // title and source wrap at this width.
    const probe = document.createElement('canvas').getContext('2d');
    const sans = "600 15px 'DM Sans', system-ui, sans-serif";
    probe.font = sans;
    const titleLines = title ? wrap(probe, title, body) : [];
    probe.font = "400 13px 'DM Sans', system-ui, sans-serif";
    const noteLines = note ? wrap(probe, note, body - 24) : [];
    probe.font = "400 11px 'DM Sans', system-ui, sans-serif";
    const srcLines = src ? wrap(probe, src, body) : [];

    const titleH = titleLines.length ? titleLines.length * 20 + 10 : 0;
    const noteH = noteLines.length ? noteLines.length * 18 + 26 : 0;
    const srcH = srcLines.length ? srcLines.length * 15 + 10 : 0;
    const chartsH = parts.reduce((t, p) => t + p.h, 0) + gap * (parts.length - 1);
    const height = pad * 2 + titleH + chartsH + noteH + srcH;

    const canvas = document.createElement('canvas');
    canvas.width = Math.round(width * scale);
    canvas.height = Math.round(height * scale);
    const ctx = canvas.getContext('2d');
    ctx.scale(scale, scale);

    // Opaque, and in the panel's own color, so the PNG works on any slide
    // background instead of coming out transparent.
    ctx.fillStyle = css('--panel') || '#ffffff';
    ctx.fillRect(0, 0, width, height);

    let y = pad;
    if (titleLines.length) {
      ctx.fillStyle = css('--ink') || '#1c252d';
      ctx.font = sans;
      ctx.textBaseline = 'top';
      for (const line of titleLines) {
        ctx.fillText(line, pad, y);
        y += 20;
      }
      y += 10;
    }

    for (const part of parts) {
      ctx.drawImage(part.img, pad, y, part.w, part.h);
      y += part.h + gap;
    }
    y -= gap;

    // The computed read-out, drawn with the same rule down its left edge it has on
    // the page. An exported chart that leaves it behind loses the one line saying
    // what the chart is evidence of.
    if (noteLines.length) {
      y += 14;
      const boxH = noteLines.length * 18 + 14;
      ctx.fillStyle = css('--panel-2') || '#f5f6f7';
      ctx.fillRect(pad, y, body, boxH);
      ctx.fillStyle = css('--accent') || '#009ba5';
      ctx.fillRect(pad, y, 2, boxH);
      ctx.fillStyle = css('--ink') || '#1c252d';
      ctx.font = "400 13px 'DM Sans', system-ui, sans-serif";
      let ny = y + 7;
      for (const line of noteLines) {
        ctx.fillText(line, pad + 12, ny);
        ny += 18;
      }
      y += boxH;
    }

    if (srcLines.length) {
      y += 10;
      ctx.fillStyle = css('--ink-3') || '#777c81';
      ctx.font = "400 11px 'DM Sans', system-ui, sans-serif";
      for (const line of srcLines) {
        ctx.fillText(line, pad, y);
        y += 15;
      }
    }

    const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/png'));
    if (!blob) return false;
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename.endsWith('.png') ? filename : `${filename}.png`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 0);
    return true;
  } catch (e) {
    return false;
  }
}
