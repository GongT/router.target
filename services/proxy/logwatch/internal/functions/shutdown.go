package functions

import (
	"fmt"
	"os"
	"os/signal"
)

var interrupt = make(chan os.Signal, 1)
var shutdown = make(chan struct{})
var quitting = false
var ExitCode = 0

func RegisterSignal() {
	signal.Notify(interrupt, os.Interrupt)

	go func() {
		<-interrupt
		fmt.Printf("\nInterrupt\n")
		Shutdown(0)
	}()
}

func Shutdown(code int) {
	ExitCode = code
	quitting = true
	close(shutdown)
}

func WaitForInterrupt() <-chan struct{} {
	return shutdown
}

func IsQuitting() bool {
	return quitting
}
