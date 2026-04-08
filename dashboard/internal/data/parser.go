package data

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
)

// Application represents a single row in applications.md
type Application struct {
	Num       int
	Date      string
	Company   string
	Role      string
	Score     float64
	Status    string
	Archetype string
	URL       string
	Notes     string
}

// StatusPriority returns sort order for status values.
// Higher = further along in process.
func StatusPriority(status string) int {
	priorities := map[string]int{
		"skip":      0,
		"withdrawn": 1,
		"rejected":  2,
		"evaluated": 3,
		"applying":  4,
		"applied":   5,
		"responded": 6,
		"interview": 7,
		"offer":     8,
		"accepted":  9,
	}
	if p, ok := priorities[strings.ToLower(status)]; ok {
		return p
	}
	return -1
}

// ParseApplications reads applications.md and returns parsed rows.
func ParseApplications(path string) ([]Application, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("open tracker: %w", err)
	}
	defer f.Close()

	var apps []Application
	scanner := bufio.NewScanner(f)

	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if !strings.HasPrefix(line, "|") || strings.HasPrefix(line, "| #") || strings.HasPrefix(line, "|--") {
			continue
		}

		cells := splitRow(line)
		if len(cells) < 8 {
			continue
		}

		num, _ := strconv.Atoi(strings.TrimSpace(cells[0]))
		score, _ := strconv.ParseFloat(strings.TrimSpace(cells[4]), 64)

		app := Application{
			Num:       num,
			Date:      strings.TrimSpace(cells[1]),
			Company:   strings.TrimSpace(cells[2]),
			Role:      strings.TrimSpace(cells[3]),
			Score:     score,
			Status:    strings.TrimSpace(cells[5]),
			Archetype: strings.TrimSpace(cells[6]),
			URL:       strings.TrimSpace(cells[7]),
		}
		if len(cells) > 8 {
			app.Notes = strings.TrimSpace(cells[8])
		}

		apps = append(apps, app)
	}

	return apps, scanner.Err()
}

// UpdateStatus rewrites a specific entry's status in the tracker file.
func UpdateStatus(path string, num int, newStatus string) error {
	content, err := os.ReadFile(path)
	if err != nil {
		return err
	}

	lines := strings.Split(string(content), "\n")
	pattern := regexp.MustCompile(fmt.Sprintf(`^\|\s*%d\s*\|`, num))

	for i, line := range lines {
		if pattern.MatchString(line) {
			cells := splitRow(line)
			if len(cells) >= 6 {
				cells[5] = " " + newStatus + " "
				lines[i] = "|" + strings.Join(cells, "|") + "|"
			}
			break
		}
	}

	return os.WriteFile(path, []byte(strings.Join(lines, "\n")), 0644)
}

// LoadReportSummary attempts to load a report preview for a company/role.
func LoadReportSummary(reportsDir, companySlug string) string {
	// Look for phase-4 pitch materials
	pattern := filepath.Join(reportsDir, "phase-4-pitch", companySlug, "talking-points.md")
	data, err := os.ReadFile(pattern)
	if err != nil {
		return "(no report found)"
	}
	// Return first 500 chars as preview
	s := string(data)
	if len(s) > 500 {
		s = s[:500] + "..."
	}
	return s
}

func splitRow(line string) []string {
	line = strings.TrimPrefix(line, "|")
	line = strings.TrimSuffix(line, "|")
	return strings.Split(line, "|")
}
