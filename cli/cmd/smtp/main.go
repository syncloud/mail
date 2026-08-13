package main

import (
	"flag"
	"fmt"
	"os"
	"strings"
)

func main() {
	socket := flag.String("socket", "", "unix socket the tunnel delivers to")
	from := flag.String("from", "", "sender")
	recipient := flag.String("rcpt", "", "recipient")
	subject := flag.String("subject", "", "subject, delivery is skipped when empty")
	body := flag.String("body", "", "message body")
	repeat := flag.Int("repeat", 1, "how many lines the body is repeated to")
	flag.Parse()

	if *socket == "" || *from == "" || *recipient == "" {
		fmt.Fprintln(os.Stderr, "socket, from and rcpt are required")
		os.Exit(2)
	}

	session, err := Dial(*socket)
	if err != nil {
		fmt.Fprintf(os.Stderr, "cannot reach %s: %v\n", *socket, err)
		os.Exit(1)
	}
	defer session.Close()

	text := *body
	if *repeat > 1 {
		text = strings.TrimSuffix(strings.Repeat(*body+"\n", *repeat), "\n")
	}

	deliverErr := session.Deliver(*from, *recipient, *subject, text)
	fmt.Print(session.Transcript())
	if deliverErr != nil {
		fmt.Fprintf(os.Stderr, "conversation failed: %v\n", deliverErr)
		os.Exit(1)
	}
}
