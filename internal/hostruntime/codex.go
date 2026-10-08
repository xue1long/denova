package hostruntime

import (
	"log/slog"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"time"
)

// CodexHome resolves the user's existing configuration and credential store.
// It is host-local, never copied into Project data or a portable settings file.
func CodexHome(environment []string) (string, error) {
	home := strings.TrimSpace(environmentValue(environment, "CODEX_HOME"))
	if home == "" {
		userHome, err := os.UserHomeDir()
		if err != nil {
			return "", err
		}
		home = filepath.Join(userHome, ".codex")
	} else if expanded, ok := expandHomePath(home); ok {
		home = expanded
	}
	return filepath.Abs(home)
}

// DiscoverCodex resolves a native executable without launching a shell wrapper.
// npm's Windows shim cannot be passed directly to exec.Command; resolve its
// installed optional binary package instead. No discovery starts a process.
//
// Search order on Windows:
//  1. PATH (codex.exe, codex.cmd, npm @openai/codex vendor layout)
//  2. OpenAI's official Windows installer location under
//     %LOCALAPPDATA%\OpenAI\Codex\bin\*\codex.exe. Newer installers ship the
//     binary outside npm, so the npm shim may point at a removed hash.
func DiscoverCodex(environment []string) string {
	if runtime.GOOS != "windows" {
		return discoverExecutable(environment, "codex")
	}
	if native := discoverExecutable(environment, "codex.exe"); native != "" {
		return native
	}
	shim := discoverExecutable(environment, "codex.cmd")
	if shim != "" {
		if resolved := resolveWindowsNPMPackageBinary(shim); resolved != "" {
			return resolved
		}
	}
	if installed := discoverOfficialWindowsInstall(environment); installed != "" {
		return installed
	}
	return ""
}

// resolveWindowsNPMPackageBinary unwraps an npm shim into its bundled native
// executable so exec.Command can launch it directly.
func resolveWindowsNPMPackageBinary(shim string) string {
	platform, target := "win32-x64", "x86_64-pc-windows-msvc"
	if runtime.GOARCH == "arm64" {
		platform, target = "win32-arm64", "aarch64-pc-windows-msvc"
	}
	packageRoot := filepath.Join(filepath.Dir(shim), "node_modules", "@openai", "codex")
	for _, vendor := range []string{
		filepath.Join(packageRoot, "node_modules", "@openai", "codex-"+platform, "vendor", target),
		filepath.Join(packageRoot, "vendor", target),
	} {
		// Current npm releases use bin; earlier releases used codex.
		for _, directory := range []string{"bin", "codex"} {
			candidate := filepath.Join(vendor, directory, "codex.exe")
			if executableFile(candidate) {
				return candidate
			}
		}
	}
	return ""
}

// discoverOfficialWindowsInstall scans the OpenAI installer's hash-suffixed
// directories under %LOCALAPPDATA%\OpenAI\Codex\bin for the newest codex.exe.
// Hash directories are content-addressed; sorted descending picks the latest
// install that did not get garbage-collected yet.
func discoverOfficialWindowsInstall(environment []string) string {
	root := filepath.Join(environmentValue(environment, "LOCALAPPDATA"), "OpenAI", "Codex", "bin")
	if _, err := os.Stat(root); err != nil {
		if home := strings.TrimSpace(environmentValue(environment, "USERPROFILE")); home != "" {
			root = filepath.Join(home, "AppData", "Local", "OpenAI", "Codex", "bin")
			if _, err := os.Stat(root); err != nil {
				return ""
			}
		} else {
			return ""
		}
	}
	entries, err := os.ReadDir(root)
	if err != nil {
		slog.Info("codex discover: readdir failed", "root", root, "error", err.Error())
		return ""
	}
	// Pick the most recently modified hash directory that actually contains
	// a codex.exe. Sorting by directory mtime alone is not enough: installers
	// update sibling binaries after codex.exe lands, which can make a
	// codex-less hash directory appear newer.
	var best string
	var bestMtime time.Time
	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}
		candidate := filepath.Join(root, entry.Name(), "codex.exe")
		info, err := os.Stat(candidate)
		if err != nil || info.IsDir() {
			continue
		}
		if info.ModTime().After(bestMtime) {
			best = entry.Name()
			bestMtime = info.ModTime()
		}
	}
	if best == "" {
		return ""
	}
	candidate := filepath.Join(root, best, "codex.exe")
	if executableFile(candidate) {
		return candidate
	}
	return ""
}
