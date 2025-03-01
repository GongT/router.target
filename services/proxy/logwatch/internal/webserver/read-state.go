package webserver

import (
	"encoding/json"
	"io"
	"net/http"

	"github.com/gongt/proxy/logwatch/internal/functions"
)

type Response struct {
	Data    []functions.Row `json:"data"`
	Page    int             `json:"page"`
	MaxPage int             `json:"maxPage"`
}

type Request struct {
	Sort    string `json:"sort"`
	Order   string `json:"order"`
	Page    int    `json:"page"`
	PerPage int    `json:"perPage"`
}

func readState(w http.ResponseWriter, r *http.Request) {
	var req Request

	body, err := io.ReadAll(r.Body)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	json.Unmarshal(body, &req)

	maxPage, err := functions.QueryMaxPage(req.PerPage)

	req.Page = req.Page - 1
	if req.Page < 0 {
		req.Page = 0
	}
	if req.Page > maxPage {
		req.Page = 0
	}

	list, err := functions.QueryPage(req.Page, req.PerPage, req.Sort, req.Order == "desc")
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	res := Response{
		Data:    list,
		Page:    req.Page,
		MaxPage: maxPage,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(res)
}
