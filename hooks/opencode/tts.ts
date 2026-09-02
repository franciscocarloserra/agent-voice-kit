// OpenCode plugin: read assistant replies aloud through the local TTS engine. Toggle per session with /tts (off by default).
// Config: ~/.config/opencode/tts.json  {ttsBin, maxChars, gateFile}. Gate: gateFile exists -> on. Global and persistent, shared with other harnesses.
import type { Plugin } from "@opencode-ai/plugin"
import { spawn } from "node:child_process"
import { readFileSync, existsSync, writeFileSync, unlinkSync } from "node:fs"
import { homedir } from "node:os"
import { join } from "node:path"

const CFG = join(homedir(), ".config/opencode/tts.json")
function cfg() {
  const d = { ttsBin: join(homedir(), "projects/know-how/local-tts/tts"), maxChars: 1500, gateFile: join(homedir(), ".config/agent-voice-kit/tts-on") }
  try { return { ...d, ...JSON.parse(readFileSync(CFG, "utf8")) } } catch { return d }
}
function clean(t: string, max: number) {
  t = t.replace(/```[\s\S]*?```/g, " ").replace(/`[^`]*`/g, " ").replace(/\[([^\]]*)\]\([^)]*\)/g, "$1").replace(/[*_#>|]+/g, " ")
  return t.replace(/\s+/g, " ").trim().slice(0, max)
}

export const TtsPlugin: Plugin = async ({ client }) => {
  const isOn = () => existsSync(cfg().gateFile)
  const toast = (message: string) => client.tui.showToast({ body: { message, variant: "info" } }).catch(() => {})
  return {
    "command.execute.before": async (input, output) => {
      if (input.command !== "tts") return
      const g = cfg().gateFile
      const want = input.arguments.trim() === "on" ? true : input.arguments.trim() === "off" ? false : !isOn()
      try { want ? writeFileSync(g, "") : unlinkSync(g) } catch {}
      await toast(`tts ${want ? "on" : "off"}`)
      output.parts.length = 0   // nothing goes to the model
    },
    event: async ({ event }) => {
      if (event.type !== "session.idle") return
      const s = (event as any).properties.sessionID
      if (!isOn()) return
      const c = cfg()
      const res = await client.session.messages({ path: { id: s } })
      const msgs = (res as any).data ?? res
      const last = [...msgs].reverse().find((m: any) => m.info?.role === "assistant")
      if (!last) return
      const text = clean(last.parts.filter((p: any) => p.type === "text" && !p.synthetic).map((p: any) => p.text).join("\n"), c.maxChars ?? 1500)
      if (!text) return
      const p = spawn(c.ttsBin, [text], { stdio: "ignore", detached: true }); p.unref()
    },
  }
}
