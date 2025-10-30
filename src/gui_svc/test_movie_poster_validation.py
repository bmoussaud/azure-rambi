#!/usr/bin/env python3
"""Unit tests for the movie poster client validation functionality"""

import unittest
from unittest.mock import patch, Mock
import json
import os
import sys

# Add the src directory to the path so we can import the modules
sys.path.insert(0, '/workspaces/azure-rambi/src/gui_svc')

from movie_poster_client import MoviePosterClient


class TestMoviePosterClientValidation(unittest.TestCase):
    """Test cases for the movie poster client validation functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = MoviePosterClient(
            endpoint="http://test-endpoint",
            api_key="test-key"
        )

    @patch('movie_poster_client.requests.get')
    @patch('movie_poster_client.os.getenv')
    def test_get_validation_scores_success(self, mock_getenv, mock_get):
        """Test successful retrieval of validation scores"""
        # Mock environment variable
        mock_getenv.return_value = "http://test-agent-endpoint"
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "test_movie_123",
            "overall_score": 85,
            "detailed_scores": [
                {
                    "category": "Design & Aesthetics",
                    "score": 90,
                    "reasoning": "Great visual design"
                }
            ],
            "recommendations": ["Add more colors"],
            "validation_timestamp": "2023-11-05T12:15:00Z"
        }
        mock_get.return_value = mock_response
        
        # Test the method
        result = self.client.get_validation_scores("test_movie_123")
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result["overall_score"], 85)
        self.assertEqual(len(result["detailed_scores"]), 1)
        self.assertEqual(result["detailed_scores"][0]["category"], "Design & Aesthetics")
        
        # Verify the correct endpoint was called
        mock_get.assert_called_once_with(
            "http://test-agent-endpoint/validations/test_movie_123",
            timeout=30
        )

    @patch('movie_poster_client.requests.get')
    @patch('movie_poster_client.os.getenv')
    def test_get_validation_scores_not_found(self, mock_getenv, mock_get):
        """Test handling of 404 response (no validation found)"""
        mock_getenv.return_value = "http://test-agent-endpoint"
        
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        result = self.client.get_validation_scores("nonexistent_movie")
        
        self.assertIsNone(result)

    @patch('movie_poster_client.requests.get')
    @patch('movie_poster_client.os.getenv')
    def test_get_validation_scores_no_endpoint(self, mock_getenv, mock_get):
        """Test handling when MOVIE_POSTER_AGENT_ENDPOINT is not configured"""
        mock_getenv.return_value = None
        
        result = self.client.get_validation_scores("test_movie")
        
        self.assertIsNone(result)
        # Should not make any HTTP calls
        mock_get.assert_not_called()

    @patch('movie_poster_client.requests.get')
    @patch('movie_poster_client.os.getenv')
    def test_get_validation_scores_server_error(self, mock_getenv, mock_get):
        """Test handling of server errors"""
        mock_getenv.return_value = "http://test-agent-endpoint"
        
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response
        
        result = self.client.get_validation_scores("test_movie")
        
        self.assertIsNone(result)

    @patch('movie_poster_client.requests.get')
    @patch('movie_poster_client.os.getenv')
    def test_get_validation_scores_network_error(self, mock_getenv, mock_get):
        """Test handling of network errors"""
        mock_getenv.return_value = "http://test-agent-endpoint"
        
        # Simulate a network error
        mock_get.side_effect = Exception("Connection timeout")
        
        result = self.client.get_validation_scores("test_movie")
        
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()