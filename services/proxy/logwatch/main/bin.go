package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path"

	funcs "github.com/gongt/proxy/logwatch/internal/functions"
	"github.com/gongt/proxy/logwatch/internal/webserver"

	_ "github.com/mattn/go-sqlite3"
)

var URL = "ws://10.0.0.1:3280/connections?token=05ab516b88ae"
var lastMessage *funcs.UpdateMessage = nil

func main() {
	run()
	os.Exit(funcs.ExitCode)
}

func run() {
	funcs.RegisterSignal()

	state_dir := os.Getenv("STATE_DIRECTORY")
	if len(state_dir) == 0 {
		state_dir = "/var/lib/proxy"
	}

	defer funcs.CloseDatabase()

	err := funcs.ConnectDatabase(path.Join(state_dir, "domain-statis.db"))
	if err != nil {
		fmt.Printf("failed to open or create database: %v\n", err)
		funcs.Shutdown(2)
		return
	}
	fmt.Println("database opened")

	defer funcs.CloseWebSocket()
	ch := funcs.ConnectWebSocket(URL)

	fmt.Println("waitting for messages...")

	defer webserver.Stop()
	go webserver.Start()

	for {
		select {
		case <-funcs.WaitForInterrupt():
			return
		case message := <-ch:
			processData(message)
		}
	}
}

// processData 函数用于处理接收到的数据
func processData(message []byte) {
	var newMsg = new(funcs.UpdateMessage)

	err := json.Unmarshal(message, &newMsg)
	if err != nil {
		fmt.Println("JSON 解码错误:", err)
		return
	}

	// 创建一个 map 用于存储 newMsg.Connections 中的 ID
	newMsgIDs := make(map[string]bool)
	for _, conn := range newMsg.Connections {
		newMsgIDs[conn.ID] = true
	}

	if lastMessage != nil {
		for _, conn := range lastMessage.Connections {
			if !newMsgIDs[conn.ID] {
				funcs.ConterDomain(conn)
			}
		}
	}

	lastMessage = newMsg
}
