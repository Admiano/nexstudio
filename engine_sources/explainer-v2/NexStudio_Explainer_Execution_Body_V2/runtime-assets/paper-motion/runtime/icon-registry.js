window.NEX_ICONS = [
  {
    "id": "icon.universal.add.paper-01",
    "name": "Add",
    "version": "1.3.0",
    "category": "icon",
    "subtype": "universal",
    "slug": "add",
    "renderer": "add",
    "order": 1,
    "intents": [
      "create_item",
      "increase_value"
    ],
    "keywords": [
      "icon",
      "universal",
      "paper",
      "add",
      "plus",
      "new",
      "create"
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
        "maxCharacters": 48
      },
      "motion": {
        "type": "enum",
        "values": [
          "cut-paper-pop",
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.2,
        "maximum": 3
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
      "recommended": 1.05,
      "maximum": 3
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "cut-paper-pop",
      "scale-bounce",
      "paper-slide"
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
      "ui.add.soft",
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
    "accessibilityLabel": "Add universal paper icon",
    "description": "A reusable layered paper-style add icon for creator and agent interfaces.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "create_item",
        "increase_value"
      ],
      "avoidWhen": [],
      "semanticRole": "action"
    }
  },
  {
    "id": "icon.universal.remove.paper-01",
    "name": "Remove",
    "version": "1.3.0",
    "category": "icon",
    "subtype": "universal",
    "slug": "remove",
    "renderer": "remove",
    "order": 2,
    "intents": [
      "remove_item",
      "decrease_value"
    ],
    "keywords": [
      "icon",
      "universal",
      "paper",
      "remove",
      "minus",
      "subtract",
      "remove"
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
        "maxCharacters": 48
      },
      "motion": {
        "type": "enum",
        "values": [
          "cut-paper-pop",
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.2,
        "maximum": 3
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
      "recommended": 1.05,
      "maximum": 3
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "cut-paper-pop",
      "scale-bounce",
      "paper-slide"
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
      "ui.remove.soft",
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
    "accessibilityLabel": "Remove universal paper icon",
    "description": "A reusable layered paper-style remove icon for creator and agent interfaces.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "remove_item",
        "decrease_value"
      ],
      "avoidWhen": [],
      "semanticRole": "action"
    }
  },
  {
    "id": "icon.universal.search.paper-01",
    "name": "Search",
    "version": "1.3.0",
    "category": "icon",
    "subtype": "universal",
    "slug": "search",
    "renderer": "search",
    "order": 3,
    "intents": [
      "search_content",
      "find_item"
    ],
    "keywords": [
      "icon",
      "universal",
      "paper",
      "search",
      "magnify",
      "find",
      "query"
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
        "maxCharacters": 48
      },
      "motion": {
        "type": "enum",
        "values": [
          "cut-paper-pop",
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.2,
        "maximum": 3
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
      "recommended": 1.35,
      "maximum": 3
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "cut-paper-pop",
      "scale-bounce",
      "paper-slide"
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
      "ui.search.soft",
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
    "accessibilityLabel": "Search universal paper icon",
    "description": "A reusable layered paper-style search icon for creator and agent interfaces.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "search_content",
        "find_item"
      ],
      "avoidWhen": [],
      "semanticRole": "action"
    }
  },
  {
    "id": "icon.universal.edit.paper-01",
    "name": "Edit",
    "version": "1.3.0",
    "category": "icon",
    "subtype": "universal",
    "slug": "edit",
    "renderer": "edit",
    "order": 4,
    "intents": [
      "edit_content",
      "modify_item"
    ],
    "keywords": [
      "icon",
      "universal",
      "paper",
      "edit",
      "pencil",
      "write",
      "modify"
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
        "maxCharacters": 48
      },
      "motion": {
        "type": "enum",
        "values": [
          "cut-paper-pop",
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.2,
        "maximum": 3
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
      "recommended": 1.05,
      "maximum": 3
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "cut-paper-pop",
      "scale-bounce",
      "paper-slide"
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
      "ui.edit.soft",
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
    "accessibilityLabel": "Edit universal paper icon",
    "description": "A reusable layered paper-style edit icon for creator and agent interfaces.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "edit_content",
        "modify_item"
      ],
      "avoidWhen": [],
      "semanticRole": "action"
    }
  },
  {
    "id": "icon.universal.delete.paper-01",
    "name": "Delete",
    "version": "1.3.0",
    "category": "icon",
    "subtype": "universal",
    "slug": "delete",
    "renderer": "delete",
    "order": 5,
    "intents": [
      "delete_item",
      "discard_content"
    ],
    "keywords": [
      "icon",
      "universal",
      "paper",
      "delete",
      "trash",
      "bin",
      "remove"
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
        "maxCharacters": 48
      },
      "motion": {
        "type": "enum",
        "values": [
          "cut-paper-pop",
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.2,
        "maximum": 3
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
      "recommended": 1.05,
      "maximum": 3
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "cut-paper-pop",
      "scale-bounce",
      "paper-slide"
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
      "ui.delete.soft",
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
    "accessibilityLabel": "Delete universal paper icon",
    "description": "A reusable layered paper-style delete icon for creator and agent interfaces.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "delete_item",
        "discard_content"
      ],
      "avoidWhen": [],
      "semanticRole": "action"
    }
  },
  {
    "id": "icon.universal.save.paper-01",
    "name": "Save",
    "version": "1.3.0",
    "category": "icon",
    "subtype": "universal",
    "slug": "save",
    "renderer": "save",
    "order": 6,
    "intents": [
      "save_content",
      "persist_changes"
    ],
    "keywords": [
      "icon",
      "universal",
      "paper",
      "save",
      "disk",
      "store",
      "save"
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
        "maxCharacters": 48
      },
      "motion": {
        "type": "enum",
        "values": [
          "cut-paper-pop",
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.2,
        "maximum": 3
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
      "recommended": 1.35,
      "maximum": 3
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "cut-paper-pop",
      "scale-bounce",
      "paper-slide"
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
      "ui.save.soft",
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
    "accessibilityLabel": "Save universal paper icon",
    "description": "A reusable layered paper-style save icon for creator and agent interfaces.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "save_content",
        "persist_changes"
      ],
      "avoidWhen": [],
      "semanticRole": "action"
    }
  },
  {
    "id": "icon.universal.copy.paper-01",
    "name": "Copy",
    "version": "1.3.0",
    "category": "icon",
    "subtype": "universal",
    "slug": "copy",
    "renderer": "copy",
    "order": 7,
    "intents": [
      "copy_content",
      "duplicate_item"
    ],
    "keywords": [
      "icon",
      "universal",
      "paper",
      "copy",
      "duplicate",
      "clipboard",
      "copy"
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
        "maxCharacters": 48
      },
      "motion": {
        "type": "enum",
        "values": [
          "cut-paper-pop",
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.2,
        "maximum": 3
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
      "recommended": 1.05,
      "maximum": 3
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "cut-paper-pop",
      "scale-bounce",
      "paper-slide"
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
      "ui.copy.soft",
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
    "accessibilityLabel": "Copy universal paper icon",
    "description": "A reusable layered paper-style copy icon for creator and agent interfaces.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "copy_content",
        "duplicate_item"
      ],
      "avoidWhen": [],
      "semanticRole": "action"
    }
  },
  {
    "id": "icon.universal.share.paper-01",
    "name": "Share",
    "version": "1.3.0",
    "category": "icon",
    "subtype": "universal",
    "slug": "share",
    "renderer": "share",
    "order": 8,
    "intents": [
      "share_content",
      "distribute_item"
    ],
    "keywords": [
      "icon",
      "universal",
      "paper",
      "share",
      "nodes",
      "send",
      "network"
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
        "maxCharacters": 48
      },
      "motion": {
        "type": "enum",
        "values": [
          "paper-slide",
          "cut-paper-pop",
          "drop-and-settle"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.2,
        "maximum": 3
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
      "recommended": 1.35,
      "maximum": 3
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "drop-and-settle"
    ],
    "defaultMotion": "paper-slide",
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
      "ui.share.soft",
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
    "accessibilityLabel": "Share universal paper icon",
    "description": "A reusable layered paper-style share icon for creator and agent interfaces.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "share_content",
        "distribute_item"
      ],
      "avoidWhen": [],
      "semanticRole": "action"
    }
  },
  {
    "id": "icon.universal.send.paper-01",
    "name": "Send",
    "version": "1.3.0",
    "category": "icon",
    "subtype": "universal",
    "slug": "send",
    "renderer": "send",
    "order": 9,
    "intents": [
      "send_message",
      "submit_content"
    ],
    "keywords": [
      "icon",
      "universal",
      "paper",
      "send",
      "plane",
      "message",
      "submit"
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
        "maxCharacters": 48
      },
      "motion": {
        "type": "enum",
        "values": [
          "paper-slide",
          "cut-paper-pop",
          "drop-and-settle"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.2,
        "maximum": 3
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
      "recommended": 1.05,
      "maximum": 3
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "drop-and-settle"
    ],
    "defaultMotion": "paper-slide",
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
      "ui.send.soft",
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
    "accessibilityLabel": "Send universal paper icon",
    "description": "A reusable layered paper-style send icon for creator and agent interfaces.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "send_message",
        "submit_content"
      ],
      "avoidWhen": [],
      "semanticRole": "action"
    }
  },
  {
    "id": "icon.universal.download.paper-01",
    "name": "Download",
    "version": "1.3.0",
    "category": "icon",
    "subtype": "universal",
    "slug": "download",
    "renderer": "download",
    "order": 10,
    "intents": [
      "download_file",
      "receive_content"
    ],
    "keywords": [
      "icon",
      "universal",
      "paper",
      "download",
      "arrow",
      "tray",
      "receive"
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
        "maxCharacters": 48
      },
      "motion": {
        "type": "enum",
        "values": [
          "paper-slide",
          "cut-paper-pop",
          "drop-and-settle"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.2,
        "maximum": 3
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
      "recommended": 1.35,
      "maximum": 3
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "drop-and-settle"
    ],
    "defaultMotion": "paper-slide",
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
      "ui.download.soft",
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
    "accessibilityLabel": "Download universal paper icon",
    "description": "A reusable layered paper-style download icon for creator and agent interfaces.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "download_file",
        "receive_content"
      ],
      "avoidWhen": [],
      "semanticRole": "action"
    }
  },
  {
    "id": "icon.universal.upload.paper-01",
    "name": "Upload",
    "version": "1.3.0",
    "category": "icon",
    "subtype": "universal",
    "slug": "upload",
    "renderer": "upload",
    "order": 11,
    "intents": [
      "upload_file",
      "publish_asset"
    ],
    "keywords": [
      "icon",
      "universal",
      "paper",
      "upload",
      "arrow",
      "tray",
      "publish"
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
        "maxCharacters": 48
      },
      "motion": {
        "type": "enum",
        "values": [
          "paper-slide",
          "cut-paper-pop",
          "drop-and-settle"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.2,
        "maximum": 3
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
      "recommended": 1.35,
      "maximum": 3
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "drop-and-settle"
    ],
    "defaultMotion": "paper-slide",
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
      "ui.upload.soft",
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
    "accessibilityLabel": "Upload universal paper icon",
    "description": "A reusable layered paper-style upload icon for creator and agent interfaces.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "upload_file",
        "publish_asset"
      ],
      "avoidWhen": [],
      "semanticRole": "action"
    }
  },
  {
    "id": "icon.universal.refresh.paper-01",
    "name": "Refresh",
    "version": "1.3.0",
    "category": "icon",
    "subtype": "universal",
    "slug": "refresh",
    "renderer": "refresh",
    "order": 12,
    "intents": [
      "refresh_content",
      "retry_action"
    ],
    "keywords": [
      "icon",
      "universal",
      "paper",
      "refresh",
      "reload",
      "sync",
      "rotate"
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
        "maxCharacters": 48
      },
      "motion": {
        "type": "enum",
        "values": [
          "paper-slide",
          "cut-paper-pop",
          "drop-and-settle"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.2,
        "maximum": 3
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
      "recommended": 1.35,
      "maximum": 3
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "drop-and-settle"
    ],
    "defaultMotion": "paper-slide",
    "states": [
      "inactive",
      "active"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "ui.refresh.soft",
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
    "accessibilityLabel": "Refresh universal paper icon",
    "description": "A reusable layered paper-style refresh icon for creator and agent interfaces.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "refresh_content",
        "retry_action"
      ],
      "avoidWhen": [],
      "semanticRole": "action"
    }
  },
  {
    "id": "icon.universal.undo.paper-01",
    "name": "Undo",
    "version": "1.3.0",
    "category": "icon",
    "subtype": "universal",
    "slug": "undo",
    "renderer": "undo",
    "order": 13,
    "intents": [
      "undo_action",
      "revert_change"
    ],
    "keywords": [
      "icon",
      "universal",
      "paper",
      "undo",
      "reverse",
      "back",
      "history"
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
        "maxCharacters": 48
      },
      "motion": {
        "type": "enum",
        "values": [
          "paper-slide",
          "cut-paper-pop",
          "drop-and-settle"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.2,
        "maximum": 3
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
      "recommended": 1.05,
      "maximum": 3
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "drop-and-settle"
    ],
    "defaultMotion": "paper-slide",
    "states": [
      "inactive",
      "active"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "ui.undo.soft",
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
    "accessibilityLabel": "Undo universal paper icon",
    "description": "A reusable layered paper-style undo icon for creator and agent interfaces.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "undo_action",
        "revert_change"
      ],
      "avoidWhen": [],
      "semanticRole": "action"
    }
  },
  {
    "id": "icon.universal.redo.paper-01",
    "name": "Redo",
    "version": "1.3.0",
    "category": "icon",
    "subtype": "universal",
    "slug": "redo",
    "renderer": "redo",
    "order": 14,
    "intents": [
      "redo_action",
      "restore_change"
    ],
    "keywords": [
      "icon",
      "universal",
      "paper",
      "redo",
      "forward",
      "repeat",
      "history"
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
        "maxCharacters": 48
      },
      "motion": {
        "type": "enum",
        "values": [
          "paper-slide",
          "cut-paper-pop",
          "drop-and-settle"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.2,
        "maximum": 3
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
      "recommended": 1.05,
      "maximum": 3
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "drop-and-settle"
    ],
    "defaultMotion": "paper-slide",
    "states": [
      "inactive",
      "active"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "ui.redo.soft",
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
    "accessibilityLabel": "Redo universal paper icon",
    "description": "A reusable layered paper-style redo icon for creator and agent interfaces.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "redo_action",
        "restore_change"
      ],
      "avoidWhen": [],
      "semanticRole": "action"
    }
  },
  {
    "id": "icon.universal.settings.paper-01",
    "name": "Settings",
    "version": "1.3.0",
    "category": "icon",
    "subtype": "universal",
    "slug": "settings",
    "renderer": "settings",
    "order": 15,
    "intents": [
      "open_settings",
      "configure_system"
    ],
    "keywords": [
      "icon",
      "universal",
      "paper",
      "settings",
      "gear",
      "preferences",
      "configure"
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
        "maxCharacters": 48
      },
      "motion": {
        "type": "enum",
        "values": [
          "cut-paper-pop",
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.2,
        "maximum": 3
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
      "recommended": 1.05,
      "maximum": 3
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "cut-paper-pop",
      "scale-bounce",
      "paper-slide"
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
      "ui.settings.soft",
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
    "accessibilityLabel": "Settings universal paper icon",
    "description": "A reusable layered paper-style settings icon for creator and agent interfaces.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "open_settings",
        "configure_system"
      ],
      "avoidWhen": [],
      "semanticRole": "action"
    }
  },
  {
    "id": "icon.universal.lock.paper-01",
    "name": "Lock",
    "version": "1.3.0",
    "category": "icon",
    "subtype": "universal",
    "slug": "lock",
    "renderer": "lock",
    "order": 16,
    "intents": [
      "lock_content",
      "secure_item"
    ],
    "keywords": [
      "icon",
      "universal",
      "paper",
      "lock",
      "security",
      "private",
      "closed"
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
        "maxCharacters": 48
      },
      "motion": {
        "type": "enum",
        "values": [
          "stamp-impact",
          "scale-bounce",
          "cut-paper-pop"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.2,
        "maximum": 3
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
      "recommended": 1.35,
      "maximum": 3
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "stamp-impact",
      "scale-bounce",
      "cut-paper-pop"
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
      "ui.lock.soft",
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
    "accessibilityLabel": "Lock universal paper icon",
    "description": "A reusable layered paper-style lock icon for creator and agent interfaces.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "lock_content",
        "secure_item"
      ],
      "avoidWhen": [],
      "semanticRole": "action"
    }
  },
  {
    "id": "icon.universal.unlock.paper-01",
    "name": "Unlock",
    "version": "1.3.0",
    "category": "icon",
    "subtype": "universal",
    "slug": "unlock",
    "renderer": "unlock",
    "order": 17,
    "intents": [
      "unlock_content",
      "open_access"
    ],
    "keywords": [
      "icon",
      "universal",
      "paper",
      "unlock",
      "security",
      "open",
      "access"
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
        "maxCharacters": 48
      },
      "motion": {
        "type": "enum",
        "values": [
          "stamp-impact",
          "scale-bounce",
          "cut-paper-pop"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.2,
        "maximum": 3
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
      "recommended": 1.35,
      "maximum": 3
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "stamp-impact",
      "scale-bounce",
      "cut-paper-pop"
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
      "ui.unlock.soft",
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
    "accessibilityLabel": "Unlock universal paper icon",
    "description": "A reusable layered paper-style unlock icon for creator and agent interfaces.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "unlock_content",
        "open_access"
      ],
      "avoidWhen": [],
      "semanticRole": "action"
    }
  },
  {
    "id": "icon.universal.check.paper-01",
    "name": "Check",
    "version": "1.3.0",
    "category": "icon",
    "subtype": "universal",
    "slug": "check",
    "renderer": "check",
    "order": 18,
    "intents": [
      "confirm_action",
      "mark_complete"
    ],
    "keywords": [
      "icon",
      "universal",
      "paper",
      "check",
      "tick",
      "success",
      "done"
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
        "maxCharacters": 48
      },
      "motion": {
        "type": "enum",
        "values": [
          "stamp-impact",
          "scale-bounce",
          "cut-paper-pop"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.2,
        "maximum": 3
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
      "recommended": 1.35,
      "maximum": 3
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "stamp-impact",
      "scale-bounce",
      "cut-paper-pop"
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
      "ui.check.soft",
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
    "accessibilityLabel": "Check universal paper icon",
    "description": "A reusable layered paper-style check icon for creator and agent interfaces.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "confirm_action",
        "mark_complete"
      ],
      "avoidWhen": [],
      "semanticRole": "action"
    }
  },
  {
    "id": "icon.universal.close.paper-01",
    "name": "Close",
    "version": "1.3.0",
    "category": "icon",
    "subtype": "universal",
    "slug": "close",
    "renderer": "close",
    "order": 19,
    "intents": [
      "close_panel",
      "cancel_action"
    ],
    "keywords": [
      "icon",
      "universal",
      "paper",
      "close",
      "x",
      "dismiss",
      "cancel"
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
        "maxCharacters": 48
      },
      "motion": {
        "type": "enum",
        "values": [
          "cut-paper-pop",
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.2,
        "maximum": 3
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
      "recommended": 1.05,
      "maximum": 3
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "cut-paper-pop",
      "scale-bounce",
      "paper-slide"
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
      "ui.close.soft",
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
    "accessibilityLabel": "Close universal paper icon",
    "description": "A reusable layered paper-style close icon for creator and agent interfaces.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "close_panel",
        "cancel_action"
      ],
      "avoidWhen": [],
      "semanticRole": "action"
    }
  },
  {
    "id": "icon.universal.warning.paper-01",
    "name": "Warning",
    "version": "1.3.0",
    "category": "icon",
    "subtype": "universal",
    "slug": "warning",
    "renderer": "warning",
    "order": 20,
    "intents": [
      "show_warning",
      "flag_risk"
    ],
    "keywords": [
      "icon",
      "universal",
      "paper",
      "warning",
      "alert",
      "danger",
      "caution"
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
        "maxCharacters": 48
      },
      "motion": {
        "type": "enum",
        "values": [
          "stamp-impact",
          "scale-bounce",
          "cut-paper-pop"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.2,
        "maximum": 3
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
      "recommended": 1.35,
      "maximum": 3
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "stamp-impact",
      "scale-bounce",
      "cut-paper-pop"
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
      "ui.warning.soft",
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
    "accessibilityLabel": "Warning universal paper icon",
    "description": "A reusable layered paper-style warning icon for creator and agent interfaces.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "show_warning",
        "flag_risk"
      ],
      "avoidWhen": [],
      "semanticRole": "status"
    }
  },
  {
    "id": "icon.universal.information.paper-01",
    "name": "Information",
    "version": "1.3.0",
    "category": "icon",
    "subtype": "universal",
    "slug": "information",
    "renderer": "information",
    "order": 21,
    "intents": [
      "show_information",
      "explain_detail"
    ],
    "keywords": [
      "icon",
      "universal",
      "paper",
      "information",
      "info",
      "details",
      "about"
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
        "maxCharacters": 48
      },
      "motion": {
        "type": "enum",
        "values": [
          "stamp-impact",
          "scale-bounce",
          "cut-paper-pop"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.2,
        "maximum": 3
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
      "recommended": 1.05,
      "maximum": 3
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "stamp-impact",
      "scale-bounce",
      "cut-paper-pop"
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
      "ui.information.soft",
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
    "accessibilityLabel": "Information universal paper icon",
    "description": "A reusable layered paper-style information icon for creator and agent interfaces.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "show_information",
        "explain_detail"
      ],
      "avoidWhen": [],
      "semanticRole": "status"
    }
  },
  {
    "id": "icon.universal.help.paper-01",
    "name": "Help",
    "version": "1.3.0",
    "category": "icon",
    "subtype": "universal",
    "slug": "help",
    "renderer": "help",
    "order": 22,
    "intents": [
      "request_help",
      "show_guidance"
    ],
    "keywords": [
      "icon",
      "universal",
      "paper",
      "help",
      "question",
      "support",
      "guide"
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
        "maxCharacters": 48
      },
      "motion": {
        "type": "enum",
        "values": [
          "stamp-impact",
          "scale-bounce",
          "cut-paper-pop"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.2,
        "maximum": 3
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
      "recommended": 1.05,
      "maximum": 3
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "stamp-impact",
      "scale-bounce",
      "cut-paper-pop"
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
      "ui.help.soft",
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
    "accessibilityLabel": "Help universal paper icon",
    "description": "A reusable layered paper-style help icon for creator and agent interfaces.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "request_help",
        "show_guidance"
      ],
      "avoidWhen": [],
      "semanticRole": "status"
    }
  },
  {
    "id": "icon.universal.home.paper-01",
    "name": "Home",
    "version": "1.3.0",
    "category": "icon",
    "subtype": "universal",
    "slug": "home",
    "renderer": "home",
    "order": 23,
    "intents": [
      "go_home",
      "open_dashboard"
    ],
    "keywords": [
      "icon",
      "universal",
      "paper",
      "home",
      "house",
      "dashboard",
      "start"
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
        "maxCharacters": 48
      },
      "motion": {
        "type": "enum",
        "values": [
          "cut-paper-pop",
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.2,
        "maximum": 3
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
      "recommended": 1.05,
      "maximum": 3
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "cut-paper-pop",
      "scale-bounce",
      "paper-slide"
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
      "ui.home.soft",
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
    "accessibilityLabel": "Home universal paper icon",
    "description": "A reusable layered paper-style home icon for creator and agent interfaces.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "go_home",
        "open_dashboard"
      ],
      "avoidWhen": [],
      "semanticRole": "action"
    }
  },
  {
    "id": "icon.universal.menu.paper-01",
    "name": "Menu",
    "version": "1.3.0",
    "category": "icon",
    "subtype": "universal",
    "slug": "menu",
    "renderer": "menu",
    "order": 24,
    "intents": [
      "open_menu",
      "show_navigation"
    ],
    "keywords": [
      "icon",
      "universal",
      "paper",
      "menu",
      "hamburger",
      "navigation",
      "list"
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
        "maxCharacters": 48
      },
      "motion": {
        "type": "enum",
        "values": [
          "cut-paper-pop",
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.2,
        "maximum": 3
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
      "recommended": 1.05,
      "maximum": 3
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "cut-paper-pop",
      "scale-bounce",
      "paper-slide"
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
      "ui.menu.soft",
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
    "accessibilityLabel": "Menu universal paper icon",
    "description": "A reusable layered paper-style menu icon for creator and agent interfaces.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "open_menu",
        "show_navigation"
      ],
      "avoidWhen": [],
      "semanticRole": "action"
    }
  },
  {
    "id": "icon.universal.calendar.paper-01",
    "name": "Calendar",
    "version": "1.3.0",
    "category": "icon",
    "subtype": "universal",
    "slug": "calendar",
    "renderer": "calendar",
    "order": 25,
    "intents": [
      "schedule_event",
      "show_date"
    ],
    "keywords": [
      "icon",
      "universal",
      "paper",
      "calendar",
      "date",
      "schedule",
      "event"
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
        "maxCharacters": 48
      },
      "motion": {
        "type": "enum",
        "values": [
          "cut-paper-pop",
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.2,
        "maximum": 3
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
      "recommended": 1.35,
      "maximum": 3
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "cut-paper-pop",
      "scale-bounce",
      "paper-slide"
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
      "ui.calendar.soft",
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
    "accessibilityLabel": "Calendar universal paper icon",
    "description": "A reusable layered paper-style calendar icon for creator and agent interfaces.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "schedule_event",
        "show_date"
      ],
      "avoidWhen": [],
      "semanticRole": "action"
    }
  },
  {
    "id": "icon.universal.clock.paper-01",
    "name": "Clock",
    "version": "1.3.0",
    "category": "icon",
    "subtype": "universal",
    "slug": "clock",
    "renderer": "clock",
    "order": 26,
    "intents": [
      "show_time",
      "set_duration"
    ],
    "keywords": [
      "icon",
      "universal",
      "paper",
      "clock",
      "time",
      "timer",
      "schedule"
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
        "maxCharacters": 48
      },
      "motion": {
        "type": "enum",
        "values": [
          "cut-paper-pop",
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.2,
        "maximum": 3
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
      "recommended": 1.35,
      "maximum": 3
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "cut-paper-pop",
      "scale-bounce",
      "paper-slide"
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
      "ui.clock.soft",
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
    "accessibilityLabel": "Clock universal paper icon",
    "description": "A reusable layered paper-style clock icon for creator and agent interfaces.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "show_time",
        "set_duration"
      ],
      "avoidWhen": [],
      "semanticRole": "action"
    }
  },
  {
    "id": "icon.universal.location.paper-01",
    "name": "Location",
    "version": "1.3.0",
    "category": "icon",
    "subtype": "universal",
    "slug": "location",
    "renderer": "location",
    "order": 27,
    "intents": [
      "show_location",
      "mark_place"
    ],
    "keywords": [
      "icon",
      "universal",
      "paper",
      "location",
      "pin",
      "map",
      "place"
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
        "maxCharacters": 48
      },
      "motion": {
        "type": "enum",
        "values": [
          "cut-paper-pop",
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.2,
        "maximum": 3
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
      "recommended": 1.05,
      "maximum": 3
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "cut-paper-pop",
      "scale-bounce",
      "paper-slide"
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
      "ui.location.soft",
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
    "accessibilityLabel": "Location universal paper icon",
    "description": "A reusable layered paper-style location icon for creator and agent interfaces.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "show_location",
        "mark_place"
      ],
      "avoidWhen": [],
      "semanticRole": "action"
    }
  },
  {
    "id": "icon.universal.link.paper-01",
    "name": "Link",
    "version": "1.3.0",
    "category": "icon",
    "subtype": "universal",
    "slug": "link",
    "renderer": "link",
    "order": 28,
    "intents": [
      "create_link",
      "connect_items"
    ],
    "keywords": [
      "icon",
      "universal",
      "paper",
      "link",
      "chain",
      "url",
      "connect"
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
        "maxCharacters": 48
      },
      "motion": {
        "type": "enum",
        "values": [
          "cut-paper-pop",
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.2,
        "maximum": 3
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
      "recommended": 1.05,
      "maximum": 3
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "cut-paper-pop",
      "scale-bounce",
      "paper-slide"
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
      "ui.link.soft",
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
    "accessibilityLabel": "Link universal paper icon",
    "description": "A reusable layered paper-style link icon for creator and agent interfaces.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "create_link",
        "connect_items"
      ],
      "avoidWhen": [],
      "semanticRole": "action"
    }
  },
  {
    "id": "icon.universal.attachment.paper-01",
    "name": "Attachment",
    "version": "1.3.0",
    "category": "icon",
    "subtype": "universal",
    "slug": "attachment",
    "renderer": "attachment",
    "order": 29,
    "intents": [
      "attach_file",
      "show_attachment"
    ],
    "keywords": [
      "icon",
      "universal",
      "paper",
      "attachment",
      "paperclip",
      "file",
      "attach"
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
        "maxCharacters": 48
      },
      "motion": {
        "type": "enum",
        "values": [
          "cut-paper-pop",
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.2,
        "maximum": 3
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
      "recommended": 1.05,
      "maximum": 3
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "cut-paper-pop",
      "scale-bounce",
      "paper-slide"
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
      "ui.attachment.soft",
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
    "accessibilityLabel": "Attachment universal paper icon",
    "description": "A reusable layered paper-style attachment icon for creator and agent interfaces.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "attach_file",
        "show_attachment"
      ],
      "avoidWhen": [],
      "semanticRole": "action"
    }
  },
  {
    "id": "icon.universal.filter.paper-01",
    "name": "Filter",
    "version": "1.3.0",
    "category": "icon",
    "subtype": "universal",
    "slug": "filter",
    "renderer": "filter",
    "order": 30,
    "intents": [
      "filter_results",
      "refine_content"
    ],
    "keywords": [
      "icon",
      "universal",
      "paper",
      "filter",
      "funnel",
      "refine",
      "query"
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
        "maxCharacters": 48
      },
      "motion": {
        "type": "enum",
        "values": [
          "cut-paper-pop",
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.2,
        "maximum": 3
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
      "recommended": 1.05,
      "maximum": 3
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "cut-paper-pop",
      "scale-bounce",
      "paper-slide"
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
      "ui.filter.soft",
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
    "accessibilityLabel": "Filter universal paper icon",
    "description": "A reusable layered paper-style filter icon for creator and agent interfaces.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "filter_results",
        "refine_content"
      ],
      "avoidWhen": [],
      "semanticRole": "action"
    }
  },
  {
    "id": "icon.universal.sort.paper-01",
    "name": "Sort",
    "version": "1.3.0",
    "category": "icon",
    "subtype": "universal",
    "slug": "sort",
    "renderer": "sort",
    "order": 31,
    "intents": [
      "sort_items",
      "order_results"
    ],
    "keywords": [
      "icon",
      "universal",
      "paper",
      "sort",
      "order",
      "up",
      "down"
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
        "maxCharacters": 48
      },
      "motion": {
        "type": "enum",
        "values": [
          "cut-paper-pop",
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.2,
        "maximum": 3
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
      "recommended": 1.05,
      "maximum": 3
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "cut-paper-pop",
      "scale-bounce",
      "paper-slide"
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
      "ui.sort.soft",
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
    "accessibilityLabel": "Sort universal paper icon",
    "description": "A reusable layered paper-style sort icon for creator and agent interfaces.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "sort_items",
        "order_results"
      ],
      "avoidWhen": [],
      "semanticRole": "action"
    }
  },
  {
    "id": "icon.universal.expand.paper-01",
    "name": "Expand",
    "version": "1.3.0",
    "category": "icon",
    "subtype": "universal",
    "slug": "expand",
    "renderer": "expand",
    "order": 32,
    "intents": [
      "expand_view",
      "enter_fullscreen"
    ],
    "keywords": [
      "icon",
      "universal",
      "paper",
      "expand",
      "outward",
      "fullscreen",
      "open"
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
        "maxCharacters": 48
      },
      "motion": {
        "type": "enum",
        "values": [
          "paper-slide",
          "cut-paper-pop",
          "drop-and-settle"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.2,
        "maximum": 3
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
      "recommended": 1.05,
      "maximum": 3
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "drop-and-settle"
    ],
    "defaultMotion": "paper-slide",
    "states": [
      "inactive",
      "active"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "ui.expand.soft",
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
    "accessibilityLabel": "Expand universal paper icon",
    "description": "A reusable layered paper-style expand icon for creator and agent interfaces.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "expand_view",
        "enter_fullscreen"
      ],
      "avoidWhen": [],
      "semanticRole": "action"
    }
  },
  {
    "id": "icon.universal.collapse.paper-01",
    "name": "Collapse",
    "version": "1.3.0",
    "category": "icon",
    "subtype": "universal",
    "slug": "collapse",
    "renderer": "collapse",
    "order": 33,
    "intents": [
      "collapse_view",
      "exit_fullscreen"
    ],
    "keywords": [
      "icon",
      "universal",
      "paper",
      "collapse",
      "inward",
      "minimise",
      "close"
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
        "maxCharacters": 48
      },
      "motion": {
        "type": "enum",
        "values": [
          "paper-slide",
          "cut-paper-pop",
          "drop-and-settle"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.2,
        "maximum": 3
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
      "recommended": 1.05,
      "maximum": 3
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "drop-and-settle"
    ],
    "defaultMotion": "paper-slide",
    "states": [
      "inactive",
      "active"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "ui.collapse.soft",
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
    "accessibilityLabel": "Collapse universal paper icon",
    "description": "A reusable layered paper-style collapse icon for creator and agent interfaces.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "collapse_view",
        "exit_fullscreen"
      ],
      "avoidWhen": [],
      "semanticRole": "action"
    }
  },
  {
    "id": "icon.universal.forward.paper-01",
    "name": "Forward",
    "version": "1.3.0",
    "category": "icon",
    "subtype": "universal",
    "slug": "forward",
    "renderer": "forward",
    "order": 34,
    "intents": [
      "go_forward",
      "next_item"
    ],
    "keywords": [
      "icon",
      "universal",
      "paper",
      "forward",
      "next",
      "right",
      "continue"
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
        "maxCharacters": 48
      },
      "motion": {
        "type": "enum",
        "values": [
          "paper-slide",
          "cut-paper-pop",
          "drop-and-settle"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.2,
        "maximum": 3
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
      "recommended": 1.05,
      "maximum": 3
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "drop-and-settle"
    ],
    "defaultMotion": "paper-slide",
    "states": [
      "inactive",
      "active"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "ui.forward.soft",
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
    "accessibilityLabel": "Forward universal paper icon",
    "description": "A reusable layered paper-style forward icon for creator and agent interfaces.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "go_forward",
        "next_item"
      ],
      "avoidWhen": [],
      "semanticRole": "action"
    }
  },
  {
    "id": "icon.universal.back.paper-01",
    "name": "Back",
    "version": "1.3.0",
    "category": "icon",
    "subtype": "universal",
    "slug": "back",
    "renderer": "back",
    "order": 35,
    "intents": [
      "go_back",
      "previous_item"
    ],
    "keywords": [
      "icon",
      "universal",
      "paper",
      "back",
      "previous",
      "left",
      "return"
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
        "maxCharacters": 48
      },
      "motion": {
        "type": "enum",
        "values": [
          "paper-slide",
          "cut-paper-pop",
          "drop-and-settle"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.2,
        "maximum": 3
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
      "recommended": 1.05,
      "maximum": 3
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "paper-slide",
      "cut-paper-pop",
      "drop-and-settle"
    ],
    "defaultMotion": "paper-slide",
    "states": [
      "inactive",
      "active"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "ui.back.soft",
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
    "accessibilityLabel": "Back universal paper icon",
    "description": "A reusable layered paper-style back icon for creator and agent interfaces.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "go_back",
        "previous_item"
      ],
      "avoidWhen": [],
      "semanticRole": "action"
    }
  },
  {
    "id": "icon.universal.play.paper-01",
    "name": "Play",
    "version": "1.3.0",
    "category": "icon",
    "subtype": "universal",
    "slug": "play",
    "renderer": "play",
    "order": 36,
    "intents": [
      "play_media",
      "start_action"
    ],
    "keywords": [
      "icon",
      "universal",
      "paper",
      "play",
      "media",
      "start",
      "triangle"
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
        "maxCharacters": 48
      },
      "motion": {
        "type": "enum",
        "values": [
          "cut-paper-pop",
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.2,
        "maximum": 3
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
      "recommended": 1.35,
      "maximum": 3
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "cut-paper-pop",
      "scale-bounce",
      "paper-slide"
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
      "ui.play.soft",
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
    "accessibilityLabel": "Play universal paper icon",
    "description": "A reusable layered paper-style play icon for creator and agent interfaces.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "play_media",
        "start_action"
      ],
      "avoidWhen": [],
      "semanticRole": "action"
    }
  },
  {
    "id": "icon.universal.pause.paper-01",
    "name": "Pause",
    "version": "1.3.0",
    "category": "icon",
    "subtype": "universal",
    "slug": "pause",
    "renderer": "pause",
    "order": 37,
    "intents": [
      "pause_media",
      "hold_action"
    ],
    "keywords": [
      "icon",
      "universal",
      "paper",
      "pause",
      "media",
      "hold",
      "bars"
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
        "maxCharacters": 48
      },
      "motion": {
        "type": "enum",
        "values": [
          "cut-paper-pop",
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.2,
        "maximum": 3
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
      "recommended": 1.05,
      "maximum": 3
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "cut-paper-pop",
      "scale-bounce",
      "paper-slide"
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
      "ui.pause.soft",
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
    "accessibilityLabel": "Pause universal paper icon",
    "description": "A reusable layered paper-style pause icon for creator and agent interfaces.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "pause_media",
        "hold_action"
      ],
      "avoidWhen": [],
      "semanticRole": "action"
    }
  },
  {
    "id": "icon.universal.stop.paper-01",
    "name": "Stop",
    "version": "1.3.0",
    "category": "icon",
    "subtype": "universal",
    "slug": "stop",
    "renderer": "stop",
    "order": 38,
    "intents": [
      "stop_media",
      "end_action"
    ],
    "keywords": [
      "icon",
      "universal",
      "paper",
      "stop",
      "media",
      "end",
      "square"
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
        "maxCharacters": 48
      },
      "motion": {
        "type": "enum",
        "values": [
          "cut-paper-pop",
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.2,
        "maximum": 3
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
      "recommended": 1.05,
      "maximum": 3
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "cut-paper-pop",
      "scale-bounce",
      "paper-slide"
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
      "ui.stop.soft",
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
    "accessibilityLabel": "Stop universal paper icon",
    "description": "A reusable layered paper-style stop icon for creator and agent interfaces.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "stop_media",
        "end_action"
      ],
      "avoidWhen": [],
      "semanticRole": "action"
    }
  },
  {
    "id": "icon.universal.favourite.paper-01",
    "name": "Favourite",
    "version": "1.3.0",
    "category": "icon",
    "subtype": "universal",
    "slug": "favourite",
    "renderer": "favourite",
    "order": 39,
    "intents": [
      "favourite_item",
      "express_love"
    ],
    "keywords": [
      "icon",
      "universal",
      "paper",
      "favourite",
      "heart",
      "like",
      "love"
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
        "maxCharacters": 48
      },
      "motion": {
        "type": "enum",
        "values": [
          "stamp-impact",
          "scale-bounce",
          "cut-paper-pop"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.2,
        "maximum": 3
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
      "recommended": 1.35,
      "maximum": 3
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "stamp-impact",
      "scale-bounce",
      "cut-paper-pop"
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
      "ui.favourite.soft",
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
    "accessibilityLabel": "Favourite universal paper icon",
    "description": "A reusable layered paper-style favourite icon for creator and agent interfaces.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "favourite_item",
        "express_love"
      ],
      "avoidWhen": [],
      "semanticRole": "action"
    }
  },
  {
    "id": "icon.universal.bookmark.paper-01",
    "name": "Bookmark",
    "version": "1.3.0",
    "category": "icon",
    "subtype": "universal",
    "slug": "bookmark",
    "renderer": "bookmark",
    "order": 40,
    "intents": [
      "bookmark_item",
      "save_for_later"
    ],
    "keywords": [
      "icon",
      "universal",
      "paper",
      "bookmark",
      "ribbon",
      "save",
      "later"
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
        "maxCharacters": 48
      },
      "motion": {
        "type": "enum",
        "values": [
          "stamp-impact",
          "scale-bounce",
          "cut-paper-pop"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.2,
        "maximum": 3
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
      "recommended": 1.35,
      "maximum": 3
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "stamp-impact",
      "scale-bounce",
      "cut-paper-pop"
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
      "ui.bookmark.soft",
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
    "accessibilityLabel": "Bookmark universal paper icon",
    "description": "A reusable layered paper-style bookmark icon for creator and agent interfaces.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "bookmark_item",
        "save_for_later"
      ],
      "avoidWhen": [],
      "semanticRole": "action"
    }
  }
];
