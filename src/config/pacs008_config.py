# src/config/pacs008_config.py
"""
PACS.008 Field Definitions and Validation Rules
Based on ISO 20022 standard and BNY Mellon documentation
"""

from typing import Dict, List, Any
from enum import Enum

class FieldStatus(Enum):
    MANDATORY = "mandatory"
    OPTIONAL = "optional"
    CONDITIONAL = "conditional"

class ValidationSeverity(Enum):
    CRITICAL = "Critical"
    HIGH = "High" 
    MEDIUM = "Medium"
    LOW = "Low"

# PACS.008 Field Definitions
PACS008_FIELD_DEFINITIONS = {
    # Group Header Fields
    "message_identification": {
        "path": "GrpHdr/MsgId",
        "name": "Message Identification",
        "status": FieldStatus.MANDATORY,
        "data_type": "string",
        "max_length": 35,
        "description": "Point-to-point reference for message identification",
        "validation_rules": [
            "Must be unique per sender",
            "Maximum 35 characters",
            "No special characters except dash and underscore"
        ],
        "test_scenarios": [
            "valid_format", "max_length_boundary", "invalid_characters", "duplicate_id"
        ]
    },
    
    "creation_date_time": {
        "path": "GrpHdr/CreDtTm", 
        "name": "Creation Date Time",
        "status": FieldStatus.MANDATORY,
        "data_type": "datetime",
        "format": "ISO_8601",
        "description": "Date and time when message was created",
        "validation_rules": [
            "Must be valid ISO 8601 format",
            "Cannot be future date beyond 1 day",
            "Cannot be older than 30 days"
        ],
        "test_scenarios": [
            "valid_datetime", "invalid_format", "future_date", "old_date"
        ]
    },
    
    "number_of_transactions": {
        "path": "GrpHdr/NbOfTxs",
        "name": "Number of Transactions", 
        "status": FieldStatus.MANDATORY,
        "data_type": "integer",
        "min_value": 1,
        "max_value": 9999,
        "description": "Number of transactions in the message",
        "validation_rules": [
            "Must be positive integer",
            "Fixed to 1 for CBPR+ usage",
            "Maximum 9999 transactions"
        ],
        "test_scenarios": [
            "valid_count", "zero_count", "negative_count", "exceeds_maximum"
        ]
    },
    
    "settlement_method": {
        "path": "GrpHdr/SttlmInf/SttlmMtd",
        "name": "Settlement Method",
        "status": FieldStatus.MANDATORY,
        "data_type": "code",
        "allowed_values": ["INDA", "INGA", "CLRG", "COVE"],
        "description": "Method of settlement between financial institutions",
        "validation_rules": [
            "Must be one of: INDA, INGA, CLRG, COVE",
            "INDA: Settlement account maintained by Instructed Agent",
            "INGA: Settlement account maintained by Instructing Agent",
            "CLRG: Cleared through clearing system",
            "COVE: Cover method"
        ],
        "test_scenarios": [
            "valid_inda", "valid_inga", "valid_clrg", "valid_cove", "invalid_code"
        ]
    },
    
    # Agent Fields
    "instructing_agent_bic": {
        "path": "InstgAgt/FinInstnId/BICFI",
        "name": "Instructing Agent BIC",
        "status": FieldStatus.MANDATORY,
        "data_type": "string",
        "length": [8, 11],
        "description": "BIC of the instructing financial institution",
        "validation_rules": [
            "Must be 8 or 11 characters",
            "Format: 4 chars bank code + 2 chars country + 2 chars location + 3 optional chars",
            "Must be valid registered BIC",
            "Country code must be valid ISO 3166"
        ],
        "test_scenarios": [
            "valid_8_char_bic", "valid_11_char_bic", "invalid_length", "invalid_format", "invalid_country"
        ]
    },
    
    "instructed_agent_bic": {
        "path": "InstdAgt/FinInstnId/BICFI", 
        "name": "Instructed Agent BIC",
        "status": FieldStatus.MANDATORY,
        "data_type": "string",
        "length": [8, 11],
        "description": "BIC of the instructed financial institution",
        "validation_rules": [
            "Must be 8 or 11 characters",
            "Format: 4 chars bank code + 2 chars country + 2 chars location + 3 optional chars",
            "Must be valid registered BIC",
            "Should not be same as Instructing Agent BIC for external transfers"
        ],
        "test_scenarios": [
            "valid_different_bic", "same_as_instructing", "invalid_format", "unregistered_bic"
        ]
    },
    
    "debtor_agent_bic": {
        "path": "DbtrAgt/FinInstnId/BICFI",
        "name": "Debtor Agent BIC", 
        "status": FieldStatus.MANDATORY,
        "data_type": "string",
        "length": [8, 11],
        "description": "BIC of the debtor's financial institution",
        "validation_rules": [
            "Must be 8 or 11 characters",
            "Usually same as Instructing Agent BIC",
            "Must be valid registered BIC"
        ],
        "test_scenarios": [
            "matches_instructing_agent", "valid_different_bic", "invalid_bic_format"
        ]
    },
    
    "creditor_agent_bic": {
        "path": "CdtrAgt/FinInstnId/BICFI",
        "name": "Creditor Agent BIC",
        "status": FieldStatus.MANDATORY, 
        "data_type": "string",
        "length": [8, 11],
        "description": "BIC of the creditor's financial institution",
        "validation_rules": [
            "Must be 8 or 11 characters",
            "Usually same as Instructed Agent BIC",
            "Must be valid registered BIC"
        ],
        "test_scenarios": [
            "matches_instructed_agent", "valid_different_bic", "invalid_bic_format"
        ]
    },
    
    # Amount Fields
    "interbank_settlement_amount": {
        "path": "IntrBkSttlmAmt",
        "name": "Interbank Settlement Amount",
        "status": FieldStatus.MANDATORY,
        "data_type": "decimal",
        "currency_required": True,
        "min_value": 0.01,
        "max_decimal_places": 2,
        "description": "Amount to be settled between financial institutions",
        "validation_rules": [
            "Must be greater than 0",
            "Maximum 2 decimal places",
            "Currency must be valid ISO 4217 code",
            "Amount format: up to 18 digits before decimal"
        ],
        "test_scenarios": [
            "valid_amount_usd", "valid_amount_eur", "zero_amount", "negative_amount", 
            "invalid_currency", "too_many_decimals", "exceeds_maximum"
        ]
    },
    
    "settlement_currency": {
        "path": "IntrBkSttlmAmt/@Ccy",
        "name": "Settlement Currency",
        "status": FieldStatus.MANDATORY,
        "data_type": "string",
        "length": 3,
        "description": "Currency code for settlement amount",
        "validation_rules": [
            "Must be valid ISO 4217 currency code",
            "Exactly 3 characters",
            "Must be uppercase"
        ],
        "test_scenarios": [
            "valid_usd", "valid_eur", "valid_gbp", "invalid_code", "lowercase", "wrong_length"
        ]
    },
    
    "interbank_settlement_date": {
        "path": "IntrBkSttlmDt",
        "name": "Interbank Settlement Date",
        "status": FieldStatus.MANDATORY,
        "data_type": "date",
        "format": "YYYY-MM-DD",
        "description": "Date when settlement should occur",
        "validation_rules": [
            "Must be valid date format YYYY-MM-DD",
            "Cannot be past date (except same day)",
            "Should be business day",
            "Cannot be more than 365 days in future"
        ],
        "test_scenarios": [
            "today_date", "future_business_day", "past_date", "weekend_date", 
            "invalid_format", "too_far_future"
        ]
    },
    
    # Identification Fields
    "instruction_identification": {
        "path": "InstrId",
        "name": "Instruction Identification",
        "status": FieldStatus.OPTIONAL,
        "data_type": "string",
        "max_length": 16,
        "description": "Point-to-point reference for the instruction",
        "validation_rules": [
            "Maximum 16 characters for CBPR+ compatibility",
            "Should be unique per instructing agent",
            "No special characters except dash and underscore"
        ],
        "test_scenarios": [
            "valid_16_chars", "exceeds_16_chars", "unique_reference", "special_characters"
        ]
    },
    
    "end_to_end_identification": {
        "path": "EndToEndId",
        "name": "End to End Identification", 
        "status": FieldStatus.OPTIONAL,
        "data_type": "string",
        "max_length": 35,
        "description": "End-to-end reference provided by debtor",
        "validation_rules": [
            "Maximum 35 characters",
            "Must be passed unchanged through payment chain",
            "Provided by originating party"
        ],
        "test_scenarios": [
            "valid_reference", "max_length", "special_characters", "unchanged_propagation"
        ]
    },
    
    "uetr": {
        "path": "UETR",
        "name": "Unique End-to-end Transaction Reference",
        "status": FieldStatus.MANDATORY,
        "data_type": "string",
        "format": "UUID_v4",
        "length": 36,
        "description": "Unique transaction reference using UUID v4 format",
        "validation_rules": [
            "Must be valid UUID v4 format",
            "Exactly 36 characters including hyphens",
            "Must be globally unique",
            "Format: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx"
        ],
        "test_scenarios": [
            "valid_uuid_v4", "invalid_format", "wrong_length", "non_v4_uuid", "duplicate_uuid"
        ]
    },
    
    # Account Fields
    "debtor_account": {
        "path": "DbtrAcct/Id",
        "name": "Debtor Account",
        "status": FieldStatus.OPTIONAL,
        "data_type": "string",
        "formats": ["IBAN", "BBAN", "Other"],
        "description": "Account identification of the debtor",
        "validation_rules": [
            "Can be IBAN, BBAN, or other account format",
            "IBAN must pass check digit validation",
            "Format depends on account scheme"
        ],
        "test_scenarios": [
            "valid_iban", "valid_bban", "invalid_iban_checksum", "wrong_format"
        ]
    },
    
    "creditor_account": {
        "path": "CdtrAcct/Id", 
        "name": "Creditor Account",
        "status": FieldStatus.OPTIONAL,
        "data_type": "string",
        "formats": ["IBAN", "BBAN", "Other"],
        "description": "Account identification of the creditor",
        "validation_rules": [
            "Can be IBAN, BBAN, or other account format", 
            "IBAN must pass check digit validation",
            "Should not be same as debtor account for external transfers"
        ],
        "test_scenarios": [
            "valid_iban", "different_from_debtor", "invalid_iban", "same_as_debtor"
        ]
    },
    
    # Charge Information
    "charge_bearer": {
        "path": "ChrgBr",
        "name": "Charge Bearer",
        "status": FieldStatus.OPTIONAL,
        "data_type": "code",
        "allowed_values": ["DEBT", "CRED", "SHAR", "SLEV"],
        "description": "Specifies which party bears the charges",
        "validation_rules": [
            "Must be one of: DEBT, CRED, SHAR, SLEV",
            "DEBT: Charges borne by debtor",
            "CRED: Charges borne by creditor", 
            "SHAR: Charges shared",
            "SLEV: Service level charges"
        ],
        "test_scenarios": [
            "debt_charges", "cred_charges", "shared_charges", "slev_charges", "invalid_code"
        ]
    },
    
    # Remittance Information
    "remittance_information": {
        "path": "RmtInf/Ustrd",
        "name": "Remittance Information",
        "status": FieldStatus.OPTIONAL,
        "data_type": "string",
        "max_length": 140,
        "description": "Unstructured remittance information",
        "validation_rules": [
            "Maximum 140 characters",
            "Free text for payment purpose",
            "Should not contain sensitive information"
        ],
        "test_scenarios": [
            "valid_reference", "max_length", "special_characters", "empty_field"
        ]
    }
}

# Validation Rules for Business Logic
PACS008_BUSINESS_RULES = {
    "consistency_checks": {
        "amount_currency_consistency": {
            "description": "Settlement amount and currency must be consistent",
            "rule": "interbank_settlement_amount.currency == settlement_currency",
            "severity": ValidationSeverity.CRITICAL
        },
        "agent_relationship": {
            "description": "Instructing and Instructed agents should be different for external transfers",
            "rule": "instructing_agent_bic != instructed_agent_bic",
            "severity": ValidationSeverity.HIGH
        },
        "settlement_date_logic": {
            "description": "Settlement date should not be in the past",
            "rule": "interbank_settlement_date >= today",
            "severity": ValidationSeverity.HIGH
        }
    },
    
    "format_validations": {
        "bic_format": {
            "description": "All BIC codes must follow ISO 9362 format",
            "pattern": r"^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$",
            "severity": ValidationSeverity.CRITICAL
        },
        "currency_format": {
            "description": "Currency codes must be valid ISO 4217",
            "pattern": r"^[A-Z]{3}$",
            "severity": ValidationSeverity.CRITICAL
        },
        "uuid_format": {
            "description": "UETR must be valid UUID v4 format",
            "pattern": r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
            "severity": ValidationSeverity.CRITICAL
        }
    }
}

# Test Case Templates for Different Validation Types
PACS008_TEST_TEMPLATES = {
    "maker_field_validation": {
        "description": "Maker role field validation test",
        "template": {
            "Role_Focus": "Maker",
            "Validation_Type": "Format",
            "Precondition": "User logged in as Maker role",
            "Steps_Template": "1. Navigate to PACS.008 creation\n2. Enter {field_name}: {test_value}\n3. Enter other required fields\n4. Attempt to submit",
            "Expected_Result_Template": "{expected_outcome} for {field_name} field"
        }
    },
    
    "checker_business_validation": {
        "description": "Checker role business validation test",
        "template": {
            "Role_Focus": "Checker", 
            "Validation_Type": "Business_Rule",
            "Precondition": "Valid PACS.008 message submitted by Maker",
            "Steps_Template": "1. Login as Checker\n2. Review message with {field_name}: {test_value}\n3. Verify business rules\n4. {checker_action}",
            "Expected_Result_Template": "Message {approval_status} with reason: {business_reason}"
        }
    },
    
    "end_to_end_workflow": {
        "description": "Complete maker-checker workflow test",
        "template": {
            "Role_Focus": "End-to-End",
            "Validation_Type": "Workflow", 
            "Precondition": "System available and users have appropriate roles",
            "Steps_Template": "1. Maker creates PACS.008 with valid data\n2. Submit for approval\n3. Checker reviews and {checker_action}\n4. Verify final status",
            "Expected_Result_Template": "Complete workflow {workflow_outcome}"
        }
    }
}

# Example realistic test data
PACS008_TEST_DATA = {
    "valid_bics": [
        "DEUTDEFF", "CHASUS33", "BNPAFRPP", "HSBCGB2L", "CITIUS33",
        "BANKAUAAXXX", "BANKGBCCXXX", "BANKUSBBXXX"
    ],
    "invalid_bics": [
        "INVALID123", "SHORT", "TOOLONGBICCODE", "123INVALID", "invalid"
    ],
    "valid_currencies": ["USD", "EUR", "GBP", "CHF", "JPY", "CAD", "AUD"],
    "invalid_currencies": ["US", "EURO", "POUND", "XYZ", "123"],
    "valid_amounts": ["100.00", "1000.50", "50000.00", "999999.99"],
    "invalid_amounts": ["0.00", "-100.00", "100.123", "abc.def"],
    "valid_settlement_methods": ["INDA", "INGA", "CLRG", "COVE"],
    "invalid_settlement_methods": ["INVALID", "ABC", "123", ""],
    "valid_charge_bearer": ["DEBT", "CRED", "SHAR", "SLEV"],
    "invalid_charge_bearer": ["INVALID", "DEB", "CREDITOR", "123"]
}

# Helper functions for field validation
def get_field_definition(field_name: str) -> Dict[str, Any]:
    """Get field definition by name"""
    return PACS008_FIELD_DEFINITIONS.get(field_name, {})

def get_mandatory_fields() -> List[str]:
    """Get list of mandatory field names"""
    return [name for name, defn in PACS008_FIELD_DEFINITIONS.items() 
            if defn.get("status") == FieldStatus.MANDATORY]

def get_optional_fields() -> List[str]:
    """Get list of optional field names"""
    return [name for name, defn in PACS008_FIELD_DEFINITIONS.items() 
            if defn.get("status") == FieldStatus.OPTIONAL]

def get_test_scenarios_for_field(field_name: str) -> List[str]:
    """Get test scenarios for a specific field"""
    field_def = get_field_definition(field_name)
    return field_def.get("test_scenarios", [])

def get_validation_rules_for_field(field_name: str) -> List[str]:
    """Get validation rules for a specific field"""
    field_def = get_field_definition(field_name)
    return field_def.get("validation_rules", [])

# Configuration for different banking regions
REGIONAL_VARIATIONS = {
    "CBPR_PLUS": {
        "instruction_id_max_length": 16,
        "settlement_methods": ["INDA", "INGA"],
        "mandatory_fields": ["uetr", "instructing_agent_bic", "instructed_agent_bic"]
    },
    "SEPA": {
        "charge_bearer_allowed": ["SHAR"],
        "currency_restriction": ["EUR"],
        "account_format": ["IBAN"]
    },
    "RTGS": {
        "settlement_methods": ["CLRG"],
        "real_time_processing": True,
        "high_value_threshold": 100000.00
    }
}

if __name__ == "__main__":
    # Example usage
    print("PACS.008 Configuration Loaded")
    print(f"Mandatory fields: {len(get_mandatory_fields())}")
    print(f"Optional fields: {len(get_optional_fields())}")
    print(f"Total field definitions: {len(PACS008_FIELD_DEFINITIONS)}")
    
    # Test field lookup
    field_def = get_field_definition("instructing_agent_bic")
    print(f"\nSample field definition:")
    print(f"Name: {field_def.get('name')}")
    print(f"Status: {field_def.get('status')}")
    print(f"Validation rules: {field_def.get('validation_rules')}")