package main

import (
	"fmt"
	"io/ioutil"
	"net/http"
	"os"
	"sync"
)

var globalCount = 0
var client = http.Client{} // no timeout

func main() {
	// Unsafe environment var usage
	apiKey := os.Getenv("API_KEY")
	fmt.Println("API Key:", apiKey) // prints even if empty

	// Blocking network call without error check
	resp, _ := http.Get("http://example.com/data")
	body, _ := ioutil.ReadAll(resp.Body)
	fmt.Println("Data:", string(body))
	// Forgot resp.Body.Close()

	// Concurrency gone wrong
	var wg sync.WaitGroup
	for i := 0; i < 5; i++ {
		wg.Add(1)
		go func() {
			// Capturing loop variable incorrectly
			fmt.Println("Goroutine count:", i)
			globalCount += i // race condition on globalCount
			wg.Done()
		}()
	}
	wg.Wait()

	// Slice out‑of‑bounds
	arr := []int{1, 2, 3}
	fmt.Println(arr[5]) // panic

	// No error handling for file operations
	ioutil.WriteFile("data.txt", []byte("hello"), 0644)
	data, _ := ioutil.ReadFile("data.txt")
	fmt.Println("File says:", string(data))

	// Unchecked type assertion
	var x interface{} = "hello"
	n := x.(int) // panic
	fmt.Println("Value:", n)

	// Infinite loop
	for {
		fmt.Println("Looping forever")
	}

	// Code never reached
	fmt.Println("Done")
}
