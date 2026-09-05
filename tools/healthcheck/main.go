// Command healthcheck pings the core API endpoints and exits non-zero if
// any of them fail. Usable manually, in CI, or from an external monitor:
//
//	go run . -base https://api.structuredadventures.com
package main

import (
	"flag"
	"fmt"
	"net/http"
	"os"
	"time"
)

var endpoints = []string{
	"/api/v1/homepage/",
	"/api/v1/tours/",
	"/api/v1/site/",
	"/sitemap.xml",
}

func main() {
	base := flag.String("base", "http://127.0.0.1:8000", "API base URL")
	timeout := flag.Duration("timeout", 5*time.Second, "per-request timeout")
	flag.Parse()

	client := &http.Client{Timeout: *timeout}
	failed := false

	for _, ep := range endpoints {
		url := *base + ep
		resp, err := client.Get(url)
		if err != nil {
			fmt.Printf("FAIL %s: %v\n", url, err)
			failed = true
			continue
		}
		resp.Body.Close()
		if resp.StatusCode != http.StatusOK {
			fmt.Printf("FAIL %s: status %d\n", url, resp.StatusCode)
			failed = true
			continue
		}
		fmt.Printf("OK   %s\n", url)
	}

	if failed {
		os.Exit(1)
	}
}
