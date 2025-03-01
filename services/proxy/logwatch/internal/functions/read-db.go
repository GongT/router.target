package functions

import (
	"fmt"
)

type Row struct {
	ID            int    `json:"id"`
	Domain        string `json:"domain"`
	DownloadTotal int    `json:"download_total"`
	UploadTotal   int    `json:"upload_total"`
	OutputDirect  int    `json:"output_direct"`
	OutputProxy   int    `json:"output_proxy"`
	OutputUnknown int    `json:"output_unknown"`
}

func QueryPage(page int, pageSize int, orderField string, orderDesc bool) ([]Row, error) {
	var err error

	var order string
	if orderDesc {
		order = orderField + " DESC"
	} else {
		order = orderField + " ASC"
	}

	sql := fmt.Sprintf(`
		SELECT id,domain,download_total,upload_total,output_direct,output_proxy,output_unknown
		FROM statistics
		ORDER BY %s
		LIMIT ? OFFSET ?`, order)
	result, err := db.Query(sql, pageSize, page*pageSize)
	if err != nil {
		return nil, err
	}

	rows := make([]Row, pageSize, pageSize)
	index := 0
	for result.Next() {
		row := &rows[index]
		index++

		err = result.Scan(&row.ID, &row.Domain, &row.DownloadTotal, &row.UploadTotal, &row.OutputDirect, &row.OutputProxy, &row.OutputUnknown)
		if err != nil {
			return nil, err
		}
	}

	return rows[0:index], nil
}

func QueryMaxPage(perPage int) (int, error) {
	var count int
	err := db.QueryRow("SELECT COUNT(*) FROM statistics").Scan(&count)
	return (count + perPage - 1) / perPage, err
}
