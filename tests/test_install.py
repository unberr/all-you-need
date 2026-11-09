import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INSTALL = ROOT / "install.sh"
BASE_UTILS = ["bash", "uname", "dirname", "grep", "sed", "python3"]


def sh(snippet: str, **env) -> subprocess.CompletedProcess:
    return subprocess.run(["bash", "-c", f'source "{INSTALL}"; {snippet}'], capture_output=True, text=True,
                          env={**os.environ, **env})


class Functions(unittest.TestCase):
    def test_detect_os(self):
        cases = {"Darwin": "macos", "Linux": "linux", "MINGW64_NT-10.0": "windows", "MSYS_NT-10.0": "windows",
                 "CYGWIN_NT-10.0": "windows"}
        for uname, expected in cases.items():
            self.assertEqual(sh("detect_os", ALL_YOU_NEED_UNAME=uname).stdout.strip(), expected, uname)

    def test_detect_os_unsupported(self):
        self.assertNotEqual(sh("detect_os", ALL_YOU_NEED_UNAME="FreeBSD").returncode, 0)

    def test_install_cmd_table(self):
        cases = [
            ("macos", "brew", "python", "brew install python"),
            ("macos", "brew", "clangd", "brew install llvm"),
            ("linux", "apt-get", "git", "sudo apt-get install -y git"),
            ("linux", "dnf", "clangd", "sudo dnf install -y clang-tools-extra"),
            ("linux", "pacman", "python", "sudo pacman -S --needed --noconfirm python"),
            ("linux", "apk", "clangd", "sudo apk add clang-extra-tools"),
            ("windows", "winget", "git", "winget install --id Git.Git -e --accept-package-agreements --accept-source-agreements"),
            ("linux", "apt-get", "rust-analyzer", "rustup component add rust-analyzer"),
            ("linux", "apt-get", "semgrep", "pipx install semgrep"),
            ("macos", "brew", "pyright", "npm install -g pyright"),
            ("linux", "dnf", "typescript-language-server", "npm install -g typescript-language-server typescript"),
            ("windows", "winget", "gopls", "go install golang.org/x/tools/gopls@latest"),
            ("macos", "brew", "csharp-ls", "dotnet tool install --global csharp-ls"),
            ("linux", "pacman", "intelephense", "npm install -g intelephense"),
        ]
        for os_name, pm, tool, expected in cases:
            self.assertEqual(sh(f"install_cmd {os_name} {pm} {tool}").stdout.strip(), expected, (os_name, pm, tool))

    def test_install_cmd_unsupported(self):
        self.assertNotEqual(sh("install_cmd windows winget semgrep").returncode, 0)
        self.assertNotEqual(sh("install_cmd linux zypper clangd").returncode, 0)


class DryRun(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.bin = Path(self._tmp.name)
        for name in BASE_UTILS:
            found = shutil.which(name)
            self.assertIsNotNone(found, name)
            os.symlink(str(found), self.bin / name)

    def tearDown(self):
        self._tmp.cleanup()

    def stub(self, *names):
        for name in names:
            path = self.bin / name
            path.write_text("#!/bin/sh\nexit 0\n")
            path.chmod(0o755)

    def project(self, *files):
        root = self.bin / "project"
        for relative, content in files:
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        return root

    def run_install(self, uname, *args, project_dir=None):
        project_arg = ["--project-dir", str(project_dir)] if project_dir else []
        return subprocess.run([str(self.bin / "bash"), str(INSTALL), "--dry-run", *args, *project_arg], capture_output=True,
                              text=True, env={"PATH": str(self.bin), "ALL_YOU_NEED_UNAME": uname, "HOME": self._tmp.name},
                              cwd=self._tmp.name)

    def test_linux_apt_installs_missing_python_and_tools(self):
        self.stub("apt-get", "git", "claude")
        project = self.project(("app.py", ""), ("app.tsx", ""), ("go.mod", ""), ("main.go", ""),
                               ("Cargo.toml", ""), ("main.rs", ""), ("main.cpp", ""), ("app.csproj", ""),
                               ("main.cs", ""), ("composer.json", "{}"), ("index.php", ""))
        result = self.run_install("Linux", "--yes", "--with-tools", "--with-companions", "--with-skills",
                                  project_dir=project)
        out = result.stdout
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("OS: linux, package manager: apt-get", out)
        self.assertIn("have python", out)
        self.assertNotIn("apt-get install -y git", out)                  
        self.assertIn("would run: sudo apt-get install -y clangd", out)
        self.assertIn("would run: rustup component add rust-analyzer", out)
        self.assertIn('would run: claude plugin marketplace add "anthropics/claude-plugins-official"', out)
        self.assertIn("would run: claude plugin install all-you-need@all-you-need", out)
        self.assertIn("claude plugin install php-lsp@claude-plugins-official --scope local", out)
        self.assertIn("claude plugin install security-guidance@claude-plugins-official --scope local", out)
        self.assertIn("would run: bash scripts/install-skills.sh", out)

    def test_macos_brew(self):
        self.stub("brew", "git", "claude")
        project = self.project(("pyproject.toml", ""), ("main.py", ""), ("src/main.rs", ""))
        out = self.run_install("Darwin", "--with-tools", project_dir=project).stdout
        self.assertIn("OS: macos, package manager: brew", out)
        self.assertIn("have python", out)
        self.assertIn("would run: brew install rust-analyzer", out)
        self.assertNotIn("semgrep", out)

    def test_windows_winget_and_no_semgrep(self):
        self.stub("winget", "claude")
        project = self.project(("main.cpp", ""))
        result = self.run_install("MINGW64_NT-10.0", "--with-tools", project_dir=project)
        self.assertIn("OS: windows, package manager: winget", result.stdout)
        self.assertIn("would run: winget install --id LLVM.LLVM -e", result.stdout)

    def test_language_servers_need_their_runtime(self):
        self.stub("apt-get", "git", "claude")
        project = self.project(("main.py", ""), ("go.mod", ""), ("main.go", ""), ("app.csproj", ""))
        result = self.run_install("Linux", "--yes", "--with-tools", project_dir=project)
        self.assertIn("pyright needs npm", result.stderr)
        self.assertIn("gopls needs go", result.stderr)
        self.assertIn("csharp-ls needs dotnet", result.stderr)
        self.assertNotIn("would run: npm install", result.stdout)

    def test_language_servers_install_when_runtime_present(self):
        self.stub("apt-get", "git", "claude", "npm", "go", "dotnet")
        project = self.project(("main.py", ""), ("index.php", ""), ("go.mod", ""), ("app.csproj", ""))
        out = self.run_install("Linux", "--yes", "--with-tools", project_dir=project).stdout
        self.assertIn("would run: npm install -g pyright", out)
        self.assertIn("would run: npm install -g intelephense", out)
        self.assertIn("would run: go install golang.org/x/tools/gopls@latest", out)
        self.assertIn("would run: dotnet tool install --global csharp-ls", out)

    def test_pyright_detected_by_langserver_binary(self):
        self.stub("apt-get", "git", "claude", "npm", "pyright-langserver")
        project = self.project(("main.py", ""))
        out = self.run_install("Linux", "--yes", "--with-tools", project_dir=project).stdout
        self.assertIn("have pyright", out)
        self.assertNotIn("npm install -g pyright", out)

    def test_default_install_is_lean_and_plugin_has_no_hard_dependencies(self):
        self.stub("apt-get", "git", "claude")
        out = self.run_install("Linux").stdout
        self.assertIn("claude plugin install all-you-need@all-you-need", out)
        self.assertNotIn('marketplace add "wshobson/agents"', out)
        self.assertNotIn("clangd", out)
        self.assertNotIn("install-skills", out)
        self.assertNotIn("php-lsp", out)
        manifest = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
        self.assertNotIn("dependencies", manifest, "a hard dependency stops the whole plugin from loading when one is missing")

    def test_flags_skip_tools_and_skills(self):
        self.stub("apt-get", "git", "claude")
        out = self.run_install("Linux").stdout
        self.assertNotIn("clangd", out)
        self.assertNotIn("install-skills", out)

    def test_missing_package_manager_for_required_tool_fails(self):
        self.stub("claude")
        result = self.run_install("Linux", "--yes")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no supported package manager", result.stderr)

    def test_unknown_option(self):
        result = self.run_install("Linux", "--bogus")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown option", result.stderr)

    def test_repo_override(self):
        self.stub("apt-get", "git", "claude")
        out = self.run_install("Linux", "--no-tools", "--repo", "someone/all-you-need").stdout
        self.assertIn('marketplace add "someone/all-you-need"', out)

    def test_companions_are_project_matched_and_local(self):
        self.stub("apt-get", "git", "claude")
        project = self.project(("package.json", "{}"), ("src/app.tsx", ""))
        out = self.run_install("Linux", "--with-companions", project_dir=project).stdout
        self.assertIn('marketplace add "anthropics/claude-plugins-official"', out)
        self.assertIn("claude plugin install typescript-lsp@claude-plugins-official --scope local", out)
        self.assertIn("claude plugin install security-guidance@claude-plugins-official --scope local", out)
        self.assertNotIn("sharp-edges", out)

    def test_no_companion_plugins_for_docs_only_project(self):
        self.stub("apt-get", "git", "claude")
        project = self.project(("README.md", "Docs"))
        out = self.run_install("Linux", "--with-companions", project_dir=project).stdout
        self.assertIn("No companion plugins match", out)
        self.assertNotIn("claude-plugins-official", out)

    def test_with_skills_installs_external_skills_only_when_requested(self):
        self.stub("apt-get", "git", "claude")
        out = self.run_install("Linux", "--with-skills").stdout
        self.assertIn("would run: bash scripts/install-skills.sh", out)
        self.assertNotIn("claude plugin install sharp-edges", out)


class HooksCommands(unittest.TestCase):

    def setUp(self):
                                                                                                                  
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.plugin_root = Path(tmp.name)
        shutil.copytree(ROOT / "hooks", self.plugin_root / "hooks")

    def run_hook(self, event_name, stdin):
        spec = json.loads((ROOT / "hooks" / "hooks.json").read_text())["hooks"][event_name]
        outputs = []
        for group in spec:
            for hook in group["hooks"]:
                result = subprocess.run(["sh", "-c", hook["command"]], input=stdin, capture_output=True, text=True,
                                        env={**os.environ, "CLAUDE_PLUGIN_ROOT": str(self.plugin_root)})
                self.assertEqual(result.returncode, 0, result.stderr)
                outputs.append(result.stdout)
        return outputs

    def test_session_start_injects_rules(self):
        (out,) = self.run_hook("SessionStart", "")
        self.assertIn("all-you-need harness is active", out)

    def test_post_tool_use_lint_runs(self):
        event = json.dumps({"tool_name": "Edit", "tool_input": {"file_path": "a.ts", "new_string": "let x: any = 1"}})
        (combined,) = self.run_hook("PostToolUse", event)
        self.assertIn("uses `any`", combined)

    def test_stop_with_missing_transcript_is_silent(self):
        (out,) = self.run_hook("Stop", json.dumps({"transcript_path": "/nonexistent"}))
        self.assertEqual(out, "")


if __name__ == "__main__":
    unittest.main()
