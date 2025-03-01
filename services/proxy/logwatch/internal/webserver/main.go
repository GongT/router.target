package webserver

import (
	"context"
	_ "embed"
	"fmt"
	"net/http"
	"time"
)

//go:embed index.html
var indexHtml []byte
var server *http.Server

func index(w http.ResponseWriter, r *http.Request) {
	w.Write(indexHtml)
}

func Start() {
	mux := http.NewServeMux()
	mux.HandleFunc("/", index)
	mux.HandleFunc("/stats", readState)
	mux.HandleFunc("/favicon.ico", http.NotFound)

	server = &http.Server{
		Addr:    ":3281",
		Handler: mux,
	}

	fmt.Println("Starting server on :3281")
	if err := server.ListenAndServe(); err != nil {
		fmt.Println("Error starting server:", err)
	}
}

func Stop() {
	if server != nil {
		fmt.Println("Shutting down the server...")
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()

		server.Shutdown(ctx)
		server = nil
	}
}
