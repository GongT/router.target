package functions

import (
	"fmt"
	"net/url"
	"time"

	"github.com/gorilla/websocket"
)

var maxRetry = 5
var message_ch chan []byte
var quit_ch chan struct{}

func CloseWebSocket() {
	close(quit_ch)
	close(message_ch)
}

func doConnect(URL string) (<-chan struct{}, error) {
	u, err := url.Parse(URL)
	if err != nil {
		return nil, fmt.Errorf("failed to parse URL: %v", err)
	}

	fmt.Printf("[ws] connecting to %s...\n", u.String())
	con, _, err := websocket.DefaultDialer.Dial(u.String(), nil)

	if err != nil {
		return nil, fmt.Errorf("dial: %v", err)
	}

	fmt.Printf("[ws] connected.\n")

	connLost := make(chan struct{})

	go func() {
		defer close(connLost)
		defer con.Close()

		for {
			_, message, err := con.ReadMessage()
			if err != nil {
				if websocket.IsUnexpectedCloseError(err, websocket.CloseNormalClosure) {
					fmt.Println("[ws] error reading:", err)
				} else {
					fmt.Println("[ws] connection closed gracefully")
				}
				return
			}
			// fmt.Println("[ws] got line")
			select {
			case message_ch <- message:
				// fmt.Println("[ws] write channel ok")
				continue
			case <-quit_ch:
				con.WriteMessage(websocket.CloseMessage, websocket.FormatCloseMessage(websocket.CloseNormalClosure, ""))
				return
			}
		}
	}()

	return connLost, nil
}

func connectWithRetry(URL string) (<-chan struct{}, error) {
	var retryCount = 0
	var retryInterval time.Duration = 1
	for {
		connLost, err := doConnect(URL)
		if err == nil {
			return connLost, nil
		}

		retryCount++
		if retryCount > maxRetry {
			return nil, fmt.Errorf("not connected after 5 retries: %v", err)
		}

		fmt.Printf("[ws] failed to connect: %v, retrying in %d seconds...", err, retryInterval)
		select {
		case <-time.After(retryInterval * time.Second):
			continue
		case <-quit_ch:
			return nil, fmt.Errorf("interrupted during retry")
		}
	}
}

func connectReconnect(URL string) {
	for {
		connLost, err := connectWithRetry(URL)
		if err != nil {
			fmt.Printf("[ws] failed: %v\n", err)
			Shutdown(1)
			return
		}

		<-connLost

		if quitting {
			return
		}

		fmt.Println("[ws] connection lost, reconnecting...")
		time.Sleep(time.Second)

		if quitting {
			return
		}
	}
}

func ConnectWebSocket(URL string) <-chan []byte {
	message_ch = make(chan []byte)
	quit_ch = make(chan struct{}, 1)
	quitting = false

	go connectReconnect(URL)

	return message_ch
}
