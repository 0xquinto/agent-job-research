package ui

import (
	"fmt"
	"strings"
)

// View implements tea.Model
func (m Model) View() string {
	if len(m.Filtered) == 0 {
		return fmt.Sprintf("%s\n\n  No applications found.\n\n%s",
			m.renderTabs(), m.renderHelp())
	}

	var b strings.Builder
	b.WriteString(m.renderTabs())
	b.WriteString("\n\n")
	b.WriteString(m.renderList())
	b.WriteString("\n\n")

	if m.ActiveView == statusPickerView {
		b.WriteString(m.renderStatusPicker())
		b.WriteString("\n\n")
	} else if m.Preview != "" {
		b.WriteString(m.renderPreview())
		b.WriteString("\n\n")
	}

	b.WriteString(m.renderHelp())
	return b.String()
}

func (m Model) renderTabs() string {
	var parts []string
	for i, t := range Tabs {
		if i == m.ActiveTab {
			parts = append(parts, ActiveTabStyle.Render(t.Label))
		} else {
			parts = append(parts, TabStyle.Render(t.Label))
		}
	}
	return "  " + strings.Join(parts, " ") +
		fmt.Sprintf("    sort: %s", SortLabels[m.SortBy])
}

func (m Model) renderList() string {
	var lines []string
	visible := m.Height - 12
	if visible < 5 {
		visible = 5
	}
	if visible > len(m.Filtered) {
		visible = len(m.Filtered)
	}

	start := 0
	if m.Cursor >= visible {
		start = m.Cursor - visible + 1
	}
	end := start + visible
	if end > len(m.Filtered) {
		end = len(m.Filtered)
	}

	for i := start; i < end; i++ {
		app := m.Filtered[i]

		// Score styling
		scoreStr := fmt.Sprintf("%.1f", app.Score)
		if app.Score >= 7.5 {
			scoreStr = ScoreHighStyle.Render(scoreStr)
		} else if app.Score >= 5.5 {
			scoreStr = ScoreMidStyle.Render(scoreStr)
		} else {
			scoreStr = ScoreLowStyle.Render(scoreStr)
		}

		// Status styling
		statusStr := app.Status
		if style, ok := StatusStyle[app.Status]; ok {
			statusStr = style.Render(app.Status)
		}

		line := fmt.Sprintf("  %s  %-20s %-44s %s  %s",
			scoreStr,
			truncate(app.Company, 20),
			truncate(app.Role, 44),
			padRight(statusStr, app.Status, 12),
			app.Date,
		)

		if i == m.Cursor {
			line = SelectedRowStyle.Render(line)
		} else {
			line = RowStyle.Render(line)
		}
		lines = append(lines, line)
	}

	return strings.Join(lines, "\n")
}

func (m Model) renderStatusPicker() string {
	var lines []string
	lines = append(lines, "  Change status:")
	for i, s := range Statuses {
		prefix := "  "
		if i == m.StatusCursor {
			prefix = "> "
		}
		styl := StatusStyle[s]
		lines = append(lines, fmt.Sprintf("  %s%s", prefix, styl.Render(s)))
	}
	return strings.Join(lines, "\n")
}

func (m Model) renderPreview() string {
	if m.Preview == "" || m.Preview == "(no report found)" {
		return ""
	}
	return PreviewStyle.Render(m.Preview)
}

func (m Model) renderHelp() string {
	if m.ActiveView == statusPickerView {
		return HelpStyle.Render("  j/k: navigate | enter: select | esc: cancel")
	}
	return HelpStyle.Render(
		fmt.Sprintf("  j/k: navigate | h/l: tabs | s: sort (%s) | c: change status | q: quit",
			SortLabels[m.SortBy]))
}

func truncate(s string, n int) string {
	if len(s) <= n {
		return s + strings.Repeat(" ", n-len(s))
	}
	return s[:n-1] + "\u2026"
}

// padRight pads based on the raw (unstyled) text length
func padRight(styled, raw string, width int) string {
	if len(raw) >= width {
		return styled
	}
	return styled + strings.Repeat(" ", width-len(raw))
}
