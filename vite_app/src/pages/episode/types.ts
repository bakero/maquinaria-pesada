// Tipos de los handlers que App inyecta a las páginas.
export type NavFn = (page: string, payload?: string) => void;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type OpenAIFn = (ctx: any) => void;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type OpenFixFn = (ctx: any) => void;
