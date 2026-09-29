window.NEX_CREATOR_ICONS = [
  {
    "id": "icon.creator.camera.paper-01",
    "name": "Camera",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "media",
    "slug": "camera",
    "renderer": "camera",
    "order": 1,
    "intents": [
      "capture_photo",
      "create_visual_content"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "camera",
      "photo",
      "capture",
      "lens",
      "creator"
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
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
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
      "creator.camera.soft",
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
    "accessibilityLabel": "Camera creator and media paper icon",
    "description": "A reusable layered paper-style camera icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "capture_photo",
        "create_visual_content"
      ],
      "avoidWhen": [],
      "semanticRole": "media"
    }
  },
  {
    "id": "icon.creator.video-camera.paper-01",
    "name": "Video camera",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "media",
    "slug": "video-camera",
    "renderer": "video-camera",
    "order": 2,
    "intents": [
      "record_video",
      "capture_motion"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "video",
      "camera",
      "record",
      "film",
      "creator"
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
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
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
      "creator.video-camera.soft",
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
    "accessibilityLabel": "Video camera creator and media paper icon",
    "description": "A reusable layered paper-style video camera icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "record_video",
        "capture_motion"
      ],
      "avoidWhen": [],
      "semanticRole": "media"
    }
  },
  {
    "id": "icon.creator.microphone.paper-01",
    "name": "Microphone",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "audio",
    "slug": "microphone",
    "renderer": "microphone",
    "order": 3,
    "intents": [
      "record_voice",
      "capture_audio"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "microphone",
      "voice",
      "audio",
      "record",
      "creator"
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
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
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
      "creator.microphone.soft",
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
    "accessibilityLabel": "Microphone creator and media paper icon",
    "description": "A reusable layered paper-style microphone icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "record_voice",
        "capture_audio"
      ],
      "avoidWhen": [],
      "semanticRole": "audio"
    }
  },
  {
    "id": "icon.creator.headphones.paper-01",
    "name": "Headphones",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "audio",
    "slug": "headphones",
    "renderer": "headphones",
    "order": 4,
    "intents": [
      "monitor_audio",
      "listen_audio"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "headphones",
      "listen",
      "monitor",
      "audio",
      "sound"
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
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
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
      "creator.headphones.soft",
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
    "accessibilityLabel": "Headphones creator and media paper icon",
    "description": "A reusable layered paper-style headphones icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "monitor_audio",
        "listen_audio"
      ],
      "avoidWhen": [],
      "semanticRole": "audio"
    }
  },
  {
    "id": "icon.creator.speaker.paper-01",
    "name": "Speaker",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "audio",
    "slug": "speaker",
    "renderer": "speaker",
    "order": 5,
    "intents": [
      "play_audio",
      "amplify_sound"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "speaker",
      "sound",
      "audio",
      "volume",
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
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
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
      "creator.speaker.soft",
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
    "accessibilityLabel": "Speaker creator and media paper icon",
    "description": "A reusable layered paper-style speaker icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "play_audio",
        "amplify_sound"
      ],
      "avoidWhen": [],
      "semanticRole": "audio"
    }
  },
  {
    "id": "icon.creator.image.paper-01",
    "name": "Image",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "media",
    "slug": "image",
    "renderer": "image",
    "order": 6,
    "intents": [
      "display_image",
      "select_visual"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "image",
      "photo",
      "picture",
      "visual",
      "media"
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
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
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
      "creator.image.soft",
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
    "accessibilityLabel": "Image creator and media paper icon",
    "description": "A reusable layered paper-style image icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "display_image",
        "select_visual"
      ],
      "avoidWhen": [],
      "semanticRole": "media"
    }
  },
  {
    "id": "icon.creator.photo-gallery.paper-01",
    "name": "Photo gallery",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "media",
    "slug": "photo-gallery",
    "renderer": "photo-gallery",
    "order": 7,
    "intents": [
      "browse_images",
      "show_gallery"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "gallery",
      "photos",
      "images",
      "collection",
      "media"
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
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
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
      "creator.photo-gallery.soft",
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
    "accessibilityLabel": "Photo gallery creator and media paper icon",
    "description": "A reusable layered paper-style photo gallery icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "browse_images",
        "show_gallery"
      ],
      "avoidWhen": [],
      "semanticRole": "media"
    }
  },
  {
    "id": "icon.creator.video.paper-01",
    "name": "Video",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "media",
    "slug": "video",
    "renderer": "video",
    "order": 8,
    "intents": [
      "play_video",
      "represent_video"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "video",
      "play",
      "media",
      "clip",
      "content"
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
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
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
      "creator.video.soft",
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
    "accessibilityLabel": "Video creator and media paper icon",
    "description": "A reusable layered paper-style video icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "play_video",
        "represent_video"
      ],
      "avoidWhen": [],
      "semanticRole": "media"
    }
  },
  {
    "id": "icon.creator.audio-waveform.paper-01",
    "name": "Audio waveform",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "audio",
    "slug": "audio-waveform",
    "renderer": "audio-waveform",
    "order": 9,
    "intents": [
      "visualize_audio",
      "edit_audio"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "waveform",
      "audio",
      "sound",
      "timeline",
      "levels"
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
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
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
      "creator.audio-waveform.soft",
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
    "accessibilityLabel": "Audio waveform creator and media paper icon",
    "description": "A reusable layered paper-style audio waveform icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "visualize_audio",
        "edit_audio"
      ],
      "avoidWhen": [],
      "semanticRole": "audio"
    }
  },
  {
    "id": "icon.creator.music-note.paper-01",
    "name": "Music note",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "audio",
    "slug": "music-note",
    "renderer": "music-note",
    "order": 10,
    "intents": [
      "add_music",
      "represent_music"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "music",
      "note",
      "audio",
      "song",
      "sound"
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
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
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
      "creator.music-note.soft",
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
    "accessibilityLabel": "Music note creator and media paper icon",
    "description": "A reusable layered paper-style music note icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "add_music",
        "represent_music"
      ],
      "avoidWhen": [],
      "semanticRole": "audio"
    }
  },
  {
    "id": "icon.creator.script.paper-01",
    "name": "Script",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "planning",
    "slug": "script",
    "renderer": "script",
    "order": 11,
    "intents": [
      "write_script",
      "prepare_narrative"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "script",
      "writing",
      "document",
      "story",
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
        "maxCharacters": 56
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
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
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
      "creator.script.soft",
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
    "accessibilityLabel": "Script creator and media paper icon",
    "description": "A reusable layered paper-style script icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "write_script",
        "prepare_narrative"
      ],
      "avoidWhen": [],
      "semanticRole": "planning"
    }
  },
  {
    "id": "icon.creator.storyboard.paper-01",
    "name": "Storyboard",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "planning",
    "slug": "storyboard",
    "renderer": "storyboard",
    "order": 12,
    "intents": [
      "plan_scenes",
      "arrange_story"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "storyboard",
      "scenes",
      "planning",
      "cards",
      "video"
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
          "cut-paper-pop",
          "drop-and-settle"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
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
      "creator.storyboard.soft",
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
    "accessibilityLabel": "Storyboard creator and media paper icon",
    "description": "A reusable layered paper-style storyboard icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "plan_scenes",
        "arrange_story"
      ],
      "avoidWhen": [],
      "semanticRole": "planning"
    }
  },
  {
    "id": "icon.creator.timeline.paper-01",
    "name": "Timeline",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "production",
    "slug": "timeline",
    "renderer": "timeline",
    "order": 13,
    "intents": [
      "edit_timeline",
      "sequence_media"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "timeline",
      "edit",
      "sequence",
      "playhead",
      "media"
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
          "cut-paper-pop",
          "drop-and-settle"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
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
      "creator.timeline.soft",
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
    "accessibilityLabel": "Timeline creator and media paper icon",
    "description": "A reusable layered paper-style timeline icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "edit_timeline",
        "sequence_media"
      ],
      "avoidWhen": [],
      "semanticRole": "production"
    }
  },
  {
    "id": "icon.creator.caption.paper-01",
    "name": "Caption",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "text",
    "slug": "caption",
    "renderer": "caption",
    "order": 14,
    "intents": [
      "add_caption",
      "show_caption"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "caption",
      "text",
      "speech",
      "accessibility",
      "video"
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
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
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
      "creator.caption.soft",
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
    "accessibilityLabel": "Caption creator and media paper icon",
    "description": "A reusable layered paper-style caption icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "add_caption",
        "show_caption"
      ],
      "avoidWhen": [],
      "semanticRole": "text"
    }
  },
  {
    "id": "icon.creator.subtitle.paper-01",
    "name": "Subtitle",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "text",
    "slug": "subtitle",
    "renderer": "subtitle",
    "order": 15,
    "intents": [
      "add_subtitles",
      "translate_dialogue"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "subtitle",
      "caption",
      "language",
      "video",
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
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
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
      "creator.subtitle.soft",
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
    "accessibilityLabel": "Subtitle creator and media paper icon",
    "description": "A reusable layered paper-style subtitle icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "add_subtitles",
        "translate_dialogue"
      ],
      "avoidWhen": [],
      "semanticRole": "text"
    }
  },
  {
    "id": "icon.creator.text.paper-01",
    "name": "Text",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "text",
    "slug": "text",
    "renderer": "text",
    "order": 16,
    "intents": [
      "add_text",
      "edit_copy"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "text",
      "type",
      "copy",
      "words",
      "content"
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
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
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
      "creator.text.soft",
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
    "accessibilityLabel": "Text creator and media paper icon",
    "description": "A reusable layered paper-style text icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "add_text",
        "edit_copy"
      ],
      "avoidWhen": [],
      "semanticRole": "text"
    }
  },
  {
    "id": "icon.creator.font.paper-01",
    "name": "Font",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "text",
    "slug": "font",
    "renderer": "font",
    "order": 17,
    "intents": [
      "choose_font",
      "style_typography"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "font",
      "typography",
      "letters",
      "typeface",
      "design"
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
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
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
      "creator.font.soft",
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
    "accessibilityLabel": "Font creator and media paper icon",
    "description": "A reusable layered paper-style font icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "choose_font",
        "style_typography"
      ],
      "avoidWhen": [],
      "semanticRole": "text"
    }
  },
  {
    "id": "icon.creator.colour-palette.paper-01",
    "name": "Colour palette",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "design",
    "slug": "colour-palette",
    "renderer": "colour-palette",
    "order": 18,
    "intents": [
      "choose_colours",
      "apply_brand_theme"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "colour",
      "palette",
      "brand",
      "design",
      "theme"
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
          "cut-paper-pop",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "unfold",
      "cut-paper-pop",
      "scale-bounce"
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
      "creator.colour-palette.soft",
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
    "accessibilityLabel": "Colour palette creator and media paper icon",
    "description": "A reusable layered paper-style colour palette icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "choose_colours",
        "apply_brand_theme"
      ],
      "avoidWhen": [],
      "semanticRole": "design"
    }
  },
  {
    "id": "icon.creator.crop.paper-01",
    "name": "Crop",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "editing",
    "slug": "crop",
    "renderer": "crop",
    "order": 19,
    "intents": [
      "crop_media",
      "reframe_visual"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "crop",
      "frame",
      "image",
      "resize",
      "edit"
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
          "unfold",
          "cut-paper-pop",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "unfold",
      "cut-paper-pop",
      "scale-bounce"
    ],
    "defaultMotion": "unfold",
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
      "creator.crop.soft",
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
    "accessibilityLabel": "Crop creator and media paper icon",
    "description": "A reusable layered paper-style crop icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "crop_media",
        "reframe_visual"
      ],
      "avoidWhen": [],
      "semanticRole": "editing"
    }
  },
  {
    "id": "icon.creator.resize.paper-01",
    "name": "Resize",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "editing",
    "slug": "resize",
    "renderer": "resize",
    "order": 20,
    "intents": [
      "resize_media",
      "change_dimensions"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "resize",
      "scale",
      "dimensions",
      "edit",
      "frame"
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
          "cut-paper-pop",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "unfold",
      "cut-paper-pop",
      "scale-bounce"
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
      "creator.resize.soft",
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
    "accessibilityLabel": "Resize creator and media paper icon",
    "description": "A reusable layered paper-style resize icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "resize_media",
        "change_dimensions"
      ],
      "avoidWhen": [],
      "semanticRole": "editing"
    }
  },
  {
    "id": "icon.creator.layers.paper-01",
    "name": "Layers",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "editing",
    "slug": "layers",
    "renderer": "layers",
    "order": 21,
    "intents": [
      "manage_layers",
      "stack_elements"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "layers",
      "stack",
      "design",
      "composition",
      "edit"
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
          "unfold",
          "cut-paper-pop",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "unfold",
      "cut-paper-pop",
      "scale-bounce"
    ],
    "defaultMotion": "unfold",
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
      "creator.layers.soft",
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
    "accessibilityLabel": "Layers creator and media paper icon",
    "description": "A reusable layered paper-style layers icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "manage_layers",
        "stack_elements"
      ],
      "avoidWhen": [],
      "semanticRole": "editing"
    }
  },
  {
    "id": "icon.creator.mask.paper-01",
    "name": "Mask",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "editing",
    "slug": "mask",
    "renderer": "mask",
    "order": 22,
    "intents": [
      "mask_media",
      "reveal_area"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "mask",
      "clip",
      "shape",
      "reveal",
      "edit"
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
          "cut-paper-pop",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "unfold",
      "cut-paper-pop",
      "scale-bounce"
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
      "creator.mask.soft",
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
    "accessibilityLabel": "Mask creator and media paper icon",
    "description": "A reusable layered paper-style mask icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "mask_media",
        "reveal_area"
      ],
      "avoidWhen": [],
      "semanticRole": "editing"
    }
  },
  {
    "id": "icon.creator.effects.paper-01",
    "name": "Effects",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "editing",
    "slug": "effects",
    "renderer": "effects",
    "order": 23,
    "intents": [
      "add_effects",
      "enhance_media"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "effects",
      "sparkle",
      "filter",
      "enhance",
      "edit"
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
          "cut-paper-pop",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "unfold",
      "cut-paper-pop",
      "scale-bounce"
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
      "creator.effects.soft",
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
    "accessibilityLabel": "Effects creator and media paper icon",
    "description": "A reusable layered paper-style effects icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "add_effects",
        "enhance_media"
      ],
      "avoidWhen": [],
      "semanticRole": "editing"
    }
  },
  {
    "id": "icon.creator.transition.paper-01",
    "name": "Transition",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "editing",
    "slug": "transition",
    "renderer": "transition",
    "order": 24,
    "intents": [
      "add_transition",
      "change_scene"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "transition",
      "wipe",
      "scene",
      "edit",
      "video"
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
          "unfold",
          "cut-paper-pop",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "unfold",
      "cut-paper-pop",
      "scale-bounce"
    ],
    "defaultMotion": "unfold",
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
      "creator.transition.soft",
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
    "accessibilityLabel": "Transition creator and media paper icon",
    "description": "A reusable layered paper-style transition icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "add_transition",
        "change_scene"
      ],
      "avoidWhen": [],
      "semanticRole": "editing"
    }
  },
  {
    "id": "icon.creator.animation.paper-01",
    "name": "Animation",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "production",
    "slug": "animation",
    "renderer": "animation",
    "order": 25,
    "intents": [
      "animate_element",
      "create_motion"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "animation",
      "motion",
      "keyframe",
      "move",
      "creator"
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
          "cut-paper-pop",
          "drop-and-settle"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
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
      "creator.animation.soft",
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
    "accessibilityLabel": "Animation creator and media paper icon",
    "description": "A reusable layered paper-style animation icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "animate_element",
        "create_motion"
      ],
      "avoidWhen": [],
      "semanticRole": "production"
    }
  },
  {
    "id": "icon.creator.render.paper-01",
    "name": "Render",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "production",
    "slug": "render",
    "renderer": "render",
    "order": 26,
    "intents": [
      "render_video",
      "process_output"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "render",
      "progress",
      "process",
      "video",
      "export"
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
          "cut-paper-pop",
          "drop-and-settle"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
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
      "creator.render.soft",
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
    "accessibilityLabel": "Render creator and media paper icon",
    "description": "A reusable layered paper-style render icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "render_video",
        "process_output"
      ],
      "avoidWhen": [],
      "semanticRole": "production"
    }
  },
  {
    "id": "icon.creator.export.paper-01",
    "name": "Export",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "production",
    "slug": "export",
    "renderer": "export",
    "order": 27,
    "intents": [
      "export_media",
      "deliver_file"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "export",
      "output",
      "download",
      "file",
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
          "paper-slide",
          "cut-paper-pop",
          "drop-and-settle"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
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
      "creator.export.soft",
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
    "accessibilityLabel": "Export creator and media paper icon",
    "description": "A reusable layered paper-style export icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "export_media",
        "deliver_file"
      ],
      "avoidWhen": [],
      "semanticRole": "production"
    }
  },
  {
    "id": "icon.creator.livestream.paper-01",
    "name": "Livestream",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "publishing",
    "slug": "livestream",
    "renderer": "livestream",
    "order": 28,
    "intents": [
      "start_livestream",
      "broadcast_live"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "live",
      "stream",
      "broadcast",
      "signal",
      "creator"
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
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "stamp-impact",
      "paper-slide",
      "scale-bounce"
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
      "creator.livestream.soft",
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
    "accessibilityLabel": "Livestream creator and media paper icon",
    "description": "A reusable layered paper-style livestream icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "start_livestream",
        "broadcast_live"
      ],
      "avoidWhen": [],
      "semanticRole": "publishing"
    }
  },
  {
    "id": "icon.creator.podcast.paper-01",
    "name": "Podcast",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "publishing",
    "slug": "podcast",
    "renderer": "podcast",
    "order": 29,
    "intents": [
      "publish_podcast",
      "record_episode"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "podcast",
      "audio",
      "episode",
      "microphone",
      "creator"
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
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "stamp-impact",
      "paper-slide",
      "scale-bounce"
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
      "creator.podcast.soft",
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
    "accessibilityLabel": "Podcast creator and media paper icon",
    "description": "A reusable layered paper-style podcast icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "publish_podcast",
        "record_episode"
      ],
      "avoidWhen": [],
      "semanticRole": "publishing"
    }
  },
  {
    "id": "icon.creator.newsletter.paper-01",
    "name": "Newsletter",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "publishing",
    "slug": "newsletter",
    "renderer": "newsletter",
    "order": 30,
    "intents": [
      "publish_newsletter",
      "email_audience"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "newsletter",
      "email",
      "publish",
      "audience",
      "creator"
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
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "stamp-impact",
      "paper-slide",
      "scale-bounce"
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
      "creator.newsletter.soft",
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
    "accessibilityLabel": "Newsletter creator and media paper icon",
    "description": "A reusable layered paper-style newsletter icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "publish_newsletter",
        "email_audience"
      ],
      "avoidWhen": [],
      "semanticRole": "publishing"
    }
  },
  {
    "id": "icon.creator.blog.paper-01",
    "name": "Blog",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "publishing",
    "slug": "blog",
    "renderer": "blog",
    "order": 31,
    "intents": [
      "publish_blog",
      "write_post"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "blog",
      "website",
      "post",
      "writing",
      "creator"
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
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "stamp-impact",
      "paper-slide",
      "scale-bounce"
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
      "creator.blog.soft",
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
    "accessibilityLabel": "Blog creator and media paper icon",
    "description": "A reusable layered paper-style blog icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "publish_blog",
        "write_post"
      ],
      "avoidWhen": [],
      "semanticRole": "publishing"
    }
  },
  {
    "id": "icon.creator.article.paper-01",
    "name": "Article",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "publishing",
    "slug": "article",
    "renderer": "article",
    "order": 32,
    "intents": [
      "publish_article",
      "write_article"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "article",
      "writing",
      "editorial",
      "document",
      "creator"
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
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "stamp-impact",
      "paper-slide",
      "scale-bounce"
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
      "creator.article.soft",
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
    "accessibilityLabel": "Article creator and media paper icon",
    "description": "A reusable layered paper-style article icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "publish_article",
        "write_article"
      ],
      "avoidWhen": [],
      "semanticRole": "publishing"
    }
  },
  {
    "id": "icon.creator.reel.paper-01",
    "name": "Reel",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "publishing",
    "slug": "reel",
    "renderer": "reel",
    "order": 33,
    "intents": [
      "create_reel",
      "publish_short_video"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "reel",
      "vertical",
      "short",
      "video",
      "social"
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
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "stamp-impact",
      "paper-slide",
      "scale-bounce"
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
      "creator.reel.soft",
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
    "accessibilityLabel": "Reel creator and media paper icon",
    "description": "A reusable layered paper-style reel icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "create_reel",
        "publish_short_video"
      ],
      "avoidWhen": [],
      "semanticRole": "publishing"
    }
  },
  {
    "id": "icon.creator.short-video.paper-01",
    "name": "Short video",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "publishing",
    "slug": "short-video",
    "renderer": "short-video",
    "order": 34,
    "intents": [
      "create_short_video",
      "publish_vertical_video"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "short",
      "video",
      "vertical",
      "clip",
      "social"
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
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "stamp-impact",
      "paper-slide",
      "scale-bounce"
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
      "creator.short-video.soft",
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
    "accessibilityLabel": "Short video creator and media paper icon",
    "description": "A reusable layered paper-style short video icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "create_short_video",
        "publish_vertical_video"
      ],
      "avoidWhen": [],
      "semanticRole": "publishing"
    }
  },
  {
    "id": "icon.creator.long-form-video.paper-01",
    "name": "Long-form video",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "publishing",
    "slug": "long-form-video",
    "renderer": "long-form-video",
    "order": 35,
    "intents": [
      "create_long_video",
      "publish_long_video"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "long",
      "video",
      "landscape",
      "episode",
      "content"
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
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "stamp-impact",
      "paper-slide",
      "scale-bounce"
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
      "creator.long-form-video.soft",
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
    "accessibilityLabel": "Long-form video creator and media paper icon",
    "description": "A reusable layered paper-style long-form video icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "create_long_video",
        "publish_long_video"
      ],
      "avoidWhen": [],
      "semanticRole": "publishing"
    }
  },
  {
    "id": "icon.creator.carousel.paper-01",
    "name": "Carousel",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "publishing",
    "slug": "carousel",
    "renderer": "carousel",
    "order": 36,
    "intents": [
      "create_carousel",
      "show_multiple_slides"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "carousel",
      "slides",
      "swipe",
      "social",
      "post"
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
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "stamp-impact",
      "paper-slide",
      "scale-bounce"
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
      "creator.carousel.soft",
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
    "accessibilityLabel": "Carousel creator and media paper icon",
    "description": "A reusable layered paper-style carousel icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "create_carousel",
        "show_multiple_slides"
      ],
      "avoidWhen": [],
      "semanticRole": "publishing"
    }
  },
  {
    "id": "icon.creator.thumbnail.paper-01",
    "name": "Thumbnail",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "design",
    "slug": "thumbnail",
    "renderer": "thumbnail",
    "order": 37,
    "intents": [
      "design_thumbnail",
      "select_cover"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "thumbnail",
      "cover",
      "preview",
      "video",
      "image"
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
          "unfold",
          "cut-paper-pop",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "unfold",
      "cut-paper-pop",
      "scale-bounce"
    ],
    "defaultMotion": "unfold",
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
      "creator.thumbnail.soft",
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
    "accessibilityLabel": "Thumbnail creator and media paper icon",
    "description": "A reusable layered paper-style thumbnail icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "design_thumbnail",
        "select_cover"
      ],
      "avoidWhen": [],
      "semanticRole": "design"
    }
  },
  {
    "id": "icon.creator.social-post.paper-01",
    "name": "Social post",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "publishing",
    "slug": "social-post",
    "renderer": "social-post",
    "order": 38,
    "intents": [
      "publish_social_post",
      "represent_post"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "social",
      "post",
      "feed",
      "content",
      "creator"
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
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "stamp-impact",
      "paper-slide",
      "scale-bounce"
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
      "creator.social-post.soft",
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
    "accessibilityLabel": "Social post creator and media paper icon",
    "description": "A reusable layered paper-style social post icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "publish_social_post",
        "represent_post"
      ],
      "avoidWhen": [],
      "semanticRole": "publishing"
    }
  },
  {
    "id": "icon.creator.comment.paper-01",
    "name": "Comment",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "engagement",
    "slug": "comment",
    "renderer": "comment",
    "order": 39,
    "intents": [
      "add_comment",
      "show_discussion"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "comment",
      "reply",
      "discussion",
      "social",
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
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
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
      "creator.comment.soft",
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
    "accessibilityLabel": "Comment creator and media paper icon",
    "description": "A reusable layered paper-style comment icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "add_comment",
        "show_discussion"
      ],
      "avoidWhen": [],
      "semanticRole": "engagement"
    }
  },
  {
    "id": "icon.creator.reaction.paper-01",
    "name": "Reaction",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "engagement",
    "slug": "reaction",
    "renderer": "reaction",
    "order": 40,
    "intents": [
      "react_to_content",
      "show_reaction"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "reaction",
      "emoji",
      "engagement",
      "social",
      "response"
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
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
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
      "creator.reaction.soft",
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
    "accessibilityLabel": "Reaction creator and media paper icon",
    "description": "A reusable layered paper-style reaction icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "react_to_content",
        "show_reaction"
      ],
      "avoidWhen": [],
      "semanticRole": "engagement"
    }
  },
  {
    "id": "icon.creator.like.paper-01",
    "name": "Like",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "engagement",
    "slug": "like",
    "renderer": "like",
    "order": 41,
    "intents": [
      "like_content",
      "show_approval"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "like",
      "thumb",
      "approval",
      "social",
      "engagement"
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
          "scale-bounce",
          "paper-slide"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
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
      "creator.like.soft",
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
    "accessibilityLabel": "Like creator and media paper icon",
    "description": "A reusable layered paper-style like icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "like_content",
        "show_approval"
      ],
      "avoidWhen": [],
      "semanticRole": "engagement"
    }
  },
  {
    "id": "icon.creator.subscriber.paper-01",
    "name": "Subscriber",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "analytics",
    "slug": "subscriber",
    "renderer": "subscriber",
    "order": 42,
    "intents": [
      "show_subscriber_count",
      "grow_audience"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "subscriber",
      "audience",
      "count",
      "growth",
      "creator"
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
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "stamp-impact",
      "paper-slide",
      "scale-bounce"
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
      "creator.subscriber.soft",
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
    "accessibilityLabel": "Subscriber creator and media paper icon",
    "description": "A reusable layered paper-style subscriber icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "show_subscriber_count",
        "grow_audience"
      ],
      "avoidWhen": [],
      "semanticRole": "analytics"
    }
  },
  {
    "id": "icon.creator.view-count.paper-01",
    "name": "View count",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "analytics",
    "slug": "view-count",
    "renderer": "view-count",
    "order": 43,
    "intents": [
      "show_view_count",
      "measure_reach"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "views",
      "count",
      "eye",
      "reach",
      "analytics"
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
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "stamp-impact",
      "paper-slide",
      "scale-bounce"
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
      "creator.view-count.soft",
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
    "accessibilityLabel": "View count creator and media paper icon",
    "description": "A reusable layered paper-style view count icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "show_view_count",
        "measure_reach"
      ],
      "avoidWhen": [],
      "semanticRole": "analytics"
    }
  },
  {
    "id": "icon.creator.analytics.paper-01",
    "name": "Analytics",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "analytics",
    "slug": "analytics",
    "renderer": "analytics",
    "order": 44,
    "intents": [
      "show_analytics",
      "measure_performance"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "analytics",
      "chart",
      "growth",
      "performance",
      "data"
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
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "stamp-impact",
      "paper-slide",
      "scale-bounce"
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
      "creator.analytics.soft",
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
    "accessibilityLabel": "Analytics creator and media paper icon",
    "description": "A reusable layered paper-style analytics icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "show_analytics",
        "measure_performance"
      ],
      "avoidWhen": [],
      "semanticRole": "analytics"
    }
  },
  {
    "id": "icon.creator.brand-kit.paper-01",
    "name": "Brand kit",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "design",
    "slug": "brand-kit",
    "renderer": "brand-kit",
    "order": 45,
    "intents": [
      "apply_brand_kit",
      "manage_brand_assets"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "brand",
      "kit",
      "logo",
      "colours",
      "assets"
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
          "cut-paper-pop",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "unfold",
      "cut-paper-pop",
      "scale-bounce"
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
      "creator.brand-kit.soft",
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
    "accessibilityLabel": "Brand kit creator and media paper icon",
    "description": "A reusable layered paper-style brand kit icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "apply_brand_kit",
        "manage_brand_assets"
      ],
      "avoidWhen": [],
      "semanticRole": "design"
    }
  },
  {
    "id": "icon.creator.template.paper-01",
    "name": "Template",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "design",
    "slug": "template",
    "renderer": "template",
    "order": 46,
    "intents": [
      "use_template",
      "create_from_template"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "template",
      "layout",
      "preset",
      "design",
      "creator"
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
          "cut-paper-pop",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "unfold",
      "cut-paper-pop",
      "scale-bounce"
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
      "creator.template.soft",
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
    "accessibilityLabel": "Template creator and media paper icon",
    "description": "A reusable layered paper-style template icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "use_template",
        "create_from_template"
      ],
      "avoidWhen": [],
      "semanticRole": "design"
    }
  },
  {
    "id": "icon.creator.content-calendar.paper-01",
    "name": "Content calendar",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "planning",
    "slug": "content-calendar",
    "renderer": "content-calendar",
    "order": 47,
    "intents": [
      "plan_content",
      "schedule_posts"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "calendar",
      "content",
      "schedule",
      "publish",
      "planning"
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
          "cut-paper-pop",
          "drop-and-settle"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
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
      "creator.content-calendar.soft",
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
    "accessibilityLabel": "Content calendar creator and media paper icon",
    "description": "A reusable layered paper-style content calendar icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": false,
    "agentSelection": {
      "useWhen": [
        "plan_content",
        "schedule_posts"
      ],
      "avoidWhen": [],
      "semanticRole": "planning"
    }
  },
  {
    "id": "icon.creator.publish.paper-01",
    "name": "Publish",
    "version": "1.4.0",
    "category": "icon",
    "subtype": "creator-media",
    "group": "publishing",
    "slug": "publish",
    "renderer": "publish",
    "order": 48,
    "intents": [
      "publish_content",
      "complete_release"
    ],
    "keywords": [
      "icon",
      "creator",
      "paper",
      "publish",
      "send",
      "release",
      "complete",
      "creator"
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
          "paper-slide",
          "scale-bounce"
        ]
      },
      "duration": {
        "type": "number",
        "minimum": 0.35,
        "recommended": 1.25,
        "maximum": 3.2
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
      "recommended": 1.15,
      "maximum": 3.2
    },
    "motionEnergy": [
      "low",
      "medium",
      "high"
    ],
    "compatibleMotions": [
      "stamp-impact",
      "paper-slide",
      "scale-bounce"
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
      "creator.publish.soft",
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
    "accessibilityLabel": "Publish creator and media paper icon",
    "description": "A reusable layered paper-style publish icon for creator, media-production and publishing workflows.",
    "layeredSvg": true,
    "editable": true,
    "scalable": true,
    "bespokeInternalMotion": true,
    "agentSelection": {
      "useWhen": [
        "publish_content",
        "complete_release"
      ],
      "avoidWhen": [],
      "semanticRole": "publishing"
    }
  }
];
