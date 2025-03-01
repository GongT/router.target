package functions

import (
	"database/sql"
	"fmt"
	"net"

	_ "github.com/mattn/go-sqlite3"
)

var db *sql.DB = nil // 全局数据库连接
var stmt *sql.Stmt = nil

func CloseDatabase() {
	fmt.Printf("closing database...\n")
	if db != nil {
		stmt.Close()
		stmt = nil
		db.Close()
		db = nil
	}
}

// 用于打开或创建 SQLite 数据库
func ConnectDatabase(dbFile string) error {
	var err error
	db, err = sql.Open("sqlite3", dbFile)
	if err != nil {
		return err
	}

	// 检查数据库连接是否成功
	if err = db.Ping(); err != nil {
		return fmt.Errorf("can not read/write database: %v", err)
	}

	// 创建 statistics 表
	_, err = db.Exec(`
		CREATE TABLE IF NOT EXISTS statistics (
			id INTEGER PRIMARY KEY,
			domain TEXT UNIQUE,
			download_total INTEGER,
			upload_total INTEGER,
			output_direct INTEGER,
			output_proxy INTEGER,
			output_unknown INTEGER
		)
	`)
	if err != nil {
		return fmt.Errorf("failed to create table: %v", err)
	}

	_stmt, err := db.Prepare(`
		INSERT INTO statistics 
			(domain,download_total,upload_total,output_direct,output_proxy,output_unknown)
		VALUES (?, ?, ?, ?, ?, ?)
		ON CONFLICT(domain) DO UPDATE
		SET
			download_total = download_total + excluded.download_total,
			upload_total = upload_total + excluded.upload_total,
			output_direct = output_direct + excluded.output_direct,
			output_proxy = output_proxy + excluded.output_proxy,
			output_unknown = output_unknown + excluded.output_unknown
	`)
	if err != nil {
		return fmt.Errorf("failed to prepare statement: %v", err)
	}

	stmt = _stmt

	return nil
}

func checkIp(host string) bool {
	ip := net.ParseIP(host)
	if ip == nil {
		return false
	}
	return true
}

type proxyKind int

func (d proxyKind) String() string {
	return [...]string{"Unknown", "Direct", "Proxy"}[d]
}

const (
	Unknown proxyKind = iota
	Direct
	Proxy
)

// 将连接信息插入到数据库中
func ConterDomain(conn ConnectionInfo) error {
	domain := conn.Metadata.Host
	if len(domain) == 0 {
		if !checkIp(conn.Metadata.DestinationIP) {
			return fmt.Errorf("invalid ip: %s", conn.Metadata.DestinationIP)
		}
		domain = conn.Metadata.DestinationIP
	}

	hitChain := "-"
	_ = hitChain
	kind := Unknown
	for _, chain := range conn.Chains {
		if chain == "out.auto" || chain == "out.select" || chain == "out.manual" {
			kind = Proxy
			hitChain = chain
			break
		}
		if chain == "out.direct" || chain == "out.lan" || chain == "out.vpn" {
			kind = Direct
			hitChain = chain
			break
		}
	}

	// fmt.Printf("closed connection: %s --> %s (%s)\n", domain, hitChain, kind)
	err := increaseDomain(domain, conn.Download, conn.Upload, kind)
	if err != nil {
		fmt.Printf("failed insert database: %v\n", err)
	}

	return nil
}

func increaseDomain(domain string, download, upload uint32, kind proxyKind) error {
	var direct, proxy, unknown int = 0, 0, 0

	switch kind {
	case Direct:
		direct = 1
	case Proxy:
		proxy = 1
	default:
		unknown = 1
	}

	result, err := stmt.Exec(domain, download, upload, direct, proxy, unknown)
	if err != nil {
		return err
	}

	_, err = result.LastInsertId()
	if err != nil {
		return err
	}

	return nil
}
