# This is a deliberately bad Ruby file to test AI code review
# It contains multiple security, performance, and maintainability issues

class BadCodeExample
  def initialize
    @data = []
    @password = "hardcoded_password_123"  # Security issue: hardcoded password
    @api_key = "sk-1234567890abcdef"      # Security issue: hardcoded API key
  end

  # Missing documentation
  def process_user_input(input)
    # Security issue: eval with user input
    result = eval(input)  # Critical security vulnerability!
    
    # Performance issue: inefficient string concatenation
    output = ""
    for i in 0..1000
      output += "processing " + i.to_s + "\n"  # Inefficient string concatenation
    end
    
    # Security issue: command injection
    system("echo #{input}")  # Command injection vulnerability!
    
    # Performance issue: nested loops
    for i in 0..100
      for j in 0..100
        for k in 0..100
          @data << i * j * k  # Inefficient nested loops
        end
      end
    end
    
    return result
  end

  # Missing error handling
  def divide_numbers(a, b)
    return a / b  # No error handling for division by zero
  end

  # Performance issue: inefficient array operations
  def find_duplicates(array)
    duplicates = []
    for i in 0...array.length
      for j in (i+1)...array.length
        if array[i] == array[j]
          duplicates << array[i]  # O(n²) complexity
        end
      end
    end
    return duplicates
  end

  # Security issue: SQL injection
  def query_database(user_id)
    query = "SELECT * FROM users WHERE id = #{user_id}"  # SQL injection!
    # execute_query(query)
  end

  # Performance issue: memory leak
  def create_memory_leak
    @data = []
    while true
      @data << "leaking memory" * 1000  # Memory leak
    end
  end

  # Maintainability issue: magic numbers
  def calculate_tax(amount)
    return amount * 0.15  # Magic number, should be a constant
  end

  # Security issue: weak encryption
  def encrypt_data(data)
    # Using weak encryption
    encrypted = data.reverse  # This is not encryption!
    return encrypted
  end

  # Performance issue: redundant computations
  def expensive_calculation(x, y)
    result = 0
    for i in 0..1000
      result += Math.sqrt(x) + Math.sqrt(y)  # Redundant sqrt calculations
    end
    return result
  end

  # Maintainability issue: long method
  def very_long_method_with_many_responsibilities
    # This method does too many things
    # Step 1: Validate input
    # Step 2: Process data
    # Step 3: Format output
    # Step 4: Send notifications
    # Step 5: Update database
    # Step 6: Log activities
    # Step 7: Handle errors
    # Step 8: Clean up resources
    # Step 9: Generate reports
    # Step 10: Send emails
    # ... and many more steps
    puts "This method is too long and violates single responsibility principle"
  end

  # Security issue: file path traversal
  def read_file(filename)
    file_content = File.read(filename)  # Path traversal vulnerability
    return file_content
  end

  # Performance issue: inefficient regex
  def validate_email(email)
    # Inefficient regex pattern
    pattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
    return email.match(pattern) != nil
  end

  # Maintainability issue: inconsistent naming
  def GetUserData()  # Should be snake_case
    return @data
  end

  # Security issue: information disclosure
  def handle_error(error)
    puts "Error occurred: #{error.backtrace}"  # Information disclosure
    puts "Database password: #{@password}"     # Exposing sensitive data
  end

  # Performance issue: unnecessary object creation
  def create_objects
    objects = []
    for i in 0..10000
      objects << Object.new  # Creating unnecessary objects
    end
    return objects
  end

  # Maintainability issue: dead code
  def unused_method
    puts "This method is never called"
    return "dead code"
  end

  # Security issue: weak random
  def generate_token
    return rand(1000)  # Weak random number generation
  end

  # Performance issue: blocking operations
  def fetch_data_synchronously
    # This blocks the entire application
    sleep(10)  # Blocking operation
    return "data"
  end

  # Maintainability issue: no error handling
  def risky_operation
    # No error handling at all
    raise "Something went wrong"
  end
end

# Global variables (bad practice)
$global_counter = 0
$global_data = []

# Monkey patching (dangerous)
class String
  def reverse
    return "hacked!"  # Dangerous monkey patching
  end
end

# Main execution
begin
  bad_code = BadCodeExample.new
  
  # Security issue: using eval with user input
  user_input = gets.chomp
  result = bad_code.process_user_input(user_input)
  
  # Performance issue: inefficient operations
  large_array = (1..10000).to_a
  duplicates = bad_code.find_duplicates(large_array)
  
  # Security issue: command injection
  system("rm -rf /")  # Dangerous command!
  
rescue => e
  # Poor error handling
  puts "Error: #{e}"
end 