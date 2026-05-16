// Barrel de páginas del cockpit.
export { PageInicio } from "./PageInicio";
export { PageMaster } from "./PageMaster";
export { PageModulo } from "./PageModulo";
export { PagePizarra } from "./PagePizarra";
export { PageMapa } from "./PageMapa";
export { PageConectores } from "./PageConectores";
export { PageLanzador } from "./PageLanzador";
export { PageFuentes } from "./PageFuentes";
export { PagePlayer } from "./PagePlayer";
export { PageLogs } from "./PageLogs";
export { PageOptimizar } from "./PageOptimizar";
export { PageConsumo } from "./PageConsumo";
export { PageAjustes } from "./PageAjustes";
export { PageMetricas } from "./PageMetricas";
export { PageEpisodio } from "./episode/PageEpisodio";

// v2 — wrappers anteriores
export { PageDatos }    from "./PageDatos";
export { PagePipeline } from "./PagePipeline";
export { PageRecursos } from "./PageRecursos";

// v3 — industrial · sólo estas tres páginas son las visibles desde el top-nav.
//  Producción  → PageProduccion (master + alertas + KPIs)
//                PageModuloTema (drill-down a Mn y Mn_Tk)
//  Datos       → PageDatos (subnav: consumo · métricas · optimización · logs)
//  Sistema     → PageSistema (subnav: conectores · lanzador · fuentes · mapa · ajustes)
export { PageProduccion } from "./PageProduccion";
export { PageModuloTema } from "./PageModuloTema";
export { PageSistema }    from "./PageSistema";
