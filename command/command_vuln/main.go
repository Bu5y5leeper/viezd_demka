package main

import (
	"fmt"
	"html/template"
	"net/http"
	"os/exec"
)

func home_page(w http.ResponseWriter, r *http.Request) {
	var ser_ip string = r.FormValue("server_ip")

	if ser_ip == "" {
		ser_ip = "ping -c 4 8.8.8.8"
	} else {
		ser_ip = fmt.Sprintf("ping -c 4 %s", ser_ip)
	}
	cmd := exec.Command("/bin/sh", "-c", ser_ip)
	output, _ := cmd.CombinedOutput()

	tmpl, err := template.ParseFiles("templates/home_page.html", "templates/header.html", "templates/footer.html")

	if err != nil {
		fmt.Fprintf(w, err.Error())
	}

	tmpl.ExecuteTemplate(w, "home_page", string(output))
}

func handleRequest() {
	fs := http.FileServer(http.Dir("static"))
	http.Handle("/static/", http.StripPrefix("/static/", fs))
	http.HandleFunc("/", home_page)
	http.ListenAndServe(":8080", nil)
}

func main() {
	handleRequest()
}
