/* Programa Depor — Instalador de programas (kit común en comun/kit.js) */
'use strict';

Object.assign(ICONS, {
  shield: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
  users: '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
  unlock: '<rect x="3" y="11" width="18" height="11" rx="2.5"/><path d="M7 11V7a5 5 0 0 1 9.9-1"/>',
  lock: '<rect x="3" y="11" width="18" height="11" rx="2.5"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
  broom: '<path d="m13 11 8-8M9.5 9.5l5 5M4 20c2-1 3-4 5.5-6.5l1.5 1.5c-2.5 2.5-5.5 3.5-7 5zM8 14l-1.5 4.5M11 16.5 9 21"/>',
  globe: '<circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15 15 0 0 1 0 20M12 2a15 15 0 0 0 0 20"/>',
  archive: '<rect x="2" y="3" width="20" height="5" rx="1.5"/><path d="M4 8v11a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8M10 12h4"/>',
  doc: '<path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5z"/><path d="M14 2v6h6M8 13h8M8 17h6"/>',
  monitor: '<rect x="2" y="3" width="20" height="14" rx="2.5"/><path d="M8 21h8M12 17v4"/>',
  cloud: '<path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"/>',
  sheet: '<rect x="3" y="3" width="18" height="18" rx="2.5"/><path d="M3 9h18M3 15h18M9 3v18"/>',
  clipboard: '<rect x="8" y="2" width="8" height="4" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2M9 12h6M9 16h4"/>',
  printer: '<path d="M6 9V2h12v7"/><rect x="2" y="9" width="20" height="9" rx="2"/><path d="M6 14h12v8H6z"/>',
  camera: '<path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/>',
  plug: '<path d="M9 2v6M15 2v6M6 8h12v4a6 6 0 0 1-12 0zM12 18v4"/>',
  gear: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-2.82 1.16V21a2 2 0 1 1-4 0v-.09a1.65 1.65 0 0 0-2.82-1.16l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 3.27 14H3a2 2 0 1 1 0-4h.09a1.65 1.65 0 0 0 1.16-2.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 10 3.09V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 2.82 1.16l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 20.91 10H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>',
  database: '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>',
  font: '<path d="M4 20 10 4h4l6 16M7 14h10"/>',
  wrench: '<path d="M14.7 6.3a4 4 0 0 0 5 5L22 14l-8 8-2.3-2.3a4 4 0 0 0-5-5L2 10l8-8z"/>',
  flame: '<path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.4-.5-2-1-3-1.1-2.1-.2-4 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.2.4-2.3 1-3.3.4 1.4 1.4 2.8 2.5 2.8z"/>',
  store: '<path d="M3 9 4.5 4h15L21 9M3 9v11h18V9M3 9h18M9 20v-6h6v6"/>',
  tool: '<path d="m14 7 3-3 3 3-3 3M17 10l-8 8-4 1 1-4 8-8"/>',
  chart: '<path d="M3 3v18h18M8 17V11M13 17V7M18 17v-4"/>',
  building: '<rect x="4" y="2" width="16" height="20" rx="2"/><path d="M9 22v-4h6v4M8 6h.01M12 6h.01M16 6h.01M8 10h.01M12 10h.01M16 10h.01M8 14h.01M12 14h.01M16 14h.01"/>',
  card: '<rect x="2" y="5" width="20" height="14" rx="2.5"/><path d="M2 10h20M6 15h4"/>',
  mail: '<rect x="2" y="4" width="20" height="16" rx="2.5"/><path d="m22 6-10 7L2 6"/>',
  history: '<path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5M12 7v5l3 2"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
  chev: '<path d="m9 6 6 6-6 6"/>',
  back: '<path d="m15 6-6 6 6 6"/>',
});

const S = { d: null, vista: 'generales', filtro: '', pila: [], procesos: new Map() };

/* ───────────── Render ───────────── */
function render() {
  $$('.tab').forEach(b => { const on = b.dataset.view === S.vista; b.classList.toggle('on', on); b.setAttribute('aria-selected', on); });
  moveIndicator();
  const d = S.d;
  if (!d.ruta) {
    $('#main').innerHTML = `<div class="view still"><div class="empty glass sin-carpeta">
      <span class="logo lg" style="background:${grad('#e67e00')}">${icon('folder')}</span>
      <h2>No encontré la carpeta «Programas»</h2>
      <p>Debe estar junto al programa. Elige a mano la carpeta que contiene los instaladores.</p>
      <button class="btn-glass btn-tinted" data-action="elegir-carpeta">${icon('folder')}Elegir carpeta</button></div></div>`;
    return;
  }
  const generales = S.vista === 'generales';
  $('#main').innerHTML = `<div class="view still">
    <div class="large-title"><div><h1>${generales ? 'Programas generales' : 'Punto de Venta'}</h1>
      <div class="sub">${generales ? 'Instaladores y configuración para un PC nuevo' : 'Pasos en orden para dejar listo un TPV de tienda'} · ${esc(d.pc)}</div></div>
      <div class="title-actions">
        <button class="btn-plain" data-action="historial">${icon('history')}Historial</button>
        ${d.pendrive ? `<button class="btn-plain" data-action="abrir-carpeta" title="${esc(d.ruta)}">${icon('folder')}Carpeta Programas</button>`
          : `<button class="btn-plain" data-action="elegir-carpeta">${icon('folder')}Usar el pendrive</button>`}
      </div></div>
    ${d.pendrive ? '' : `<div class="modo-web glass"><span class="logo" style="background:${grad('#0a84ff')}">${icon('cloud')}</span>
      <div><b>Sin pendrive</b><small>Funcionan los programas que se descargan de su sitio oficial (Chrome, AnyDesk, TeamViewer, Drive, 7-Zip, WinRAR, FortiClient) y las herramientas de Windows. Para el resto conecta el pendrive y elige su carpeta «Programas».</small></div></div>`}
    ${generales ? `<label class="buscador glass">${icon('search')}<input id="buscar" type="search" placeholder="Buscar programa…" value="${esc(S.filtro)}" autocomplete="off" spellcheck="false" aria-label="Buscar programa"></label>` : ''}
    <div class="grilla ${generales ? '' : 'pasos'}" id="grilla">${generales ? tarjetasGenerales() : tarjetasTpv()}</div>
  </div>`;
}

const ALIAS_ID = id => ({ defender: 'defender_custom' })[id] || id;
/** ¿Se puede usar sin pendrive? (una tarjeta con submenú, si alguna de sus opciones se puede) */
function disponible(id) {
  if (S.d.pendrive) return true;
  const m = S.d.submenus[id];
  return m ? m.opciones.some(o => disponible(o.id)) : S.d.en_linea.includes(ALIAS_ID(id));
}

function tarjeta(t, extra = '') {
  const sub = !!S.d.submenus[t.id];
  const ok = disponible(t.id);
  return `<button class="tarjeta glass ${ok ? '' : 'sin-red'}" data-action="tarjeta" data-id="${t.id}" style="--c:${t.color}" ${ok ? '' : 'title="Necesita el pendrive"'}>
    ${extra}<span class="logo" style="background:${grad(t.color)}">${icon(t.icono)}</span>
    <span class="t-txt"><b>${esc(t.titulo)}</b><small>${ok ? esc(t.desc) : 'Necesita el pendrive'}</small></span>
    ${sub && ok ? `<span class="t-mas">${icon('chev')}</span>` : ''}</button>`;
}
const normalizar = s => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
function tarjetasGenerales() {
  const f = normalizar(S.filtro.trim());
  const visibles = S.d.generales.filter(t => !f || normalizar(t.titulo + ' ' + t.desc + ' ' + (S.d.submenus[t.id]?.opciones.map(o => o.titulo).join(' ') || '')).includes(f));
  return visibles.length ? visibles.map(t => tarjeta(t)).join('') : `<div class="empty-inline">No hay programas que coincidan con «${esc(S.filtro)}».</div>`;
}
const tarjetasTpv = () => S.d.tpv.map((t, i) => tarjeta(t, `<span class="paso num">${i + 1}</span>`)).join('');

/* ───────────── Submenús (sheet con navegación) ───────────── */
function abrirSubmenu(id, apilar = true) {
  const m = S.d.submenus[id];
  if (apilar) S.pila.push(id);
  const atras = S.pila.length > 1;
  openSheet({ title: m.titulo, noConfirm: true, small: true, body: `
    ${atras ? `<button class="btn-plain volver" data-action="volver">${icon('back')}${esc(S.d.submenus[S.pila[S.pila.length - 2]].titulo)}</button>` : ''}
    <div class="list glass opciones">${m.opciones.map(o => disponible(o.id) ? `<button class="opcion" data-action="opcion" data-id="${o.id}">
      <span class="o-txt"><b>${esc(o.titulo)}</b><small>${esc(o.desc)}</small></span>
      <span class="t-mas">${icon('chev')}</span></button>`
      : `<div class="opcion sin-red"><span class="o-txt"><b>${esc(o.titulo)}</b><small>${esc(o.desc)}</small></span><span class="pill off">Pendrive</span></div>`).join('')}</div>` });
}

// La tarjeta «Exclusión Windows Defender» ejecuta directo la exclusión completa (igual que la 3.6)
const ALIAS = { defender: 'defender_custom' };

function ejecutar(id) {
  id = ALIAS[id] || id;
  const texto = S.d.confirmar[id];
  const lanzar = async () => { closeSheet(); S.pila = []; const r = await api.ejecutar(id); if (!r.ok) toast(r.error); };
  if (texto) {
    const nombre = S.d.generales.find(t => t.id === id || ALIAS[t.id] === id)?.titulo || S.d.submenus.drivers.opciones.concat(S.d.submenus.inventario.opciones).find(o => o.id === id)?.titulo || 'Confirmar';
    confirmSheet({ title: nombre, text: texto, label: 'Continuar', danger: id === 'defender_custom' || id === 'drivers_bios', onConfirm: lanzar });
  } else lanzar();
}

/* ───────────── Avisos de procesos ───────────── */
const ICONO_EST = { ok: 'check', error: 'x', aviso: 'warn' };
window.onProceso = p => {
  const pr = S.procesos.get(p.id) || {};
  Object.assign(pr, p, { texto: p.texto, detalle: p.detalle ?? pr.detalle });
  S.procesos.set(p.id, pr);
  let el = $(`.proceso[data-id="${p.id}"]`);
  if (!el) { el = document.createElement('div'); el.className = 'proceso glass'; el.dataset.id = p.id; $('#procesos').append(el); }
  const corriendo = p.estado === 'inicio' || p.estado === 'avance';
  el.className = `proceso glass ${corriendo ? 'corriendo' : p.estado}`;
  el.innerHTML = `${corriendo ? '<span class="spinner"></span>' : `<span class="p-ico">${icon(ICONO_EST[p.estado])}</span>`}
    <span class="p-txt">${esc(pr.texto)}</span>
    ${p.estado === 'error' ? '<button class="btn-plain mini" data-action="ver-error">Ver detalle</button>' : ''}
    ${corriendo ? '' : `<button class="mini-btn" data-action="cerrar-proceso" aria-label="Cerrar aviso">${icon('x')}</button>`}`;
  if (p.estado === 'ok' || p.estado === 'aviso') setTimeout(() => cerrarProceso(p.id), 7000);
};
function cerrarProceso(id) {
  const el = $(`.proceso[data-id="${id}"]`);
  if (!el) return;
  el.classList.add('saliendo');
  setTimeout(() => { el.remove(); S.procesos.delete(Number(id)); }, 260);
}

/* ───────────── Historial ───────────── */
async function historial() {
  const r = await api.historial();
  openSheet({ title: 'Historial de instalaciones', noConfirm: true, wide: true, body: r.filas.length
    ? `<p class="help" style="margin:0 4px 10px">Últimas acciones registradas en instalaciones.log (de todos los equipos donde se usó este pendrive).</p>
       <div class="hist glass">${r.filas.map(f => `<div class="h-fila"><span class="pill ${f.ok ? 'ok' : 'error'}">${f.ok ? 'OK' : 'Error'}</span>
         <span class="h-n"><b>${esc(f.nombre)}</b><small>${esc(f.resultado)}</small></span>
         <span class="h-m num">${esc(f.fecha)}<small>${esc(f.pc)}</small></span></div>`).join('')}</div>`
    : '<div class="empty-inline">Todavía no hay instalaciones registradas.</div>' });
}

/* ───────────── Eventos ───────────── */
document.addEventListener('input', e => {
  if (e.target.id !== 'buscar') return;
  S.filtro = e.target.value;
  $('#grilla').innerHTML = tarjetasGenerales();
});
document.addEventListener('keydown', e => {
  if (e.target.id === 'buscar' && e.key === 'Escape' && S.filtro) { e.stopPropagation(); S.filtro = ''; e.target.value = ''; $('#grilla').innerHTML = tarjetasGenerales(); }
  if (e.target.id === 'buscar' && e.key === 'Enter') { const t = $('#grilla .tarjeta'); if (t) t.click(); }
  if ((e.ctrlKey && e.key.toLowerCase() === 'f') || (e.key === '/' && !e.target.matches('input, textarea'))) {
    const b = $('#buscar'); if (b) { e.preventDefault(); b.focus(); b.select(); }
  }
});

Object.assign(actions, {
  go: el => { S.vista = el.dataset.view; S.pila = []; render(); api.guardar_tab(S.vista === 'tpv' ? 1 : 0); },
  tarjeta: el => { const id = el.dataset.id; if (!disponible(id)) { toast('Este programa necesita el pendrive: conéctalo y usa «Usar el pendrive»'); return; } if (S.d.submenus[id]) { S.pila = []; abrirSubmenu(id); } else ejecutar(id); },
  opcion: el => { const id = el.dataset.id; if (S.d.submenus[id]) abrirSubmenu(id); else ejecutar(id); },
  volver: () => { S.pila.pop(); abrirSubmenu(S.pila[S.pila.length - 1], false); },
  'cerrar-proceso': el => cerrarProceso(el.closest('.proceso').dataset.id),
  'ver-error': el => {
    const p = S.procesos.get(Number(el.closest('.proceso').dataset.id));
    openSheet({ title: p.texto, noConfirm: true, small: true, body: `<p class="sheet-text pre">${esc(p.detalle || '')}</p><div class="sheet-buttons"><button class="btn-glass btn-tinted" data-action="close-sheet">Entendido</button></div>` });
  },
  historial: () => historial(),
  'abrir-carpeta': () => api.abrir_carpeta_programas(),
  'elegir-carpeta': async () => { const d = await api.elegir_carpeta_programas(); if (d) { S.d = d; render(); } },
});

buildTabbar([{ id: 'generales', label: 'Programas', icon: 'gear' }, { id: 'tpv', label: 'Punto de Venta', icon: 'store' }]);
document.body.insertAdjacentHTML('beforeend', '<div class="procesos" id="procesos" aria-live="polite"></div>');
conectar(async () => {
  S.d = await api.inicio();
  S.vista = S.d.ultima_tab === 1 ? 'tpv' : 'generales';
  render();
});
