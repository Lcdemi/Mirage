// Creates a Mirage Extension that can be deployed within Mirage
// This code is compiled into an executable and run as a service
// The goal of this program is to run display.exe every time a specific key in the word "PUZZLER" is pressed
// Display.exe will rotate the screen 90 degrees clockwise on Windows systems

package main

import (
	"fmt"
	"log"
	"os/exec"

	"github.com/eiannone/keyboard"
	"github.com/kardianos/service"
)

type program struct{}

var logger service.Logger

func (p *program) Start(s service.Service) error {
	go p.run()
	return nil
}
func (p *program) run() {
	listen()
}
func (p *program) Stop(s service.Service) error {
	return nil
}

func listen() {
	if err := keyboard.Open(); err != nil {
		logger.Error(fmt.Sprintf("Failed to open keyboard: %v", err))
		return
	}
	defer keyboard.Close()

	rotationValue := 0

	for {
		char, key, err := keyboard.GetKey()
		if err != nil {
			logger.Error(fmt.Sprintf("Error reading key: %v", err))
			continue
		}

		if key == keyboard.KeyEsc {
			break
		}

		switch char {
		case 'p', 'P', 'u', 'U', 'z', 'Z', 'l', 'L', 'e', 'E', 'r', 'R':
			rotationValue += 90
			fmt.Printf("%c key pressed - executing display.exe to rotate screen\n", char)
			logger.Info(fmt.Sprintf("%c key pressed - executing display.exe to rotate screen", char))

			err := exec.Command("C:\\Windows\\System32\\display.exe", fmt.Sprintf("/rotate:%d", rotationValue%360)).Start()
			if err != nil {
				fmt.Println("Error executing display.exe:", err)
				logger.Error(fmt.Sprintf("Error executing display.exe: %v", err))
			}
		}
	}
}

func main() {
	svcConfig := &service.Config{
		Name:        "DispSvc",
		DisplayName: "Display Enhancement Service",
		Description: "Provides color management and hardware-specific enhancements for monitors and internal displays.",
	}

	prg := &program{}
	s, err := service.New(prg, svcConfig)
	if err != nil {
		log.Fatal(err)
	}
	logger, err = s.Logger(nil)
	if err != nil {
		log.Fatal(err)
	}
	err = s.Run()
	if err != nil {
		logger.Error(err)
	}
}
