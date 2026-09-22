/* ChocoManía — carrito de compras persistido en localStorage.
   Se comparte entre todas las páginas mediante window.ChocoCart. */

(function (global) {
  const STORAGE_KEY = "chocomania_cart_v1";

  function getItems() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      const items = raw ? JSON.parse(raw) : [];
      return Array.isArray(items) ? items : [];
    } catch (err) {
      return [];
    }
  }

  function saveItems(items) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
    } catch (err) {
      /* localStorage no disponible (modo privado, etc.): el carrito
         simplemente no persistirá entre recargas. */
    }
    notify();
  }

  function notify() {
    document.dispatchEvent(new CustomEvent("chocomania:cart-updated"));
  }

  function addItem(producto, cantidad) {
    cantidad = cantidad && cantidad > 0 ? cantidad : 1;
    const items = getItems();
    const existente = items.find((it) => it.id === producto.id);
    if (existente) {
      existente.cantidad += cantidad;
    } else {
      items.push({
        id: producto.id,
        nombre: producto.nombre,
        precio: producto.precio,
        imagen: producto.imagen || null,
        cantidad,
      });
    }
    saveItems(items);
  }

  function setQty(id, cantidad) {
    const items = getItems();
    const item = items.find((it) => it.id === id);
    if (!item) return;
    item.cantidad = Math.max(1, cantidad);
    saveItems(items);
  }

  function removeItem(id) {
    saveItems(getItems().filter((it) => it.id !== id));
  }

  function clear() {
    saveItems([]);
  }

  function count(items) {
    return (items || getItems()).reduce((sum, it) => sum + it.cantidad, 0);
  }

  function subtotal(items) {
    return (items || getItems()).reduce(
      (sum, it) => sum + it.precio * it.cantidad,
      0
    );
  }

  function updateBadges() {
    const total = count();
    document.querySelectorAll("[data-cart-badge]").forEach((el) => {
      el.textContent = String(total);
    });
  }

  document.addEventListener("chocomania:cart-updated", updateBadges);
  document.addEventListener("DOMContentLoaded", updateBadges);

  global.ChocoCart = {
    getItems,
    addItem,
    setQty,
    removeItem,
    clear,
    count,
    subtotal,
    updateBadges,
  };
})(window);
