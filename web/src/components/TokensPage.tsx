import { useMemo } from "react";
import indexCss from "../index.css?raw";
import appCss from "../App.css?raw";
import "./TokensPage.css";

// Página de tokens (/#tokens): lista todas las custom properties de :root,
// leyendo el valor resuelto en vivo del navegador y contando usos en App.css.
// Al final lista los valores literales todavía sin tokenizar. Es una página
// de desarrollo/documentación: no la enlaza nadie desde la app.

interface Token {
  name: string;
  raw: string; // tal cual está escrito en index.css (puede ser var(...))
  group: string;
}

const GROUPS: [string, (n: string) => boolean][] = [
  ["Colors", (n) => n.startsWith("--color-")],
  ["Radius", (n) => n.startsWith("--radius-")],
  ["Spacing", (n) => n.startsWith("--space-")],
  ["Type scale", (n) => n.startsWith("--font-size-")],
];

const stripComments = (css: string) => css.replace(/\/\*[\s\S]*?\*\//g, "");

function parseRootTokens(): Token[] {
  const css = stripComments(indexCss);
  const rootBlock = css.match(/:root\s*\{([\s\S]*?)\n\}/)?.[1] ?? "";
  const out: Token[] = [];
  for (const m of rootBlock.matchAll(/(--[\w-]+)\s*:\s*([^;]+);/g)) {
    const name = m[1];
    const group = GROUPS.find(([, test]) => test(name))?.[0] ?? "Other";
    out.push({ name, raw: m[2].trim().replace(/\s+/g, " "), group });
  }
  return out;
}

function countUses(name: string): number {
  const re = new RegExp(`var\\(\\s*${name}\\b`, "g");
  return (appCss.match(re)?.length ?? 0) + (indexCss.match(re)?.length ?? 0);
}

// Valores literales en App.css que podrían ser (o reutilizar) un token.
function scanLiterals(): Record<string, [string, number][]> {
  const css = stripComments(appCss);
  const tally = (map: Record<string, number>, v: string) => {
    map[v] = (map[v] ?? 0) + 1;
  };
  const colors: Record<string, number> = {};
  const spacing: Record<string, number> = {};
  const fontSizes: Record<string, number> = {};
  const radii: Record<string, number> = {};

  for (const m of css.matchAll(/(#[0-9a-fA-F]{3,8}\b|rgba?\([^)]*\))/g)) tally(colors, m[1].replace(/\s+/g, " "));

  for (const m of css.matchAll(/(?:^|[;{\s])(padding[\w-]*|gap|row-gap|column-gap)\s*:\s*([^;}]+)/g)) {
    for (const px of m[2].matchAll(/(?<![\w(-])(\d+(?:\.\d+)?)px/g)) {
      if (px[1] !== "0" && px[1] !== "1") tally(spacing, `${px[1]}px`);
    }
  }
  for (const m of css.matchAll(/font-size\s*:\s*([^;}]+)/g)) {
    if (!m[1].includes("var(")) tally(fontSizes, m[1].trim());
  }
  for (const m of css.matchAll(/border-radius\s*:\s*([^;}]+)/g)) {
    if (!m[1].includes("var(")) tally(radii, m[1].trim());
  }

  const sorted = (o: Record<string, number>): [string, number][] =>
    Object.entries(o).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  return {
    "Colors (hex / rgb outside :root)": sorted(colors),
    "Spacing (padding / gap in px)": sorted(spacing),
    "Font size": sorted(fontSizes),
    "Border radius": sorted(radii),
  };
}

function Preview({ token, value }: { token: Token; value: string }) {
  const n = token.name;
  if (n.startsWith("--color-")) {
    return <span className="tk-swatch" style={{ background: `var(${n})` }} />;
  }
  if (n.startsWith("--radius-")) {
    return <span className="tk-box" style={{ borderRadius: `var(${n})` }} />;
  }
  if (n.startsWith("--space-")) {
    return <span className="tk-space" style={{ width: `var(${n})` }} />;
  }
  if (n.startsWith("--font-size-")) {
    return <span style={{ fontSize: `var(${n})` }}>Tracing origins</span>;
  }
  return <span className="tk-muted">{value}</span>;
}

export default function TokensPage() {
  const tokens = useMemo(parseRootTokens, []);
  const literals = useMemo(scanLiterals, []);
  const computed = getComputedStyle(document.documentElement);

  const groupNames = [...GROUPS.map(([g]) => g), "Other"];

  return (
    <main className="tk-page">
      <header className="tk-head">
        <h1>Design tokens</h1>
        <p>
          Every custom property on <code>:root</code> in <code>index.css</code>, with its resolved value read live from
          the browser and how many times <code>App.css</code> uses it. <a href="#">← Back to the app</a>
        </p>
        <nav className="tk-toc">
          {groupNames
            .filter((g) => tokens.some((t) => t.group === g))
            .map((g) => (
              <a key={g} href={`#tokens`} onClick={(e) => {
                e.preventDefault();
                document.getElementById(`tk-${g}`)?.scrollIntoView({ behavior: "smooth" });
              }}>
                {g}
              </a>
            ))}
          <a
            href="#tokens"
            onClick={(e) => {
              e.preventDefault();
              document.getElementById("tk-raw")?.scrollIntoView({ behavior: "smooth" });
            }}
          >
            Not tokenized yet
          </a>
        </nav>
      </header>

      {groupNames.map((g) => {
        const list = tokens.filter((t) => t.group === g);
        if (!list.length) return null;
        return (
          <section key={g} id={`tk-${g}`} className="tk-section">
            <h2>
              {g} <span>{list.length}</span>
            </h2>
            <table className="tk-table">
              <thead>
                <tr>
                  <th>Token</th>
                  <th>Preview</th>
                  <th>Value</th>
                  <th>Used</th>
                </tr>
              </thead>
              <tbody>
                {list.map((t) => {
                  const value = computed.getPropertyValue(t.name).trim();
                  const uses = countUses(t.name);
                  return (
                    <tr key={t.name}>
                      <td>
                        <code className="tk-name">{t.name}</code>
                      </td>
                      <td>
                        <Preview token={t} value={value} />
                      </td>
                      <td>
                        <code>{t.raw}</code>
                        {value && value !== t.raw && <small>→ {value}</small>}
                      </td>
                      <td className={uses === 0 ? "tk-unused" : ""}>{uses === 0 ? "unused" : `${uses} ${uses === 1 ? "use" : "uses"}`}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </section>
        );
      })}

      <section id="tk-raw" className="tk-section">
        <h2>Not tokenized yet</h2>
        <p className="tk-note">
          Literal values written straight into <code>App.css</code> (outside <code>:root</code>). Each one is a candidate
          for a token, or for merging into an existing one. Layout offsets (top / left / width) aren't scanned on purpose.
        </p>
        {Object.entries(literals).map(([title, rows]) => (
          <div key={title} className="tk-raw">
            <h3>
              {title} <span>{rows.length} distinct</span>
            </h3>
            {rows.length === 0 ? (
              <p className="tk-note">All tokenized ✓</p>
            ) : (
              <table className="tk-table">
                <tbody>
                  {rows.map(([v, count]) => (
                    <tr key={v}>
                      <td className="tk-rawval">
                        {title.startsWith("Colors") && <span className="tk-swatch tk-swatch-sm" style={{ background: v }} />}
                        <code>{v}</code>
                      </td>
                      <td className="tk-count">×{count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        ))}
      </section>
    </main>
  );
}
