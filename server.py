from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os
import uuid
import tempfile

app = Flask(__name__)
CORS(app)

# Directory for temporary code execution
CODE_DIR = "submissions"
os.makedirs(CODE_DIR, exist_ok=True)

# Test cases for the "Eid Sweet Parity" problem
# Format: (input, expected_output)
TEST_CASES = [
    ("4\n", "Even\n"),
    ("7\n", "Odd\n"),
    ("10\n", "Even\n"),
    ("15\n", "Odd\n"),
    ("1000000000000000000\n", "Even\n")
]

def run_python(code, test_cases):
    # Write the user's code to a temporary file
    temp_file = f"{CODE_DIR}/{uuid.uuid4()}.py"
    with open(temp_file, "w") as f:
        f.write(code)

    results = []
    all_passed = True

    for i, (test_input, expected_output) in enumerate(test_cases, 1):
        status = {}
        try:
            # Run the Python code with the test case input
            process = subprocess.run(
                ["python3", temp_file],
                input=test_input,
                text=True,
                capture_output=True,
                timeout=3
            )
            output = process.stdout.strip() + "\n"
            expected_output = expected_output.strip() + "\n"

            if process.returncode != 0:
                status = {"test_case": i, "status": "Runtime Error", "error": process.stderr}
                all_passed = False
            elif output != expected_output:
                status = {"test_case": i, "status": "Wrong Answer"}
                all_passed = False
            else:
                status = {"test_case": i, "status": "Passed"}

        except subprocess.TimeoutExpired:
            status = {"test_case": i, "status": "Time Limit Exceeded"}
            all_passed = False
        except Exception as e:
            status = {"test_case": i, "status": "Error", "error": str(e)}
            all_passed = False

        results.append(status)

    os.remove(temp_file)
    return {"success": all_passed, "results": results}

def run_cpp(code, test_cases):
    # Write the user's code to a temporary file
    base_name = f"{CODE_DIR}/{uuid.uuid4()}"
    cpp_file = f"{base_name}.cpp"
    exe_file = f"{base_name}.out"

    with open(cpp_file, "w") as f:
        f.write(code)

    # Compile the C++ code
    try:
        compile_result = subprocess.run(
            ["g++", cpp_file, "-o", exe_file],
            text=True,
            capture_output=True,
            timeout=5
        )
        if compile_result.returncode != 0:
            os.remove(cpp_file)
            return {"success": False, "results": [{"test_case": 0, "status": "Compilation Error", "error": compile_result.stderr}]}
    except Exception as e:
        os.remove(cpp_file)
        return {"success": False, "results": [{"test_case": 0, "status": "Compilation Error", "error": str(e)}]}

    results = []
    all_passed = True

    for i, (test_input, expected_output) in enumerate(test_cases, 1):
        status = {}
        try:
            # Run the compiled C++ program with the test case input
            process = subprocess.run(
                [exe_file],
                input=test_input,
                text=True,
                capture_output=True,
                timeout=3
            )
            output = process.stdout.strip() + "\n"
            expected_output = expected_output.strip() + "\n"

            if process.returncode != 0:
                status = {"test_case": i, "status": "Runtime Error", "error": process.stderr}
                all_passed = False
            elif output != expected_output:
                status = {"test_case": i, "status": "Wrong Answer"}
                all_passed = False
            else:
                status = {"test_case": i, "status": "Passed"}

        except subprocess.TimeoutExpired:
            status = {"test_case": i, "status": "Time Limit Exceeded"}
            all_passed = False
        except Exception as e:
            status = {"test_case": i, "status": "Error", "error": str(e)}
            all_passed = False

        results.append(status)

    os.remove(cpp_file)
    os.remove(exe_file)
    return {"success": all_passed, "results": results}

@app.route('/submit', methods=['POST'])
def submit_code():
    data = request.json
    code = data.get("code")
    language = data.get("language")

    if not code or not language:
        return jsonify({"success": False, "results": [{"test_case": 0, "status": "Error", "error": "Code or language missing"}]})

    if language == "python":
        result = run_python(code, TEST_CASES)
    elif language == "cpp":
        result = run_cpp(code, TEST_CASES)
    else:
        return jsonify({"success": False, "results": [{"test_case": 0, "status": "Error", "error": "Unsupported language"}]})

    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)