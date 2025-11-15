"""Lending Agent for loan approval verification."""
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List
import uuid

from agents.base_verification_agent import (
    VerificationAgent,
    TaskDetails,
    ValidationResult
)
from models.transaction import Transaction
from models.verification import (
    VerificationReport,
    VerificationType,
    ReportStatus,
    TaskStatus
)


class LendingAgent(VerificationAgent):
    """
    Agent responsible for coordinating lending verification and validating loan approvals.
    
    Payment amount: $0 (lender is paid separately by buyer)
    Dependencies: Title search and appraisal must be completed first
    """
    
    PAYMENT_AMOUNT = Decimal("0.00")
    DEPENDENCIES = [VerificationType.TITLE_SEARCH, VerificationType.APPRAISAL]
    
    def __init__(self, agent_id: str = None):
        """Initialize the Lending Agent."""
        agent_id = agent_id or f"lending-{uuid.uuid4().hex[:8]}"
        super().__init__(agent_id=agent_id, agent_name="LendingAgent")
    
    async def execute_verification(
        self,
        transaction: Transaction,
        task_details: TaskDetails
    ) -> VerificationReport:
        """
        Execute lending verification.
        
        This method coordinates with lenders to verify loan approval
        and generates a verification report.
        
        Args:
            transaction: The transaction being verified
            task_details: Details about the verification task
        
        Returns:
            VerificationReport: The completed lending verification report
        """
        self.log_activity(
            f"Starting lending verification for transaction {transaction.id}",
            extra_data={
                "transaction_id": transaction.id,
                "property_id": task_details.property_id,
                "task_id": task_details.task_id,
                "loan_amount": str(transaction.total_purchase_price - transaction.earnest_money)
            }
        )
        
        # Mock lending verification - in production, this would integrate with lender APIs
        lending_results = await self._perform_lending_verification(
            property_id=task_details.property_id,
            transaction=transaction
        )
        
        # Create verification report
        report = VerificationReport(
            id=str(uuid.uuid4()),
            task_id=task_details.task_id,
            agent_id=self.agent_id,
            report_type=VerificationType.LENDING,
            status=ReportStatus.NEEDS_REVIEW,
            findings=lending_results,
            documents=self._generate_document_urls(task_details.task_id),
            submitted_at=datetime.utcnow()
        )
        
        self.log_activity(
            f"Lending verification completed for transaction {transaction.id}",
            extra_data={
                "transaction_id": transaction.id,
                "report_id": report.id,
                "loan_approved": lending_results.get("loan_approved", False)
            }
        )
        
        return report
    
    async def validate_report(
        self,
        report: VerificationReport
    ) -> ValidationResult:
        """
        Validate a lending verification report.
        
        Checks for required fields, loan approval status, and validates loan terms.
        
        Args:
            report: The report to validate
        
        Returns:
            ValidationResult: The validation result
        """
        errors = []
        warnings = []
        
        # Validate report type
        if report.report_type != VerificationType.LENDING:
            errors.append(f"Invalid report type: {report.report_type}. Expected LENDING")
        
        # Validate findings structure
        if not report.findings:
            errors.append("Report findings are missing")
        else:
            findings = report.findings
            
            # Check required fields
            required_fields = [
                "lender_name",
                "loan_officer_name",
                "loan_officer_contact",
                "loan_approved",
                "loan_amount",
                "loan_type",
                "interest_rate",
                "loan_term_years"
            ]
            
            for field in required_fields:
                if field not in findings:
                    errors.append(f"Missing required field: {field}")
            
            # Validate loan approval status
            if "loan_approved" in findings:
                if not isinstance(findings["loan_approved"], bool):
                    errors.append("loan_approved must be a boolean value")
                elif not findings["loan_approved"]:
                    errors.append("Loan has not been approved")
            
            # Validate loan amount
            if "loan_amount" in findings:
                try:
                    loan_amount = Decimal(str(findings["loan_amount"]))
                    if loan_amount <= 0:
                        errors.append("Loan amount must be greater than zero")
                    
                    # Check if loan amount is reasonable for purchase price
                    if "purchase_price" in findings:
                        purchase_price = Decimal(str(findings["purchase_price"]))
                        down_payment_percent = (purchase_price - loan_amount) / purchase_price * 100
                        
                        if down_payment_percent < 3:
                            warnings.append(
                                f"Down payment is only {down_payment_percent:.1f}%. "
                                "Consider higher down payment for better terms"
                            )
                        elif down_payment_percent > 50:
                            warnings.append(
                                f"Down payment is {down_payment_percent:.1f}%. "
                                "Unusually high down payment"
                            )
                except (ValueError, TypeError):
                    errors.append("Invalid loan_amount format")
            
            # Validate interest rate
            if "interest_rate" in findings:
                try:
                    interest_rate = float(findings["interest_rate"])
                    if interest_rate <= 0 or interest_rate > 20:
                        errors.append("Interest rate must be between 0 and 20 percent")
                    elif interest_rate > 10:
                        warnings.append(f"Interest rate of {interest_rate}% is unusually high")
                except (ValueError, TypeError):
                    errors.append("Invalid interest_rate format")
            
            # Validate loan type
            if "loan_type" in findings:
                valid_loan_types = [
                    "conventional",
                    "fha",
                    "va",
                    "usda",
                    "jumbo",
                    "adjustable_rate",
                    "fixed_rate"
                ]
                if findings["loan_type"] not in valid_loan_types:
                    warnings.append(
                        f"Unusual loan_type: {findings['loan_type']}. "
                        f"Expected one of: {', '.join(valid_loan_types)}"
                    )
            
            # Validate loan term
            if "loan_term_years" in findings:
                try:
                    loan_term = int(findings["loan_term_years"])
                    if loan_term not in [10, 15, 20, 30]:
                        warnings.append(
                            f"Unusual loan term: {loan_term} years. "
                            "Standard terms are 10, 15, 20, or 30 years"
                        )
                except (ValueError, TypeError):
                    errors.append("Invalid loan_term_years format")
            
            # Check for conditions
            if "conditions" in findings:
                conditions = findings["conditions"]
                if isinstance(conditions, list) and len(conditions) > 0:
                    warnings.append(
                        f"Loan approval has {len(conditions)} condition(s) that must be met"
                    )
            
            # Validate underwriting status
            if "underwriting_complete" in findings:
                if not findings["underwriting_complete"]:
                    warnings.append("Underwriting is not yet complete")
            
            # Check for appraisal requirement
            if "appraisal_required" in findings:
                if findings["appraisal_required"] and not findings.get("appraisal_received"):
                    errors.append("Lender requires appraisal but it has not been received")
        
        # Validate documents
        if not report.documents or len(report.documents) == 0:
            warnings.append("No supporting documents attached")
        
        # Determine status
        if errors:
            status = ReportStatus.REJECTED
            is_valid = False
        elif not findings.get("loan_approved"):
            status = ReportStatus.REJECTED
            is_valid = False
        elif findings.get("conditions") and len(findings["conditions"]) > 0:
            status = ReportStatus.NEEDS_REVIEW
            is_valid = True
        else:
            status = ReportStatus.APPROVED
            is_valid = True
        
        return ValidationResult(
            is_valid=is_valid,
            status=status,
            errors=errors,
            warnings=warnings
        )
    
    async def _perform_lending_verification(
        self,
        property_id: str,
        transaction: Transaction
    ) -> Dict[str, Any]:
        """
        Perform lending verification (mock implementation for MVP).
        
        In production, this would integrate with lender APIs.
        
        Args:
            property_id: The property identifier
            transaction: The transaction
        
        Returns:
            Dict containing lending verification results
        """
        # Mock lending verification results
        # In production, this would call external lender APIs
        
        self.log_activity(
            "Performing lending verification via lender API (mock)",
            extra_data={"property_id": property_id}
        )
        
        from services.ai_mock_verification import ai_mock_service
        
        # Calculate loan amount (purchase price minus earnest money)
        loan_amount = transaction.total_purchase_price - transaction.earnest_money
        
        # Get property address from transaction metadata
        metadata = transaction.transaction_metadata or {}
        property_address = metadata.get("property_address", f"Property {property_id}")
        borrower_name = metadata.get("buyer_name")
        
        # Generate AI-powered realistic lending verification
        results = await ai_mock_service.generate_lending_verification(
            property_address=property_address,
            loan_amount=loan_amount,
            purchase_price=transaction.total_purchase_price,
            down_payment=transaction.earnest_money,
            borrower_name=borrower_name
        )
        
        return results
    
    def _generate_document_urls(self, task_id: str) -> List[str]:
        """
        Generate URLs for supporting documents.
        
        In production, these would be actual document storage URLs.
        
        Args:
            task_id: The task identifier
        
        Returns:
            List of document URLs
        """
        return [
            f"https://documents.example.com/lending/{task_id}/loan-commitment-letter.pdf",
            f"https://documents.example.com/lending/{task_id}/loan-estimate.pdf",
            f"https://documents.example.com/lending/{task_id}/underwriting-approval.pdf",
            f"https://documents.example.com/lending/{task_id}/credit-report.pdf"
        ]
