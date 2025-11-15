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
        Perform title search via x402 payment service (Locus or mock).
        
        In production with Locus: Uses Locus payment handler for real payments.
        In demo mode: Uses mock services.
        
        Args:
            property_id: The property identifier
            transaction: The transaction
        
        Returns:
            Dict containing title search results
        """
        from config.settings import settings
        from services.x402_protocol_handler import X402ProtocolHandler
        from services.locus_integration import get_locus
        
        self.log_activity(
            "Performing title search via x402 payment service",
            extra_data={"property_id": property_id}
        )
        
        service_url = settings.landamerica_service
        agent_id = "title-agent"
        recipient = settings.service_recipient_landamerica  # LandAmerica Wallet
        
        # Convert payment amount to USDC (from USD)
        amount_usdc = float(self.PAYMENT_AMOUNT) / 1000.0  # $1200 -> 1.2 USDC (example conversion)
        
        # Try to use Locus if available
        locus = get_locus()
        payment_handler = None
        
        if locus and not settings.use_mock_services:
            try:
                from services.locus_payment_handler import LocusPaymentHandler
                payment_handler = LocusPaymentHandler(locus)
                self.log_activity("Using Locus payment handler", extra_data={"agent": agent_id})
            except Exception as e:
                self.log_activity(f"Locus unavailable, using mock: {str(e)}", level="WARNING")
        
        # Initialize x402 protocol handler
        x402_handler = X402ProtocolHandler(payment_handler=payment_handler)
        
        # Execute x402 flow
        result = await x402_handler.execute_x402_flow(
            service_url=service_url,
            amount=amount_usdc,
            agent_id=agent_id if payment_handler else None,
            recipient=recipient if payment_handler else None
        )
        
        if result.get("status") != "success":
            error_msg = result.get("error", "Unknown error")
            self.log_activity(f"x402 flow failed: {error_msg}", level="ERROR")
            raise Exception(f"Title search failed: {error_msg}")
        
        # Extract data from result
        data = result.get("data", {})
        result_data = data.get("result", data)
        
        return {
            "property_address": result_data.get("property_address", f"Property {property_id}"),
            "current_owner": result_data.get("current_owner", "Unknown"),
            "chain_of_title": result_data.get("chain_of_title", []),
            "liens_and_encumbrances": result_data.get("liens_and_encumbrances", []),
            "has_issues": not result_data.get("title_status") == "CLEAR",
            "title_status": result_data.get("title_status", "UNKNOWN"),
            "payment_tx": result.get("tx_hash", result.get("payment_signed")),
            "report_date": result_data.get("report_date")
        }
    
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
