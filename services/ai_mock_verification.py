"""AI-powered mock verification services for hackathon demo.

This service uses OpenAI to generate realistic verification reports
when real API integrations are not available.

For production, replace these with actual API integrations.
"""
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional
import json

from openai import OpenAI
from config.settings import settings

logger = logging.getLogger(__name__)


class AIMockVerificationService:
    """Service for generating AI-powered mock verification reports."""
    
    def __init__(self):
        """Initialize the AI mock verification service."""
        self.client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
    
    async def generate_title_search_report(
        self,
        property_address: str,
        property_id: str,
        purchase_price: Decimal,
        seller_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a realistic title search report using AI.
        
        Args:
            property_address: Property address
            property_id: Property identifier
            purchase_price: Purchase price
            seller_name: Seller name (optional)
        
        Returns:
            Dict containing title search results
        """
        if not self.client:
            # Fallback to basic mock if OpenAI not available
            return self._basic_title_mock(property_address, property_id, seller_name)
        
        try:
            prompt = f"""Generate a realistic title search report for a real estate property.

Property Address: {property_address}
Property ID: {property_id}
Purchase Price: ${purchase_price:,.2f}
Seller: {seller_name or 'Current Owner'}

Generate a JSON response with the following structure:
{{
    "property_address": "{property_address}",
    "current_owner": "Realistic owner name",
    "chain_of_title": [
        {{
            "owner": "Current owner name",
            "date_acquired": "YYYY-MM-DD (within last 10 years)",
            "deed_type": "Warranty Deed",
            "sale_price": "Realistic price"
        }},
        {{
            "owner": "Previous owner name",
            "date_acquired": "YYYY-MM-DD (5-15 years ago)",
            "deed_type": "Warranty Deed",
            "sale_price": "Realistic price"
        }}
    ],
    "liens_and_encumbrances": [
        {{
            "type": "Mortgage" or "Tax Lien" or "HOA Lien" or null,
            "amount": "Realistic amount if applicable",
            "lien_holder": "Bank name if applicable",
            "date_recorded": "YYYY-MM-DD if applicable"
        }}
    ],
    "has_issues": false or true,
    "issues": ["List of issues if has_issues is true, otherwise empty array"],
    "title_insurance_available": true,
    "search_date": "{datetime.utcnow().isoformat()}",
    "searcher": "AI-Generated Title Search Agent",
    "title_company": "Demo Title Company LLC"
}}

Make it realistic. Most properties should have no issues. If there are issues, make them minor (like an old mortgage that will be paid off at closing).
Return ONLY valid JSON, no markdown formatting."""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a title search expert. Generate realistic title search reports in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"Generated AI title search report for {property_address}")
            return result
            
        except Exception as e:
            logger.warning(f"AI title search generation failed: {e}, using basic mock")
            return self._basic_title_mock(property_address, property_id, seller_name)
    
    async def generate_inspection_report(
        self,
        property_address: str,
        property_id: str,
        property_type: Optional[str] = "single-family",
        year_built: Optional[int] = None,
        square_feet: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate a realistic inspection report using AI.
        
        Args:
            property_address: Property address
            property_id: Property identifier
            property_type: Type of property
            year_built: Year built (optional)
            square_feet: Square footage (optional)
        
        Returns:
            Dict containing inspection results
        """
        if not self.client:
            return self._basic_inspection_mock(property_address, property_id)
        
        try:
            prompt = f"""Generate a realistic home inspection report for a real estate property.

Property Address: {property_address}
Property Type: {property_type}
Year Built: {year_built or "Unknown"}
Square Feet: {square_feet or "Unknown"}

Generate a JSON response with the following structure:
{{
    "property_address": "{property_address}",
    "inspection_date": "{datetime.utcnow().isoformat()}",
    "inspector_name": "Realistic inspector name",
    "inspector_license": "INS-XXXXX",
    "inspector_company": "Demo Inspection Services LLC",
    "areas_inspected": [
        {{
            "area": "foundation",
            "condition": "excellent" or "good" or "fair" or "poor",
            "notes": "Realistic inspection notes"
        }},
        {{
            "area": "roof",
            "condition": "excellent" or "good" or "fair" or "poor",
            "notes": "Realistic inspection notes"
        }},
        {{
            "area": "electrical",
            "condition": "excellent" or "good" or "fair" or "poor",
            "notes": "Realistic inspection notes"
        }},
        {{
            "area": "plumbing",
            "condition": "excellent" or "good" or "fair" or "poor",
            "notes": "Realistic inspection notes"
        }},
        {{
            "area": "hvac",
            "condition": "excellent" or "good" or "fair" or "poor",
            "notes": "Realistic inspection notes"
        }},
        {{
            "area": "interior",
            "condition": "excellent" or "good" or "fair" or "poor",
            "notes": "Realistic inspection notes"
        }},
        {{
            "area": "exterior",
            "condition": "excellent" or "good" or "fair" or "poor",
            "notes": "Realistic inspection notes"
        }}
    ],
    "has_major_issues": false or true,
    "major_issues": ["List of major issues if has_major_issues is true, otherwise empty array"],
    "minor_issues": [
        {{
            "area": "Area name",
            "issue": "Description of minor issue",
            "severity": "low" or "medium",
            "recommendation": "What should be done"
        }}
    ],
    "overall_condition": "excellent" or "good" or "fair" or "poor",
    "summary": "Brief overall summary of property condition"
}}

Make it realistic. Most properties should be in "good" condition with minor issues. Only occasionally include major issues.
Return ONLY valid JSON, no markdown formatting."""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a professional home inspector. Generate realistic inspection reports in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"Generated AI inspection report for {property_address}")
            return result
            
        except Exception as e:
            logger.warning(f"AI inspection generation failed: {e}, using basic mock")
            return self._basic_inspection_mock(property_address, property_id)
    
    async def generate_appraisal_report(
        self,
        property_address: str,
        property_id: str,
        purchase_price: Decimal,
        property_type: Optional[str] = "single-family",
        bedrooms: Optional[int] = None,
        bathrooms: Optional[float] = None,
        square_feet: Optional[int] = None,
        year_built: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate a realistic appraisal report using AI.
        
        Args:
            property_address: Property address
            property_id: Property identifier
            purchase_price: Purchase price
            property_type: Type of property
            bedrooms: Number of bedrooms
            bathrooms: Number of bathrooms
            square_feet: Square footage
            year_built: Year built
        
        Returns:
            Dict containing appraisal results
        """
        if not self.client:
            return self._basic_appraisal_mock(property_address, property_id, purchase_price)
        
        try:
            # Generate appraised value (usually within 5% of purchase price)
            import random
            variance = random.uniform(-0.05, 0.05)
            appraised_value = float(purchase_price) * (1 + variance)
            
            prompt = f"""Generate a realistic property appraisal report.

Property Address: {property_address}
Purchase Price: ${purchase_price:,.2f}
Property Type: {property_type}
Bedrooms: {bedrooms or "Unknown"}
Bathrooms: {bathrooms or "Unknown"}
Square Feet: {square_feet or "Unknown"}
Year Built: {year_built or "Unknown"}

Appraised Value: ${appraised_value:,.2f}

Generate a JSON response with the following structure:
{{
    "property_address": "{property_address}",
    "appraisal_date": "{datetime.utcnow().isoformat()}",
    "appraiser_name": "Realistic appraiser name",
    "appraiser_license": "APP-XXXXX",
    "appraiser_company": "Demo Appraisal Services LLC",
    "appraised_value": {appraised_value},
    "purchase_price": {float(purchase_price)},
    "appraisal_method": "sales_comparison",
    "property_characteristics": {{
        "square_feet": {square_feet or 2000},
        "bedrooms": {bedrooms or 3},
        "bathrooms": {bathrooms or 2.0},
        "year_built": {year_built or 1990},
        "lot_size": "Realistic lot size",
        "property_type": "{property_type}"
    }},
    "comparable_properties": [
        {{
            "address": "Similar property address 1",
            "sale_price": "Price within 10% of appraised value",
            "sale_date": "Date within last 6 months",
            "square_feet": "Similar square footage",
            "bedrooms": "Similar bedrooms",
            "bathrooms": "Similar bathrooms",
            "distance": "Within 1 mile"
        }},
        {{
            "address": "Similar property address 2",
            "sale_price": "Price within 10% of appraised value",
            "sale_date": "Date within last 6 months",
            "square_feet": "Similar square footage",
            "bedrooms": "Similar bedrooms",
            "bathrooms": "Similar bathrooms",
            "distance": "Within 1 mile"
        }},
        {{
            "address": "Similar property address 3",
            "sale_price": "Price within 10% of appraised value",
            "sale_date": "Date within last 6 months",
            "square_feet": "Similar square footage",
            "bedrooms": "Similar bedrooms",
            "bathrooms": "Similar bathrooms",
            "distance": "Within 1 mile"
        }}
    ],
    "value_adjustments": {{
        "location": "Neutral or positive adjustment",
        "condition": "Neutral or positive adjustment",
        "features": "Neutral or positive adjustment"
    }},
    "appraisal_notes": "Brief notes about the appraisal",
    "loan_to_value_ratio": {{
        "ltv": "Calculate based on appraised value and typical loan amount",
        "status": "acceptable" or "needs_review"
    }}
}}

Make it realistic. Appraised value should be close to purchase price (within 5%). Comparables should be similar properties.
Return ONLY valid JSON, no markdown formatting."""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a certified property appraiser. Generate realistic appraisal reports in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            # Ensure appraised_value matches
            result["appraised_value"] = appraised_value
            logger.info(f"Generated AI appraisal report for {property_address}")
            return result
            
        except Exception as e:
            logger.warning(f"AI appraisal generation failed: {e}, using basic mock")
            return self._basic_appraisal_mock(property_address, property_id, purchase_price)
    
    async def generate_lending_verification(
        self,
        property_address: str,
        loan_amount: Decimal,
        purchase_price: Decimal,
        down_payment: Decimal,
        borrower_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate realistic lending verification using AI.
        
        Args:
            property_address: Property address
            loan_amount: Loan amount
            purchase_price: Purchase price
            down_payment: Down payment amount
            borrower_name: Borrower name (optional)
        
        Returns:
            Dict containing lending verification results
        """
        if not self.client:
            return self._basic_lending_mock(loan_amount, purchase_price, down_payment)
        
        try:
            down_payment_percent = float((down_payment / purchase_price) * 100)
            monthly_payment = float(loan_amount * Decimal("0.00632"))  # Approximate P&I at 6.5%
            
            prompt = f"""Generate a realistic loan verification report.

Property Address: {property_address}
Loan Amount: ${loan_amount:,.2f}
Purchase Price: ${purchase_price:,.2f}
Down Payment: ${down_payment:,.2f} ({down_payment_percent:.1f}%)
Borrower: {borrower_name or "Buyer"}

Generate a JSON response with the following structure:
{{
    "lender_name": "Realistic mortgage lender name",
    "lender_nmls": "NMLS-XXXXXX",
    "loan_officer_name": "Realistic loan officer name",
    "loan_officer_contact": "email@lender.com",
    "loan_officer_phone": "Realistic phone number",
    "loan_approved": true,
    "approval_date": "{datetime.utcnow().isoformat()}",
    "loan_amount": {float(loan_amount)},
    "purchase_price": {float(purchase_price)},
    "down_payment": {float(down_payment)},
    "down_payment_percent": {down_payment_percent},
    "loan_type": "conventional" or "fha" or "va",
    "interest_rate": "Realistic rate between 6.0% and 7.5%",
    "loan_term_years": 30,
    "monthly_payment": {monthly_payment},
    "estimated_closing_costs": "3% of purchase price",
    "underwriting_complete": true,
    "credit_score_required": 620,
    "credit_score_verified": true,
    "income_verified": true,
    "employment_verified": true,
    "debt_to_income_ratio": "Realistic DTI between 30% and 40%",
    "appraisal_required": true,
    "appraisal_received": true,
    "title_insurance_required": true,
    "conditions": [],
    "contingencies": [
        "Property must appraise at or above purchase price",
        "Clear title must be obtained",
        "Homeowners insurance must be in place at closing"
    ],
    "loan_estimate_provided": true,
    "closing_disclosure_pending": true,
    "estimated_closing_date": "Date 2-4 weeks from now",
    "loan_commitment_letter": "https://documents.example.com/lending/commitment-letter.pdf"
}}

Make it realistic. Loan should be approved. All verifications should be complete.
Return ONLY valid JSON, no markdown formatting."""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a mortgage loan processor. Generate realistic loan verification reports in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            # Ensure numeric values match
            result["loan_amount"] = float(loan_amount)
            result["purchase_price"] = float(purchase_price)
            result["down_payment"] = float(down_payment)
            result["down_payment_percent"] = down_payment_percent
            result["monthly_payment"] = monthly_payment
            
            logger.info(f"Generated AI lending verification for {property_address}")
            return result
            
        except Exception as e:
            logger.warning(f"AI lending verification generation failed: {e}, using basic mock")
            return self._basic_lending_mock(loan_amount, purchase_price, down_payment)
    
    # Basic fallback mocks (if OpenAI not available)
    def _basic_title_mock(self, property_address: str, property_id: str, seller_name: Optional[str]) -> Dict[str, Any]:
        """Basic title search mock (fallback)."""
        return {
            "property_address": property_address,
            "current_owner": seller_name or "Current Owner",
            "chain_of_title": [
                {
                    "owner": seller_name or "Current Owner",
                    "date_acquired": (datetime.utcnow() - timedelta(days=1825)).strftime("%Y-%m-%d"),
                    "deed_type": "Warranty Deed"
                }
            ],
            "liens_and_encumbrances": [],
            "has_issues": False,
            "issues": [],
            "title_insurance_available": True,
            "search_date": datetime.utcnow().isoformat(),
            "searcher": "Demo Title Search Agent",
            "title_company": "Demo Title Company LLC"
        }
    
    def _basic_inspection_mock(self, property_address: str, property_id: str) -> Dict[str, Any]:
        """Basic inspection mock (fallback)."""
        return {
            "property_address": property_address,
            "inspection_date": datetime.utcnow().isoformat(),
            "inspector_name": "John Smith",
            "inspector_license": "INS-12345",
            "inspector_company": "Demo Inspection Services LLC",
            "areas_inspected": [
                {"area": "foundation", "condition": "good", "notes": "No visible issues"},
                {"area": "roof", "condition": "good", "notes": "Shingles in good condition"},
                {"area": "electrical", "condition": "good", "notes": "Updated panel"},
                {"area": "plumbing", "condition": "fair", "notes": "Minor maintenance needed"},
                {"area": "hvac", "condition": "good", "notes": "System functioning properly"},
                {"area": "interior", "condition": "good", "notes": "Well maintained"},
                {"area": "exterior", "condition": "good", "notes": "Good condition"}
            ],
            "has_major_issues": False,
            "major_issues": [],
            "minor_issues": [
                {"area": "plumbing", "issue": "Minor leak under sink", "severity": "low", "recommendation": "Repair recommended"}
            ],
            "overall_condition": "good",
            "summary": "Property is in good condition with minor maintenance items"
        }
    
    def _basic_appraisal_mock(self, property_address: str, property_id: str, purchase_price: Decimal) -> Dict[str, Any]:
        """Basic appraisal mock (fallback)."""
        appraised_value = float(purchase_price) * 1.02  # 2% above purchase price
        return {
            "property_address": property_address,
            "appraisal_date": datetime.utcnow().isoformat(),
            "appraiser_name": "Jane Doe",
            "appraiser_license": "APP-67890",
            "appraiser_company": "Demo Appraisal Services LLC",
            "appraised_value": appraised_value,
            "purchase_price": float(purchase_price),
            "appraisal_method": "sales_comparison",
            "property_characteristics": {
                "square_feet": 2000,
                "bedrooms": 3,
                "bathrooms": 2.0,
                "year_built": 1990,
                "lot_size": "0.25 acres",
                "property_type": "single-family"
            },
            "comparable_properties": [
                {
                    "address": "123 Similar St",
                    "sale_price": appraised_value * 0.98,
                    "sale_date": (datetime.utcnow() - timedelta(days=90)).strftime("%Y-%m-%d"),
                    "square_feet": 1950,
                    "bedrooms": 3,
                    "bathrooms": 2.0,
                    "distance": "0.5 miles"
                }
            ],
            "appraisal_notes": "Property appraises at or above purchase price",
            "loan_to_value_ratio": {"ltv": 80.0, "status": "acceptable"}
        }
    
    def _basic_lending_mock(self, loan_amount: Decimal, purchase_price: Decimal, down_payment: Decimal) -> Dict[str, Any]:
        """Basic lending mock (fallback)."""
        return {
            "lender_name": "Demo Mortgage Company",
            "lender_nmls": "NMLS-123456",
            "loan_officer_name": "Robert Johnson",
            "loan_officer_contact": "robert@demomortgage.com",
            "loan_officer_phone": "555-0123",
            "loan_approved": True,
            "approval_date": datetime.utcnow().isoformat(),
            "loan_amount": float(loan_amount),
            "purchase_price": float(purchase_price),
            "down_payment": float(down_payment),
            "down_payment_percent": float((down_payment / purchase_price) * 100),
            "loan_type": "conventional",
            "interest_rate": 6.5,
            "loan_term_years": 30,
            "monthly_payment": float(loan_amount * Decimal("0.00632")),
            "estimated_closing_costs": float(purchase_price * Decimal("0.03")),
            "underwriting_complete": True,
            "credit_score_required": 620,
            "credit_score_verified": True,
            "income_verified": True,
            "employment_verified": True,
            "debt_to_income_ratio": 35.5,
            "appraisal_required": True,
            "appraisal_received": True,
            "title_insurance_required": True,
            "conditions": [],
            "contingencies": [
                "Property must appraise at or above purchase price",
                "Clear title must be obtained",
                "Homeowners insurance must be in place at closing"
            ],
            "loan_estimate_provided": True,
            "closing_disclosure_pending": True,
            "estimated_closing_date": (datetime.utcnow() + timedelta(days=21)).isoformat(),
            "loan_commitment_letter": "https://documents.example.com/lending/commitment-letter.pdf"
        }


# Global instance
ai_mock_service = AIMockVerificationService()

