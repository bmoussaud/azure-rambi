# Movie Gallery Validation Scores Feature

## Overview

This update enhances the Movie Gallery UI to display validation scores from the `movie_poster_agent_svc` for each generated movie. The feature provides both a quick overview score in the gallery cards and detailed scoring information in the movie detail modal.

## Changes Made

### 1. Backend Changes

#### movie_poster_client.py
- Added `get_validation_scores(movie_id)` method to fetch validation data from the movie_poster_agent_svc
- Handles various error scenarios gracefully (404, server errors, network timeouts)
- Uses the `MOVIE_POSTER_AGENT_ENDPOINT` environment variable for service communication

#### app.py
- Modified the `/gallery` route to fetch validation scores for each movie
- Integrated validation scores into the movie data passed to the template
- Added proper error handling and logging for the validation score retrieval

### 2. Infrastructure Changes

#### infra/modules/apps/gui-svc.bicep
- Added `MOVIE_POSTER_AGENT_ENDPOINT` environment variable to the GUI service container configuration
- Enables communication between GUI service and movie poster agent service

### 3. Frontend Changes

#### templates/gallery.html
- **Gallery Overview**: Added score badges showing the overall_score next to each movie title
- **Movie Detail Modal**: Added comprehensive validation score section including:
  - Overall score with timestamp
  - Detailed scores for each category (Design & Aesthetics, Clarity & Readability, Genre Representation, Emotional Impact)
  - Color-coded badges (green for scores ≥80, yellow for 60-79, red for <60)
  - Detailed reasoning for each score category
  - Recommendations from the validation service

### 4. Testing

#### test_movie_poster_validation.py
- Comprehensive unit tests for the new validation functionality
- Tests success scenarios, error handling, and edge cases
- All tests pass successfully

#### test_gallery_with_scores.py
- Demo script to showcase the new feature with mock data
- Demonstrates both movies with and without validation scores

## API Integration

The feature integrates with the `movie_poster_agent_svc` validation endpoint:

```
GET /validations/{movie_id}
```

Expected response format:
```json
{
  "id": "movie_id",
  "overall_score": 88,
  "detailed_scores": [
    {
      "category": "Design & Aesthetics",
      "score": 90,
      "reasoning": "Detailed explanation..."
    }
  ],
  "recommendations": [
    "Suggestion for improvement..."
  ],
  "validation_timestamp": "2023-11-05T12:15:00Z"
}
```

## User Experience

### Gallery Overview
- Each movie card now shows a blue score badge if validation scores are available
- Badge format: "🏆 Score: XX" where XX is the overall_score
- Movies without validation scores display normally without the badge

### Movie Detail Modal
- New "Poster Quality Score" section with overall score and validation timestamp
- "Detailed Scores" section with category-specific scores and reasoning
- Color-coded score badges for easy visual assessment
- "Recommendations" section with actionable improvement suggestions

## Environment Variables

Ensure the following environment variable is configured:

```
MOVIE_POSTER_AGENT_ENDPOINT=https://movie-poster-agent-svc.your-domain.com
```

## Deployment

The infrastructure changes require redeployment of the GUI service container app to include the new environment variable. Use `azd up` to deploy the updated infrastructure and service configurations.

## Future Enhancements

Potential improvements for future versions:
- Caching of validation scores to reduce API calls
- Batch validation score retrieval for better performance
- Score history tracking
- User rating comparison with AI validation scores
- Filtering/sorting movies by validation scores