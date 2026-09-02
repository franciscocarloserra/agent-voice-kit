// Pipes finalized assistant messages to the local tts script.
// Config: ~/.pi/agent/tts-hook.json (reloaded on every message). Gate: config.gateFile must exist (voice-on / voice-off aliases).
import { spawn } from "node:child_process";
import { existsSync, readFileSync, appendFileSync, writeFileSync, unlinkSync } from "node:fs";
const LOG = "/tmp/tts-hook.log";
const log = (m: string) => { try { appendFileSync(LOG, `${new Date().toISOString()} ${m}\n`); } catch {} };
import { homedir } from "node:os";
import { join } from "node:path";

const CFG = join(homedir(), ".pi/agent/tts-hook.json");

function cfg() {
  try { return JSON.parse(readFileSync(CFG, "utf8")); } catch { return { enabled: false }; }
}

function clean(text: string, c: any): string {
  let t = text;
  if (c.stripCodeBlocks) t = t.replace(/```[\s\S]*?```/g, " ");
  if (c.stripMarkdown) t = t.replace(/`[^`]*`/g, " ").replace(/[*_#>|]+/g, " ").replace(/\[([^\]]*)\]\([^)]*\)/g, "$1");
  t = t.replace(/\s+/g, " ").trim();
  return c.maxChars ? t.slice(0, c.maxChars) : t;
}

export default function (pi: any) {
  const gate = () => cfg().gateFile || join(homedir(), ".config/agent-voice-kit/tts-on");
  const isOn = () => existsSync(gate());
  log("loaded");
  pi.registerCommand("tts", {
    description: "Toggle TTS of assistant replies (global, persistent)",
    handler: async (a: string, ctx: any) => {
      const want = a.trim() === "on" ? true : a.trim() === "off" ? false : !isOn();
      try { want ? writeFileSync(gate(), "") : unlinkSync(gate()); } catch {}
      ctx.ui.notify(`tts ${want ? "on" : "off"}`);
    },
  });
  pi.on("message_end", async (event: any) => {
    if (!isOn() || event.message.role !== "assistant") return;
    const c = cfg();
    if (!c.enabled) return;
    const text = (event.message.content || [])
      .filter((b: any) => b.type === "text").map((b: any) => b.text).join("\n");
    const t = clean(text, c);
    log(`text=${JSON.stringify(t).slice(0,120)} content=${JSON.stringify(event.message.content).slice(0,200)}`);
    if (!t) return;
    const p = spawn(c.ttsBin, c.voice ? ["-v", c.voice, t] : [t], { stdio: "ignore", detached: true });
    p.unref();
  });
}
