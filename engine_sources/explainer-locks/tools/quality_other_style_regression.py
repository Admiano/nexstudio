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
    "newscast.neon": {
        "default": ("A city opens a new public library on Monday. "
                    "The building includes a reading room and a children\u0027s corner. "
                    "A reception desk welcomes visitors at the entrance. "
                    "Staff recorded 120 visits on opening day. "
                    "Another 85 visitors arrived on Tuesday. "
                    "Community workshops begin on Friday. "
                    "Families can book a free reading session. "
                    "The library closes at six in the evening.")
    },
})

if __name__ == "__main__":
    proof.main()
