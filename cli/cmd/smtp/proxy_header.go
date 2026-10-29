package main

import (
	"encoding/binary"
	"fmt"
	"net"
)

var proxySignature = []byte{0x0D, 0x0A, 0x0D, 0x0A, 0x00, 0x0D, 0x0A, 0x51, 0x55, 0x49, 0x54, 0x0A}

func proxyHeader(source string) ([]byte, error) {
	ip := net.ParseIP(source).To4()
	if ip == nil {
		return nil, fmt.Errorf("%s is not an IPv4 address", source)
	}
	header := append([]byte{}, proxySignature...)
	header = append(header, 0x21, 0x11)
	header = binary.BigEndian.AppendUint16(header, 12)
	header = append(header, ip...)
	header = append(header, net.IPv4(127, 0, 0, 1).To4()...)
	header = binary.BigEndian.AppendUint16(header, 50000)
	header = binary.BigEndian.AppendUint16(header, 25)
	return header, nil
}
