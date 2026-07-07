package model

import "testing"

func TestIncidentStateMachine(t *testing.T) {
	cases := []struct {
		from    IncidentStatus
		to      IncidentStatus
		allowed bool
	}{
		{StatusDetected, StatusDiagnosing, true},
		{StatusDetected, StatusResolved, false},
		{StatusDiagnosing, StatusDiagnosed, true},
		{StatusDiagnosed, StatusFixing, true},
		{StatusFixing, StatusFixReady, true},
		{StatusFixReady, StatusApplying, true},
		{StatusApplying, StatusVerifying, true},
		{StatusVerifying, StatusResolved, true},
		{StatusResolved, StatusDetected, false},
		{StatusFailed, StatusDiagnosing, true},
		{StatusEscalated, StatusFixReady, true},
		{StatusDetected, StatusEscalated, true},
		{StatusVerifying, StatusApplying, false},
	}

	for _, c := range cases {
		inc := &Incident{Status: c.from}
		if got := inc.CanTransition(c.to); got != c.allowed {
			t.Errorf("CanTransition(%s -> %s) = %v, want %v", c.from, c.to, got, c.allowed)
		}
	}
}
