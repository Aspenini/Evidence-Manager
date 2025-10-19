# GitHub Workflows for Evidence Manager

This directory contains GitHub Actions workflows for building Evidence Manager across multiple platforms.

## Available Workflows

### 1. `build.yml` - Main Build Workflow
Builds Evidence Manager for the main supported platforms:
- **Windows** (x86_64-pc-windows-msvc)
- **Linux** (x86_64-unknown-linux-gnu)
- **macOS Intel** (x86_64-apple-darwin)
- **macOS Apple Silicon** (aarch64-apple-darwin)

**Usage:**
1. Go to the Actions tab in your GitHub repository
2. Select "Build Evidence Manager" workflow
3. Click "Run workflow"
4. Choose build type (release/debug)
5. Click "Run workflow"

### 2. FreeBSD Support
FreeBSD support will be added in a future update.

## Build Artifacts

After a successful build, you'll find:
- **Artifacts** in the Actions run (downloadable for 30 days)
- **Releases** (for release builds only) with downloadable assets

## Platform-Specific Notes

### Windows
- Builds with Windows icon resource
- Creates `.zip` archives
- Includes all assets (icons, docs, etc.)

### Linux
- Installs GTK3 and WebKit dependencies
- Creates `.tar.gz` archives
- Universal Linux compatibility

### macOS
- Builds for both Intel and Apple Silicon
- Creates `.tar.gz` archives
- Native macOS integration

### FreeBSD
- Support planned for future release
- Will be cross-compiled from Ubuntu runners

## Manual Triggering

The workflow uses `workflow_dispatch` which allows manual triggering with custom parameters. This is perfect for:
- Testing builds before releases
- Building specific platforms
- Debug builds for troubleshooting

## Dependencies

The workflows automatically handle:
- Rust toolchain installation
- Cross-compilation targets
- Platform-specific dependencies
- Cargo caching for faster builds
- Asset packaging and archiving
