import { Panel, SourceTitle } from "../../../components";

export interface TabLogsProps {
  epId: string;
}

export function TabLogs({ epId }: TabLogsProps) {
  return (
    <Panel
      title={<SourceTitle kind="logs" epId={epId} customPath={`logs/2026-05-12_${epId}.jsonl`} />}
      meta="auto-refresh 3s"
    >
      <pre className="code" style={{ maxHeight: 480, overflow: "auto" }}>
{`{"t":"12:14:02","lvl":"ERROR","src":"eleven","msg":"502 Bad Gateway","blk":4,"retry":2}
{"t":"12:13:38","lvl":"WARN", "src":"eleven","msg":"502 Bad Gateway","blk":4,"retry":1}
{"t":"12:13:14","lvl":"INFO", "src":"eleven","msg":"block synthesized","blk":3,"dur":1.04,"cost":0.018}
{"t":"12:12:50","lvl":"INFO", "src":"eleven","msg":"block synthesized","blk":2,"dur":1.88,"cost":0.032}
{"t":"12:12:18","lvl":"INFO", "src":"eleven","msg":"block synthesized","blk":1,"dur":0.42,"cost":0.008}
{"t":"12:12:02","lvl":"INFO", "src":"runner","msg":"starting audio generation","blocks":7}
{"t":"12:11:48","lvl":"INFO", "src":"escaleta","msg":"7 blocks parsed","total_words":5530}
{"t":"12:11:30","lvl":"INFO", "src":"guion","msg":"script loaded","words":9842,"turns":142}
{"t":"12:11:24","lvl":"INFO", "src":"runner","msg":"M3_T2 pipeline start","mode":"v2"}`}
      </pre>
    </Panel>
  );
}
