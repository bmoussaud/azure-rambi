#!/usr/bin/env python3
"""Test script to demonstrate the gallery with validation scores"""

import json
from flask import Flask, render_template
from dataclasses import dataclass
import os

# Mock data for testing
mock_movies = [
    {
        "id": "744_911430_Action_71391",
        "title": "Sky Racing Adventures",
        "plot": "An action-packed adventure where two unlikely heroes team up in a high-stakes racing competition that combines aviation and ground racing. With stunning aerial sequences and heart-pounding chase scenes, they must overcome their differences to save the day.",
        "poster_url": "https://example.com/poster1.jpg",
        "poster_description": "A dynamic poster showing racing cars and aircraft in an action scene",
        "validation_scores": {
            "id": "744_911430_Action_71391",
            "overall_score": 88,
            "detailed_scores": [
                {
                    "category": "Design & Aesthetics",
                    "score": 90,
                    "reasoning": "The poster is visually striking, with a well-balanced composition highlighting the central characters and dynamic action. The transition from dawn to dusk creates an engaging atmosphere, while the use of vibrant colors adds to the visual appeal."
                },
                {
                    "category": "Clarity & Readability",
                    "score": 85,
                    "reasoning": "The visual elements are clear and illustrative, effectively conveying the movie's theme of speed and excitement. The prominence of the characters and racecourse is well-defined."
                },
                {
                    "category": "Genre Representation",
                    "score": 80,
                    "reasoning": "The poster strongly suggests action and adventure themes. The combination of aviation and racing elements effectively represent these genres."
                },
                {
                    "category": "Emotional Impact",
                    "score": 90,
                    "reasoning": "The characters' confident postures and focused gazes evoke a sense of excitement and anticipation. The depiction of high-speed motion enhances emotional engagement."
                }
            ],
            "recommendations": [
                "Consider incorporating a tagline or textual element to enhance clarity and convey additional context.",
                "Ensure that the genre is clearly communicated through visual cues or text to set accurate audience expectations."
            ],
            "validation_timestamp": "2023-11-05T12:15:00Z"
        }
    },
    {
        "id": "512_789123_Comedy_42567",
        "title": "The Laughing Detective",
        "plot": "A comedy-mystery about a bumbling detective who accidentally stumbles into solving the crime of the century while trying to find his missing lunch. Hilarity ensues as he navigates through clues and red herrings.",
        "poster_url": "https://example.com/poster2.jpg",
        "poster_description": "A humorous poster with a detective character and magnifying glass",
        "validation_scores": {
            "id": "512_789123_Comedy_42567",
            "overall_score": 75,
            "detailed_scores": [
                {
                    "category": "Design & Aesthetics",
                    "score": 70,
                    "reasoning": "The poster has a playful design that matches the comedy genre, but could benefit from more vibrant colors and better character positioning."
                },
                {
                    "category": "Clarity & Readability",
                    "score": 80,
                    "reasoning": "The comedic elements are clearly visible and the detective theme is well communicated through visual cues."
                },
                {
                    "category": "Genre Representation",
                    "score": 85,
                    "reasoning": "Excellent representation of the comedy genre with visual gags and humorous character expressions that clearly indicate this is a light-hearted film."
                },
                {
                    "category": "Emotional Impact",
                    "score": 65,
                    "reasoning": "The poster evokes a sense of fun and lightheartedness but could be more engaging to draw viewers in."
                }
            ],
            "recommendations": [
                "Add brighter colors to make the poster more eye-catching and appealing to comedy fans.",
                "Consider adding more comedic visual elements to enhance the humor."
            ],
            "validation_timestamp": "2023-11-05T12:20:00Z"
        }
    },
    {
        "id": "333_654321_Drama_98765",
        "title": "Reflections of Time",
        "plot": "A deeply moving drama about a woman who discovers old letters in her grandmother's attic that reveal family secrets spanning three generations. As she uncovers the truth, she learns about love, loss, and redemption.",
        "poster_url": "https://example.com/poster3.jpg",
        "poster_description": "An emotional poster featuring vintage letters and family photos",
        # This movie has no validation scores to test the conditional display
    }
]

@dataclass
class GitHubContext:
    """ Data class for GitHubContext """
    job: str = "test"
    sha: str = "abc123"
    actor: str = "test-user"
    run_number: str = "1"
    repository: str = "https://github.com/bmoussaud/azure-rambi"

app = Flask(__name__)

@app.route('/test-gallery')
def test_gallery():
    """Test gallery with mock data including validation scores"""
    return render_template('gallery.html', movies=mock_movies, github=GitHubContext())

if __name__ == '__main__':
    print("Starting test gallery server...")
    print("Visit http://127.0.0.1:5556/test-gallery to see the gallery with validation scores")
    app.run(debug=True, port=5556, host='0.0.0.0')