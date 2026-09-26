window.NEX_TYPOGRAPHY = [
  {
    "id": "typography.chapter-opener.paper-01",
    "name": "Chapter opener",
    "version": "1.7.0",
    "category": "typography",
    "subtype": "display",
    "slug": "chapter-opener",
    "renderer": "chapter-opener",
    "order": 1,
    "intents": [
      "open_chapter",
      "introduce_section"
    ],
    "keywords": [
      "typography",
      "paper",
      "animated",
      "responsive",
      "display",
      "chapter opener",
      "open_chapter",
      "introduce_section"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "alignment": {
        "type": "enum",
        "values": [
          "left",
          "center",
          "right"
        ]
      },
      "emphasisWords": {
        "type": "array",
        "maximum": 6
      },
      "duration": {
        "type": "number",
        "minimum": 0.6,
        "recommended": 1.5,
        "maximum": 5
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      },
      "kicker": {
        "type": "string",
        "maxCharacters": 24,
        "guidance": "Maximum 24 characters; shorter copy is preferred."
      },
      "title": {
        "type": "string",
        "maxCharacters": 72,
        "guidance": "Maximum 72 characters; shorter copy is preferred."
      },
      "body": {
        "type": "string",
        "maxCharacters": 140,
        "guidance": "Maximum 140 characters; shorter copy is preferred."
      },
      "meta": {
        "type": "string",
        "maxCharacters": 32,
        "guidance": "Maximum 32 characters; shorter copy is preferred."
      }
    },
    "characterGuidance": {
      "kicker": 24,
      "title": 72,
      "body": 140,
      "meta": 32
    },
    "duration": {
      "minimum": 0.6,
      "recommended": 1.5,
      "maximum": 5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "ink-reveal"
    ],
    "defaultMotion": "paper-slide",
    "soundTags": [
      "typography.chapter-opener.soft",
      "paper.text.reveal"
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
    "accessibilityLabel": "Chapter opener animated paper typography component",
    "responsiveText": true,
    "editable": true,
    "scalable": true,
    "agentSelection": {
      "useWhen": [
        "open_chapter",
        "introduce_section"
      ],
      "semanticRole": "display",
      "copyGuidance": {
        "kicker": 24,
        "title": 72,
        "body": 140,
        "meta": 32
      }
    }
  },
  {
    "id": "typography.large-statement.paper-01",
    "name": "Large statement",
    "version": "1.7.0",
    "category": "typography",
    "subtype": "display",
    "slug": "large-statement",
    "renderer": "large-statement",
    "order": 2,
    "intents": [
      "make_bold_statement",
      "emphasize_message"
    ],
    "keywords": [
      "typography",
      "paper",
      "animated",
      "responsive",
      "display",
      "large statement",
      "make_bold_statement",
      "emphasize_message"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "alignment": {
        "type": "enum",
        "values": [
          "left",
          "center",
          "right"
        ]
      },
      "emphasisWords": {
        "type": "array",
        "maximum": 6
      },
      "duration": {
        "type": "number",
        "minimum": 0.6,
        "recommended": 1.5,
        "maximum": 5
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      },
      "title": {
        "type": "string",
        "maxCharacters": 110,
        "guidance": "Maximum 110 characters; shorter copy is preferred."
      },
      "body": {
        "type": "string",
        "maxCharacters": 180,
        "guidance": "Maximum 180 characters; shorter copy is preferred."
      }
    },
    "characterGuidance": {
      "title": 110,
      "body": 180
    },
    "duration": {
      "minimum": 0.6,
      "recommended": 1.5,
      "maximum": 5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "ink-reveal"
    ],
    "defaultMotion": "cut-paper-pop",
    "soundTags": [
      "typography.large-statement.soft",
      "paper.text.reveal"
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
    "accessibilityLabel": "Large statement animated paper typography component",
    "responsiveText": true,
    "editable": true,
    "scalable": true,
    "agentSelection": {
      "useWhen": [
        "make_bold_statement",
        "emphasize_message"
      ],
      "semanticRole": "display",
      "copyGuidance": {
        "title": 110,
        "body": 180
      }
    }
  },
  {
    "id": "typography.question-hook.paper-01",
    "name": "Question hook",
    "version": "1.7.0",
    "category": "typography",
    "subtype": "display",
    "slug": "question-hook",
    "renderer": "question-hook",
    "order": 3,
    "intents": [
      "ask_hook_question",
      "open_with_question"
    ],
    "keywords": [
      "typography",
      "paper",
      "animated",
      "responsive",
      "display",
      "question hook",
      "ask_hook_question",
      "open_with_question"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "alignment": {
        "type": "enum",
        "values": [
          "left",
          "center",
          "right"
        ]
      },
      "emphasisWords": {
        "type": "array",
        "maximum": 6
      },
      "duration": {
        "type": "number",
        "minimum": 0.6,
        "recommended": 1.5,
        "maximum": 5
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      },
      "title": {
        "type": "string",
        "maxCharacters": 110,
        "guidance": "Maximum 110 characters; shorter copy is preferred."
      },
      "body": {
        "type": "string",
        "maxCharacters": 150,
        "guidance": "Maximum 150 characters; shorter copy is preferred."
      }
    },
    "characterGuidance": {
      "title": 110,
      "body": 150
    },
    "duration": {
      "minimum": 0.6,
      "recommended": 1.5,
      "maximum": 5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "ink-reveal"
    ],
    "defaultMotion": "ink-reveal",
    "soundTags": [
      "typography.question-hook.soft",
      "paper.text.reveal"
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
    "accessibilityLabel": "Question hook animated paper typography component",
    "responsiveText": true,
    "editable": true,
    "scalable": true,
    "agentSelection": {
      "useWhen": [
        "ask_hook_question",
        "open_with_question"
      ],
      "semanticRole": "display",
      "copyGuidance": {
        "title": 110,
        "body": 150
      }
    }
  },
  {
    "id": "typography.quote-card.paper-01",
    "name": "Quote card",
    "version": "1.7.0",
    "category": "typography",
    "subtype": "editorial",
    "slug": "quote-card",
    "renderer": "quote-card",
    "order": 4,
    "intents": [
      "show_quote",
      "attribute_statement"
    ],
    "keywords": [
      "typography",
      "paper",
      "animated",
      "responsive",
      "editorial",
      "quote card",
      "show_quote",
      "attribute_statement"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "alignment": {
        "type": "enum",
        "values": [
          "left",
          "center",
          "right"
        ]
      },
      "emphasisWords": {
        "type": "array",
        "maximum": 6
      },
      "duration": {
        "type": "number",
        "minimum": 0.6,
        "recommended": 1.5,
        "maximum": 5
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      },
      "title": {
        "type": "string",
        "maxCharacters": 220,
        "guidance": "Maximum 220 characters; shorter copy is preferred."
      },
      "meta": {
        "type": "string",
        "maxCharacters": 72,
        "guidance": "Maximum 72 characters; shorter copy is preferred."
      }
    },
    "characterGuidance": {
      "title": 220,
      "meta": 72
    },
    "duration": {
      "minimum": 0.6,
      "recommended": 1.5,
      "maximum": 5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "ink-reveal"
    ],
    "defaultMotion": "paper-slide",
    "soundTags": [
      "typography.quote-card.soft",
      "paper.text.reveal"
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
    "accessibilityLabel": "Quote card animated paper typography component",
    "responsiveText": true,
    "editable": true,
    "scalable": true,
    "agentSelection": {
      "useWhen": [
        "show_quote",
        "attribute_statement"
      ],
      "semanticRole": "editorial",
      "copyGuidance": {
        "title": 220,
        "meta": 72
      }
    }
  },
  {
    "id": "typography.definition-card.paper-01",
    "name": "Definition card",
    "version": "1.7.0",
    "category": "typography",
    "subtype": "editorial",
    "slug": "definition-card",
    "renderer": "definition-card",
    "order": 5,
    "intents": [
      "define_term",
      "explain_concept"
    ],
    "keywords": [
      "typography",
      "paper",
      "animated",
      "responsive",
      "editorial",
      "definition card",
      "define_term",
      "explain_concept"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "alignment": {
        "type": "enum",
        "values": [
          "left",
          "center",
          "right"
        ]
      },
      "emphasisWords": {
        "type": "array",
        "maximum": 6
      },
      "duration": {
        "type": "number",
        "minimum": 0.6,
        "recommended": 1.5,
        "maximum": 5
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      },
      "title": {
        "type": "string",
        "maxCharacters": 48,
        "guidance": "Maximum 48 characters; shorter copy is preferred."
      },
      "body": {
        "type": "string",
        "maxCharacters": 220,
        "guidance": "Maximum 220 characters; shorter copy is preferred."
      },
      "meta": {
        "type": "string",
        "maxCharacters": 60,
        "guidance": "Maximum 60 characters; shorter copy is preferred."
      }
    },
    "characterGuidance": {
      "title": 48,
      "body": 220,
      "meta": 60
    },
    "duration": {
      "minimum": 0.6,
      "recommended": 1.5,
      "maximum": 5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "ink-reveal"
    ],
    "defaultMotion": "cut-paper-pop",
    "soundTags": [
      "typography.definition-card.soft",
      "paper.text.reveal"
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
    "accessibilityLabel": "Definition card animated paper typography component",
    "responsiveText": true,
    "editable": true,
    "scalable": true,
    "agentSelection": {
      "useWhen": [
        "define_term",
        "explain_concept"
      ],
      "semanticRole": "editorial",
      "copyGuidance": {
        "title": 48,
        "body": 220,
        "meta": 60
      }
    }
  },
  {
    "id": "typography.numbered-list.paper-01",
    "name": "Numbered list",
    "version": "1.7.0",
    "category": "typography",
    "subtype": "list",
    "slug": "numbered-list",
    "renderer": "numbered-list",
    "order": 6,
    "intents": [
      "show_numbered_steps",
      "present_sequence"
    ],
    "keywords": [
      "typography",
      "paper",
      "animated",
      "responsive",
      "list",
      "numbered list",
      "show_numbered_steps",
      "present_sequence"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "alignment": {
        "type": "enum",
        "values": [
          "left",
          "center",
          "right"
        ]
      },
      "emphasisWords": {
        "type": "array",
        "maximum": 6
      },
      "duration": {
        "type": "number",
        "minimum": 0.6,
        "recommended": 1.5,
        "maximum": 5
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      },
      "title": {
        "type": "string",
        "maxCharacters": 54,
        "guidance": "Maximum 54 characters; shorter copy is preferred."
      },
      "items": {
        "type": "array",
        "maximumItems": 5,
        "itemMaxCharacters": 78
      }
    },
    "characterGuidance": {
      "title": 54,
      "items": 5,
      "itemCharacters": 78
    },
    "duration": {
      "minimum": 0.6,
      "recommended": 1.5,
      "maximum": 5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "ink-reveal"
    ],
    "defaultMotion": "ink-reveal",
    "soundTags": [
      "typography.numbered-list.soft",
      "paper.text.reveal"
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
    "accessibilityLabel": "Numbered list animated paper typography component",
    "responsiveText": true,
    "editable": true,
    "scalable": true,
    "agentSelection": {
      "useWhen": [
        "show_numbered_steps",
        "present_sequence"
      ],
      "semanticRole": "list",
      "copyGuidance": {
        "title": 54,
        "items": 5,
        "itemCharacters": 78
      }
    }
  },
  {
    "id": "typography.bullet-list.paper-01",
    "name": "Bullet list",
    "version": "1.7.0",
    "category": "typography",
    "subtype": "list",
    "slug": "bullet-list",
    "renderer": "bullet-list",
    "order": 7,
    "intents": [
      "show_bullet_points",
      "summarize_points"
    ],
    "keywords": [
      "typography",
      "paper",
      "animated",
      "responsive",
      "list",
      "bullet list",
      "show_bullet_points",
      "summarize_points"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "alignment": {
        "type": "enum",
        "values": [
          "left",
          "center",
          "right"
        ]
      },
      "emphasisWords": {
        "type": "array",
        "maximum": 6
      },
      "duration": {
        "type": "number",
        "minimum": 0.6,
        "recommended": 1.5,
        "maximum": 5
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      },
      "title": {
        "type": "string",
        "maxCharacters": 54,
        "guidance": "Maximum 54 characters; shorter copy is preferred."
      },
      "items": {
        "type": "array",
        "maximumItems": 6,
        "itemMaxCharacters": 72
      }
    },
    "characterGuidance": {
      "title": 54,
      "items": 6,
      "itemCharacters": 72
    },
    "duration": {
      "minimum": 0.6,
      "recommended": 1.5,
      "maximum": 5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "ink-reveal"
    ],
    "defaultMotion": "paper-slide",
    "soundTags": [
      "typography.bullet-list.soft",
      "paper.text.reveal"
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
    "accessibilityLabel": "Bullet list animated paper typography component",
    "responsiveText": true,
    "editable": true,
    "scalable": true,
    "agentSelection": {
      "useWhen": [
        "show_bullet_points",
        "summarize_points"
      ],
      "semanticRole": "list",
      "copyGuidance": {
        "title": 54,
        "items": 6,
        "itemCharacters": 72
      }
    }
  },
  {
    "id": "typography.word-by-word-emphasis.paper-01",
    "name": "Word-by-word emphasis",
    "version": "1.7.0",
    "category": "typography",
    "subtype": "emphasis",
    "slug": "word-by-word-emphasis",
    "renderer": "word-by-word-emphasis",
    "order": 8,
    "intents": [
      "emphasize_words_sequentially",
      "animate_phrase"
    ],
    "keywords": [
      "typography",
      "paper",
      "animated",
      "responsive",
      "emphasis",
      "word by word emphasis",
      "emphasize_words_sequentially",
      "animate_phrase"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "alignment": {
        "type": "enum",
        "values": [
          "left",
          "center",
          "right"
        ]
      },
      "emphasisWords": {
        "type": "array",
        "maximum": 6
      },
      "duration": {
        "type": "number",
        "minimum": 0.6,
        "recommended": 1.5,
        "maximum": 5
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      },
      "title": {
        "type": "string",
        "maxCharacters": 120,
        "guidance": "Maximum 120 characters; shorter copy is preferred."
      }
    },
    "characterGuidance": {
      "title": 120,
      "emphasisWords": 6
    },
    "duration": {
      "minimum": 0.6,
      "recommended": 1.5,
      "maximum": 5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "ink-reveal"
    ],
    "defaultMotion": "cut-paper-pop",
    "soundTags": [
      "typography.word-by-word-emphasis.soft",
      "paper.text.reveal"
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
    "accessibilityLabel": "Word-by-word emphasis animated paper typography component",
    "responsiveText": true,
    "editable": true,
    "scalable": true,
    "agentSelection": {
      "useWhen": [
        "emphasize_words_sequentially",
        "animate_phrase"
      ],
      "semanticRole": "emphasis",
      "copyGuidance": {
        "title": 120,
        "emphasisWords": 6
      }
    }
  },
  {
    "id": "typography.marker-highlight.paper-01",
    "name": "Marker highlight",
    "version": "1.7.0",
    "category": "typography",
    "subtype": "emphasis",
    "slug": "marker-highlight",
    "renderer": "marker-highlight",
    "order": 9,
    "intents": [
      "highlight_phrase",
      "mark_key_text"
    ],
    "keywords": [
      "typography",
      "paper",
      "animated",
      "responsive",
      "emphasis",
      "marker highlight",
      "highlight_phrase",
      "mark_key_text"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "alignment": {
        "type": "enum",
        "values": [
          "left",
          "center",
          "right"
        ]
      },
      "emphasisWords": {
        "type": "array",
        "maximum": 4
      },
      "duration": {
        "type": "number",
        "minimum": 0.6,
        "recommended": 1.5,
        "maximum": 5
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      },
      "title": {
        "type": "string",
        "maxCharacters": 120,
        "guidance": "Maximum 120 characters; shorter copy is preferred."
      },
      "body": {
        "type": "string",
        "maxCharacters": 130,
        "guidance": "Maximum 130 characters; shorter copy is preferred."
      }
    },
    "characterGuidance": {
      "title": 120,
      "body": 130,
      "emphasisWords": 4
    },
    "duration": {
      "minimum": 0.6,
      "recommended": 1.5,
      "maximum": 5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "ink-reveal"
    ],
    "defaultMotion": "ink-reveal",
    "soundTags": [
      "typography.marker-highlight.soft",
      "paper.text.reveal"
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
    "accessibilityLabel": "Marker highlight animated paper typography component",
    "responsiveText": true,
    "editable": true,
    "scalable": true,
    "agentSelection": {
      "useWhen": [
        "highlight_phrase",
        "mark_key_text"
      ],
      "semanticRole": "emphasis",
      "copyGuidance": {
        "title": 120,
        "body": 130,
        "emphasisWords": 4
      }
    }
  },
  {
    "id": "typography.scribble-underline.paper-01",
    "name": "Scribble underline",
    "version": "1.7.0",
    "category": "typography",
    "subtype": "emphasis",
    "slug": "scribble-underline",
    "renderer": "scribble-underline",
    "order": 10,
    "intents": [
      "underline_phrase",
      "emphasize_text"
    ],
    "keywords": [
      "typography",
      "paper",
      "animated",
      "responsive",
      "emphasis",
      "scribble underline",
      "underline_phrase",
      "emphasize_text"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "alignment": {
        "type": "enum",
        "values": [
          "left",
          "center",
          "right"
        ]
      },
      "emphasisWords": {
        "type": "array",
        "maximum": 4
      },
      "duration": {
        "type": "number",
        "minimum": 0.6,
        "recommended": 1.5,
        "maximum": 5
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      },
      "title": {
        "type": "string",
        "maxCharacters": 110,
        "guidance": "Maximum 110 characters; shorter copy is preferred."
      },
      "body": {
        "type": "string",
        "maxCharacters": 130,
        "guidance": "Maximum 130 characters; shorter copy is preferred."
      }
    },
    "characterGuidance": {
      "title": 110,
      "body": 130,
      "emphasisWords": 4
    },
    "duration": {
      "minimum": 0.6,
      "recommended": 1.5,
      "maximum": 5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "ink-reveal"
    ],
    "defaultMotion": "paper-slide",
    "soundTags": [
      "typography.scribble-underline.soft",
      "paper.text.reveal"
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
    "accessibilityLabel": "Scribble underline animated paper typography component",
    "responsiveText": true,
    "editable": true,
    "scalable": true,
    "agentSelection": {
      "useWhen": [
        "underline_phrase",
        "emphasize_text"
      ],
      "semanticRole": "emphasis",
      "copyGuidance": {
        "title": 110,
        "body": 130,
        "emphasisWords": 4
      }
    }
  },
  {
    "id": "typography.circled-phrase.paper-01",
    "name": "Circled phrase",
    "version": "1.7.0",
    "category": "typography",
    "subtype": "emphasis",
    "slug": "circled-phrase",
    "renderer": "circled-phrase",
    "order": 11,
    "intents": [
      "circle_phrase",
      "call_attention"
    ],
    "keywords": [
      "typography",
      "paper",
      "animated",
      "responsive",
      "emphasis",
      "circled phrase",
      "circle_phrase",
      "call_attention"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "alignment": {
        "type": "enum",
        "values": [
          "left",
          "center",
          "right"
        ]
      },
      "emphasisWords": {
        "type": "array",
        "maximum": 4
      },
      "duration": {
        "type": "number",
        "minimum": 0.6,
        "recommended": 1.5,
        "maximum": 5
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      },
      "title": {
        "type": "string",
        "maxCharacters": 110,
        "guidance": "Maximum 110 characters; shorter copy is preferred."
      },
      "body": {
        "type": "string",
        "maxCharacters": 130,
        "guidance": "Maximum 130 characters; shorter copy is preferred."
      }
    },
    "characterGuidance": {
      "title": 110,
      "body": 130,
      "emphasisWords": 4
    },
    "duration": {
      "minimum": 0.6,
      "recommended": 1.5,
      "maximum": 5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "ink-reveal"
    ],
    "defaultMotion": "cut-paper-pop",
    "soundTags": [
      "typography.circled-phrase.soft",
      "paper.text.reveal"
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
    "accessibilityLabel": "Circled phrase animated paper typography component",
    "responsiveText": true,
    "editable": true,
    "scalable": true,
    "agentSelection": {
      "useWhen": [
        "circle_phrase",
        "call_attention"
      ],
      "semanticRole": "emphasis",
      "copyGuidance": {
        "title": 110,
        "body": 130,
        "emphasisWords": 4
      }
    }
  },
  {
    "id": "typography.crossed-out-phrase.paper-01",
    "name": "Crossed-out phrase",
    "version": "1.7.0",
    "category": "typography",
    "subtype": "emphasis",
    "slug": "crossed-out-phrase",
    "renderer": "crossed-out-phrase",
    "order": 12,
    "intents": [
      "cross_out_phrase",
      "show_revision"
    ],
    "keywords": [
      "typography",
      "paper",
      "animated",
      "responsive",
      "emphasis",
      "crossed out phrase",
      "cross_out_phrase",
      "show_revision"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "alignment": {
        "type": "enum",
        "values": [
          "left",
          "center",
          "right"
        ]
      },
      "emphasisWords": {
        "type": "array",
        "maximum": 4
      },
      "duration": {
        "type": "number",
        "minimum": 0.6,
        "recommended": 1.5,
        "maximum": 5
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      },
      "title": {
        "type": "string",
        "maxCharacters": 110,
        "guidance": "Maximum 110 characters; shorter copy is preferred."
      },
      "body": {
        "type": "string",
        "maxCharacters": 130,
        "guidance": "Maximum 130 characters; shorter copy is preferred."
      }
    },
    "characterGuidance": {
      "title": 110,
      "body": 130,
      "emphasisWords": 4
    },
    "duration": {
      "minimum": 0.6,
      "recommended": 1.5,
      "maximum": 5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "ink-reveal"
    ],
    "defaultMotion": "ink-reveal",
    "soundTags": [
      "typography.crossed-out-phrase.soft",
      "paper.text.reveal"
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
    "accessibilityLabel": "Crossed-out phrase animated paper typography component",
    "responsiveText": true,
    "editable": true,
    "scalable": true,
    "agentSelection": {
      "useWhen": [
        "cross_out_phrase",
        "show_revision"
      ],
      "semanticRole": "emphasis",
      "copyGuidance": {
        "title": 110,
        "body": 130,
        "emphasisWords": 4
      }
    }
  },
  {
    "id": "typography.typewriter-note.paper-01",
    "name": "Typewriter note",
    "version": "1.7.0",
    "category": "typography",
    "subtype": "editorial",
    "slug": "typewriter-note",
    "renderer": "typewriter-note",
    "order": 13,
    "intents": [
      "show_typed_note",
      "reveal_note"
    ],
    "keywords": [
      "typography",
      "paper",
      "animated",
      "responsive",
      "editorial",
      "typewriter note",
      "show_typed_note",
      "reveal_note"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "alignment": {
        "type": "enum",
        "values": [
          "left",
          "center",
          "right"
        ]
      },
      "emphasisWords": {
        "type": "array",
        "maximum": 6
      },
      "duration": {
        "type": "number",
        "minimum": 0.6,
        "recommended": 1.5,
        "maximum": 5
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      },
      "title": {
        "type": "string",
        "maxCharacters": 52,
        "guidance": "Maximum 52 characters; shorter copy is preferred."
      },
      "body": {
        "type": "string",
        "maxCharacters": 260,
        "guidance": "Maximum 260 characters; shorter copy is preferred."
      },
      "meta": {
        "type": "string",
        "maxCharacters": 48,
        "guidance": "Maximum 48 characters; shorter copy is preferred."
      }
    },
    "characterGuidance": {
      "title": 52,
      "body": 260,
      "meta": 48
    },
    "duration": {
      "minimum": 0.6,
      "recommended": 1.5,
      "maximum": 5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "ink-reveal"
    ],
    "defaultMotion": "paper-slide",
    "soundTags": [
      "typography.typewriter-note.soft",
      "paper.text.reveal"
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
    "accessibilityLabel": "Typewriter note animated paper typography component",
    "responsiveText": true,
    "editable": true,
    "scalable": true,
    "agentSelection": {
      "useWhen": [
        "show_typed_note",
        "reveal_note"
      ],
      "semanticRole": "editorial",
      "copyGuidance": {
        "title": 52,
        "body": 260,
        "meta": 48
      }
    }
  },
  {
    "id": "typography.kinetic-keyword.paper-01",
    "name": "Kinetic keyword",
    "version": "1.7.0",
    "category": "typography",
    "subtype": "display",
    "slug": "kinetic-keyword",
    "renderer": "kinetic-keyword",
    "order": 14,
    "intents": [
      "animate_keyword",
      "emphasize_single_word"
    ],
    "keywords": [
      "typography",
      "paper",
      "animated",
      "responsive",
      "display",
      "kinetic keyword",
      "animate_keyword",
      "emphasize_single_word"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "alignment": {
        "type": "enum",
        "values": [
          "left",
          "center",
          "right"
        ]
      },
      "emphasisWords": {
        "type": "array",
        "maximum": 6
      },
      "duration": {
        "type": "number",
        "minimum": 0.6,
        "recommended": 1.5,
        "maximum": 5
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      },
      "title": {
        "type": "string",
        "maxCharacters": 28,
        "guidance": "Maximum 28 characters; shorter copy is preferred."
      },
      "body": {
        "type": "string",
        "maxCharacters": 110,
        "guidance": "Maximum 110 characters; shorter copy is preferred."
      }
    },
    "characterGuidance": {
      "title": 28,
      "body": 110
    },
    "duration": {
      "minimum": 0.6,
      "recommended": 1.5,
      "maximum": 5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "ink-reveal"
    ],
    "defaultMotion": "cut-paper-pop",
    "soundTags": [
      "typography.kinetic-keyword.soft",
      "paper.text.reveal"
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
    "accessibilityLabel": "Kinetic keyword animated paper typography component",
    "responsiveText": true,
    "editable": true,
    "scalable": true,
    "agentSelection": {
      "useWhen": [
        "animate_keyword",
        "emphasize_single_word"
      ],
      "semanticRole": "display",
      "copyGuidance": {
        "title": 28,
        "body": 110
      }
    }
  },
  {
    "id": "typography.statistic-headline.paper-01",
    "name": "Statistic headline",
    "version": "1.7.0",
    "category": "typography",
    "subtype": "data",
    "slug": "statistic-headline",
    "renderer": "statistic-headline",
    "order": 15,
    "intents": [
      "show_statistic",
      "emphasize_metric"
    ],
    "keywords": [
      "typography",
      "paper",
      "animated",
      "responsive",
      "data",
      "statistic headline",
      "show_statistic",
      "emphasize_metric"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "alignment": {
        "type": "enum",
        "values": [
          "left",
          "center",
          "right"
        ]
      },
      "emphasisWords": {
        "type": "array",
        "maximum": 6
      },
      "duration": {
        "type": "number",
        "minimum": 0.6,
        "recommended": 1.5,
        "maximum": 5
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      },
      "value": {
        "type": "string",
        "maxCharacters": 16,
        "guidance": "Maximum 16 characters; shorter copy is preferred."
      },
      "title": {
        "type": "string",
        "maxCharacters": 72,
        "guidance": "Maximum 72 characters; shorter copy is preferred."
      },
      "body": {
        "type": "string",
        "maxCharacters": 120,
        "guidance": "Maximum 120 characters; shorter copy is preferred."
      },
      "meta": {
        "type": "string",
        "maxCharacters": 48,
        "guidance": "Maximum 48 characters; shorter copy is preferred."
      }
    },
    "characterGuidance": {
      "value": 16,
      "title": 72,
      "body": 120,
      "meta": 48
    },
    "duration": {
      "minimum": 0.6,
      "recommended": 1.5,
      "maximum": 5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "ink-reveal"
    ],
    "defaultMotion": "ink-reveal",
    "soundTags": [
      "typography.statistic-headline.soft",
      "paper.text.reveal"
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
    "accessibilityLabel": "Statistic headline animated paper typography component",
    "responsiveText": true,
    "editable": true,
    "scalable": true,
    "agentSelection": {
      "useWhen": [
        "show_statistic",
        "emphasize_metric"
      ],
      "semanticRole": "data",
      "copyGuidance": {
        "value": 16,
        "title": 72,
        "body": 120,
        "meta": 48
      }
    }
  },
  {
    "id": "typography.name-role-card.paper-01",
    "name": "Name and role card",
    "version": "1.7.0",
    "category": "typography",
    "subtype": "identity",
    "slug": "name-role-card",
    "renderer": "name-role-card",
    "order": 16,
    "intents": [
      "identify_person",
      "show_name_and_role"
    ],
    "keywords": [
      "typography",
      "paper",
      "animated",
      "responsive",
      "identity",
      "name role card",
      "identify_person",
      "show_name_and_role"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "alignment": {
        "type": "enum",
        "values": [
          "left",
          "center",
          "right"
        ]
      },
      "emphasisWords": {
        "type": "array",
        "maximum": 6
      },
      "duration": {
        "type": "number",
        "minimum": 0.6,
        "recommended": 1.5,
        "maximum": 5
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      },
      "title": {
        "type": "string",
        "maxCharacters": 56,
        "guidance": "Maximum 56 characters; shorter copy is preferred."
      },
      "body": {
        "type": "string",
        "maxCharacters": 70,
        "guidance": "Maximum 70 characters; shorter copy is preferred."
      },
      "meta": {
        "type": "string",
        "maxCharacters": 70,
        "guidance": "Maximum 70 characters; shorter copy is preferred."
      }
    },
    "characterGuidance": {
      "title": 56,
      "body": 70,
      "meta": 70
    },
    "duration": {
      "minimum": 0.6,
      "recommended": 1.5,
      "maximum": 5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "ink-reveal"
    ],
    "defaultMotion": "paper-slide",
    "soundTags": [
      "typography.name-role-card.soft",
      "paper.text.reveal"
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
    "accessibilityLabel": "Name and role card animated paper typography component",
    "responsiveText": true,
    "editable": true,
    "scalable": true,
    "agentSelection": {
      "useWhen": [
        "identify_person",
        "show_name_and_role"
      ],
      "semanticRole": "identity",
      "copyGuidance": {
        "title": 56,
        "body": 70,
        "meta": 70
      }
    }
  },
  {
    "id": "typography.date-location-label.paper-01",
    "name": "Date and location label",
    "version": "1.7.0",
    "category": "typography",
    "subtype": "identity",
    "slug": "date-location-label",
    "renderer": "date-location-label",
    "order": 17,
    "intents": [
      "show_date_and_location",
      "set_context"
    ],
    "keywords": [
      "typography",
      "paper",
      "animated",
      "responsive",
      "identity",
      "date location label",
      "show_date_and_location",
      "set_context"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "alignment": {
        "type": "enum",
        "values": [
          "left",
          "center",
          "right"
        ]
      },
      "emphasisWords": {
        "type": "array",
        "maximum": 6
      },
      "duration": {
        "type": "number",
        "minimum": 0.6,
        "recommended": 1.5,
        "maximum": 5
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      },
      "title": {
        "type": "string",
        "maxCharacters": 42,
        "guidance": "Maximum 42 characters; shorter copy is preferred."
      },
      "body": {
        "type": "string",
        "maxCharacters": 70,
        "guidance": "Maximum 70 characters; shorter copy is preferred."
      },
      "meta": {
        "type": "string",
        "maxCharacters": 60,
        "guidance": "Maximum 60 characters; shorter copy is preferred."
      }
    },
    "characterGuidance": {
      "title": 42,
      "body": 70,
      "meta": 60
    },
    "duration": {
      "minimum": 0.6,
      "recommended": 1.5,
      "maximum": 5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "ink-reveal"
    ],
    "defaultMotion": "cut-paper-pop",
    "soundTags": [
      "typography.date-location-label.soft",
      "paper.text.reveal"
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
    "accessibilityLabel": "Date and location label animated paper typography component",
    "responsiveText": true,
    "editable": true,
    "scalable": true,
    "agentSelection": {
      "useWhen": [
        "show_date_and_location",
        "set_context"
      ],
      "semanticRole": "identity",
      "copyGuidance": {
        "title": 42,
        "body": 70,
        "meta": 60
      }
    }
  },
  {
    "id": "typography.source-citation.paper-01",
    "name": "Source citation",
    "version": "1.7.0",
    "category": "typography",
    "subtype": "reference",
    "slug": "source-citation",
    "renderer": "source-citation",
    "order": 18,
    "intents": [
      "cite_source",
      "show_attribution"
    ],
    "keywords": [
      "typography",
      "paper",
      "animated",
      "responsive",
      "reference",
      "source citation",
      "cite_source",
      "show_attribution"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "alignment": {
        "type": "enum",
        "values": [
          "left",
          "center",
          "right"
        ]
      },
      "emphasisWords": {
        "type": "array",
        "maximum": 6
      },
      "duration": {
        "type": "number",
        "minimum": 0.6,
        "recommended": 1.5,
        "maximum": 5
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      },
      "title": {
        "type": "string",
        "maxCharacters": 100,
        "guidance": "Maximum 100 characters; shorter copy is preferred."
      },
      "body": {
        "type": "string",
        "maxCharacters": 160,
        "guidance": "Maximum 160 characters; shorter copy is preferred."
      },
      "meta": {
        "type": "string",
        "maxCharacters": 110,
        "guidance": "Maximum 110 characters; shorter copy is preferred."
      }
    },
    "characterGuidance": {
      "title": 100,
      "body": 160,
      "meta": 110
    },
    "duration": {
      "minimum": 0.6,
      "recommended": 1.5,
      "maximum": 5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "ink-reveal"
    ],
    "defaultMotion": "ink-reveal",
    "soundTags": [
      "typography.source-citation.soft",
      "paper.text.reveal"
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
    "accessibilityLabel": "Source citation animated paper typography component",
    "responsiveText": true,
    "editable": true,
    "scalable": true,
    "agentSelection": {
      "useWhen": [
        "cite_source",
        "show_attribution"
      ],
      "semanticRole": "reference",
      "copyGuidance": {
        "title": 100,
        "body": 160,
        "meta": 110
      }
    }
  },
  {
    "id": "typography.footnote.paper-01",
    "name": "Footnote",
    "version": "1.7.0",
    "category": "typography",
    "subtype": "reference",
    "slug": "footnote",
    "renderer": "footnote",
    "order": 19,
    "intents": [
      "show_footnote",
      "add_context_note"
    ],
    "keywords": [
      "typography",
      "paper",
      "animated",
      "responsive",
      "reference",
      "footnote",
      "show_footnote",
      "add_context_note"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "alignment": {
        "type": "enum",
        "values": [
          "left",
          "center",
          "right"
        ]
      },
      "emphasisWords": {
        "type": "array",
        "maximum": 6
      },
      "duration": {
        "type": "number",
        "minimum": 0.6,
        "recommended": 1.5,
        "maximum": 5
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      },
      "title": {
        "type": "string",
        "maxCharacters": 12,
        "guidance": "Maximum 12 characters; shorter copy is preferred."
      },
      "body": {
        "type": "string",
        "maxCharacters": 220,
        "guidance": "Maximum 220 characters; shorter copy is preferred."
      },
      "meta": {
        "type": "string",
        "maxCharacters": 70,
        "guidance": "Maximum 70 characters; shorter copy is preferred."
      }
    },
    "characterGuidance": {
      "title": 12,
      "body": 220,
      "meta": 70
    },
    "duration": {
      "minimum": 0.6,
      "recommended": 1.5,
      "maximum": 5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "ink-reveal"
    ],
    "defaultMotion": "paper-slide",
    "soundTags": [
      "typography.footnote.soft",
      "paper.text.reveal"
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
    "accessibilityLabel": "Footnote animated paper typography component",
    "responsiveText": true,
    "editable": true,
    "scalable": true,
    "agentSelection": {
      "useWhen": [
        "show_footnote",
        "add_context_note"
      ],
      "semanticRole": "reference",
      "copyGuidance": {
        "title": 12,
        "body": 220,
        "meta": 70
      }
    }
  },
  {
    "id": "typography.subtitle-card.paper-01",
    "name": "Subtitle card",
    "version": "1.7.0",
    "category": "typography",
    "subtype": "caption",
    "slug": "subtitle-card",
    "renderer": "subtitle-card",
    "order": 20,
    "intents": [
      "show_subtitle",
      "caption_speech"
    ],
    "keywords": [
      "typography",
      "paper",
      "animated",
      "responsive",
      "caption",
      "subtitle card",
      "show_subtitle",
      "caption_speech"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "alignment": {
        "type": "enum",
        "values": [
          "left",
          "center",
          "right"
        ]
      },
      "emphasisWords": {
        "type": "array",
        "maximum": 6
      },
      "duration": {
        "type": "number",
        "minimum": 0.6,
        "recommended": 1.5,
        "maximum": 5
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      },
      "title": {
        "type": "string",
        "maxCharacters": 42,
        "guidance": "Maximum 42 characters; shorter copy is preferred."
      },
      "body": {
        "type": "string",
        "maxCharacters": 150,
        "guidance": "Maximum 150 characters; shorter copy is preferred."
      },
      "meta": {
        "type": "string",
        "maxCharacters": 44,
        "guidance": "Maximum 44 characters; shorter copy is preferred."
      }
    },
    "characterGuidance": {
      "title": 42,
      "body": 150,
      "meta": 44
    },
    "duration": {
      "minimum": 0.6,
      "recommended": 1.5,
      "maximum": 5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "ink-reveal"
    ],
    "defaultMotion": "cut-paper-pop",
    "soundTags": [
      "typography.subtitle-card.soft",
      "paper.text.reveal"
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
    "accessibilityLabel": "Subtitle card animated paper typography component",
    "responsiveText": true,
    "editable": true,
    "scalable": true,
    "agentSelection": {
      "useWhen": [
        "show_subtitle",
        "caption_speech"
      ],
      "semanticRole": "caption",
      "copyGuidance": {
        "title": 42,
        "body": 150,
        "meta": 44
      }
    }
  },
  {
    "id": "typography.speaker-identification.paper-01",
    "name": "Speaker identification",
    "version": "1.7.0",
    "category": "typography",
    "subtype": "identity",
    "slug": "speaker-identification",
    "renderer": "speaker-identification",
    "order": 21,
    "intents": [
      "identify_speaker",
      "label_voice"
    ],
    "keywords": [
      "typography",
      "paper",
      "animated",
      "responsive",
      "identity",
      "speaker identification",
      "identify_speaker",
      "label_voice"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "alignment": {
        "type": "enum",
        "values": [
          "left",
          "center",
          "right"
        ]
      },
      "emphasisWords": {
        "type": "array",
        "maximum": 6
      },
      "duration": {
        "type": "number",
        "minimum": 0.6,
        "recommended": 1.5,
        "maximum": 5
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      },
      "title": {
        "type": "string",
        "maxCharacters": 52,
        "guidance": "Maximum 52 characters; shorter copy is preferred."
      },
      "body": {
        "type": "string",
        "maxCharacters": 65,
        "guidance": "Maximum 65 characters; shorter copy is preferred."
      },
      "meta": {
        "type": "string",
        "maxCharacters": 60,
        "guidance": "Maximum 60 characters; shorter copy is preferred."
      }
    },
    "characterGuidance": {
      "title": 52,
      "body": 65,
      "meta": 60
    },
    "duration": {
      "minimum": 0.6,
      "recommended": 1.5,
      "maximum": 5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "ink-reveal"
    ],
    "defaultMotion": "ink-reveal",
    "soundTags": [
      "typography.speaker-identification.soft",
      "paper.text.reveal"
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
    "accessibilityLabel": "Speaker identification animated paper typography component",
    "responsiveText": true,
    "editable": true,
    "scalable": true,
    "agentSelection": {
      "useWhen": [
        "identify_speaker",
        "label_voice"
      ],
      "semanticRole": "identity",
      "copyGuidance": {
        "title": 52,
        "body": 65,
        "meta": 60
      }
    }
  },
  {
    "id": "typography.callout-label.paper-01",
    "name": "Callout label",
    "version": "1.7.0",
    "category": "typography",
    "subtype": "annotation",
    "slug": "callout-label",
    "renderer": "callout-label",
    "order": 22,
    "intents": [
      "label_feature",
      "point_to_detail"
    ],
    "keywords": [
      "typography",
      "paper",
      "animated",
      "responsive",
      "annotation",
      "callout label",
      "label_feature",
      "point_to_detail"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "alignment": {
        "type": "enum",
        "values": [
          "left",
          "center",
          "right"
        ]
      },
      "emphasisWords": {
        "type": "array",
        "maximum": 6
      },
      "duration": {
        "type": "number",
        "minimum": 0.6,
        "recommended": 1.5,
        "maximum": 5
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      },
      "title": {
        "type": "string",
        "maxCharacters": 50,
        "guidance": "Maximum 50 characters; shorter copy is preferred."
      },
      "body": {
        "type": "string",
        "maxCharacters": 120,
        "guidance": "Maximum 120 characters; shorter copy is preferred."
      },
      "meta": {
        "type": "string",
        "maxCharacters": 50,
        "guidance": "Maximum 50 characters; shorter copy is preferred."
      }
    },
    "characterGuidance": {
      "title": 50,
      "body": 120,
      "meta": 50
    },
    "duration": {
      "minimum": 0.6,
      "recommended": 1.5,
      "maximum": 5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "ink-reveal"
    ],
    "defaultMotion": "paper-slide",
    "soundTags": [
      "typography.callout-label.soft",
      "paper.text.reveal"
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
    "accessibilityLabel": "Callout label animated paper typography component",
    "responsiveText": true,
    "editable": true,
    "scalable": true,
    "agentSelection": {
      "useWhen": [
        "label_feature",
        "point_to_detail"
      ],
      "semanticRole": "annotation",
      "copyGuidance": {
        "title": 50,
        "body": 120,
        "meta": 50
      }
    }
  },
  {
    "id": "typography.warning-note.paper-01",
    "name": "Warning note",
    "version": "1.7.0",
    "category": "typography",
    "subtype": "annotation",
    "slug": "warning-note",
    "renderer": "warning-note",
    "order": 23,
    "intents": [
      "show_warning",
      "communicate_caution"
    ],
    "keywords": [
      "typography",
      "paper",
      "animated",
      "responsive",
      "annotation",
      "warning note",
      "show_warning",
      "communicate_caution"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "alignment": {
        "type": "enum",
        "values": [
          "left",
          "center",
          "right"
        ]
      },
      "emphasisWords": {
        "type": "array",
        "maximum": 6
      },
      "duration": {
        "type": "number",
        "minimum": 0.6,
        "recommended": 1.5,
        "maximum": 5
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      },
      "title": {
        "type": "string",
        "maxCharacters": 54,
        "guidance": "Maximum 54 characters; shorter copy is preferred."
      },
      "body": {
        "type": "string",
        "maxCharacters": 180,
        "guidance": "Maximum 180 characters; shorter copy is preferred."
      },
      "meta": {
        "type": "string",
        "maxCharacters": 48,
        "guidance": "Maximum 48 characters; shorter copy is preferred."
      }
    },
    "characterGuidance": {
      "title": 54,
      "body": 180,
      "meta": 48
    },
    "duration": {
      "minimum": 0.6,
      "recommended": 1.5,
      "maximum": 5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "ink-reveal"
    ],
    "defaultMotion": "cut-paper-pop",
    "soundTags": [
      "typography.warning-note.soft",
      "paper.text.reveal"
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
    "accessibilityLabel": "Warning note animated paper typography component",
    "responsiveText": true,
    "editable": true,
    "scalable": true,
    "agentSelection": {
      "useWhen": [
        "show_warning",
        "communicate_caution"
      ],
      "semanticRole": "annotation",
      "copyGuidance": {
        "title": 54,
        "body": 180,
        "meta": 48
      }
    }
  },
  {
    "id": "typography.call-to-action-card.paper-01",
    "name": "Call to action card",
    "version": "1.7.0",
    "category": "typography",
    "subtype": "action",
    "slug": "call-to-action-card",
    "renderer": "call-to-action-card",
    "order": 24,
    "intents": [
      "show_call_to_action",
      "prompt_next_step"
    ],
    "keywords": [
      "typography",
      "paper",
      "animated",
      "responsive",
      "action",
      "call to action card",
      "show_call_to_action",
      "prompt_next_step"
    ],
    "paperStyles": [
      "clean-editorial",
      "handmade-scrapbook",
      "technical-notebook"
    ],
    "aspectRatios": [
      "16:9",
      "1:1",
      "9:16"
    ],
    "slots": {
      "alignment": {
        "type": "enum",
        "values": [
          "left",
          "center",
          "right"
        ]
      },
      "emphasisWords": {
        "type": "array",
        "maximum": 6
      },
      "duration": {
        "type": "number",
        "minimum": 0.6,
        "recommended": 1.5,
        "maximum": 5
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      },
      "title": {
        "type": "string",
        "maxCharacters": 68,
        "guidance": "Maximum 68 characters; shorter copy is preferred."
      },
      "body": {
        "type": "string",
        "maxCharacters": 150,
        "guidance": "Maximum 150 characters; shorter copy is preferred."
      },
      "meta": {
        "type": "string",
        "maxCharacters": 42,
        "guidance": "Maximum 42 characters; shorter copy is preferred."
      }
    },
    "characterGuidance": {
      "title": 68,
      "body": 150,
      "meta": 42
    },
    "duration": {
      "minimum": 0.6,
      "recommended": 1.5,
      "maximum": 5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "ink-reveal"
    ],
    "defaultMotion": "ink-reveal",
    "soundTags": [
      "typography.call-to-action-card.soft",
      "paper.text.reveal"
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
    "accessibilityLabel": "Call to action card animated paper typography component",
    "responsiveText": true,
    "editable": true,
    "scalable": true,
    "agentSelection": {
      "useWhen": [
        "show_call_to_action",
        "prompt_next_step"
      ],
      "semanticRole": "action",
      "copyGuidance": {
        "title": 68,
        "body": 150,
        "meta": 42
      }
    }
  }
];
