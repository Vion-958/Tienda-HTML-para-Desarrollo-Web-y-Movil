/* ChocoManía — comportamiento compartido del layout:
   menú móvil, resaltado del enlace activo, buscador y toasts. */

(function (global) {
  function initNavToggle() {
    const toggle = document.querySelector(".nav-toggle");
    const nav = document.getElementById("siteNav");
    if (!toggle || !nav) return;
    toggle.addEventListener("click", () => {
      const abierto = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", String(abierto));
    });
  }

  function markActiveLink() {
    const current = document.body.getAttribute("data-page");
    if (!current) return;
    document.querySelectorAll(`.site-nav a[data-page]`).forEach((a) => {
      if (a.getAttribute("data-page") === current) {
        a.setAttribute("aria-current", "page");
      } else {
        a.removeAttribute("aria-current");
      }
    });
    const cartLink = document.querySelector(".cart-link");
    if (cartLink) {
      if (current === "carrito") {
        cartLink.setAttribute("aria-current", "page");
      } else {
        cartLink.removeAttribute("aria-current");
      }
    }
  }

  function initSearchForms() {
    document.querySelectorAll(".search-form").forEach((form) => {
      const input = form.querySelector("input[name='q']");
      const params = new URLSearchParams(global.location.search);
      if (input && params.get("q")) {
        input.value = params.get("q");
      }
    });
  }

  const CACAO_ICON =
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M12 2c3.2 3.2 3.2 7.6 0 10.8-3.2-3.2-3.2-7.6 0-10.8Z"/><path d="M12 12.2c4.3 0 7.8 3.3 7.8 7.8H4.2c0-4.5 3.5-7.8 7.8-7.8Z"/></svg>';

  function buildMedia(producto) {
    const wrap = document.createElement("div");
    wrap.className = "img-placeholder";
    if (producto.imagen) {
      const img = document.createElement("img");
      img.src = producto.imagen;
      img.alt = producto.nombre;
      img.loading = "lazy";
      img.addEventListener("error", () => {
        img.remove();
        wrap.innerHTML = CACAO_ICON;
      });
      wrap.textContent = "";
      wrap.appendChild(img);
    } else {
      wrap.innerHTML = CACAO_ICON;
    }
    return wrap;
  }

  function buildProductCard(producto) {
    const article = document.createElement("article");
    article.className = "product-card";

    const link = document.createElement("a");
    link.className = "product-card__media";
    link.href = `producto.php?id=${encodeURIComponent(producto.id)}`;
    link.setAttribute("aria-label", `Ver detalles de ${producto.nombre}`);
    link.appendChild(buildMedia(producto));

    const body = document.createElement("div");
    body.className = "product-card__body";

    const titulo = document.createElement("h3");
    titulo.className = "product-card__title";
    titulo.textContent = producto.nombre;

    const desc = document.createElement("p");
    desc.className = "product-card__desc";
    desc.textContent = producto.descripcion || "";

    const footer = document.createElement("div");
    footer.className = "product-card__footer";

    const precio = document.createElement("span");
    precio.className = "price";
    precio.textContent = global.ChocoAPI.formatCLP(producto.precio);

    const actions = document.createElement("div");
    actions.className = "product-card__actions";

    const detalles = document.createElement("a");
    detalles.className = "btn btn--ghost btn--sm";
    detalles.href = `producto.php?id=${encodeURIComponent(producto.id)}`;
    detalles.textContent = "Detalles";

    const agregar = document.createElement("button");
    agregar.type = "button";
    agregar.className = "btn btn--accent btn--sm";
    agregar.textContent = "Agregar";
    agregar.dataset.addId = producto.id;
    agregar.dataset.addNombre = producto.nombre;
    agregar.dataset.addPrecio = String(producto.precio);
    if (producto.imagen) agregar.dataset.addImagen = producto.imagen;

    actions.append(detalles, agregar);
    footer.append(precio, actions);
    body.append(titulo, desc, footer);
    article.append(link, body);
    return article;
  }

  function initAddToCartDelegation() {
    document.addEventListener("click", (event) => {
      const btn = event.target.closest("[data-add-id]");
      if (!btn) return;
      const producto = {
        id: btn.dataset.addId,
        nombre: btn.dataset.addNombre,
        precio: Number(btn.dataset.addPrecio),
        imagen: btn.dataset.addImagen || null,
      };
      const cantidad = Number(btn.dataset.addQty || 1);
      global.ChocoCart.addItem(producto, cantidad);
      showToast(`${producto.nombre} se agregó al carrito`);
    });
  }

  function showToast(mensaje) {
    let toast = document.querySelector(".toast");
    if (!toast) {
      toast = document.createElement("div");
      toast.className = "toast";
      toast.setAttribute("role", "status");
      toast.setAttribute("aria-live", "polite");
      document.body.appendChild(toast);
    }
    toast.textContent = mensaje;
    toast.classList.add("is-visible");
    clearTimeout(toast._timer);
    toast._timer = setTimeout(() => toast.classList.remove("is-visible"), 2200);
  }

  document.addEventListener("DOMContentLoaded", () => {
    initNavToggle();
    markActiveLink();
    initSearchForms();
    initAddToCartDelegation();
  });

  global.ChocoUI = { showToast, buildProductCard };
})(window);
