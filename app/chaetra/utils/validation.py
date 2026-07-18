"""Validation utilities for CHAETRA."""
from typing import Dict, Any, List, Optional, Type, Union, Callable
from dataclasses import dataclass
from datetime import datetime
import re
from app.chaetra.utils.errors import ValidationError

@dataclass
class ValidationRule:
    """Validation rule definition."""
    field: str
    rule_type: str
    params: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    custom_validator: Optional[Callable] = None

class Validator:
    """Generic validator for CHAETRA data structures."""
    
    def __init__(self):
        self.rules: Dict[str, List[ValidationRule]] = {}
        
    def add_rule(self, rule: ValidationRule) -> None:
        """Add a validation rule."""
        if rule.field not in self.rules:
            self.rules[rule.field] = []
        self.rules[rule.field].append(rule)
        
    def validate(self, data: Dict[str, Any]) -> None:
        """Validate data against defined rules."""
        errors = []
        
        for field, rules in self.rules.items():
            value = data.get(field)
            for rule in rules:
                try:
                    self._validate_rule(rule, value)
                except ValidationError as e:
                    errors.append(str(e))
                    
        if errors:
            raise ValidationError(
                "Validation failed",
                details={"errors": errors}
            )

    def _validate_rule(self, rule: ValidationRule, value: Any) -> None:
        """Validate a single rule."""
        if rule.custom_validator:
            if not rule.custom_validator(value):
                raise ValidationError(
                    rule.message or f"Custom validation failed for {rule.field}",
                    details={"field": rule.field, "value": value}
                )
                
        if rule.rule_type == "required" and value is None:
            raise ValidationError(
                rule.message or f"Field {rule.field} is required",
                details={"field": rule.field}
            )
            
        if value is not None:
            self._validate_type_and_constraints(rule, value)

    def _validate_type_and_constraints(self, rule: ValidationRule, value: Any) -> None:
        """Validate type and constraints of a value."""
        if rule.rule_type == "type":
            expected_type = rule.params.get("type")
            if not isinstance(value, expected_type):
                raise ValidationError(
                    rule.message or f"Field {rule.field} must be of type {expected_type.__name__}",
                    details={"field": rule.field, "value": value, "expected_type": expected_type.__name__}
                )
                
        elif rule.rule_type == "range":
            min_val = rule.params.get("min")
            max_val = rule.params.get("max")
            if min_val is not None and value < min_val:
                raise ValidationError(
                    rule.message or f"Field {rule.field} must be >= {min_val}",
                    details={"field": rule.field, "value": value, "min": min_val}
                )
            if max_val is not None and value > max_val:
                raise ValidationError(
                    rule.message or f"Field {rule.field} must be <= {max_val}",
                    details={"field": rule.field, "value": value, "max": max_val}
                )
                
        elif rule.rule_type == "regex":
            pattern = rule.params.get("pattern")
            if not re.match(pattern, str(value)):
                raise ValidationError(
                    rule.message or f"Field {rule.field} does not match pattern",
                    details={"field": rule.field, "value": value, "pattern": pattern}
                )

class ChaetraValidators:
    """Pre-configured validators for CHAETRA components."""
    
    @staticmethod
    def get_memory_validator() -> Validator:
        """Get validator for memory items."""
        validator = Validator()
        
        validator.add_rule(ValidationRule(
            field="id",
            rule_type="required"
        ))
        validator.add_rule(ValidationRule(
            field="content",
            rule_type="required"
        ))
        validator.add_rule(ValidationRule(
            field="memory_type",
            rule_type="regex",
            params={"pattern": r"^(short_term|core)$"},
            message="memory_type must be either 'short_term' or 'core'"
        ))
        
        return validator
        
    @staticmethod
    def get_pattern_validator() -> Validator:
        """Get validator for patterns."""
        validator = Validator()
        
        validator.add_rule(ValidationRule(
            field="pattern_type",
            rule_type="required"
        ))
        validator.add_rule(ValidationRule(
            field="confidence",
            rule_type="range",
            params={"min": 0.0, "max": 1.0},
            message="confidence must be between 0 and 1"
        ))
        
        return validator
        
    @staticmethod
    def get_opinion_validator() -> Validator:
        """Get validator for opinions."""
        validator = Validator()
        
        validator.add_rule(ValidationRule(
            field="subject",
            rule_type="required"
        ))
        validator.add_rule(ValidationRule(
            field="belief",
            rule_type="required"
        ))
        validator.add_rule(ValidationRule(
            field="confidence",
            rule_type="range",
            params={"min": 0.0, "max": 1.0}
        ))
        
        return validator

def validate_data(data: Dict[str, Any], validator: Validator) -> None:
    """Validate data using specified validator."""
    validator.validate(data)

def validate_type(value: Any, expected_type: Type) -> None:
    """Validate value is of expected type."""
    if not isinstance(value, expected_type):
        raise ValidationError(
            f"Expected type {expected_type.__name__}",
            details={"value": value, "actual_type": type(value).__name__}
        )

def validate_range(value: Union[int, float], min_val: Optional[Union[int, float]] = None, 
                  max_val: Optional[Union[int, float]] = None) -> None:
    """Validate value is within range."""
    if min_val is not None and value < min_val:
        raise ValidationError(
            f"Value must be >= {min_val}",
            details={"value": value, "min": min_val}
        )
    if max_val is not None and value > max_val:
        raise ValidationError(
            f"Value must be <= {max_val}",
            details={"value": value, "max": max_val}
        )

def validate_pattern(value: str, pattern: str) -> None:
    """Validate value matches regex pattern."""
    if not re.match(pattern, value):
        raise ValidationError(
            "Value does not match pattern",
            details={"value": value, "pattern": pattern}
        )
