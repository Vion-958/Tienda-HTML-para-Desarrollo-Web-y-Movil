// Carrito en localStorage, compartido como window.ChocoCart.

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
      // Sin localStorage el carrito no persiste.
    }
    notify();
  }

  function notify() {
    document.dispatchEvent(new CustomEvent("chocomania:cart-updated"));
  }

  // Tope por stock conocido; null = sin dato.
  function tope(stock) {
    return typeof stock === "number" && stock >= 0 ? stock : Infinity;
  }

  // Devuelve cuantas unidades se agregaron (0 si no queda stock).
  function addItem(producto, cantidad) {
    cantidad = cantidad && cantidad > 0 ? cantidad : 1;
    const items = getItems();
    let item = items.find((it) => it.id === producto.id);
    if (!item) {
      item = { id: producto.id, nombre: producto.nombre, precio: producto.precio, imagen: producto.imagen || null, cantidad: 0 };
      items.push(item);
    }
    if (typeof producto.stock === "number") item.stock = producto.stock;
    const agregados = Math.max(0, Math.min(cantidad, tope(item.stock) - item.cantidad));
    item.cantidad += agregados;
    saveItems(items.filter((it) => it.cantidad > 0));
    return agregados;
  }

  function setQty(id, cantidad) {
    const items = getItems();
    const item = items.find((it) => it.id === id);
    if (!item) return;
    item.cantidad = Math.max(1, Math.min(cantidad, tope(item.stock)));
    saveItems(items);
  }

  function enCarrito(id) {
    const item = getItems().find((it) => it.id === id);
    return item ? item.cantidad : 0;
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
    enCarrito,
    setQty,
    removeItem,
    clear,
    count,
    subtotal,
    updateBadges,
  };
})(window);
