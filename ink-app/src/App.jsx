import { Component, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Compiler } from "inkjs/full";

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }
  static getDerivedStateFromError(error) {
    return { error };
  }
  componentDidCatch(error, info) {
    console.error("Ink app crashed:", error, info);
  }
  reset = () => this.setState({ error: null });
  render() {
    if (this.state.error) {
      return (
        <div className="banner error">
          <strong>Runtime error</strong>
          <div style={{ marginTop: 6, fontFamily: "ui-monospace, Menlo, monospace", fontSize: "0.78rem" }}>
            {String(this.state.error?.message ?? this.state.error)}
          </div>
          <button className="btn" style={{ marginTop: 8 }} onClick={this.reset}>
            Dismiss
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

function FileDrop({ onLoad, fileName }) {
  const inputRef = useRef(null);
  const [drag, setDrag] = useState(false);

  const readFile = useCallback(
    (file) => {
      const reader = new FileReader();
      reader.onload = (e) => onLoad(file.name, String(e.target?.result ?? ""));
      reader.readAsText(file);
    },
    [onLoad],
  );

  const onChange = (e) => {
    const f = e.target.files?.[0];
    if (f) readFile(f);
    // Reset so picking the same file again still triggers onChange.
    e.target.value = "";
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDrag(false);
    const f = e.dataTransfer.files?.[0];
    if (f) readFile(f);
    if (inputRef.current) inputRef.current.value = "";
  };

  const openPicker = () => {
    if (!inputRef.current) return;
    inputRef.current.value = "";
    inputRef.current.click();
  };

  return (
    <div
      className={`dropzone ${drag ? "drag" : ""}`}
      onClick={openPicker}
      onDragOver={(e) => {
        e.preventDefault();
        setDrag(true);
      }}
      onDragLeave={() => setDrag(false)}
      onDrop={onDrop}
    >
      <div>Drop a .ink file here, or click to browse.</div>
      <input
        ref={inputRef}
        type="file"
        accept=".ink,.txt,text/plain"
        onChange={onChange}
      />
      {fileName ? <div className="file-meta">{fileName}</div> : null}
    </div>
  );
}

const ALLOWED_TAGS = new Set(["i", "em", "b", "strong", "u", "br"]);

const ALLOWED_INK_TAGS = new Set([
  "speaker",
  "portrait",
  "layout",
  "cutscene",
  "unknown",
  "emotion",
  "textEffects",
]);

const ALLOWED_LAYOUT_VALUES = new Set(["Left", "Right"]);

function parseInkTag(rawTag) {
  // Ink tags are stored as plain strings. Conventional form: "name: value".
  const idx = rawTag.indexOf(":");
  if (idx === -1) return { name: rawTag.trim(), value: null };
  return {
    name: rawTag.slice(0, idx).trim(),
    value: rawTag.slice(idx + 1).trim(),
  };
}

function validateInkTags(tags) {
  const errors = [];
  for (const raw of tags) {
    const { name, value } = parseInkTag(raw);
    if (!ALLOWED_INK_TAGS.has(name)) {
      errors.push(
        `Disallowed tag '${name}' (raw: '${raw}'). Allowed: ${[...ALLOWED_INK_TAGS].join(", ")}.`,
      );
      continue;
    }
    if (name === "layout") {
      if (value === null || !ALLOWED_LAYOUT_VALUES.has(value)) {
        errors.push(
          `Invalid layout value '${value ?? ""}' (raw: '${raw}'). Must be exactly 'Left' or 'Right'.`,
        );
      }
    }
  }
  return errors;
}

function renderRichText(text) {
  // Parse a small allowed subset of HTML-style tags safely. Strips anything else.
  const out = [];
  const re = /<\s*\/?\s*([a-zA-Z]+)\s*\/?\s*>/g;
  let cursor = 0;
  const stack = [{ tag: null, children: [] }];
  let m;

  const append = (node) => {
    stack[stack.length - 1].children.push(node);
  };

  while ((m = re.exec(text)) !== null) {
    const before = text.slice(cursor, m.index);
    if (before) append(before);
    cursor = re.lastIndex;

    const raw = m[0];
    const name = m[1].toLowerCase();
    const isClose = /^<\s*\//.test(raw);
    const isSelfClosing = /\/\s*>$/.test(raw) || name === "br";

    if (!ALLOWED_TAGS.has(name)) {
      // Unknown tag: render its raw text as a plain string (escaped via React).
      append(raw);
      continue;
    }

    if (name === "br" || isSelfClosing) {
      append({ tag: name, children: [] });
      continue;
    }

    if (isClose) {
      // pop until matching tag
      for (let i = stack.length - 1; i > 0; i--) {
        if (stack[i].tag === name) {
          const popped = stack.splice(i)[0];
          append(popped);
          break;
        }
      }
    } else {
      stack.push({ tag: name, children: [] });
    }
  }
  const tail = text.slice(cursor);
  if (tail) append(tail);

  // Close any unclosed tags by flattening upward.
  while (stack.length > 1) {
    const popped = stack.pop();
    stack[stack.length - 1].children.push(popped);
  }

  const toReact = (node, key) => {
    if (typeof node === "string") return node;
    if (node.tag === "br") return <br key={key} />;
    const Tag = node.tag;
    return (
      <Tag key={key}>
        {node.children.map((c, i) => toReact(c, i))}
      </Tag>
    );
  };

  return stack[0].children.map((c, i) => toReact(c, i));
}

function extractExternalNames(source) {
  const names = new Set();
  const re = /^\s*EXTERNAL\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(/gm;
  let m;
  while ((m = re.exec(source)) !== null) names.add(m[1]);
  return [...names];
}

function bindNoopExternals(story, source) {
  const bound = [];
  for (const name of extractExternalNames(source)) {
    try {
      story.BindExternalFunction(name, () => null, true);
      bound.push(name);
    } catch (e) {
      console.warn(`Could not bind external '${name}':`, e);
    }
  }
  return bound;
}

function compileSource(source) {
  try {
    const story = new Compiler(source).Compile();
    const boundExternals = bindNoopExternals(story, source);
    return { story, errors: [], warnings: [], boundExternals };
  } catch (err) {
    const errors = [];
    const warnings = [];
    const message = err?.message || String(err);
    for (const line of message.split("\n")) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      if (/warning/i.test(trimmed)) warnings.push(trimmed);
      else errors.push(trimmed);
    }
    if (errors.length === 0 && warnings.length === 0) {
      errors.push(message);
    }
    return { story: null, errors, warnings, boundExternals: [] };
  }
}

function PlayerPanel({ source }) {
  const { story, errors, warnings, boundExternals } = useMemo(
    () => compileSource(source),
    [source],
  );

  const [version, setVersion] = useState(0);
  const [transcript, setTranscript] = useState([]);
  const seededFor = useRef(null);

  const continueMax = useCallback(() => {
    if (!story) return;
    try {
      const lines = [];
      while (story.canContinue) {
        const text = story.Continue();
        const tags = [...(story.currentTags || [])];
        if (text && text.trim()) lines.push({ kind: "line", text: text.trim() });
        if (tags.length) {
          const tagErrors = validateInkTags(tags);
          lines.push({ kind: "tags", tags });
          if (tagErrors.length) {
            for (const err of tagErrors) {
              lines.push({ kind: "error", text: err });
            }
            setTranscript((t) => [...t, ...lines]);
            setVersion((v) => v + 1);
            throw new Error(tagErrors[0]);
          }
        }
      }
      setTranscript((t) => [...t, ...lines]);
      setVersion((v) => v + 1);
    } catch (e) {
      setTranscript((t) => [
        ...t,
        { kind: "error", text: `[runtime error: ${e?.message ?? e}]` },
      ]);
    }
  }, [story]);

  const reset = useCallback(() => {
    if (!story) return;
    try {
      story.ResetState();
    } catch (e) {
      console.error("ResetState failed", e);
    }
    seededFor.current = null;
    setTranscript([]);
    setVersion((v) => v + 1);
  }, [story]);

  const continueOnce = useCallback(() => {
    if (!story || !story.canContinue) return;
    try {
      const text = story.Continue();
      const tags = [...(story.currentTags || [])];
      const tagErrors = tags.length ? validateInkTags(tags) : [];
      setTranscript((t) => {
        const next = [...t];
        if (text && text.trim()) next.push({ kind: "line", text: text.trim() });
        if (tags.length) next.push({ kind: "tags", tags });
        for (const err of tagErrors) next.push({ kind: "error", text: err });
        return next;
      });
      setVersion((v) => v + 1);
    } catch (e) {
      setTranscript((t) => [
        ...t,
        { kind: "error", text: `[runtime error: ${e?.message ?? e}]` },
      ]);
    }
  }, [story]);

  useEffect(() => {
    if (!story) return;
    if (seededFor.current === story) return;
    seededFor.current = story;
    const lines = [];
    try {
      while (story.canContinue) {
        const text = story.Continue();
        const tags = [...(story.currentTags || [])];
        if (text && text.trim()) lines.push({ kind: "line", text: text.trim() });
        if (tags.length) {
          const tagErrors = validateInkTags(tags);
          lines.push({ kind: "tags", tags });
          if (tagErrors.length) {
            for (const err of tagErrors) lines.push({ kind: "error", text: err });
            throw new Error(tagErrors[0]);
          }
        }
      }
      setTranscript(lines);
      setVersion((v) => v + 1);
    } catch (e) {
      lines.push({ kind: "error", text: `[runtime error: ${e?.message ?? e}]` });
      setTranscript(lines);
      setVersion((v) => v + 1);
    }
  }, [story]);

  const choose = useCallback(
    (idx) => {
      if (!story) return;
      const choice = story.currentChoices[idx];
      story.ChooseChoiceIndex(idx);
      setTranscript((t) => [
        ...t,
        { kind: "choice", text: `> ${choice.text}` },
      ]);
      setVersion((v) => v + 1);
    },
    [story],
  );

  if (errors.length > 0) {
    return (
      <>
        <div className="banner error">
          <strong>Compile failed</strong>
          <ul className="errors-list">
            {errors.map((e, i) => (
              <li key={`e${i}`}>{e}</li>
            ))}
          </ul>
        </div>
        {warnings.length > 0 ? (
          <div className="banner warn">
            <strong>Warnings</strong>
            <ul className="errors-list">
              {warnings.map((w, i) => (
                <li key={`w${i}`}>{w}</li>
              ))}
            </ul>
          </div>
        ) : null}
      </>
    );
  }

  // suppress unused warning; version forces re-render after story mutation
  void version;

  const choices = story?.currentChoices ?? [];
  const canContinue = !!story?.canContinue;
  const ended = !canContinue && choices.length === 0 && transcript.length > 0;

  return (
    <div className="player">
      <div className="player-controls">
        <div className="banner ok">Compiled successfully.</div>
        {warnings.length > 0 ? (
          <div className="banner warn">
            <strong>Warnings</strong>
            <ul className="errors-list">
              {warnings.map((w, i) => (
                <li key={`w${i}`}>{w}</li>
              ))}
            </ul>
          </div>
        ) : null}
        {boundExternals && boundExternals.length > 0 ? (
          <div className="banner warn">
            <strong>External functions stubbed (no-op):</strong>{" "}
            <code>{boundExternals.join(", ")}</code>
          </div>
        ) : null}

        <div className="state-row">
          <span>
            <strong>
              {transcript.filter((t) => t.kind === "line").length}
            </strong>{" "}
            lines
          </span>
          <span>
            canContinue: <strong>{String(canContinue)}</strong>
          </span>
          <span>
            choices: <strong>{choices.length}</strong>
          </span>
        </div>

        <div className="btn-row">
          <button
            className="btn primary"
            onClick={continueOnce}
            disabled={!canContinue}
          >
            Continue (1 step)
          </button>
          <button className="btn" onClick={continueMax} disabled={!canContinue}>
            Continue to next choice
          </button>
          <button className="btn" onClick={reset}>
            Restart
          </button>
        </div>
      </div>

      <div className="transcript">
        {transcript.length === 0 ? (
          <div className="muted">
            Press <em>Continue</em> to begin playback.
          </div>
        ) : (
          transcript.map((entry, i) => {
            if (entry.kind === "line")
              return (
                <div key={i} className="line">
                  {renderRichText(entry.text)}
                </div>
              );
            if (entry.kind === "choice")
              return (
                <div key={i} className="line choice-made">
                  {renderRichText(entry.text)}
                </div>
              );
            if (entry.kind === "tags")
              return (
                <div key={i} className="line tag">
                  # {entry.tags.join(", ")}
                </div>
              );
            if (entry.kind === "error")
              return (
                <div key={i} className="line line-error">
                  {entry.text}
                </div>
              );
            return null;
          })
        )}
        {ended ? <div className="muted">— end of story —</div> : null}
      </div>

      {choices.length > 0 ? (
        <div className="choices">
          {choices.map((c, i) => (
            <button
              key={i}
              className="choice-btn"
              onClick={() => choose(i)}
            >
              {renderRichText(c.text)}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}

export default function App() {
  const [fileName, setFileName] = useState("");
  const [source, setSource] = useState("");

  const onLoad = (name, text) => {
    setFileName(name);
    setSource(text);
  };

  return (
    <div className="app">
      <aside className="sidebar">
        <h1>Ink Validator</h1>
        <p>
          Compile and step through <code>.ink</code> dialogue files in your
          browser. No files leave your machine.
        </p>

        <h2>File</h2>
        <FileDrop onLoad={onLoad} fileName={fileName} />
        {source ? (
          <div className="btn-row">
            <button
              className="btn"
              onClick={() => {
                setFileName("");
                setSource("");
              }}
            >
              Clear
            </button>
          </div>
        ) : null}

        <h2>About</h2>
        <p>
          Powered by{" "}
          <a
            href="https://github.com/y-lohse/inkjs"
            target="_blank"
            rel="noreferrer"
            style={{ color: "var(--accent)" }}
          >
            inkjs
          </a>
          . Validation runs on every change.
        </p>
      </aside>

      <main className="main">
        {!source ? (
          <div className="muted">Load a .ink file to begin.</div>
        ) : (
          <>
            <div className="file-header">
              <span className="file-header-label">Analyzing</span>
              <span className="file-header-name">{fileName || "(untitled)"}</span>
              <span className="file-header-meta">
                {source.length.toLocaleString()} chars
              </span>
            </div>
            <div className="split">
              <section className="split-pane">
                <div className="split-pane-title">Source</div>
                <textarea
                  className="source-view"
                  value={source}
                  onChange={(e) => setSource(e.target.value)}
                  spellCheck={false}
                />
              </section>
              <section className="split-pane">
                <div className="split-pane-title">Walkthrough</div>
                <ErrorBoundary key={fileName + ":" + source.length}>
                  <PlayerPanel source={source} />
                </ErrorBoundary>
              </section>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
