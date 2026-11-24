// Catalogo: categorias, tags, busqueda, paginacion y mini-carrito.

(function () {
  const PAGE_SIZE = 6;

  const state = {
    productos: [],
    categoria: "Todas",
    tags: new Set(), // un producto debe tener TODOS los tags elegidos
    busqueda: "",
    pagina: 1,
  };

  // Minusculas y sin tildes: "cumpleanos" encuentra "cumplea\u00f1os".
  function simple(texto) {
    return String(texto || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  }

  function productosFiltrados() {
    const termino = simple(state.busqueda.trim());
    return state.productos.filter((p) => {
      const coincideCategoria = state.categoria === "Todas" || p.categoria === state.categoria;
      const tags = p.tags || [];
      const coincideTags = [...state.tags].every((t) => tags.includes(t));
      const coincideBusqueda =
        !termino ||
        simple(p.nombre).includes(termino) ||
        simple(p.descripcion).includes(termino) ||
        tags.some((t) => simple(t).includes(termino));
      return coincideCategoria && coincideTags && coincideBusqueda;
    });
  }

  function renderCategorias() {
    const cont = document.getElementById("categoryList");
    if (!cont) return;
    const categorias = ["Todas", ...new Set(state.productos.map((p) => p.categoria))];
    cont.innerHTML = "";
    categorias.forEach((cat) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = cat;
      btn.setAttribute("aria-pressed", String(cat === state.categoria));
      btn.addEventListener("click", () => {
        state.categoria = cat;
        state.pagina = 1;
        renderCategorias();
        renderGrid();
      });
      cont.appendChild(btn);
    });
  }

  function renderTags() {
    const panel = document.getElementById("tagPanel");
    const cont = document.getElementById("tagFilter");
    if (!panel || !cont) return;

    // Cuantos productos tiene cada tag (para ordenar por popularidad).
    const conteo = new Map();
    state.productos.forEach((p) => (p.tags || []).forEach((t) => conteo.set(t, (conteo.get(t) || 0) + 1)));
    const tags = [...conteo.keys()].sort((a, b) => conteo.get(b) - conteo.get(a) || a.localeCompare(b));

    panel.hidden = tags.length === 0;
    cont.innerHTML = "";
    tags.forEach((tag) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = tag;
      btn.setAttribute("aria-pressed", String(state.tags.has(tag)));
      btn.addEventListener("click", () => {
        if (state.tags.has(tag)) state.tags.delete(tag);
        else state.tags.add(tag);
        state.pagina = 1;
        renderTags();
        renderGrid();
      });
      cont.appendChild(btn);
    });

    if (state.tags.size) {
      const limpiar = document.createElement("button");
      limpiar.type = "button";
      limpiar.className = "tag-filter__clear";
      limpiar.textContent = "Quitar filtros";
      limpiar.addEventListener("click", () => {
        state.tags.clear();
        state.pagina = 1;
        renderTags();
        renderGrid();
      });
      cont.appendChild(limpiar);
    }
  }

  function renderGrid() {
    const grid = document.getElementById("productGrid");
    const status = document.getElementById("catalogStatus");
    const pagination = document.getElementById("pagination");
    if (!grid) return;

    const filtrados = productosFiltrados();
    grid.innerHTML = "";

    if (filtrados.length === 0) {
      status.textContent = "No encontramos productos con ese filtro. Prueba con otra categor\u00eda, tag o b\u00fasqueda.";
      pagination.hidden = true;
      return;
    }

    const totalPaginas = Math.max(1, Math.ceil(filtrados.length / PAGE_SIZE));
    state.pagina = Math.min(state.pagina, totalPaginas);
    const inicio = (state.pagina - 1) * PAGE_SIZE;
    const pagina = filtrados.slice(inicio, inicio + PAGE_SIZE);

    status.textContent = `Mostrando ${pagina.length} de ${filtrados.length} producto(s)`;
    pagina.forEach((p) => grid.appendChild(window.ChocoUI.buildProductCard(p)));

    pagination.hidden = totalPaginas <= 1;
    document.getElementById("pageIndicator").textContent = `${state.pagina} / ${totalPaginas}`;
    document.getElementById("prevPage").disabled = state.pagina <= 1;
    document.getElementById("nextPage").disabled = state.pagina >= totalPaginas;
  }

  function renderMiniCart() {
    const cont = document.getElementById("miniCart");
    if (!cont) return;
    const items = window.ChocoCart.getItems();
    cont.innerHTML = "";
    if (items.length === 0) {
      const vacio = document.createElement("div");
      vacio.className = "mini-cart__empty";
      vacio.innerHTML =
        '<p style="margin:0; font-weight:700;">\u00a1A\u00fan no eliges nada!</p><p style="margin:0;">No pierdas la oportunidad de darte un gusto.</p>';
      cont.appendChild(vacio);
      return;
    }
    items.forEach((it) => {
      const row = document.createElement("div");
      row.className = "mini-cart__row";
      const nombre = document.createElement("span");
      nombre.textContent = `${it.nombre} x${it.cantidad}`;
      const subtotal = document.createElement("span");
      subtotal.style.fontWeight = "800";
      subtotal.textContent = window.ChocoAPI.formatCLP(it.precio * it.cantidad);
      row.append(nombre, subtotal);
      cont.appendChild(row);
    });
    const total = document.createElement("div");
    total.className = "mini-cart__total";
    total.textContent = `Total: ${window.ChocoAPI.formatCLP(window.ChocoCart.subtotal(items))}`;
    cont.appendChild(total);
  }

  // Producto destacado: el de menor precio, al precio real.
  function renderOferta() {
    const slot = document.getElementById("offerSlot");
    if (!slot || state.productos.length === 0) return;
    const producto = state.productos.reduce((min, p) => (p.precio < min.precio ? p : min), state.productos[0]);

    const card = document.createElement("div");
    card.className = "offer-card";

    const media = document.createElement("div");
    media.className = "offer-card__media";
    if (producto.imagen) {
      const img = document.createElement("img");
      img.src = producto.imagen;
      img.alt = producto.nombre;
      img.addEventListener("error", () => img.remove());
      media.appendChild(img);
    }

    const titulo = document.createElement("p");
    titulo.style.fontWeight = "700";
    titulo.style.margin = "0 0 14px";
    titulo.textContent = producto.nombre;

    const precios = document.createElement("div");
    precios.style.marginBottom = "16px";
    precios.innerHTML = `<span class="price">${window.ChocoAPI.formatCLP(producto.precio)}</span>`;

    const acciones = document.createElement("div");
    acciones.style.display = "flex";
    acciones.style.gap = "10px";
    acciones.style.justifyContent = "center";

    const detalles = document.createElement("a");
    detalles.className = "btn btn--accent btn--sm";
    detalles.href = `producto.php?id=${encodeURIComponent(producto.id)}`;
    detalles.textContent = "Detalles";

    const agregar = document.createElement("button");
    agregar.type = "button";
    agregar.className = "btn btn--accent btn--sm";
    agregar.textContent = "\u{1f6d2} Agregar";
    agregar.dataset.addId = producto.id;
    agregar.dataset.addNombre = producto.nombre;
    agregar.dataset.addPrecio = String(producto.precio);
    if (typeof producto.stock === "number") agregar.dataset.addStock = String(producto.stock);
    if (producto.imagen) agregar.dataset.addImagen = producto.imagen;

    acciones.append(detalles, agregar);
    card.append(media, titulo, precios, acciones);
    slot.innerHTML = "";
    slot.appendChild(card);
  }

  function initPagination() {
    document.getElementById("prevPage").addEventListener("click", () => {
      state.pagina -= 1;
      renderGrid();
    });
    document.getElementById("nextPage").addEventListener("click", () => {
      state.pagina += 1;
      renderGrid();
    });
  }

  function initSearchSync() {
    const params = new URLSearchParams(window.location.search);
    state.busqueda = params.get("q") || "";
    if (params.get("categoria")) state.categoria = params.get("categoria");
    params.getAll("tag").forEach((t) => state.tags.add(t.toLowerCase()));
    const form = document.querySelector(".search-form");
    if (form) {
      form.addEventListener("submit", (event) => {
        event.preventDefault();
        state.busqueda = form.querySelector("input[name='q']").value;
        state.pagina = 1;
        renderGrid();
        const url = new URL(window.location.href);
        if (state.busqueda) url.searchParams.set("q", state.busqueda);
        else url.searchParams.delete("q");
        window.history.replaceState({}, "", url);
      });
    }
  }

  async function init() {
    initSearchSync();
    initPagination();
    document.addEventListener("chocomania:cart-updated", renderMiniCart);

    state.productos = await window.ChocoAPI.fetchProductos();
    renderCategorias();
    renderTags();
    renderGrid();
    renderMiniCart();
    renderOferta();
  }

  document.addEventListener("DOMContentLoaded", init);
})();
