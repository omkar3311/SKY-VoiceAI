app = {
   #add your app path 
}

website = {
    "chat gpt": "https://chat.openai.com",
    "youtube": "https://www.youtube.com",
    "facebook": "https://www.facebook.com",
    "instagram": "https://www.instagram.com",
    "google":"https://www.google.com",
}

intro='''Hi, I'm SKY—your Smart, Knowledgeable Assistant! 
I’m here to help you with anything from answering questions to managing tasks and providing quick information. 
Whether you need assistance with coding, browsing the web, or just a fun fact,
I’m always ready. Just call my name, and I’ll be there to assist you! '''

#you can add any of algorithms
code = {
    "hello world": '''#include <iostream>\nusing namespace std;\nint main() {\n    cout << "Hello, World!";\n    return 0;\n}''',

    "sum of two numbers": '''#include <iostream>\nusing namespace std;\nint main() {\n    int a, b;\n    cout << "Enter two numbers: ";\n    cin >> a >> b;\n    cout << "Sum: " << a + b;\n    return 0;\n}''',

    "even odd": '''#include <iostream>\nusing namespace std;\nint main() {\n    int num;\n    cout << "Enter a number: ";\n    cin >> num;\n    if (num % 2 == 0)\n        cout << "Even";\n    else\n        cout << "Odd";\n    return 0;\n}''',

    "factorial": '''#include <iostream>\nusing namespace std;\nint factorial(int n) {\n    return (n == 0 || n == 1) ? 1 : n * factorial(n - 1);\n}\nint main() {\n    int num;\n    cout << "Enter a number: ";\n    cin >> num;\n    cout << "Factorial: " << factorial(num);\n    return 0;\n}''',

    "fibonacci series": '''#include <iostream>\nusing namespace std;\nvoid fibonacci(int n) {\n    int a = 0, b = 1, next;\n    for (int i = 0; i < n; i++) {\n        cout << a << " ";\n        next = a + b;\n        a = b;\n        b = next;\n    }\n}\nint main() {\n    int n;\n    cout << "Enter number of terms: ";\n    cin >> n;\n    fibonacci(n);\n    return 0;\n}''',

    "reverse string": '''#include <iostream>\n#include <algorithm>\nusing namespace std;\nint main() {\n    string str;\n    cout << "Enter a string: ";\n    cin >> str;\n    reverse(str.begin(), str.end());\n    cout << "Reversed: " << str;\n    return 0;\n}''',

    "prime number": '''#include <iostream>\nusing namespace std;\nbool isPrime(int n) {\n    if (n < 2) return false;\n    for (int i = 2; i * i <= n; i++) {\n        if (n % i == 0)\n            return false;\n    }\n    return true;\n}\nint main() {\n    int num;\n    cout << "Enter a number: ";\n    cin >> num;\n    if (isPrime(num))\n        cout << "Prime";\n    else\n        cout << "Not Prime";\n    return 0;\n}''',

    "armstrong number": '''#include <iostream>\n#include <cmath>\nusing namespace std;\nbool isArmstrong(int num) {\n    int sum = 0, temp = num, digits = 0;\n    while (temp > 0) {\n        temp /= 10;\n        digits++;\n    }\n    temp = num;\n    while (temp > 0) {\n        int digit = temp % 10;\n        sum += pow(digit, digits);\n        temp /= 10;\n    }\n    return sum == num;\n}\nint main() {\n    int num;\n    cout << "Enter a number: ";\n    cin >> num;\n    if (isArmstrong(num))\n        cout << "Armstrong Number";\n    else\n        cout << "Not an Armstrong Number";\n    return 0;\n}''',

    "palindrome check": '''#include <iostream>\nusing namespace std;\nbool isPalindrome(int num) {\n    int rev = 0, temp = num;\n    while (temp > 0) {\n        rev = rev * 10 + temp % 10;\n        temp /= 10;\n    }\n    return rev == num;\n}\nint main() {\n    int num;\n    cout << "Enter a number: ";\n    cin >> num;\n    if (isPalindrome(num))\n        cout << "Palindrome";\n    else\n        cout << "Not a Palindrome";\n    return 0;\n}''',

    "gcd lcm": '''#include <iostream>\nusing namespace std;\nint gcd(int a, int b) {\n    return (b == 0) ? a : gcd(b, a % b);\n}\nint lcm(int a, int b) {\n    return (a * b) / gcd(a, b);\n}\nint main() {\n    int a, b;\n    cout << "Enter two numbers: ";\n    cin >> a >> b;\n    cout << "GCD: " << gcd(a, b) << "\\nLCM: " << lcm(a, b);\n    return 0;\n}''',

    "matrix addition": '''#include <iostream>\nusing namespace std;\nint main() {\n    int a[2][2], b[2][2], sum[2][2];\n    cout << "Enter elements of first 2x2 matrix:\\n";\n    for (int i = 0; i < 2; i++)\n        for (int j = 0; j < 2; j++)\n            cin >> a[i][j];\n    cout << "Enter elements of second 2x2 matrix:\\n";\n    for (int i = 0; i < 2; i++)\n        for (int j = 0; j < 2; j++)\n            cin >> b[i][j];\n    cout << "Sum of matrices:\\n";\n    for (int i = 0; i < 2; i++) {\n        for (int j = 0; j < 2; j++) {\n            sum[i][j] = a[i][j] + b[i][j];\n            cout << sum[i][j] << " ";\n        }\n        cout << "\\n";\n    }\n    return 0;\n}''',

    "bubble sort": '''#include <iostream>\nusing namespace std;\nvoid bubbleSort(int arr[], int n) {\n    for (int i = 0; i < n - 1; i++)\n        for (int j = 0; j < n - i - 1; j++)\n            if (arr[j] > arr[j + 1])\n                swap(arr[j], arr[j + 1]);\n}\nint main() {\n    int n;\n    cout << "Enter array size: ";\n    cin >> n;\n    int arr[n];\n    cout << "Enter elements: ";\n    for (int i = 0; i < n; i++)\n        cin >> arr[i];\n    bubbleSort(arr, n);\n    cout << "Sorted array: ";\n    for (int i = 0; i < n; i++)\n        cout << arr[i] << " ";\n    return 0;\n}''',

    "swap two numbers": '''#include <iostream>\nusing namespace std;\nint main() {\n    int a, b, temp;\n    cout << "Enter two numbers: ";\n    cin >> a >> b;\n    temp = a;\n    a = b;\n    b = temp;\n    cout << "Swapped values: " << a << " " << b;\n    return 0;\n}''',

    "largest of three": '''#include <iostream>\nusing namespace std;\nint main() {\n    int a, b, c;\n    cout << "Enter three numbers: ";\n    cin >> a >> b >> c;\n    cout << "Largest number: " << ((a > b && a > c) ? a : (b > c ? b : c));\n    return 0;\n}''',

    "reverse number": '''#include <iostream>\nusing namespace std;\nint main() {\n    int num, rev = 0;\n    cout << "Enter a number: ";\n    cin >> num;\n    while (num > 0) {\n        rev = rev * 10 + num % 10;\n        num /= 10;\n    }\n    cout << "Reversed number: " << rev;\n    return 0;\n}''',

    "ascii value": '''#include <iostream>\nusing namespace std;\nint main() {\n    char ch;\n    cout << "Enter a character: ";\n    cin >> ch;\n    cout << "ASCII Value: " << int(ch);\n    return 0;\n}''',

    "simple calculator": '''#include <iostream>\nusing namespace std;\nint main() {\n    double num1, num2;\n    char op;\n    cout << "Enter two numbers: ";\n    cin >> num1 >> num2;\n    cout << "Enter operator (+, -, *, /): ";\n    cin >> op;\n    switch (op) {\n        case '+': cout << "Result: " << num1 + num2; break;\n        case '-': cout << "Result: " << num1 - num2; break;\n        case '*': cout << "Result: " << num1 * num2; break;\n        case '/': cout << (num2 != 0 ? num1 / num2 : 0); break;\n        default: cout << "Invalid operator!";\n    }\n    return 0;\n}''',

    "sum of digits": '''#include <iostream>\nusing namespace std;\nint main() {\n    int num, sum = 0;\n    cout << "Enter a number: ";\n    cin >> num;\n    while (num > 0) {\n        sum += num % 10;\n        num /= 10;\n    }\n    cout << "Sum of digits: " << sum;\n    return 0;\n}''',

    "count digits": '''#include <iostream>\nusing namespace std;\nint main() {\n    int num, count = 0;\n    cout << "Enter a number: ";\n    cin >> num;\n    while (num > 0) {\n        count++;\n        num /= 10;\n    }\n    cout << "Number of digits: " << count;\n    return 0;\n}''',

    "character check": '''#include <iostream>\nusing namespace std;\nint main() {\n    char ch;\n    cout << "Enter a character: ";\n    cin >> ch;\n    if (isalpha(ch))\n        cout << "Alphabet";\n    else if (isdigit(ch))\n        cout << "Digit";\n    else\n        cout << "Special Character";\n    return 0;\n}''',

    "power of number": '''#include <iostream>\n#include <cmath>\nusing namespace std;\nint main() {\n    double base, exp;\n    cout << "Enter base and exponent: ";\n    cin >> base >> exp;\n    cout << "Result: " << pow(base, exp);\n    return 0;\n}''',

    "temperature converter": '''#include <iostream>\nusing namespace std;\nint main() {\n    double celsius, fahrenheit;\n    cout << "Enter temperature in Celsius: ";\n    cin >> celsius;\n    fahrenheit = (celsius * 9/5) + 32;\n    cout << "Temperature in Fahrenheit: " << fahrenheit;\n    return 0;\n}''',

}

