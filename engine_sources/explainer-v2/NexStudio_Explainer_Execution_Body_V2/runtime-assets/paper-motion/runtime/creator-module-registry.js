window.NEX_CREATOR_MODULES=[
  {
    "id": "module.creator.social-post.paper-01",
    "name": "Social post",
    "version": "2.0.0",
    "category": "creator-module",
    "subtype": "social",
    "slug": "social-post",
    "renderer": "social-post",
    "order": 1,
    "intents": [
      "show_social_post",
      "publish_update"
    ],
    "keywords": [
      "creator",
      "publishing",
      "paper",
      "animated",
      "platform-neutral",
      "social",
      "social post",
      "show_social_post",
      "publish_update"
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
    "contentStates": [
      "short",
      "medium",
      "long"
    ],
    "duration": {
      "minimum": 0.8,
      "recommended": 1.8,
      "maximum": 6
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "drop-and-settle",
      "unfold"
    ],
    "defaultMotion": "cut-paper-pop",
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 88
      },
      "caption": {
        "type": "string",
        "maxCharacters": 240
      },
      "handle": {
        "type": "string",
        "maxCharacters": 56
      },
      "date": {
        "type": "string",
        "maxCharacters": 48
      },
      "avatar": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ]
      },
      "media": {
        "type": "media",
        "accepted": [
          "image",
          "video",
          "transparent-png",
          "website-screenshot"
        ]
      },
      "logo": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ],
        "authorizedOnly": true
      },
      "items": {
        "type": "array",
        "maximumItems": 8
      },
      "contentLength": {
        "type": "enum",
        "values": [
          "short",
          "medium",
          "long"
        ]
      }
    },
    "soundTags": [
      "creator.module.social-post.soft",
      "paper.module.reveal"
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
    "accessibilityLabel": "Animated platform-neutral social post paper module",
    "platformNeutral": true,
    "thirdPartyLogosBakedIn": false,
    "authorizedLogoSlot": true,
    "replaceableContent": true,
    "composedFromLowerLevelComponents": true,
    "agentSelection": {
      "useWhen": [
        "show_social_post",
        "publish_update"
      ],
      "semanticRole": "social",
      "avoidWhen": [
        "imitate_specific_social_platform"
      ]
    },
    "sampleConfig": {
      "title": "Maya Cole",
      "handle": "@mayamakes",
      "caption": "Three systems I use to turn one research session into a full week of useful content.",
      "date": "Today \u00b7 10:24",
      "counts": {
        "likes": 2840,
        "comments": 184,
        "shares": 96
      }
    }
  },
  {
    "id": "module.creator.thread.paper-01",
    "name": "Thread",
    "version": "2.0.0",
    "category": "creator-module",
    "subtype": "social",
    "slug": "thread",
    "renderer": "thread",
    "order": 2,
    "intents": [
      "show_thread",
      "explain_sequence"
    ],
    "keywords": [
      "creator",
      "publishing",
      "paper",
      "animated",
      "platform-neutral",
      "social",
      "thread",
      "show_thread",
      "explain_sequence"
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
    "contentStates": [
      "short",
      "medium",
      "long"
    ],
    "duration": {
      "minimum": 0.8,
      "recommended": 1.8,
      "maximum": 6
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "drop-and-settle",
      "unfold"
    ],
    "defaultMotion": "drop-and-settle",
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 88
      },
      "caption": {
        "type": "string",
        "maxCharacters": 240
      },
      "handle": {
        "type": "string",
        "maxCharacters": 56
      },
      "date": {
        "type": "string",
        "maxCharacters": 48
      },
      "avatar": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ]
      },
      "media": {
        "type": "media",
        "accepted": [
          "image",
          "video",
          "transparent-png",
          "website-screenshot"
        ]
      },
      "logo": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ],
        "authorizedOnly": true
      },
      "items": {
        "type": "array",
        "maximumItems": 8
      },
      "contentLength": {
        "type": "enum",
        "values": [
          "short",
          "medium",
          "long"
        ]
      }
    },
    "soundTags": [
      "creator.module.thread.soft",
      "paper.module.reveal"
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
    "accessibilityLabel": "Animated platform-neutral thread paper module",
    "platformNeutral": true,
    "thirdPartyLogosBakedIn": false,
    "authorizedLogoSlot": true,
    "replaceableContent": true,
    "composedFromLowerLevelComponents": true,
    "agentSelection": {
      "useWhen": [
        "show_thread",
        "explain_sequence"
      ],
      "semanticRole": "social",
      "avoidWhen": [
        "imitate_specific_social_platform"
      ]
    },
    "sampleConfig": {
      "title": "A practical creator workflow",
      "handle": "@mayamakes",
      "items": [
        "Start with one sharp question.",
        "Collect evidence before writing.",
        "Turn the answer into several formats.",
        "Review the result before publishing."
      ]
    }
  },
  {
    "id": "module.creator.comment-exchange.paper-01",
    "name": "Comment exchange",
    "version": "2.0.0",
    "category": "creator-module",
    "subtype": "community",
    "slug": "comment-exchange",
    "renderer": "comment-exchange",
    "order": 3,
    "intents": [
      "show_comment_exchange",
      "show_conversation"
    ],
    "keywords": [
      "creator",
      "publishing",
      "paper",
      "animated",
      "platform-neutral",
      "community",
      "comment exchange",
      "show_comment_exchange",
      "show_conversation"
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
    "contentStates": [
      "short",
      "medium",
      "long"
    ],
    "duration": {
      "minimum": 0.8,
      "recommended": 1.8,
      "maximum": 6
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "drop-and-settle",
      "unfold"
    ],
    "defaultMotion": "paper-slide",
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 88
      },
      "caption": {
        "type": "string",
        "maxCharacters": 240
      },
      "handle": {
        "type": "string",
        "maxCharacters": 56
      },
      "date": {
        "type": "string",
        "maxCharacters": 48
      },
      "avatar": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ]
      },
      "media": {
        "type": "media",
        "accepted": [
          "image",
          "video",
          "transparent-png",
          "website-screenshot"
        ]
      },
      "logo": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ],
        "authorizedOnly": true
      },
      "items": {
        "type": "array",
        "maximumItems": 8
      },
      "contentLength": {
        "type": "enum",
        "values": [
          "short",
          "medium",
          "long"
        ]
      }
    },
    "soundTags": [
      "creator.module.comment-exchange.soft",
      "paper.module.reveal"
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
    "accessibilityLabel": "Animated platform-neutral comment exchange paper module",
    "platformNeutral": true,
    "thirdPartyLogosBakedIn": false,
    "authorizedLogoSlot": true,
    "replaceableContent": true,
    "composedFromLowerLevelComponents": true,
    "agentSelection": {
      "useWhen": [
        "show_comment_exchange",
        "show_conversation"
      ],
      "semanticRole": "community",
      "avoidWhen": [
        "imitate_specific_social_platform"
      ]
    },
    "sampleConfig": {
      "title": "Community discussion",
      "items": [
        {
          "author": "Lena",
          "text": "How do you keep the videos consistent?"
        },
        {
          "author": "Maya",
          "text": "The style system is reusable; only the story changes."
        },
        {
          "author": "Tobi",
          "text": "That makes the workflow much faster."
        }
      ]
    }
  },
  {
    "id": "module.creator.creator-profile.paper-01",
    "name": "Creator profile",
    "version": "2.0.0",
    "category": "creator-module",
    "subtype": "identity",
    "slug": "creator-profile",
    "renderer": "creator-profile",
    "order": 4,
    "intents": [
      "introduce_creator",
      "show_profile"
    ],
    "keywords": [
      "creator",
      "publishing",
      "paper",
      "animated",
      "platform-neutral",
      "identity",
      "creator profile",
      "introduce_creator",
      "show_profile"
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
    "contentStates": [
      "short",
      "medium",
      "long"
    ],
    "duration": {
      "minimum": 0.8,
      "recommended": 1.8,
      "maximum": 6
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "drop-and-settle",
      "unfold"
    ],
    "defaultMotion": "cut-paper-pop",
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 88
      },
      "caption": {
        "type": "string",
        "maxCharacters": 240
      },
      "handle": {
        "type": "string",
        "maxCharacters": 56
      },
      "date": {
        "type": "string",
        "maxCharacters": 48
      },
      "avatar": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ]
      },
      "media": {
        "type": "media",
        "accepted": [
          "image",
          "video",
          "transparent-png",
          "website-screenshot"
        ]
      },
      "logo": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ],
        "authorizedOnly": true
      },
      "items": {
        "type": "array",
        "maximumItems": 8
      },
      "contentLength": {
        "type": "enum",
        "values": [
          "short",
          "medium",
          "long"
        ]
      }
    },
    "soundTags": [
      "creator.module.creator-profile.soft",
      "paper.module.reveal"
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
    "accessibilityLabel": "Animated platform-neutral creator profile paper module",
    "platformNeutral": true,
    "thirdPartyLogosBakedIn": false,
    "authorizedLogoSlot": true,
    "replaceableContent": true,
    "composedFromLowerLevelComponents": true,
    "agentSelection": {
      "useWhen": [
        "introduce_creator",
        "show_profile"
      ],
      "semanticRole": "identity",
      "avoidWhen": [
        "imitate_specific_social_platform"
      ]
    },
    "sampleConfig": {
      "title": "Maya Cole",
      "handle": "@mayamakes",
      "body": "Product educator \u00b7 128K subscribers",
      "caption": "Clear systems for creators building sustainable media businesses."
    }
  },
  {
    "id": "module.creator.subscriber-counter.paper-01",
    "name": "Subscriber counter",
    "version": "2.0.0",
    "category": "creator-module",
    "subtype": "metrics",
    "slug": "subscriber-counter",
    "renderer": "subscriber-counter",
    "order": 5,
    "intents": [
      "show_subscriber_growth",
      "celebrate_audience"
    ],
    "keywords": [
      "creator",
      "publishing",
      "paper",
      "animated",
      "platform-neutral",
      "metrics",
      "subscriber counter",
      "show_subscriber_growth",
      "celebrate_audience"
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
    "contentStates": [
      "short",
      "medium",
      "long"
    ],
    "duration": {
      "minimum": 0.8,
      "recommended": 1.8,
      "maximum": 6
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "drop-and-settle",
      "unfold"
    ],
    "defaultMotion": "drop-and-settle",
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 88
      },
      "caption": {
        "type": "string",
        "maxCharacters": 240
      },
      "handle": {
        "type": "string",
        "maxCharacters": 56
      },
      "date": {
        "type": "string",
        "maxCharacters": 48
      },
      "avatar": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ]
      },
      "media": {
        "type": "media",
        "accepted": [
          "image",
          "video",
          "transparent-png",
          "website-screenshot"
        ]
      },
      "logo": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ],
        "authorizedOnly": true
      },
      "items": {
        "type": "array",
        "maximumItems": 8
      },
      "contentLength": {
        "type": "enum",
        "values": [
          "short",
          "medium",
          "long"
        ]
      }
    },
    "soundTags": [
      "creator.module.subscriber-counter.soft",
      "paper.module.reveal"
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
    "accessibilityLabel": "Animated platform-neutral subscriber counter paper module",
    "platformNeutral": true,
    "thirdPartyLogosBakedIn": false,
    "authorizedLogoSlot": true,
    "replaceableContent": true,
    "composedFromLowerLevelComponents": true,
    "agentSelection": {
      "useWhen": [
        "show_subscriber_growth",
        "celebrate_audience"
      ],
      "semanticRole": "metrics",
      "avoidWhen": [
        "imitate_specific_social_platform"
      ]
    },
    "sampleConfig": {
      "title": "Subscribers",
      "value": 128400,
      "change": 18.4
    }
  },
  {
    "id": "module.creator.view-counter.paper-01",
    "name": "View counter",
    "version": "2.0.0",
    "category": "creator-module",
    "subtype": "metrics",
    "slug": "view-counter",
    "renderer": "view-counter",
    "order": 6,
    "intents": [
      "show_view_count",
      "show_reach"
    ],
    "keywords": [
      "creator",
      "publishing",
      "paper",
      "animated",
      "platform-neutral",
      "metrics",
      "view counter",
      "show_view_count",
      "show_reach"
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
    "contentStates": [
      "short",
      "medium",
      "long"
    ],
    "duration": {
      "minimum": 0.8,
      "recommended": 1.8,
      "maximum": 6
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "drop-and-settle",
      "unfold"
    ],
    "defaultMotion": "paper-slide",
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 88
      },
      "caption": {
        "type": "string",
        "maxCharacters": 240
      },
      "handle": {
        "type": "string",
        "maxCharacters": 56
      },
      "date": {
        "type": "string",
        "maxCharacters": 48
      },
      "avatar": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ]
      },
      "media": {
        "type": "media",
        "accepted": [
          "image",
          "video",
          "transparent-png",
          "website-screenshot"
        ]
      },
      "logo": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ],
        "authorizedOnly": true
      },
      "items": {
        "type": "array",
        "maximumItems": 8
      },
      "contentLength": {
        "type": "enum",
        "values": [
          "short",
          "medium",
          "long"
        ]
      }
    },
    "soundTags": [
      "creator.module.view-counter.soft",
      "paper.module.reveal"
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
    "accessibilityLabel": "Animated platform-neutral view counter paper module",
    "platformNeutral": true,
    "thirdPartyLogosBakedIn": false,
    "authorizedLogoSlot": true,
    "replaceableContent": true,
    "composedFromLowerLevelComponents": true,
    "agentSelection": {
      "useWhen": [
        "show_view_count",
        "show_reach"
      ],
      "semanticRole": "metrics",
      "avoidWhen": [
        "imitate_specific_social_platform"
      ]
    },
    "sampleConfig": {
      "title": "Monthly views",
      "value": 2400000,
      "change": 23.1
    }
  },
  {
    "id": "module.creator.engagement-summary.paper-01",
    "name": "Engagement summary",
    "version": "2.0.0",
    "category": "creator-module",
    "subtype": "metrics",
    "slug": "engagement-summary",
    "renderer": "engagement-summary",
    "order": 7,
    "intents": [
      "summarize_engagement",
      "show_performance"
    ],
    "keywords": [
      "creator",
      "publishing",
      "paper",
      "animated",
      "platform-neutral",
      "metrics",
      "engagement summary",
      "summarize_engagement",
      "show_performance"
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
    "contentStates": [
      "short",
      "medium",
      "long"
    ],
    "duration": {
      "minimum": 0.8,
      "recommended": 1.8,
      "maximum": 6
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "drop-and-settle",
      "unfold"
    ],
    "defaultMotion": "cut-paper-pop",
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 88
      },
      "caption": {
        "type": "string",
        "maxCharacters": 240
      },
      "handle": {
        "type": "string",
        "maxCharacters": 56
      },
      "date": {
        "type": "string",
        "maxCharacters": 48
      },
      "avatar": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ]
      },
      "media": {
        "type": "media",
        "accepted": [
          "image",
          "video",
          "transparent-png",
          "website-screenshot"
        ]
      },
      "logo": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ],
        "authorizedOnly": true
      },
      "items": {
        "type": "array",
        "maximumItems": 8
      },
      "contentLength": {
        "type": "enum",
        "values": [
          "short",
          "medium",
          "long"
        ]
      }
    },
    "soundTags": [
      "creator.module.engagement-summary.soft",
      "paper.module.reveal"
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
    "accessibilityLabel": "Animated platform-neutral engagement summary paper module",
    "platformNeutral": true,
    "thirdPartyLogosBakedIn": false,
    "authorizedLogoSlot": true,
    "replaceableContent": true,
    "composedFromLowerLevelComponents": true,
    "agentSelection": {
      "useWhen": [
        "summarize_engagement",
        "show_performance"
      ],
      "semanticRole": "metrics",
      "avoidWhen": [
        "imitate_specific_social_platform"
      ]
    },
    "sampleConfig": {
      "title": "Engagement summary",
      "items": [
        {
          "label": "Likes",
          "value": 18400,
          "change": 14
        },
        {
          "label": "Comments",
          "value": 2640,
          "change": 9
        },
        {
          "label": "Shares",
          "value": 1820,
          "change": 22
        },
        {
          "label": "Saves",
          "value": 7300,
          "change": 31
        }
      ]
    }
  },
  {
    "id": "module.creator.content-calendar.paper-01",
    "name": "Content calendar",
    "version": "2.0.0",
    "category": "creator-module",
    "subtype": "planning",
    "slug": "content-calendar",
    "renderer": "content-calendar",
    "order": 8,
    "intents": [
      "show_content_calendar",
      "plan_publishing"
    ],
    "keywords": [
      "creator",
      "publishing",
      "paper",
      "animated",
      "platform-neutral",
      "planning",
      "content calendar",
      "show_content_calendar",
      "plan_publishing"
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
    "contentStates": [
      "short",
      "medium",
      "long"
    ],
    "duration": {
      "minimum": 0.8,
      "recommended": 1.8,
      "maximum": 6
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "drop-and-settle",
      "unfold"
    ],
    "defaultMotion": "drop-and-settle",
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 88
      },
      "caption": {
        "type": "string",
        "maxCharacters": 240
      },
      "handle": {
        "type": "string",
        "maxCharacters": 56
      },
      "date": {
        "type": "string",
        "maxCharacters": 48
      },
      "avatar": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ]
      },
      "media": {
        "type": "media",
        "accepted": [
          "image",
          "video",
          "transparent-png",
          "website-screenshot"
        ]
      },
      "logo": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ],
        "authorizedOnly": true
      },
      "items": {
        "type": "array",
        "maximumItems": 8
      },
      "contentLength": {
        "type": "enum",
        "values": [
          "short",
          "medium",
          "long"
        ]
      }
    },
    "soundTags": [
      "creator.module.content-calendar.soft",
      "paper.module.reveal"
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
    "accessibilityLabel": "Animated platform-neutral content calendar paper module",
    "platformNeutral": true,
    "thirdPartyLogosBakedIn": false,
    "authorizedLogoSlot": true,
    "replaceableContent": true,
    "composedFromLowerLevelComponents": true,
    "agentSelection": {
      "useWhen": [
        "show_content_calendar",
        "plan_publishing"
      ],
      "semanticRole": "planning",
      "avoidWhen": [
        "imitate_specific_social_platform"
      ]
    },
    "sampleConfig": {
      "title": "Publishing week",
      "items": [
        {
          "label": "MON",
          "text": "Research note"
        },
        {
          "label": "TUE",
          "text": "Short video"
        },
        {
          "label": "WED",
          "text": "Newsletter"
        },
        {
          "label": "THU",
          "text": "Carousel"
        },
        {
          "label": "FRI",
          "text": "Podcast clip"
        }
      ]
    }
  },
  {
    "id": "module.creator.publishing-checklist.paper-01",
    "name": "Publishing checklist",
    "version": "2.0.0",
    "category": "creator-module",
    "subtype": "planning",
    "slug": "publishing-checklist",
    "renderer": "publishing-checklist",
    "order": 9,
    "intents": [
      "show_publishing_checklist",
      "track_readiness"
    ],
    "keywords": [
      "creator",
      "publishing",
      "paper",
      "animated",
      "platform-neutral",
      "planning",
      "publishing checklist",
      "show_publishing_checklist",
      "track_readiness"
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
    "contentStates": [
      "short",
      "medium",
      "long"
    ],
    "duration": {
      "minimum": 0.8,
      "recommended": 1.8,
      "maximum": 6
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "drop-and-settle",
      "unfold"
    ],
    "defaultMotion": "paper-slide",
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 88
      },
      "caption": {
        "type": "string",
        "maxCharacters": 240
      },
      "handle": {
        "type": "string",
        "maxCharacters": 56
      },
      "date": {
        "type": "string",
        "maxCharacters": 48
      },
      "avatar": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ]
      },
      "media": {
        "type": "media",
        "accepted": [
          "image",
          "video",
          "transparent-png",
          "website-screenshot"
        ]
      },
      "logo": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ],
        "authorizedOnly": true
      },
      "items": {
        "type": "array",
        "maximumItems": 8
      },
      "contentLength": {
        "type": "enum",
        "values": [
          "short",
          "medium",
          "long"
        ]
      }
    },
    "soundTags": [
      "creator.module.publishing-checklist.soft",
      "paper.module.reveal"
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
    "accessibilityLabel": "Animated platform-neutral publishing checklist paper module",
    "platformNeutral": true,
    "thirdPartyLogosBakedIn": false,
    "authorizedLogoSlot": true,
    "replaceableContent": true,
    "composedFromLowerLevelComponents": true,
    "agentSelection": {
      "useWhen": [
        "show_publishing_checklist",
        "track_readiness"
      ],
      "semanticRole": "planning",
      "avoidWhen": [
        "imitate_specific_social_platform"
      ]
    },
    "sampleConfig": {
      "title": "Ready to publish",
      "items": [
        {
          "text": "Hook reviewed",
          "done": true
        },
        {
          "text": "Captions checked",
          "done": true
        },
        {
          "text": "Thumbnail approved",
          "done": true
        },
        {
          "text": "Links verified",
          "done": false
        }
      ]
    }
  },
  {
    "id": "module.creator.thumbnail-selector.paper-01",
    "name": "Thumbnail selector",
    "version": "2.0.0",
    "category": "creator-module",
    "subtype": "production",
    "slug": "thumbnail-selector",
    "renderer": "thumbnail-selector",
    "order": 10,
    "intents": [
      "compare_thumbnails",
      "select_thumbnail"
    ],
    "keywords": [
      "creator",
      "publishing",
      "paper",
      "animated",
      "platform-neutral",
      "production",
      "thumbnail selector",
      "compare_thumbnails",
      "select_thumbnail"
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
    "contentStates": [
      "short",
      "medium",
      "long"
    ],
    "duration": {
      "minimum": 0.8,
      "recommended": 1.8,
      "maximum": 6
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "drop-and-settle",
      "unfold"
    ],
    "defaultMotion": "cut-paper-pop",
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 88
      },
      "caption": {
        "type": "string",
        "maxCharacters": 240
      },
      "handle": {
        "type": "string",
        "maxCharacters": 56
      },
      "date": {
        "type": "string",
        "maxCharacters": 48
      },
      "avatar": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ]
      },
      "media": {
        "type": "media",
        "accepted": [
          "image",
          "video",
          "transparent-png",
          "website-screenshot"
        ]
      },
      "logo": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ],
        "authorizedOnly": true
      },
      "items": {
        "type": "array",
        "maximumItems": 8
      },
      "contentLength": {
        "type": "enum",
        "values": [
          "short",
          "medium",
          "long"
        ]
      }
    },
    "soundTags": [
      "creator.module.thumbnail-selector.soft",
      "paper.module.reveal"
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
    "accessibilityLabel": "Animated platform-neutral thumbnail selector paper module",
    "platformNeutral": true,
    "thirdPartyLogosBakedIn": false,
    "authorizedLogoSlot": true,
    "replaceableContent": true,
    "composedFromLowerLevelComponents": true,
    "agentSelection": {
      "useWhen": [
        "compare_thumbnails",
        "select_thumbnail"
      ],
      "semanticRole": "production",
      "avoidWhen": [
        "imitate_specific_social_platform"
      ]
    },
    "sampleConfig": {
      "title": "Choose the strongest thumbnail",
      "items": [
        "The hidden cost of bad systems",
        "One idea. Seven useful posts.",
        "Build a repeatable content engine."
      ],
      "selected": 1
    }
  },
  {
    "id": "module.creator.video-chapters.paper-01",
    "name": "Video chapters",
    "version": "2.0.0",
    "category": "creator-module",
    "subtype": "production",
    "slug": "video-chapters",
    "renderer": "video-chapters",
    "order": 11,
    "intents": [
      "show_video_chapters",
      "structure_video"
    ],
    "keywords": [
      "creator",
      "publishing",
      "paper",
      "animated",
      "platform-neutral",
      "production",
      "video chapters",
      "show_video_chapters",
      "structure_video"
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
    "contentStates": [
      "short",
      "medium",
      "long"
    ],
    "duration": {
      "minimum": 0.8,
      "recommended": 1.8,
      "maximum": 6
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "drop-and-settle",
      "unfold"
    ],
    "defaultMotion": "drop-and-settle",
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 88
      },
      "caption": {
        "type": "string",
        "maxCharacters": 240
      },
      "handle": {
        "type": "string",
        "maxCharacters": 56
      },
      "date": {
        "type": "string",
        "maxCharacters": 48
      },
      "avatar": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ]
      },
      "media": {
        "type": "media",
        "accepted": [
          "image",
          "video",
          "transparent-png",
          "website-screenshot"
        ]
      },
      "logo": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ],
        "authorizedOnly": true
      },
      "items": {
        "type": "array",
        "maximumItems": 8
      },
      "contentLength": {
        "type": "enum",
        "values": [
          "short",
          "medium",
          "long"
        ]
      }
    },
    "soundTags": [
      "creator.module.video-chapters.soft",
      "paper.module.reveal"
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
    "accessibilityLabel": "Animated platform-neutral video chapters paper module",
    "platformNeutral": true,
    "thirdPartyLogosBakedIn": false,
    "authorizedLogoSlot": true,
    "replaceableContent": true,
    "composedFromLowerLevelComponents": true,
    "agentSelection": {
      "useWhen": [
        "show_video_chapters",
        "structure_video"
      ],
      "semanticRole": "production",
      "avoidWhen": [
        "imitate_specific_social_platform"
      ]
    },
    "sampleConfig": {
      "title": "Video chapters",
      "items": [
        {
          "time": "00:00",
          "text": "The problem"
        },
        {
          "time": "01:12",
          "text": "The system"
        },
        {
          "time": "03:48",
          "text": "Real example"
        },
        {
          "time": "06:20",
          "text": "What to do next"
        }
      ]
    }
  },
  {
    "id": "module.creator.newsletter-card.paper-01",
    "name": "Newsletter card",
    "version": "2.0.0",
    "category": "creator-module",
    "subtype": "publishing",
    "slug": "newsletter-card",
    "renderer": "newsletter-card",
    "order": 12,
    "intents": [
      "promote_newsletter",
      "show_newsletter"
    ],
    "keywords": [
      "creator",
      "publishing",
      "paper",
      "animated",
      "platform-neutral",
      "publishing",
      "newsletter card",
      "promote_newsletter",
      "show_newsletter"
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
    "contentStates": [
      "short",
      "medium",
      "long"
    ],
    "duration": {
      "minimum": 0.8,
      "recommended": 1.8,
      "maximum": 6
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "drop-and-settle",
      "unfold"
    ],
    "defaultMotion": "paper-slide",
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 88
      },
      "caption": {
        "type": "string",
        "maxCharacters": 240
      },
      "handle": {
        "type": "string",
        "maxCharacters": 56
      },
      "date": {
        "type": "string",
        "maxCharacters": 48
      },
      "avatar": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ]
      },
      "media": {
        "type": "media",
        "accepted": [
          "image",
          "video",
          "transparent-png",
          "website-screenshot"
        ]
      },
      "logo": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ],
        "authorizedOnly": true
      },
      "items": {
        "type": "array",
        "maximumItems": 8
      },
      "contentLength": {
        "type": "enum",
        "values": [
          "short",
          "medium",
          "long"
        ]
      }
    },
    "soundTags": [
      "creator.module.newsletter-card.soft",
      "paper.module.reveal"
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
    "accessibilityLabel": "Animated platform-neutral newsletter card paper module",
    "platformNeutral": true,
    "thirdPartyLogosBakedIn": false,
    "authorizedLogoSlot": true,
    "replaceableContent": true,
    "composedFromLowerLevelComponents": true,
    "agentSelection": {
      "useWhen": [
        "promote_newsletter",
        "show_newsletter"
      ],
      "semanticRole": "publishing",
      "avoidWhen": [
        "imitate_specific_social_platform"
      ]
    },
    "sampleConfig": {
      "title": "The Useful Systems Letter",
      "caption": "One practical creator workflow every Thursday.",
      "handle": "Issue 48 \u00b7 6 min read"
    }
  },
  {
    "id": "module.creator.podcast-episode.paper-01",
    "name": "Podcast episode",
    "version": "2.0.0",
    "category": "creator-module",
    "subtype": "publishing",
    "slug": "podcast-episode",
    "renderer": "podcast-episode",
    "order": 13,
    "intents": [
      "promote_podcast",
      "show_episode"
    ],
    "keywords": [
      "creator",
      "publishing",
      "paper",
      "animated",
      "platform-neutral",
      "publishing",
      "podcast episode",
      "promote_podcast",
      "show_episode"
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
    "contentStates": [
      "short",
      "medium",
      "long"
    ],
    "duration": {
      "minimum": 0.8,
      "recommended": 1.8,
      "maximum": 6
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "drop-and-settle",
      "unfold"
    ],
    "defaultMotion": "cut-paper-pop",
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 88
      },
      "caption": {
        "type": "string",
        "maxCharacters": 240
      },
      "handle": {
        "type": "string",
        "maxCharacters": 56
      },
      "date": {
        "type": "string",
        "maxCharacters": 48
      },
      "avatar": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ]
      },
      "media": {
        "type": "media",
        "accepted": [
          "image",
          "video",
          "transparent-png",
          "website-screenshot"
        ]
      },
      "logo": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ],
        "authorizedOnly": true
      },
      "items": {
        "type": "array",
        "maximumItems": 8
      },
      "contentLength": {
        "type": "enum",
        "values": [
          "short",
          "medium",
          "long"
        ]
      }
    },
    "soundTags": [
      "creator.module.podcast-episode.soft",
      "paper.module.reveal"
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
    "accessibilityLabel": "Animated platform-neutral podcast episode paper module",
    "platformNeutral": true,
    "thirdPartyLogosBakedIn": false,
    "authorizedLogoSlot": true,
    "replaceableContent": true,
    "composedFromLowerLevelComponents": true,
    "agentSelection": {
      "useWhen": [
        "promote_podcast",
        "show_episode"
      ],
      "semanticRole": "publishing",
      "avoidWhen": [
        "imitate_specific_social_platform"
      ]
    },
    "sampleConfig": {
      "title": "Build Once, Publish Better",
      "caption": "Maya Cole with Jordan Ellis",
      "handle": "Episode 72 \u00b7 38 min"
    }
  },
  {
    "id": "module.creator.blog-article.paper-01",
    "name": "Blog article",
    "version": "2.0.0",
    "category": "creator-module",
    "subtype": "publishing",
    "slug": "blog-article",
    "renderer": "blog-article",
    "order": 14,
    "intents": [
      "show_blog_article",
      "promote_article"
    ],
    "keywords": [
      "creator",
      "publishing",
      "paper",
      "animated",
      "platform-neutral",
      "publishing",
      "blog article",
      "show_blog_article",
      "promote_article"
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
    "contentStates": [
      "short",
      "medium",
      "long"
    ],
    "duration": {
      "minimum": 0.8,
      "recommended": 1.8,
      "maximum": 6
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "drop-and-settle",
      "unfold"
    ],
    "defaultMotion": "drop-and-settle",
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 88
      },
      "caption": {
        "type": "string",
        "maxCharacters": 240
      },
      "handle": {
        "type": "string",
        "maxCharacters": 56
      },
      "date": {
        "type": "string",
        "maxCharacters": 48
      },
      "avatar": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ]
      },
      "media": {
        "type": "media",
        "accepted": [
          "image",
          "video",
          "transparent-png",
          "website-screenshot"
        ]
      },
      "logo": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ],
        "authorizedOnly": true
      },
      "items": {
        "type": "array",
        "maximumItems": 8
      },
      "contentLength": {
        "type": "enum",
        "values": [
          "short",
          "medium",
          "long"
        ]
      }
    },
    "soundTags": [
      "creator.module.blog-article.soft",
      "paper.module.reveal"
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
    "accessibilityLabel": "Animated platform-neutral blog article paper module",
    "platformNeutral": true,
    "thirdPartyLogosBakedIn": false,
    "authorizedLogoSlot": true,
    "replaceableContent": true,
    "composedFromLowerLevelComponents": true,
    "agentSelection": {
      "useWhen": [
        "show_blog_article",
        "promote_article"
      ],
      "semanticRole": "publishing",
      "avoidWhen": [
        "imitate_specific_social_platform"
      ]
    },
    "sampleConfig": {
      "title": "How to design a repeatable content system",
      "caption": "A field guide for creators who want quality without starting from zero every week.",
      "handle": "12 AUG 2026 \u00b7 8 MIN READ"
    }
  },
  {
    "id": "module.creator.community-poll.paper-01",
    "name": "Community poll",
    "version": "2.0.0",
    "category": "creator-module",
    "subtype": "community",
    "slug": "community-poll",
    "renderer": "community-poll",
    "order": 15,
    "intents": [
      "show_poll",
      "collect_opinion"
    ],
    "keywords": [
      "creator",
      "publishing",
      "paper",
      "animated",
      "platform-neutral",
      "community",
      "community poll",
      "show_poll",
      "collect_opinion"
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
    "contentStates": [
      "short",
      "medium",
      "long"
    ],
    "duration": {
      "minimum": 0.8,
      "recommended": 1.8,
      "maximum": 6
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "drop-and-settle",
      "unfold"
    ],
    "defaultMotion": "paper-slide",
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 88
      },
      "caption": {
        "type": "string",
        "maxCharacters": 240
      },
      "handle": {
        "type": "string",
        "maxCharacters": 56
      },
      "date": {
        "type": "string",
        "maxCharacters": 48
      },
      "avatar": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ]
      },
      "media": {
        "type": "media",
        "accepted": [
          "image",
          "video",
          "transparent-png",
          "website-screenshot"
        ]
      },
      "logo": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ],
        "authorizedOnly": true
      },
      "items": {
        "type": "array",
        "maximumItems": 8
      },
      "contentLength": {
        "type": "enum",
        "values": [
          "short",
          "medium",
          "long"
        ]
      }
    },
    "soundTags": [
      "creator.module.community-poll.soft",
      "paper.module.reveal"
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
    "accessibilityLabel": "Animated platform-neutral community poll paper module",
    "platformNeutral": true,
    "thirdPartyLogosBakedIn": false,
    "authorizedLogoSlot": true,
    "replaceableContent": true,
    "composedFromLowerLevelComponents": true,
    "agentSelection": {
      "useWhen": [
        "show_poll",
        "collect_opinion"
      ],
      "semanticRole": "community",
      "avoidWhen": [
        "imitate_specific_social_platform"
      ]
    },
    "sampleConfig": {
      "title": "What slows your workflow most?",
      "items": [
        {
          "label": "Research",
          "value": 24
        },
        {
          "label": "Writing",
          "value": 19
        },
        {
          "label": "Editing",
          "value": 42
        },
        {
          "label": "Publishing",
          "value": 15
        }
      ]
    }
  },
  {
    "id": "module.creator.question-and-answer-card.paper-01",
    "name": "Question and answer card",
    "version": "2.0.0",
    "category": "creator-module",
    "subtype": "community",
    "slug": "question-and-answer-card",
    "renderer": "question-and-answer-card",
    "order": 16,
    "intents": [
      "show_question_answer",
      "educate_audience"
    ],
    "keywords": [
      "creator",
      "publishing",
      "paper",
      "animated",
      "platform-neutral",
      "community",
      "question and answer card",
      "show_question_answer",
      "educate_audience"
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
    "contentStates": [
      "short",
      "medium",
      "long"
    ],
    "duration": {
      "minimum": 0.8,
      "recommended": 1.8,
      "maximum": 6
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "drop-and-settle",
      "unfold"
    ],
    "defaultMotion": "cut-paper-pop",
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 88
      },
      "caption": {
        "type": "string",
        "maxCharacters": 240
      },
      "handle": {
        "type": "string",
        "maxCharacters": 56
      },
      "date": {
        "type": "string",
        "maxCharacters": 48
      },
      "avatar": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ]
      },
      "media": {
        "type": "media",
        "accepted": [
          "image",
          "video",
          "transparent-png",
          "website-screenshot"
        ]
      },
      "logo": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ],
        "authorizedOnly": true
      },
      "items": {
        "type": "array",
        "maximumItems": 8
      },
      "contentLength": {
        "type": "enum",
        "values": [
          "short",
          "medium",
          "long"
        ]
      }
    },
    "soundTags": [
      "creator.module.question-and-answer-card.soft",
      "paper.module.reveal"
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
    "accessibilityLabel": "Animated platform-neutral question and answer card paper module",
    "platformNeutral": true,
    "thirdPartyLogosBakedIn": false,
    "authorizedLogoSlot": true,
    "replaceableContent": true,
    "composedFromLowerLevelComponents": true,
    "agentSelection": {
      "useWhen": [
        "show_question_answer",
        "educate_audience"
      ],
      "semanticRole": "community",
      "avoidWhen": [
        "imitate_specific_social_platform"
      ]
    },
    "sampleConfig": {
      "title": "How much should be reusable?",
      "caption": "Reuse the structure, motion and design rules. Keep the story, evidence and point of view specific."
    }
  },
  {
    "id": "module.creator.testimonial.paper-01",
    "name": "Testimonial",
    "version": "2.0.0",
    "category": "creator-module",
    "subtype": "proof",
    "slug": "testimonial",
    "renderer": "testimonial",
    "order": 17,
    "intents": [
      "show_testimonial",
      "build_trust"
    ],
    "keywords": [
      "creator",
      "publishing",
      "paper",
      "animated",
      "platform-neutral",
      "proof",
      "testimonial",
      "show_testimonial",
      "build_trust"
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
    "contentStates": [
      "short",
      "medium",
      "long"
    ],
    "duration": {
      "minimum": 0.8,
      "recommended": 1.8,
      "maximum": 6
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "drop-and-settle",
      "unfold"
    ],
    "defaultMotion": "drop-and-settle",
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 88
      },
      "caption": {
        "type": "string",
        "maxCharacters": 240
      },
      "handle": {
        "type": "string",
        "maxCharacters": 56
      },
      "date": {
        "type": "string",
        "maxCharacters": 48
      },
      "avatar": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ]
      },
      "media": {
        "type": "media",
        "accepted": [
          "image",
          "video",
          "transparent-png",
          "website-screenshot"
        ]
      },
      "logo": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ],
        "authorizedOnly": true
      },
      "items": {
        "type": "array",
        "maximumItems": 8
      },
      "contentLength": {
        "type": "enum",
        "values": [
          "short",
          "medium",
          "long"
        ]
      }
    },
    "soundTags": [
      "creator.module.testimonial.soft",
      "paper.module.reveal"
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
    "accessibilityLabel": "Animated platform-neutral testimonial paper module",
    "platformNeutral": true,
    "thirdPartyLogosBakedIn": false,
    "authorizedLogoSlot": true,
    "replaceableContent": true,
    "composedFromLowerLevelComponents": true,
    "agentSelection": {
      "useWhen": [
        "show_testimonial",
        "build_trust"
      ],
      "semanticRole": "proof",
      "avoidWhen": [
        "imitate_specific_social_platform"
      ]
    },
    "sampleConfig": {
      "title": "Jordan Ellis",
      "handle": "Independent creator",
      "caption": "The system helped us cut production time without making the work feel templated."
    }
  },
  {
    "id": "module.creator.review.paper-01",
    "name": "Review",
    "version": "2.0.0",
    "category": "creator-module",
    "subtype": "proof",
    "slug": "review",
    "renderer": "review",
    "order": 18,
    "intents": [
      "show_review",
      "show_rating"
    ],
    "keywords": [
      "creator",
      "publishing",
      "paper",
      "animated",
      "platform-neutral",
      "proof",
      "review",
      "show_review",
      "show_rating"
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
    "contentStates": [
      "short",
      "medium",
      "long"
    ],
    "duration": {
      "minimum": 0.8,
      "recommended": 1.8,
      "maximum": 6
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "drop-and-settle",
      "unfold"
    ],
    "defaultMotion": "paper-slide",
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 88
      },
      "caption": {
        "type": "string",
        "maxCharacters": 240
      },
      "handle": {
        "type": "string",
        "maxCharacters": 56
      },
      "date": {
        "type": "string",
        "maxCharacters": 48
      },
      "avatar": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ]
      },
      "media": {
        "type": "media",
        "accepted": [
          "image",
          "video",
          "transparent-png",
          "website-screenshot"
        ]
      },
      "logo": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ],
        "authorizedOnly": true
      },
      "items": {
        "type": "array",
        "maximumItems": 8
      },
      "contentLength": {
        "type": "enum",
        "values": [
          "short",
          "medium",
          "long"
        ]
      }
    },
    "soundTags": [
      "creator.module.review.soft",
      "paper.module.reveal"
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
    "accessibilityLabel": "Animated platform-neutral review paper module",
    "platformNeutral": true,
    "thirdPartyLogosBakedIn": false,
    "authorizedLogoSlot": true,
    "replaceableContent": true,
    "composedFromLowerLevelComponents": true,
    "agentSelection": {
      "useWhen": [
        "show_review",
        "show_rating"
      ],
      "semanticRole": "proof",
      "avoidWhen": [
        "imitate_specific_social_platform"
      ]
    },
    "sampleConfig": {
      "title": "Northstar Creator Kit",
      "caption": "A genuinely useful system with thoughtful defaults and enough control to keep the work personal.",
      "value": 4.9
    }
  },
  {
    "id": "module.creator.user-generated-content-frame.paper-01",
    "name": "User-generated content frame",
    "version": "2.0.0",
    "category": "creator-module",
    "subtype": "community",
    "slug": "user-generated-content-frame",
    "renderer": "user-generated-content-frame",
    "order": 19,
    "intents": [
      "show_user_generated_content",
      "feature_community"
    ],
    "keywords": [
      "creator",
      "publishing",
      "paper",
      "animated",
      "platform-neutral",
      "community",
      "user generated content frame",
      "show_user_generated_content",
      "feature_community"
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
    "contentStates": [
      "short",
      "medium",
      "long"
    ],
    "duration": {
      "minimum": 0.8,
      "recommended": 1.8,
      "maximum": 6
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "drop-and-settle",
      "unfold"
    ],
    "defaultMotion": "cut-paper-pop",
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 88
      },
      "caption": {
        "type": "string",
        "maxCharacters": 240
      },
      "handle": {
        "type": "string",
        "maxCharacters": 56
      },
      "date": {
        "type": "string",
        "maxCharacters": 48
      },
      "avatar": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ]
      },
      "media": {
        "type": "media",
        "accepted": [
          "image",
          "video",
          "transparent-png",
          "website-screenshot"
        ]
      },
      "logo": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ],
        "authorizedOnly": true
      },
      "items": {
        "type": "array",
        "maximumItems": 8
      },
      "contentLength": {
        "type": "enum",
        "values": [
          "short",
          "medium",
          "long"
        ]
      }
    },
    "soundTags": [
      "creator.module.user-generated-content-frame.soft",
      "paper.module.reveal"
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
    "accessibilityLabel": "Animated platform-neutral user-generated content frame paper module",
    "platformNeutral": true,
    "thirdPartyLogosBakedIn": false,
    "authorizedLogoSlot": true,
    "replaceableContent": true,
    "composedFromLowerLevelComponents": true,
    "agentSelection": {
      "useWhen": [
        "show_user_generated_content",
        "feature_community"
      ],
      "semanticRole": "community",
      "avoidWhen": [
        "imitate_specific_social_platform"
      ]
    },
    "sampleConfig": {
      "title": "Lena Adebayo",
      "handle": "@lenacreates",
      "caption": "Tried the workflow for my product launch. The storyboard was ready before lunch."
    }
  },
  {
    "id": "module.creator.reaction-panel.paper-01",
    "name": "Reaction panel",
    "version": "2.0.0",
    "category": "creator-module",
    "subtype": "community",
    "slug": "reaction-panel",
    "renderer": "reaction-panel",
    "order": 20,
    "intents": [
      "show_reactions",
      "show_sentiment"
    ],
    "keywords": [
      "creator",
      "publishing",
      "paper",
      "animated",
      "platform-neutral",
      "community",
      "reaction panel",
      "show_reactions",
      "show_sentiment"
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
    "contentStates": [
      "short",
      "medium",
      "long"
    ],
    "duration": {
      "minimum": 0.8,
      "recommended": 1.8,
      "maximum": 6
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "drop-and-settle",
      "unfold"
    ],
    "defaultMotion": "drop-and-settle",
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 88
      },
      "caption": {
        "type": "string",
        "maxCharacters": 240
      },
      "handle": {
        "type": "string",
        "maxCharacters": 56
      },
      "date": {
        "type": "string",
        "maxCharacters": 48
      },
      "avatar": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ]
      },
      "media": {
        "type": "media",
        "accepted": [
          "image",
          "video",
          "transparent-png",
          "website-screenshot"
        ]
      },
      "logo": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ],
        "authorizedOnly": true
      },
      "items": {
        "type": "array",
        "maximumItems": 8
      },
      "contentLength": {
        "type": "enum",
        "values": [
          "short",
          "medium",
          "long"
        ]
      }
    },
    "soundTags": [
      "creator.module.reaction-panel.soft",
      "paper.module.reveal"
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
    "accessibilityLabel": "Animated platform-neutral reaction panel paper module",
    "platformNeutral": true,
    "thirdPartyLogosBakedIn": false,
    "authorizedLogoSlot": true,
    "replaceableContent": true,
    "composedFromLowerLevelComponents": true,
    "agentSelection": {
      "useWhen": [
        "show_reactions",
        "show_sentiment"
      ],
      "semanticRole": "community",
      "avoidWhen": [
        "imitate_specific_social_platform"
      ]
    },
    "sampleConfig": {
      "title": "Audience reaction",
      "items": [
        {
          "label": "Useful",
          "value": 68
        },
        {
          "label": "Surprising",
          "value": 17
        },
        {
          "label": "Saved",
          "value": 11
        },
        {
          "label": "More please",
          "value": 4
        }
      ]
    }
  },
  {
    "id": "module.creator.creator-collaboration.paper-01",
    "name": "Creator collaboration",
    "version": "2.0.0",
    "category": "creator-module",
    "subtype": "partnership",
    "slug": "creator-collaboration",
    "renderer": "creator-collaboration",
    "order": 21,
    "intents": [
      "announce_collaboration",
      "show_creators"
    ],
    "keywords": [
      "creator",
      "publishing",
      "paper",
      "animated",
      "platform-neutral",
      "partnership",
      "creator collaboration",
      "announce_collaboration",
      "show_creators"
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
    "contentStates": [
      "short",
      "medium",
      "long"
    ],
    "duration": {
      "minimum": 0.8,
      "recommended": 1.8,
      "maximum": 6
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "drop-and-settle",
      "unfold"
    ],
    "defaultMotion": "paper-slide",
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 88
      },
      "caption": {
        "type": "string",
        "maxCharacters": 240
      },
      "handle": {
        "type": "string",
        "maxCharacters": 56
      },
      "date": {
        "type": "string",
        "maxCharacters": 48
      },
      "avatar": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ]
      },
      "media": {
        "type": "media",
        "accepted": [
          "image",
          "video",
          "transparent-png",
          "website-screenshot"
        ]
      },
      "logo": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ],
        "authorizedOnly": true
      },
      "items": {
        "type": "array",
        "maximumItems": 8
      },
      "contentLength": {
        "type": "enum",
        "values": [
          "short",
          "medium",
          "long"
        ]
      }
    },
    "soundTags": [
      "creator.module.creator-collaboration.soft",
      "paper.module.reveal"
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
    "accessibilityLabel": "Animated platform-neutral creator collaboration paper module",
    "platformNeutral": true,
    "thirdPartyLogosBakedIn": false,
    "authorizedLogoSlot": true,
    "replaceableContent": true,
    "composedFromLowerLevelComponents": true,
    "agentSelection": {
      "useWhen": [
        "announce_collaboration",
        "show_creators"
      ],
      "semanticRole": "partnership",
      "avoidWhen": [
        "imitate_specific_social_platform"
      ]
    },
    "sampleConfig": {
      "title": "Maya Cole \u00d7 Jordan Ellis",
      "caption": "A practical conversation about building durable creator businesses.",
      "handle": "LIVE SESSION \u00b7 18 AUG"
    }
  },
  {
    "id": "module.creator.sponsorship-card.paper-01",
    "name": "Sponsorship card",
    "version": "2.0.0",
    "category": "creator-module",
    "subtype": "partnership",
    "slug": "sponsorship-card",
    "renderer": "sponsorship-card",
    "order": 22,
    "intents": [
      "announce_sponsorship",
      "show_sponsor"
    ],
    "keywords": [
      "creator",
      "publishing",
      "paper",
      "animated",
      "platform-neutral",
      "partnership",
      "sponsorship card",
      "announce_sponsorship",
      "show_sponsor"
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
    "contentStates": [
      "short",
      "medium",
      "long"
    ],
    "duration": {
      "minimum": 0.8,
      "recommended": 1.8,
      "maximum": 6
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "drop-and-settle",
      "unfold"
    ],
    "defaultMotion": "cut-paper-pop",
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 88
      },
      "caption": {
        "type": "string",
        "maxCharacters": 240
      },
      "handle": {
        "type": "string",
        "maxCharacters": 56
      },
      "date": {
        "type": "string",
        "maxCharacters": 48
      },
      "avatar": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ]
      },
      "media": {
        "type": "media",
        "accepted": [
          "image",
          "video",
          "transparent-png",
          "website-screenshot"
        ]
      },
      "logo": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ],
        "authorizedOnly": true
      },
      "items": {
        "type": "array",
        "maximumItems": 8
      },
      "contentLength": {
        "type": "enum",
        "values": [
          "short",
          "medium",
          "long"
        ]
      }
    },
    "soundTags": [
      "creator.module.sponsorship-card.soft",
      "paper.module.reveal"
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
    "accessibilityLabel": "Animated platform-neutral sponsorship card paper module",
    "platformNeutral": true,
    "thirdPartyLogosBakedIn": false,
    "authorizedLogoSlot": true,
    "replaceableContent": true,
    "composedFromLowerLevelComponents": true,
    "agentSelection": {
      "useWhen": [
        "announce_sponsorship",
        "show_sponsor"
      ],
      "semanticRole": "partnership",
      "avoidWhen": [
        "imitate_specific_social_platform"
      ]
    },
    "sampleConfig": {
      "title": "This episode is supported by Northstar Audio",
      "caption": "Studio-quality sound tools built for independent creators.",
      "handle": "AUTHORIZED PARTNER"
    }
  },
  {
    "id": "module.creator.brand-partnership.paper-01",
    "name": "Brand partnership",
    "version": "2.0.0",
    "category": "creator-module",
    "subtype": "partnership",
    "slug": "brand-partnership",
    "renderer": "brand-partnership",
    "order": 23,
    "intents": [
      "announce_brand_partnership",
      "show_partners"
    ],
    "keywords": [
      "creator",
      "publishing",
      "paper",
      "animated",
      "platform-neutral",
      "partnership",
      "brand partnership",
      "announce_brand_partnership",
      "show_partners"
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
    "contentStates": [
      "short",
      "medium",
      "long"
    ],
    "duration": {
      "minimum": 0.8,
      "recommended": 1.8,
      "maximum": 6
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "drop-and-settle",
      "unfold"
    ],
    "defaultMotion": "drop-and-settle",
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 88
      },
      "caption": {
        "type": "string",
        "maxCharacters": 240
      },
      "handle": {
        "type": "string",
        "maxCharacters": 56
      },
      "date": {
        "type": "string",
        "maxCharacters": 48
      },
      "avatar": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ]
      },
      "media": {
        "type": "media",
        "accepted": [
          "image",
          "video",
          "transparent-png",
          "website-screenshot"
        ]
      },
      "logo": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ],
        "authorizedOnly": true
      },
      "items": {
        "type": "array",
        "maximumItems": 8
      },
      "contentLength": {
        "type": "enum",
        "values": [
          "short",
          "medium",
          "long"
        ]
      }
    },
    "soundTags": [
      "creator.module.brand-partnership.soft",
      "paper.module.reveal"
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
    "accessibilityLabel": "Animated platform-neutral brand partnership paper module",
    "platformNeutral": true,
    "thirdPartyLogosBakedIn": false,
    "authorizedLogoSlot": true,
    "replaceableContent": true,
    "composedFromLowerLevelComponents": true,
    "agentSelection": {
      "useWhen": [
        "announce_brand_partnership",
        "show_partners"
      ],
      "semanticRole": "partnership",
      "avoidWhen": [
        "imitate_specific_social_platform"
      ]
    },
    "sampleConfig": {
      "title": "Maya Makes \u00d7 Northstar Audio",
      "caption": "A three-part educational series about better production systems.",
      "handle": "BRAND PARTNERSHIP \u00b7 Q3"
    }
  },
  {
    "id": "module.creator.campaign-result.paper-01",
    "name": "Campaign result",
    "version": "2.0.0",
    "category": "creator-module",
    "subtype": "metrics",
    "slug": "campaign-result",
    "renderer": "campaign-result",
    "order": 24,
    "intents": [
      "show_campaign_result",
      "report_campaign"
    ],
    "keywords": [
      "creator",
      "publishing",
      "paper",
      "animated",
      "platform-neutral",
      "metrics",
      "campaign result",
      "show_campaign_result",
      "report_campaign"
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
    "contentStates": [
      "short",
      "medium",
      "long"
    ],
    "duration": {
      "minimum": 0.8,
      "recommended": 1.8,
      "maximum": 6
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "drop-and-settle",
      "unfold"
    ],
    "defaultMotion": "paper-slide",
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 88
      },
      "caption": {
        "type": "string",
        "maxCharacters": 240
      },
      "handle": {
        "type": "string",
        "maxCharacters": 56
      },
      "date": {
        "type": "string",
        "maxCharacters": 48
      },
      "avatar": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ]
      },
      "media": {
        "type": "media",
        "accepted": [
          "image",
          "video",
          "transparent-png",
          "website-screenshot"
        ]
      },
      "logo": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ],
        "authorizedOnly": true
      },
      "items": {
        "type": "array",
        "maximumItems": 8
      },
      "contentLength": {
        "type": "enum",
        "values": [
          "short",
          "medium",
          "long"
        ]
      }
    },
    "soundTags": [
      "creator.module.campaign-result.soft",
      "paper.module.reveal"
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
    "accessibilityLabel": "Animated platform-neutral campaign result paper module",
    "platformNeutral": true,
    "thirdPartyLogosBakedIn": false,
    "authorizedLogoSlot": true,
    "replaceableContent": true,
    "composedFromLowerLevelComponents": true,
    "agentSelection": {
      "useWhen": [
        "show_campaign_result",
        "report_campaign"
      ],
      "semanticRole": "metrics",
      "avoidWhen": [
        "imitate_specific_social_platform"
      ]
    },
    "sampleConfig": {
      "title": "Launch campaign",
      "items": [
        {
          "label": "Reach",
          "value": 840000,
          "change": 28
        },
        {
          "label": "Views",
          "value": 312000,
          "change": 22
        },
        {
          "label": "Signups",
          "value": 12400,
          "change": 17
        },
        {
          "label": "Sales",
          "value": 2860,
          "change": 31
        }
      ]
    }
  },
  {
    "id": "module.creator.affiliate-result.paper-01",
    "name": "Affiliate result",
    "version": "2.0.0",
    "category": "creator-module",
    "subtype": "metrics",
    "slug": "affiliate-result",
    "renderer": "affiliate-result",
    "order": 25,
    "intents": [
      "show_affiliate_result",
      "report_conversion"
    ],
    "keywords": [
      "creator",
      "publishing",
      "paper",
      "animated",
      "platform-neutral",
      "metrics",
      "affiliate result",
      "show_affiliate_result",
      "report_conversion"
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
    "contentStates": [
      "short",
      "medium",
      "long"
    ],
    "duration": {
      "minimum": 0.8,
      "recommended": 1.8,
      "maximum": 6
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "drop-and-settle",
      "unfold"
    ],
    "defaultMotion": "cut-paper-pop",
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 88
      },
      "caption": {
        "type": "string",
        "maxCharacters": 240
      },
      "handle": {
        "type": "string",
        "maxCharacters": 56
      },
      "date": {
        "type": "string",
        "maxCharacters": 48
      },
      "avatar": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ]
      },
      "media": {
        "type": "media",
        "accepted": [
          "image",
          "video",
          "transparent-png",
          "website-screenshot"
        ]
      },
      "logo": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ],
        "authorizedOnly": true
      },
      "items": {
        "type": "array",
        "maximumItems": 8
      },
      "contentLength": {
        "type": "enum",
        "values": [
          "short",
          "medium",
          "long"
        ]
      }
    },
    "soundTags": [
      "creator.module.affiliate-result.soft",
      "paper.module.reveal"
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
    "accessibilityLabel": "Animated platform-neutral affiliate result paper module",
    "platformNeutral": true,
    "thirdPartyLogosBakedIn": false,
    "authorizedLogoSlot": true,
    "replaceableContent": true,
    "composedFromLowerLevelComponents": true,
    "agentSelection": {
      "useWhen": [
        "show_affiliate_result",
        "report_conversion"
      ],
      "semanticRole": "metrics",
      "avoidWhen": [
        "imitate_specific_social_platform"
      ]
    },
    "sampleConfig": {
      "title": "Affiliate performance",
      "items": [
        {
          "label": "Clicks",
          "value": 38200,
          "change": 18
        },
        {
          "label": "Trials",
          "value": 6200,
          "change": 26
        },
        {
          "label": "Paid",
          "value": 1480,
          "change": 21
        },
        {
          "label": "Revenue",
          "value": 42600,
          "change": 34
        }
      ]
    }
  },
  {
    "id": "module.creator.link-in-bio-screen.paper-01",
    "name": "Link in bio screen",
    "version": "2.0.0",
    "category": "creator-module",
    "subtype": "action",
    "slug": "link-in-bio-screen",
    "renderer": "link-in-bio-screen",
    "order": 26,
    "intents": [
      "show_link_hub",
      "direct_audience"
    ],
    "keywords": [
      "creator",
      "publishing",
      "paper",
      "animated",
      "platform-neutral",
      "action",
      "link in bio screen",
      "show_link_hub",
      "direct_audience"
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
    "contentStates": [
      "short",
      "medium",
      "long"
    ],
    "duration": {
      "minimum": 0.8,
      "recommended": 1.8,
      "maximum": 6
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "drop-and-settle",
      "unfold"
    ],
    "defaultMotion": "drop-and-settle",
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 88
      },
      "caption": {
        "type": "string",
        "maxCharacters": 240
      },
      "handle": {
        "type": "string",
        "maxCharacters": 56
      },
      "date": {
        "type": "string",
        "maxCharacters": 48
      },
      "avatar": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ]
      },
      "media": {
        "type": "media",
        "accepted": [
          "image",
          "video",
          "transparent-png",
          "website-screenshot"
        ]
      },
      "logo": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ],
        "authorizedOnly": true
      },
      "items": {
        "type": "array",
        "maximumItems": 8
      },
      "contentLength": {
        "type": "enum",
        "values": [
          "short",
          "medium",
          "long"
        ]
      }
    },
    "soundTags": [
      "creator.module.link-in-bio-screen.soft",
      "paper.module.reveal"
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
    "accessibilityLabel": "Animated platform-neutral link in bio screen paper module",
    "platformNeutral": true,
    "thirdPartyLogosBakedIn": false,
    "authorizedLogoSlot": true,
    "replaceableContent": true,
    "composedFromLowerLevelComponents": true,
    "agentSelection": {
      "useWhen": [
        "show_link_hub",
        "direct_audience"
      ],
      "semanticRole": "action",
      "avoidWhen": [
        "imitate_specific_social_platform"
      ]
    },
    "sampleConfig": {
      "title": "Maya Cole",
      "handle": "@mayamakes",
      "items": [
        "Latest video",
        "The Useful Systems Letter",
        "Creator workflow template",
        "Book a workshop"
      ]
    }
  },
  {
    "id": "module.creator.call-to-follow.paper-01",
    "name": "Call to follow",
    "version": "2.0.0",
    "category": "creator-module",
    "subtype": "action",
    "slug": "call-to-follow",
    "renderer": "call-to-follow",
    "order": 27,
    "intents": [
      "ask_to_follow",
      "grow_audience"
    ],
    "keywords": [
      "creator",
      "publishing",
      "paper",
      "animated",
      "platform-neutral",
      "action",
      "call to follow",
      "ask_to_follow",
      "grow_audience"
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
    "contentStates": [
      "short",
      "medium",
      "long"
    ],
    "duration": {
      "minimum": 0.8,
      "recommended": 1.8,
      "maximum": 6
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "drop-and-settle",
      "unfold"
    ],
    "defaultMotion": "paper-slide",
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 88
      },
      "caption": {
        "type": "string",
        "maxCharacters": 240
      },
      "handle": {
        "type": "string",
        "maxCharacters": 56
      },
      "date": {
        "type": "string",
        "maxCharacters": 48
      },
      "avatar": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ]
      },
      "media": {
        "type": "media",
        "accepted": [
          "image",
          "video",
          "transparent-png",
          "website-screenshot"
        ]
      },
      "logo": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ],
        "authorizedOnly": true
      },
      "items": {
        "type": "array",
        "maximumItems": 8
      },
      "contentLength": {
        "type": "enum",
        "values": [
          "short",
          "medium",
          "long"
        ]
      }
    },
    "soundTags": [
      "creator.module.call-to-follow.soft",
      "paper.module.reveal"
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
    "accessibilityLabel": "Animated platform-neutral call to follow paper module",
    "platformNeutral": true,
    "thirdPartyLogosBakedIn": false,
    "authorizedLogoSlot": true,
    "replaceableContent": true,
    "composedFromLowerLevelComponents": true,
    "agentSelection": {
      "useWhen": [
        "ask_to_follow",
        "grow_audience"
      ],
      "semanticRole": "action",
      "avoidWhen": [
        "imitate_specific_social_platform"
      ]
    },
    "sampleConfig": {
      "title": "Follow for practical creator systems",
      "caption": "Clear workflows, honest experiments and useful templates.",
      "handle": "@mayamakes"
    }
  },
  {
    "id": "module.creator.call-to-subscribe.paper-01",
    "name": "Call to subscribe",
    "version": "2.0.0",
    "category": "creator-module",
    "subtype": "action",
    "slug": "call-to-subscribe",
    "renderer": "call-to-subscribe",
    "order": 28,
    "intents": [
      "ask_to_subscribe",
      "grow_subscribers"
    ],
    "keywords": [
      "creator",
      "publishing",
      "paper",
      "animated",
      "platform-neutral",
      "action",
      "call to subscribe",
      "ask_to_subscribe",
      "grow_subscribers"
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
    "contentStates": [
      "short",
      "medium",
      "long"
    ],
    "duration": {
      "minimum": 0.8,
      "recommended": 1.8,
      "maximum": 6
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "drop-and-settle",
      "unfold"
    ],
    "defaultMotion": "cut-paper-pop",
    "slots": {
      "title": {
        "type": "string",
        "maxCharacters": 88
      },
      "caption": {
        "type": "string",
        "maxCharacters": 240
      },
      "handle": {
        "type": "string",
        "maxCharacters": 56
      },
      "date": {
        "type": "string",
        "maxCharacters": 48
      },
      "avatar": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ]
      },
      "media": {
        "type": "media",
        "accepted": [
          "image",
          "video",
          "transparent-png",
          "website-screenshot"
        ]
      },
      "logo": {
        "type": "media",
        "accepted": [
          "image",
          "transparent-png"
        ],
        "authorizedOnly": true
      },
      "items": {
        "type": "array",
        "maximumItems": 8
      },
      "contentLength": {
        "type": "enum",
        "values": [
          "short",
          "medium",
          "long"
        ]
      }
    },
    "soundTags": [
      "creator.module.call-to-subscribe.soft",
      "paper.module.reveal"
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
    "accessibilityLabel": "Animated platform-neutral call to subscribe paper module",
    "platformNeutral": true,
    "thirdPartyLogosBakedIn": false,
    "authorizedLogoSlot": true,
    "replaceableContent": true,
    "composedFromLowerLevelComponents": true,
    "agentSelection": {
      "useWhen": [
        "ask_to_subscribe",
        "grow_subscribers"
      ],
      "semanticRole": "action",
      "avoidWhen": [
        "imitate_specific_social_platform"
      ]
    },
    "sampleConfig": {
      "title": "Subscribe to build better every week",
      "caption": "One deeply useful video every Tuesday.",
      "handle": "128K CREATORS ALREADY HERE"
    }
  }
];
