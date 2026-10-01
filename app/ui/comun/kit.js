/* Kit común de los programas Depor — utilidades, íconos, sheets, toast, menús y ventana */
'use strict';

const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const miles = n => Number(n || 0).toLocaleString('es-CL');
const clone = o => JSON.parse(JSON.stringify(o));
const cap = t => t ? t[0].toUpperCase() + t.slice(1) : '';

const ICONS = {
  files: '<path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5z"/><path d="M14 2v6h6M8 13h8M8 17h5"/>',
  columns: '<rect x="3" y="3" width="18" height="18" rx="3"/><path d="M9 3v18M15 3v18"/>',
  upload: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12"/>',
  download: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  x: '<path d="M18 6 6 18M6 6l12 12"/>',
  check: '<path d="M20 6 9 17l-5-5"/>',
  alert: '<path d="M12 8v5M12 16.5h.01"/>',
  warn: '<path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0zM12 9v4M12 17h.01"/>',
  info: '<path d="M12 11v5M12 7.5h.01"/>',
  minus: '<path d="M6 12h12"/>',
  chevL: '<path d="m15 18-6-6 6-6"/>',
  chevR: '<path d="m9 18 6-6-6-6"/>',
  up: '<path d="m18 15-6-6-6 6"/>',
  down: '<path d="m6 9 6 6 6-6"/>',
  folder: '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
  refresh: '<path d="M21 12a9 9 0 1 1-2.64-6.36L21 8"/><path d="M21 3v5h-5"/>',
  trash: '<path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>',
  more: '<circle cx="5" cy="12" r="1.2"/><circle cx="12" cy="12" r="1.2"/><circle cx="19" cy="12" r="1.2"/>',
  edit: '<path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4z"/>',
};
const icon = (name, cls = '') => `<svg class="i ${cls}" viewBox="0 0 24 24" aria-hidden="true">${ICONS[name] || ''}</svg>`;
const grad = c => `linear-gradient(160deg, color-mix(in srgb,${c} 78%,#fff), ${c} 45%, color-mix(in srgb,${c} 70%,#000))`;

let api = null;
const actions = {
  'close-sheet': () => closeSheet(),
  'confirm-sheet': () => $('#sheet-root')._onConfirm?.(),
};

const field = (label, input, cls = '') => `<div class="field ${cls}"><label>${label}</label>${input}</div>`;
const sw = (name, on, label) => `<label class="switch"><input type="checkbox" name="${name}" ${on ? 'checked' : ''} aria-label="${label}"><span class="track"></span><span class="thumb"></span></label>`;
const selectHtml = (name, value, options) => `<select name="${name}">${options.map(([v, l]) => `<option value="${esc(v)}" ${String(v) === String(value) ? 'selected' : ''}>${esc(l)}</option>`).join('')}</select>`;

function confirmSheet({ title, text, label, danger = false, onConfirm }) {
  openSheet({
    title, noConfirm: true, small: true, onConfirm,
    body: `<p class="sheet-text">${esc(text)}</p>
      <div class="sheet-buttons"><button class="btn-glass" data-action="close-sheet">Cancelar</button>
      <button class="btn-glass btn-tinted ${danger ? 'danger' : ''}" data-action="confirm-sheet">${esc(label)}</button></div>`,
  });
}

function moveIndicator() {
  const on = $('.tab.on'), ind = $('.tab-indicator');
  if (on && ind) { ind.style.width = `${on.offsetWidth}px`; ind.style.transform = `translateX(${on.offsetLeft - 5}px)`; }
}

/** Crea los botones de la tab bar flotante. tabs: [{id, label, icon}] */
function buildTabbar(tabs) {
  $('.tabbar').insertAdjacentHTML('beforeend', tabs.map(t =>
    `<button class="tab" role="tab" data-action="go" data-view="${t.id}" aria-label="${t.label}">${icon(t.icon)}<span>${t.label}</span></button>`).join(''));
}

/** Ejecuta una acción del backend mostrando estado y errores de forma clara. */
async function runBusy(el, label, fn) {
  const original = el?.innerHTML;
  if (el) { el.disabled = true; el.innerHTML = `<span class="spinner"></span>${label}`; }
  try { return await fn(); }
  catch (e) { toast(String(e?.message || e).replace(/^.*?Error: /, '')); return undefined; }
  finally { if (el?.isConnected) { el.disabled = false; el.innerHTML = original; } }
}

/* ───────────── Sheets ───────────── */
function openSheet({ title, body, onConfirm, noConfirm = false, small = false, wide = false }) {
  closeSheet(true);
  const root = $('#sheet-root');
  root.innerHTML = `<div class="scrim" data-scrim>
    <div class="sheet glass ${small ? 'small' : wide ? 'wide' : ''}" role="dialog" aria-modal="true" aria-label="${esc(title)}">
      <div class="sheet-head">
        <button class="round-btn" data-action="close-sheet" aria-label="Cancelar">${icon('x')}</button>
        <h3>${esc(title)}</h3>
        ${noConfirm ? '<span></span>' : `<button class="round-btn confirm right" data-action="confirm-sheet" aria-label="Guardar">${icon('check')}</button>`}
      </div>
      <div class="sheet-body">${body}</div>
    </div></div>`;
  root._onConfirm = onConfirm;
  const scrim = $('[data-scrim]', root);
  scrim.addEventListener('mousedown', e => { if (e.target === scrim) closeSheet(); });
  setTimeout(() => { const f = $('.sheet input:not([type=hidden]):not([type=checkbox]), .sheet .btn-tinted', root); f && f.focus(); }, 60);
}
function closeSheet(instant = false) {
  closeSelectMenu();
  const root = $('#sheet-root'), scrim = $('[data-scrim]', root);
  if (!scrim) return;
  root._onConfirm = null;
  if (instant) { root.innerHTML = ''; return; }
  scrim.classList.add('closing');
  setTimeout(() => { if (scrim.isConnected) root.innerHTML = ''; }, 220);
}
function readForm(el) {
  const o = {};
  $$('input[name], select[name], textarea[name]', el).forEach(i => { o[i.name] = i.type === 'checkbox' ? i.checked : i.value; });
  return o;
}

let toastTimer;
/** Aviso breve. Con `undo` muestra un botón (por defecto «Deshacer»; `etiqueta` lo cambia, ej. «Mostrar»). */
function toast(msg, undo, etiqueta = 'Deshacer') {
  $('.toast')?.remove();
  const el = document.createElement('div');
  el.className = 'toast glass'; el.setAttribute('role', 'status');
  el.innerHTML = `<span>${esc(msg)}</span>${undo ? `<button class="undo">${esc(etiqueta)}</button>` : ''}`;
  if (undo) $('.undo', el).addEventListener('click', () => { el.remove(); undo(); });
  document.body.appendChild(el);
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.remove(), undo ? 5000 : 2800);
}

/* ───────────── Eventos ───────────── */
document.addEventListener('click', e => {
  const w = e.target.closest('[data-win]');
  if (w) { if (api) ({ min: () => api.win_minimize(), max: () => api.win_toggle_max(), close: () => (typeof window.antesDeCerrar === 'function' ? window.antesDeCerrar(() => api.win_close()) : api.win_close()) })[w.dataset.win](); return; }
  const el = e.target.closest('[data-action]');
  if (el && !el.disabled && actions[el.dataset.action]) actions[el.dataset.action](el);
});
document.addEventListener('change', e => { if (e.target.dataset.change && typeof onChange === 'function') onChange(e.target); });
document.addEventListener('keydown', e => {
  if (e.key === 'Escape' && $('[data-scrim]')) closeSheet();
  if (e.key === 'Enter' && e.target.matches('[role=button][data-action]')) e.target.click();
  if (e.key === 'Enter' && e.target.matches('.sheet input:not([type=checkbox])')) actions['confirm-sheet']();
});
window.addEventListener('resize', moveIndicator);

// barra de título propia (ventana sin marco)
document.addEventListener('mousedown', e => {
  if (e.button !== 0 || !api?.win_drag || !e.target.closest('#titlebar') || e.target.closest('.win-btn') || e.detail >= 2) return;
  api.win_drag();
});
document.addEventListener('dblclick', e => { if (api && e.target.closest('#titlebar') && !e.target.closest('.win-btn')) api.win_toggle_max(); });
window.onWindowState = ({ state }) => { document.documentElement.dataset.window = state; };

/* ───────────── Menú desplegable estilo iOS (reemplaza el popup nativo de <select>) ───────────── */
let selectMenu = null;
function closeSelectMenu(refocus = false) {
  if (!selectMenu) return;
  const { el, select } = selectMenu;
  selectMenu = null;
  select.classList.remove('menu-open');
  select.setAttribute('aria-expanded', 'false');
  el.classList.add('closing');
  setTimeout(() => el.remove(), 140);
  if (refocus && select.isConnected) select.focus({ preventScroll: true });
}
function openSelectMenu(select) {
  closeSelectMenu();
  if (typeof closePopover === 'function') closePopover();
  const options = [...select.options];
  const el = document.createElement('div');
  el.className = 'select-menu glass';
  el.setAttribute('role', 'listbox');
  el.setAttribute('aria-label', select.getAttribute('aria-label') || select.closest('.field')?.querySelector('label')?.textContent || 'Opciones');
  const buscable = 'buscable' in select.dataset || options.length > 12;
  el.innerHTML = (buscable ? `<div class="sm-search-wrap"><input class="sm-search" type="search" placeholder="Escribe para buscar…" aria-label="Buscar opción" autocomplete="off"></div>` : '') +
    options.map((o, i) => `<button type="button" role="option" class="sm-item ${o.selected ? 'on' : ''}" data-i="${i}" aria-selected="${o.selected}" ${o.disabled ? 'disabled' : ''}>
      <span class="sm-check">${o.selected ? icon('check') : ''}</span><span class="sm-label">${esc(o.textContent)}</span></button>`).join('');
  if (select.classList.contains('pick')) el.style.maxWidth = 'min(520px, calc(100vw - 24px))';
  document.body.appendChild(el);

  const r = select.getBoundingClientRect();
  const w = el.offsetWidth, h = el.offsetHeight;
  const left = Math.min(Math.max(12, r.right - w), innerWidth - w - 12);
  let top = r.bottom + 6, below = true;
  if (top + h > innerHeight - 12 && r.top - h - 6 > 12) { top = r.top - h - 6; below = false; }
  else if (top + h > innerHeight - 12) top = Math.max(12, innerHeight - h - 12);
  el.style.left = `${left}px`;
  el.style.top = `${Math.max(12, top)}px`;
  el.style.transformOrigin = `${below ? 'top' : 'bottom'} right`;

  selectMenu = { el, select, openedAt: performance.now() };
  select.classList.add('menu-open');
  select.setAttribute('aria-expanded', 'true');
  const current = el.querySelector('.sm-item.on') || el.querySelector('.sm-item:not([disabled])');
  if (current) el.scrollTop = Math.max(0, current.offsetTop - el.clientHeight / 2);
  const buscador = el.querySelector('.sm-search');
  if (buscador) {
    buscador.focus({ preventScroll: true });
    const sinAcentos = t => t.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    buscador.addEventListener('input', () => {
      const q = sinAcentos(buscador.value.trim());
      el.querySelectorAll('.sm-item').forEach(b => { b.hidden = q && !sinAcentos(b.textContent).includes(q); });
    });
  } else {
    current?.focus({ preventScroll: true });
  }

  el.addEventListener('click', e => {
    const item = e.target.closest('.sm-item');
    if (!item || item.disabled) return;
    const i = Number(item.dataset.i);
    if (select.selectedIndex !== i) {
      select.selectedIndex = i;
      select.dispatchEvent(new Event('input', { bubbles: true }));
      select.dispatchEvent(new Event('change', { bubbles: true }));
    }
    closeSelectMenu(true);
  });
}
document.addEventListener('mousedown', e => {
  const select = e.target.closest('select');
  if (select && !select.disabled) {
    e.preventDefault(); // evita el popup nativo de Windows
    if (selectMenu?.select === select) closeSelectMenu(true);
    else { select.focus({ preventScroll: true }); openSelectMenu(select); }
    return;
  }
  if (selectMenu && !e.target.closest('.select-menu')) closeSelectMenu();
}, true);
document.addEventListener('keydown', e => {
  if (selectMenu) {
    const items = [...selectMenu.el.querySelectorAll('.sm-item:not([disabled]):not([hidden])')];
    if (e.target.matches?.('.sm-search')) {   // escribiendo en el buscador del menú
      if (e.key === 'ArrowDown') { e.preventDefault(); e.stopPropagation(); items[0]?.focus(); }
      else if (e.key === 'Enter') { e.preventDefault(); e.stopPropagation(); items[0]?.click(); }
      else if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); closeSelectMenu(true); }
      else if (e.key === 'Tab') closeSelectMenu(true);
      return;
    }
    const idx = items.indexOf(document.activeElement);
    const move = d => { e.preventDefault(); e.stopPropagation(); items[(idx + d + items.length) % items.length]?.focus(); };
    if (e.key === 'ArrowDown') return move(1);
    if (e.key === 'ArrowUp') return move(-1);
    if (e.key === 'Home') return move(-idx);
    if (e.key === 'End') return move(items.length - 1 - idx);
    if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); return closeSelectMenu(true); }
    if (e.key === 'Tab') return closeSelectMenu(true);
    const buscador = selectMenu.el.querySelector('.sm-search');
    if (buscador && e.key.length === 1 && !e.ctrlKey) { buscador.focus(); return; }
    if (/^[\wáéíóúñ]$/i.test(e.key)) {
      const hit = items.find(b => b.textContent.trim().toLowerCase().startsWith(e.key.toLowerCase()));
      if (hit) { e.preventDefault(); hit.focus(); }
    }
    return;
  }
  const select = e.target.closest?.('select');
  if (select && ['ArrowDown', 'ArrowUp', 'Enter', ' '].includes(e.key)) {
    e.preventDefault(); e.stopPropagation();
    openSelectMenu(select);
  }
}, true);
const menuSettled = () => selectMenu && performance.now() - selectMenu.openedAt > 400;
document.addEventListener('scroll', e => { if (menuSettled() && !selectMenu.el.contains(e.target)) closeSelectMenu(); }, true);
window.addEventListener('resize', () => { if (menuSettled()) closeSelectMenu(); });
window.addEventListener('blur', () => { if (menuSettled()) closeSelectMenu(); });

/* ───────────── Conexión con Python ───────────── */
/**
 * Llama a boot() cuando la API de Python está lista.
 * Con #dev en la URL usa un servidor de prueba que responde /api/<método> (para revisar en el navegador).
 */
function conectar(boot) {
  let listo = false;
  const go = () => { if (!listo) { listo = true; boot(); } };
  if (location.hash.includes('dev')) {
    document.documentElement.classList.toggle('demo-static', location.hash.includes('static'));
    api = new Proxy({}, { get: (_, m) => (...args) => fetch(`/api/${m}`, { method: 'POST', body: JSON.stringify(args) }).then(r => r.json()) });
    // los avisos que Python manda con push_js llegan por /api/__eventos
    setInterval(async () => {
      for (const [fn, payload] of await api.__eventos()) window[fn]?.(payload);
    }, 250);
    go();
  } else if (window.pywebview?.api?.win_drag) {
    api = window.pywebview.api; go();
  } else {
    window.addEventListener('pywebviewready', () => { api = window.pywebview.api; go(); });
  }
}

/* ───────────── Registro en vivo, progreso y rutas ───────────── */
/** Agrega una línea al <pre id="log" class="console">. tipo: ok | error | aviso | titulo */
function logLine(texto, tipo = '') {
  const c = $('#log');
  if (!c) return;
  const abajo = c.scrollHeight - c.scrollTop - c.clientHeight < 40;
  c.insertAdjacentHTML('beforeend', `<span class="${tipo}">${esc(texto)}</span>\n`);
  if (abajo) c.scrollTop = c.scrollHeight;
}
function logClear() { const c = $('#log'); if (c) c.innerHTML = ''; }
window.onLog = ({ texto, tipo }) => logLine(texto, tipo);

/** Barra de progreso: <div id="progreso" class="progress"><span></span></div> + <div id="progreso-txt"> */
function setProgreso(valor, total = 100, texto = '') {
  const p = $('#progreso');
  if (p) { p.hidden = false; $('span', p).style.width = `${total ? Math.min(100, valor * 100 / total) : 0}%`; }
  const t = $('#progreso-txt');
  if (t) t.textContent = texto;
}
window.onProgreso = ({ valor, total, texto }) => setProgreso(valor, total, texto);

/** Fila de formulario con una ruta y botón «Elegir…». La acción recibe el botón (dataset.campo). */
function pathField(label, campo, valor, accion = 'elegir-ruta', placeholder = 'Sin elegir') {
  return `<div class="field path-field"><label>${esc(label)}</label>
    <span class="path ${valor ? '' : 'vacio'}" title="${esc(valor || '')}">${esc(valor || placeholder)}</span>
    <button class="btn-plain" data-action="${accion}" data-campo="${esc(campo)}">Elegir…</button></div>`;
}

/** Tabla simple con encabezado. cols: [{k, t, num?}], filas: objetos. */
function tablaHtml(cols, filas, { vacio = 'Sin datos', maxFilas = 2000, onRow = '' } = {}) {
  if (!filas.length) return `<div class="empty-inline">${esc(vacio)}</div>`;
  const cuerpo = filas.slice(0, maxFilas).map((f, i) => `<tr ${onRow ? `data-action="${onRow}" data-i="${i}" tabindex="0"` : ''}>${cols.map(c =>
    `<td class="${c.num ? 'num' : ''}" title="${esc(f[c.k] ?? '')}">${esc(f[c.k] ?? '')}</td>`).join('')}</tr>`).join('');
  return `<div class="preview glass"><div class="preview-scroll"><table class="tabla">
    <thead><tr>${cols.map(c => `<th class="${c.num ? 'num' : ''}">${esc(c.t)}</th>`).join('')}</tr></thead>
    <tbody>${cuerpo}</tbody></table></div></div>
    ${filas.length > maxFilas ? `<p class="help">Se muestran ${miles(maxFilas)} de ${miles(filas.length)} filas.</p>` : ''}`;
}

/** Copia texto al portapapeles (con respaldo para navegadores sin permiso). */
async function copiarTexto(texto) {
  try { await navigator.clipboard.writeText(texto); return true; } catch { /* respaldo abajo */ }
  const t = document.createElement('textarea');
  t.value = texto; t.style.position = 'fixed'; t.style.opacity = '0';
  document.body.appendChild(t); t.select();
  const ok = document.execCommand('copy');
  t.remove();
  return ok;
}


/* ───────────── Fechas ───────────── */
const MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];
const MESES_LARGOS = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
const DIAS_SEMANA = ['LUN', 'MAR', 'MIÉ', 'JUE', 'VIE', 'SÁB', 'DOM'];
const hoy = () => { const d = new Date(); return new Date(d.getFullYear(), d.getMonth(), d.getDate()); };
const iso = d => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
const parseISO = s => { const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(s || ''); return m ? new Date(+m[1], m[2] - 1, +m[3]) : null; };
const diasDelMes = (y, m) => new Date(y, m + 1, 0).getDate();
const sumarDias = (d, n) => new Date(d.getFullYear(), d.getMonth(), d.getDate() + n);
const fechaCorta = d => `${String(d.getDate()).padStart(2, '0')}-${String(d.getMonth() + 1).padStart(2, '0')}-${d.getFullYear()}`;

/* ───────────── Popovers de vidrio ───────────── */
let popover = null; // { el, anchor, onKey }
function closePopover(refocus = false) {
  if (!popover) return;
  const { el, anchor } = popover;
  popover = null;
  anchor.classList.remove('pop-open');
  anchor.setAttribute('aria-expanded', 'false');
  el.classList.add('closing');
  setTimeout(() => el.remove(), 140);
  if (refocus && anchor.isConnected) anchor.focus({ preventScroll: true });
}
function placePopover(el, anchor) {
  const r = anchor.getBoundingClientRect();
  const w = el.offsetWidth, h = el.offsetHeight;
  const left = Math.min(Math.max(12, r.right - w), innerWidth - w - 12);
  let top = r.bottom + 8, below = true;
  if (top + h > innerHeight - 12 && r.top - h - 8 > 12) { top = r.top - h - 8; below = false; }
  else if (top + h > innerHeight - 12) top = Math.max(12, innerHeight - h - 12);
  el.style.left = `${left}px`;
  el.style.top = `${top}px`;
  el.style.transformOrigin = `${below ? 'top' : 'bottom'} right`;
}
function openPopover(anchor, el, onKey) {
  closePopover(); closeSelectMenu();
  document.body.appendChild(el);
  placePopover(el, anchor);
  anchor.classList.add('pop-open');
  anchor.setAttribute('aria-expanded', 'true');
  popover = { el, anchor, onKey, openedAt: performance.now() };
}
document.addEventListener('mousedown', e => {
  if (popover && !popover.el.contains(e.target) && !popover.anchor.contains(e.target)) closePopover();
}, true);
document.addEventListener('keydown', e => {
  if (!popover) return;
  if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); closePopover(true); return; }
  popover.onKey?.(e);
}, true);
document.addEventListener('scroll', e => {
  if (popover && !popover.el.contains(e.target) && performance.now() - popover.openedAt > 300) closePopover();
}, true);
const popoverSettled = () => popover && performance.now() - popover.openedAt > 400;
window.addEventListener('resize', () => { if (popoverSettled()) closePopover(); else if (popover) placePopover(popover.el, popover.anchor); });
window.addEventListener('blur', () => { if (popoverSettled()) closePopover(); });

function emitInput(input) {
  input.dispatchEvent(new Event('input', { bubbles: true }));
  input.dispatchEvent(new Event('change', { bubbles: true }));
}

/** Convierte cada <input type="date"> en un botón con calendario iOS (el valor sigue en el input, ISO). */
function enhanceControls(root = document) {
  $$('input[type=date]', root).forEach(input => {
    const pill = document.createElement('button');
    pill.type = 'button';
    pill.className = 'date-pill';
    pill.setAttribute('aria-haspopup', 'dialog');
    pill._input = input;
    pill._optional = !input.required;
    input.type = 'hidden';
    input.classList.add('date-value');
    input.after(pill);
    paintDatePill(pill);
    pill.addEventListener('click', () => (popover?.anchor === pill ? closePopover(true) : openDatePicker(pill)));
  });
}
// se aplica solo a todo lo que se dibuje
new MutationObserver(muts => {
  if (muts.some(m => [...m.addedNodes].some(n => n.nodeType === 1 && (n.matches?.('input[type=date]') || n.querySelector?.('input[type=date]'))))) enhanceControls();
}).observe(document.documentElement, { childList: true, subtree: true });

function paintDatePill(pill) {
  const d = parseISO(pill._input.value);
  pill.classList.toggle('empty', !d);
  pill.textContent = d ? `${d.getDate()} ${MESES[d.getMonth()]} ${d.getFullYear()}` : 'Sin fecha';
  const label = pill.closest('.field')?.querySelector('label')?.textContent || pill._input.getAttribute('aria-label') || 'Fecha';
  pill.setAttribute('aria-label', `${label}: ${d ? d.toLocaleDateString('es-CL', { dateStyle: 'long' }) : 'sin fecha'}`);
}
/** Cambia por código el valor de una fecha mejorada (y repinta su botón). */
function setFecha(input, valorIso) {
  input.value = valorIso || '';
  const pill = input.nextElementSibling;
  if (pill?._input === input) paintDatePill(pill);
}
function openDatePicker(pill) {
  const selected = parseISO(pill._input.value);
  let focus = selected || hoy();
  let month = new Date(focus.getFullYear(), focus.getMonth(), 1);
  let mode = 'days';
  const el = document.createElement('div');
  el.className = 'date-pop glass';
  el.setAttribute('role', 'dialog');
  el.setAttribute('aria-label', 'Elegir fecha');

  const choose = d => {
    pill._input.value = d ? iso(d) : '';
    paintDatePill(pill);
    emitInput(pill._input);
    closePopover(true);
  };
  const draw = (focusGrid = false) => {
    const t = hoy();
    const sel = parseISO(pill._input.value);
    let body;
    if (mode === 'days') {
      const lead = (month.getDay() + 6) % 7;
      const n = diasDelMes(month.getFullYear(), month.getMonth());
      let cells = '<span></span>'.repeat(lead);
      for (let day = 1; day <= n; day++) {
        const d = new Date(month.getFullYear(), month.getMonth(), day);
        const k = iso(d);
        const cls = [k === iso(t) && 'today', sel && k === iso(sel) && 'sel'].filter(Boolean).join(' ');
        cells += `<button type="button" class="dp-day ${cls}" data-date="${k}" tabindex="${k === iso(focus) ? 0 : -1}"
          aria-label="${d.toLocaleDateString('es-CL', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}">${day}</button>`;
      }
      body = `<div class="dp-grid">${DIAS_SEMANA.map(d => `<span class="dp-dow" aria-hidden="true">${d}</span>`).join('')}${cells}</div>`;
    } else {
      body = `<div class="dp-months">${MESES_LARGOS.map((m, i) => {
        const on = i === month.getMonth();
        return `<button type="button" class="dp-month ${on ? 'sel' : ''}" data-month="${i}" tabindex="${on ? 0 : -1}">${cap(m.slice(0, 3))}</button>`;
      }).join('')}</div>`;
    }
    el.innerHTML = `
      <div class="dp-head">
        <button type="button" class="dp-title" data-dp="mode" aria-expanded="${mode === 'months'}">
          ${mode === 'days' ? `${cap(MESES_LARGOS[month.getMonth()])} ${month.getFullYear()}` : month.getFullYear()}
          <span class="dp-chev ${mode === 'months' ? 'open' : ''}">${icon('chevR')}</span></button>
        <div class="dp-nav">
          <button type="button" data-dp="prev" aria-label="${mode === 'days' ? 'Mes anterior' : 'Año anterior'}">${icon('chevL')}</button>
          <button type="button" data-dp="next" aria-label="${mode === 'days' ? 'Mes siguiente' : 'Año siguiente'}">${icon('chevR')}</button>
        </div>
      </div>
      ${body}
      <div class="dp-foot">
        <button type="button" class="btn-plain" data-dp="today">Hoy</button>
        ${pill._optional && sel ? '<button type="button" class="btn-plain btn-danger" data-dp="clear">Quitar fecha</button>' : ''}
      </div>`;
    if (focusGrid) el.querySelector('.dp-day[tabindex="0"], .dp-month[tabindex="0"]')?.focus({ preventScroll: true });
  };
  const shiftMonth = delta => {
    month = new Date(month.getFullYear(), month.getMonth() + delta, 1);
    focus = new Date(month.getFullYear(), month.getMonth(), Math.min(focus.getDate(), diasDelMes(month.getFullYear(), month.getMonth())));
  };
  el.addEventListener('click', e => {
    const b = e.target.closest('button');
    if (!b) return;
    if (b.dataset.date) return choose(parseISO(b.dataset.date));
    if (b.dataset.month) { month = new Date(month.getFullYear(), Number(b.dataset.month), 1); shiftMonth(0); mode = 'days'; return draw(true); }
    switch (b.dataset.dp) {
      case 'mode': mode = mode === 'days' ? 'months' : 'days'; return draw();
      case 'prev': shiftMonth(mode === 'days' ? -1 : -12); return draw();
      case 'next': shiftMonth(mode === 'days' ? 1 : 12); return draw();
      case 'today': return choose(hoy());
      case 'clear': return choose(null);
    }
  });
  const onKey = e => {
    const onGrid = e.target.closest?.('.dp-day, .dp-month');
    if (e.key === 'PageUp' || e.key === 'PageDown') {
      e.preventDefault(); e.stopPropagation();
      shiftMonth((e.key === 'PageUp' ? -1 : 1) * (mode === 'days' ? (e.shiftKey ? 12 : 1) : 12));
      return draw(true);
    }
    if (!onGrid) return;
    const step = mode === 'days'
      ? { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -7, ArrowDown: 7 }[e.key]
      : { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -3, ArrowDown: 3 }[e.key];
    if (step === undefined) return;
    e.preventDefault(); e.stopPropagation();
    if (mode === 'days') { focus = sumarDias(focus, step); month = new Date(focus.getFullYear(), focus.getMonth(), 1); }
    else month = new Date(month.getFullYear(), month.getMonth() + step, 1);
    draw(true);
  };
  draw();
  openPopover(pill, el, onKey);
  requestAnimationFrame(() => el.querySelector('.dp-day[tabindex="0"]')?.focus({ preventScroll: true }));
}
