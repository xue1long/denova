package main

import (
	"net"
	"testing"
)

func TestFindAvailablePortFallsBackToSystemAssignedPort(t *testing.T) {
	port, err := findAvailablePort("65535", 20)
	if err != nil {
		t.Fatal(err)
	}
	listener, err := net.Listen("tcp", net.JoinHostPort("0.0.0.0", port))
	if err != nil {
		t.Fatalf("selected port %s cannot be bound: %v", port, err)
	}
	defer listener.Close()
}
