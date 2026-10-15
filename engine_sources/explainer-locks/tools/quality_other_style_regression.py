#!/usr/bin/env python3
"""Exercise unchanged SceneBam families through the actual recovery video engine.

Only test fixtures are added. The authoritative compiler, asset registry,
rendering pipeline and continuous master audio stay unmodified.
"""
import recovery_video_proof as proof

proof.SCRIPTS.update({
    "photo_story": {
        "default": "A mother walks through the park and reads a story to her child."
    },
    "emoji": {
        "default": "A garden starts with a seed, receives sunlight, and grows into a beautiful tree."
    },
    "journey": {
        "default": "A parcel leaves the warehouse and travels to the customer's front door."
    },
    "collage": {
        "default": "A team shares an idea, builds a prototype, and celebrates a new project."
    },
    "newscast": {
        "default": "A city opens a new public library. Visitors arrive throughout the day."
    },
})

if __name__ == "__main__":
    proof.main()
