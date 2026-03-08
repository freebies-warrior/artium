package handlers

import "testing"

func TestParseUUIDAcceptsPostgresFormats(t *testing.T) {
	tests := []string{
		"a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
		"A0EEBC99-9C0B-4EF8-BB6D-6BB9BD380A11",
		"{a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11}",
		"a0eebc999c0b4ef8bb6d6bb9bd380a11",
		"a0ee-bc99-9c0b-4ef8-bb6d-6bb9-bd38-0a11",
		"{a0eebc99-9c0b4ef8-bb6d6bb9-bd380a11}",
	}

	for _, tc := range tests {
		if _, err := parseUUID(tc); err != nil {
			t.Fatalf("expected %q to parse: %v", tc, err)
		}
	}
}

func TestParseUUIDRejectsMalformedFormats(t *testing.T) {
	tests := []string{
		"",
		"not-a-uuid",
		"{a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
		"a0e-ebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
		"a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11-",
		"urn:uuid:a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
		"g0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
	}

	for _, tc := range tests {
		if _, err := parseUUID(tc); err == nil {
			t.Fatalf("expected %q to be rejected", tc)
		}
	}
}
