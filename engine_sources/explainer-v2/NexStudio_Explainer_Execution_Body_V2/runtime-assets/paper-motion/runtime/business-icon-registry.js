window.NEX_BUSINESS_ICONS = [
  {
    "id": "icon.business.revenue.paper-01",
    "name": "Revenue",
    "version": "1.6.0",
    "category": "icon",
    "subtype": "business-commerce",
    "group": "metrics",
    "slug": "revenue",
    "renderer": "revenue",
    "order": 1,
    "intents": [
      "show_revenue",
      "communicate_income"
    ],
    "keywords": [
      "icon",
      "business",
      "commerce",
      "paper",
      "revenue",
      "income",
      "money",
      "growth",
      "finance"
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
      "size": {
        "type": "number",
        "minimum": 24,
        "recommended": 96,
        "maximum": 420
      },
      "treatment": {
        "type": "enum",
        "values": [
          "paper-cutout",
          "printed-outline"
        ]
      },
      "state": {
        "type": "enum",
        "values": [
          "inactive",
          "active"
        ]
      },
      "label": {
        "type": "string",
        "maxCharacters": 56
      },
      "motion": {
        "type": "enum",
        "values": [
          "cut-paper-pop",
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.4
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      }
    },
    "duration": {
      "minimum": 0.45,
      "recommended": 1.2,
      "maximum": 3.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "cut-paper-pop",
      "paper-slide",
      "scale-bounce"
    ],
    "defaultMotion": "cut-paper-pop",
    "states": [
      "inactive",
      "active"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "business.revenue.soft",
      "paper.icon.tap"
    ],
    "themeTokens": [
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
    "accessibilityLabel": "Revenue business and commerce paper icon",
    "description": "A reusable layered paper-style revenue icon for business, commerce, growth, marketing and organizational storytelling.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "show_revenue",
        "communicate_income"
      ],
      "avoidWhen": [],
      "semanticRole": "metrics",
      "polarity": "neutral-or-positive"
    }
  },
  {
    "id": "icon.business.expense.paper-01",
    "name": "Expense",
    "version": "1.6.0",
    "category": "icon",
    "subtype": "business-commerce",
    "group": "metrics",
    "slug": "expense",
    "renderer": "expense",
    "order": 2,
    "intents": [
      "show_expense",
      "communicate_cost"
    ],
    "keywords": [
      "icon",
      "business",
      "commerce",
      "paper",
      "expense",
      "cost",
      "spend",
      "money",
      "finance"
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
      "size": {
        "type": "number",
        "minimum": 24,
        "recommended": 96,
        "maximum": 420
      },
      "treatment": {
        "type": "enum",
        "values": [
          "paper-cutout",
          "printed-outline"
        ]
      },
      "state": {
        "type": "enum",
        "values": [
          "inactive",
          "active"
        ]
      },
      "label": {
        "type": "string",
        "maxCharacters": 56
      },
      "motion": {
        "type": "enum",
        "values": [
          "cut-paper-pop",
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.4
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      }
    },
    "duration": {
      "minimum": 0.45,
      "recommended": 1.2,
      "maximum": 3.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "cut-paper-pop",
      "paper-slide",
      "scale-bounce"
    ],
    "defaultMotion": "cut-paper-pop",
    "states": [
      "inactive",
      "active"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "business.expense.soft",
      "paper.icon.tap"
    ],
    "themeTokens": [
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
    "accessibilityLabel": "Expense business and commerce paper icon",
    "description": "A reusable layered paper-style expense icon for business, commerce, growth, marketing and organizational storytelling.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "show_expense",
        "communicate_cost"
      ],
      "avoidWhen": [
        "show_system_error"
      ],
      "semanticRole": "metrics",
      "polarity": "negative-directional"
    }
  },
  {
    "id": "icon.business.growth.paper-01",
    "name": "Growth",
    "version": "1.6.0",
    "category": "icon",
    "subtype": "business-commerce",
    "group": "metrics",
    "slug": "growth",
    "renderer": "growth",
    "order": 3,
    "intents": [
      "show_growth",
      "communicate_positive_trend"
    ],
    "keywords": [
      "icon",
      "business",
      "commerce",
      "paper",
      "growth",
      "upward",
      "trend",
      "increase",
      "metrics"
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
      "size": {
        "type": "number",
        "minimum": 24,
        "recommended": 96,
        "maximum": 420
      },
      "treatment": {
        "type": "enum",
        "values": [
          "paper-cutout",
          "printed-outline"
        ]
      },
      "state": {
        "type": "enum",
        "values": [
          "inactive",
          "active"
        ]
      },
      "label": {
        "type": "string",
        "maxCharacters": 56
      },
      "motion": {
        "type": "enum",
        "values": [
          "drop-and-settle",
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.4
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      }
    },
    "duration": {
      "minimum": 0.45,
      "recommended": 1.2,
      "maximum": 3.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "drop-and-settle",
      "paper-slide",
      "scale-bounce"
    ],
    "defaultMotion": "drop-and-settle",
    "states": [
      "inactive",
      "active"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "business.growth.soft",
      "paper.icon.tap"
    ],
    "themeTokens": [
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
    "accessibilityLabel": "Growth business and commerce paper icon",
    "description": "A reusable layered paper-style growth icon for business, commerce, growth, marketing and organizational storytelling.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "show_growth",
        "communicate_positive_trend"
      ],
      "avoidWhen": [],
      "semanticRole": "metrics",
      "polarity": "neutral-or-positive"
    }
  },
  {
    "id": "icon.business.decline.paper-01",
    "name": "Decline",
    "version": "1.6.0",
    "category": "icon",
    "subtype": "business-commerce",
    "group": "metrics",
    "slug": "decline",
    "renderer": "decline",
    "order": 4,
    "intents": [
      "show_decline",
      "communicate_negative_trend"
    ],
    "keywords": [
      "icon",
      "business",
      "commerce",
      "paper",
      "decline",
      "downward",
      "trend",
      "decrease",
      "metrics"
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
      "size": {
        "type": "number",
        "minimum": 24,
        "recommended": 96,
        "maximum": 420
      },
      "treatment": {
        "type": "enum",
        "values": [
          "paper-cutout",
          "printed-outline"
        ]
      },
      "state": {
        "type": "enum",
        "values": [
          "inactive",
          "active"
        ]
      },
      "label": {
        "type": "string",
        "maxCharacters": 56
      },
      "motion": {
        "type": "enum",
        "values": [
          "cut-paper-pop",
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.4
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      }
    },
    "duration": {
      "minimum": 0.45,
      "recommended": 1.2,
      "maximum": 3.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "cut-paper-pop",
      "paper-slide",
      "scale-bounce"
    ],
    "defaultMotion": "cut-paper-pop",
    "states": [
      "inactive",
      "active"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "business.decline.soft",
      "paper.icon.tap"
    ],
    "themeTokens": [
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
    "accessibilityLabel": "Decline business and commerce paper icon",
    "description": "A reusable layered paper-style decline icon for business, commerce, growth, marketing and organizational storytelling.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "show_decline",
        "communicate_negative_trend"
      ],
      "avoidWhen": [
        "show_system_error"
      ],
      "semanticRole": "metrics",
      "polarity": "negative-directional"
    }
  },
  {
    "id": "icon.business.customer.paper-01",
    "name": "Customer",
    "version": "1.6.0",
    "category": "icon",
    "subtype": "business-commerce",
    "group": "organization",
    "slug": "customer",
    "renderer": "customer",
    "order": 5,
    "intents": [
      "represent_customer",
      "show_user"
    ],
    "keywords": [
      "icon",
      "business",
      "commerce",
      "paper",
      "customer",
      "user",
      "person",
      "client",
      "audience"
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
      "size": {
        "type": "number",
        "minimum": 24,
        "recommended": 96,
        "maximum": 420
      },
      "treatment": {
        "type": "enum",
        "values": [
          "paper-cutout",
          "printed-outline"
        ]
      },
      "state": {
        "type": "enum",
        "values": [
          "inactive",
          "active"
        ]
      },
      "label": {
        "type": "string",
        "maxCharacters": 56
      },
      "motion": {
        "type": "enum",
        "values": [
          "stamp-impact",
          "cut-paper-pop",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.4
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      }
    },
    "duration": {
      "minimum": 0.45,
      "recommended": 1.2,
      "maximum": 3.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "stamp-impact",
      "cut-paper-pop",
      "paper-slide"
    ],
    "defaultMotion": "stamp-impact",
    "states": [
      "inactive",
      "active"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "business.customer.soft",
      "paper.icon.tap"
    ],
    "themeTokens": [
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
    "accessibilityLabel": "Customer business and commerce paper icon",
    "description": "A reusable layered paper-style customer icon for business, commerce, growth, marketing and organizational storytelling.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "represent_customer",
        "show_user"
      ],
      "avoidWhen": [],
      "semanticRole": "organization",
      "polarity": "neutral-or-positive"
    }
  },
  {
    "id": "icon.business.team.paper-01",
    "name": "Team",
    "version": "1.6.0",
    "category": "icon",
    "subtype": "business-commerce",
    "group": "organization",
    "slug": "team",
    "renderer": "team",
    "order": 6,
    "intents": [
      "represent_team",
      "show_people"
    ],
    "keywords": [
      "icon",
      "business",
      "commerce",
      "paper",
      "team",
      "people",
      "group",
      "staff",
      "organization"
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
      "size": {
        "type": "number",
        "minimum": 24,
        "recommended": 96,
        "maximum": 420
      },
      "treatment": {
        "type": "enum",
        "values": [
          "paper-cutout",
          "printed-outline"
        ]
      },
      "state": {
        "type": "enum",
        "values": [
          "inactive",
          "active"
        ]
      },
      "label": {
        "type": "string",
        "maxCharacters": 56
      },
      "motion": {
        "type": "enum",
        "values": [
          "drop-and-settle",
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.4
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      }
    },
    "duration": {
      "minimum": 0.45,
      "recommended": 1.2,
      "maximum": 3.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "drop-and-settle",
      "paper-slide",
      "scale-bounce"
    ],
    "defaultMotion": "drop-and-settle",
    "states": [
      "inactive",
      "active"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "business.team.soft",
      "paper.icon.tap"
    ],
    "themeTokens": [
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
    "accessibilityLabel": "Team business and commerce paper icon",
    "description": "A reusable layered paper-style team icon for business, commerce, growth, marketing and organizational storytelling.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "represent_team",
        "show_people"
      ],
      "avoidWhen": [],
      "semanticRole": "organization",
      "polarity": "neutral-or-positive"
    }
  },
  {
    "id": "icon.business.company.paper-01",
    "name": "Company",
    "version": "1.6.0",
    "category": "icon",
    "subtype": "business-commerce",
    "group": "organization",
    "slug": "company",
    "renderer": "company",
    "order": 7,
    "intents": [
      "represent_company",
      "show_business"
    ],
    "keywords": [
      "icon",
      "business",
      "commerce",
      "paper",
      "company",
      "business",
      "building",
      "organization",
      "brand"
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
      "size": {
        "type": "number",
        "minimum": 24,
        "recommended": 96,
        "maximum": 420
      },
      "treatment": {
        "type": "enum",
        "values": [
          "paper-cutout",
          "printed-outline"
        ]
      },
      "state": {
        "type": "enum",
        "values": [
          "inactive",
          "active"
        ]
      },
      "label": {
        "type": "string",
        "maxCharacters": 56
      },
      "motion": {
        "type": "enum",
        "values": [
          "cut-paper-pop",
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.4
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      }
    },
    "duration": {
      "minimum": 0.45,
      "recommended": 1.2,
      "maximum": 3.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "cut-paper-pop",
      "paper-slide",
      "scale-bounce"
    ],
    "defaultMotion": "cut-paper-pop",
    "states": [
      "inactive",
      "active"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "business.company.soft",
      "paper.icon.tap"
    ],
    "themeTokens": [
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
    "accessibilityLabel": "Company business and commerce paper icon",
    "description": "A reusable layered paper-style company icon for business, commerce, growth, marketing and organizational storytelling.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "represent_company",
        "show_business"
      ],
      "avoidWhen": [],
      "semanticRole": "organization",
      "polarity": "neutral-or-positive"
    }
  },
  {
    "id": "icon.business.product.paper-01",
    "name": "Product",
    "version": "1.6.0",
    "category": "icon",
    "subtype": "business-commerce",
    "group": "commerce",
    "slug": "product",
    "renderer": "product",
    "order": 8,
    "intents": [
      "represent_product",
      "show_offering"
    ],
    "keywords": [
      "icon",
      "business",
      "commerce",
      "paper",
      "product",
      "cube",
      "offering",
      "item",
      "business"
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
      "size": {
        "type": "number",
        "minimum": 24,
        "recommended": 96,
        "maximum": 420
      },
      "treatment": {
        "type": "enum",
        "values": [
          "paper-cutout",
          "printed-outline"
        ]
      },
      "state": {
        "type": "enum",
        "values": [
          "inactive",
          "active"
        ]
      },
      "label": {
        "type": "string",
        "maxCharacters": 56
      },
      "motion": {
        "type": "enum",
        "values": [
          "cut-paper-pop",
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.4
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      }
    },
    "duration": {
      "minimum": 0.45,
      "recommended": 1.2,
      "maximum": 3.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "cut-paper-pop",
      "paper-slide",
      "scale-bounce"
    ],
    "defaultMotion": "cut-paper-pop",
    "states": [
      "inactive",
      "active"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "business.product.soft",
      "paper.icon.tap"
    ],
    "themeTokens": [
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
    "accessibilityLabel": "Product business and commerce paper icon",
    "description": "A reusable layered paper-style product icon for business, commerce, growth, marketing and organizational storytelling.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "represent_product",
        "show_offering"
      ],
      "avoidWhen": [],
      "semanticRole": "commerce",
      "polarity": "neutral-or-positive"
    }
  },
  {
    "id": "icon.business.package.paper-01",
    "name": "Package",
    "version": "1.6.0",
    "category": "icon",
    "subtype": "business-commerce",
    "group": "commerce",
    "slug": "package",
    "renderer": "package",
    "order": 9,
    "intents": [
      "show_package",
      "represent_shipping_box"
    ],
    "keywords": [
      "icon",
      "business",
      "commerce",
      "paper",
      "package",
      "box",
      "shipping",
      "parcel",
      "commerce"
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
      "size": {
        "type": "number",
        "minimum": 24,
        "recommended": 96,
        "maximum": 420
      },
      "treatment": {
        "type": "enum",
        "values": [
          "paper-cutout",
          "printed-outline"
        ]
      },
      "state": {
        "type": "enum",
        "values": [
          "inactive",
          "active"
        ]
      },
      "label": {
        "type": "string",
        "maxCharacters": 56
      },
      "motion": {
        "type": "enum",
        "values": [
          "drop-and-settle",
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.4
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      }
    },
    "duration": {
      "minimum": 0.45,
      "recommended": 1.2,
      "maximum": 3.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "drop-and-settle",
      "paper-slide",
      "scale-bounce"
    ],
    "defaultMotion": "drop-and-settle",
    "states": [
      "inactive",
      "active"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "business.package.soft",
      "paper.icon.tap"
    ],
    "themeTokens": [
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
    "accessibilityLabel": "Package business and commerce paper icon",
    "description": "A reusable layered paper-style package icon for business, commerce, growth, marketing and organizational storytelling.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "show_package",
        "represent_shipping_box"
      ],
      "avoidWhen": [],
      "semanticRole": "commerce",
      "polarity": "neutral-or-positive"
    }
  },
  {
    "id": "icon.business.store.paper-01",
    "name": "Store",
    "version": "1.6.0",
    "category": "icon",
    "subtype": "business-commerce",
    "group": "commerce",
    "slug": "store",
    "renderer": "store",
    "order": 10,
    "intents": [
      "represent_store",
      "show_retail"
    ],
    "keywords": [
      "icon",
      "business",
      "commerce",
      "paper",
      "store",
      "shop",
      "retail",
      "commerce",
      "market"
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
      "size": {
        "type": "number",
        "minimum": 24,
        "recommended": 96,
        "maximum": 420
      },
      "treatment": {
        "type": "enum",
        "values": [
          "paper-cutout",
          "printed-outline"
        ]
      },
      "state": {
        "type": "enum",
        "values": [
          "inactive",
          "active"
        ]
      },
      "label": {
        "type": "string",
        "maxCharacters": 56
      },
      "motion": {
        "type": "enum",
        "values": [
          "stamp-impact",
          "cut-paper-pop",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.4
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      }
    },
    "duration": {
      "minimum": 0.45,
      "recommended": 1.2,
      "maximum": 3.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "stamp-impact",
      "cut-paper-pop",
      "paper-slide"
    ],
    "defaultMotion": "stamp-impact",
    "states": [
      "inactive",
      "active"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "business.store.soft",
      "paper.icon.tap"
    ],
    "themeTokens": [
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
    "accessibilityLabel": "Store business and commerce paper icon",
    "description": "A reusable layered paper-style store icon for business, commerce, growth, marketing and organizational storytelling.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "represent_store",
        "show_retail"
      ],
      "avoidWhen": [],
      "semanticRole": "commerce",
      "polarity": "neutral-or-positive"
    }
  },
  {
    "id": "icon.business.shopping-cart.paper-01",
    "name": "Shopping cart",
    "version": "1.6.0",
    "category": "icon",
    "subtype": "business-commerce",
    "group": "commerce",
    "slug": "shopping-cart",
    "renderer": "shopping-cart",
    "order": 11,
    "intents": [
      "show_cart",
      "add_to_cart"
    ],
    "keywords": [
      "icon",
      "business",
      "commerce",
      "paper",
      "shopping",
      "cart",
      "basket",
      "commerce",
      "checkout"
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
      "size": {
        "type": "number",
        "minimum": 24,
        "recommended": 96,
        "maximum": 420
      },
      "treatment": {
        "type": "enum",
        "values": [
          "paper-cutout",
          "printed-outline"
        ]
      },
      "state": {
        "type": "enum",
        "values": [
          "inactive",
          "active"
        ]
      },
      "label": {
        "type": "string",
        "maxCharacters": 56
      },
      "motion": {
        "type": "enum",
        "values": [
          "cut-paper-pop",
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.4
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      }
    },
    "duration": {
      "minimum": 0.45,
      "recommended": 1.2,
      "maximum": 3.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "cut-paper-pop",
      "paper-slide",
      "scale-bounce"
    ],
    "defaultMotion": "cut-paper-pop",
    "states": [
      "inactive",
      "active"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "business.shopping-cart.soft",
      "paper.icon.tap"
    ],
    "themeTokens": [
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
    "accessibilityLabel": "Shopping cart business and commerce paper icon",
    "description": "A reusable layered paper-style shopping cart icon for business, commerce, growth, marketing and organizational storytelling.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "show_cart",
        "add_to_cart"
      ],
      "avoidWhen": [],
      "semanticRole": "commerce",
      "polarity": "neutral-or-positive"
    }
  },
  {
    "id": "icon.business.order.paper-01",
    "name": "Order",
    "version": "1.6.0",
    "category": "icon",
    "subtype": "business-commerce",
    "group": "commerce",
    "slug": "order",
    "renderer": "order",
    "order": 12,
    "intents": [
      "show_order",
      "confirm_order"
    ],
    "keywords": [
      "icon",
      "business",
      "commerce",
      "paper",
      "order",
      "clipboard",
      "purchase",
      "check",
      "commerce"
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
      "size": {
        "type": "number",
        "minimum": 24,
        "recommended": 96,
        "maximum": 420
      },
      "treatment": {
        "type": "enum",
        "values": [
          "paper-cutout",
          "printed-outline"
        ]
      },
      "state": {
        "type": "enum",
        "values": [
          "inactive",
          "active",
          "completed"
        ]
      },
      "label": {
        "type": "string",
        "maxCharacters": 56
      },
      "motion": {
        "type": "enum",
        "values": [
          "drop-and-settle",
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.4
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      }
    },
    "duration": {
      "minimum": 0.45,
      "recommended": 1.2,
      "maximum": 3.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "drop-and-settle",
      "paper-slide",
      "scale-bounce"
    ],
    "defaultMotion": "drop-and-settle",
    "states": [
      "inactive",
      "active",
      "completed"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "business.order.soft",
      "paper.icon.tap"
    ],
    "themeTokens": [
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
    "accessibilityLabel": "Order business and commerce paper icon",
    "description": "A reusable layered paper-style order icon for business, commerce, growth, marketing and organizational storytelling.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "show_order",
        "confirm_order"
      ],
      "avoidWhen": [],
      "semanticRole": "commerce",
      "polarity": "neutral-or-positive"
    }
  },
  {
    "id": "icon.business.delivery.paper-01",
    "name": "Delivery",
    "version": "1.6.0",
    "category": "icon",
    "subtype": "business-commerce",
    "group": "commerce",
    "slug": "delivery",
    "renderer": "delivery",
    "order": 13,
    "intents": [
      "show_delivery",
      "represent_shipping"
    ],
    "keywords": [
      "icon",
      "business",
      "commerce",
      "paper",
      "delivery",
      "truck",
      "shipping",
      "logistics",
      "commerce"
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
      "size": {
        "type": "number",
        "minimum": 24,
        "recommended": 96,
        "maximum": 420
      },
      "treatment": {
        "type": "enum",
        "values": [
          "paper-cutout",
          "printed-outline"
        ]
      },
      "state": {
        "type": "enum",
        "values": [
          "inactive",
          "active",
          "completed"
        ]
      },
      "label": {
        "type": "string",
        "maxCharacters": 56
      },
      "motion": {
        "type": "enum",
        "values": [
          "cut-paper-pop",
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.4
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      }
    },
    "duration": {
      "minimum": 0.45,
      "recommended": 1.2,
      "maximum": 3.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "cut-paper-pop",
      "paper-slide",
      "scale-bounce"
    ],
    "defaultMotion": "cut-paper-pop",
    "states": [
      "inactive",
      "active",
      "completed"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "business.delivery.soft",
      "paper.icon.tap"
    ],
    "themeTokens": [
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
    "accessibilityLabel": "Delivery business and commerce paper icon",
    "description": "A reusable layered paper-style delivery icon for business, commerce, growth, marketing and organizational storytelling.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "show_delivery",
        "represent_shipping"
      ],
      "avoidWhen": [],
      "semanticRole": "commerce",
      "polarity": "neutral-or-positive"
    }
  },
  {
    "id": "icon.business.payment.paper-01",
    "name": "Payment",
    "version": "1.6.0",
    "category": "icon",
    "subtype": "business-commerce",
    "group": "commerce",
    "slug": "payment",
    "renderer": "payment",
    "order": 14,
    "intents": [
      "show_payment",
      "complete_transaction"
    ],
    "keywords": [
      "icon",
      "business",
      "commerce",
      "paper",
      "payment",
      "card",
      "transaction",
      "money",
      "checkout"
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
      "size": {
        "type": "number",
        "minimum": 24,
        "recommended": 96,
        "maximum": 420
      },
      "treatment": {
        "type": "enum",
        "values": [
          "paper-cutout",
          "printed-outline"
        ]
      },
      "state": {
        "type": "enum",
        "values": [
          "inactive",
          "active",
          "completed"
        ]
      },
      "label": {
        "type": "string",
        "maxCharacters": 56
      },
      "motion": {
        "type": "enum",
        "values": [
          "cut-paper-pop",
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.4
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      }
    },
    "duration": {
      "minimum": 0.45,
      "recommended": 1.2,
      "maximum": 3.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "cut-paper-pop",
      "paper-slide",
      "scale-bounce"
    ],
    "defaultMotion": "cut-paper-pop",
    "states": [
      "inactive",
      "active",
      "completed"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "business.payment.soft",
      "paper.icon.tap"
    ],
    "themeTokens": [
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
    "accessibilityLabel": "Payment business and commerce paper icon",
    "description": "A reusable layered paper-style payment icon for business, commerce, growth, marketing and organizational storytelling.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "show_payment",
        "complete_transaction"
      ],
      "avoidWhen": [],
      "semanticRole": "commerce",
      "polarity": "neutral-or-positive"
    }
  },
  {
    "id": "icon.business.subscription.paper-01",
    "name": "Subscription",
    "version": "1.6.0",
    "category": "icon",
    "subtype": "business-commerce",
    "group": "commerce",
    "slug": "subscription",
    "renderer": "subscription",
    "order": 15,
    "intents": [
      "show_subscription",
      "represent_recurring_payment"
    ],
    "keywords": [
      "icon",
      "business",
      "commerce",
      "paper",
      "subscription",
      "recurring",
      "renewal",
      "plan",
      "payment"
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
      "size": {
        "type": "number",
        "minimum": 24,
        "recommended": 96,
        "maximum": 420
      },
      "treatment": {
        "type": "enum",
        "values": [
          "paper-cutout",
          "printed-outline"
        ]
      },
      "state": {
        "type": "enum",
        "values": [
          "inactive",
          "active",
          "completed"
        ]
      },
      "label": {
        "type": "string",
        "maxCharacters": 56
      },
      "motion": {
        "type": "enum",
        "values": [
          "stamp-impact",
          "cut-paper-pop",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.4
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      }
    },
    "duration": {
      "minimum": 0.45,
      "recommended": 1.2,
      "maximum": 3.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "stamp-impact",
      "cut-paper-pop",
      "paper-slide"
    ],
    "defaultMotion": "stamp-impact",
    "states": [
      "inactive",
      "active",
      "completed"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "business.subscription.soft",
      "paper.icon.tap"
    ],
    "themeTokens": [
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
    "accessibilityLabel": "Subscription business and commerce paper icon",
    "description": "A reusable layered paper-style subscription icon for business, commerce, growth, marketing and organizational storytelling.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "show_subscription",
        "represent_recurring_payment"
      ],
      "avoidWhen": [],
      "semanticRole": "commerce",
      "polarity": "neutral-or-positive"
    }
  },
  {
    "id": "icon.business.invoice.paper-01",
    "name": "Invoice",
    "version": "1.6.0",
    "category": "icon",
    "subtype": "business-commerce",
    "group": "commerce",
    "slug": "invoice",
    "renderer": "invoice",
    "order": 16,
    "intents": [
      "show_invoice",
      "represent_bill"
    ],
    "keywords": [
      "icon",
      "business",
      "commerce",
      "paper",
      "invoice",
      "bill",
      "document",
      "amount",
      "finance"
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
      "size": {
        "type": "number",
        "minimum": 24,
        "recommended": 96,
        "maximum": 420
      },
      "treatment": {
        "type": "enum",
        "values": [
          "paper-cutout",
          "printed-outline"
        ]
      },
      "state": {
        "type": "enum",
        "values": [
          "inactive",
          "active",
          "completed"
        ]
      },
      "label": {
        "type": "string",
        "maxCharacters": 56
      },
      "motion": {
        "type": "enum",
        "values": [
          "cut-paper-pop",
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.4
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      }
    },
    "duration": {
      "minimum": 0.45,
      "recommended": 1.2,
      "maximum": 3.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "cut-paper-pop",
      "paper-slide",
      "scale-bounce"
    ],
    "defaultMotion": "cut-paper-pop",
    "states": [
      "inactive",
      "active",
      "completed"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "business.invoice.soft",
      "paper.icon.tap"
    ],
    "themeTokens": [
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
    "accessibilityLabel": "Invoice business and commerce paper icon",
    "description": "A reusable layered paper-style invoice icon for business, commerce, growth, marketing and organizational storytelling.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "show_invoice",
        "represent_bill"
      ],
      "avoidWhen": [],
      "semanticRole": "commerce",
      "polarity": "neutral-or-positive"
    }
  },
  {
    "id": "icon.business.receipt.paper-01",
    "name": "Receipt",
    "version": "1.6.0",
    "category": "icon",
    "subtype": "business-commerce",
    "group": "commerce",
    "slug": "receipt",
    "renderer": "receipt",
    "order": 17,
    "intents": [
      "show_receipt",
      "confirm_purchase"
    ],
    "keywords": [
      "icon",
      "business",
      "commerce",
      "paper",
      "receipt",
      "purchase",
      "proof",
      "transaction",
      "commerce"
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
      "size": {
        "type": "number",
        "minimum": 24,
        "recommended": 96,
        "maximum": 420
      },
      "treatment": {
        "type": "enum",
        "values": [
          "paper-cutout",
          "printed-outline"
        ]
      },
      "state": {
        "type": "enum",
        "values": [
          "inactive",
          "active",
          "completed"
        ]
      },
      "label": {
        "type": "string",
        "maxCharacters": 56
      },
      "motion": {
        "type": "enum",
        "values": [
          "cut-paper-pop",
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.4
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      }
    },
    "duration": {
      "minimum": 0.45,
      "recommended": 1.2,
      "maximum": 3.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "cut-paper-pop",
      "paper-slide",
      "scale-bounce"
    ],
    "defaultMotion": "cut-paper-pop",
    "states": [
      "inactive",
      "active",
      "completed"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "business.receipt.soft",
      "paper.icon.tap"
    ],
    "themeTokens": [
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
    "accessibilityLabel": "Receipt business and commerce paper icon",
    "description": "A reusable layered paper-style receipt icon for business, commerce, growth, marketing and organizational storytelling.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "show_receipt",
        "confirm_purchase"
      ],
      "avoidWhen": [],
      "semanticRole": "commerce",
      "polarity": "neutral-or-positive"
    }
  },
  {
    "id": "icon.business.contract.paper-01",
    "name": "Contract",
    "version": "1.6.0",
    "category": "icon",
    "subtype": "business-commerce",
    "group": "organization",
    "slug": "contract",
    "renderer": "contract",
    "order": 18,
    "intents": [
      "show_contract",
      "represent_agreement"
    ],
    "keywords": [
      "icon",
      "business",
      "commerce",
      "paper",
      "contract",
      "agreement",
      "signature",
      "document",
      "business"
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
      "size": {
        "type": "number",
        "minimum": 24,
        "recommended": 96,
        "maximum": 420
      },
      "treatment": {
        "type": "enum",
        "values": [
          "paper-cutout",
          "printed-outline"
        ]
      },
      "state": {
        "type": "enum",
        "values": [
          "inactive",
          "active",
          "completed"
        ]
      },
      "label": {
        "type": "string",
        "maxCharacters": 56
      },
      "motion": {
        "type": "enum",
        "values": [
          "drop-and-settle",
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.4
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      }
    },
    "duration": {
      "minimum": 0.45,
      "recommended": 1.2,
      "maximum": 3.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "drop-and-settle",
      "paper-slide",
      "scale-bounce"
    ],
    "defaultMotion": "drop-and-settle",
    "states": [
      "inactive",
      "active",
      "completed"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "business.contract.soft",
      "paper.icon.tap"
    ],
    "themeTokens": [
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
    "accessibilityLabel": "Contract business and commerce paper icon",
    "description": "A reusable layered paper-style contract icon for business, commerce, growth, marketing and organizational storytelling.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "show_contract",
        "represent_agreement"
      ],
      "avoidWhen": [],
      "semanticRole": "organization",
      "polarity": "neutral-or-positive"
    }
  },
  {
    "id": "icon.business.target.paper-01",
    "name": "Target",
    "version": "1.6.0",
    "category": "icon",
    "subtype": "business-commerce",
    "group": "metrics",
    "slug": "target",
    "renderer": "target",
    "order": 19,
    "intents": [
      "show_target",
      "communicate_objective"
    ],
    "keywords": [
      "icon",
      "business",
      "commerce",
      "paper",
      "target",
      "bullseye",
      "objective",
      "aim",
      "goal"
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
      "size": {
        "type": "number",
        "minimum": 24,
        "recommended": 96,
        "maximum": 420
      },
      "treatment": {
        "type": "enum",
        "values": [
          "paper-cutout",
          "printed-outline"
        ]
      },
      "state": {
        "type": "enum",
        "values": [
          "inactive",
          "active",
          "completed"
        ]
      },
      "label": {
        "type": "string",
        "maxCharacters": 56
      },
      "motion": {
        "type": "enum",
        "values": [
          "cut-paper-pop",
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.4
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      }
    },
    "duration": {
      "minimum": 0.45,
      "recommended": 1.2,
      "maximum": 3.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "cut-paper-pop",
      "paper-slide",
      "scale-bounce"
    ],
    "defaultMotion": "cut-paper-pop",
    "states": [
      "inactive",
      "active",
      "completed"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "business.target.soft",
      "paper.icon.tap"
    ],
    "themeTokens": [
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
    "accessibilityLabel": "Target business and commerce paper icon",
    "description": "A reusable layered paper-style target icon for business, commerce, growth, marketing and organizational storytelling.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "show_target",
        "communicate_objective"
      ],
      "avoidWhen": [],
      "semanticRole": "metrics",
      "polarity": "neutral-or-positive"
    }
  },
  {
    "id": "icon.business.goal.paper-01",
    "name": "Goal",
    "version": "1.6.0",
    "category": "icon",
    "subtype": "business-commerce",
    "group": "metrics",
    "slug": "goal",
    "renderer": "goal",
    "order": 20,
    "intents": [
      "show_goal",
      "communicate_destination"
    ],
    "keywords": [
      "icon",
      "business",
      "commerce",
      "paper",
      "goal",
      "flag",
      "objective",
      "destination",
      "achievement"
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
      "size": {
        "type": "number",
        "minimum": 24,
        "recommended": 96,
        "maximum": 420
      },
      "treatment": {
        "type": "enum",
        "values": [
          "paper-cutout",
          "printed-outline"
        ]
      },
      "state": {
        "type": "enum",
        "values": [
          "inactive",
          "active",
          "completed"
        ]
      },
      "label": {
        "type": "string",
        "maxCharacters": 56
      },
      "motion": {
        "type": "enum",
        "values": [
          "stamp-impact",
          "cut-paper-pop",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.4
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      }
    },
    "duration": {
      "minimum": 0.45,
      "recommended": 1.2,
      "maximum": 3.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "stamp-impact",
      "cut-paper-pop",
      "paper-slide"
    ],
    "defaultMotion": "stamp-impact",
    "states": [
      "inactive",
      "active",
      "completed"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "business.goal.soft",
      "paper.icon.tap"
    ],
    "themeTokens": [
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
    "accessibilityLabel": "Goal business and commerce paper icon",
    "description": "A reusable layered paper-style goal icon for business, commerce, growth, marketing and organizational storytelling.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "show_goal",
        "communicate_destination"
      ],
      "avoidWhen": [],
      "semanticRole": "metrics",
      "polarity": "neutral-or-positive"
    }
  },
  {
    "id": "icon.business.trophy.paper-01",
    "name": "Trophy",
    "version": "1.6.0",
    "category": "icon",
    "subtype": "business-commerce",
    "group": "metrics",
    "slug": "trophy",
    "renderer": "trophy",
    "order": 21,
    "intents": [
      "show_win",
      "celebrate_achievement"
    ],
    "keywords": [
      "icon",
      "business",
      "commerce",
      "paper",
      "trophy",
      "award",
      "win",
      "success",
      "achievement"
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
      "size": {
        "type": "number",
        "minimum": 24,
        "recommended": 96,
        "maximum": 420
      },
      "treatment": {
        "type": "enum",
        "values": [
          "paper-cutout",
          "printed-outline"
        ]
      },
      "state": {
        "type": "enum",
        "values": [
          "inactive",
          "active",
          "completed"
        ]
      },
      "label": {
        "type": "string",
        "maxCharacters": 56
      },
      "motion": {
        "type": "enum",
        "values": [
          "drop-and-settle",
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.4
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      }
    },
    "duration": {
      "minimum": 0.45,
      "recommended": 1.2,
      "maximum": 3.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "drop-and-settle",
      "paper-slide",
      "scale-bounce"
    ],
    "defaultMotion": "drop-and-settle",
    "states": [
      "inactive",
      "active",
      "completed"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "business.trophy.soft",
      "paper.icon.tap"
    ],
    "themeTokens": [
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
    "accessibilityLabel": "Trophy business and commerce paper icon",
    "description": "A reusable layered paper-style trophy icon for business, commerce, growth, marketing and organizational storytelling.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "show_win",
        "celebrate_achievement"
      ],
      "avoidWhen": [],
      "semanticRole": "metrics",
      "polarity": "neutral-or-positive"
    }
  },
  {
    "id": "icon.business.milestone.paper-01",
    "name": "Milestone",
    "version": "1.6.0",
    "category": "icon",
    "subtype": "business-commerce",
    "group": "metrics",
    "slug": "milestone",
    "renderer": "milestone",
    "order": 22,
    "intents": [
      "show_milestone",
      "communicate_progress"
    ],
    "keywords": [
      "icon",
      "business",
      "commerce",
      "paper",
      "milestone",
      "path",
      "progress",
      "marker",
      "achievement"
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
      "size": {
        "type": "number",
        "minimum": 24,
        "recommended": 96,
        "maximum": 420
      },
      "treatment": {
        "type": "enum",
        "values": [
          "paper-cutout",
          "printed-outline"
        ]
      },
      "state": {
        "type": "enum",
        "values": [
          "inactive",
          "active",
          "completed"
        ]
      },
      "label": {
        "type": "string",
        "maxCharacters": 56
      },
      "motion": {
        "type": "enum",
        "values": [
          "cut-paper-pop",
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.4
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      }
    },
    "duration": {
      "minimum": 0.45,
      "recommended": 1.2,
      "maximum": 3.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "cut-paper-pop",
      "paper-slide",
      "scale-bounce"
    ],
    "defaultMotion": "cut-paper-pop",
    "states": [
      "inactive",
      "active",
      "completed"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "business.milestone.soft",
      "paper.icon.tap"
    ],
    "themeTokens": [
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
    "accessibilityLabel": "Milestone business and commerce paper icon",
    "description": "A reusable layered paper-style milestone icon for business, commerce, growth, marketing and organizational storytelling.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "show_milestone",
        "communicate_progress"
      ],
      "avoidWhen": [],
      "semanticRole": "metrics",
      "polarity": "neutral-or-positive"
    }
  },
  {
    "id": "icon.business.launch.paper-01",
    "name": "Launch",
    "version": "1.6.0",
    "category": "icon",
    "subtype": "business-commerce",
    "group": "marketing",
    "slug": "launch",
    "renderer": "launch",
    "order": 23,
    "intents": [
      "show_launch",
      "announce_release"
    ],
    "keywords": [
      "icon",
      "business",
      "commerce",
      "paper",
      "launch",
      "rocket",
      "release",
      "start",
      "product"
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
      "size": {
        "type": "number",
        "minimum": 24,
        "recommended": 96,
        "maximum": 420
      },
      "treatment": {
        "type": "enum",
        "values": [
          "paper-cutout",
          "printed-outline"
        ]
      },
      "state": {
        "type": "enum",
        "values": [
          "inactive",
          "active",
          "completed"
        ]
      },
      "label": {
        "type": "string",
        "maxCharacters": 56
      },
      "motion": {
        "type": "enum",
        "values": [
          "cut-paper-pop",
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.4
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      }
    },
    "duration": {
      "minimum": 0.45,
      "recommended": 1.2,
      "maximum": 3.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "cut-paper-pop",
      "paper-slide",
      "scale-bounce"
    ],
    "defaultMotion": "cut-paper-pop",
    "states": [
      "inactive",
      "active",
      "completed"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "business.launch.soft",
      "paper.icon.tap"
    ],
    "themeTokens": [
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
    "accessibilityLabel": "Launch business and commerce paper icon",
    "description": "A reusable layered paper-style launch icon for business, commerce, growth, marketing and organizational storytelling.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "show_launch",
        "announce_release"
      ],
      "avoidWhen": [],
      "semanticRole": "marketing",
      "polarity": "neutral-or-positive"
    }
  },
  {
    "id": "icon.business.rocket.paper-01",
    "name": "Rocket",
    "version": "1.6.0",
    "category": "icon",
    "subtype": "business-commerce",
    "group": "marketing",
    "slug": "rocket",
    "renderer": "rocket",
    "order": 24,
    "intents": [
      "represent_rocket",
      "show_acceleration"
    ],
    "keywords": [
      "icon",
      "business",
      "commerce",
      "paper",
      "rocket",
      "speed",
      "startup",
      "launch",
      "growth"
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
      "size": {
        "type": "number",
        "minimum": 24,
        "recommended": 96,
        "maximum": 420
      },
      "treatment": {
        "type": "enum",
        "values": [
          "paper-cutout",
          "printed-outline"
        ]
      },
      "state": {
        "type": "enum",
        "values": [
          "inactive",
          "active"
        ]
      },
      "label": {
        "type": "string",
        "maxCharacters": 56
      },
      "motion": {
        "type": "enum",
        "values": [
          "drop-and-settle",
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.4
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      }
    },
    "duration": {
      "minimum": 0.45,
      "recommended": 1.2,
      "maximum": 3.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "drop-and-settle",
      "paper-slide",
      "scale-bounce"
    ],
    "defaultMotion": "drop-and-settle",
    "states": [
      "inactive",
      "active"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "business.rocket.soft",
      "paper.icon.tap"
    ],
    "themeTokens": [
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
    "accessibilityLabel": "Rocket business and commerce paper icon",
    "description": "A reusable layered paper-style rocket icon for business, commerce, growth, marketing and organizational storytelling.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "represent_rocket",
        "show_acceleration"
      ],
      "avoidWhen": [],
      "semanticRole": "marketing",
      "polarity": "neutral-or-positive"
    }
  },
  {
    "id": "icon.business.campaign.paper-01",
    "name": "Campaign",
    "version": "1.6.0",
    "category": "icon",
    "subtype": "business-commerce",
    "group": "marketing",
    "slug": "campaign",
    "renderer": "campaign",
    "order": 25,
    "intents": [
      "show_campaign",
      "announce_marketing"
    ],
    "keywords": [
      "icon",
      "business",
      "commerce",
      "paper",
      "campaign",
      "marketing",
      "message",
      "promotion",
      "megaphone"
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
      "size": {
        "type": "number",
        "minimum": 24,
        "recommended": 96,
        "maximum": 420
      },
      "treatment": {
        "type": "enum",
        "values": [
          "paper-cutout",
          "printed-outline"
        ]
      },
      "state": {
        "type": "enum",
        "values": [
          "inactive",
          "active",
          "completed"
        ]
      },
      "label": {
        "type": "string",
        "maxCharacters": 56
      },
      "motion": {
        "type": "enum",
        "values": [
          "stamp-impact",
          "cut-paper-pop",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.4
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      }
    },
    "duration": {
      "minimum": 0.45,
      "recommended": 1.2,
      "maximum": 3.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "stamp-impact",
      "cut-paper-pop",
      "paper-slide"
    ],
    "defaultMotion": "stamp-impact",
    "states": [
      "inactive",
      "active",
      "completed"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "business.campaign.soft",
      "paper.icon.tap"
    ],
    "themeTokens": [
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
    "accessibilityLabel": "Campaign business and commerce paper icon",
    "description": "A reusable layered paper-style campaign icon for business, commerce, growth, marketing and organizational storytelling.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "show_campaign",
        "announce_marketing"
      ],
      "avoidWhen": [],
      "semanticRole": "marketing",
      "polarity": "neutral-or-positive"
    }
  },
  {
    "id": "icon.business.megaphone.paper-01",
    "name": "Megaphone",
    "version": "1.6.0",
    "category": "icon",
    "subtype": "business-commerce",
    "group": "marketing",
    "slug": "megaphone",
    "renderer": "megaphone",
    "order": 26,
    "intents": [
      "announce_message",
      "show_promotion"
    ],
    "keywords": [
      "icon",
      "business",
      "commerce",
      "paper",
      "megaphone",
      "announcement",
      "marketing",
      "broadcast",
      "message"
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
      "size": {
        "type": "number",
        "minimum": 24,
        "recommended": 96,
        "maximum": 420
      },
      "treatment": {
        "type": "enum",
        "values": [
          "paper-cutout",
          "printed-outline"
        ]
      },
      "state": {
        "type": "enum",
        "values": [
          "inactive",
          "active"
        ]
      },
      "label": {
        "type": "string",
        "maxCharacters": 56
      },
      "motion": {
        "type": "enum",
        "values": [
          "cut-paper-pop",
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.4
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      }
    },
    "duration": {
      "minimum": 0.45,
      "recommended": 1.2,
      "maximum": 3.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "cut-paper-pop",
      "paper-slide",
      "scale-bounce"
    ],
    "defaultMotion": "cut-paper-pop",
    "states": [
      "inactive",
      "active"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "business.megaphone.soft",
      "paper.icon.tap"
    ],
    "themeTokens": [
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
    "accessibilityLabel": "Megaphone business and commerce paper icon",
    "description": "A reusable layered paper-style megaphone icon for business, commerce, growth, marketing and organizational storytelling.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "announce_message",
        "show_promotion"
      ],
      "avoidWhen": [],
      "semanticRole": "marketing",
      "polarity": "neutral-or-positive"
    }
  },
  {
    "id": "icon.business.audience.paper-01",
    "name": "Audience",
    "version": "1.6.0",
    "category": "icon",
    "subtype": "business-commerce",
    "group": "marketing",
    "slug": "audience",
    "renderer": "audience",
    "order": 27,
    "intents": [
      "show_audience",
      "represent_reach"
    ],
    "keywords": [
      "icon",
      "business",
      "commerce",
      "paper",
      "audience",
      "people",
      "reach",
      "community",
      "marketing"
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
      "size": {
        "type": "number",
        "minimum": 24,
        "recommended": 96,
        "maximum": 420
      },
      "treatment": {
        "type": "enum",
        "values": [
          "paper-cutout",
          "printed-outline"
        ]
      },
      "state": {
        "type": "enum",
        "values": [
          "inactive",
          "active"
        ]
      },
      "label": {
        "type": "string",
        "maxCharacters": 56
      },
      "motion": {
        "type": "enum",
        "values": [
          "drop-and-settle",
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.4
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      }
    },
    "duration": {
      "minimum": 0.45,
      "recommended": 1.2,
      "maximum": 3.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "drop-and-settle",
      "paper-slide",
      "scale-bounce"
    ],
    "defaultMotion": "drop-and-settle",
    "states": [
      "inactive",
      "active"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "business.audience.soft",
      "paper.icon.tap"
    ],
    "themeTokens": [
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
    "accessibilityLabel": "Audience business and commerce paper icon",
    "description": "A reusable layered paper-style audience icon for business, commerce, growth, marketing and organizational storytelling.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "show_audience",
        "represent_reach"
      ],
      "avoidWhen": [],
      "semanticRole": "marketing",
      "polarity": "neutral-or-positive"
    }
  },
  {
    "id": "icon.business.conversion.paper-01",
    "name": "Conversion",
    "version": "1.6.0",
    "category": "icon",
    "subtype": "business-commerce",
    "group": "marketing",
    "slug": "conversion",
    "renderer": "conversion",
    "order": 28,
    "intents": [
      "show_conversion",
      "communicate_action_completion"
    ],
    "keywords": [
      "icon",
      "business",
      "commerce",
      "paper",
      "conversion",
      "transform",
      "customer",
      "action",
      "marketing"
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
      "size": {
        "type": "number",
        "minimum": 24,
        "recommended": 96,
        "maximum": 420
      },
      "treatment": {
        "type": "enum",
        "values": [
          "paper-cutout",
          "printed-outline"
        ]
      },
      "state": {
        "type": "enum",
        "values": [
          "inactive",
          "active",
          "completed"
        ]
      },
      "label": {
        "type": "string",
        "maxCharacters": 56
      },
      "motion": {
        "type": "enum",
        "values": [
          "cut-paper-pop",
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.4
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      }
    },
    "duration": {
      "minimum": 0.45,
      "recommended": 1.2,
      "maximum": 3.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "cut-paper-pop",
      "paper-slide",
      "scale-bounce"
    ],
    "defaultMotion": "cut-paper-pop",
    "states": [
      "inactive",
      "active",
      "completed"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "business.conversion.soft",
      "paper.icon.tap"
    ],
    "themeTokens": [
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
    "accessibilityLabel": "Conversion business and commerce paper icon",
    "description": "A reusable layered paper-style conversion icon for business, commerce, growth, marketing and organizational storytelling.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "show_conversion",
        "communicate_action_completion"
      ],
      "avoidWhen": [],
      "semanticRole": "marketing",
      "polarity": "neutral-or-positive"
    }
  },
  {
    "id": "icon.business.funnel.paper-01",
    "name": "Funnel",
    "version": "1.6.0",
    "category": "icon",
    "subtype": "business-commerce",
    "group": "marketing",
    "slug": "funnel",
    "renderer": "funnel",
    "order": 29,
    "intents": [
      "show_funnel",
      "explain_conversion_path"
    ],
    "keywords": [
      "icon",
      "business",
      "commerce",
      "paper",
      "funnel",
      "pipeline",
      "conversion",
      "filter",
      "marketing"
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
      "size": {
        "type": "number",
        "minimum": 24,
        "recommended": 96,
        "maximum": 420
      },
      "treatment": {
        "type": "enum",
        "values": [
          "paper-cutout",
          "printed-outline"
        ]
      },
      "state": {
        "type": "enum",
        "values": [
          "inactive",
          "active"
        ]
      },
      "label": {
        "type": "string",
        "maxCharacters": 56
      },
      "motion": {
        "type": "enum",
        "values": [
          "cut-paper-pop",
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.4
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      }
    },
    "duration": {
      "minimum": 0.45,
      "recommended": 1.2,
      "maximum": 3.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "cut-paper-pop",
      "paper-slide",
      "scale-bounce"
    ],
    "defaultMotion": "cut-paper-pop",
    "states": [
      "inactive",
      "active"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "business.funnel.soft",
      "paper.icon.tap"
    ],
    "themeTokens": [
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
    "accessibilityLabel": "Funnel business and commerce paper icon",
    "description": "A reusable layered paper-style funnel icon for business, commerce, growth, marketing and organizational storytelling.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "show_funnel",
        "explain_conversion_path"
      ],
      "avoidWhen": [],
      "semanticRole": "marketing",
      "polarity": "neutral-or-positive"
    }
  },
  {
    "id": "icon.business.leads.paper-01",
    "name": "Leads",
    "version": "1.6.0",
    "category": "icon",
    "subtype": "business-commerce",
    "group": "marketing",
    "slug": "leads",
    "renderer": "leads",
    "order": 30,
    "intents": [
      "show_leads",
      "represent_prospects"
    ],
    "keywords": [
      "icon",
      "business",
      "commerce",
      "paper",
      "leads",
      "prospects",
      "contacts",
      "pipeline",
      "sales"
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
      "size": {
        "type": "number",
        "minimum": 24,
        "recommended": 96,
        "maximum": 420
      },
      "treatment": {
        "type": "enum",
        "values": [
          "paper-cutout",
          "printed-outline"
        ]
      },
      "state": {
        "type": "enum",
        "values": [
          "inactive",
          "active",
          "completed"
        ]
      },
      "label": {
        "type": "string",
        "maxCharacters": 56
      },
      "motion": {
        "type": "enum",
        "values": [
          "stamp-impact",
          "cut-paper-pop",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.4
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      }
    },
    "duration": {
      "minimum": 0.45,
      "recommended": 1.2,
      "maximum": 3.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "stamp-impact",
      "cut-paper-pop",
      "paper-slide"
    ],
    "defaultMotion": "stamp-impact",
    "states": [
      "inactive",
      "active",
      "completed"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "business.leads.soft",
      "paper.icon.tap"
    ],
    "themeTokens": [
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
    "accessibilityLabel": "Leads business and commerce paper icon",
    "description": "A reusable layered paper-style leads icon for business, commerce, growth, marketing and organizational storytelling.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "show_leads",
        "represent_prospects"
      ],
      "avoidWhen": [],
      "semanticRole": "marketing",
      "polarity": "neutral-or-positive"
    }
  },
  {
    "id": "icon.business.sales.paper-01",
    "name": "Sales",
    "version": "1.6.0",
    "category": "icon",
    "subtype": "business-commerce",
    "group": "metrics",
    "slug": "sales",
    "renderer": "sales",
    "order": 31,
    "intents": [
      "show_sales",
      "communicate_sales_performance"
    ],
    "keywords": [
      "icon",
      "business",
      "commerce",
      "paper",
      "sales",
      "revenue",
      "bars",
      "money",
      "performance"
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
      "size": {
        "type": "number",
        "minimum": 24,
        "recommended": 96,
        "maximum": 420
      },
      "treatment": {
        "type": "enum",
        "values": [
          "paper-cutout",
          "printed-outline"
        ]
      },
      "state": {
        "type": "enum",
        "values": [
          "inactive",
          "active",
          "completed"
        ]
      },
      "label": {
        "type": "string",
        "maxCharacters": 56
      },
      "motion": {
        "type": "enum",
        "values": [
          "cut-paper-pop",
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.4
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      }
    },
    "duration": {
      "minimum": 0.45,
      "recommended": 1.2,
      "maximum": 3.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "cut-paper-pop",
      "paper-slide",
      "scale-bounce"
    ],
    "defaultMotion": "cut-paper-pop",
    "states": [
      "inactive",
      "active",
      "completed"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "business.sales.soft",
      "paper.icon.tap"
    ],
    "themeTokens": [
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
    "accessibilityLabel": "Sales business and commerce paper icon",
    "description": "A reusable layered paper-style sales icon for business, commerce, growth, marketing and organizational storytelling.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "show_sales",
        "communicate_sales_performance"
      ],
      "avoidWhen": [],
      "semanticRole": "metrics",
      "polarity": "neutral-or-positive"
    }
  },
  {
    "id": "icon.business.performance.paper-01",
    "name": "Performance",
    "version": "1.6.0",
    "category": "icon",
    "subtype": "business-commerce",
    "group": "metrics",
    "slug": "performance",
    "renderer": "performance",
    "order": 32,
    "intents": [
      "show_performance",
      "communicate_score"
    ],
    "keywords": [
      "icon",
      "business",
      "commerce",
      "paper",
      "performance",
      "gauge",
      "score",
      "speed",
      "metrics"
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
      "size": {
        "type": "number",
        "minimum": 24,
        "recommended": 96,
        "maximum": 420
      },
      "treatment": {
        "type": "enum",
        "values": [
          "paper-cutout",
          "printed-outline"
        ]
      },
      "state": {
        "type": "enum",
        "values": [
          "inactive",
          "active",
          "completed"
        ]
      },
      "label": {
        "type": "string",
        "maxCharacters": 56
      },
      "motion": {
        "type": "enum",
        "values": [
          "cut-paper-pop",
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.4
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      }
    },
    "duration": {
      "minimum": 0.45,
      "recommended": 1.2,
      "maximum": 3.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "cut-paper-pop",
      "paper-slide",
      "scale-bounce"
    ],
    "defaultMotion": "cut-paper-pop",
    "states": [
      "inactive",
      "active",
      "completed"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "business.performance.soft",
      "paper.icon.tap"
    ],
    "themeTokens": [
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
    "accessibilityLabel": "Performance business and commerce paper icon",
    "description": "A reusable layered paper-style performance icon for business, commerce, growth, marketing and organizational storytelling.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "show_performance",
        "communicate_score"
      ],
      "avoidWhen": [],
      "semanticRole": "metrics",
      "polarity": "neutral-or-positive"
    }
  },
  {
    "id": "icon.business.globe.paper-01",
    "name": "Globe",
    "version": "1.6.0",
    "category": "icon",
    "subtype": "business-commerce",
    "group": "organization",
    "slug": "globe",
    "renderer": "globe",
    "order": 33,
    "intents": [
      "show_global_market",
      "represent_world"
    ],
    "keywords": [
      "icon",
      "business",
      "commerce",
      "paper",
      "globe",
      "world",
      "global",
      "international",
      "market"
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
      "size": {
        "type": "number",
        "minimum": 24,
        "recommended": 96,
        "maximum": 420
      },
      "treatment": {
        "type": "enum",
        "values": [
          "paper-cutout",
          "printed-outline"
        ]
      },
      "state": {
        "type": "enum",
        "values": [
          "inactive",
          "active"
        ]
      },
      "label": {
        "type": "string",
        "maxCharacters": 56
      },
      "motion": {
        "type": "enum",
        "values": [
          "drop-and-settle",
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.4
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      }
    },
    "duration": {
      "minimum": 0.45,
      "recommended": 1.2,
      "maximum": 3.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "drop-and-settle",
      "paper-slide",
      "scale-bounce"
    ],
    "defaultMotion": "drop-and-settle",
    "states": [
      "inactive",
      "active"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "business.globe.soft",
      "paper.icon.tap"
    ],
    "themeTokens": [
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
    "accessibilityLabel": "Globe business and commerce paper icon",
    "description": "A reusable layered paper-style globe icon for business, commerce, growth, marketing and organizational storytelling.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "show_global_market",
        "represent_world"
      ],
      "avoidWhen": [],
      "semanticRole": "organization",
      "polarity": "neutral-or-positive"
    }
  },
  {
    "id": "icon.business.market.paper-01",
    "name": "Market",
    "version": "1.6.0",
    "category": "icon",
    "subtype": "business-commerce",
    "group": "commerce",
    "slug": "market",
    "renderer": "market",
    "order": 34,
    "intents": [
      "show_market",
      "represent_marketplace"
    ],
    "keywords": [
      "icon",
      "business",
      "commerce",
      "paper",
      "market",
      "store",
      "chart",
      "economy",
      "commerce"
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
      "size": {
        "type": "number",
        "minimum": 24,
        "recommended": 96,
        "maximum": 420
      },
      "treatment": {
        "type": "enum",
        "values": [
          "paper-cutout",
          "printed-outline"
        ]
      },
      "state": {
        "type": "enum",
        "values": [
          "inactive",
          "active"
        ]
      },
      "label": {
        "type": "string",
        "maxCharacters": 56
      },
      "motion": {
        "type": "enum",
        "values": [
          "cut-paper-pop",
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.4
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      }
    },
    "duration": {
      "minimum": 0.45,
      "recommended": 1.2,
      "maximum": 3.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "cut-paper-pop",
      "paper-slide",
      "scale-bounce"
    ],
    "defaultMotion": "cut-paper-pop",
    "states": [
      "inactive",
      "active"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "business.market.soft",
      "paper.icon.tap"
    ],
    "themeTokens": [
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
    "accessibilityLabel": "Market business and commerce paper icon",
    "description": "A reusable layered paper-style market icon for business, commerce, growth, marketing and organizational storytelling.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "show_market",
        "represent_marketplace"
      ],
      "avoidWhen": [],
      "semanticRole": "commerce",
      "polarity": "neutral-or-positive"
    }
  },
  {
    "id": "icon.business.partnership.paper-01",
    "name": "Partnership",
    "version": "1.6.0",
    "category": "icon",
    "subtype": "business-commerce",
    "group": "organization",
    "slug": "partnership",
    "renderer": "partnership",
    "order": 35,
    "intents": [
      "show_partnership",
      "represent_collaboration"
    ],
    "keywords": [
      "icon",
      "business",
      "commerce",
      "paper",
      "partnership",
      "handshake",
      "collaboration",
      "deal",
      "business"
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
      "size": {
        "type": "number",
        "minimum": 24,
        "recommended": 96,
        "maximum": 420
      },
      "treatment": {
        "type": "enum",
        "values": [
          "paper-cutout",
          "printed-outline"
        ]
      },
      "state": {
        "type": "enum",
        "values": [
          "inactive",
          "active",
          "completed"
        ]
      },
      "label": {
        "type": "string",
        "maxCharacters": 56
      },
      "motion": {
        "type": "enum",
        "values": [
          "stamp-impact",
          "cut-paper-pop",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.4
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      }
    },
    "duration": {
      "minimum": 0.45,
      "recommended": 1.2,
      "maximum": 3.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "stamp-impact",
      "cut-paper-pop",
      "paper-slide"
    ],
    "defaultMotion": "stamp-impact",
    "states": [
      "inactive",
      "active",
      "completed"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "business.partnership.soft",
      "paper.icon.tap"
    ],
    "themeTokens": [
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
    "accessibilityLabel": "Partnership business and commerce paper icon",
    "description": "A reusable layered paper-style partnership icon for business, commerce, growth, marketing and organizational storytelling.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "show_partnership",
        "represent_collaboration"
      ],
      "avoidWhen": [],
      "semanticRole": "organization",
      "polarity": "neutral-or-positive"
    }
  },
  {
    "id": "icon.business.support.paper-01",
    "name": "Support",
    "version": "1.6.0",
    "category": "icon",
    "subtype": "business-commerce",
    "group": "organization",
    "slug": "support",
    "renderer": "support",
    "order": 36,
    "intents": [
      "show_support",
      "represent_customer_service"
    ],
    "keywords": [
      "icon",
      "business",
      "commerce",
      "paper",
      "support",
      "headset",
      "help",
      "service",
      "customer"
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
      "size": {
        "type": "number",
        "minimum": 24,
        "recommended": 96,
        "maximum": 420
      },
      "treatment": {
        "type": "enum",
        "values": [
          "paper-cutout",
          "printed-outline"
        ]
      },
      "state": {
        "type": "enum",
        "values": [
          "inactive",
          "active",
          "completed"
        ]
      },
      "label": {
        "type": "string",
        "maxCharacters": 56
      },
      "motion": {
        "type": "enum",
        "values": [
          "drop-and-settle",
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.4
      },
      "motionEnergy": {
        "type": "enum",
        "values": [
          "low",
          "medium",
          "high"
        ]
      }
    },
    "duration": {
      "minimum": 0.45,
      "recommended": 1.2,
      "maximum": 3.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "drop-and-settle",
      "paper-slide",
      "scale-bounce"
    ],
    "defaultMotion": "drop-and-settle",
    "states": [
      "inactive",
      "active",
      "completed"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "business.support.soft",
      "paper.icon.tap"
    ],
    "themeTokens": [
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
    "accessibilityLabel": "Support business and commerce paper icon",
    "description": "A reusable layered paper-style support icon for business, commerce, growth, marketing and organizational storytelling.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "show_support",
        "represent_customer_service"
      ],
      "avoidWhen": [],
      "semanticRole": "organization",
      "polarity": "neutral-or-positive"
    }
  }
];
