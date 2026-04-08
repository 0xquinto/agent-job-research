package ui

import "github.com/charmbracelet/lipgloss"

// Catppuccin Mocha palette
var (
	colorBase     = lipgloss.Color("#1e1e2e")
	colorSurface0 = lipgloss.Color("#313244")
	colorSurface1 = lipgloss.Color("#45475a")
	colorText     = lipgloss.Color("#cdd6f4")
	colorSubtext  = lipgloss.Color("#a6adc8")
	colorGreen    = lipgloss.Color("#a6e3a1")
	colorYellow   = lipgloss.Color("#f9e2af")
	colorRed      = lipgloss.Color("#f38ba8")
	colorBlue     = lipgloss.Color("#89b4fa")
	colorMauve    = lipgloss.Color("#cba6f7")
)

var (
	TabStyle = lipgloss.NewStyle().
			Padding(0, 2).
			Foreground(colorSubtext)

	ActiveTabStyle = lipgloss.NewStyle().
			Padding(0, 2).
			Foreground(colorBase).
			Background(colorBlue).
			Bold(true)

	RowStyle = lipgloss.NewStyle().
			Foreground(colorText)

	SelectedRowStyle = lipgloss.NewStyle().
				Foreground(colorBase).
				Background(colorSurface1)

	ScoreHighStyle = lipgloss.NewStyle().Foreground(colorGreen).Bold(true)
	ScoreMidStyle  = lipgloss.NewStyle().Foreground(colorYellow)
	ScoreLowStyle  = lipgloss.NewStyle().Foreground(colorRed)

	StatusStyle = map[string]lipgloss.Style{
		"evaluated": lipgloss.NewStyle().Foreground(colorSubtext),
		"applying":  lipgloss.NewStyle().Foreground(colorYellow),
		"applied":   lipgloss.NewStyle().Foreground(colorBlue),
		"responded": lipgloss.NewStyle().Foreground(colorBlue).Bold(true),
		"interview": lipgloss.NewStyle().Foreground(colorMauve).Bold(true),
		"offer":     lipgloss.NewStyle().Foreground(colorGreen).Bold(true),
		"accepted":  lipgloss.NewStyle().Foreground(colorGreen).Bold(true),
		"rejected":  lipgloss.NewStyle().Foreground(colorRed),
		"withdrawn": lipgloss.NewStyle().Foreground(colorRed),
		"skip":      lipgloss.NewStyle().Foreground(colorSurface1),
	}

	PreviewStyle = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(colorSurface1).
			Padding(1, 2).
			Foreground(colorSubtext)

	HelpStyle = lipgloss.NewStyle().
			Foreground(colorSurface1).
			Padding(1, 0)
)
