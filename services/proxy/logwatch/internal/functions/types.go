package functions

// 数据结构
type MetaData struct {
	DestinationIP   string `json:"destinationIP"`
	DestinationPort string `json:"destinationPort"`
	DNSMode         string `json:"dnsMode"`
	Host            string `json:"host"`
	Network         string `json:"network"`
	ProcessPath     string `json:"processPath"`
	SourceIP        string `json:"sourceIP"`
	SourcePort      string `json:"sourcePort"`
	Type            string `json:"type"`
}
type ConnectionInfo struct {
	Chains      []string `json:"chains"`
	Download    uint32   `json:"download"`
	ID          string   `json:"id"`
	Metadata    MetaData `json:"metadata"`
	Rule        string   `json:"rule"`
	RulePayload string   `json:"rulePayload"`
	Start       string   `json:"start"`
	Upload      uint32   `json:"upload"`
}
type UpdateMessage struct {
	Connections   []ConnectionInfo `json:"connections"`
	DownloadTotal uint32           `json:"downloadTotal"`
	Memory        uint32           `json:"memory"`
	UploadTotal   uint32           `json:"uploadTotal"`
}
