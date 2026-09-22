/* ChocoManía — página de catálogo: categorías, búsqueda, paginación,
   mini-carrito lateral y panel de ofertas. */

(function () {
  const PAGE_SIZE = 6;

  const state = {
    productos: [],
    categoria: "Todas",
    busqueda: "",
    pagina: 1,
  };

  function productosFiltrados() {
    const termino = state.busqueda.trim().toLowerCase();
    return state.productos.filter((p) => {
      const coincideCategoria = state.categoria === "Todas" || p.categoria === state.categoria;
      const coincideBusqueda =
        !termino ||
        p.nombre.toLowerCase().includes(termino) ||
        (p.descripcion || "").toLowerCase().includes(termino);
      return coincideCategoria && coincideBusqueda;
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

  function renderGrid() {
    const grid = document.getElementById("productGrid");
    const status = document.getElementById("catalogStatus");
    const pagination = document.getElementById("pagination");
    if (!grid) return;

    const filtrados = productosFiltrados();
    grid.innerHTML = "";

    if (filtrados.length === 0) {
      status.textContent = "No encontramos productos con ese filtro. Prueba con otra categoría o búsqueda.";
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
        '<p style="margin:0; font-weight:700;">¡Aún no eliges nada!</p><p style="margin:0;">No pierdas la oportunidad de darte un gusto.</p>';
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

  function renderOferta() {
    const slot = document.getElementById("offerSlot");
    if (!slot || state.productos.length === 0) return;
    const producto = state.productos.reduce((min, p) => (p.precio < min.precio ? p : min), state.productos[0]);
    const precioOferta = Math.round(producto.precio * 0.85);

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
    precios.innerHTML = `<span class="price price--old">${window.ChocoAPI.formatCLP(producto.precio)}</span><span class="price">${window.ChocoAPI.formatCLP(precioOferta)}</span>`;

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
    agregar.textContent = "🛒 Agregar";
    agregar.dataset.addId = producto.id;
    agregar.dataset.addNombre = producto.nombre;
    agregar.dataset.addPrecio = String(precioOferta);
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
    renderGrid();
    renderMiniCart();
    renderOferta();
  }

  document.addEventListener("DOMContentLoaded", init);
})();
