"""Integration tests for property search tool."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from models.user import User
from models.search_history import SearchHistory


class TestPropertySearchIntegration:
    """Integration tests for property search endpoint."""
    
    @pytest.mark.asyncio
    async def test_search_with_mocked_rentcast(
        self,
        client,
        test_db,
        sample_search_request,
        mock_rentcast_listings
    ):
        """Test property search with mocked RentCast API."""
        # Create test user
        user = User(
            id=sample_search_request["user_id"],
            phone_number="+1234567890",
            email="test@example.com",
            name="Test User"
        )
        test_db.add(user)
        test_db.commit()
        
        # Mock RentCast client
        with patch("api.tools.search.RentCastClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.search_listings.return_value = mock_rentcast_listings
            mock_client_class.return_value = mock_client
            
            # Mock OpenAI for summary generation
            with patch("api.tools.search.openai.OpenAI") as mock_openai_class:
                mock_openai = MagicMock()
                mock_response = MagicMock()
                mock_response.choices = [
                    MagicMock(message=MagicMock(content="Charming 3-bed colonial with updated kitchen"))
                ]
                mock_openai.chat.completions.create.return_value = mock_response
                mock_openai_class.return_value = mock_openai
                
                # Mock cache client
                with patch("api.tools.search.cache_client") as mock_cache:
                    mock_cache.get.return_value = None  # Cache miss
                    mock_cache.set.return_value = True
                    
                    # Make request
                    response = client.post("/tools/search", json=sample_search_request)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "properties" in data
        assert "total_found" in data
        assert "cached" in data
        
        # Should return max 3 properties
        assert len(data["properties"]) <= 3
        assert len(data["properties"]) > 0
        
        # Check property structure
        first_property = data["properties"][0]
        assert "address" in first_property
        assert "price" in first_property
        assert "beds" in first_property
        assert "baths" in first_property
        assert "summary" in first_property
        assert "property_id" in first_property
        
        # Verify search history was saved
        search_history = test_db.query(SearchHistory).filter_by(
            user_id=sample_search_request["user_id"]
        ).first()
        assert search_history is not None
        assert search_history.location == sample_search_request["location"]
        assert search_history.max_price == sample_search_request["max_price"]
    
    @pytest.mark.asyncio
    async def test_search_with_cache_hit(
        self,
        client,
        test_db,
        sample_search_request
    ):
        """Test property search returns cached results."""
        # Create test user
        user = User(
            id=sample_search_request["user_id"],
            phone_number="+1234567890",
            email="test@example.com"
        )
        test_db.add(user)
        test_db.commit()
        
        # Mock cached data
        cached_data = {
            "properties": [
                {
                    "address": "123 Main St, Baltimore, MD 21201",
                    "price": 385000,
                    "beds": 3,
                    "baths": 2.5,
                    "sqft": 1800,
                    "summary": "Charming colonial",
                    "listing_url": "https://example.com/listing",
                    "property_id": "prop_001"
                }
            ],
            "total_found": 10
        }
        
        with patch("api.tools.search.cache_client") as mock_cache:
            mock_cache.get.return_value = cached_data
            
            # Make request
            response = client.post("/tools/search", json=sample_search_request)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        assert data["cached"] is True
        assert len(data["properties"]) == 1
        assert data["total_found"] == 10
        assert data["properties"][0]["address"] == "123 Main St, Baltimore, MD 21201"
    
    @pytest.mark.asyncio
    async def test_search_with_api_failure_graceful_degradation(
        self,
        client,
        test_db,
        sample_search_request
    ):
        """Test search handles RentCast API failure gracefully."""
        # Create test user
        user = User(
            id=sample_search_request["user_id"],
            phone_number="+1234567890"
        )
        test_db.add(user)
        test_db.commit()
        
        # Mock RentCast client to raise error
        with patch("api.tools.search.RentCastClient") as mock_client_class:
            mock_client = AsyncMock()
            from services.rentcast_client import RentCastAPIError
            mock_client.search_listings.side_effect = RentCastAPIError("API unavailable")
            mock_client_class.return_value = mock_client
            
            # Mock cache to return None (no fallback)
            with patch("api.tools.search.cache_client") as mock_cache:
                mock_cache.get.return_value = None
                
                # Make request
                response = client.post("/tools/search", json=sample_search_request)
        
        # Should return 503 Service Unavailable
        assert response.status_code == 503
        assert "temporarily unavailable" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_search_filters_by_criteria(
        self,
        client,
        test_db,
        mock_rentcast_listings
    ):
        """Test search properly filters and sorts results."""
        # Create test user
        user = User(
            id="test_user_123",
            phone_number="+1234567890"
        )
        test_db.add(user)
        test_db.commit()
        
        request_data = {
            "location": "Baltimore, MD",
            "max_price": 390000,
            "min_beds": 3,
            "min_baths": 2,
            "user_id": "test_user_123"
        }
        
        with patch("api.tools.search.RentCastClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.search_listings.return_value = mock_rentcast_listings
            mock_client_class.return_value = mock_client
            
            with patch("api.tools.search.openai.OpenAI") as mock_openai_class:
                mock_openai = MagicMock()
                mock_response = MagicMock()
                mock_response.choices = [
                    MagicMock(message=MagicMock(content="Great home"))
                ]
                mock_openai.chat.completions.create.return_value = mock_response
                mock_openai_class.return_value = mock_openai
                
                with patch("api.tools.search.cache_client") as mock_cache:
                    mock_cache.get.return_value = None
                    mock_cache.set.return_value = True
                    
                    response = client.post("/tools/search", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned properties should meet criteria
        for prop in data["properties"]:
            assert prop["beds"] >= request_data["min_beds"]
            assert prop["baths"] >= request_data["min_baths"]
    
    def test_search_invalid_location(self, client, test_db):
        """Test search with invalid location format."""
        user = User(id="test_user_123", phone_number="+1234567890")
        test_db.add(user)
        test_db.commit()
        
        request_data = {
            "location": "",  # Empty location
            "max_price": 400000,
            "user_id": "test_user_123"
        }
        
        response = client.post("/tools/search", json=request_data)
        
        # Should return validation error
        assert response.status_code == 422
    
    def test_search_price_validation(self, client, test_db):
        """Test search validates price constraints."""
        user = User(id="test_user_123", phone_number="+1234567890")
        test_db.add(user)
        test_db.commit()
        
        request_data = {
            "location": "Baltimore, MD",
            "min_price": 500000,
            "max_price": 400000,  # max < min
            "user_id": "test_user_123"
        }
        
        response = client.post("/tools/search", json=request_data)
        
        # Should return validation error
        assert response.status_code == 422
