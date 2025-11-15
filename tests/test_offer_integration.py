"""Integration tests for offer generation tool."""
import pytest
from unittest.mock import AsyncMock, patch

from models.user import User
from models.offer import Offer


class TestOfferGenerationIntegration:
    """Integration tests for offer generation endpoint."""
    
    @pytest.mark.asyncio
    async def test_draft_offer_with_mocked_docusign(
        self,
        client,
        test_db,
        sample_offer_request,
        mock_docusign_envelope
    ):
        """Test offer generation with mocked Docusign API."""
        # Create test user
        user = User(
            id=sample_offer_request["user_id"],
            phone_number="+1234567890",
            email=sample_offer_request["user_email"],
            name=sample_offer_request["user_name"]
        )
        test_db.add(user)
        test_db.commit()
        
        # Mock Docusign client
        with patch("api.tools.draft_offer.DocusignClient") as mock_docusign_class:
            mock_docusign = AsyncMock()
            mock_docusign.create_envelope_from_template.return_value = mock_docusign_envelope
            mock_docusign_class.return_value = mock_docusign
            
            # Make request
            response = client.post("/tools/draft-offer", json=sample_offer_request)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert data["status"] == "sent"
        assert "message" in data
        assert "offer_id" in data
        assert "envelope_id" in data
        assert "signing_url" in data
        
        # Verify envelope details
        assert data["envelope_id"] == mock_docusign_envelope["envelope_id"]
        assert data["signing_url"] == mock_docusign_envelope["signing_url"]
        
        # Verify offer was saved to database
        offer = test_db.query(Offer).filter_by(
            envelope_id=mock_docusign_envelope["envelope_id"]
        ).first()
        assert offer is not None
        assert offer.property_id == sample_offer_request["property_id"]
        assert offer.offer_price == sample_offer_request["offer_price"]
        assert offer.status == "sent"
        assert offer.financing_type == sample_offer_request["financing_type"]
        assert set(offer.contingencies) == set(sample_offer_request["contingencies"])
    
    @pytest.mark.asyncio
    async def test_draft_offer_state_template_mapping(
        self,
        client,
        test_db,
        mock_docusign_envelope
    ):
        """Test offer uses correct state-specific template."""
        user = User(id="test_user_123", phone_number="+1234567890")
        test_db.add(user)
        test_db.commit()
        
        # Test different states
        test_cases = [
            ("123 Main St, Baltimore, MD 21201", "MD"),
            ("456 Oak Ave, Arlington, VA 22201", "VA"),
            ("789 Penn Ave, Washington, DC 20001", "DC"),
        ]
        
        for address, expected_state in test_cases:
            request_data = {
                "property_id": f"prop_{expected_state}",
                "address": address,
                "offer_price": 350000,
                "closing_days": 30,
                "financing_type": "conventional",
                "contingencies": ["inspection"],
                "user_id": "test_user_123",
                "user_email": "buyer@example.com",
                "user_name": "John Doe"
            }
            
            with patch("api.tools.draft_offer.DocusignClient") as mock_docusign_class:
                mock_docusign = AsyncMock()
                mock_docusign.create_envelope_from_template.return_value = mock_docusign_envelope
                mock_docusign_class.return_value = mock_docusign
                
                response = client.post("/tools/draft-offer", json=request_data)
            
            assert response.status_code == 200
            
            # Verify correct template was used
            offer = test_db.query(Offer).filter_by(
                property_id=f"prop_{expected_state}"
            ).first()
            assert offer is not None
            assert expected_state.lower() in offer.template_id.lower()
    
    @pytest.mark.asyncio
    async def test_draft_offer_unsupported_state(
        self,
        client,
        test_db
    ):
        """Test offer generation fails gracefully for unsupported states."""
        user = User(id="test_user_123", phone_number="+1234567890")
        test_db.add(user)
        test_db.commit()
        
        request_data = {
            "property_id": "prop_unsupported",
            "address": "123 Main St, Honolulu, HI 96801",  # Hawaii not supported
            "offer_price": 500000,
            "closing_days": 30,
            "financing_type": "conventional",
            "contingencies": [],
            "user_id": "test_user_123",
            "user_email": "buyer@example.com",
            "user_name": "John Doe"
        }
        
        response = client.post("/tools/draft-offer", json=request_data)
        
        # Should return 400 Bad Request
        assert response.status_code == 400
        assert "not yet supported" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_draft_offer_contingencies_mapping(
        self,
        client,
        test_db,
        mock_docusign_envelope
    ):
        """Test offer correctly maps contingencies to contract fields."""
        user = User(id="test_user_123", phone_number="+1234567890")
        test_db.add(user)
        test_db.commit()
        
        request_data = {
            "property_id": "prop_contingencies",
            "address": "123 Main St, Baltimore, MD 21201",
            "offer_price": 350000,
            "closing_days": 30,
            "financing_type": "conventional",
            "contingencies": ["inspection", "appraisal", "financing"],
            "user_id": "test_user_123",
            "user_email": "buyer@example.com",
            "user_name": "John Doe"
        }
        
        with patch("api.tools.draft_offer.DocusignClient") as mock_docusign_class:
            mock_docusign = AsyncMock()
            mock_docusign.create_envelope_from_template.return_value = mock_docusign_envelope
            mock_docusign_class.return_value = mock_docusign
            
            response = client.post("/tools/draft-offer", json=request_data)
        
        assert response.status_code == 200
        
        # Verify Docusign was called with correct tabs
        call_args = mock_docusign.create_envelope_from_template.call_args
        tabs = call_args.kwargs["tabs"]
        
        # Check checkbox tabs for contingencies
        checkbox_tabs = tabs["checkboxTabs"]
        inspection_tab = next(t for t in checkbox_tabs if t["tabLabel"] == "InspectionContingency")
        appraisal_tab = next(t for t in checkbox_tabs if t["tabLabel"] == "AppraisalContingency")
        financing_tab = next(t for t in checkbox_tabs if t["tabLabel"] == "FinancingContingency")
        
        assert inspection_tab["selected"] is True
        assert appraisal_tab["selected"] is True
        assert financing_tab["selected"] is True
    
    @pytest.mark.asyncio
    async def test_draft_offer_price_formatting(
        self,
        client,
        test_db,
        mock_docusign_envelope
    ):
        """Test offer formats prices correctly for contract."""
        user = User(id="test_user_123", phone_number="+1234567890")
        test_db.add(user)
        test_db.commit()
        
        request_data = {
            "property_id": "prop_price_format",
            "address": "123 Main St, Baltimore, MD 21201",
            "offer_price": 385000,
            "list_price": 400000,
            "closing_days": 30,
            "financing_type": "cash",
            "contingencies": [],
            "earnest_money": 10000,
            "user_id": "test_user_123",
            "user_email": "buyer@example.com",
            "user_name": "John Doe"
        }
        
        with patch("api.tools.draft_offer.DocusignClient") as mock_docusign_class:
            mock_docusign = AsyncMock()
            mock_docusign.create_envelope_from_template.return_value = mock_docusign_envelope
            mock_docusign_class.return_value = mock_docusign
            
            response = client.post("/tools/draft-offer", json=request_data)
        
        assert response.status_code == 200
        
        # Verify Docusign was called with formatted prices
        call_args = mock_docusign.create_envelope_from_template.call_args
        tabs = call_args.kwargs["tabs"]
        
        text_tabs = tabs["textTabs"]
        price_tab = next(t for t in text_tabs if t["tabLabel"] == "PurchasePrice")
        earnest_tab = next(t for t in text_tabs if t["tabLabel"] == "EarnestMoney")
        
        # Prices should be formatted with commas and dollar sign
        assert price_tab["value"] == "$385,000"
        assert earnest_tab["value"] == "$10,000"
    
    @pytest.mark.asyncio
    async def test_draft_offer_closing_date_calculation(
        self,
        client,
        test_db,
        mock_docusign_envelope
    ):
        """Test offer calculates closing date correctly."""
        user = User(id="test_user_123", phone_number="+1234567890")
        test_db.add(user)
        test_db.commit()
        
        request_data = {
            "property_id": "prop_closing",
            "address": "123 Main St, Baltimore, MD 21201",
            "offer_price": 350000,
            "closing_days": 45,  # 45 days from now
            "financing_type": "conventional",
            "contingencies": [],
            "user_id": "test_user_123",
            "user_email": "buyer@example.com",
            "user_name": "John Doe"
        }
        
        with patch("api.tools.draft_offer.DocusignClient") as mock_docusign_class:
            mock_docusign = AsyncMock()
            mock_docusign.create_envelope_from_template.return_value = mock_docusign_envelope
            mock_docusign_class.return_value = mock_docusign
            
            response = client.post("/tools/draft-offer", json=request_data)
        
        assert response.status_code == 200
        
        # Verify closing date was calculated and stored
        offer = test_db.query(Offer).filter_by(
            property_id="prop_closing"
        ).first()
        assert offer is not None
        assert offer.closing_date is not None
        assert offer.closing_days == 45
        
        # Closing date should be in MM/DD/YYYY format
        import re
        date_pattern = r'^\d{2}/\d{2}/\d{4}$'
        assert re.match(date_pattern, offer.closing_date)
    
    @pytest.mark.asyncio
    async def test_draft_offer_docusign_api_failure(
        self,
        client,
        test_db
    ):
        """Test offer generation handles Docusign API failures."""
        user = User(id="test_user_123", phone_number="+1234567890")
        test_db.add(user)
        test_db.commit()
        
        request_data = {
            "property_id": "prop_fail",
            "address": "123 Main St, Baltimore, MD 21201",
            "offer_price": 350000,
            "closing_days": 30,
            "financing_type": "conventional",
            "contingencies": [],
            "user_id": "test_user_123",
            "user_email": "buyer@example.com",
            "user_name": "John Doe"
        }
        
        # Mock Docusign to raise error
        with patch("api.tools.draft_offer.DocusignClient") as mock_docusign_class:
            mock_docusign = AsyncMock()
            from services.docusign_client import DocusignAPIError
            mock_docusign.create_envelope_from_template.side_effect = DocusignAPIError(
                "Authentication failed"
            )
            mock_docusign_class.return_value = mock_docusign
            
            response = client.post("/tools/draft-offer", json=request_data)
        
        # Should return 503 Service Unavailable
        assert response.status_code == 503
        assert "failed to create offer document" in response.json()["detail"].lower()
    
    def test_draft_offer_validation(self, client, test_db):
        """Test offer request validation."""
        user = User(id="test_user_123", phone_number="+1234567890")
        test_db.add(user)
        test_db.commit()
        
        # Test invalid financing type
        request_data = {
            "property_id": "prop_invalid",
            "address": "123 Main St, Baltimore, MD 21201",
            "offer_price": 350000,
            "closing_days": 30,
            "financing_type": "invalid_type",  # Invalid
            "contingencies": [],
            "user_id": "test_user_123",
            "user_email": "buyer@example.com",
            "user_name": "John Doe"
        }
        
        response = client.post("/tools/draft-offer", json=request_data)
        
        # Should return validation error
        assert response.status_code == 422
    
    def test_draft_offer_closing_days_validation(self, client, test_db):
        """Test closing days must be within valid range."""
        user = User(id="test_user_123", phone_number="+1234567890")
        test_db.add(user)
        test_db.commit()
        
        # Test closing days too short
        request_data = {
            "property_id": "prop_short_close",
            "address": "123 Main St, Baltimore, MD 21201",
            "offer_price": 350000,
            "closing_days": 5,  # Less than minimum of 7
            "financing_type": "cash",
            "contingencies": [],
            "user_id": "test_user_123",
            "user_email": "buyer@example.com",
            "user_name": "John Doe"
        }
        
        response = client.post("/tools/draft-offer", json=request_data)
        
        # Should return validation error
        assert response.status_code == 422
