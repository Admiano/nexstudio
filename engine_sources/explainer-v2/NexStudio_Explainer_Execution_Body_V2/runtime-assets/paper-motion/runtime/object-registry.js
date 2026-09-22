window.NEX_OBJECTS = [
  {
    "id": "object.rectangular-card.paper-01",
    "name": "Rectangular paper card",
    "version": "1.1.0",
    "category": "paper-object",
    "subtype": "card",
    "cssClass": "obj-rectangular-card",
    "renderer": "rectangular-card",
    "intents": [
      "compose_paper_story",
      "display_card"
    ],
    "keywords": [
      "paper",
      "card",
      "rectangular",
      "card"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook",
      "bold-paper-collage"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 42
      },
      "body": {
        "type": "string",
        "maxCharacters": 120
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 1.25,
      "maximum": 3.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "drop-settle",
      "lift-hover"
    ],
    "defaultMotion": "paper-slide",
    "soundTags": [
      "paper.object.soft",
      "motion.paper-slide"
    ],
    "themeTokens": [
      "--paper-bg",
      "--paper-surface",
      "--paper-surface-alt",
      "--ink",
      "--ink-muted",
      "--primary",
      "--secondary",
      "--accent",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity",
      "--outline-width"
    ],
    "accessibilityLabel": "Rectangular paper card animated paper component",
    "description": "A versatile rectangular card for titles, facts and visual grouping.",
    "attachable": false,
    "bespokeMotion": false
  },
  {
    "id": "object.torn-strip.paper-01",
    "name": "Torn paper strip",
    "version": "1.1.0",
    "category": "paper-object",
    "subtype": "strip",
    "cssClass": "obj-torn-strip",
    "renderer": "torn-strip",
    "intents": [
      "compose_paper_story",
      "display_strip"
    ],
    "keywords": [
      "paper",
      "strip",
      "torn",
      "strip"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook",
      "bold-paper-collage"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 40
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 1.25,
      "maximum": 3.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "tear-reveal",
      "paper-slide",
      "drop-settle"
    ],
    "defaultMotion": "tear-reveal",
    "soundTags": [
      "paper.object.soft",
      "motion.tear-reveal"
    ],
    "themeTokens": [
      "--paper-bg",
      "--paper-surface",
      "--paper-surface-alt",
      "--ink",
      "--ink-muted",
      "--primary",
      "--secondary",
      "--accent",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity",
      "--outline-width"
    ],
    "accessibilityLabel": "Torn paper strip animated paper component",
    "description": "A horizontal torn strip for labels, transitions and emphasis.",
    "attachable": false,
    "bespokeMotion": false
  },
  {
    "id": "object.sticky-note.paper-01",
    "name": "Sticky note",
    "version": "1.1.0",
    "category": "paper-object",
    "subtype": "note",
    "cssClass": "obj-sticky-note",
    "renderer": "sticky-note",
    "intents": [
      "compose_paper_story",
      "display_note"
    ],
    "keywords": [
      "paper",
      "note",
      "sticky",
      "note"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook",
      "bold-paper-collage"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 28
      },
      "body": {
        "type": "string",
        "maxCharacters": 90
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 1.25,
      "maximum": 3.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "peel",
      "paper-slide",
      "lift-hover"
    ],
    "defaultMotion": "peel",
    "soundTags": [
      "paper.object.soft",
      "motion.peel"
    ],
    "themeTokens": [
      "--paper-bg",
      "--paper-surface",
      "--paper-surface-alt",
      "--ink",
      "--ink-muted",
      "--primary",
      "--secondary",
      "--accent",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity",
      "--outline-width"
    ],
    "accessibilityLabel": "Sticky note animated paper component",
    "description": "A compact adhesive note with a lifting paper corner.",
    "attachable": false,
    "bespokeMotion": true
  },
  {
    "id": "object.index-card.paper-01",
    "name": "Index card",
    "version": "1.1.0",
    "category": "paper-object",
    "subtype": "card",
    "cssClass": "obj-index-card",
    "renderer": "index-card",
    "intents": [
      "compose_paper_story",
      "display_card"
    ],
    "keywords": [
      "paper",
      "card",
      "index",
      "card"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook",
      "bold-paper-collage"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 36
      },
      "body": {
        "type": "string",
        "maxCharacters": 100
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 1.25,
      "maximum": 3.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "drop-settle",
      "paper-slide",
      "lift-hover"
    ],
    "defaultMotion": "drop-settle",
    "soundTags": [
      "paper.object.soft",
      "motion.drop-settle"
    ],
    "themeTokens": [
      "--paper-bg",
      "--paper-surface",
      "--paper-surface-alt",
      "--ink",
      "--ink-muted",
      "--primary",
      "--secondary",
      "--accent",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity",
      "--outline-width"
    ],
    "accessibilityLabel": "Index card animated paper component",
    "description": "A ruled index card for concise structured notes.",
    "attachable": false,
    "bespokeMotion": false
  },
  {
    "id": "object.notebook-page.paper-01",
    "name": "Notebook page",
    "version": "1.1.0",
    "category": "paper-object",
    "subtype": "page",
    "cssClass": "obj-notebook-page",
    "renderer": "notebook-page",
    "intents": [
      "compose_paper_story",
      "display_page"
    ],
    "keywords": [
      "paper",
      "page",
      "notebook",
      "page"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook",
      "bold-paper-collage"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 36
      },
      "body": {
        "type": "string",
        "maxCharacters": 180
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 1.25,
      "maximum": 3.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "page-flip",
      "paper-slide",
      "drop-settle"
    ],
    "defaultMotion": "page-flip",
    "soundTags": [
      "paper.object.soft",
      "motion.page-flip"
    ],
    "themeTokens": [
      "--paper-bg",
      "--paper-surface",
      "--paper-surface-alt",
      "--ink",
      "--ink-muted",
      "--primary",
      "--secondary",
      "--accent",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity",
      "--outline-width"
    ],
    "accessibilityLabel": "Notebook page animated paper component",
    "description": "A ruled notebook sheet with punched binding holes.",
    "attachable": false,
    "bespokeMotion": false
  },
  {
    "id": "object.graph-page.paper-01",
    "name": "Graph-paper page",
    "version": "1.1.0",
    "category": "paper-object",
    "subtype": "page",
    "cssClass": "obj-graph-page",
    "renderer": "graph-page",
    "intents": [
      "compose_paper_story",
      "display_page"
    ],
    "keywords": [
      "paper",
      "page",
      "graph",
      "page"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook",
      "bold-paper-collage"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 28
      },
      "body": {
        "type": "string",
        "maxCharacters": 220
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 1.25,
      "maximum": 3.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "unfold",
      "paper-slide",
      "page-flip"
    ],
    "defaultMotion": "unfold",
    "soundTags": [
      "paper.object.soft",
      "motion.unfold"
    ],
    "themeTokens": [
      "--paper-bg",
      "--paper-surface",
      "--paper-surface-alt",
      "--ink",
      "--ink-muted",
      "--primary",
      "--secondary",
      "--accent",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity",
      "--outline-width"
    ],
    "accessibilityLabel": "Graph-paper page animated paper component",
    "description": "A graph-paper sheet for diagrams, plans and technical content.",
    "attachable": false,
    "bespokeMotion": false
  },
  {
    "id": "object.kraft-card.paper-01",
    "name": "Kraft card",
    "version": "1.1.0",
    "category": "paper-object",
    "subtype": "card",
    "cssClass": "obj-kraft-card",
    "renderer": "kraft-card",
    "intents": [
      "compose_paper_story",
      "display_card"
    ],
    "keywords": [
      "paper",
      "card",
      "kraft",
      "card"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook",
      "bold-paper-collage"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 36
      },
      "body": {
        "type": "string",
        "maxCharacters": 100
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 1.25,
      "maximum": 3.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "drop-settle",
      "lift-hover"
    ],
    "defaultMotion": "paper-slide",
    "soundTags": [
      "paper.object.soft",
      "motion.paper-slide"
    ],
    "themeTokens": [
      "--paper-bg",
      "--paper-surface",
      "--paper-surface-alt",
      "--ink",
      "--ink-muted",
      "--primary",
      "--secondary",
      "--accent",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity",
      "--outline-width"
    ],
    "accessibilityLabel": "Kraft card animated paper component",
    "description": "A sturdy kraft-paper card with dark printed ink.",
    "attachable": false,
    "bespokeMotion": false
  },
  {
    "id": "object.photo-sheet.paper-01",
    "name": "Photo-paper sheet",
    "version": "1.1.0",
    "category": "paper-object",
    "subtype": "media",
    "cssClass": "obj-photo-sheet",
    "renderer": "photo-sheet",
    "intents": [
      "compose_paper_story",
      "display_media"
    ],
    "keywords": [
      "paper",
      "media",
      "photo",
      "sheet"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook",
      "bold-paper-collage"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 32
      },
      "media": {
        "type": "image",
        "replaceable": true
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 1.25,
      "maximum": 3.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "drop-settle",
      "paper-slide",
      "lift-hover"
    ],
    "defaultMotion": "drop-settle",
    "soundTags": [
      "paper.object.soft",
      "motion.drop-settle"
    ],
    "themeTokens": [
      "--paper-bg",
      "--paper-surface",
      "--paper-surface-alt",
      "--ink",
      "--ink-muted",
      "--primary",
      "--secondary",
      "--accent",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity",
      "--outline-width"
    ],
    "accessibilityLabel": "Photo-paper sheet animated paper component",
    "description": "A glossy paper-photo holder with replaceable media.",
    "attachable": false,
    "bespokeMotion": false
  },
  {
    "id": "object.printed-label.paper-01",
    "name": "Printed label",
    "version": "1.1.0",
    "category": "paper-object",
    "subtype": "label",
    "cssClass": "obj-printed-label",
    "renderer": "printed-label",
    "intents": [
      "compose_paper_story",
      "display_label"
    ],
    "keywords": [
      "paper",
      "label",
      "printed",
      "label"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook",
      "bold-paper-collage"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 22
      },
      "body": {
        "type": "string",
        "maxCharacters": 40
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 1.25,
      "maximum": 3.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "stamp",
      "drop-settle",
      "paper-slide"
    ],
    "defaultMotion": "stamp",
    "soundTags": [
      "paper.object.soft",
      "motion.stamp"
    ],
    "themeTokens": [
      "--paper-bg",
      "--paper-surface",
      "--paper-surface-alt",
      "--ink",
      "--ink-muted",
      "--primary",
      "--secondary",
      "--accent",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity",
      "--outline-width"
    ],
    "accessibilityLabel": "Printed label animated paper component",
    "description": "A small printed label for metadata and categorisation.",
    "attachable": false,
    "bespokeMotion": false
  },
  {
    "id": "object.hanging-tag.paper-01",
    "name": "Hanging tag",
    "version": "1.1.0",
    "category": "paper-object",
    "subtype": "label",
    "cssClass": "obj-hanging-tag",
    "renderer": "hanging-tag",
    "intents": [
      "compose_paper_story",
      "display_label"
    ],
    "keywords": [
      "paper",
      "label",
      "hanging",
      "tag"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook",
      "bold-paper-collage"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 20
      },
      "body": {
        "type": "string",
        "maxCharacters": 36
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 1.25,
      "maximum": 3.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "pin-board",
      "drop-settle",
      "paper-slide"
    ],
    "defaultMotion": "pin-board",
    "soundTags": [
      "paper.object.soft",
      "motion.pin-board"
    ],
    "themeTokens": [
      "--paper-bg",
      "--paper-surface",
      "--paper-surface-alt",
      "--ink",
      "--ink-muted",
      "--primary",
      "--secondary",
      "--accent",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity",
      "--outline-width"
    ],
    "accessibilityLabel": "Hanging tag animated paper component",
    "description": "A pierced paper tag suspended by a configurable string.",
    "attachable": false,
    "bespokeMotion": true
  },
  {
    "id": "object.paper-tab.paper-01",
    "name": "Paper tab",
    "version": "1.1.0",
    "category": "paper-object",
    "subtype": "navigation",
    "cssClass": "obj-paper-tab",
    "renderer": "paper-tab",
    "intents": [
      "compose_paper_story",
      "display_navigation"
    ],
    "keywords": [
      "paper",
      "navigation",
      "paper",
      "tab"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook",
      "bold-paper-collage"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 18
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 1.25,
      "maximum": 3.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "drop-settle",
      "lift-hover"
    ],
    "defaultMotion": "paper-slide",
    "soundTags": [
      "paper.object.soft",
      "motion.paper-slide"
    ],
    "themeTokens": [
      "--paper-bg",
      "--paper-surface",
      "--paper-surface-alt",
      "--ink",
      "--ink-muted",
      "--primary",
      "--secondary",
      "--accent",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity",
      "--outline-width"
    ],
    "accessibilityLabel": "Paper tab animated paper component",
    "description": "A folder or chapter tab for organising scenes.",
    "attachable": false,
    "bespokeMotion": false
  },
  {
    "id": "object.bookmark.paper-01",
    "name": "Bookmark",
    "version": "1.1.0",
    "category": "paper-object",
    "subtype": "navigation",
    "cssClass": "obj-bookmark",
    "renderer": "bookmark",
    "intents": [
      "compose_paper_story",
      "display_navigation"
    ],
    "keywords": [
      "paper",
      "navigation",
      "bookmark"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook",
      "bold-paper-collage"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 16
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 1.25,
      "maximum": 3.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "drop-settle",
      "paper-slide",
      "lift-hover"
    ],
    "defaultMotion": "drop-settle",
    "soundTags": [
      "paper.object.soft",
      "motion.drop-settle"
    ],
    "themeTokens": [
      "--paper-bg",
      "--paper-surface",
      "--paper-surface-alt",
      "--ink",
      "--ink-muted",
      "--primary",
      "--secondary",
      "--accent",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity",
      "--outline-width"
    ],
    "accessibilityLabel": "Bookmark animated paper component",
    "description": "A long bookmark with a folded or notched end.",
    "attachable": false,
    "bespokeMotion": false
  },
  {
    "id": "object.speech-bubble.paper-01",
    "name": "Speech bubble",
    "version": "1.1.0",
    "category": "paper-object",
    "subtype": "communication",
    "cssClass": "obj-speech-bubble",
    "renderer": "speech-bubble",
    "intents": [
      "compose_paper_story",
      "display_communication"
    ],
    "keywords": [
      "paper",
      "communication",
      "speech",
      "bubble"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook",
      "bold-paper-collage"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "body": {
        "type": "string",
        "maxCharacters": 90
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 1.25,
      "maximum": 3.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "drop-settle",
      "paper-slide",
      "lift-hover"
    ],
    "defaultMotion": "drop-settle",
    "soundTags": [
      "paper.object.soft",
      "motion.drop-settle"
    ],
    "themeTokens": [
      "--paper-bg",
      "--paper-surface",
      "--paper-surface-alt",
      "--ink",
      "--ink-muted",
      "--primary",
      "--secondary",
      "--accent",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity",
      "--outline-width"
    ],
    "accessibilityLabel": "Speech bubble animated paper component",
    "description": "A paper speech bubble with editable dialogue.",
    "attachable": false,
    "bespokeMotion": true
  },
  {
    "id": "object.thought-bubble.paper-01",
    "name": "Thought bubble",
    "version": "1.1.0",
    "category": "paper-object",
    "subtype": "communication",
    "cssClass": "obj-thought-bubble",
    "renderer": "thought-bubble",
    "intents": [
      "compose_paper_story",
      "display_communication"
    ],
    "keywords": [
      "paper",
      "communication",
      "thought",
      "bubble"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook",
      "bold-paper-collage"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "body": {
        "type": "string",
        "maxCharacters": 90
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 1.25,
      "maximum": 3.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "drop-settle",
      "paper-slide",
      "lift-hover"
    ],
    "defaultMotion": "drop-settle",
    "soundTags": [
      "paper.object.soft",
      "motion.drop-settle"
    ],
    "themeTokens": [
      "--paper-bg",
      "--paper-surface",
      "--paper-surface-alt",
      "--ink",
      "--ink-muted",
      "--primary",
      "--secondary",
      "--accent",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity",
      "--outline-width"
    ],
    "accessibilityLabel": "Thought bubble animated paper component",
    "description": "A layered paper thought bubble for ideas and reflections.",
    "attachable": false,
    "bespokeMotion": true
  },
  {
    "id": "object.price-sticker.paper-01",
    "name": "Price sticker",
    "version": "1.1.0",
    "category": "paper-object",
    "subtype": "sticker",
    "cssClass": "obj-price-sticker",
    "renderer": "price-sticker",
    "intents": [
      "compose_paper_story",
      "display_sticker"
    ],
    "keywords": [
      "paper",
      "sticker",
      "price",
      "sticker"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook",
      "bold-paper-collage"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 14
      },
      "body": {
        "type": "string",
        "maxCharacters": 20
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 1.25,
      "maximum": 3.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "stamp",
      "drop-settle",
      "paper-slide"
    ],
    "defaultMotion": "stamp",
    "soundTags": [
      "paper.object.soft",
      "motion.stamp"
    ],
    "themeTokens": [
      "--paper-bg",
      "--paper-surface",
      "--paper-surface-alt",
      "--ink",
      "--ink-muted",
      "--primary",
      "--secondary",
      "--accent",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity",
      "--outline-width"
    ],
    "accessibilityLabel": "Price sticker animated paper component",
    "description": "A bold paper price marker with editable value and label.",
    "attachable": false,
    "bespokeMotion": false
  },
  {
    "id": "object.announcement-sticker.paper-01",
    "name": "Announcement sticker",
    "version": "1.1.0",
    "category": "paper-object",
    "subtype": "sticker",
    "cssClass": "obj-announcement-sticker",
    "renderer": "announcement-sticker",
    "intents": [
      "compose_paper_story",
      "display_sticker"
    ],
    "keywords": [
      "paper",
      "sticker",
      "announcement",
      "sticker"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook",
      "bold-paper-collage"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 22
      },
      "body": {
        "type": "string",
        "maxCharacters": 35
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 1.25,
      "maximum": 3.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "stamp",
      "drop-settle",
      "paper-slide"
    ],
    "defaultMotion": "stamp",
    "soundTags": [
      "paper.object.soft",
      "motion.stamp"
    ],
    "themeTokens": [
      "--paper-bg",
      "--paper-surface",
      "--paper-surface-alt",
      "--ink",
      "--ink-muted",
      "--primary",
      "--secondary",
      "--accent",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity",
      "--outline-width"
    ],
    "accessibilityLabel": "Announcement sticker animated paper component",
    "description": "A high-impact announcement burst for launches and alerts.",
    "attachable": false,
    "bespokeMotion": false
  },
  {
    "id": "object.approval-seal.paper-01",
    "name": "Approval seal",
    "version": "1.1.0",
    "category": "paper-object",
    "subtype": "sticker",
    "cssClass": "obj-approval-seal",
    "renderer": "approval-seal",
    "intents": [
      "compose_paper_story",
      "display_sticker"
    ],
    "keywords": [
      "paper",
      "sticker",
      "approval",
      "seal"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook",
      "bold-paper-collage"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 18
      },
      "body": {
        "type": "string",
        "maxCharacters": 20
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 1.25,
      "maximum": 3.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "stamp",
      "drop-settle",
      "paper-slide"
    ],
    "defaultMotion": "stamp",
    "soundTags": [
      "paper.object.soft",
      "motion.stamp"
    ],
    "themeTokens": [
      "--paper-bg",
      "--paper-surface",
      "--paper-surface-alt",
      "--ink",
      "--ink-muted",
      "--primary",
      "--secondary",
      "--accent",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity",
      "--outline-width"
    ],
    "accessibilityLabel": "Approval seal animated paper component",
    "description": "A stamped paper approval seal with editable status.",
    "attachable": false,
    "bespokeMotion": true
  },
  {
    "id": "object.event-ticket.paper-01",
    "name": "Event ticket",
    "version": "1.1.0",
    "category": "paper-object",
    "subtype": "document",
    "cssClass": "obj-event-ticket",
    "renderer": "event-ticket",
    "intents": [
      "compose_paper_story",
      "display_document"
    ],
    "keywords": [
      "paper",
      "document",
      "event",
      "ticket"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook",
      "bold-paper-collage"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 28
      },
      "body": {
        "type": "string",
        "maxCharacters": 55
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 1.25,
      "maximum": 3.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "tear-reveal",
      "paper-slide",
      "drop-settle"
    ],
    "defaultMotion": "tear-reveal",
    "soundTags": [
      "paper.object.soft",
      "motion.tear-reveal"
    ],
    "themeTokens": [
      "--paper-bg",
      "--paper-surface",
      "--paper-surface-alt",
      "--ink",
      "--ink-muted",
      "--primary",
      "--secondary",
      "--accent",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity",
      "--outline-width"
    ],
    "accessibilityLabel": "Event ticket animated paper component",
    "description": "A perforated admission or event ticket with detachable stub.",
    "attachable": false,
    "bespokeMotion": true
  },
  {
    "id": "object.receipt.paper-01",
    "name": "Receipt",
    "version": "1.1.0",
    "category": "paper-object",
    "subtype": "document",
    "cssClass": "obj-receipt",
    "renderer": "receipt",
    "intents": [
      "compose_paper_story",
      "display_document"
    ],
    "keywords": [
      "paper",
      "document",
      "receipt"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook",
      "bold-paper-collage"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 18
      },
      "body": {
        "type": "string",
        "maxCharacters": 120
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 1.25,
      "maximum": 3.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "drop-settle",
      "lift-hover"
    ],
    "defaultMotion": "paper-slide",
    "soundTags": [
      "paper.object.soft",
      "motion.paper-slide"
    ],
    "themeTokens": [
      "--paper-bg",
      "--paper-surface",
      "--paper-surface-alt",
      "--ink",
      "--ink-muted",
      "--primary",
      "--secondary",
      "--accent",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity",
      "--outline-width"
    ],
    "accessibilityLabel": "Receipt animated paper component",
    "description": "A long paper receipt with editable line items and total.",
    "attachable": false,
    "bespokeMotion": true
  },
  {
    "id": "object.newspaper-clipping.paper-01",
    "name": "Newspaper clipping",
    "version": "1.1.0",
    "category": "paper-object",
    "subtype": "document",
    "cssClass": "obj-newspaper-clipping",
    "renderer": "newspaper-clipping",
    "intents": [
      "compose_paper_story",
      "display_document"
    ],
    "keywords": [
      "paper",
      "document",
      "newspaper",
      "clipping"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook",
      "bold-paper-collage"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 44
      },
      "body": {
        "type": "string",
        "maxCharacters": 150
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 1.25,
      "maximum": 3.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "drop-settle",
      "lift-hover"
    ],
    "defaultMotion": "paper-slide",
    "soundTags": [
      "paper.object.soft",
      "motion.paper-slide"
    ],
    "themeTokens": [
      "--paper-bg",
      "--paper-surface",
      "--paper-surface-alt",
      "--ink",
      "--ink-muted",
      "--primary",
      "--secondary",
      "--accent",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity",
      "--outline-width"
    ],
    "accessibilityLabel": "Newspaper clipping animated paper component",
    "description": "A multi-column newspaper clipping with headline and source.",
    "attachable": false,
    "bespokeMotion": true
  },
  {
    "id": "object.magazine-clipping.paper-01",
    "name": "Magazine clipping",
    "version": "1.1.0",
    "category": "paper-object",
    "subtype": "document",
    "cssClass": "obj-magazine-clipping",
    "renderer": "magazine-clipping",
    "intents": [
      "compose_paper_story",
      "display_document"
    ],
    "keywords": [
      "paper",
      "document",
      "magazine",
      "clipping"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook",
      "bold-paper-collage"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 28
      },
      "body": {
        "type": "string",
        "maxCharacters": 70
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 1.25,
      "maximum": 3.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "drop-settle",
      "lift-hover"
    ],
    "defaultMotion": "paper-slide",
    "soundTags": [
      "paper.object.soft",
      "motion.paper-slide"
    ],
    "themeTokens": [
      "--paper-bg",
      "--paper-surface",
      "--paper-surface-alt",
      "--ink",
      "--ink-muted",
      "--primary",
      "--secondary",
      "--accent",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity",
      "--outline-width"
    ],
    "accessibilityLabel": "Magazine clipping animated paper component",
    "description": "A colourful editorial clipping with image and headline.",
    "attachable": false,
    "bespokeMotion": false
  },
  {
    "id": "object.closed-envelope.paper-01",
    "name": "Closed envelope",
    "version": "1.1.0",
    "category": "paper-object",
    "subtype": "mail",
    "cssClass": "obj-closed-envelope",
    "renderer": "closed-envelope",
    "intents": [
      "compose_paper_story",
      "display_mail"
    ],
    "keywords": [
      "paper",
      "mail",
      "closed",
      "envelope"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook",
      "bold-paper-collage"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 26
      },
      "body": {
        "type": "string",
        "maxCharacters": 60
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 1.25,
      "maximum": 3.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "drop-settle",
      "paper-slide",
      "lift-hover"
    ],
    "defaultMotion": "drop-settle",
    "soundTags": [
      "paper.object.soft",
      "motion.drop-settle"
    ],
    "themeTokens": [
      "--paper-bg",
      "--paper-surface",
      "--paper-surface-alt",
      "--ink",
      "--ink-muted",
      "--primary",
      "--secondary",
      "--accent",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity",
      "--outline-width"
    ],
    "accessibilityLabel": "Closed envelope animated paper component",
    "description": "A sealed paper envelope ready to receive or send.",
    "attachable": false,
    "bespokeMotion": false
  },
  {
    "id": "object.opening-envelope.paper-01",
    "name": "Opening envelope",
    "version": "1.1.0",
    "category": "paper-object",
    "subtype": "mail",
    "cssClass": "obj-opening-envelope",
    "renderer": "opening-envelope",
    "intents": [
      "compose_paper_story",
      "display_mail"
    ],
    "keywords": [
      "paper",
      "mail",
      "opening",
      "envelope"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook",
      "bold-paper-collage"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 28
      },
      "body": {
        "type": "string",
        "maxCharacters": 100
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 1.25,
      "maximum": 3.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "unfold",
      "paper-slide",
      "page-flip"
    ],
    "defaultMotion": "unfold",
    "soundTags": [
      "paper.object.soft",
      "motion.unfold"
    ],
    "themeTokens": [
      "--paper-bg",
      "--paper-surface",
      "--paper-surface-alt",
      "--ink",
      "--ink-muted",
      "--primary",
      "--secondary",
      "--accent",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity",
      "--outline-width"
    ],
    "accessibilityLabel": "Opening envelope animated paper component",
    "description": "An envelope whose flap opens and letter rises.",
    "attachable": false,
    "bespokeMotion": true
  },
  {
    "id": "object.letter-sheet.paper-01",
    "name": "Letter sheet",
    "version": "1.1.0",
    "category": "paper-object",
    "subtype": "mail",
    "cssClass": "obj-letter-sheet",
    "renderer": "letter-sheet",
    "intents": [
      "compose_paper_story",
      "display_mail"
    ],
    "keywords": [
      "paper",
      "mail",
      "letter",
      "sheet"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook",
      "bold-paper-collage"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 36
      },
      "body": {
        "type": "string",
        "maxCharacters": 220
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 1.25,
      "maximum": 3.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "unfold",
      "paper-slide",
      "page-flip"
    ],
    "defaultMotion": "unfold",
    "soundTags": [
      "paper.object.soft",
      "motion.unfold"
    ],
    "themeTokens": [
      "--paper-bg",
      "--paper-surface",
      "--paper-surface-alt",
      "--ink",
      "--ink-muted",
      "--primary",
      "--secondary",
      "--accent",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity",
      "--outline-width"
    ],
    "accessibilityLabel": "Letter sheet animated paper component",
    "description": "A formal letter sheet with address, heading and body slots.",
    "attachable": false,
    "bespokeMotion": false
  },
  {
    "id": "object.postcard.paper-01",
    "name": "Postcard",
    "version": "1.1.0",
    "category": "paper-object",
    "subtype": "mail",
    "cssClass": "obj-postcard",
    "renderer": "postcard",
    "intents": [
      "compose_paper_story",
      "display_mail"
    ],
    "keywords": [
      "paper",
      "mail",
      "postcard"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook",
      "bold-paper-collage"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 22
      },
      "body": {
        "type": "string",
        "maxCharacters": 75
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 1.25,
      "maximum": 3.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "page-flip",
      "paper-slide",
      "drop-settle"
    ],
    "defaultMotion": "page-flip",
    "soundTags": [
      "paper.object.soft",
      "motion.page-flip"
    ],
    "themeTokens": [
      "--paper-bg",
      "--paper-surface",
      "--paper-surface-alt",
      "--ink",
      "--ink-muted",
      "--primary",
      "--secondary",
      "--accent",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity",
      "--outline-width"
    ],
    "accessibilityLabel": "Postcard animated paper component",
    "description": "A two-sided postcard with image, note and address.",
    "attachable": false,
    "bespokeMotion": false
  },
  {
    "id": "object.certificate.paper-01",
    "name": "Certificate",
    "version": "1.1.0",
    "category": "paper-object",
    "subtype": "document",
    "cssClass": "obj-certificate",
    "renderer": "certificate",
    "intents": [
      "compose_paper_story",
      "display_document"
    ],
    "keywords": [
      "paper",
      "document",
      "certificate"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook",
      "bold-paper-collage"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 32
      },
      "body": {
        "type": "string",
        "maxCharacters": 90
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 1.25,
      "maximum": 3.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "unfold",
      "paper-slide",
      "page-flip"
    ],
    "defaultMotion": "unfold",
    "soundTags": [
      "paper.object.soft",
      "motion.unfold"
    ],
    "themeTokens": [
      "--paper-bg",
      "--paper-surface",
      "--paper-surface-alt",
      "--ink",
      "--ink-muted",
      "--primary",
      "--secondary",
      "--accent",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity",
      "--outline-width"
    ],
    "accessibilityLabel": "Certificate animated paper component",
    "description": "A bordered certificate with recipient and award slots.",
    "attachable": false,
    "bespokeMotion": false
  },
  {
    "id": "object.checklist-sheet.paper-01",
    "name": "Checklist sheet",
    "version": "1.1.0",
    "category": "paper-object",
    "subtype": "document",
    "cssClass": "obj-checklist-sheet",
    "renderer": "checklist-sheet",
    "intents": [
      "compose_paper_story",
      "display_document"
    ],
    "keywords": [
      "paper",
      "document",
      "checklist",
      "sheet"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook",
      "bold-paper-collage"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 26
      },
      "body": {
        "type": "string",
        "maxCharacters": 60
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 1.25,
      "maximum": 3.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "drop-settle",
      "lift-hover"
    ],
    "defaultMotion": "paper-slide",
    "soundTags": [
      "paper.object.soft",
      "motion.paper-slide"
    ],
    "themeTokens": [
      "--paper-bg",
      "--paper-surface",
      "--paper-surface-alt",
      "--ink",
      "--ink-muted",
      "--primary",
      "--secondary",
      "--accent",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity",
      "--outline-width"
    ],
    "accessibilityLabel": "Checklist sheet animated paper component",
    "description": "A checklist with animated completion marks.",
    "attachable": false,
    "bespokeMotion": true
  },
  {
    "id": "object.folder.paper-01",
    "name": "Folder",
    "version": "1.1.0",
    "category": "paper-object",
    "subtype": "storage",
    "cssClass": "obj-folder",
    "renderer": "folder",
    "intents": [
      "compose_paper_story",
      "display_storage"
    ],
    "keywords": [
      "paper",
      "storage",
      "folder"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook",
      "bold-paper-collage"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 26
      },
      "body": {
        "type": "string",
        "maxCharacters": 70
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 1.25,
      "maximum": 3.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "unfold",
      "paper-slide",
      "page-flip"
    ],
    "defaultMotion": "unfold",
    "soundTags": [
      "paper.object.soft",
      "motion.unfold"
    ],
    "themeTokens": [
      "--paper-bg",
      "--paper-surface",
      "--paper-surface-alt",
      "--ink",
      "--ink-muted",
      "--primary",
      "--secondary",
      "--accent",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity",
      "--outline-width"
    ],
    "accessibilityLabel": "Folder animated paper component",
    "description": "An opening paper folder with replaceable title and contents.",
    "attachable": false,
    "bespokeMotion": true
  },
  {
    "id": "object.document-stack.paper-01",
    "name": "Document stack",
    "version": "1.1.0",
    "category": "paper-object",
    "subtype": "stack",
    "cssClass": "obj-document-stack",
    "renderer": "document-stack",
    "intents": [
      "compose_paper_story",
      "display_stack"
    ],
    "keywords": [
      "paper",
      "stack",
      "document",
      "stack"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook",
      "bold-paper-collage"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 26
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 1.25,
      "maximum": 3.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "stack-shuffle",
      "drop-settle",
      "paper-slide"
    ],
    "defaultMotion": "stack-shuffle",
    "soundTags": [
      "paper.object.soft",
      "motion.stack-shuffle"
    ],
    "themeTokens": [
      "--paper-bg",
      "--paper-surface",
      "--paper-surface-alt",
      "--ink",
      "--ink-muted",
      "--primary",
      "--secondary",
      "--accent",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity",
      "--outline-width"
    ],
    "accessibilityLabel": "Document stack animated paper component",
    "description": "A layered stack of documents with visible page offsets.",
    "attachable": false,
    "bespokeMotion": true
  },
  {
    "id": "object.paper-stack.paper-01",
    "name": "Paper stack",
    "version": "1.1.0",
    "category": "paper-object",
    "subtype": "stack",
    "cssClass": "obj-paper-stack",
    "renderer": "paper-stack",
    "intents": [
      "compose_paper_story",
      "display_stack"
    ],
    "keywords": [
      "paper",
      "stack",
      "paper",
      "stack"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook",
      "bold-paper-collage"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 24
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 1.25,
      "maximum": 3.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "stack-shuffle",
      "drop-settle",
      "paper-slide"
    ],
    "defaultMotion": "stack-shuffle",
    "soundTags": [
      "paper.object.soft",
      "motion.stack-shuffle"
    ],
    "themeTokens": [
      "--paper-bg",
      "--paper-surface",
      "--paper-surface-alt",
      "--ink",
      "--ink-muted",
      "--primary",
      "--secondary",
      "--accent",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity",
      "--outline-width"
    ],
    "accessibilityLabel": "Paper stack animated paper component",
    "description": "A neutral stack of blank paper sheets for content grouping.",
    "attachable": false,
    "bespokeMotion": false
  },
  {
    "id": "object.folded-note.paper-01",
    "name": "Folded note",
    "version": "1.1.0",
    "category": "paper-object",
    "subtype": "note",
    "cssClass": "obj-folded-note",
    "renderer": "folded-note",
    "intents": [
      "compose_paper_story",
      "display_note"
    ],
    "keywords": [
      "paper",
      "note",
      "folded",
      "note"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook",
      "bold-paper-collage"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 26
      },
      "body": {
        "type": "string",
        "maxCharacters": 80
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 1.25,
      "maximum": 3.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "unfold",
      "paper-slide",
      "page-flip"
    ],
    "defaultMotion": "unfold",
    "soundTags": [
      "paper.object.soft",
      "motion.unfold"
    ],
    "themeTokens": [
      "--paper-bg",
      "--paper-surface",
      "--paper-surface-alt",
      "--ink",
      "--ink-muted",
      "--primary",
      "--secondary",
      "--accent",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity",
      "--outline-width"
    ],
    "accessibilityLabel": "Folded note animated paper component",
    "description": "A folded message that opens into a readable note.",
    "attachable": false,
    "bespokeMotion": true
  },
  {
    "id": "object.crumpled-ball.paper-01",
    "name": "Crumpled paper ball",
    "version": "1.1.0",
    "category": "paper-object",
    "subtype": "scrap",
    "cssClass": "obj-crumpled-ball",
    "renderer": "crumpled-ball",
    "intents": [
      "compose_paper_story",
      "display_scrap"
    ],
    "keywords": [
      "paper",
      "scrap",
      "crumpled",
      "ball"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook",
      "bold-paper-collage"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 20
      },
      "body": {
        "type": "string",
        "maxCharacters": 90
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 1.25,
      "maximum": 3.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "crumple-flatten",
      "drop-settle",
      "paper-slide"
    ],
    "defaultMotion": "crumple-flatten",
    "soundTags": [
      "paper.object.soft",
      "motion.crumple-flatten"
    ],
    "themeTokens": [
      "--paper-bg",
      "--paper-surface",
      "--paper-surface-alt",
      "--ink",
      "--ink-muted",
      "--primary",
      "--secondary",
      "--accent",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity",
      "--outline-width"
    ],
    "accessibilityLabel": "Crumpled paper ball animated paper component",
    "description": "A dimensional paper ball that can flatten into a sheet.",
    "attachable": false,
    "bespokeMotion": true
  },
  {
    "id": "object.irregular-scrap.paper-01",
    "name": "Irregular torn scrap",
    "version": "1.1.0",
    "category": "paper-object",
    "subtype": "scrap",
    "cssClass": "obj-irregular-scrap",
    "renderer": "irregular-scrap",
    "intents": [
      "compose_paper_story",
      "display_scrap"
    ],
    "keywords": [
      "paper",
      "scrap",
      "irregular",
      "scrap"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook",
      "bold-paper-collage"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 28
      },
      "body": {
        "type": "string",
        "maxCharacters": 70
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 1.25,
      "maximum": 3.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "tear-reveal",
      "paper-slide",
      "drop-settle"
    ],
    "defaultMotion": "tear-reveal",
    "soundTags": [
      "paper.object.soft",
      "motion.tear-reveal"
    ],
    "themeTokens": [
      "--paper-bg",
      "--paper-surface",
      "--paper-surface-alt",
      "--ink",
      "--ink-muted",
      "--primary",
      "--secondary",
      "--accent",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity",
      "--outline-width"
    ],
    "accessibilityLabel": "Irregular torn scrap animated paper component",
    "description": "An asymmetrical torn scrap for collage and annotation.",
    "attachable": false,
    "bespokeMotion": false
  },
  {
    "id": "object.ripped-hole.paper-01",
    "name": "Ripped-hole reveal",
    "version": "1.1.0",
    "category": "paper-object",
    "subtype": "scrap",
    "cssClass": "obj-ripped-hole",
    "renderer": "ripped-hole",
    "intents": [
      "compose_paper_story",
      "display_scrap"
    ],
    "keywords": [
      "paper",
      "scrap",
      "ripped",
      "hole"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook",
      "bold-paper-collage"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 26
      },
      "body": {
        "type": "string",
        "maxCharacters": 65
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 1.25,
      "maximum": 3.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "tear-reveal",
      "paper-slide",
      "drop-settle"
    ],
    "defaultMotion": "tear-reveal",
    "soundTags": [
      "paper.object.soft",
      "motion.tear-reveal"
    ],
    "themeTokens": [
      "--paper-bg",
      "--paper-surface",
      "--paper-surface-alt",
      "--ink",
      "--ink-muted",
      "--primary",
      "--secondary",
      "--accent",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity",
      "--outline-width"
    ],
    "accessibilityLabel": "Ripped-hole reveal animated paper component",
    "description": "A paper layer with a torn opening revealing content beneath.",
    "attachable": false,
    "bespokeMotion": true
  },
  {
    "id": "object.masking-tape.paper-01",
    "name": "Masking-tape strip",
    "version": "1.1.0",
    "category": "paper-object",
    "subtype": "attachment",
    "cssClass": "obj-masking-tape",
    "renderer": "masking-tape",
    "intents": [
      "compose_paper_story",
      "display_attachment"
    ],
    "keywords": [
      "paper",
      "attachment",
      "masking",
      "tape"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook",
      "bold-paper-collage"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "color": {
        "type": "theme-token"
      },
      "anchor": {
        "type": "position"
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 1.25,
      "maximum": 3.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "tape-down",
      "paper-slide",
      "drop-settle"
    ],
    "defaultMotion": "tape-down",
    "soundTags": [
      "paper.attach.soft",
      "motion.tape-down"
    ],
    "themeTokens": [
      "--paper-bg",
      "--paper-surface",
      "--paper-surface-alt",
      "--ink",
      "--ink-muted",
      "--primary",
      "--secondary",
      "--accent",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity",
      "--outline-width"
    ],
    "accessibilityLabel": "Masking-tape strip animated paper component",
    "description": "A standalone masking-tape strip attachable to any component.",
    "attachable": true,
    "bespokeMotion": false
  },
  {
    "id": "object.clear-tape.paper-01",
    "name": "Clear-tape strip",
    "version": "1.1.0",
    "category": "paper-object",
    "subtype": "attachment",
    "cssClass": "obj-clear-tape",
    "renderer": "clear-tape",
    "intents": [
      "compose_paper_story",
      "display_attachment"
    ],
    "keywords": [
      "paper",
      "attachment",
      "clear",
      "tape"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook",
      "bold-paper-collage"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "color": {
        "type": "theme-token"
      },
      "anchor": {
        "type": "position"
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 1.25,
      "maximum": 3.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "tape-down",
      "paper-slide",
      "drop-settle"
    ],
    "defaultMotion": "tape-down",
    "soundTags": [
      "paper.attach.soft",
      "motion.tape-down"
    ],
    "themeTokens": [
      "--paper-bg",
      "--paper-surface",
      "--paper-surface-alt",
      "--ink",
      "--ink-muted",
      "--primary",
      "--secondary",
      "--accent",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity",
      "--outline-width"
    ],
    "accessibilityLabel": "Clear-tape strip animated paper component",
    "description": "A translucent tape strip with a moving reflective sheen.",
    "attachable": true,
    "bespokeMotion": true
  },
  {
    "id": "object.staple-attachment.paper-01",
    "name": "Staple attachment",
    "version": "1.1.0",
    "category": "paper-object",
    "subtype": "attachment",
    "cssClass": "obj-staple-attachment",
    "renderer": "staple-attachment",
    "intents": [
      "compose_paper_story",
      "display_attachment"
    ],
    "keywords": [
      "paper",
      "attachment",
      "staple",
      "attachment"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook",
      "bold-paper-collage"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "color": {
        "type": "theme-token"
      },
      "anchor": {
        "type": "position"
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 1.25,
      "maximum": 3.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "pin-board",
      "drop-settle",
      "paper-slide"
    ],
    "defaultMotion": "pin-board",
    "soundTags": [
      "paper.attach.soft",
      "motion.pin-board"
    ],
    "themeTokens": [
      "--paper-bg",
      "--paper-surface",
      "--paper-surface-alt",
      "--ink",
      "--ink-muted",
      "--primary",
      "--secondary",
      "--accent",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity",
      "--outline-width"
    ],
    "accessibilityLabel": "Staple attachment animated paper component",
    "description": "A standalone metal staple attachable to paper objects.",
    "attachable": true,
    "bespokeMotion": true
  },
  {
    "id": "object.paperclip-attachment.paper-01",
    "name": "Paper-clip attachment",
    "version": "1.1.0",
    "category": "paper-object",
    "subtype": "attachment",
    "cssClass": "obj-paperclip-attachment",
    "renderer": "paperclip-attachment",
    "intents": [
      "compose_paper_story",
      "display_attachment"
    ],
    "keywords": [
      "paper",
      "attachment",
      "paperclip",
      "attachment"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook",
      "bold-paper-collage"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "color": {
        "type": "theme-token"
      },
      "anchor": {
        "type": "position"
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 1.25,
      "maximum": 3.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "pin-board",
      "drop-settle",
      "paper-slide"
    ],
    "defaultMotion": "pin-board",
    "soundTags": [
      "paper.attach.soft",
      "motion.pin-board"
    ],
    "themeTokens": [
      "--paper-bg",
      "--paper-surface",
      "--paper-surface-alt",
      "--ink",
      "--ink-muted",
      "--primary",
      "--secondary",
      "--accent",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity",
      "--outline-width"
    ],
    "accessibilityLabel": "Paper-clip attachment animated paper component",
    "description": "A standalone paper clip that slides over an object edge.",
    "attachable": true,
    "bespokeMotion": true
  },
  {
    "id": "object.pushpin-attachment.paper-01",
    "name": "Pushpin attachment",
    "version": "1.1.0",
    "category": "paper-object",
    "subtype": "attachment",
    "cssClass": "obj-pushpin-attachment",
    "renderer": "pushpin-attachment",
    "intents": [
      "compose_paper_story",
      "display_attachment"
    ],
    "keywords": [
      "paper",
      "attachment",
      "pushpin",
      "attachment"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook",
      "bold-paper-collage"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "color": {
        "type": "theme-token"
      },
      "anchor": {
        "type": "position"
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 1.25,
      "maximum": 3.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "pin-board",
      "drop-settle",
      "paper-slide"
    ],
    "defaultMotion": "pin-board",
    "soundTags": [
      "paper.attach.soft",
      "motion.pin-board"
    ],
    "themeTokens": [
      "--paper-bg",
      "--paper-surface",
      "--paper-surface-alt",
      "--ink",
      "--ink-muted",
      "--primary",
      "--secondary",
      "--accent",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity",
      "--outline-width"
    ],
    "accessibilityLabel": "Pushpin attachment animated paper component",
    "description": "A dimensional pushpin attachable to boards and paper objects.",
    "attachable": true,
    "bespokeMotion": true
  },
  {
    "id": "object.string-connector.paper-01",
    "name": "String connector",
    "version": "1.1.0",
    "category": "paper-object",
    "subtype": "attachment",
    "cssClass": "obj-string-connector",
    "renderer": "string-connector",
    "intents": [
      "compose_paper_story",
      "display_attachment"
    ],
    "keywords": [
      "paper",
      "attachment",
      "string",
      "connector"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook",
      "bold-paper-collage"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "color": {
        "type": "theme-token"
      },
      "anchor": {
        "type": "position"
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 1.25,
      "maximum": 3.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "pin-board",
      "drop-settle",
      "paper-slide"
    ],
    "defaultMotion": "pin-board",
    "soundTags": [
      "paper.attach.soft",
      "motion.pin-board"
    ],
    "themeTokens": [
      "--paper-bg",
      "--paper-surface",
      "--paper-surface-alt",
      "--ink",
      "--ink-muted",
      "--primary",
      "--secondary",
      "--accent",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity",
      "--outline-width"
    ],
    "accessibilityLabel": "String connector animated paper component",
    "description": "A configurable curved string connector between two anchors.",
    "attachable": true,
    "bespokeMotion": true
  }
];
