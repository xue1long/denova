package hostruntime

import (
	"os"
	"path/filepath"
	"runtime"
	"testing"
	"time"
)

func TestCodexHomeUsesExistingUserConfiguration(t *testing.T) {
	userHome, err := os.UserHomeDir()
	if err != nil {
		t.Fatal(err)
	}
	custom := filepath.Join(t.TempDir(), "shared codex")
	for _, test := range []struct {
		name string
		env  []string
		want string
	}{
		{"default", nil, filepath.Join(userHome, ".codex")},
		{"explicit", []string{"CODEX_HOME=" + custom}, custom},
		{"home expansion", []string{"CODEX_HOME=~/.codex-team"}, filepath.Join(userHome, ".codex-team")},
		{"empty", []string{"CODEX_HOME= "}, filepath.Join(userHome, ".codex")},
	} {
		t.Run(test.name, func(t *testing.T) {
			got, err := CodexHome(test.env)
			if err != nil || got != test.want {
				t.Fatalf("CodexHome = %q, %v; want %q", got, err, test.want)
			}
		})
	}
}

func TestDiscoverCodexUsesNativeExecutableWithoutLaunchingIt(t *testing.T) {
	directory := filepath.Join(t.TempDir(), "工具 with spaces")
	if err := os.MkdirAll(directory, 0o700); err != nil {
		t.Fatal(err)
	}
	name := "codex"
	if runtime.GOOS == "windows" {
		name = "codex.exe"
	}
	executable := filepath.Join(directory, name)
	// Deliberately not a program: discovery must only inspect the file.
	if err := os.WriteFile(executable, []byte("not executable code"), 0o700); err != nil {
		t.Fatal(err)
	}
	environment := []string{"PATH=" + directory}
	if got := DiscoverCodex(environment); got != executable {
		t.Fatalf("DiscoverCodex = %q, want %q", got, executable)
	}
	if got := DiscoverCodex([]string{"PATH=" + filepath.Join(directory, "missing")}); got != "" {
		t.Fatalf("missing executable resolved to %q", got)
	}
}

func TestDiscoverCodexResolvesWindowsNPMShimToNativeBinary(t *testing.T) {
	if runtime.GOOS != "windows" {
		t.Skip("Windows npm layout")
	}
	for _, binaryDirectory := range []string{"bin", "codex"} {
		t.Run(binaryDirectory, func(t *testing.T) {
			directory := filepath.Join(t.TempDir(), "npm 用户")
			if err := os.MkdirAll(directory, 0o700); err != nil {
				t.Fatal(err)
			}
			if err := os.WriteFile(filepath.Join(directory, "codex.cmd"), []byte("invalid shell wrapper"), 0o600); err != nil {
				t.Fatal(err)
			}
			environment := []string{"PATH=" + directory}
			if got := DiscoverCodex(environment); got != "" {
				t.Fatalf("shell wrapper without native binary resolved to %q", got)
			}
			platform, target := "win32-x64", "x86_64-pc-windows-msvc"
			if runtime.GOARCH == "arm64" {
				platform, target = "win32-arm64", "aarch64-pc-windows-msvc"
			}
			executable := filepath.Join(directory, "node_modules", "@openai", "codex", "node_modules", "@openai", "codex-"+platform, "vendor", target, binaryDirectory, "codex.exe")
			if err := os.MkdirAll(filepath.Dir(executable), 0o700); err != nil {
				t.Fatal(err)
			}
			if err := os.WriteFile(executable, []byte("not executable code"), 0o600); err != nil {
				t.Fatal(err)
			}
			if got := DiscoverCodex(environment); got != executable {
				t.Fatalf("DiscoverCodex = %q, want native npm binary %q", got, executable)
			}
		})
	}
}

func TestDiscoverInstalledCodex(t *testing.T) {
	executable := os.Getenv("DENOVA_TEST_CODEX_EXE")
	if executable == "" {
		t.Skip("DENOVA_TEST_CODEX_EXE is not set")
	}
	got := DiscoverCodex([]string{"PATH=" + filepath.Dir(executable)})
	gotInfo, gotErr := os.Stat(got)
	wantInfo, wantErr := os.Stat(executable)
	if gotErr != nil || wantErr != nil || !os.SameFile(gotInfo, wantInfo) {
		t.Fatalf("DiscoverCodex = %q, want installed program %q", got, executable)
	}
}

func TestDiscoverCodexFindsOfficialWindowsInstall(t *testing.T) {
	if runtime.GOOS != "windows" {
		t.Skip("Windows-only OpenAI installer layout")
	}
	localAppData := t.TempDir()
	root := filepath.Join(localAppData, "OpenAI", "Codex", "bin")
	if err := os.MkdirAll(root, 0o700); err != nil {
		t.Fatal(err)
	}
	// Oldest hash directory holds the real codex.exe with the oldest mtime.
	// A neighbouring empty hash directory uses a later mtime than the
	// codex.exe it would shadow if we sorted by directory alone.
	base := time.Date(2026, 1, 1, 0, 0, 0, 0, time.UTC)
	real := filepath.Join(root, "9691020b546a15b2", "codex.exe")
	if err := os.MkdirAll(filepath.Dir(real), 0o700); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(real, []byte("not executable code"), 0o600); err != nil {
		t.Fatal(err)
	}
	if err := os.Chtimes(real, base, base); err != nil {
		t.Fatal(err)
	}
	empty := filepath.Join(root, "441edec208d1681c")
	if err := os.MkdirAll(empty, 0o700); err != nil {
		t.Fatal(err)
	}
	if err := os.Chtimes(empty, base.Add(15*time.Second), base.Add(15*time.Second)); err != nil {
		t.Fatal(err)
	}
	environment := []string{
		"PATH=" + filepath.Join(t.TempDir(), "empty"),
		"LOCALAPPDATA=" + localAppData,
	}
	got := DiscoverCodex(environment)
	want := real
	if got != want {
		t.Fatalf("DiscoverCodex = %q, want real installer binary %q", got, want)
	}
}

func TestDiscoverCodexPrefersPATHOverOfficialInstall(t *testing.T) {
	if runtime.GOOS != "windows" {
		t.Skip("Windows-only ordering")
	}
	pathDir := filepath.Join(t.TempDir(), "path")
	if err := os.MkdirAll(pathDir, 0o700); err != nil {
		t.Fatal(err)
	}
	pathExecutable := filepath.Join(pathDir, "codex.exe")
	if err := os.WriteFile(pathExecutable, []byte("not executable code"), 0o600); err != nil {
		t.Fatal(err)
	}
	localAppData := t.TempDir()
	root := filepath.Join(localAppData, "OpenAI", "Codex", "bin")
	if err := os.MkdirAll(filepath.Join(root, "9691020b546a15b2"), 0o700); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(root, "9691020b546a15b2", "codex.exe"), []byte("not executable code"), 0o600); err != nil {
		t.Fatal(err)
	}
	environment := []string{
		"PATH=" + pathDir,
		"LOCALAPPDATA=" + localAppData,
	}
	got := DiscoverCodex(environment)
	if got != pathExecutable {
		t.Fatalf("DiscoverCodex = %q, want PATH binary %q", got, pathExecutable)
	}
}

func TestDiscoverCodexReturnsEmptyWhenOfficialInstallMissing(t *testing.T) {
	if runtime.GOOS != "windows" {
		t.Skip("Windows-only OpenAI installer layout")
	}
	environment := []string{
		"PATH=" + filepath.Join(t.TempDir(), "missing"),
		"LOCALAPPDATA=" + t.TempDir(),
		"USERPROFILE=" + t.TempDir(),
	}
	if got := DiscoverCodex(environment); got != "" {
		t.Fatalf("DiscoverCodex = %q, want empty when no installer present", got)
	}
}
