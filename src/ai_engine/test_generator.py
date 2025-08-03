# src/ai_engine/test_generator.py
import json
import re
from typing import Dict, List, Any, Optional
import logging
from openai import OpenAI
import time

logger = logging.getLogger(__name__)

class TestCaseGenerator:
    """AI-powered test case generation using GPT-4o-mini"""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4.1-mini-2025-04-14"
        
    def generate_test_cases(self, content: str, custom_instructions: str = "") -> List[Dict[str, Any]]:
        """Generate comprehensive test cases from document content"""
        try:
            # Clean and prepare content
            cleaned_content = self._clean_content(content)
            
            # Extract user stories and acceptance criteria
            user_stories = self._extract_user_stories(cleaned_content)
            
            if not user_stories:
                # If no formal user stories found, treat entire content as requirements
                user_stories = [{"id": "REQ001", "content": cleaned_content[:2000]}]
            
            all_test_cases = []
            
            for story in user_stories:
                test_cases = self._generate_test_cases_for_story(story, custom_instructions)
                all_test_cases.extend(test_cases)
            
            # Post-process and validate
            validated_test_cases = self._validate_and_enhance_test_cases(all_test_cases)
            
            return validated_test_cases
            
        except Exception as e:
            logger.error(f"Error generating test cases: {str(e)}")
    def _repair_json_response(self, response_text: str) -> str:
        """Attempt to repair malformed JSON response"""
        try:
            # Remove any text before the first [
            start_idx = response_text.find('[')
            if start_idx == -1:
                return ""
            
            # Remove any text after the last ]
            end_idx = response_text.rfind(']')
            if end_idx == -1:
                return ""
            
            json_str = response_text[start_idx:end_idx + 1]
            
            # Fix common JSON issues
            # Replace single quotes with double quotes
            json_str = json_str.replace("'", '"')
            
            # Fix unescaped newlines in strings
            json_str = re.sub(r'(?<!\\)\\n', '\\\\n', json_str)
            
            # Remove trailing commas
            json_str = re.sub(r',\s*}', '}', json_str)
            json_str = re.sub(r',\s*]', ']', json_str)
            
            return json_str
            
        except Exception as e:
            logger.error(f"JSON repair failed: {str(e)}")
            return ""
    
    def _fallback_test_case_generation(self, story: Dict[str, str]) -> List[Dict[str, Any]]:
        """Generate basic test cases when AI parsing fails"""
        logger.info("Generating fallback test cases")
        
        fallback_cases = [
            {
                "User Story ID": story['id'],
                "Acceptance Criteria ID": "AC001",
                "Scenario": "Valid Input Processing",
                "Test Case ID": "TC001",
                "Test Case Description": f"Verify successful processing for {story['id']}",
                "Precondition": "System is available and user is authenticated",
                "Steps": "1. Input valid data\n2. Submit request\n3. Verify processing",
                "Expected Result": "Request processed successfully",
                "Part of Regression": "Yes",
                "Priority": "High"
            },
            {
                "User Story ID": story['id'],
                "Acceptance Criteria ID": "AC002", 
                "Scenario": "Invalid Input Handling",
                "Test Case ID": "TC002",
                "Test Case Description": f"Verify error handling for {story['id']}",
                "Precondition": "System is available",
                "Steps": "1. Input invalid data\n2. Submit request\n3. Verify error message",
                "Expected Result": "Appropriate error message displayed",
                "Part of Regression": "No",
                "Priority": "Medium"
            }
        ]
        
        return fallback_cases
    
    def _clean_content(self, content: str) -> str:
        """Clean and normalize content for processing"""
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove special characters that might interfere
        content = re.sub(r'[^\w\s\-\.\,\:\;\(\)\[\]\"\'\/\@\#\$\%\&\*\+\=\<\>\?]', ' ', content)
        
        # Limit content length to avoid token limits
        if len(content) > 8000:
            content = content[:8000] + "..."
        
        return content.strip()
    
    def _extract_user_stories(self, content: str) -> List[Dict[str, str]]:
        """Extract user stories and acceptance criteria from content"""
        user_stories = []
        
        # Pattern for formal user stories
        story_patterns = [
            r'(?:As\s+(?:a|an)\s+.+?I\s+want\s+.+?(?:so\s+that|in\s+order\s+to).+?)(?=As\s+(?:a|an)|$)',
            r'(?:User\s+Story\s*:?\s*.+?)(?=User\s+Story|$)',
            r'(?:Given\s+.+?When\s+.+?Then\s+.+?)(?=Given|$)',
            r'(?:Scenario\s*:?\s*.+?)(?=Scenario|$)'
        ]
        
        story_id = 1
        for pattern in story_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                if len(match.strip()) > 20:  # Filter out very short matches
                    user_stories.append({
                        "id": f"US{story_id:03d}",
                        "content": match.strip()
                    })
                    story_id += 1
        
        # If no formal stories found, look for sections or paragraphs
        if not user_stories:
            sections = self._split_into_sections(content)
            for i, section in enumerate(sections, 1):
                if len(section.strip()) > 50:
                    user_stories.append({
                        "id": f"REQ{i:03d}",
                        "content": section.strip()
                    })
        
        return user_stories[:10]  # Limit to prevent excessive API calls
    
    def _split_into_sections(self, content: str) -> List[str]:
        """Split content into logical sections"""
        # Try different splitting strategies
        sections = []
        
        # Split by headers or numbered items
        header_split = re.split(r'\n(?=\d+\.|[A-Z][A-Z\s]+:|\#|\*)', content)
        if len(header_split) > 1:
            sections = header_split
        else:
            # Split by paragraphs
            paragraphs = content.split('\n\n')
            sections = [p for p in paragraphs if len(p.strip()) > 100]
        
        return sections
    
    def _generate_test_cases_for_story(self, story: Dict[str, str], custom_instructions: str) -> List[Dict[str, Any]]:
        """Generate test cases for a single user story"""
        
    def _generate_test_cases_for_story(self, story: Dict[str, str], custom_instructions: str) -> List[Dict[str, Any]]:
        """Generate test cases for a single user story"""
        
        # Extract the exact number from instructions
        num_cases = 8  # default
        if "exactly" in custom_instructions:
            import re
            match = re.search(r'exactly (\d+) test cases', custom_instructions)
            if match:
                num_cases = int(match.group(1))
        
        prompt = f"""
You are an expert BFSI (Banking, Financial Services, Insurance) test engineer. 
Generate comprehensive test cases from the provided user story/requirement.

User Story/Requirement:
{story['content']}

Custom Instructions: {custom_instructions}

IMPORTANT: You must respond with ONLY a valid JSON array. No explanations, no markdown, no code blocks.

Generate EXACTLY {num_cases} test cases with these EXACT fields:
1. User Story ID: {story['id']}
2. Acceptance Criteria ID: Generate as AC001, AC002, etc.
3. Scenario: Brief scenario name (e.g., "Valid Payment Processing", "Invalid Amount Entry")
4. Test Case ID: Generate unique sequential IDs (TC001, TC002, etc.)
5. Test Case Description: Clear one-line description
6. Precondition: Prerequisites for test execution
7. Steps: Detailed numbered steps (use \\n for line breaks)
8. Expected Result: Clear expected outcome
9. Part of Regression: "Yes" for critical functionality, "No" for edge cases
10. Priority: "High" for happy path, "Medium" for validations, "Low" for edge cases

REQUIREMENTS:
- Include positive scenarios (happy path)
- Include negative scenarios (error conditions)
- Include edge cases and boundary conditions
- Use realistic BFSI data (IBANs, amounts, dates, etc.)
- Each test case must be independent and executable
- Steps should be detailed and unambiguous

Output format (respond with ONLY this JSON, nothing else):
[
  {{
    "User Story ID": "{story['id']}",
    "Acceptance Criteria ID": "AC001",
    "Scenario": "Valid Payment Processing",
    "Test Case ID": "TC001",
    "Test Case Description": "Verify successful payment processing with valid inputs",
    "Precondition": "User is logged in and has sufficient balance",
    "Steps": "1. Navigate to payment page\\n2. Enter amount: 1000.00\\n3. Enter beneficiary IBAN: DE89370400440532013000\\n4. Click Submit\\n5. Confirm payment",
    "Expected Result": "Payment processed successfully, confirmation displayed",
    "Part of Regression": "Yes",
    "Priority": "High"
  }}
]
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert BFSI test engineer. You MUST respond with ONLY valid JSON array format. No explanations, no markdown, no code blocks. Just pure JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Lower temperature for more consistent JSON output
                max_tokens=3000   # Increased for more comprehensive test cases
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Log the response for debugging
            logger.info(f"AI Response length: {len(response_text)}")
            logger.info(f"AI Response preview: {response_text[:200]}...")
            
            # Try multiple JSON extraction methods
            test_cases = []
            
            # Method 1: Look for JSON array
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                try:
                    test_cases = json.loads(json_match.group())
                    logger.info(f"Successfully parsed {len(test_cases)} test cases using Method 1")
                except json.JSONDecodeError as e:
                    logger.warning(f"Method 1 JSON decode failed: {str(e)}")
            
            # Method 2: Look for JSON between code blocks
            if not test_cases:
                code_block_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', response_text, re.DOTALL)
                if code_block_match:
                    try:
                        test_cases = json.loads(code_block_match.group(1))
                        logger.info(f"Successfully parsed {len(test_cases)} test cases using Method 2")
                    except json.JSONDecodeError as e:
                        logger.warning(f"Method 2 JSON decode failed: {str(e)}")
            
            # Method 3: Extract individual JSON objects
            if not test_cases:
                object_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
                json_objects = re.findall(object_pattern, response_text, re.DOTALL)
                for obj_str in json_objects:
                    try:
                        obj = json.loads(obj_str)
                        if 'Test Case ID' in obj or 'Test Case Description' in obj:
                            test_cases.append(obj)
                    except json.JSONDecodeError:
                        continue
                
                if test_cases:
                    logger.info(f"Successfully parsed {len(test_cases)} test cases using Method 3")
            
            # Method 4: If still no success, try to repair the JSON
            if not test_cases:
                logger.warning("All JSON extraction methods failed. Attempting to repair JSON...")
                repaired_json = self._repair_json_response(response_text)
                if repaired_json:
                    try:
                        test_cases = json.loads(repaired_json)
                        logger.info(f"Successfully parsed {len(test_cases)} test cases using JSON repair")
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON repair also failed: {str(e)}")
            
            if test_cases:
                return test_cases
            else:
                logger.error("All JSON extraction methods failed")
                logger.error(f"Full response: {response_text}")
                # Return fallback test cases instead of empty list
                return self._fallback_test_case_generation(story)
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            return self._fallback_test_case_generation(story)
        except Exception as e:
            logger.error(f"API call error: {str(e)}")
            return self._fallback_test_case_generation(story)
    
    def _validate_and_enhance_test_cases(self, test_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and enhance generated test cases"""
        validated_cases = []
        required_fields = [
            "User Story ID", "Acceptance Criteria ID", "Scenario", "Test Case ID",
            "Test Case Description", "Precondition", "Steps", "Expected Result",
            "Part of Regression", "Priority"
        ]
        
        tc_counter = 1
        ac_counter = 1
        
        for case in test_cases:
            try:
                # Ensure all required fields exist
                validated_case = {}
                for field in required_fields:
                    validated_case[field] = case.get(field, "").strip()
                
                # Auto-generate missing IDs
                if not validated_case["Test Case ID"]:
                    validated_case["Test Case ID"] = f"TC{tc_counter:03d}"
                
                if not validated_case["Acceptance Criteria ID"]:
                    validated_case["Acceptance Criteria ID"] = f"AC{ac_counter:03d}"
                
                # Validate critical fields
                if len(validated_case["Test Case Description"]) < 10:
                    continue  # Skip incomplete test cases
                
                if len(validated_case["Steps"]) < 10:
                    continue  # Skip test cases without proper steps
                
                # Ensure proper values for regression and priority
                if validated_case["Part of Regression"] not in ["Yes", "No"]:
                    validated_case["Part of Regression"] = "No"
                
                if validated_case["Priority"] not in ["High", "Medium", "Low"]:
                    validated_case["Priority"] = "Medium"
                
                validated_cases.append(validated_case)
                tc_counter += 1
                
                # Update AC counter for unique acceptance criteria
                if tc_counter % 3 == 0:  # Group every 3 test cases under same AC
                    ac_counter += 1
                    
            except Exception as e:
                logger.warning(f"Skipping invalid test case: {str(e)}")
                continue
        
        return validated_cases
    
    def enhance_with_custom_instructions(self, test_cases: List[Dict[str, Any]], instructions: str) -> List[Dict[str, Any]]:
        """Enhance test cases based on custom instructions"""
        if not instructions or not test_cases:
            return test_cases
        
        enhancement_prompt = f"""
Based on these custom instructions: "{instructions}"
Modify the following test cases accordingly.

Current test cases:
{json.dumps(test_cases[:5], indent=2)}  # Limit for token efficiency

Instructions could be:
- "create more negative cases" -> Add more error scenarios
- "cover only basic scenarios" -> Remove edge cases
- "create optimized test cases" -> Reduce redundancy
- "write four test per acceptance criteria" -> Adjust test count

Return the modified test cases as JSON array.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a test optimization expert. Always respond with valid JSON."},
                    {"role": "user", "content": enhancement_prompt}
                ],
                temperature=0.2,
                max_tokens=1500
            )
            
            response_text = response.choices[0].message.content.strip()
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            
            if json_match:
                enhanced_cases = json.loads(json_match.group())
                return enhanced_cases
            else:
                return test_cases  # Return original if enhancement fails
                
        except Exception as e:
            logger.error(f"Enhancement error: {str(e)}")
            return test_cases

# Usage example
if __name__ == "__main__":
    generator = TestCaseGenerator("your-openai-api-key")
    
    sample_content = """
    User Story: As a bank customer, I want to transfer money to another account 
    so that I can pay my bills online.
    
    Acceptance Criteria:
    - User must be authenticated
    - Transfer amount must be positive
    - Recipient account must be valid
    - User must have sufficient balance
    """
    
    test_cases = generator.generate_test_cases(sample_content)
    print(f"Generated {len(test_cases)} test cases")
    for case in test_cases[:2]:
        print(json.dumps(case, indent=2))