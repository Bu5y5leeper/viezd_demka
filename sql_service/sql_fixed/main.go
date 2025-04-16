package main

import (
	"database/sql"
	"fmt"
	"html/template"
	"net/http"
	"strconv"
	"strings"
	"unicode"

	_ "github.com/mattn/go-sqlite3"
)

type Person struct {
	Id          uint16
	LastName    string
	Name        string
	Otchestvo   string
	City        string
	Street      string
	HouseNumber uint16
	PhoneNumber string
	Secret      bool
}

var contacts []Person = []Person{}

func CreatePerson(id uint16, lastName string,
	name string, otchestvo string,
	city string, street string,
	houseNumber uint16, phoneNumber string,
	secret ...bool) *Person {
	var answ *Person = &Person{
		Id:          id,
		LastName:    lastName,
		Name:        name,
		Otchestvo:   otchestvo,
		City:        city,
		Street:      street,
		HouseNumber: houseNumber,
		PhoneNumber: phoneNumber,
	}
	if len(secret) != 0 {
		answ.Secret = secret[0]
	}
	return answ // если 0, то тут стандартно будет false
}

func (p Person) FullName() string {
	return fmt.Sprintf("%s %s %s from %s, street %s, h. %v | %s | is he hiden: %t \n",
		p.LastName, p.Name, p.Otchestvo, p.City, p.Street, p.HouseNumber, p.PhoneNumber, p.Secret)
}

//------------------------------------------------------------------------------------------------

func home_page(w http.ResponseWriter, r *http.Request) {
	// var bob_test Person = *CreatePerson(1, "Bob", "Brown", "Son of Dave", "New York", "Bruh", 15, "+7910-753-__-__")
	// fmt.Fprintf(w, "start one: %s", bob_test.FullName())
	tmpl, err := template.ParseFiles("templates/home_page.html", "templates/header.html", "templates/footer.html")

	if err != nil {
		fmt.Fprintf(w, err.Error())
	}

	tmpl.ExecuteTemplate(w, "home_page", nil)
}

func check_string(s string) string {
	if s == "" {
		return ""
	}
	var runes []rune = []rune(strings.ToLower(s))
	runes[0] = unicode.ToUpper(runes[0])
	return string(runes)
}

func search_the_person(w http.ResponseWriter, r *http.Request) {
	db, err := sql.Open("sqlite3", "./data/peopledb.db")
	if err != nil {
		fmt.Println(err.Error())
	}
	defer db.Close()

	var person Person = Person{}
	person.LastName = check_string(r.FormValue("lastname"))
	person.Name = check_string(r.FormValue("name"))
	person.Otchestvo = check_string(r.FormValue("otchestvo"))
	person.City = check_string(r.FormValue("city"))
	person.Street = check_string(r.FormValue("street"))
	temp, _ := strconv.Atoi(r.FormValue("house"))
	person.HouseNumber = uint16(temp)

	var request string
	if person.LastName != "" {
		request += fmt.Sprintf("LastName = '%s'", person.LastName)
	}
	if person.Name != "" {
		if request != "" {
			request += " and "
		}
		request += fmt.Sprintf("Name = '%s'", person.Name)
	}
	if person.Otchestvo != "" {
		if request != "" {
			request += " and "
		}
		request += fmt.Sprintf("Otchestvo = '%s'", person.Otchestvo)
	}
	if person.City != "" {
		if request != "" {
			request += " and "
		}
		request += fmt.Sprintf("City = '%s'", person.City)
	}
	if person.Street != "" {
		if request != "" {
			request += " and "
		}
		request += fmt.Sprintf("Street = '%s'", person.Street)
	}
	if person.HouseNumber != 0 {
		if request != "" {
			request += " and "
		}
		request += fmt.Sprintf("HouseNumber = '%v'", person.HouseNumber)
	}
	var res *sql.Rows
	contacts = []Person{}
	if request == "" {
		res, err = db.Query("Select * from person where Secret = 0")
		if err != nil {
			fmt.Println(err.Error())
		}

	} else {
		res, err = db.Query("Select * from person where ? and Secret = 0", request)
		if err != nil {
			fmt.Println(err.Error())
		}
	}
	for res.Next() {
		var contact Person
		err = res.Scan(&contact.Id, &contact.LastName, &contact.Name,
			&contact.Otchestvo, &contact.City, &contact.Street,
			&contact.HouseNumber, &contact.PhoneNumber, &contact.Secret)
		if err != nil {
			fmt.Fprintf(w, err.Error())
		}
		contacts = append(contacts, contact)
		//fmt.Printf(contact.FullName())
	}
	tmpl, err := template.ParseFiles("templates/home_page.html", "templates/header.html", "templates/footer.html")

	if err != nil {
		fmt.Fprintf(w, err.Error())
	}

	tmpl.ExecuteTemplate(w, "home_page", contacts)
}

func handleRequest() {
	fs := http.FileServer(http.Dir("static"))
	fd := http.FileServer(http.Dir("data"))
	http.Handle("/static/", http.StripPrefix("/static/", fs))
	http.Handle("/data/", http.StripPrefix("/data/", fd))
	http.HandleFunc("/", home_page)
	http.HandleFunc("/search_the_person", search_the_person)
	http.ListenAndServe(":8080", nil)
}

func main() {
	handleRequest()
}
