// Use `go run foo.go` to run your program

package main

import (
    "fmt"
    "runtime"
)


func number_server(add_number <-chan int, finishedExit <-chan int, outputNumber chan<- int) {
	var i = 0

	// This for-select pattern is one you will become familiar with if you're using go "correctly".
	for {
		select {
			// TODO: receive different messages and handle them correctly
			// You will at least need to update the number and handle control signals.
		case receivedNumber := <-add_number: //Whenever a number is sent on the defined addNumber channel, this number is placed in receivedNumber and added to i
			i += receivedNumber
		case outputNumber <- i:
			//sends i into outputNumber channel, such that it can be displayed
		case <-finishedExit: //Detects that the incrementing is finished by receiving a value on the defined finishedExit channel, and closes the select. 
			return
		}
	}
}

func incrementing(add_number chan<-int, finished chan<- bool) {
	for j := 0; j<1000000; j++ {
		add_number <- 1
	}
	//TODO: signal that the goroutine is finished
	close(finished) // close() is safer than channel <- true. this works when the channel is the source of the for loop incrementer , https://gobyexample.com/channel-synchronization
}

func decrementing(add_number chan<- int, finished chan<- bool) {
	for j := 0; j<1000000; j++ {
		add_number <- -1
	}
	//TODO: signal that the goroutine is finished
	close(finished) // close() is safer than channel <- true. This works when the channel is the source of the for loop incrementer, which channel <- does not do. , https://gobyexample.com/channel-synchronization
}

func main() {
	runtime.GOMAXPROCS(runtime.NumCPU())


	// TODO: Construct the required channels
	chAdd_number := make(chan int) //channels numbers to the number server from inc and dec functions
	chOutputNumber := make(chan int) // makes the final number available to the Println
	chFinishedInc := make(chan bool) //gives exit action to increment function
	chFinishedDec := make(chan bool) // gives exit action to decrement function
	chFinishedExit := make(chan int) // gives exit care for select function(number server)


	// TODO: Spawn the required goroutines
	go number_server(chAdd_number, chFinishedExit, chOutputNumber)
	go incrementing(chAdd_number, chFinishedInc)
	go decrementing(chAdd_number, chFinishedDec)

	// TODO: block on finished from both "worker" goroutines
	<- chFinishedInc  	//this blocks until the channel recevies something to output, or until it is closed with close()
	<- chFinishedDec	//this blocks until the channel recevies something to output, or until it is closed with close()

	fmt.Println("The magic number is:", <- chOutputNumber)
	chFinishedExit <- 0 //Exits the number server
}
