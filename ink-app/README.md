# Ink Dialogue Validator (SPA)

Vite + React app that compiles `.ink` files in the browser using
[inkjs](https://github.com/y-lohse/inkjs) and lets you step through the
resulting story.

## Quick start

```bash
cd ink-app
npm install
npm run dev      # http://localhost:5173
```

Build for production:

```bash
npm run build
npm run preview
```

## Features

- Drag-and-drop `.ink` upload (everything stays client-side).
- Continuous compile-on-change — errors and warnings surface in the **Play** tab.
- Step-through playback: `Continue (1 step)`, `Continue to next choice`,
  `Restart`. Choices render as clickable buttons.
- `Source` tab to view/edit the loaded `.ink` text.
- Built-in sample story.
