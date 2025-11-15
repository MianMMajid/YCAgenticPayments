"""Inspection Agent for property inspection coordination."""
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


class InspectionAgent(VerificationAgent):
    """
    Agent responsible for coordinating property inspections and validating inspection reports.
    
    Payment amount: $500
    """
    
    PAYMENT_AMOUNT = Decimal("500.00")
    
    def __init__(self, agent_id: str = None):
        """Initialize the Inspection Agent."""
        agent_id = agent_id or f"inspection-{uuid.uuid4().hex[:8]}"
        super().__init__(agent_id=agent_id, agent_name="InspectionAgent")
    
    async def execute_verification(
        self,
        transaction: Transaction,
        task_details: TaskDetails
    ) -> VerificationReport:
        """
        Execute property inspection verification.
        
        This method coordinates with inspection services to perform a property inspection
        and generates a verification report.
        
        Args:
            transaction: The transaction being verified
            task_details: Details about the verification task
        
        Returns:
            VerificationReport: The completed inspection report
        """
        self.log_activity(
            f"Starting property inspection for property {task_details.property_id}",
            extra_data={
                "transaction_id": transaction.id,
                "property_id": task_details.property_id,
                "task_id": task_details.task_id
            }
        )
        
        # Mock inspection - in production, this would integrate with inspection service APIs
        inspection_results = await self._perform_inspection(
            property_id=task_details.property_id,
            transaction=transaction
        )
        
        # Create verification report
        report = VerificationReport(
            id=str(uuid.uuid4()),
            task_id=task_details.task_id,
            agent_id=self.agent_id,
            report_type=VerificationType.INSPECTION,
            status=ReportStatus.NEEDS_REVIEW,
            findings=inspection_results,
            documents=self._generate_document_urls(task_details.task_id),
            submitted_at=datetime.utcnow()
        )
        
        self.log_activity(
            f"Property inspection completed for property {task_details.property_id}",
            extra_data={
                "transaction_id": transaction.id,
                "report_id": report.id,
                "has_major_issues": inspection_results.get("has_major_issues", False)
            }
        )
        
        return report
    
    async def validate_report(
        self,
        report: VerificationReport
    ) -> ValidationResult:
        """
        Validate an inspection report.
        
        Checks for required fields, data completeness, and identifies any issues.
        
        Args:
            report: The report to validate
        
        Returns:
            ValidationResult: The validation result
        """
        errors = []
        warnings = []
        
        # Validate report type
        if report.report_type != VerificationType.INSPECTION:
            errors.append(f"Invalid report type: {report.report_type}. Expected INSPECTION")
        
        # Validate findings structure
        if not report.findings:
            errors.append("Report findings are missing")
        else:
            findings = report.findings
            
            # Check required fields
            required_fields = [
                "property_address",
                "inspection_date",
                "inspector_name",
                "inspector_license",
                "areas_inspected",
                "has_major_issues"
            ]
            
            for field in required_fields:
                if field not in findings:
                    errors.append(f"Missing required field: {field}")
            
            # Validate areas inspected
            if "areas_inspected" in findings:
                areas = findings["areas_inspected"]
                if not isinstance(areas, list) or len(areas) == 0:
                    errors.append("areas_inspected must be a non-empty list")
                else:
                    # Check for minimum required inspection areas
                    required_areas = ["foundation", "roof", "electrical", "plumbing", "hvac"]
                    inspected_area_names = [area.get("area") for area in areas if isinstance(area, dict)]
                    missing_areas = [area for area in required_areas if area not in inspected_area_names]
                    if missing_areas:
                        warnings.append(f"Missing inspection of recommended areas: {', '.join(missing_areas)}")
            
            # Check for major issues
            if findings.get("has_major_issues"):
                issues = findings.get("major_issues", [])
                if not issues:
                    errors.append("has_major_issues is True but no major issues listed")
                else:
                    warnings.append(f"Inspection found {len(issues)} major issue(s) requiring attention")
            
            # Check for minor issues
            minor_issues = findings.get("minor_issues", [])
            if len(minor_issues) > 0:
                warnings.append(f"Inspection found {len(minor_issues)} minor issue(s)")
            
            # Validate overall condition rating
            if "overall_condition" in findings:
                valid_ratings = ["excellent", "good", "fair", "poor"]
                if findings["overall_condition"] not in valid_ratings:
                    errors.append(f"Invalid overall_condition rating. Must be one of: {', '.join(valid_ratings)}")
        
        # Validate documents
        if not report.documents or len(report.documents) == 0:
            warnings.append("No supporting documents attached")
        
        # Determine status
        if errors:
            status = ReportStatus.REJECTED
            is_valid = False
        elif findings.get("has_major_issues"):
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
    
    async def _perform_inspection(
        self,
        property_id: str,
        transaction: Transaction
    ) -> Dict[str, Any]:
        """
        Perform property inspection (mock implementation for MVP).
        
        In production, this would integrate with inspection service APIs.
        
        Args:
            property_id: The property identifier
            transaction: The transaction
        
        Returns:
            Dict containing inspection results
        """
        from services.ai_mock_verification import ai_mock_service
        
        self.log_activity(
            "Performing property inspection via AI-powered mock service (hackathon demo)",
            extra_data={"property_id": property_id}
        )
        
        # Get property details from transaction metadata
        metadata = transaction.transaction_metadata or {}
        property_address = metadata.get("property_address", f"Property {property_id}")
        property_type = metadata.get("property_type", "single-family")
        year_built = metadata.get("year_built")
        square_feet = metadata.get("square_feet")
        
        # Generate AI-powered realistic inspection report
        results = await ai_mock_service.generate_inspection_report(
            property_address=property_address,
            property_id=property_id,
            property_type=property_type,
            year_built=year_built,
            square_feet=square_feet
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
            f"https://documents.example.com/inspection/{task_id}/inspection-report.pdf",
            f"https://documents.example.com/inspection/{task_id}/photos.zip",
            f"https://documents.example.com/inspection/{task_id}/inspector-license.pdf"
        ]
