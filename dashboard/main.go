package main

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/0xQuinto/dossier/dashboard/internal/data"
	"github.com/0xQuinto/dossier/dashboard/internal/ui"
	tea "github.com/charmbracelet/bubbletea"
)

func main() {
	// Default paths relative to project root
	trackerPath := "research/applications.md"
	reportsDir := "research/latest"

	if len(os.Args) > 1 {
		trackerPath = os.Args[1]
	}
	if len(os.Args) > 2 {
		reportsDir = os.Args[2]
	}

	absTracker, err := filepath.Abs(trackerPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error resolving path: %v\n", err)
		os.Exit(1)
	}

	apps, err := data.ParseApplications(absTracker)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error reading tracker: %v\n", err)
		os.Exit(1)
	}

	absReports, _ := filepath.Abs(reportsDir)
	model := ui.NewModel(apps, absTracker, absReports)

	p := tea.NewProgram(model, tea.WithAltScreen())
	if _, err := p.Run(); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}
