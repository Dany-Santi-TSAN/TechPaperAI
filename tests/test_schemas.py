import pytest
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from core.schemas import SafetyCheck, SafetyStatus

def test_safety_check_valid():
    """Test the creation of a valid SafetyCheck instance with SAFE status"""
    check = SafetyCheck(
        status=SafetyStatus.SAFE,
        confidence=0.95
    )
    # Enum values are serialized as strings (use_enum_values=True)
    assert check.status == "safe"
    # No categories should be flagged for safe content
    assert check.categories_flagged == []

def test_safety_check_unsafe():
    """Test SafetyCheck creation when unsafe content is detected"""
    check = SafetyCheck(
        status=SafetyStatus.UNSAFE,
        reason="Query contains hate speech",
        categories_flagged=["hate_speech", "harassment"],
        confidence=0.92
    )

    assert check.status == "unsafe"  # use_enum_values=True
    # Reason should clearly describe why the content is unsafe
    assert check.reason == "Query contains hate speech"
    # Ensure all unsafe categories are correctly captured
    assert len(check.categories_flagged) == 2
    assert "hate_speech" in check.categories_flagged
    assert "harassment" in check.categories_flagged
    assert check.confidence == 0.92

def test_safety_check_review_needed():
    """Test SafetyCheck creation for ambiguous content requiring human review"""
    check = SafetyCheck(
        status=SafetyStatus.REVIEW_NEEDED,
        reason="Borderline content detected",
        categories_flagged=["sexual_content"],
        confidence=0.65  # Low confidence triggers review workflow
    )

    assert check.status == "review_needed"
    # Confidence score below the review threshold should require manual validation
    assert check.confidence < 0.7  # Threshold pour review
    assert len(check.categories_flagged) == 1
