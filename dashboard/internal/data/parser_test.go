package data

import (
	"os"
	"path/filepath"
	"testing"
)

func TestParseApplications(t *testing.T) {
	content := `# Application Tracker

| # | Date | Company | Role | Score | Status | Archetype | URL | Notes |
|---|------|---------|------|-------|--------|-----------|-----|-------|
| 1 | 2026-04-08 | Anthropic | Research Engineer, Agents | 8.9 | evaluated | Agentic | https://example.com | A-tier |
| 2 | 2026-04-08 | Anthropic | Applied AI Engineer | 8.5 | applied | FDE | https://example.com/2 | |
`
	dir := t.TempDir()
	path := filepath.Join(dir, "applications.md")
	os.WriteFile(path, []byte(content), 0644)

	apps, err := ParseApplications(path)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(apps) != 2 {
		t.Fatalf("expected 2 apps, got %d", len(apps))
	}
	if apps[0].Company != "Anthropic" {
		t.Errorf("expected Anthropic, got %s", apps[0].Company)
	}
	if apps[0].Score != 8.9 {
		t.Errorf("expected 8.9, got %f", apps[0].Score)
	}
	if apps[1].Status != "applied" {
		t.Errorf("expected applied, got %s", apps[1].Status)
	}
}

func TestStatusPriority(t *testing.T) {
	if StatusPriority("skip") >= StatusPriority("evaluated") {
		t.Error("skip should be lower priority than evaluated")
	}
	if StatusPriority("interview") <= StatusPriority("applied") {
		t.Error("interview should be higher priority than applied")
	}
	if StatusPriority("offer") <= StatusPriority("interview") {
		t.Error("offer should be higher priority than interview")
	}
}

func TestParseApplicationsFileNotFound(t *testing.T) {
	_, err := ParseApplications("/nonexistent/path.md")
	if err == nil {
		t.Error("expected error for missing file")
	}
}
