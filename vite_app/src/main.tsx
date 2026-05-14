// Entry-point del cockpit Vite + React 18.
// Carga los estilos globales y delega el montaje al bundle legacy
// concatenado (cockpit-bundle.jsx), que llama a `createRoot` al final
// de app.jsx tras esperar a /api/bootstrap.
import "./styles.css";
import "./cockpit-bundle.jsx";
