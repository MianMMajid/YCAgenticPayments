"""Integration tests for risk analysis tool."""
import pytest
from unittest.mock import AsyncMock, patch

from models.user import User
from models.risk_analysis import RiskAnalysis


class TestRiskAnalysisIntegration:
    """Integration tests for risk analysis endpoint."""
    
    @pytest.mark.asyncio
    async def test_risk_analysis_with_mocked_apis(
        self,
        client,
        test_db,
        sample_risk_request,
        mock_rentcast_property_value,
        mock_fema_flood_data,
        mock_crime_data
    ):
        """Test risk analysis with all mocked external APIs."""
        # Create test user
        user = User(
            id=sample_risk_request["user_id"],
            phone_number="+1234567890",
            email="test@example.com"
        )
        test_db.add(user)
        test_db.commit()
        
        # Mock all external API clients
        with patch("api.tools.analyze_risk.RentCastClient") as mock_rentcast_class:
            mock_rentcast = AsyncMock()
            mock_rentcast.get_property_value.return_value = mock_rentcast_property_value
            mock_rentcast_class.return_value = mock_rentcast
            
            with patch("api.tools.analyze_risk.FEMAClient") as mock_fema_class:
                mock_fema = AsyncMock()
                mock_fema.get_flood_zone.return_value = mock_fema_flood_data
                mock_fema_class.return_value = mock_fema
                
                with patch("api.tools.analyze_risk.CrimeClient") as mock_crime_class:
                    mock_crime = AsyncMock()
                    mock_crime.get_crime_score.return_value = mock_crime_data
                    mock_crime_class.return_value = mock_crime
                    
                    with patch("api.tools.analyze_risk.cache_client") as mock_cache:
                        mock_cache.get.return_value = None  # Cache miss
                        mock_cache.set.return_value = True
                        
                        # Make request
                        response = client.post("/tools/analyze-risk", json=sample_risk_request)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "flags" in data
        assert "overall_risk" in data
        assert "data_sources" in data
        
        # Should have multiple risk flags based on mock data
        assert len(data["flags"]) > 0
        
        # Check for expected flags
        flag_categories = [flag["category"] for flag in data["flags"]]
        
        # Should detect overpricing (list_price 385000 > estimated_value 350000 * 1.1)
        assert "pricing" in flag_categories
        
        # Should detect flood risk (zone AE)
        assert "flood" in flag_categories
        
        # Should detect tax gap (tax_assessment 200000 < list_price 385000 * 0.6)
        assert "tax" in flag_categories
        
        # Should detect crime risk (score 75 > 70)
        assert "crime" in flag_categories
        
        # Overall risk should be high (multiple high-severity flags)
        assert data["overall_risk"] == "high"
        
        # Verify risk analysis was saved to database
        risk_analysis = test_db.query(RiskAnalysis).filter_by(
            property_id=sample_risk_request["property_id"]
        ).first()
        assert risk_analysis is not None
        assert risk_analysis.overall_risk == "high"
        assert len(risk_analysis.flags) > 0
    
    @pytest.mark.asyncio
    async def test_risk_analysis_overpricing_detection(
        self,
        client,
        test_db
    ):
        """Test risk analysis correctly detects overpricing."""
        user = User(id="test_user_123", phone_number="+1234567890")
        test_db.add(user)
        test_db.commit()
        
        request_data = {
            "property_id": "prop_overpriced",
            "address": "456 Oak Ave, Baltimore, MD 21202",
            "list_price": 500000,  # Significantly overpriced
            "user_id": "test_user_123",
            "latitude": 39.2904,
            "longitude": -76.6122
        }
        
        # Mock RentCast with lower estimated value
        mock_value_data = {
            "estimated_value": 400000,  # 20% below list price
            "tax_assessment": 350000
        }
        
        with patch("api.tools.analyze_risk.RentCastClient") as mock_rentcast_class:
            mock_rentcast = AsyncMock()
            mock_rentcast.get_property_value.return_value = mock_value_data
            mock_rentcast_class.return_value = mock_rentcast
            
            with patch("api.tools.analyze_risk.FEMAClient") as mock_fema_class:
                mock_fema = AsyncMock()
                mock_fema.get_flood_zone.return_value = {"flood_zone": "X", "is_high_risk": False}
                mock_fema_class.return_value = mock_fema
                
                with patch("api.tools.analyze_risk.CrimeClient") as mock_crime_class:
                    mock_crime = AsyncMock()
                    mock_crime.get_crime_score.return_value = {"crime_score": 50, "crime_level": "medium"}
                    mock_crime_class.return_value = mock_crime
                    
                    with patch("api.tools.analyze_risk.cache_client") as mock_cache:
                        mock_cache.get.return_value = None
                        mock_cache.set.return_value = True
                        
                        response = client.post("/tools/analyze-risk", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have pricing flag
        pricing_flags = [f for f in data["flags"] if f["category"] == "pricing"]
        assert len(pricing_flags) > 0
        
        pricing_flag = pricing_flags[0]
        assert pricing_flag["severity"] == "high"
        assert "overpriced" in pricing_flag["message"].lower()
        assert "25" in pricing_flag["message"]  # 25% overpriced
    
    @pytest.mark.asyncio
    async def test_risk_analysis_flood_zone_detection(
        self,
        client,
        test_db
    ):
        """Test risk analysis correctly detects flood zones."""
        user = User(id="test_user_123", phone_number="+1234567890")
        test_db.add(user)
        test_db.commit()
        
        request_data = {
            "property_id": "prop_flood",
            "address": "789 River Rd, Baltimore, MD 21201",
            "list_price": 350000,
            "user_id": "test_user_123",
            "latitude": 39.2904,
            "longitude": -76.6122
        }
        
        # Mock FEMA with high-risk flood zone
        mock_flood_data = {
            "flood_zone": "AE",
            "is_high_risk": True,
            "description": "Special Flood Hazard Area"
        }
        
        with patch("api.tools.analyze_risk.RentCastClient") as mock_rentcast_class:
            mock_rentcast = AsyncMock()
            mock_rentcast.get_property_value.return_value = {
                "estimated_value": 350000,
                "tax_assessment": 300000
            }
            mock_rentcast_class.return_value = mock_rentcast
            
            with patch("api.tools.analyze_risk.FEMAClient") as mock_fema_class:
                mock_fema = AsyncMock()
                mock_fema.get_flood_zone.return_value = mock_flood_data
                mock_fema_class.return_value = mock_fema
                
                with patch("api.tools.analyze_risk.CrimeClient") as mock_crime_class:
                    mock_crime = AsyncMock()
                    mock_crime.get_crime_score.return_value = {"crime_score": 40}
                    mock_crime_class.return_value = mock_crime
                    
                    with patch("api.tools.analyze_risk.cache_client") as mock_cache:
                        mock_cache.get.return_value = None
                        mock_cache.set.return_value = True
                        
                        response = client.post("/tools/analyze-risk", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have flood flag
        flood_flags = [f for f in data["flags"] if f["category"] == "flood"]
        assert len(flood_flags) > 0
        
        flood_flag = flood_flags[0]
        assert flood_flag["severity"] == "high"
        assert "flood insurance" in flood_flag["message"].lower()
        assert "AE" in flood_flag["message"]
    
    @pytest.mark.asyncio
    async def test_risk_analysis_with_cache_hit(
        self,
        client,
        test_db,
        sample_risk_request
    ):
        """Test risk analysis returns cached results."""
        user = User(
            id=sample_risk_request["user_id"],
            phone_number="+1234567890"
        )
        test_db.add(user)
        test_db.commit()
        
        # Mock cached data
        cached_data = {
            "flags": [
                {
                    "severity": "high",
                    "category": "pricing",
                    "message": "Property is overpriced by 10%",
                    "details": {"difference_percent": 10}
                }
            ],
            "overall_risk": "high",
            "data_sources": {
                "rentcast": True,
                "fema": True,
                "crime": True
            }
        }
        
        with patch("api.tools.analyze_risk.cache_client") as mock_cache:
            mock_cache.get.return_value = cached_data
            
            response = client.post("/tools/analyze-risk", json=sample_risk_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["flags"]) == 1
        assert data["flags"][0]["category"] == "pricing"
        assert data["overall_risk"] == "high"
    
    @pytest.mark.asyncio
    async def test_risk_analysis_graceful_degradation(
        self,
        client,
        test_db
    ):
        """Test risk analysis handles partial API failures gracefully."""
        user = User(id="test_user_123", phone_number="+1234567890")
        test_db.add(user)
        test_db.commit()
        
        request_data = {
            "property_id": "prop_partial",
            "address": "100 Test St, Baltimore, MD 21201",
            "list_price": 400000,
            "user_id": "test_user_123",
            "latitude": 39.2904,
            "longitude": -76.6122
        }
        
        # Mock RentCast success, but FEMA and Crime fail
        with patch("api.tools.analyze_risk.RentCastClient") as mock_rentcast_class:
            mock_rentcast = AsyncMock()
            mock_rentcast.get_property_value.return_value = {
                "estimated_value": 380000,
                "tax_assessment": 350000
            }
            mock_rentcast_class.return_value = mock_rentcast
            
            with patch("api.tools.analyze_risk.FEMAClient") as mock_fema_class:
                mock_fema = AsyncMock()
                from services.fema_client import FEMAAPIError
                mock_fema.get_flood_zone.side_effect = FEMAAPIError("Service unavailable")
                mock_fema_class.return_value = mock_fema
                
                with patch("api.tools.analyze_risk.CrimeClient") as mock_crime_class:
                    mock_crime = AsyncMock()
                    from services.crime_client import CrimeAPIError
                    mock_crime.get_crime_score.side_effect = CrimeAPIError("Service unavailable")
                    mock_crime_class.return_value = mock_crime
                    
                    with patch("api.tools.analyze_risk.cache_client") as mock_cache:
                        mock_cache.get.return_value = None
                        mock_cache.set.return_value = True
                        
                        response = client.post("/tools/analyze-risk", json=request_data)
        
        # Should still succeed with partial data
        assert response.status_code == 200
        data = response.json()
        
        # Should indicate which data sources were unavailable
        assert data["data_sources"]["rentcast"] is True
        assert data["data_sources"]["fema"] is False
        assert data["data_sources"]["crime"] is False
        
        # Should still perform analysis with available data
        assert "flags" in data
        assert "overall_risk" in data
    
    @pytest.mark.asyncio
    async def test_risk_analysis_sorts_flags_by_severity(
        self,
        client,
        test_db
    ):
        """Test risk flags are sorted by severity (high first)."""
        user = User(id="test_user_123", phone_number="+1234567890")
        test_db.add(user)
        test_db.commit()
        
        request_data = {
            "property_id": "prop_multi_risk",
            "address": "200 Risk St, Baltimore, MD 21201",
            "list_price": 500000,
            "user_id": "test_user_123",
            "latitude": 39.2904,
            "longitude": -76.6122
        }
        
        # Mock data that will generate multiple flags
        with patch("api.tools.analyze_risk.RentCastClient") as mock_rentcast_class:
            mock_rentcast = AsyncMock()
            mock_rentcast.get_property_value.return_value = {
                "estimated_value": 400000,  # Overpriced (high)
                "tax_assessment": 250000  # Tax gap (medium)
            }
            mock_rentcast_class.return_value = mock_rentcast
            
            with patch("api.tools.analyze_risk.FEMAClient") as mock_fema_class:
                mock_fema = AsyncMock()
                mock_fema.get_flood_zone.return_value = {
                    "flood_zone": "AE",  # High risk (high)
                    "is_high_risk": True
                }
                mock_fema_class.return_value = mock_fema
                
                with patch("api.tools.analyze_risk.CrimeClient") as mock_crime_class:
                    mock_crime = AsyncMock()
                    mock_crime.get_crime_score.return_value = {
                        "crime_score": 75  # High crime (medium)
                    }
                    mock_crime_class.return_value = mock_crime
                    
                    with patch("api.tools.analyze_risk.cache_client") as mock_cache:
                        mock_cache.get.return_value = None
                        mock_cache.set.return_value = True
                        
                        response = client.post("/tools/analyze-risk", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check flags are sorted by severity
        flags = data["flags"]
        assert len(flags) >= 2
        
        # First flags should be high severity
        high_severity_flags = [f for f in flags if f["severity"] == "high"]
        medium_severity_flags = [f for f in flags if f["severity"] == "medium"]
        
        # High severity flags should come before medium
        if high_severity_flags and medium_severity_flags:
            high_index = flags.index(high_severity_flags[0])
            medium_index = flags.index(medium_severity_flags[0])
            assert high_index < medium_index
