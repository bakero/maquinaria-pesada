export interface SpeakerProps {
  who: "iago" | "maria" | string;
}

export function Speaker({ who }: SpeakerProps) {
  const name = who === "iago" ? "IAGO" : "MARÍA";
  return (
    <span className={`spk spk-${who}`}>
      <span className="spk-dot" />
      <span className="spk-name">{name}</span>
    </span>
  );
}
