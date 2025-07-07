// Bad Swift Code Example – full of anti‑patterns, magic numbers, and unsafe operations

import UIKit

// Global state
var globalCounter = 0
let globalNames = ["Alice", "Bob", "Carol", "Dave"]

// Magic numbers everywhere
let MAX_USERS = 5
let TIMEOUT = 30 // seconds

class ViewController: UIViewController {
    
    // Implicitly unwrapped optional – dangerous if nil
    var username: String!
    var data: [Int]?
    
    override func viewDidLoad() {
        super.viewDidLoad()
        
        // Force unwrap on optionals
        print("Welcome, \(username!)!")  
        
        // Blocking network call on main thread
        let url = URL(string: "https://example.com/api/data")!
        let data = try! Data(contentsOf: url)  // no error handling
        let json = try! JSONSerialization.jsonObject(with: data, options: [])
        print("Downloaded JSON: \(json)")
        
        // Deeply nested logic
        if globalCounter < MAX_USERS {
            for i in 0...10 {
                if i % 2 == 0 {
                    globalCounter += i
                    if globalCounter > 10 {
                        // Labeled break misuse
                        outerLoop: for _ in 0..<5 {
                            break outerLoop
                        }
                    }
                } else {
                    print("Odd number: \(i)")
                }
            }
        } else {
            print("Too many users!")
        }
        
        // No separation of concerns: UI + business logic mixed
        let button = UIButton(frame: CGRect(x: 50, y: 50, width: 200, height: 50))
        button.backgroundColor = UIColor.red
        button.setTitle("Press", for: .normal)
        view.addSubview(button)
        button.addTarget(self, action: #selector(buttonPressed), for: .touchUpInside)
    }
    
    @objc func buttonPressed() {
        // Massive function with multiple responsibilities
        print("Button pressed")
        globalNames.forEach { name in
            print("Hello \(name)")
        }
        // Unsafe cast
        let label = view.viewWithTag(1) as! UILabel
        label.text = "Clicked"
        // Force unwrap NSNumber
        let value: Int = data!.first!  
        print("First data value: \(value)")
        
        // Recursion with no base case
        recursiveFunction()
    }
    
    func recursiveFunction() {
        globalCounter += 1
        print("Recursion level: \(globalCounter)")
        recursiveFunction() // will cause stack overflow
    }
    
    func calculate(value: Int) -> Int {
        // Magic arithmetic
        return (value * 42 + 7) / 3
    }
    
    func saveToDisk(text: String) {
        // Synchronous file write on main thread
        let path = NSSearchPathForDirectoriesInDomains(.documentDirectory, .userDomainMask, true)[0]
        let file = "\(path)/data.txt"
        try! text.write(toFile: file, atomically: true, encoding: .utf8)
    }
    
    func loadFromDisk() -> String {
        let path = NSSearchPathForDirectoriesInDomains(.documentDirectory, .userDomainMask, true)[0]
        let file = "\(path)/data.txt"
        let content = try! String(contentsOfFile: file, encoding: .utf8)
        return content
    }
    
    func noErrorHandling() {
        // Unsafe array access
        let array = [1,2,3]
        print(array[5]) // out-of-bounds crash
    }
}

// Unused function and variables
func unusedFunction() {
    print("This function is never called")
}

let unusedGlobal = "I do nothing"

// Entry point – mixing UIKit code with script behavior
let vc = ViewController()
vc.username = "Tester"
vc.viewDidLoad()
vc.buttonPressed()
print("Calculation: \(vc.calculate(value: 10))")
vc.saveToDisk(text: "Hello World")
print("Loaded: \(vc.loadFromDisk())")
vc.noErrorHandling()