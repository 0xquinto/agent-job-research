package ui

import (
	"sort"
	"strings"

	"github.com/0xQuinto/agent-job-research/dashboard/internal/data"
	tea "github.com/charmbracelet/bubbletea"
)

type viewState int

const (
	pipelineView viewState = iota
	statusPickerView
)

type sortMode int

const (
	sortByScore sortMode = iota
	sortByDate
	sortByCompany
	sortByStatus
)

// SortLabels exported for use in views
var SortLabels = []string{"score", "date", "company", "status"}

type tab struct {
	Label  string
	Filter func(data.Application) bool
}

// Tabs defines the filter tabs
var Tabs = []tab{
	{"ALL", func(_ data.Application) bool { return true }},
	{"EVALUATED", func(a data.Application) bool { return a.Status == "evaluated" }},
	{"APPLIED", func(a data.Application) bool { return a.Status == "applied" }},
	{"INTERVIEW", func(a data.Application) bool { return a.Status == "interview" }},
	{"TOP >=7.5", func(a data.Application) bool { return a.Score >= 7.5 && a.Status != "skip" }},
	{"SKIP", func(a data.Application) bool { return a.Status == "skip" }},
}

// Statuses is the ordered list for the status picker
var Statuses = []string{
	"evaluated", "applying", "applied", "responded",
	"interview", "offer", "accepted", "rejected", "withdrawn", "skip",
}

// Model is the main Bubble Tea model
type Model struct {
	AllApps      []data.Application
	Filtered     []data.Application
	Cursor       int
	ActiveTab    int
	SortBy       sortMode
	ActiveView   viewState
	TrackerPath  string
	ReportsDir   string
	Preview      string
	StatusCursor int
	Width        int
	Height       int
}

// NewModel creates a new model from parsed applications
func NewModel(apps []data.Application, trackerPath, reportsDir string) Model {
	m := Model{
		AllApps:     apps,
		TrackerPath: trackerPath,
		ReportsDir:  reportsDir,
	}
	m.applyFilter()
	return m
}

func (m *Model) applyFilter() {
	m.Filtered = nil
	for _, a := range m.AllApps {
		if Tabs[m.ActiveTab].Filter(a) {
			m.Filtered = append(m.Filtered, a)
		}
	}
	m.applySort()
	if m.Cursor >= len(m.Filtered) {
		m.Cursor = max(0, len(m.Filtered)-1)
	}
}

func (m *Model) applySort() {
	sort.SliceStable(m.Filtered, func(i, j int) bool {
		a, b := m.Filtered[i], m.Filtered[j]
		switch m.SortBy {
		case sortByScore:
			return a.Score > b.Score
		case sortByDate:
			return a.Date > b.Date
		case sortByCompany:
			return strings.ToLower(a.Company) < strings.ToLower(b.Company)
		case sortByStatus:
			return data.StatusPriority(a.Status) > data.StatusPriority(b.Status)
		}
		return false
	})
}

// Init implements tea.Model
func (m Model) Init() tea.Cmd { return nil }

// Update implements tea.Model
func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.Width = msg.Width
		m.Height = msg.Height
		return m, nil

	case tea.KeyMsg:
		if m.ActiveView == statusPickerView {
			return m.updateStatusPicker(msg)
		}
		return m.updatePipeline(msg)
	}
	return m, nil
}

func (m Model) updatePipeline(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch msg.String() {
	case "q", "ctrl+c":
		return m, tea.Quit
	case "up", "k":
		if m.Cursor > 0 {
			m.Cursor--
			m.loadPreview()
		}
	case "down", "j":
		if m.Cursor < len(m.Filtered)-1 {
			m.Cursor++
			m.loadPreview()
		}
	case "left", "h":
		if m.ActiveTab > 0 {
			m.ActiveTab--
			m.applyFilter()
		}
	case "right", "l", "f":
		if m.ActiveTab < len(Tabs)-1 {
			m.ActiveTab++
			m.applyFilter()
		}
	case "s":
		m.SortBy = (m.SortBy + 1) % 4
		m.applySort()
	case "c":
		if len(m.Filtered) > 0 {
			m.ActiveView = statusPickerView
			m.StatusCursor = 0
		}
	}
	return m, nil
}

func (m Model) updateStatusPicker(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch msg.String() {
	case "esc", "q":
		m.ActiveView = pipelineView
	case "up", "k":
		if m.StatusCursor > 0 {
			m.StatusCursor--
		}
	case "down", "j":
		if m.StatusCursor < len(Statuses)-1 {
			m.StatusCursor++
		}
	case "enter":
		if m.Cursor < len(m.Filtered) {
			app := m.Filtered[m.Cursor]
			newStatus := Statuses[m.StatusCursor]
			_ = data.UpdateStatus(m.TrackerPath, app.Num, newStatus)
			// Update in memory
			for i := range m.AllApps {
				if m.AllApps[i].Num == app.Num {
					m.AllApps[i].Status = newStatus
					break
				}
			}
			m.applyFilter()
			m.ActiveView = pipelineView
		}
	}
	return m, nil
}

func (m *Model) loadPreview() {
	if m.Cursor < len(m.Filtered) {
		app := m.Filtered[m.Cursor]
		slug := strings.ToLower(strings.ReplaceAll(app.Company, " ", "-"))
		m.Preview = data.LoadReportSummary(m.ReportsDir, slug)
	}
}

func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}
