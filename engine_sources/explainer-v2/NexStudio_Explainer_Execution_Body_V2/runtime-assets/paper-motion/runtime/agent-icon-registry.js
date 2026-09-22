window.NEX_AGENT_ICONS = [
  {
    "id": "icon.agent.agent.paper-01",
    "name": "Agent",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "ai-core",
    "slug": "agent",
    "renderer": "agent",
    "order": 1,
    "intents": [
      "represent_ai_agent",
      "show_autonomous_worker"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "agent",
      "ai",
      "assistant",
      "worker",
      "automation"
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
        "recommended": 1.3,
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
      "agent.agent.soft",
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
    "accessibilityLabel": "Agent AI agent and automation paper icon",
    "description": "A reusable layered paper-style agent icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "represent_ai_agent",
        "show_autonomous_worker"
      ],
      "avoidWhen": [],
      "semanticRole": "ai-core"
    }
  },
  {
    "id": "icon.agent.multiple-agents.paper-01",
    "name": "Multiple agents",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "ai-core",
    "slug": "multiple-agents",
    "renderer": "multiple-agents",
    "order": 2,
    "intents": [
      "show_agent_team",
      "orchestrate_agents"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "agents",
      "team",
      "multi-agent",
      "orchestration",
      "swarm"
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
        "recommended": 1.3,
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
      "agent.multiple-agents.soft",
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
    "accessibilityLabel": "Multiple agents AI agent and automation paper icon",
    "description": "A reusable layered paper-style multiple agents icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "show_agent_team",
        "orchestrate_agents"
      ],
      "avoidWhen": [],
      "semanticRole": "ai-core"
    }
  },
  {
    "id": "icon.agent.ai-sparkle.paper-01",
    "name": "AI sparkle",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "ai-core",
    "slug": "ai-sparkle",
    "renderer": "ai-sparkle",
    "order": 3,
    "intents": [
      "indicate_ai",
      "show_generated_result"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "ai",
      "sparkle",
      "magic",
      "generate",
      "intelligence"
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
        "recommended": 1.3,
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
      "agent.ai-sparkle.soft",
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
    "accessibilityLabel": "AI sparkle AI agent and automation paper icon",
    "description": "A reusable layered paper-style ai sparkle icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "indicate_ai",
        "show_generated_result"
      ],
      "avoidWhen": [],
      "semanticRole": "ai-core"
    }
  },
  {
    "id": "icon.agent.brain.paper-01",
    "name": "Brain",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "ai-core",
    "slug": "brain",
    "renderer": "brain",
    "order": 4,
    "intents": [
      "represent_reasoning",
      "show_intelligence"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "brain",
      "intelligence",
      "reasoning",
      "cognition",
      "ai"
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
        "recommended": 1.3,
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
      "agent.brain.soft",
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
    "accessibilityLabel": "Brain AI agent and automation paper icon",
    "description": "A reusable layered paper-style brain icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "represent_reasoning",
        "show_intelligence"
      ],
      "avoidWhen": [],
      "semanticRole": "ai-core"
    }
  },
  {
    "id": "icon.agent.model.paper-01",
    "name": "Model",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "ai-core",
    "slug": "model",
    "renderer": "model",
    "order": 5,
    "intents": [
      "represent_ai_model",
      "select_model"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "model",
      "ai",
      "layers",
      "inference",
      "system"
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
        "recommended": 1.3,
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
      "agent.model.soft",
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
    "accessibilityLabel": "Model AI agent and automation paper icon",
    "description": "A reusable layered paper-style model icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "represent_ai_model",
        "select_model"
      ],
      "avoidWhen": [],
      "semanticRole": "ai-core"
    }
  },
  {
    "id": "icon.agent.prompt.paper-01",
    "name": "Prompt",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "ai-core",
    "slug": "prompt",
    "renderer": "prompt",
    "order": 6,
    "intents": [
      "enter_prompt",
      "show_instruction"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "prompt",
      "instruction",
      "input",
      "command",
      "text"
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
        "recommended": 1.3,
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
      "agent.prompt.soft",
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
    "accessibilityLabel": "Prompt AI agent and automation paper icon",
    "description": "A reusable layered paper-style prompt icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "enter_prompt",
        "show_instruction"
      ],
      "avoidWhen": [],
      "semanticRole": "ai-core"
    }
  },
  {
    "id": "icon.agent.chat.paper-01",
    "name": "Chat",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "ai-core",
    "slug": "chat",
    "renderer": "chat",
    "order": 7,
    "intents": [
      "show_conversation",
      "agent_chat"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "chat",
      "conversation",
      "message",
      "assistant",
      "dialogue"
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
        "recommended": 1.3,
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
      "agent.chat.soft",
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
    "accessibilityLabel": "Chat AI agent and automation paper icon",
    "description": "A reusable layered paper-style chat icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "show_conversation",
        "agent_chat"
      ],
      "avoidWhen": [],
      "semanticRole": "ai-core"
    }
  },
  {
    "id": "icon.agent.reasoning.paper-01",
    "name": "Reasoning",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "ai-core",
    "slug": "reasoning",
    "renderer": "reasoning",
    "order": 8,
    "intents": [
      "show_reasoning_process",
      "connect_ideas"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "reasoning",
      "logic",
      "thought",
      "nodes",
      "analysis"
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
        "recommended": 1.3,
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
      "agent.reasoning.soft",
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
    "accessibilityLabel": "Reasoning AI agent and automation paper icon",
    "description": "A reusable layered paper-style reasoning icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "show_reasoning_process",
        "connect_ideas"
      ],
      "avoidWhen": [],
      "semanticRole": "ai-core"
    }
  },
  {
    "id": "icon.agent.memory.paper-01",
    "name": "Memory",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "ai-core",
    "slug": "memory",
    "renderer": "memory",
    "order": 9,
    "intents": [
      "store_memory",
      "retrieve_context"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "memory",
      "cards",
      "stack",
      "recall",
      "agent"
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
        "recommended": 1.3,
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
      "agent.memory.soft",
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
    "accessibilityLabel": "Memory AI agent and automation paper icon",
    "description": "A reusable layered paper-style memory icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "store_memory",
        "retrieve_context"
      ],
      "avoidWhen": [],
      "semanticRole": "ai-core"
    }
  },
  {
    "id": "icon.agent.context.paper-01",
    "name": "Context",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "ai-core",
    "slug": "context",
    "renderer": "context",
    "order": 10,
    "intents": [
      "expand_context",
      "show_context_window"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "context",
      "window",
      "tokens",
      "expand",
      "information"
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
        "recommended": 1.3,
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
      "agent.context.soft",
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
    "accessibilityLabel": "Context AI agent and automation paper icon",
    "description": "A reusable layered paper-style context icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "expand_context",
        "show_context_window"
      ],
      "avoidWhen": [],
      "semanticRole": "ai-core"
    }
  },
  {
    "id": "icon.agent.knowledge-base.paper-01",
    "name": "Knowledge base",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "ai-core",
    "slug": "knowledge-base",
    "renderer": "knowledge-base",
    "order": 11,
    "intents": [
      "query_knowledge",
      "show_reference_library"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "knowledge",
      "base",
      "library",
      "documents",
      "retrieval"
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
        "recommended": 1.3,
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
      "agent.knowledge-base.soft",
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
    "accessibilityLabel": "Knowledge base AI agent and automation paper icon",
    "description": "A reusable layered paper-style knowledge base icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "query_knowledge",
        "show_reference_library"
      ],
      "avoidWhen": [],
      "semanticRole": "ai-core"
    }
  },
  {
    "id": "icon.agent.website.paper-01",
    "name": "Website",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "resources",
    "slug": "website",
    "renderer": "website",
    "order": 12,
    "intents": [
      "open_website",
      "use_web_source"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "website",
      "browser",
      "web",
      "page",
      "source"
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
          "unfold",
          "paper-slide",
          "cut-paper-pop"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.3,
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
      "unfold",
      "paper-slide",
      "cut-paper-pop"
    ],
    "defaultMotion": "unfold",
    "states": [
      "inactive",
      "active"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "agent.website.soft",
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
    "accessibilityLabel": "Website AI agent and automation paper icon",
    "description": "A reusable layered paper-style website icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "open_website",
        "use_web_source"
      ],
      "avoidWhen": [],
      "semanticRole": "resources"
    }
  },
  {
    "id": "icon.agent.document.paper-01",
    "name": "Document",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "resources",
    "slug": "document",
    "renderer": "document",
    "order": 13,
    "intents": [
      "read_document",
      "show_document"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "document",
      "page",
      "text",
      "source",
      "file"
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
          "unfold",
          "paper-slide",
          "cut-paper-pop"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.3,
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
      "unfold",
      "paper-slide",
      "cut-paper-pop"
    ],
    "defaultMotion": "unfold",
    "states": [
      "inactive",
      "active"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "agent.document.soft",
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
    "accessibilityLabel": "Document AI agent and automation paper icon",
    "description": "A reusable layered paper-style document icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "read_document",
        "show_document"
      ],
      "avoidWhen": [],
      "semanticRole": "resources"
    }
  },
  {
    "id": "icon.agent.file.paper-01",
    "name": "File",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "resources",
    "slug": "file",
    "renderer": "file",
    "order": 14,
    "intents": [
      "use_file",
      "show_file"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "file",
      "asset",
      "document",
      "data",
      "resource"
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
          "unfold",
          "paper-slide",
          "cut-paper-pop"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.3,
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
      "unfold",
      "paper-slide",
      "cut-paper-pop"
    ],
    "defaultMotion": "unfold",
    "states": [
      "inactive",
      "active"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "agent.file.soft",
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
    "accessibilityLabel": "File AI agent and automation paper icon",
    "description": "A reusable layered paper-style file icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "use_file",
        "show_file"
      ],
      "avoidWhen": [],
      "semanticRole": "resources"
    }
  },
  {
    "id": "icon.agent.folder.paper-01",
    "name": "Folder",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "resources",
    "slug": "folder",
    "renderer": "folder",
    "order": 15,
    "intents": [
      "open_folder",
      "organize_files"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "folder",
      "directory",
      "files",
      "organize",
      "resource"
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
          "unfold",
          "paper-slide",
          "cut-paper-pop"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.3,
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
      "unfold",
      "paper-slide",
      "cut-paper-pop"
    ],
    "defaultMotion": "unfold",
    "states": [
      "inactive",
      "active"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "agent.folder.soft",
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
    "accessibilityLabel": "Folder AI agent and automation paper icon",
    "description": "A reusable layered paper-style folder icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "open_folder",
        "organize_files"
      ],
      "avoidWhen": [],
      "semanticRole": "resources"
    }
  },
  {
    "id": "icon.agent.database.paper-01",
    "name": "Database",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "resources",
    "slug": "database",
    "renderer": "database",
    "order": 16,
    "intents": [
      "query_database",
      "populate_data"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "database",
      "data",
      "storage",
      "layers",
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
        "maxCharacters": 56
      },
      "motion": {
        "type": "enum",
        "values": [
          "unfold",
          "paper-slide",
          "cut-paper-pop"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.3,
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
      "unfold",
      "paper-slide",
      "cut-paper-pop"
    ],
    "defaultMotion": "unfold",
    "states": [
      "inactive",
      "active"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "agent.database.soft",
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
    "accessibilityLabel": "Database AI agent and automation paper icon",
    "description": "A reusable layered paper-style database icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "query_database",
        "populate_data"
      ],
      "avoidWhen": [],
      "semanticRole": "resources"
    }
  },
  {
    "id": "icon.agent.api.paper-01",
    "name": "API",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "resources",
    "slug": "api",
    "renderer": "api",
    "order": 17,
    "intents": [
      "call_api",
      "exchange_data"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "api",
      "nodes",
      "request",
      "response",
      "integration"
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
          "unfold",
          "paper-slide",
          "cut-paper-pop"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.3,
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
      "unfold",
      "paper-slide",
      "cut-paper-pop"
    ],
    "defaultMotion": "unfold",
    "states": [
      "inactive",
      "active"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "agent.api.soft",
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
    "accessibilityLabel": "API AI agent and automation paper icon",
    "description": "A reusable layered paper-style api icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "call_api",
        "exchange_data"
      ],
      "avoidWhen": [],
      "semanticRole": "resources"
    }
  },
  {
    "id": "icon.agent.webhook.paper-01",
    "name": "Webhook",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "resources",
    "slug": "webhook",
    "renderer": "webhook",
    "order": 18,
    "intents": [
      "trigger_webhook",
      "send_event"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "webhook",
      "trigger",
      "event",
      "signal",
      "integration"
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
          "unfold",
          "paper-slide",
          "cut-paper-pop"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.3,
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
      "unfold",
      "paper-slide",
      "cut-paper-pop"
    ],
    "defaultMotion": "unfold",
    "states": [
      "inactive",
      "active"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "agent.webhook.soft",
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
    "accessibilityLabel": "Webhook AI agent and automation paper icon",
    "description": "A reusable layered paper-style webhook icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "trigger_webhook",
        "send_event"
      ],
      "avoidWhen": [],
      "semanticRole": "resources"
    }
  },
  {
    "id": "icon.agent.connector.paper-01",
    "name": "Connector",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "resources",
    "slug": "connector",
    "renderer": "connector",
    "order": 19,
    "intents": [
      "connect_service",
      "integrate_tool"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "connector",
      "plug",
      "integration",
      "service",
      "link"
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
          "unfold",
          "paper-slide",
          "cut-paper-pop"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.3,
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
      "unfold",
      "paper-slide",
      "cut-paper-pop"
    ],
    "defaultMotion": "unfold",
    "states": [
      "inactive",
      "active"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "agent.connector.soft",
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
    "accessibilityLabel": "Connector AI agent and automation paper icon",
    "description": "A reusable layered paper-style connector icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "connect_service",
        "integrate_tool"
      ],
      "avoidWhen": [],
      "semanticRole": "resources"
    }
  },
  {
    "id": "icon.agent.tool.paper-01",
    "name": "Tool",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "resources",
    "slug": "tool",
    "renderer": "tool",
    "order": 20,
    "intents": [
      "use_tool",
      "show_capability"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "tool",
      "wrench",
      "capability",
      "action",
      "agent"
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
          "unfold",
          "paper-slide",
          "cut-paper-pop"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.3,
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
      "unfold",
      "paper-slide",
      "cut-paper-pop"
    ],
    "defaultMotion": "unfold",
    "states": [
      "inactive",
      "active"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "agent.tool.soft",
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
    "accessibilityLabel": "Tool AI agent and automation paper icon",
    "description": "A reusable layered paper-style tool icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "use_tool",
        "show_capability"
      ],
      "avoidWhen": [],
      "semanticRole": "resources"
    }
  },
  {
    "id": "icon.agent.code.paper-01",
    "name": "Code",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "resources",
    "slug": "code",
    "renderer": "code",
    "order": 21,
    "intents": [
      "write_code",
      "show_source_code"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "code",
      "brackets",
      "programming",
      "developer",
      "source"
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
          "unfold",
          "paper-slide",
          "cut-paper-pop"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.3,
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
      "unfold",
      "paper-slide",
      "cut-paper-pop"
    ],
    "defaultMotion": "unfold",
    "states": [
      "inactive",
      "active"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "agent.code.soft",
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
    "accessibilityLabel": "Code AI agent and automation paper icon",
    "description": "A reusable layered paper-style code icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "write_code",
        "show_source_code"
      ],
      "avoidWhen": [],
      "semanticRole": "resources"
    }
  },
  {
    "id": "icon.agent.terminal.paper-01",
    "name": "Terminal",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "resources",
    "slug": "terminal",
    "renderer": "terminal",
    "order": 22,
    "intents": [
      "run_command",
      "show_terminal"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "terminal",
      "command",
      "cli",
      "console",
      "developer"
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
          "unfold",
          "paper-slide",
          "cut-paper-pop"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.3,
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
      "unfold",
      "paper-slide",
      "cut-paper-pop"
    ],
    "defaultMotion": "unfold",
    "states": [
      "inactive",
      "active"
    ],
    "treatments": [
      "paper-cutout",
      "printed-outline"
    ],
    "soundTags": [
      "agent.terminal.soft",
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
    "accessibilityLabel": "Terminal AI agent and automation paper icon",
    "description": "A reusable layered paper-style terminal icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "run_command",
        "show_terminal"
      ],
      "avoidWhen": [],
      "semanticRole": "resources"
    }
  },
  {
    "id": "icon.agent.automation.paper-01",
    "name": "Automation",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "automation",
    "slug": "automation",
    "renderer": "automation",
    "order": 23,
    "intents": [
      "run_automation",
      "show_automated_loop"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "automation",
      "loop",
      "gear",
      "workflow",
      "agent"
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
          "paper-slide",
          "drop-and-settle",
          "stamp-impact"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.3,
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
      "paper-slide",
      "drop-and-settle",
      "stamp-impact"
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
      "agent.automation.soft",
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
    "accessibilityLabel": "Automation AI agent and automation paper icon",
    "description": "A reusable layered paper-style automation icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "run_automation",
        "show_automated_loop"
      ],
      "avoidWhen": [],
      "semanticRole": "automation"
    }
  },
  {
    "id": "icon.agent.trigger.paper-01",
    "name": "Trigger",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "automation",
    "slug": "trigger",
    "renderer": "trigger",
    "order": 24,
    "intents": [
      "start_workflow",
      "show_trigger"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "trigger",
      "start",
      "event",
      "lightning",
      "automation"
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
          "paper-slide",
          "drop-and-settle",
          "stamp-impact"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.3,
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
      "paper-slide",
      "drop-and-settle",
      "stamp-impact"
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
      "agent.trigger.soft",
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
    "accessibilityLabel": "Trigger AI agent and automation paper icon",
    "description": "A reusable layered paper-style trigger icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "start_workflow",
        "show_trigger"
      ],
      "avoidWhen": [],
      "semanticRole": "automation"
    }
  },
  {
    "id": "icon.agent.schedule.paper-01",
    "name": "Schedule",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "automation",
    "slug": "schedule",
    "renderer": "schedule",
    "order": 25,
    "intents": [
      "schedule_task",
      "show_timing"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "schedule",
      "calendar",
      "clock",
      "task",
      "automation"
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
          "paper-slide",
          "drop-and-settle",
          "stamp-impact"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.3,
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
      "paper-slide",
      "drop-and-settle",
      "stamp-impact"
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
      "agent.schedule.soft",
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
    "accessibilityLabel": "Schedule AI agent and automation paper icon",
    "description": "A reusable layered paper-style schedule icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "schedule_task",
        "show_timing"
      ],
      "avoidWhen": [],
      "semanticRole": "automation"
    }
  },
  {
    "id": "icon.agent.condition.paper-01",
    "name": "Condition",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "automation",
    "slug": "condition",
    "renderer": "condition",
    "order": 26,
    "intents": [
      "evaluate_condition",
      "branch_on_rule"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "condition",
      "rule",
      "decision",
      "if",
      "branch"
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
          "paper-slide",
          "drop-and-settle",
          "stamp-impact"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.3,
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
      "paper-slide",
      "drop-and-settle",
      "stamp-impact"
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
      "agent.condition.soft",
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
    "accessibilityLabel": "Condition AI agent and automation paper icon",
    "description": "A reusable layered paper-style condition icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "evaluate_condition",
        "branch_on_rule"
      ],
      "avoidWhen": [],
      "semanticRole": "automation"
    }
  },
  {
    "id": "icon.agent.approval.paper-01",
    "name": "Approval",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "automation",
    "slug": "approval",
    "renderer": "approval",
    "order": 27,
    "intents": [
      "approve_task",
      "show_confirmation"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "approval",
      "stamp",
      "check",
      "review",
      "confirm"
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
          "paper-slide",
          "drop-and-settle",
          "stamp-impact"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.3,
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
      "paper-slide",
      "drop-and-settle",
      "stamp-impact"
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
      "agent.approval.soft",
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
    "accessibilityLabel": "Approval AI agent and automation paper icon",
    "description": "A reusable layered paper-style approval icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "approve_task",
        "show_confirmation"
      ],
      "avoidWhen": [],
      "semanticRole": "automation"
    }
  },
  {
    "id": "icon.agent.human-review.paper-01",
    "name": "Human review",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "automation",
    "slug": "human-review",
    "renderer": "human-review",
    "order": 28,
    "intents": [
      "request_human_review",
      "show_human_in_loop"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "human",
      "review",
      "person",
      "approval",
      "oversight"
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
          "paper-slide",
          "drop-and-settle",
          "stamp-impact"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.3,
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
      "paper-slide",
      "drop-and-settle",
      "stamp-impact"
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
      "agent.human-review.soft",
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
    "accessibilityLabel": "Human review AI agent and automation paper icon",
    "description": "A reusable layered paper-style human review icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "request_human_review",
        "show_human_in_loop"
      ],
      "avoidWhen": [],
      "semanticRole": "automation"
    }
  },
  {
    "id": "icon.agent.agent-handoff.paper-01",
    "name": "Agent handoff",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "automation",
    "slug": "agent-handoff",
    "renderer": "agent-handoff",
    "order": 29,
    "intents": [
      "handoff_between_agents",
      "transfer_task"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "handoff",
      "agents",
      "transfer",
      "token",
      "workflow"
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
          "paper-slide",
          "drop-and-settle",
          "stamp-impact"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.3,
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
      "paper-slide",
      "drop-and-settle",
      "stamp-impact"
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
      "agent.agent-handoff.soft",
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
    "accessibilityLabel": "Agent handoff AI agent and automation paper icon",
    "description": "A reusable layered paper-style agent handoff icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "handoff_between_agents",
        "transfer_task"
      ],
      "avoidWhen": [],
      "semanticRole": "automation"
    }
  },
  {
    "id": "icon.agent.parallel-tasks.paper-01",
    "name": "Parallel tasks",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "automation",
    "slug": "parallel-tasks",
    "renderer": "parallel-tasks",
    "order": 30,
    "intents": [
      "run_parallel_tasks",
      "split_work"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "parallel",
      "tasks",
      "lanes",
      "simultaneous",
      "workflow"
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
          "paper-slide",
          "drop-and-settle",
          "stamp-impact"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.3,
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
      "paper-slide",
      "drop-and-settle",
      "stamp-impact"
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
      "agent.parallel-tasks.soft",
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
    "accessibilityLabel": "Parallel tasks AI agent and automation paper icon",
    "description": "A reusable layered paper-style parallel tasks icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "run_parallel_tasks",
        "split_work"
      ],
      "avoidWhen": [],
      "semanticRole": "automation"
    }
  },
  {
    "id": "icon.agent.sequential-tasks.paper-01",
    "name": "Sequential tasks",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "automation",
    "slug": "sequential-tasks",
    "renderer": "sequential-tasks",
    "order": 31,
    "intents": [
      "run_sequential_tasks",
      "show_order"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "sequential",
      "tasks",
      "steps",
      "order",
      "workflow"
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
          "paper-slide",
          "drop-and-settle",
          "stamp-impact"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.3,
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
      "paper-slide",
      "drop-and-settle",
      "stamp-impact"
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
      "agent.sequential-tasks.soft",
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
    "accessibilityLabel": "Sequential tasks AI agent and automation paper icon",
    "description": "A reusable layered paper-style sequential tasks icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "run_sequential_tasks",
        "show_order"
      ],
      "avoidWhen": [],
      "semanticRole": "automation"
    }
  },
  {
    "id": "icon.agent.workflow.paper-01",
    "name": "Workflow",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "automation",
    "slug": "workflow",
    "renderer": "workflow",
    "order": 32,
    "intents": [
      "show_workflow",
      "connect_steps"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "workflow",
      "nodes",
      "process",
      "automation",
      "flow"
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
          "paper-slide",
          "drop-and-settle",
          "stamp-impact"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.3,
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
      "paper-slide",
      "drop-and-settle",
      "stamp-impact"
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
      "agent.workflow.soft",
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
    "accessibilityLabel": "Workflow AI agent and automation paper icon",
    "description": "A reusable layered paper-style workflow icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "show_workflow",
        "connect_steps"
      ],
      "avoidWhen": [],
      "semanticRole": "automation"
    }
  },
  {
    "id": "icon.agent.decision-branch.paper-01",
    "name": "Decision branch",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "automation",
    "slug": "decision-branch",
    "renderer": "decision-branch",
    "order": 33,
    "intents": [
      "show_decision_branch",
      "route_workflow"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "decision",
      "branch",
      "route",
      "condition",
      "workflow"
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
          "paper-slide",
          "drop-and-settle",
          "stamp-impact"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.3,
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
      "paper-slide",
      "drop-and-settle",
      "stamp-impact"
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
      "agent.decision-branch.soft",
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
    "accessibilityLabel": "Decision branch AI agent and automation paper icon",
    "description": "A reusable layered paper-style decision branch icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "show_decision_branch",
        "route_workflow"
      ],
      "avoidWhen": [],
      "semanticRole": "automation"
    }
  },
  {
    "id": "icon.agent.retry.paper-01",
    "name": "Retry",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "automation",
    "slug": "retry",
    "renderer": "retry",
    "order": 34,
    "intents": [
      "retry_task",
      "restart_process"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "retry",
      "again",
      "reverse",
      "repeat",
      "workflow"
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
          "paper-slide",
          "drop-and-settle",
          "stamp-impact"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.3,
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
      "paper-slide",
      "drop-and-settle",
      "stamp-impact"
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
      "agent.retry.soft",
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
    "accessibilityLabel": "Retry AI agent and automation paper icon",
    "description": "A reusable layered paper-style retry icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "retry_task",
        "restart_process"
      ],
      "avoidWhen": [],
      "semanticRole": "automation"
    }
  },
  {
    "id": "icon.agent.validation.paper-01",
    "name": "Validation",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "automation",
    "slug": "validation",
    "renderer": "validation",
    "order": 35,
    "intents": [
      "validate_output",
      "scan_result"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "validation",
      "scan",
      "check",
      "verify",
      "quality"
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
          "paper-slide",
          "drop-and-settle",
          "stamp-impact"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.3,
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
      "paper-slide",
      "drop-and-settle",
      "stamp-impact"
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
      "agent.validation.soft",
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
    "accessibilityLabel": "Validation AI agent and automation paper icon",
    "description": "A reusable layered paper-style validation icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "validate_output",
        "scan_result"
      ],
      "avoidWhen": [],
      "semanticRole": "automation"
    }
  },
  {
    "id": "icon.agent.quality-check.paper-01",
    "name": "Quality check",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "automation",
    "slug": "quality-check",
    "renderer": "quality-check",
    "order": 36,
    "intents": [
      "check_quality",
      "approve_quality"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "quality",
      "check",
      "star",
      "review",
      "validation"
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
          "paper-slide",
          "drop-and-settle",
          "stamp-impact"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.3,
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
      "paper-slide",
      "drop-and-settle",
      "stamp-impact"
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
      "agent.quality-check.soft",
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
    "accessibilityLabel": "Quality check AI agent and automation paper icon",
    "description": "A reusable layered paper-style quality check icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "check_quality",
        "approve_quality"
      ],
      "avoidWhen": [],
      "semanticRole": "automation"
    }
  },
  {
    "id": "icon.agent.security.paper-01",
    "name": "Security",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "trust",
    "slug": "security",
    "renderer": "security",
    "order": 37,
    "intents": [
      "secure_workflow",
      "show_protection"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "security",
      "shield",
      "protection",
      "safe",
      "lock"
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
        "recommended": 1.3,
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
      "agent.security.soft",
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
    "accessibilityLabel": "Security AI agent and automation paper icon",
    "description": "A reusable layered paper-style security icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "secure_workflow",
        "show_protection"
      ],
      "avoidWhen": [],
      "semanticRole": "trust"
    }
  },
  {
    "id": "icon.agent.identity.paper-01",
    "name": "Identity",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "trust",
    "slug": "identity",
    "renderer": "identity",
    "order": 38,
    "intents": [
      "verify_identity",
      "show_profile_identity"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "identity",
      "person",
      "card",
      "verification",
      "profile"
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
        "recommended": 1.3,
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
      "agent.identity.soft",
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
    "accessibilityLabel": "Identity AI agent and automation paper icon",
    "description": "A reusable layered paper-style identity icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "verify_identity",
        "show_profile_identity"
      ],
      "avoidWhen": [],
      "semanticRole": "trust"
    }
  },
  {
    "id": "icon.agent.wallet.paper-01",
    "name": "Wallet",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "trust",
    "slug": "wallet",
    "renderer": "wallet",
    "order": 39,
    "intents": [
      "use_wallet",
      "show_crypto_wallet"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "wallet",
      "money",
      "account",
      "crypto",
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
        "recommended": 1.3,
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
      "agent.wallet.soft",
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
    "accessibilityLabel": "Wallet AI agent and automation paper icon",
    "description": "A reusable layered paper-style wallet icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "use_wallet",
        "show_crypto_wallet"
      ],
      "avoidWhen": [],
      "semanticRole": "trust"
    }
  },
  {
    "id": "icon.agent.payment.paper-01",
    "name": "Payment",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "trust",
    "slug": "payment",
    "renderer": "payment",
    "order": 40,
    "intents": [
      "make_payment",
      "show_transaction"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "payment",
      "card",
      "coin",
      "transaction",
      "money"
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
        "recommended": 1.3,
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
      "agent.payment.soft",
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
    "accessibilityLabel": "Payment AI agent and automation paper icon",
    "description": "A reusable layered paper-style payment icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "make_payment",
        "show_transaction"
      ],
      "avoidWhen": [],
      "semanticRole": "trust"
    }
  },
  {
    "id": "icon.agent.escrow.paper-01",
    "name": "Escrow",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "trust",
    "slug": "escrow",
    "renderer": "escrow",
    "order": 41,
    "intents": [
      "hold_in_escrow",
      "release_payment"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "escrow",
      "lock",
      "payment",
      "funds",
      "trust"
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
        "recommended": 1.3,
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
      "agent.escrow.soft",
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
    "accessibilityLabel": "Escrow AI agent and automation paper icon",
    "description": "A reusable layered paper-style escrow icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "hold_in_escrow",
        "release_payment"
      ],
      "avoidWhen": [],
      "semanticRole": "trust"
    }
  },
  {
    "id": "icon.agent.notification.paper-01",
    "name": "Notification",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "trust",
    "slug": "notification",
    "renderer": "notification",
    "order": 42,
    "intents": [
      "send_notification",
      "show_alert"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "notification",
      "bell",
      "alert",
      "message",
      "update"
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
        "recommended": 1.3,
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
      "agent.notification.soft",
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
    "accessibilityLabel": "Notification AI agent and automation paper icon",
    "description": "A reusable layered paper-style notification icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "send_notification",
        "show_alert"
      ],
      "avoidWhen": [],
      "semanticRole": "trust"
    }
  },
  {
    "id": "icon.agent.output.paper-01",
    "name": "Output",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "output",
    "slug": "output",
    "renderer": "output",
    "order": 43,
    "intents": [
      "deliver_output",
      "show_result"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "output",
      "result",
      "export",
      "delivery",
      "complete"
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
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.3,
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
      "scale-bounce",
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
      "agent.output.soft",
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
    "accessibilityLabel": "Output AI agent and automation paper icon",
    "description": "A reusable layered paper-style output icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "deliver_output",
        "show_result"
      ],
      "avoidWhen": [],
      "semanticRole": "output"
    }
  },
  {
    "id": "icon.agent.completed-task.paper-01",
    "name": "Completed task",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "output",
    "slug": "completed-task",
    "renderer": "completed-task",
    "order": 44,
    "intents": [
      "show_completed_task",
      "mark_done"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "completed",
      "task",
      "done",
      "check",
      "success"
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
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.3,
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
      "scale-bounce",
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
      "agent.completed-task.soft",
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
    "accessibilityLabel": "Completed task AI agent and automation paper icon",
    "description": "A reusable layered paper-style completed task icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "show_completed_task",
        "mark_done"
      ],
      "avoidWhen": [],
      "semanticRole": "output"
    }
  },
  {
    "id": "icon.agent.failed-task.paper-01",
    "name": "Failed task",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "output",
    "slug": "failed-task",
    "renderer": "failed-task",
    "order": 45,
    "intents": [
      "show_failed_task",
      "mark_error"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "failed",
      "task",
      "error",
      "cross",
      "failure"
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
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.3,
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
      "scale-bounce",
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
      "agent.failed-task.soft",
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
    "accessibilityLabel": "Failed task AI agent and automation paper icon",
    "description": "A reusable layered paper-style failed task icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "show_failed_task",
        "mark_error"
      ],
      "avoidWhen": [],
      "semanticRole": "output"
    }
  },
  {
    "id": "icon.agent.processing.paper-01",
    "name": "Processing",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "output",
    "slug": "processing",
    "renderer": "processing",
    "order": 46,
    "intents": [
      "show_processing",
      "advance_progress"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "processing",
      "progress",
      "loading",
      "work",
      "status"
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
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.3,
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
      "scale-bounce",
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
      "agent.processing.soft",
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
    "accessibilityLabel": "Processing AI agent and automation paper icon",
    "description": "A reusable layered paper-style processing icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "show_processing",
        "advance_progress"
      ],
      "avoidWhen": [],
      "semanticRole": "output"
    }
  },
  {
    "id": "icon.agent.data-extraction.paper-01",
    "name": "Data extraction",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "output",
    "slug": "data-extraction",
    "renderer": "data-extraction",
    "order": 47,
    "intents": [
      "extract_data",
      "structure_information"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "data",
      "extraction",
      "document",
      "blocks",
      "structure"
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
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.3,
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
      "scale-bounce",
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
      "agent.data-extraction.soft",
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
    "accessibilityLabel": "Data extraction AI agent and automation paper icon",
    "description": "A reusable layered paper-style data extraction icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "extract_data",
        "structure_information"
      ],
      "avoidWhen": [],
      "semanticRole": "output"
    }
  },
  {
    "id": "icon.agent.transformation.paper-01",
    "name": "Transformation",
    "version": "1.5.0",
    "category": "icon",
    "subtype": "agent-automation",
    "group": "output",
    "slug": "transformation",
    "renderer": "transformation",
    "order": 48,
    "intents": [
      "transform_data",
      "convert_format"
    ],
    "keywords": [
      "icon",
      "agent",
      "automation",
      "paper",
      "transformation",
      "morph",
      "convert",
      "change",
      "output"
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
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.3,
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
      "scale-bounce",
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
      "agent.transformation.soft",
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
    "accessibilityLabel": "Transformation AI agent and automation paper icon",
    "description": "A reusable layered paper-style transformation icon for AI agents, automation and modern software workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "transform_data",
        "convert_format"
      ],
      "avoidWhen": [],
      "semanticRole": "output"
    }
  }
];
