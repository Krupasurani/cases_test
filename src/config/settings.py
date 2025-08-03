# config/settings.py
import os
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class Settings:
    # API Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Model preferences
    PRIMARY_MODEL: str = "gpt-4.1-mini-2025-04-14"
    FALLBACK_MODEL: str = "gpt-4o-mini"
    
    # File processing
    MAX_FILE_SIZE_MB: int = 50
    SUPPORTED_FORMATS: List[str] = [
        '.docx', '.pdf', '.xlsx', '.png', '.jpg', '.jpeg', 
        '.txt', '.eml', '.json', '.xml', '.csv'
    ]
    
    # Output configuration
    OUTPUT_FIELDS: List[str] = [
        "User Story ID",
        "Acceptance Criteria ID", 
        "Scenario",
        "Test Case ID",
        "Test Case Description",
        "Precondition",
        "Steps",
        "Expected Result",
        "Part of Regression",
        "Priority"
    ]
    
    # OCR settings
    OCR_LANGUAGES: List[str] = ['eng']
    OCR_CONFIG: str = '--oem 3 --psm 6'
    
    # AI generation settings
    MIN_TEST_CASES_PER_STORY: int = 5
    MAX_TEST_CASES_PER_STORY: int = 15
    INCLUDE_EDGE_CASES: bool = True
    
    # Security
    TEMP_FILE_CLEANUP: bool = True
    LOG_SENSITIVE_DATA: bool = False

# Prompts for test case generation
TEST_CASE_GENERATION_PROMPT = """
You are an expert BFSI (Banking, Financial Services, Insurance) test engineer. 
Generate comprehensive test cases from the provided requirements.

Requirements/User Stories:
{requirements}

Generate test cases with these exact fields:
1. User Story ID: Extract or generate (US001, US002, etc.)
2. Acceptance Criteria ID: Extract from inputs 
3. Scenario: Brief scenario description
4. Test Case ID: Generate unique ID (TC001, TC002, etc.)
5. Test Case Description: Clear, concise description
6. Precondition: What must be true before test execution
7. Steps: Detailed step-by-step test execution (numbered)
8. Expected Result: Clear expected outcome
9. Part of Regression: Yes/No based on criticality
10. Priority: High/Medium/Low

Requirements:
- Generate 8-12 test cases per user story
- Include positive, negative, and edge cases
- Focus on BFSI domain scenarios (payments, authentication, compliance)
- Use realistic banking data examples with variety:
  * IBANs: DE89370400440532013000, GB33BUKB20201555555555, FR1420041010050500013M02606
  * BICs: DEUTDEFF, CHASUS33, BNPAFRPP, SBININBB
  * Amounts: 0.01, 100.50, 1000.00, 9999.99, 50000.00, 999999.99
  * Currencies: EUR, USD, GBP, CHF, JPY
  * Dates: Future dates, past dates, weekends, holidays
- Ensure each test case is independent and executable
- Include boundary testing (min/max amounts, field lengths)
- Cover security scenarios (authentication, authorization)
- Include performance considerations for high-volume scenarios

Output as JSON array with each test case as an object.
"""

VALIDATION_PROMPT = """
Review these generated test cases for:
1. Completeness of all required fields
2. BFSI domain accuracy
3. Test case independence
4. Realistic test data
5. Edge case coverage

Test Cases:
{test_cases}

Provide feedback and corrections if needed.
"""