# Evidence Manager

Evidence Manager is a cross-platform desktop application for cataloguing people, their information, quotes, and supporting evidence. The project now ships as a Tauri 2.0 application with a lightweight static web UI and a Rust backend.

## Features

- **Person Management** – Create and delete people, store structured information, and capture quotes.
- **Evidence Library** – Keep every person's related files organised by media type on disk.
- **Import & Export** – Move entire collections between machines using Evidence Manager Archive (`.ema`) files.
- **Search & Filter** – Quickly locate people through a responsive search panel.
- **Cross-platform** – Built with Tauri 2.0 and pure Rust so it runs on Windows, macOS, and Linux.

## Project Structure

```
frontend/            # Static web UI loaded directly by Tauri
  css/               # Styling for the single-page interface
  js/                # Front-end behaviour and Tauri command bindings
  index.html         # Entry point served inside the Tauri window

tauri-src/           # Rust backend crate
  src/               # Backend application source
  tauri.conf.json    # Tauri configuration (dist directory, window settings)
  Cargo.toml         # Backend crate manifest

Cargo.toml           # Workspace manifest pointing at the backend crate
Evidence/            # Created at runtime to store person folders and evidence
```

The backend reuses the original Rust domain logic for working with people, evidence files, and archive import/export. Commands are exposed to the frontend via Tauri's `invoke` API.

## Running the App

### Requirements
- Rust 1.70+ with the `cargo` toolchain
- System dependencies required by [Tauri 2.0](https://tauri.app/v2) (GTK on Linux, WebView2 on Windows, etc.)

### Development
```bash
# Install the frontend dependencies (none required – it's a static site)

# Install the CLI once if you don't have it yet
cargo install tauri-cli --version ^2

# Run the Tauri app in debug mode
cargo tauri dev --manifest-path tauri-src/Cargo.toml
```

### Release Build
```bash
cargo tauri build --manifest-path tauri-src/Cargo.toml
```

The compiled application bundles the static assets found in `frontend/` and uses them directly without a Node runtime.

## Evidence Folder Layout

```
Evidence/
├── Person_Name/
│   ├── person_data.json
│   ├── images/
│   ├── audio/
│   ├── videos/
│   ├── documents/
│   └── quotes/
└── ...
```

## Commands Exposed to the Frontend

The Rust backend registers the following Tauri commands:

- `list_persons` – Retrieve every person stored on disk.
- `add_person`, `delete_person` – Manage person records.
- `add_information`, `remove_information` – Maintain key-value information entries.
- `add_quote`, `remove_quote` – Track quotes with dates, times, and locations.
- `scan_evidence`, `add_evidence` – Inspect or copy evidence files for a person.
- `import_archive`, `export_archive` – Handle `.ema` archive import/export operations.

Refer to `frontend/js/app.js` for examples of invoking these commands from the UI.

## License

This project is licensed under the MIT License.
