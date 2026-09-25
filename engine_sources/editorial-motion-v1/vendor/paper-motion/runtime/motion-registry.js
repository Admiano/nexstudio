window.NEX_MOTIONS = [
  {
    "id": "motion.entrance.cut-paper-pop",
    "name": "Cut-paper pop",
    "version": "1.2.0",
    "category": "motion",
    "subtype": "entrance",
    "key": "cut-paper-pop",
    "intents": [
      "animate_entrance",
      "cut_paper_pop"
    ],
    "keywords": [
      "motion",
      "paper",
      "entrance",
      "cut",
      "paper",
      "pop"
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
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 2.4
      },
      "delay": {
        "type": "number",
        "minimum": 0,
        "maximum": 10
      },
      "intensity": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 1.8
      },
      "easing": {
        "type": "string",
        "default": "back.out(1.7)"
      }
    },
    "duration": {
      "minimum": 0.35,
      "recommended": 0.9,
      "maximum": 2.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleTargets": [
      "paper-object",
      "text",
      "svg"
    ],
    "compatibleMotions": [],
    "defaultEase": "back.out(1.7)",
    "soundTags": [
      "paper.pop.soft",
      "motion.impact.light"
    ],
    "themeTokens": [
      "--primary",
      "--secondary",
      "--accent",
      "--ink",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity"
    ],
    "accessibilityLabel": "Cut-paper pop reusable animation behaviour",
    "description": "A crisp cut-paper element pops from a compressed offset and settles with tactile weight.",
    "deterministic": true,
    "seekable": true,
    "finite": true
  },
  {
    "id": "motion.entrance.paper-slide",
    "name": "Paper slide",
    "version": "1.2.0",
    "category": "motion",
    "subtype": "entrance",
    "key": "paper-slide",
    "intents": [
      "animate_entrance",
      "paper_slide"
    ],
    "keywords": [
      "motion",
      "paper",
      "entrance",
      "paper",
      "slide"
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
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 2.4
      },
      "delay": {
        "type": "number",
        "minimum": 0,
        "maximum": 10
      },
      "intensity": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 1.8
      },
      "easing": {
        "type": "string",
        "default": "expo.out"
      }
    },
    "duration": {
      "minimum": 0.35,
      "recommended": 0.9,
      "maximum": 2.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleTargets": [
      "paper-object",
      "text",
      "svg"
    ],
    "compatibleMotions": [],
    "defaultEase": "expo.out",
    "soundTags": [
      "paper.slide.soft"
    ],
    "themeTokens": [
      "--primary",
      "--secondary",
      "--accent",
      "--ink",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity"
    ],
    "accessibilityLabel": "Paper slide reusable animation behaviour",
    "description": "Slides an element in as if pushed across a paper surface.",
    "deterministic": true,
    "seekable": true,
    "finite": true
  },
  {
    "id": "motion.entrance.drop-and-settle",
    "name": "Drop and settle",
    "version": "1.2.0",
    "category": "motion",
    "subtype": "entrance",
    "key": "drop-and-settle",
    "intents": [
      "animate_entrance",
      "drop_and_settle"
    ],
    "keywords": [
      "motion",
      "paper",
      "entrance",
      "drop",
      "and",
      "settle"
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
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 2.4
      },
      "delay": {
        "type": "number",
        "minimum": 0,
        "maximum": 10
      },
      "intensity": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 1.8
      },
      "easing": {
        "type": "string",
        "default": "back.out(1.7)"
      }
    },
    "duration": {
      "minimum": 0.35,
      "recommended": 0.9,
      "maximum": 2.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleTargets": [
      "paper-object",
      "text",
      "svg"
    ],
    "compatibleMotions": [],
    "defaultEase": "back.out(1.7)",
    "soundTags": [
      "paper.drop.medium"
    ],
    "themeTokens": [
      "--primary",
      "--secondary",
      "--accent",
      "--ink",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity"
    ],
    "accessibilityLabel": "Drop and settle reusable animation behaviour",
    "description": "Drops an element from above with a restrained rebound and final grounded settle.",
    "deterministic": true,
    "seekable": true,
    "finite": true
  },
  {
    "id": "motion.entrance.unfold",
    "name": "Unfold",
    "version": "1.2.0",
    "category": "motion",
    "subtype": "entrance",
    "key": "unfold",
    "intents": [
      "animate_entrance",
      "unfold"
    ],
    "keywords": [
      "motion",
      "paper",
      "entrance",
      "unfold"
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
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 2.4
      },
      "delay": {
        "type": "number",
        "minimum": 0,
        "maximum": 10
      },
      "intensity": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 1.8
      },
      "easing": {
        "type": "string",
        "default": "power2.inOut"
      }
    },
    "duration": {
      "minimum": 0.35,
      "recommended": 0.9,
      "maximum": 2.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleTargets": [
      "paper-object",
      "text",
      "svg"
    ],
    "compatibleMotions": [],
    "defaultEase": "power2.inOut",
    "soundTags": [
      "paper.unfold.soft"
    ],
    "themeTokens": [
      "--primary",
      "--secondary",
      "--accent",
      "--ink",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity"
    ],
    "accessibilityLabel": "Unfold reusable animation behaviour",
    "description": "Opens a flat element from a folded horizontal state using transform-origin-aware motion.",
    "deterministic": true,
    "seekable": true,
    "finite": true
  },
  {
    "id": "motion.entrance.peel-reveal",
    "name": "Peel reveal",
    "version": "1.2.0",
    "category": "motion",
    "subtype": "entrance",
    "key": "peel-reveal",
    "intents": [
      "animate_entrance",
      "peel_reveal"
    ],
    "keywords": [
      "motion",
      "paper",
      "entrance",
      "peel",
      "reveal"
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
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 2.4
      },
      "delay": {
        "type": "number",
        "minimum": 0,
        "maximum": 10
      },
      "intensity": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 1.8
      },
      "easing": {
        "type": "string",
        "default": "power3.out"
      }
    },
    "duration": {
      "minimum": 0.35,
      "recommended": 0.9,
      "maximum": 2.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleTargets": [
      "paper-object",
      "text",
      "svg"
    ],
    "compatibleMotions": [],
    "defaultEase": "power3.out",
    "soundTags": [
      "paper.peel.soft"
    ],
    "themeTokens": [
      "--primary",
      "--secondary",
      "--accent",
      "--ink",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity"
    ],
    "accessibilityLabel": "Peel reveal reusable animation behaviour",
    "description": "Peels a temporary cover away to reveal the target beneath.",
    "deterministic": true,
    "seekable": true,
    "finite": true
  },
  {
    "id": "motion.entrance.stamp-impact",
    "name": "Stamp impact",
    "version": "1.2.0",
    "category": "motion",
    "subtype": "entrance",
    "key": "stamp-impact",
    "intents": [
      "animate_entrance",
      "stamp_impact"
    ],
    "keywords": [
      "motion",
      "paper",
      "entrance",
      "stamp",
      "impact"
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
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 2.4
      },
      "delay": {
        "type": "number",
        "minimum": 0,
        "maximum": 10
      },
      "intensity": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 1.8
      },
      "easing": {
        "type": "string",
        "default": "power3.out"
      }
    },
    "duration": {
      "minimum": 0.35,
      "recommended": 0.9,
      "maximum": 2.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleTargets": [
      "paper-object",
      "text",
      "svg"
    ],
    "compatibleMotions": [],
    "defaultEase": "power3.out",
    "soundTags": [
      "paper.stamp.medium"
    ],
    "themeTokens": [
      "--primary",
      "--secondary",
      "--accent",
      "--ink",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity"
    ],
    "accessibilityLabel": "Stamp impact reusable animation behaviour",
    "description": "Lands with a fast stamp, compressed overshoot and subtle impact ring.",
    "deterministic": true,
    "seekable": true,
    "finite": true
  },
  {
    "id": "motion.entrance.draw-on",
    "name": "Draw-on",
    "version": "1.2.0",
    "category": "motion",
    "subtype": "entrance",
    "key": "draw-on",
    "intents": [
      "animate_entrance",
      "draw_on"
    ],
    "keywords": [
      "motion",
      "paper",
      "entrance",
      "draw",
      "on"
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
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 2.4
      },
      "delay": {
        "type": "number",
        "minimum": 0,
        "maximum": 10
      },
      "intensity": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 1.8
      },
      "easing": {
        "type": "string",
        "default": "sine.inOut"
      }
    },
    "duration": {
      "minimum": 0.35,
      "recommended": 0.9,
      "maximum": 2.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleTargets": [
      "paper-object",
      "text",
      "svg"
    ],
    "compatibleMotions": [],
    "defaultEase": "sine.inOut",
    "soundTags": [
      "draw.ink.soft"
    ],
    "themeTokens": [
      "--primary",
      "--secondary",
      "--accent",
      "--ink",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity"
    ],
    "accessibilityLabel": "Draw-on reusable animation behaviour",
    "description": "Draws SVG strokes or an automatically generated paper-ink line onto the target.",
    "deterministic": true,
    "seekable": true,
    "finite": true
  },
  {
    "id": "motion.entrance.ink-reveal",
    "name": "Ink reveal",
    "version": "1.2.0",
    "category": "motion",
    "subtype": "entrance",
    "key": "ink-reveal",
    "intents": [
      "animate_entrance",
      "ink_reveal"
    ],
    "keywords": [
      "motion",
      "paper",
      "entrance",
      "ink",
      "reveal"
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
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 2.4
      },
      "delay": {
        "type": "number",
        "minimum": 0,
        "maximum": 10
      },
      "intensity": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 1.8
      },
      "easing": {
        "type": "string",
        "default": "power2.inOut"
      }
    },
    "duration": {
      "minimum": 0.35,
      "recommended": 0.9,
      "maximum": 2.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleTargets": [
      "paper-object",
      "text",
      "svg"
    ],
    "compatibleMotions": [],
    "defaultEase": "power2.inOut",
    "soundTags": [
      "ink.reveal.soft"
    ],
    "themeTokens": [
      "--primary",
      "--secondary",
      "--accent",
      "--ink",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity"
    ],
    "accessibilityLabel": "Ink reveal reusable animation behaviour",
    "description": "Reveals the target through a spreading irregular ink mask.",
    "deterministic": true,
    "seekable": true,
    "finite": true
  },
  {
    "id": "motion.entrance.scale-bounce",
    "name": "Scale bounce",
    "version": "1.2.0",
    "category": "motion",
    "subtype": "entrance",
    "key": "scale-bounce",
    "intents": [
      "animate_entrance",
      "scale_bounce"
    ],
    "keywords": [
      "motion",
      "paper",
      "entrance",
      "scale",
      "bounce"
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
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 2.4
      },
      "delay": {
        "type": "number",
        "minimum": 0,
        "maximum": 10
      },
      "intensity": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 1.8
      },
      "easing": {
        "type": "string",
        "default": "back.out(1.7)"
      }
    },
    "duration": {
      "minimum": 0.35,
      "recommended": 0.9,
      "maximum": 2.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleTargets": [
      "paper-object",
      "text",
      "svg"
    ],
    "compatibleMotions": [],
    "defaultEase": "back.out(1.7)",
    "soundTags": [
      "motion.pop.soft"
    ],
    "themeTokens": [
      "--primary",
      "--secondary",
      "--accent",
      "--ink",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity"
    ],
    "accessibilityLabel": "Scale bounce reusable animation behaviour",
    "description": "A controlled scale-up with one premium bounce, avoiding toy-like elasticity.",
    "deterministic": true,
    "seekable": true,
    "finite": true
  },
  {
    "id": "motion.entrance.page-flip",
    "name": "Page flip",
    "version": "1.2.0",
    "category": "motion",
    "subtype": "entrance",
    "key": "page-flip",
    "intents": [
      "animate_entrance",
      "page_flip"
    ],
    "keywords": [
      "motion",
      "paper",
      "entrance",
      "page",
      "flip"
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
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 2.4
      },
      "delay": {
        "type": "number",
        "minimum": 0,
        "maximum": 10
      },
      "intensity": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 1.8
      },
      "easing": {
        "type": "string",
        "default": "power2.inOut"
      }
    },
    "duration": {
      "minimum": 0.35,
      "recommended": 0.9,
      "maximum": 2.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleTargets": [
      "paper-object",
      "text",
      "svg"
    ],
    "compatibleMotions": [],
    "defaultEase": "power2.inOut",
    "soundTags": [
      "paper.page-turn.soft"
    ],
    "themeTokens": [
      "--primary",
      "--secondary",
      "--accent",
      "--ink",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity"
    ],
    "accessibilityLabel": "Page flip reusable animation behaviour",
    "description": "Flips the target into view around a paper-edge hinge.",
    "deterministic": true,
    "seekable": true,
    "finite": true
  },
  {
    "id": "motion.action.pulse",
    "name": "Pulse",
    "version": "1.2.0",
    "category": "motion",
    "subtype": "action",
    "key": "pulse",
    "intents": [
      "animate_action",
      "pulse"
    ],
    "keywords": [
      "motion",
      "paper",
      "action",
      "pulse"
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
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 2.4
      },
      "delay": {
        "type": "number",
        "minimum": 0,
        "maximum": 10
      },
      "intensity": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 1.8
      },
      "easing": {
        "type": "string",
        "default": "sine.inOut"
      }
    },
    "duration": {
      "minimum": 0.35,
      "recommended": 0.9,
      "maximum": 2.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleTargets": [
      "paper-object",
      "text",
      "svg"
    ],
    "compatibleMotions": [],
    "defaultEase": "sine.inOut",
    "soundTags": [
      "ui.emphasis.soft"
    ],
    "themeTokens": [
      "--primary",
      "--secondary",
      "--accent",
      "--ink",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity"
    ],
    "accessibilityLabel": "Pulse reusable animation behaviour",
    "description": "Produces a finite emphasis pulse while returning exactly to the original layout state.",
    "deterministic": true,
    "seekable": true,
    "finite": true
  },
  {
    "id": "motion.action.wiggle",
    "name": "Wiggle",
    "version": "1.2.0",
    "category": "motion",
    "subtype": "action",
    "key": "wiggle",
    "intents": [
      "animate_action",
      "wiggle"
    ],
    "keywords": [
      "motion",
      "paper",
      "action",
      "wiggle"
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
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 2.4
      },
      "delay": {
        "type": "number",
        "minimum": 0,
        "maximum": 10
      },
      "intensity": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 1.8
      },
      "easing": {
        "type": "string",
        "default": "sine.inOut"
      }
    },
    "duration": {
      "minimum": 0.35,
      "recommended": 0.9,
      "maximum": 2.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleTargets": [
      "paper-object",
      "text",
      "svg"
    ],
    "compatibleMotions": [],
    "defaultEase": "sine.inOut",
    "soundTags": [
      "paper.wiggle.soft"
    ],
    "themeTokens": [
      "--primary",
      "--secondary",
      "--accent",
      "--ink",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity"
    ],
    "accessibilityLabel": "Wiggle reusable animation behaviour",
    "description": "Applies a short finite paper wiggle for attention or uncertainty.",
    "deterministic": true,
    "seekable": true,
    "finite": true
  },
  {
    "id": "motion.action.tick-confirm",
    "name": "Tick or confirm",
    "version": "1.2.0",
    "category": "motion",
    "subtype": "action",
    "key": "tick-confirm",
    "intents": [
      "animate_action",
      "tick_confirm"
    ],
    "keywords": [
      "motion",
      "paper",
      "action",
      "tick",
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
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 2.4
      },
      "delay": {
        "type": "number",
        "minimum": 0,
        "maximum": 10
      },
      "intensity": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 1.8
      },
      "easing": {
        "type": "string",
        "default": "power3.out"
      }
    },
    "duration": {
      "minimum": 0.35,
      "recommended": 0.9,
      "maximum": 2.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleTargets": [
      "paper-object",
      "text",
      "svg"
    ],
    "compatibleMotions": [],
    "defaultEase": "power3.out",
    "soundTags": [
      "ui.confirm.soft"
    ],
    "themeTokens": [
      "--primary",
      "--secondary",
      "--accent",
      "--ink",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity"
    ],
    "accessibilityLabel": "Tick or confirm reusable animation behaviour",
    "description": "Draws and lands a paper-ink confirmation mark above or inside the target.",
    "deterministic": true,
    "seekable": true,
    "finite": true
  },
  {
    "id": "motion.action.numeric-count",
    "name": "Numeric count",
    "version": "1.2.0",
    "category": "motion",
    "subtype": "action",
    "key": "numeric-count",
    "intents": [
      "animate_action",
      "numeric_count"
    ],
    "keywords": [
      "motion",
      "paper",
      "action",
      "numeric",
      "count"
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
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 2.4
      },
      "delay": {
        "type": "number",
        "minimum": 0,
        "maximum": 10
      },
      "intensity": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 1.8
      },
      "easing": {
        "type": "string",
        "default": "power2.out"
      }
    },
    "duration": {
      "minimum": 0.35,
      "recommended": 0.9,
      "maximum": 2.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleTargets": [
      "text",
      "paper-object",
      "data-label"
    ],
    "compatibleMotions": [],
    "defaultEase": "power2.out",
    "soundTags": [
      "ui.counter.soft"
    ],
    "themeTokens": [
      "--primary",
      "--secondary",
      "--accent",
      "--ink",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity"
    ],
    "accessibilityLabel": "Numeric count reusable animation behaviour",
    "description": "Counts deterministically from a configured start value to an end value.",
    "deterministic": true,
    "seekable": true,
    "finite": true
  },
  {
    "id": "motion.action.colour-fill",
    "name": "Colour fill",
    "version": "1.2.0",
    "category": "motion",
    "subtype": "action",
    "key": "colour-fill",
    "intents": [
      "animate_action",
      "colour_fill"
    ],
    "keywords": [
      "motion",
      "paper",
      "action",
      "colour",
      "fill"
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
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 2.4
      },
      "delay": {
        "type": "number",
        "minimum": 0,
        "maximum": 10
      },
      "intensity": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 1.8
      },
      "easing": {
        "type": "string",
        "default": "power2.inOut"
      }
    },
    "duration": {
      "minimum": 0.35,
      "recommended": 0.9,
      "maximum": 2.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleTargets": [
      "paper-object",
      "text",
      "svg"
    ],
    "compatibleMotions": [],
    "defaultEase": "power2.inOut",
    "soundTags": [
      "paper.fill.soft"
    ],
    "themeTokens": [
      "--primary",
      "--secondary",
      "--accent",
      "--ink",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity"
    ],
    "accessibilityLabel": "Colour fill reusable animation behaviour",
    "description": "Sweeps a theme-token colour across the target without permanently baking a colour.",
    "deterministic": true,
    "seekable": true,
    "finite": true
  },
  {
    "id": "motion.action.rotate",
    "name": "Rotate",
    "version": "1.2.0",
    "category": "motion",
    "subtype": "action",
    "key": "rotate",
    "intents": [
      "animate_action",
      "rotate"
    ],
    "keywords": [
      "motion",
      "paper",
      "action",
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
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 2.4
      },
      "delay": {
        "type": "number",
        "minimum": 0,
        "maximum": 10
      },
      "intensity": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 1.8
      },
      "easing": {
        "type": "string",
        "default": "power2.inOut"
      }
    },
    "duration": {
      "minimum": 0.35,
      "recommended": 0.9,
      "maximum": 2.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleTargets": [
      "paper-object",
      "text",
      "svg"
    ],
    "compatibleMotions": [],
    "defaultEase": "power2.inOut",
    "soundTags": [
      "motion.rotate.soft"
    ],
    "themeTokens": [
      "--primary",
      "--secondary",
      "--accent",
      "--ink",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity"
    ],
    "accessibilityLabel": "Rotate reusable animation behaviour",
    "description": "Completes a finite configurable rotation and returns or holds as configured.",
    "deterministic": true,
    "seekable": true,
    "finite": true
  },
  {
    "id": "motion.action.open-and-close",
    "name": "Open and close",
    "version": "1.2.0",
    "category": "motion",
    "subtype": "action",
    "key": "open-and-close",
    "intents": [
      "animate_action",
      "open_and_close"
    ],
    "keywords": [
      "motion",
      "paper",
      "action",
      "open",
      "and",
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
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 2.4
      },
      "delay": {
        "type": "number",
        "minimum": 0,
        "maximum": 10
      },
      "intensity": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 1.8
      },
      "easing": {
        "type": "string",
        "default": "power2.inOut"
      }
    },
    "duration": {
      "minimum": 0.35,
      "recommended": 0.9,
      "maximum": 2.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleTargets": [
      "paper-object",
      "text",
      "svg"
    ],
    "compatibleMotions": [],
    "defaultEase": "power2.inOut",
    "soundTags": [
      "paper.open-close.soft"
    ],
    "themeTokens": [
      "--primary",
      "--secondary",
      "--accent",
      "--ink",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity"
    ],
    "accessibilityLabel": "Open and close reusable animation behaviour",
    "description": "Opens then closes a target around a configurable hinge.",
    "deterministic": true,
    "seekable": true,
    "finite": true
  },
  {
    "id": "motion.action.connect",
    "name": "Connect",
    "version": "1.2.0",
    "category": "motion",
    "subtype": "action",
    "key": "connect",
    "intents": [
      "animate_action",
      "connect"
    ],
    "keywords": [
      "motion",
      "paper",
      "action",
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
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 2.4
      },
      "delay": {
        "type": "number",
        "minimum": 0,
        "maximum": 10
      },
      "intensity": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 1.8
      },
      "easing": {
        "type": "string",
        "default": "sine.inOut"
      }
    },
    "duration": {
      "minimum": 0.35,
      "recommended": 0.9,
      "maximum": 2.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleTargets": [
      "workflow",
      "paper-object",
      "svg"
    ],
    "compatibleMotions": [],
    "defaultEase": "sine.inOut",
    "soundTags": [
      "line.connect.soft"
    ],
    "themeTokens": [
      "--primary",
      "--secondary",
      "--accent",
      "--ink",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity"
    ],
    "accessibilityLabel": "Connect reusable animation behaviour",
    "description": "Draws a deterministic connection between two marked nodes inside the target.",
    "deterministic": true,
    "seekable": true,
    "finite": true
  },
  {
    "id": "motion.action.marker-highlight",
    "name": "Marker highlight",
    "version": "1.2.0",
    "category": "motion",
    "subtype": "action",
    "key": "marker-highlight",
    "intents": [
      "animate_action",
      "marker_highlight"
    ],
    "keywords": [
      "motion",
      "paper",
      "action",
      "marker",
      "highlight"
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
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 2.4
      },
      "delay": {
        "type": "number",
        "minimum": 0,
        "maximum": 10
      },
      "intensity": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 1.8
      },
      "easing": {
        "type": "string",
        "default": "power2.out"
      }
    },
    "duration": {
      "minimum": 0.35,
      "recommended": 0.9,
      "maximum": 2.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleTargets": [
      "text",
      "paper-object",
      "caption"
    ],
    "compatibleMotions": [],
    "defaultEase": "power2.out",
    "soundTags": [
      "draw.marker.soft"
    ],
    "themeTokens": [
      "--primary",
      "--secondary",
      "--accent",
      "--ink",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity"
    ],
    "accessibilityLabel": "Marker highlight reusable animation behaviour",
    "description": "Sweeps a paper-marker highlight beneath editable text.",
    "deterministic": true,
    "seekable": true,
    "finite": true
  },
  {
    "id": "motion.action.type-or-write",
    "name": "Type or write",
    "version": "1.2.0",
    "category": "motion",
    "subtype": "action",
    "key": "type-or-write",
    "intents": [
      "animate_action",
      "type_or_write"
    ],
    "keywords": [
      "motion",
      "paper",
      "action",
      "type",
      "or",
      "write"
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
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 2.4
      },
      "delay": {
        "type": "number",
        "minimum": 0,
        "maximum": 10
      },
      "intensity": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 1.8
      },
      "easing": {
        "type": "string",
        "default": "none"
      }
    },
    "duration": {
      "minimum": 0.35,
      "recommended": 0.9,
      "maximum": 2.4
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleTargets": [
      "text",
      "paper-object",
      "caption"
    ],
    "compatibleMotions": [],
    "defaultEase": "none",
    "soundTags": [
      "write.type.soft"
    ],
    "themeTokens": [
      "--primary",
      "--secondary",
      "--accent",
      "--ink",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity"
    ],
    "accessibilityLabel": "Type or write reusable animation behaviour",
    "description": "Reveals editable text character by character with deterministic timing.",
    "deterministic": true,
    "seekable": true,
    "finite": true
  },
  {
    "id": "motion.ambient.paper-flutter",
    "name": "Paper flutter",
    "version": "1.2.0",
    "category": "motion",
    "subtype": "ambient",
    "key": "paper-flutter",
    "intents": [
      "animate_ambient",
      "paper_flutter"
    ],
    "keywords": [
      "motion",
      "paper",
      "ambient",
      "paper",
      "flutter"
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
      "duration": {
        "type": "number",
        "minimum": 1.4,
        "maximum": 8
      },
      "delay": {
        "type": "number",
        "minimum": 0,
        "maximum": 10
      },
      "intensity": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 1.8
      },
      "easing": {
        "type": "string",
        "default": "sine.inOut"
      }
    },
    "duration": {
      "minimum": 1.4,
      "recommended": 3.2,
      "maximum": 8
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleTargets": [
      "paper-object",
      "text",
      "svg"
    ],
    "compatibleMotions": [],
    "defaultEase": "sine.inOut",
    "soundTags": [
      "paper.flutter.soft"
    ],
    "themeTokens": [
      "--primary",
      "--secondary",
      "--accent",
      "--ink",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity"
    ],
    "accessibilityLabel": "Paper flutter reusable animation behaviour",
    "description": "A finite edge-and-plane flutter that retains the component\u2019s resting position.",
    "deterministic": true,
    "seekable": true,
    "finite": true,
    "finiteCycles": 3,
    "recommendedCycleDuration": 1.1
  },
  {
    "id": "motion.ambient.subtle-float",
    "name": "Subtle float",
    "version": "1.2.0",
    "category": "motion",
    "subtype": "ambient",
    "key": "subtle-float",
    "intents": [
      "animate_ambient",
      "subtle_float"
    ],
    "keywords": [
      "motion",
      "paper",
      "ambient",
      "subtle",
      "float"
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
      "duration": {
        "type": "number",
        "minimum": 1.4,
        "maximum": 8
      },
      "delay": {
        "type": "number",
        "minimum": 0,
        "maximum": 10
      },
      "intensity": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 1.8
      },
      "easing": {
        "type": "string",
        "default": "sine.inOut"
      }
    },
    "duration": {
      "minimum": 1.4,
      "recommended": 3.4,
      "maximum": 8
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleTargets": [
      "paper-object",
      "text",
      "svg"
    ],
    "compatibleMotions": [],
    "defaultEase": "sine.inOut",
    "soundTags": [
      "motion.air.soft"
    ],
    "themeTokens": [
      "--primary",
      "--secondary",
      "--accent",
      "--ink",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity"
    ],
    "accessibilityLabel": "Subtle float reusable animation behaviour",
    "description": "A finite, low-amplitude vertical drift suitable for hero objects.",
    "deterministic": true,
    "seekable": true,
    "finite": true,
    "finiteCycles": 3,
    "recommendedCycleDuration": 1.1
  },
  {
    "id": "motion.ambient.shadow-breathing",
    "name": "Shadow breathing",
    "version": "1.2.0",
    "category": "motion",
    "subtype": "ambient",
    "key": "shadow-breathing",
    "intents": [
      "animate_ambient",
      "shadow_breathing"
    ],
    "keywords": [
      "motion",
      "paper",
      "ambient",
      "shadow",
      "breathing"
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
      "duration": {
        "type": "number",
        "minimum": 1.4,
        "maximum": 8
      },
      "delay": {
        "type": "number",
        "minimum": 0,
        "maximum": 10
      },
      "intensity": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 1.8
      },
      "easing": {
        "type": "string",
        "default": "sine.inOut"
      }
    },
    "duration": {
      "minimum": 1.4,
      "recommended": 3.4,
      "maximum": 8
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleTargets": [
      "paper-object",
      "text",
      "svg"
    ],
    "compatibleMotions": [],
    "defaultEase": "sine.inOut",
    "soundTags": [
      "motion.ambient.none"
    ],
    "themeTokens": [
      "--primary",
      "--secondary",
      "--accent",
      "--ink",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity"
    ],
    "accessibilityLabel": "Shadow breathing reusable animation behaviour",
    "description": "Gently expands and contracts a generated paper shadow for finite ambient depth.",
    "deterministic": true,
    "seekable": true,
    "finite": true,
    "finiteCycles": 3,
    "recommendedCycleDuration": 1.1
  },
  {
    "id": "motion.ambient.grain-drift",
    "name": "Grain drift",
    "version": "1.2.0",
    "category": "motion",
    "subtype": "ambient",
    "key": "grain-drift",
    "intents": [
      "animate_ambient",
      "grain_drift"
    ],
    "keywords": [
      "motion",
      "paper",
      "ambient",
      "grain",
      "drift"
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
      "duration": {
        "type": "number",
        "minimum": 1.4,
        "maximum": 8
      },
      "delay": {
        "type": "number",
        "minimum": 0,
        "maximum": 10
      },
      "intensity": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 1.8
      },
      "easing": {
        "type": "string",
        "default": "sine.inOut"
      }
    },
    "duration": {
      "minimum": 1.4,
      "recommended": 3.4,
      "maximum": 8
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleTargets": [
      "paper-object",
      "text",
      "svg"
    ],
    "compatibleMotions": [],
    "defaultEase": "sine.inOut",
    "soundTags": [
      "paper.grain.none"
    ],
    "themeTokens": [
      "--primary",
      "--secondary",
      "--accent",
      "--ink",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity"
    ],
    "accessibilityLabel": "Grain drift reusable animation behaviour",
    "description": "Moves an existing or generated grain layer in a finite deterministic loop.",
    "deterministic": true,
    "seekable": true,
    "finite": true,
    "finiteCycles": 3,
    "recommendedCycleDuration": 1.1
  },
  {
    "id": "motion.ambient.ink-jitter",
    "name": "Ink jitter",
    "version": "1.2.0",
    "category": "motion",
    "subtype": "ambient",
    "key": "ink-jitter",
    "intents": [
      "animate_ambient",
      "ink_jitter"
    ],
    "keywords": [
      "motion",
      "paper",
      "ambient",
      "ink",
      "jitter"
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
      "duration": {
        "type": "number",
        "minimum": 1.2,
        "maximum": 7
      },
      "delay": {
        "type": "number",
        "minimum": 0,
        "maximum": 10
      },
      "intensity": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 1.8
      },
      "easing": {
        "type": "string",
        "default": "sine.inOut"
      }
    },
    "duration": {
      "minimum": 1.2,
      "recommended": 2.8,
      "maximum": 7
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleTargets": [
      "paper-object",
      "text",
      "svg"
    ],
    "compatibleMotions": [],
    "defaultEase": "sine.inOut",
    "soundTags": [
      "ink.jitter.soft"
    ],
    "themeTokens": [
      "--primary",
      "--secondary",
      "--accent",
      "--ink",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity"
    ],
    "accessibilityLabel": "Ink jitter reusable animation behaviour",
    "description": "Adds a very restrained finite registration jitter to ink or text.",
    "deterministic": true,
    "seekable": true,
    "finite": true,
    "finiteCycles": 3,
    "recommendedCycleDuration": 1.1
  },
  {
    "id": "motion.transition.page-turn",
    "name": "Page turn",
    "version": "1.2.0",
    "category": "motion",
    "subtype": "transition",
    "key": "page-turn",
    "intents": [
      "animate_transition",
      "page_turn"
    ],
    "keywords": [
      "motion",
      "paper",
      "transition",
      "page",
      "turn"
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
      "duration": {
        "type": "number",
        "minimum": 0.55,
        "maximum": 1.8
      },
      "delay": {
        "type": "number",
        "minimum": 0,
        "maximum": 10
      },
      "intensity": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 1.8
      },
      "easing": {
        "type": "string",
        "default": "power2.inOut"
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 0.95,
      "maximum": 1.8
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleTargets": [
      "editorial-scene",
      "collage-scene",
      "technical-scene"
    ],
    "compatibleMotions": [],
    "defaultEase": "power2.inOut",
    "soundTags": [
      "transition.page-turn"
    ],
    "themeTokens": [
      "--primary",
      "--secondary",
      "--accent",
      "--ink",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity"
    ],
    "accessibilityLabel": "Page turn reusable animation behaviour",
    "description": "Turns the outgoing scene like a physical page while revealing the incoming scene underneath.",
    "deterministic": true,
    "seekable": true,
    "finite": true,
    "preservesOutgoingUntilStart": true,
    "requiresIncomingAndOutgoing": true
  },
  {
    "id": "motion.transition.paper-wipe",
    "name": "Paper wipe",
    "version": "1.2.0",
    "category": "motion",
    "subtype": "transition",
    "key": "paper-wipe",
    "intents": [
      "animate_transition",
      "paper_wipe"
    ],
    "keywords": [
      "motion",
      "paper",
      "transition",
      "paper",
      "wipe"
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
      "duration": {
        "type": "number",
        "minimum": 0.45,
        "maximum": 1.5
      },
      "delay": {
        "type": "number",
        "minimum": 0,
        "maximum": 10
      },
      "intensity": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 1.8
      },
      "easing": {
        "type": "string",
        "default": "power3.inOut"
      }
    },
    "duration": {
      "minimum": 0.45,
      "recommended": 0.8,
      "maximum": 1.5
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleTargets": [
      "editorial-scene",
      "collage-scene",
      "technical-scene"
    ],
    "compatibleMotions": [],
    "defaultEase": "power3.inOut",
    "soundTags": [
      "transition.paper-wipe"
    ],
    "themeTokens": [
      "--primary",
      "--secondary",
      "--accent",
      "--ink",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity"
    ],
    "accessibilityLabel": "Paper wipe reusable animation behaviour",
    "description": "Moves a full paper sheet across the composition and switches scenes beneath it.",
    "deterministic": true,
    "seekable": true,
    "finite": true,
    "preservesOutgoingUntilStart": true,
    "requiresIncomingAndOutgoing": true
  },
  {
    "id": "motion.transition.torn-paper-reveal",
    "name": "Torn-paper reveal",
    "version": "1.2.0",
    "category": "motion",
    "subtype": "transition",
    "key": "torn-paper-reveal",
    "intents": [
      "animate_transition",
      "torn_paper_reveal"
    ],
    "keywords": [
      "motion",
      "paper",
      "transition",
      "torn",
      "paper",
      "reveal"
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
      "duration": {
        "type": "number",
        "minimum": 0.55,
        "maximum": 1.8
      },
      "delay": {
        "type": "number",
        "minimum": 0,
        "maximum": 10
      },
      "intensity": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 1.8
      },
      "easing": {
        "type": "string",
        "default": "power2.inOut"
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 0.95,
      "maximum": 1.8
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleTargets": [
      "editorial-scene",
      "collage-scene",
      "technical-scene"
    ],
    "compatibleMotions": [],
    "defaultEase": "power2.inOut",
    "soundTags": [
      "transition.tear"
    ],
    "themeTokens": [
      "--primary",
      "--secondary",
      "--accent",
      "--ink",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity"
    ],
    "accessibilityLabel": "Torn-paper reveal reusable animation behaviour",
    "description": "Pulls a torn paper boundary across the outgoing scene to expose the incoming scene.",
    "deterministic": true,
    "seekable": true,
    "finite": true,
    "preservesOutgoingUntilStart": true,
    "requiresIncomingAndOutgoing": true
  },
  {
    "id": "motion.transition.collage-push",
    "name": "Collage push",
    "version": "1.2.0",
    "category": "motion",
    "subtype": "transition",
    "key": "collage-push",
    "intents": [
      "animate_transition",
      "collage_push"
    ],
    "keywords": [
      "motion",
      "paper",
      "transition",
      "collage",
      "push"
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
      "duration": {
        "type": "number",
        "minimum": 0.5,
        "maximum": 1.6
      },
      "delay": {
        "type": "number",
        "minimum": 0,
        "maximum": 10
      },
      "intensity": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 1.8
      },
      "easing": {
        "type": "string",
        "default": "expo.out"
      }
    },
    "duration": {
      "minimum": 0.5,
      "recommended": 0.85,
      "maximum": 1.6
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleTargets": [
      "editorial-scene",
      "collage-scene",
      "technical-scene"
    ],
    "compatibleMotions": [],
    "defaultEase": "expo.out",
    "soundTags": [
      "transition.collage-push"
    ],
    "themeTokens": [
      "--primary",
      "--secondary",
      "--accent",
      "--ink",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity"
    ],
    "accessibilityLabel": "Collage push reusable animation behaviour",
    "description": "Pushes layered outgoing and incoming compositions as offset collage sheets.",
    "deterministic": true,
    "seekable": true,
    "finite": true,
    "preservesOutgoingUntilStart": true,
    "requiresIncomingAndOutgoing": true
  },
  {
    "id": "motion.transition.tape-peel",
    "name": "Tape peel",
    "version": "1.2.0",
    "category": "motion",
    "subtype": "transition",
    "key": "tape-peel",
    "intents": [
      "animate_transition",
      "tape_peel"
    ],
    "keywords": [
      "motion",
      "paper",
      "transition",
      "tape",
      "peel"
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
      "duration": {
        "type": "number",
        "minimum": 0.65,
        "maximum": 2
      },
      "delay": {
        "type": "number",
        "minimum": 0,
        "maximum": 10
      },
      "intensity": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 1.8
      },
      "easing": {
        "type": "string",
        "default": "power3.inOut"
      }
    },
    "duration": {
      "minimum": 0.65,
      "recommended": 1.05,
      "maximum": 2
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleTargets": [
      "editorial-scene",
      "collage-scene",
      "technical-scene"
    ],
    "compatibleMotions": [],
    "defaultEase": "power3.inOut",
    "soundTags": [
      "transition.tape-peel"
    ],
    "themeTokens": [
      "--primary",
      "--secondary",
      "--accent",
      "--ink",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity"
    ],
    "accessibilityLabel": "Tape peel reusable animation behaviour",
    "description": "Peels a tape strip free before lifting the outgoing scene away.",
    "deterministic": true,
    "seekable": true,
    "finite": true,
    "preservesOutgoingUntilStart": true,
    "requiresIncomingAndOutgoing": true
  },
  {
    "id": "motion.transition.card-stack-shuffle",
    "name": "Card-stack shuffle",
    "version": "1.2.0",
    "category": "motion",
    "subtype": "transition",
    "key": "card-stack-shuffle",
    "intents": [
      "animate_transition",
      "card_stack_shuffle"
    ],
    "keywords": [
      "motion",
      "paper",
      "transition",
      "card",
      "stack",
      "shuffle"
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
      "duration": {
        "type": "number",
        "minimum": 0.55,
        "maximum": 1.8
      },
      "delay": {
        "type": "number",
        "minimum": 0,
        "maximum": 10
      },
      "intensity": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 1.8
      },
      "easing": {
        "type": "string",
        "default": "back.out(1.7)"
      }
    },
    "duration": {
      "minimum": 0.55,
      "recommended": 0.95,
      "maximum": 1.8
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleTargets": [
      "editorial-scene",
      "collage-scene",
      "technical-scene"
    ],
    "compatibleMotions": [],
    "defaultEase": "back.out(1.7)",
    "soundTags": [
      "transition.card-shuffle"
    ],
    "themeTokens": [
      "--primary",
      "--secondary",
      "--accent",
      "--ink",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity"
    ],
    "accessibilityLabel": "Card-stack shuffle reusable animation behaviour",
    "description": "Shuffles the outgoing card away as the incoming card rises from the stack.",
    "deterministic": true,
    "seekable": true,
    "finite": true,
    "preservesOutgoingUntilStart": true,
    "requiresIncomingAndOutgoing": true
  },
  {
    "id": "motion.transition.crumple-transition",
    "name": "Crumple transition",
    "version": "1.2.0",
    "category": "motion",
    "subtype": "transition",
    "key": "crumple-transition",
    "intents": [
      "animate_transition",
      "crumple_transition"
    ],
    "keywords": [
      "motion",
      "paper",
      "transition",
      "crumple",
      "transition"
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
      "duration": {
        "type": "number",
        "minimum": 0.7,
        "maximum": 2.2
      },
      "delay": {
        "type": "number",
        "minimum": 0,
        "maximum": 10
      },
      "intensity": {
        "type": "number",
        "minimum": 0.35,
        "maximum": 1.8
      },
      "easing": {
        "type": "string",
        "default": "power2.inOut"
      }
    },
    "duration": {
      "minimum": 0.7,
      "recommended": 1.15,
      "maximum": 2.2
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleTargets": [
      "editorial-scene",
      "collage-scene",
      "technical-scene"
    ],
    "compatibleMotions": [],
    "defaultEase": "power2.inOut",
    "soundTags": [
      "transition.crumple"
    ],
    "themeTokens": [
      "--primary",
      "--secondary",
      "--accent",
      "--ink",
      "--highlight",
      "--shadow-color",
      "--shadow-opacity",
      "--grain-opacity"
    ],
    "accessibilityLabel": "Crumple transition reusable animation behaviour",
    "description": "Compresses the outgoing scene into a paper wad before the incoming scene unfolds.",
    "deterministic": true,
    "seekable": true,
    "finite": true,
    "preservesOutgoingUntilStart": true,
    "requiresIncomingAndOutgoing": true
  }
];
