// Barrel de páginas del cockpit · v3 industrial.
//
// Solo se exportan las páginas vivas. Las versiones legacy (PageInicio,
// PageMaster, PageModulo, PagePizarra, PagePlayer, PageEpisodio,
// PagePipeline, PageRecursos) se eliminaron en la limpieza de bundle v3.

// Páginas v3 montadas directamente por el shell
export { PageProduccion } from "./PageProduccion";
export { PageModuloTema } from "./PageModuloTema";
export { PageDatos }      from "./PageDatos";
export { PageSistema }    from "./PageSistema";

// Sub-páginas embebidas dentro de PageDatos / PageSistema
export { PageConsumo }    from "./PageConsumo";
export { PageMetricas }   from "./PageMetricas";
export { PageOptimizar }  from "./PageOptimizar";
export { PageLogs }       from "./PageLogs";
export { PageConectores } from "./PageConectores";
export { PageLanzador }   from "./PageLanzador";
export { PageFuentes }    from "./PageFuentes";
export { PageMapa }       from "./PageMapa";
export { PageAjustes }    from "./PageAjustes";
