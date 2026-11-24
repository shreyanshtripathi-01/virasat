/* Register the optional service worker. This is the only page script in Virasat. */
if ("serviceWorker" in navigator) {
  window.addEventListener("load", function () {
    navigator.serviceWorker.register("/sw.js").catch(function () {
      /* Installation is optional; the website keeps working without it. */
    });
  });
}
