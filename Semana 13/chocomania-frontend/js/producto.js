/* ChocoManía — página de detalle de producto. */

(function () {
  let cantidad = 1;
  let miniaturaActiva = 0;

  function idSolicitado() {
    if (window.CHOCO_PRODUCT_ID) return window.CHOCO_PRODUCT_ID;
    return new URLSearchParams(window.location.search).get("id") || "";
  }

  function renderNoEncontrado() {
    document.getElementById("breadcrumbCurrent").textContent = "Producto no encontrado";
    document.getElementById("productRoot").innerHTML = `
      <div class="panel-body" style="border-radius:8px; text-align:center;">
        <p style="font-weight:800; font-size:18px; margin:0 0 12px;">No encontramos ese producto.</p>
        <p style="margin:0 0 20px;">Puede que ya no esté disponible o el enlace esté incompleto.</p>
        <a class="btn btn--accent btn--pill" href="catalogo.php">Ver catálogo</a>
      </div>`;
  }

  function renderProducto(producto, relacionados) {
    document.title = `ChocoManía — ${producto.nombre}`;
    document.getElementById("breadcrumbCurrent").textContent = producto.nombre;

    const root = document.getElementById("productRoot");
    root.innerHTML = "";

    const layout = document.createElement("div");
    layout.className = "product-detail";

    // Galería (Semana 13): una miniatura por cada imagen del producto.
    // Al hacer clic, la miniatura pasa a la imagen principal.
    const imagenes = producto.imagenes && producto.imagenes.length ? producto.imagenes : [];
    const gallery = document.createElement("div");
    gallery.className = "product-gallery";

    const main = document.createElement("div");
    main.className = "product-gallery__main";
    main.id = "galleryMain";
    gallery.appendChild(main);
    renderMedia(main, producto, imagenes[0]);

    if (imagenes.length > 1) {
      const thumbs = document.createElement("div");
      thumbs.className = "product-gallery__thumbs";
      imagenes.forEach((src, i) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.setAttribute("aria-label", `Ver imagen ${i + 1} de ${imagenes.length}`);
        btn.setAttribute("aria-pressed", String(i === miniaturaActiva));
        const img = document.createElement("img");
        img.src = src;
        img.alt = "";
        btn.appendChild(img);
        btn.addEventListener("click", () => {
          miniaturaActiva = i;
          thumbs.querySelectorAll("button").forEach((b, idx) => b.setAttribute("aria-pressed", String(idx === i)));
          renderMedia(main, producto, src);
        });
        thumbs.appendChild(btn);
      });
      gallery.appendChild(thumbs);
    }

    // Info
    const info = document.createElement("div");
    info.className = "product-info";

    const badges = document.createElement("div");
    badges.className = "badges";
    const categoria = document.createElement("span");
    categoria.className = "badge";
    categoria.textContent = producto.categoria;
    badges.appendChild(categoria);
    (producto.tags || []).forEach((t) => {
      const tag = document.createElement("a");
      tag.className = "badge badge--light";
      tag.href = `catalogo.php?tag=${encodeURIComponent(t)}`;
      tag.textContent = t;
      badges.appendChild(tag);
    });

    const h1 = document.createElement("h1");
    h1.textContent = producto.nombre;

    const precio = document.createElement("div");
    precio.className = "product-price";
    precio.innerHTML = `<strong>${window.ChocoAPI.formatCLP(producto.precio)}</strong><span>CLP</span>`;

    const descPanel = document.createElement("div");
    descPanel.className = "panel";
    descPanel.innerHTML = `
      <div class="panel-title"><h2>Descripción</h2></div>
      <div class="panel-body">
        <p style="margin:0;">${escapeHtml(producto.descripcion || "Producto artesanal ChocoManía, hecho a mano en pequeños lotes.")}</p>
      </div>`;

    const qty = document.createElement("div");
    qty.className = "qty-control";
    qty.innerHTML = `
      <button type="button" id="qtyDec" aria-label="Quitar una unidad">−</button>
      <span id="qtyValue">${cantidad}</span>
      <button type="button" id="qtyInc" aria-label="Agregar una unidad">+</button>`;

    const actions = document.createElement("div");
    actions.className = "product-actions";
    const addBtn = document.createElement("button");
    addBtn.type = "button";
    addBtn.className = "btn btn--accent btn--pill";
    addBtn.id = "addToCartBtn";
    addBtn.textContent = "Agregar al carrito";
    actions.append(qty, addBtn);

    // Stock (Semana 13). Si el producto no informa stock, se asume disponible.
    const stockNote = document.createElement("p");
    stockNote.className = "stock-note";
    const agotado = producto.stock === 0;
    if (agotado) {
      stockNote.classList.add("stock-note--out");
      stockNote.textContent = "Agotado por ahora";
      addBtn.disabled = true;
    } else if (typeof producto.stock === "number" && producto.stock <= 5) {
      stockNote.textContent = `¡Quedan ${producto.stock}!`;
    }

    info.append(badges, h1, precio, descPanel);
    if (stockNote.textContent) info.appendChild(stockNote);
    info.appendChild(actions);
    layout.append(gallery, info);
    root.appendChild(layout);

    const detailInfo = document.createElement("section");
    detailInfo.className = "panel mt-lg";
    detailInfo.innerHTML = `
      <div class="panel-title"><h2>Detalles del producto</h2></div>
      <div class="panel-body">
        <div class="detail-grid">
          <div>
            <h3 style="font-size:18px; margin-bottom:8px;">Ingredientes y alérgenos</h3>
            <p style="margin:0 0 8px;"><strong>Ingredientes:</strong> ${escapeHtml(producto.ingredientes || "harina, huevo, mantequilla, azúcar y chocolate de cacao seleccionado.")}</p>
            <p style="margin:0;"><strong>Alérgenos:</strong> ${escapeHtml(textoAlergenos(producto))}</p>
          </div>
          <div>
            <h3 style="font-size:18px; margin-bottom:8px;">Conservación</h3>
            <p style="margin:0;">Se conserva refrigerado hasta por 4 días. Retira del refrigerador 30 minutos antes de servir para disfrutar mejor su sabor.</p>
          </div>
          <div>
            <h3 style="font-size:18px; margin-bottom:8px;">Entrega y personalización</h3>
            <p style="margin:0;">Retiro en tienda o delivery. ¿Quieres una versión a tu medida? Revisa nuestros <a href="index.php" style="color:inherit; font-weight:700;">Pedidos Especiales</a>.</p>
          </div>
        </div>
      </div>`;
    root.appendChild(detailInfo);

    document.getElementById("qtyDec").addEventListener("click", () => actualizarCantidad(-1));
    document.getElementById("qtyInc").addEventListener("click", () => actualizarCantidad(1));
    addBtn.addEventListener("click", () => {
      window.ChocoCart.addItem(producto, cantidad);
      window.ChocoUI.showToast(`${producto.nombre} (x${cantidad}) se agregó al carrito`);
      cantidad = 1;
      document.getElementById("qtyValue").textContent = "1";
    });

    renderRelacionados(relacionados);
  }

  function actualizarCantidad(delta) {
    cantidad = Math.max(1, cantidad + delta);
    document.getElementById("qtyValue").textContent = String(cantidad);
  }

  function textoAlergenos(producto) {
    if (!Array.isArray(producto.alergenos)) {
      return "contiene gluten, huevo y lácteos. Elaborado en un local que también procesa frutos secos.";
    }
    const base = producto.alergenos.length
      ? `contiene ${producto.alergenos.join(", ")}.`
      : "no declara alérgenos.";
    return `${base} Elaborado en un local que también procesa frutos secos.`;
  }

  function renderMedia(container, producto, src) {
    container.innerHTML = "";
    const fuente = src || producto.imagen;
    if (fuente) {
      const img = document.createElement("img");
      img.src = fuente;
      img.alt = producto.nombre;
      img.addEventListener("error", () => {
        container.innerHTML = '<span style="font-weight:800; color:#5a3d37;">IMAGEN</span>';
      });
      container.appendChild(img);
    } else {
      container.innerHTML = '<span style="font-weight:800; color:#5a3d37;">IMAGEN</span>';
    }
  }

  function renderRelacionados(lista) {
    const section = document.getElementById("relatedSection");
    const grid = document.getElementById("relatedGrid");
    if (!lista.length) {
      section.hidden = true;
      return;
    }
    grid.innerHTML = "";
    lista.forEach((p) => grid.appendChild(window.ChocoUI.buildProductCard(p)));
    section.hidden = false;
  }

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  async function init() {
    const id = idSolicitado();
    const producto = await window.ChocoAPI.fetchProducto(id);
    if (!producto) {
      renderNoEncontrado();
      return;
    }
    const todos = await window.ChocoAPI.fetchProductos();
    const relacionados = todos.filter((p) => p.id !== producto.id).slice(0, 4);
    renderProducto(producto, relacionados);
  }

  document.addEventListener("DOMContentLoaded", init);
})();
