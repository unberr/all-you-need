#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OFFICIAL_MARKETPLACE="claude-plugins-official|anthropics/claude-plugins-official"

DRY_RUN=0; ASSUME_YES=0; WITH_TOOLS=0; WITH_SKILLS=0; WITH_COMPANIONS=0; REPO=""; PROJECT_DIR="$PWD"

have() { command -v "$1" >/dev/null 2>&1; }
say() { printf '%s\n' "$*"; }
warn() { printf 'warning: %s\n' "$*" >&2; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

detect_os() {
  case "${ALL_YOU_NEED_UNAME:-$(uname -s)}" in
    Darwin) echo macos ;;
    Linux) echo linux ;;
    MINGW* | MSYS* | CYGWIN*) echo windows ;;
    *) return 1 ;;
  esac
}

detect_distro() {
  local id="" like=""
  if [[ -r /etc/os-release ]]; then
    id="$(grep -E '^ID=' /etc/os-release | cut -d= -f2 | tr -d '"' | tr '[:upper:]' '[:lower:]')"
    like="$(grep -E '^ID_LIKE=' /etc/os-release | cut -d= -f2 | tr -d '"' | tr '[:upper:]' '[:lower:]')"
  fi
  case " $id $like " in
    *"debian"* | *"ubuntu"* | *"mint"* | *"pop"*) echo debian ;;
    *"arch"* | *"manjaro"* | *"endeavour"*) echo arch ;;
    *"fedora"* | *"rhel"* | *"centos"* | *"rocky"* | *"alma"*) echo fedora ;;
    *"suse"* | *"opensuse"*) echo suse ;;
    *"alpine"*) echo alpine ;;
    *) [[ -n "$id" ]] && echo "$id" || echo "" ;;
  esac
}

detect_pm() {
  local os="$1" pm
  case "$os" in
    macos) have brew && echo brew ;;
    windows) have winget && echo winget ;;
    linux) for pm in apt-get dnf pacman zypper apk; do have "$pm" && { echo "$pm"; return; }; done ;;
  esac
  return 0
}

install_cmd() {
  local os="$1" pm="$2" tool="$3"
  [[ "$os:$tool" == "windows:semgrep" ]] && return 1  # semgrep has no native Windows build: use WSL
  case "$pm:$tool" in
    brew:python) echo "brew install python" ;;
    brew:git) echo "brew install git" ;;
    brew:rust-analyzer) echo "brew install rust-analyzer" ;;
    brew:clangd) echo "brew install llvm" ;;
    brew:semgrep) echo "brew install semgrep" ;;
    apt-get:python) echo "sudo apt-get install -y python3" ;;
    apt-get:git) echo "sudo apt-get install -y git" ;;
    apt-get:clangd) echo "sudo apt-get install -y clangd" ;;
    dnf:python) echo "sudo dnf install -y python3" ;;
    dnf:git) echo "sudo dnf install -y git" ;;
    dnf:clangd) echo "sudo dnf install -y clang-tools-extra" ;;
    pacman:python) echo "sudo pacman -S --needed --noconfirm python" ;;
    pacman:git) echo "sudo pacman -S --needed --noconfirm git" ;;
    pacman:clangd) echo "sudo pacman -S --needed --noconfirm clang" ;;
    zypper:python) echo "sudo zypper install -y python3" ;;
    zypper:git) echo "sudo zypper install -y git" ;;
    apk:python) echo "sudo apk add python3" ;;
    apk:git) echo "sudo apk add git" ;;
    apk:clangd) echo "sudo apk add clang-extra-tools" ;;
    winget:python) echo "winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements" ;;
    winget:git) echo "winget install --id Git.Git -e --accept-package-agreements --accept-source-agreements" ;;
    winget:clangd) echo "winget install --id LLVM.LLVM -e --accept-package-agreements --accept-source-agreements" ;;
    *:rust-analyzer) echo "rustup component add rust-analyzer" ;;
    *:pyright) echo "npm install -g pyright" ;;
    *:typescript-language-server) echo "npm install -g typescript-language-server typescript" ;;
    *:gopls) echo "go install golang.org/x/tools/gopls@latest" ;;
    *:csharp-ls) echo "dotnet tool install --global csharp-ls" ;;
    *:intelephense) echo "npm install -g intelephense" ;;
    *:semgrep) echo "pipx install semgrep" ;;
    *) return 1 ;;
  esac
}

python_ok() {
  local py
  for py in python3 python; do
    if have "$py" && "$py" -c 'import sys; sys.exit(sys.version_info < (3, 9))' 2>/dev/null; then return 0; fi
  done
  return 1
}

tool_binary() { case "$1" in pyright) echo pyright-langserver ;; *) echo "$1" ;; esac; }
tool_runtime() {
  case "$1" in
    pyright | typescript-language-server | intelephense) echo npm ;;
    gopls) echo go ;;
    csharp-ls) echo dotnet ;;
  esac
  return 0
}

tool_present() {
  case "$1" in
    python) python_ok ;;
    *) have "$(tool_binary "$1")" ;;
  esac
}

confirm() {
  [[ "$ASSUME_YES" == 1 || "$DRY_RUN" == 1 ]] && return 0
  [[ -t 0 ]] || die "not a terminal: re-run with --yes to allow installing packages"
  local answer
  read -r -p "$1 [y/N] " answer
  [[ "$answer" == [yY]* ]]
}

run_str() {
  if [[ "$DRY_RUN" == 1 ]]; then say "  would run: $1"; else say "  running: $1"; bash -c "$1"; fi
}

marketplace_has() {
  printf '%s\n' "$2" | grep -qxF -- "$1"
}

run_project_plugin() {
  local plugin="$1"
  if [[ "$DRY_RUN" == 1 ]]; then
    say "  would run in $PROJECT_DIR: claude plugin install $plugin --scope local"
  else
    (cd "$PROJECT_DIR" && claude plugin install "$plugin" --scope local)
  fi
}

ensure_tool() {  # ensure_tool OS PM TOOL REQUIRED(1|0)
  local os="$1" pm="$2" tool="$3" required="$4" cmd
  if tool_present "$tool"; then say "have $tool"; return 0; fi
  local runtime; runtime="$(tool_runtime "$tool")"
  if [[ -n "$runtime" ]] && ! have "$runtime"; then
    warn "$tool needs $runtime, which is not installed: install $runtime first, then re-run this script"; return 0
  fi
  if [[ -z "$pm" ]]; then
    [[ "$required" == 1 ]] && die "$tool is missing and no supported package manager was found: install it manually"
    warn "$tool is missing and no package manager was found: install it manually"; return 0
  fi
  if ! cmd="$(install_cmd "$os" "$pm" "$tool")"; then
    [[ "$required" == 1 ]] && die "no known install command for $tool with $pm: install it manually"
    warn "no known install command for $tool on $os: install it manually"; return 0
  fi
  if ! confirm "Install $tool with: $cmd ?"; then
    [[ "$required" == 1 ]] && die "$tool is required"
    warn "skipped $tool"; return 0
  fi
  if [[ "$required" == 1 ]]; then run_str "$cmd"
  else run_str "$cmd" || warn "$tool install failed: install it manually"; fi
}

usage() { echo "Usage: ./install.sh [--yes] [--dry-run] [--with-tools] [--with-skills] [--with-companions] [--project-dir PATH] [--repo <github-user>/all-you-need]"; }

main() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --yes | -y) ASSUME_YES=1 ;;
      --dry-run) DRY_RUN=1 ;;
      --with-tools) WITH_TOOLS=1 ;;
      --with-skills) WITH_SKILLS=1 ;;
      --with-companions) WITH_COMPANIONS=1 ;;
      --no-tools) WITH_TOOLS=0 ;;
      --no-skills) WITH_SKILLS=0 ;;
      --no-companions) WITH_COMPANIONS=0 ;;
      --project-dir) PROJECT_DIR="${2:?--project-dir needs a path}"; shift ;;
      --repo) REPO="${2:?--repo needs a value}"; shift ;;
      -h | --help) usage; exit 0 ;;
      *) die "unknown option: $1 (see --help)" ;;
    esac
    shift
  done

  [[ -d "$PROJECT_DIR" ]] || die "project directory does not exist: $PROJECT_DIR"
  PROJECT_DIR="$(cd "$PROJECT_DIR" && pwd)"

  local os pm distro source entry name src tool selection kind value python_cmd
  local selected_tools=() selected_plugins=()
  os="$(detect_os)" || die "unsupported OS: $(uname -s). Supported: macOS (Darwin), Linux, Windows via Git Bash/MSYS/Cygwin (or WSL as linux)."
  pm="$(detect_pm "$os")"
  distro=""
  [[ "$os" == linux ]] && distro="$(detect_distro)"
  if [[ -n "$distro" ]]; then say "OS: $os ($distro), package manager: ${pm:-none found}"
  else say "OS: $os, package manager: ${pm:-none found}"; fi
  if [[ "$os" == linux && -z "$pm" ]]; then
    warn "No supported Linux package manager found (looked for apt-get=debian, dnf=fedora, pacman=arch, zypper=suse, apk=alpine). Install git and Python 3.9+ manually."
  fi
  [[ "$os" == macos ]] && ! have brew && warn "Homebrew not found: install it from https://brew.sh for automatic tool installs, or install git and Python manually."
  [[ "$os" == windows ]] && say "Windows: running under Git Bash or MSYS. For WSL, run this script inside WSL (it reports linux)."

  ensure_tool "$os" "$pm" git 1
  ensure_tool "$os" "$pm" python 1
  selection=""
  if [[ "$WITH_TOOLS" == 1 || "$WITH_COMPANIONS" == 1 ]]; then
    python_cmd=""
    if have python3; then python_cmd=python3; elif have python; then python_cmd=python; fi
    if [[ -n "$python_cmd" ]]; then
      selection="$("$python_cmd" -I "$ROOT/scripts/project_stack.py" --root "$PROJECT_DIR" --field setup)"
      while IFS=$'\t' read -r kind value; do
        [[ -z "$value" ]] && continue
        case "$kind" in
          tools) selected_tools+=("$value") ;;
          companions) selected_plugins+=("$value") ;;
        esac
      done <<< "$selection"
    else
      say "Project matching deferred: Python is unavailable in this dry run; rerun after installing Python."
    fi
  fi
  if [[ "$WITH_TOOLS" == 1 ]]; then
    if [[ ${#selected_tools[@]} -gt 0 ]]; then
      for tool in "${selected_tools[@]}"; do ensure_tool "$os" "$pm" "$tool" 0; done
    else
      say "No language tools match the project files in $PROJECT_DIR"
    fi
  fi

  if ! have claude; then
    [[ "$DRY_RUN" == 1 ]] && warn "claude CLI not found (continuing because of --dry-run)" \
      || die "claude CLI not found. Install Claude Code from https://claude.com/claude-code, then re-run this script."
  elif [[ "$DRY_RUN" == 0 ]]; then
    claude --version >/dev/null 2>&1 || warn "claude CLI present but 'claude --version' failed; continuing"
  fi

  source="${REPO:-$ROOT}"
  if [[ -n "$REPO" && ! "$REPO" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]]; then
    die "invalid --repo $REPO: use <github-user>/<repo>"
  fi
  [[ -z "$REPO" && "$os" == windows ]] && have cygpath && source="$(cygpath -w "$ROOT")"

  local existing="" selected_marketplaces=("all-you-need|$source")
  [[ "$DRY_RUN" == 1 ]] || existing="$(claude plugin marketplace list)"
  if [[ "$WITH_COMPANIONS" == 1 && ${#selected_plugins[@]} -gt 0 ]]; then
    selected_marketplaces+=("$OFFICIAL_MARKETPLACE")
  fi
  for entry in "${selected_marketplaces[@]}"; do
    name="${entry%%|*}"; src="${entry#*|}"
    if [[ "$DRY_RUN" == 0 ]] && marketplace_has "$name" "$existing"; then say "have marketplace $name"; continue; fi
    if [[ "$DRY_RUN" == 1 ]]; then
      run_str "claude plugin marketplace add \"$src\""
    else
      say "  running: claude plugin marketplace add <source>"
      claude plugin marketplace add "$src"
    fi
  done
  if [[ "$DRY_RUN" == 1 ]]; then
    run_str "claude plugin install all-you-need@all-you-need"
  else
    if claude plugin list 2>/dev/null | grep -q "all-you-need"; then say "have plugin all-you-need";
    else say "  running: claude plugin install all-you-need"; claude plugin install all-you-need@all-you-need; fi
    claude plugin list 2>/dev/null | grep -q "all-you-need" || warn "plugin install did not verify: run 'claude plugin list'"
  fi
  if [[ "$WITH_COMPANIONS" == 1 ]]; then
    if [[ ${#selected_plugins[@]} -eq 0 ]]; then
      say "No companion plugins match the project files in $PROJECT_DIR"
    else
      for entry in "${selected_plugins[@]}"; do
        run_project_plugin "$entry" || warn "could not install $entry: all-you-need works without it"
      done
    fi
  fi

  if [[ "$WITH_SKILLS" == 1 ]]; then
    if [[ "$DRY_RUN" == 1 ]]; then say "  would run: bash scripts/install-skills.sh"; else bash "$ROOT/scripts/install-skills.sh"; fi
  fi
  say "Done. Start a new Claude Code session to load the plugin."
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then main "$@"; fi
