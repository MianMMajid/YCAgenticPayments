"""Appraisal Agent for property appraisal coordination."""
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


class AppraisalAgent(VerificationAgent):
    """
    Agent responsible for coordinating property appraisals and validating appraisal reports.
    
    Payment amount: $400
    Dependencies: Inspection must be completed first
    """
    
    PAYMENT_AMOUNT = Decimal("400.00")
    DEPENDENCIES = [VerificationType.INSPECTION]
    
    def __init__(self, agent_id: str = None):
        """Initialize the Appraisal Agent."""
        agent_id = agent_id or f"appraisal-{uuid.uuid4().hex[:8]}"
        super().__init__(agent_id=agent_id, agent_name="AppraisalAgent")
    
    async def execute_verification(
        self,
        transaction: Transaction,
        task_details: TaskDetails
    ) -> VerificationReport:
        """
        Execute property appraisal verification.
        
        This method coordinates with appraisal services to perform a property appraisal
        and generates a verification report.
        
        Args:
            transaction: The transaction being verified
            task_details: Details about the verification task
        
        Returns:
            VerificationReport: The completed appraisal report
        """
        self.log_activity(
            f"Starting property appraisal for property {task_details.property_id}",
            extra_data={
                "transaction_id": transaction.id,
                "property_id": task_details.property_id,
                "task_id": task_details.task_id,
                "purchase_price": str(transaction.total_purchase_price)
            }
        )
        
        # Mock appraisal - in production, this would integrate with appraisal service APIs
        appraisal_results = await self._perform_appraisal(
            property_id=task_details.property_id,
            transaction=transaction
        )
        
        # Create verification report
        report = VerificationReport(
            id=str(uuid.uuid4()),
            task_id=task_details.task_id,
            agent_id=self.agent_id,
            report_type=VerificationType.APPRAISAL,
            status=ReportStatus.NEEDS_REVIEW,
            findings=appraisal_results,
            documents=self._generate_document_urls(task_details.task_id),
            submitted_at=datetime.utcnow()
        )
        
        self.log_activity(
            f"Property appraisal completed for property {task_details.property_id}",
            extra_data={
                "transaction_id": transaction.id,
                "report_id": report.id,
                "appraised_value": appraisal_results.get("appraised_value"),
                "purchase_price": str(transaction.total_purchase_price)
            }
        )
        
        return report
    
    async def validate_report(
        self,
        report: VerificationReport
    ) -> ValidationResult:
        """
        Validate an appraisal report.
        
        Checks for required fields, data completeness, and validates appraisal methodology.
        
        Args:
            report: The report to validate
        
        Returns:
            ValidationResult: The validation result
        """
        errors = []
        warnings = []
        
        # Validate report type
        if report.report_type != VerificationType.APPRAISAL:
            errors.append(f"Invalid report type: {report.report_type}. Expected APPRAISAL")
        
        # Validate findings structure
        if not report.findings:
            errors.append("Report findings are missing")
        else:
            findings = report.findings
            
            # Check required fields
            required_fields = [
                "property_address",
                "appraisal_date",
                "appraiser_name",
                "appraiser_license",
                "appraised_value",
                "appraisal_method",
                "comparable_properties"
            ]
            
            for field in required_fields:
                if field not in findings:
                    errors.append(f"Missing required field: {field}")
            
            # Validate appraised value
            if "appraised_value" in findings:
                try:
                    appraised_value = Decimal(str(findings["appraised_value"]))
                    if appraised_value <= 0:
                        errors.append("Appraised value must be greater than zero")
                    
                    # Check if appraisal is significantly different from purchase price
                    if "purchase_price" in findings:
                        purchase_price = Decimal(str(findings["purchase_price"]))
                        variance = abs(appraised_value - purchase_price) / purchase_price
                        
                        if variance > Decimal("0.10"):  # More than 10% difference
                            warnings.append(
                                f"Appraised value differs from purchase price by {variance * 100:.1f}%"
                            )
                except (ValueError, TypeError):
                    errors.append("Invalid appraised_value format")
            
            # Validate appraisal method
            if "appraisal_method" in findings:
                valid_methods = ["sales_comparison", "cost_approach", "income_approach", "hybrid"]
                if findings["appraisal_method"] not in valid_methods:
                    errors.append(
                        f"Invalid appraisal_method. Must be one of: {', '.join(valid_methods)}"
                    )
            
            # Validate comparable properties
            if "comparable_properties" in findings:
                comps = findings["comparable_properties"]
                if not isinstance(comps, list):
                    errors.append("comparable_properties must be a list")
                elif len(comps) < 3:
                    warnings.append(
                        f"Only {len(comps)} comparable properties provided. Recommended minimum is 3"
                    )
                else:
                    # Validate each comparable
                    for i, comp in enumerate(comps):
                        if not isinstance(comp, dict):
                            errors.append(f"Comparable property {i+1} must be a dictionary")
                            continue
                        
                        required_comp_fields = ["address", "sale_price", "sale_date", "square_feet"]
                        for field in required_comp_fields:
                            if field not in comp:
                                errors.append(
                                    f"Comparable property {i+1} missing required field: {field}"
                                )
            
            # Validate property characteristics
            if "property_characteristics" in findings:
                chars = findings["property_characteristics"]
                recommended_fields = ["square_feet", "bedrooms", "bathrooms", "year_built", "lot_size"]
                missing_fields = [f for f in recommended_fields if f not in chars]
                if missing_fields:
                    warnings.append(
                        f"Property characteristics missing recommended fields: {', '.join(missing_fields)}"
                    )
        
        # Validate documents
        if not report.documents or len(report.documents) == 0:
            warnings.append("No supporting documents attached")
        
        # Determine status
        if errors:
            status = ReportStatus.REJECTED
            is_valid = False
        elif len(warnings) > 2:  # Multiple warnings may require review
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
    
    async def _perform_appraisal(
        self,
        property_id: str,
        transaction: Transaction
    ) -> Dict[str, Any]:
        """
        Perform property appraisal (mock implementation for MVP).
        
        In production, this would integrate with appraisal service APIs.
        
        Args:
            property_id: The property identifier
            transaction: The transaction
        
        Returns:
            Dict containing appraisal results
        """
        from services.ai_mock_verification import ai_mock_service
        
        self.log_activity(
            "Performing property appraisal via AI-powered mock service (hackathon demo)",
            extra_data={"property_id": property_id}
        )
        
        # Get property details from transaction metadata
        metadata = transaction.transaction_metadata or {}
        property_address = metadata.get("property_address", f"Property {property_id}")
        property_type = metadata.get("property_type", "single-family")
        bedrooms = metadata.get("bedrooms")
        bathrooms = metadata.get("bathrooms")
        square_feet = metadata.get("square_feet")
        year_built = metadata.get("year_built")
        
        # Generate AI-powered realistic appraisal report
        results = await ai_mock_service.generate_appraisal_report(
            property_address=property_address,
            property_id=property_id,
            purchase_price=transaction.total_purchase_price,
            property_type=property_type,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            square_feet=square_feet,
            year_built=year_built
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
            f"https://documents.example.com/appraisal/{task_id}/appraisal-report.pdf",
            f"https://documents.example.com/appraisal/{task_id}/comparable-sales.pdf",
            f"https://documents.example.com/appraisal/{task_id}/appraiser-license.pdf",
            f"https://documents.example.com/appraisal/{task_id}/property-photos.zip"
        ]
