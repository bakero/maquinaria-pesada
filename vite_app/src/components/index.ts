// Barrel del sistema de componentes del cockpit.
// Estos son los componentes canónicos: el bundle los importa de aquí en
// lugar de redefinirlos (split incremental fuera del monolito).

export { Btn } from "./Btn";
export type { BtnProps, BtnKind, BtnSize } from "./Btn";

export { Icon } from "./Icon";
export type { IconProps, IconName } from "./Icon";

export { Panel } from "./Panel";
export type { PanelProps } from "./Panel";

export { Kpi } from "./Kpi";
export type { KpiProps } from "./Kpi";

export { StatusDot } from "./StatusDot";
export type { StatusDotProps } from "./StatusDot";

export { Bar } from "./Bar";
export type { BarProps } from "./Bar";

export { Badge } from "./Badge";
export type { BadgeProps } from "./Badge";

export { Ring } from "./Ring";
export type { RingProps } from "./Ring";

export { Speaker } from "./Speaker";
export type { SpeakerProps } from "./Speaker";

export { HazardTape } from "./HazardTape";

export { KindCell } from "./KindCell";
export type { KindCellProps } from "./KindCell";

export { PageHeader } from "./PageHeader";
export type { PageHeaderProps } from "./PageHeader";

export { SourcePills } from "./SourcePills";
export type { SourcePillsProps } from "./SourcePills";

export { SourceTitle } from "./SourceTitle";
export type { SourceTitleProps } from "./SourceTitle";

export { GenGuionPanel } from "./GenGuionPanel";
export type { GenGuionPanelProps } from "./GenGuionPanel";
