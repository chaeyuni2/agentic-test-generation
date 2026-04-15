# Automated Test Generation PoC

## Overview

This project demonstrates an automated testing pipeline:

- Detect code changes (git diff)
- Extract modified Java methods
- Generate test scenarios using LLM
- Convert scenarios into pytest code
- Execute tests against a mock API

## Flow

Java code change  
→ LLM test generation  
→ pytest creation  
→ API testing  

## Structure

- poc_test_gen/: core logic
- sample_repo/: demo project and mock server

## Run

```bash
python extract_diff.py
python generate_tests.py
python generate_pytest_from_json.py
pytest outputs/generated_pytests
