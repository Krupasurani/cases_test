# src/ai_engine/enhanced_test_generator.py
import json
import re
from typing import Dict, List, Any, Optional, Tuple
import logging
from openai import OpenAI
import time

logger = logging.getLogger(__name__)

class EnhancedTestCaseGenerator:
    """AI-powered test case generation with PACS.008 field intelligence and Maker-Checker workflow"""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4.1-mini-2025-04-14"
        self.maker_checker_enabled = True
        
    def generate_test_cases(self, content: str, custom_instructions: str = "") -> List[Dict[str, Any]]:
        """Enhanced test case generation with maker-checker validation"""
        try:
            # Clean and prepare content
            cleaned_content = self._clean_content(content)
            
            # Check if content is PACS.008 related
            is_pacs008 = self._is_pacs008_content(cleaned_content)
            
            if is_pacs008 and self.maker_checker_enabled:
                logger.info("Detected PACS.008 content - using enhanced maker-checker workflow")
                return self._generate_pacs008_test_cases(cleaned_content, custom_instructions)
            else:
                logger.info("Using standard test case generation")
                return self._generate_standard_test_cases(cleaned_content, custom_instructions)
                
        except Exception as e:
            logger.error(f"Error in enhanced test generation: {str(e)}")
            return self._get_fallback_test_cases()
    
    def _is_pacs008_content(self, content: str) -> bool:
        """Detect if content is related to PACS.008"""
        pacs008_indicators = [
            "pacs.008", "pacs008", "FI to FI Customer Credit Transfer",
            "Debtor Agent", "Creditor Agent", "Interbank Settlement",
            "ISO 20022", "Business Application Header", "BAH",
            "Group Header", "Credit Transfer Transaction Information"
        ]
        
        content_lower = content.lower()
        indicators_found = sum(1 for indicator in pacs008_indicators 
                             if indicator.lower() in content_lower)
        
        return indicators_found >= 3
    
    def _generate_pacs008_test_cases(self, content: str, custom_instructions: str) -> List[Dict[str, Any]]:
        """Generate test cases using PACS.008 maker-checker workflow"""
        
        # Step 1: Extract PACS.008 fields from document
        logger.info("Extracting PACS.008 fields...")
        pacs_fields = self._extract_pacs008_fields(content)
        
        # Step 2: Run maker-checker validation
        logger.info("Running maker-checker validation...")
        maker_checker_results = self._run_maker_checker_validation(pacs_fields)
        
        # Step 3: Extract user stories and acceptance criteria
        logger.info("Extracting user stories...")
        user_stories = self._extract_user_stories_with_context(content, pacs_fields)
        
        # Step 4: Generate test cases based on validation results
        logger.info("Generating enhanced test cases...")
        test_cases = self._generate_tests_from_validation_results(
            user_stories, 
            pacs_fields, 
            maker_checker_results, 
            custom_instructions
        )
        
        return test_cases
    
    def _extract_pacs008_fields(self, content: str) -> Dict[str, Any]:
        """Extract PACS.008 fields from document content"""
        
        extraction_prompt = f"""
        You are a PACS.008 field extraction expert. Analyze this banking document and extract relevant pacs.008 message fields.

        Document Content: {content[:3000]}...

        Extract both explicit field values mentioned in the document AND create realistic example values for missing fields.

        Return the field data in this exact JSON format:
        {{
            "message_identification": "extracted or realistic example",
            "creation_date_time": "extracted or example ISO datetime",
            "number_of_transactions": "extracted or example number",
            "settlement_method": "extracted (INDA/INGA/CLRG.I/COVE) or example",
            "instructing_agent_bic": "extracted or example BIC (8 or 11 chars)",
            "instructed_agent_bic": "extracted or example BIC (8 or 11 chars)",
            "interbank_settlement_amount": "extracted or example amount",
            "settlement_currency": "extracted or example currency (USD/EUR/GBP)",
            "interbank_settlement_date": "extracted or example date",
            "instruction_identification": "extracted or example (max 16 chars)",
            "end_to_end_identification": "extracted or example",
            "uetr": "extracted or example UUID format",
            "debtor_agent_bic": "extracted or example BIC",
            "creditor_agent_bic": "extracted or example BIC", 
            "debtor_account": "extracted or example account",
            "creditor_account": "extracted or example account",
            "charge_bearer": "extracted (DEBT/CRED/SHAR/SLEV) or example",
            "remittance_information": "extracted or example"
        }}

        Use realistic banking data for examples (valid BIC formats, proper currencies, reasonable amounts).
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a PACS.008 field extraction expert. Return only valid JSON with no additional text."},
                    {"role": "user", "content": extraction_prompt}
                ],
                temperature=0.1,
                max_tokens=1200
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                extracted_fields = json.loads(json_match.group())
                logger.info(f"Successfully extracted {len(extracted_fields)} PACS.008 fields")
                return extracted_fields
            else:
                logger.warning("No JSON found in field extraction response")
                return self._get_example_pacs_fields()
                
        except Exception as e:
            logger.error(f"PACS.008 field extraction error: {str(e)}")
            return self._get_example_pacs_fields()
    
    def _run_maker_checker_validation(self, pacs_fields: Dict[str, Any]) -> Dict[str, Any]:
        """Run the complete maker-checker validation process"""
        
        # Step 1: Maker validation
        maker_results = self._run_maker_validation(pacs_fields)
        
        # Step 2: Checker validation
        checker_results = self._run_checker_validation(maker_results)
        
        return {
            "maker_validations": maker_results,
            "checker_response": checker_results,
            "original_fields": pacs_fields,
            "validation_summary": self._create_validation_summary(maker_results, checker_results)
        }
    
    def _run_maker_validation(self, pacs_fields: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Simulate Maker role validation using GPT's ISO 20022 knowledge"""
        
        maker_prompt = f"""
You are an expert ISO 20022 Validator acting as the MAKER role in a banking system.
You are validating a PACS.008 (FI to FI Customer Credit Transfer) message fields.

Use your knowledge of ISO 20022 standards to validate each field:

PACS.008 Message Fields:
{json.dumps(pacs_fields, indent=2)}

Perform comprehensive field-level validation:

1. FORMAT VALIDATION:
   - BIC codes: Must be 8 or 11 characters (e.g., DEUTDEFF or DEUTDEFFXXX)
   - Currency codes: Must be valid ISO 4217 (USD, EUR, GBP, etc.)
   - Amounts: Must be positive numbers with max 2 decimal places
   - Dates: Must be valid ISO date format
   - UUIDs: Must follow UUID v4 format

2. BUSINESS LOGIC VALIDATION:
   - Settlement amounts must be > 0
   - Settlement method codes must be valid (INDA, INGA, CLRG.I, COVE)
   - Charge bearer codes must be valid (DEBT, CRED, SHAR, SLEV)
   - Instruction ID max 16 characters

3. CONSISTENCY CHECKS:
   - Debtor and Creditor agents should not be same for external transfers
   - Currency consistency across amount fields
   - Date logical consistency

Return validation results as JSON array:
[
  {{
    "field_name": "exact field name",
    "field_value": "field value",
    "validation_status": "Valid|Invalid|Missing|Suspicious",
    "validation_reason": "specific technical reason",
    "error_code": "BFSI error code if invalid",
    "severity": "Critical|High|Medium|Low"
  }}
]

Focus only on ISO 20022 PACS.008 compliance. Be specific about validation failures.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an ISO 20022 MAKER validator. Return only valid JSON array with specific validation results."},
                    {"role": "user", "content": maker_prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Extract JSON array from response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                maker_validations = json.loads(json_match.group())
                logger.info(f"Maker validation completed for {len(maker_validations)} fields")
                return maker_validations
            else:
                logger.warning("No JSON array found in maker validation response")
                return []
                
        except Exception as e:
            logger.error(f"Maker validation error: {str(e)}")
            return []
    
    def _run_checker_validation(self, maker_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Simulate Checker role validation and approval process"""
        
        checker_prompt = f"""
You are an ISO 20022 CHECKER reviewing the MAKER's validation of a PACS.008 message.

Your responsibilities as Checker:
1. Review all Maker validations
2. Make business-level assessment
3. Decide on approval/rejection
4. Provide clear business reasoning

MAKER'S VALIDATION RESULTS:
{json.dumps(maker_results, indent=2)}

Based on the Maker's findings, perform Checker review:

1. RISK ASSESSMENT:
   - Count critical vs minor issues
   - Assess business impact of each issue
   - Determine if message is processable

2. BUSINESS DECISION:
   - Approve: No critical issues, minor issues acceptable
   - Reject: Critical issues present, cannot process
   - Hold: Needs additional review or clarification

3. AUDIT REQUIREMENTS:
   - Document decision reasoning
   - Provide specific feedback for rejected items
   - Suggest corrective actions

Return response in JSON format:
{{
  "overall_status": "Approved|Rejected|Hold|Review_Required",
  "decision_summary": "clear business explanation",
  "critical_issues_count": number,
  "approval_conditions": ["condition1", "condition2"],
  "checker_remarks": ["business remark 1", "business remark 2"],
  "recommended_actions": ["action1", "action2"],
  "business_risk_level": "Low|Medium|High|Critical",
  "processing_authorization": "Authorized|Not_Authorized|Conditional"
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an ISO 20022 CHECKER making business decisions. Return only valid JSON."},
                    {"role": "user", "content": checker_prompt}
                ],
                temperature=0.1,
                max_tokens=1500
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                checker_response = json.loads(json_match.group())
                logger.info(f"Checker validation completed: {checker_response.get('overall_status', 'Unknown')}")
                return checker_response
            else:
                logger.warning("No JSON found in checker validation response")
                return {"overall_status": "Error", "decision_summary": "Checker validation failed"}
                
        except Exception as e:
            logger.error(f"Checker validation error: {str(e)}")
            return {"overall_status": "Error", "decision_summary": f"Checker error: {str(e)}"}
    
    def _extract_user_stories_with_context(self, content: str, pacs_fields: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract user stories with PACS.008 context"""
        
        user_story_prompt = f"""
        Analyze this PACS.008 banking document and extract or infer User Stories with Acceptance Criteria.

        Document Content: {content[:2000]}...
        
        PACS.008 Fields Identified: {list(pacs_fields.keys())}

        Extract or create realistic User Stories that would lead to PACS.008 message processing tests.

        Return in JSON format:
        [
          {{
            "user_story_id": "US001",
            "user_story": "As a [role], I want [goal] so that [benefit]",
            "business_context": "how this relates to PACS.008 processing",
            "acceptance_criteria": [
              {{
                "ac_id": "AC001",
                "ac_description": "specific testable requirement",
                "pacs008_fields": ["relevant field names"],
                "validation_focus": "what should be validated",
                "test_scenarios": ["scenario1", "scenario2"]
              }}
            ]
          }}
        ]

        Focus on banking workflows like payment creation, validation, approval, processing.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a BFSI business analyst. Extract realistic user stories for PACS.008 workflows."},
                    {"role": "user", "content": user_story_prompt}
                ],
                temperature=0.2,
                max_tokens=2000
            )
            
            response_text = response.choices[0].message.content.strip()
            
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                user_stories = json.loads(json_match.group())
                logger.info(f"Extracted {len(user_stories)} user stories with PACS.008 context")
                return user_stories
            else:
                return self._get_default_user_stories()
                
        except Exception as e:
            logger.error(f"User story extraction error: {str(e)}")
            return self._get_default_user_stories()
    
    def _generate_tests_from_validation_results(self, user_stories: List[Dict[str, Any]], 
                                               pacs_fields: Dict[str, Any],
                                               validation_results: Dict[str, Any], 
                                               custom_instructions: str) -> List[Dict[str, Any]]:
        """Generate comprehensive test cases based on maker-checker validation results"""
        
        test_generation_prompt = f"""
You are an expert BFSI test engineer generating test cases for PACS.008 message processing with Maker-Checker workflow.

USER STORIES CONTEXT:
{json.dumps(user_stories, indent=2)}

PACS.008 FIELDS:
{json.dumps(pacs_fields, indent=2)}

MAKER VALIDATION RESULTS:
{json.dumps(validation_results.get('maker_validations', []), indent=2)}

CHECKER VALIDATION RESULTS:
{json.dumps(validation_results.get('checker_response', {}), indent=2)}

CUSTOM INSTRUCTIONS: {custom_instructions}

Generate comprehensive test cases covering:

1. MAKER WORKFLOW TESTS:
   - Field validation for each PACS.008 field
   - Format validation (BIC, IBAN, currency, amount)
   - Business rule validation
   - Error handling scenarios

2. CHECKER WORKFLOW TESTS:
   - Review and approval processes
   - Rejection scenarios with specific reasons
   - Business rule verification
   - Risk assessment validation

3. END-TO-END WORKFLOW TESTS:
   - Complete maker-checker-processing cycle
   - Integration testing scenarios
   - Error recovery workflows

4. FIELD-SPECIFIC TESTS:
   - Based on validation issues found by Maker/Checker
   - Boundary testing for amounts and dates
   - Format validation for each field type

Each test case must:
- Reference specific PACS.008 fields being tested
- Include realistic banking data (valid BICs, IBANs, amounts)
- Specify Maker or Checker role clearly
- Include expected validation messages
- Map to specific User Stories and Acceptance Criteria

Generate exactly 15 comprehensive test cases in this format:
[
  {{
    "User Story ID": "user_story_id from context",
    "Acceptance Criteria ID": "ac_id from context",
    "Scenario": "descriptive scenario name",
    "Test Case ID": "TC001",
    "Test Case Description": "specific description mentioning PACS.008 fields and roles",
    "Precondition": "system state and user role",
    "Steps": "detailed numbered steps with actual field names, values, and expected validations",
    "Expected Result": "specific validation outcome and business result",
    "Part of Regression": "Yes|No",
    "Priority": "High|Medium|Low",
    "Role_Focus": "Maker|Checker|End-to-End",
    "PACS008_Fields_Tested": ["field names"],
    "Validation_Type": "Format|Business_Rule|Workflow|Integration"
  }}
]
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert BFSI test engineer. Generate realistic, specific, executable test cases based on PACS.008 validation results."},
                    {"role": "user", "content": test_generation_prompt}
                ],
                temperature=0.2,
                max_tokens=4000
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Extract JSON array from response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                test_cases = json.loads(json_match.group())
                
                # Validate and enhance test cases
                validated_test_cases = self._validate_and_enhance_test_cases(test_cases)
                
                logger.info(f"Generated {len(validated_test_cases)} enhanced test cases")
                return validated_test_cases
            else:
                logger.warning("No JSON array found in test generation response")
                return self._get_fallback_test_cases()
                
        except Exception as e:
            logger.error(f"Test generation from validation results error: {str(e)}")
            return self._get_fallback_test_cases()
    
    def _generate_standard_test_cases(self, content: str, custom_instructions: str) -> List[Dict[str, Any]]:
        """Generate standard test cases for non-PACS.008 content"""
        
        # Extract user stories using existing logic
        user_stories = self._extract_user_stories(content)
        
        if not user_stories:
            user_stories = [{"id": "REQ001", "content": content[:2000]}]
        
        all_test_cases = []
        
        for story in user_stories:
            test_cases = self._generate_test_cases_for_story(story, custom_instructions)
            all_test_cases.extend(test_cases)
        
        return self._validate_and_enhance_test_cases(all_test_cases)
    
    # Helper methods and existing logic...
    def _clean_content(self, content: str) -> str:
        """Clean and normalize content for processing"""
        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'[^\w\s\-\.\,\:\;\(\)\[\]\"\'\/\@\#\$\%\&\*\+\=\<\>\?]', ' ', content)
        
        if len(content) > 8000:
            content = content[:8000] + "..."
        
        return content.strip()
    
    def _extract_user_stories(self, content: str) -> List[Dict[str, str]]:
        """Extract user stories from content (existing logic)"""
        user_stories = []
        
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
                if len(match.strip()) > 20:
                    user_stories.append({
                        "id": f"US{story_id:03d}",
                        "content": match.strip()
                    })
                    story_id += 1
        
        if not user_stories:
            sections = self._split_into_sections(content)
            for i, section in enumerate(sections, 1):
                if len(section.strip()) > 50:
                    user_stories.append({
                        "id": f"REQ{i:03d}",
                        "content": section.strip()
                    })
        
        return user_stories[:10]
    
    def _split_into_sections(self, content: str) -> List[str]:
        """Split content into logical sections"""
        header_split = re.split(r'\n(?=\d+\.|[A-Z][A-Z\s]+:|\#|\*)', content)
        if len(header_split) > 1:
            return header_split
        else:
            paragraphs = content.split('\n\n')
            return [p for p in paragraphs if len(p.strip()) > 100]
    
    def _generate_test_cases_for_story(self, story: Dict[str, str], custom_instructions: str) -> List[Dict[str, Any]]:
        """Generate test cases for a single user story (existing logic)"""
        
        num_cases = 8  # default
        if "exactly" in custom_instructions:
            match = re.search(r'exactly (\d+) test cases', custom_instructions)
            if match:
                num_cases = int(match.group(1))
        
        prompt = f"""
You are an expert BFSI test engineer. Generate test cases from the provided requirement.

User Story/Requirement: {story['content']}
Custom Instructions: {custom_instructions}

Generate EXACTLY {num_cases} test cases with these fields:
1. User Story ID: {story['id']}
2. Acceptance Criteria ID: Generate as AC001, AC002, etc.
3. Scenario: Brief scenario name
4. Test Case ID: Generate unique sequential IDs (TC001, TC002, etc.)
5. Test Case Description: Clear one-line description
6. Precondition: Prerequisites for test execution
7. Steps: Detailed numbered steps (use \\n for line breaks)
8. Expected Result: Clear expected outcome
9. Part of Regression: "Yes" for critical functionality, "No" for edge cases
10. Priority: "High" for happy path, "Medium" for validations, "Low" for edge cases

Include positive scenarios, negative scenarios, and edge cases.
Use realistic BFSI data (IBANs, amounts, dates, etc.)

Output as JSON array only.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert BFSI test engineer. Respond with ONLY valid JSON array."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=3000
            )
            
            response_text = response.choices[0].message.content.strip()
            
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return self._fallback_test_case_generation(story)
                
        except Exception as e:
            logger.error(f"Test case generation error: {str(e)}")
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
                    continue
                
                if len(validated_case["Steps"]) < 10:
                    continue
                
                # Ensure proper values
                if validated_case["Part of Regression"] not in ["Yes", "No"]:
                    validated_case["Part of Regression"] = "No"
                
                if validated_case["Priority"] not in ["High", "Medium", "Low"]:
                    validated_case["Priority"] = "Medium"
                
                # Add enhanced fields if present
                for extra_field in ["Role_Focus", "PACS008_Fields_Tested", "Validation_Type"]:
                    if extra_field in case:
                        validated_case[extra_field] = case[extra_field]
                
                validated_cases.append(validated_case)
                tc_counter += 1
                
                if tc_counter % 3 == 0:
                    ac_counter += 1
                    
            except Exception as e:
                logger.warning(f"Skipping invalid test case: {str(e)}")
                continue
        
        return validated_cases
    
    def _get_example_pacs_fields(self) -> Dict[str, Any]:
        """Fallback example PACS.008 fields"""
        return {
            "message_identification": "MSG20250803001",
            "creation_date_time": "2025-08-03T10:30:00Z",
            "number_of_transactions": "1",
            "settlement_method": "INDA",
            "instructing_agent_bic": "BANKAUAAXXX",
            "instructed_agent_bic": "BANKUSBBXXX",
            "interbank_settlement_amount": "565000.00",
            "settlement_currency": "USD",
            "interbank_settlement_date": "2025-08-03",
            "instruction_identification": "INSTR123456789012",
            "end_to_end_identification": "CORPORATIONXENDTOENDID",
            "uetr": "d0b7077f-49fb-42ed-b78d-af331c0e5012",
            "debtor_agent_bic": "BANKAUAAXXX",
            "creditor_agent_bic": "BANKGBCCXXX",
            "debtor_account": "123456789",
            "creditor_account": "GB11111111111111111111",
            "charge_bearer": "DEBT",
            "remittance_information": "Contract 123"
        }
    
    def _get_default_user_stories(self) -> List[Dict[str, Any]]:
        """Default user stories for PACS.008"""
        return [
            {
                "user_story_id": "US001",
                "user_story": "As a Bank Officer, I want to create valid PACS.008 messages so that interbank payments are processed correctly",
                "business_context": "PACS.008 message creation and validation for interbank transfers",
                "acceptance_criteria": [
                    {
                        "ac_id": "AC001",
                        "ac_description": "PACS.008 message must contain all mandatory fields with valid formats",
                        "pacs008_fields": ["message_identification", "instructing_agent_bic", "instructed_agent_bic"],
                        "validation_focus": "mandatory field presence and format validation",
                        "test_scenarios": ["valid creation", "missing field validation", "invalid format rejection"]
                    }
                ]
            },
            {
                "user_story_id": "US002",
                "user_story": "As a Checker, I want to review and approve PACS.008 messages so that only valid payments are processed",
                "business_context": "Maker-checker workflow for PACS.008 message approval",
                "acceptance_criteria": [
                    {
                        "ac_id": "AC002",
                        "ac_description": "Checker must validate business rules before approving PACS.008 messages",
                        "pacs008_fields": ["interbank_settlement_amount", "charge_bearer", "settlement_method"],
                        "validation_focus": "business rule validation and approval workflow",
                        "test_scenarios": ["approval process", "rejection with reasons", "business rule verification"]
                    }
                ]
            }
        ]
    
    def _get_fallback_test_cases(self) -> List[Dict[str, Any]]:
        """Fallback test cases when AI generation fails"""
        return [
            {
                "User Story ID": "US001",
                "Acceptance Criteria ID": "AC001",
                "Scenario": "PACS.008 Message Creation",
                "Test Case ID": "TC001",
                "Test Case Description": "Verify successful PACS.008 message creation with valid mandatory fields",
                "Precondition": "User logged in as Maker role with appropriate permissions",
                "Steps": "1. Navigate to PACS.008 message creation\n2. Enter Message ID: MSG20250803001\n3. Enter Instructing Agent BIC: BANKAUAAXXX\n4. Enter Instructed Agent BIC: BANKUSBBXXX\n5. Enter Settlement Amount: 100000.00 USD\n6. Submit for validation",
                "Expected Result": "PACS.008 message created successfully and submitted for checker approval",
                "Part of Regression": "Yes",
                "Priority": "High",
                "Role_Focus": "Maker",
                "PACS008_Fields_Tested": ["message_identification", "instructing_agent_bic", "instructed_agent_bic", "interbank_settlement_amount"],
                "Validation_Type": "Format"
            },
            {
                "User Story ID": "US001",
                "Acceptance Criteria ID": "AC001",
                "Scenario": "Invalid BIC Format Validation",
                "Test Case ID": "TC002",
                "Test Case Description": "Verify PACS.008 rejects invalid BIC format in Instructing Agent field",
                "Precondition": "User logged in as Maker role",
                "Steps": "1. Navigate to PACS.008 message creation\n2. Enter valid Message ID\n3. Enter invalid Instructing Agent BIC: INVALID123\n4. Enter valid Instructed Agent BIC\n5. Attempt to submit",
                "Expected Result": "Validation error displayed: 'Invalid BIC format for Instructing Agent'",
                "Part of Regression": "Yes",
                "Priority": "High",
                "Role_Focus": "Maker",
                "PACS008_Fields_Tested": ["instructing_agent_bic"],
                "Validation_Type": "Format"
            }
        ]
    
    def _fallback_test_case_generation(self, story: Dict[str, str]) -> List[Dict[str, Any]]:
        """Generate basic test cases when AI parsing fails"""
        return [
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
    
    def _create_validation_summary(self, maker_results: List[Dict[str, Any]], 
                                  checker_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of validation results"""
        
        # Count validation statuses from maker results
        status_counts = {}
        critical_issues = []
        
        for result in maker_results:
            status = result.get('validation_status', 'Unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
            
            if result.get('severity') == 'Critical':
                critical_issues.append(result.get('field_name', 'Unknown'))
        
        return {
            "total_fields_validated": len(maker_results),
            "validation_status_counts": status_counts,
            "critical_issues": critical_issues,
            "checker_decision": checker_results.get('overall_status', 'Unknown'),
            "business_risk_level": checker_results.get('business_risk_level', 'Unknown'),
            "processing_authorized": checker_results.get('processing_authorization', 'Unknown')
        }

# Example usage and integration
if __name__ == "__main__":
    # Test the enhanced generator
    generator = EnhancedTestCaseGenerator("your-openai-api-key")
    
    sample_pacs008_content = """
    PACS.008 FI to FI Customer Credit Transfer Message
    
    This message is used for interbank customer credit transfers.
    
    Key fields include:
    - Message Identification: Unique identifier for the message
    - Instructing Agent BIC: BIC of the sending bank
    - Instructed Agent BIC: BIC of the receiving bank
    - Interbank Settlement Amount: Amount to be transferred
    - Settlement Method: Method of settlement (INDA, INGA, etc.)
    - Charge Bearer: Who bears the charges (DEBT, CRED, SHAR, SLEV)
    
    Business Scenario:
    Corporation X needs to pay Corporation Y USD 565,000 through Bank A to Bank C via Bank B.
    """
    
    test_cases = generator.generate_test_cases(
        content=sample_pacs008_content,
        custom_instructions="Focus on maker-checker workflow and field validation"
    )
    
    print(f"Generated {len(test_cases)} test cases")
    for i, case in enumerate(test_cases[:3], 1):
        print(f"\nTest Case {i}:")
        print(f"Description: {case.get('Test Case Description', 'N/A')}")
        print(f"Role Focus: {case.get('Role_Focus', 'N/A')}")
        print(f"PACS.008 Fields: {case.get('PACS008_Fields_Tested', 'N/A')}")