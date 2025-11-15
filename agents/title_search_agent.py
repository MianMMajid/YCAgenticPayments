"""Title Search Agent for property title verification."""
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


class TitleSearchAgent(VerificationAgent):
    """
    Agent responsible for coordinating title searches and validating title reports.
    
    Payment amount: $1,200
    """
    
    PAYMENT_AMOUNT = Decimal("1200.00")
    
    def __init__(self, agent_id: str = None):
        """Initialize the Title Search Agent."""
        agent_id = agent_id or f"title-search-{uuid.uuid4().hex[:8]}"
        super().__init__(agent_id=agent_id, agent_name="TitleSearchAgent")
    
    async def execute_verification(
        self,
        transaction: Transaction,
        task_details: TaskDetails
    ) -> VerificationReport:
        """
        Execute title search verification.
        
        This method coordinates with title companies to perform a title search
        and generates a verification report.
        
        Args:
            transaction: The transaction being verified
            task_details: Details about the verification task
        
        Returns:
            VerificationReport: The completed title search report
        """
        self.log_activity(
            f"Starting title search for property {task_details.property_id}",
            extra_data={
                "transaction_id": transaction.id,
                "property_id": task_details.property_id,
                "task_id": task_details.task_id
            }
        )
        
        # Mock title search - in production, this would integrate with title company APIs
        title_search_results = await self._perform_title_search(
            property_id=task_details.property_id,
            transaction=transaction
        )
        
        # Create verification report
        report = VerificationReport(
            id=str(uuid.uuid4()),
            task_id=task_details.task_id,
            agent_id=self.agent_id,
            report_type=VerificationType.TITLE_SEARCH,
            status=ReportStatus.NEEDS_REVIEW,
            findings=title_search_results,
            documents=self._generate_document_urls(task_details.task_id),
            submitted_at=datetime.utcnow()
        )
        
        self.log_activity(
            f"Title search completed for property {task_details.property_id}",
            extra_data={
                "transaction_id": transaction.id,
                "report_id": report.id,
                "has_issues": title_search_results.get("has_issues", False)
            }
        )
        
        return report
    
    async def validate_report(
        self,
        report: VerificationReport
    ) -> ValidationResult:
        """
        Validate a title search report.
        
        Checks for required fields, data completeness, and identifies any issues.
        
        Args:
            report: The report to validate
        
        Returns:
            ValidationResult: The validation result
        """
        errors = []
        warnings = []
        
        # Validate report type
        if report.report_type != VerificationType.TITLE_SEARCH:
            errors.append(f"Invalid report type: {report.report_type}. Expected TITLE_SEARCH")
        
        # Validate findings structure
        if not report.findings:
            errors.append("Report findings are missing")
        else:
            findings = report.findings
            
            # Check required fields
            required_fields = [
                "property_address",
                "current_owner",
                "chain_of_title",
                "liens_and_encumbrances",
                "has_issues"
            ]
            
            for field in required_fields:
                if field not in findings:
                    errors.append(f"Missing required field: {field}")
            
            # Validate chain of title
            if "chain_of_title" in findings:
                chain = findings["chain_of_title"]
                if not isinstance(chain, list) or len(chain) == 0:
                    errors.append("Chain of title must be a non-empty list")
            
            # Check for title issues
            if findings.get("has_issues"):
                issues = findings.get("issues", [])
                if not issues:
                    errors.append("has_issues is True but no issues listed")
                else:
                    warnings.append(f"Title has {len(issues)} issue(s) that need resolution")
            
            # Validate liens and encumbrances
            if "liens_and_encumbrances" in findings:
                liens = findings["liens_and_encumbrances"]
                if not isinstance(liens, list):
                    errors.append("liens_and_encumbrances must be a list")
                elif len(liens) > 0:
                    warnings.append(f"Property has {len(liens)} lien(s) or encumbrance(s)")
        
        # Validate documents
        if not report.documents or len(report.documents) == 0:
            warnings.append("No supporting documents attached")
        
        # Determine status
        if errors:
            status = ReportStatus.REJECTED
            is_valid = False
        elif findings.get("has_issues") and not findings.get("issues_resolved", False):
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
    
    async def _perform_title_search(
        self,
        property_id: str,
        transaction: Transaction
    ) -> Dict[str, Any]:
        """
        Perform title search (AI-powered mock for hackathon demo).
        
        In production, this would integrate with title company APIs.
        For hackathon, uses AI to generate realistic reports.
        
        Args:
            property_id: The property identifier
            transaction: The transaction
        
        Returns:
            Dict containing title search results
        """
        from services.ai_mock_verification import ai_mock_service
        
        self.log_activity(
            "Performing title search via AI-powered mock service (hackathon demo)",
            extra_data={"property_id": property_id}
        )
        
        # Get property address from transaction metadata or use property_id
        property_address = (
            transaction.transaction_metadata.get("property_address") 
            if transaction.transaction_metadata 
            else f"Property {property_id}"
        )
        
        # Generate AI-powered realistic title search report
        results = await ai_mock_service.generate_title_search_report(
            property_address=property_address,
            property_id=property_id,
            purchase_price=transaction.total_purchase_price,
            seller_name=transaction.seller_agent_id
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
            f"https://documents.example.com/title-search/{task_id}/title-report.pdf",
            f"https://documents.example.com/title-search/{task_id}/chain-of-title.pdf",
            f"https://documents.example.com/title-search/{task_id}/lien-search.pdf"
        ]
