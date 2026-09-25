export interface DocSection { id: string; title: string; body: string[]; }
export interface Doc { slug: string; kicker: string; title: string; intro: string; updated: string; sections: DocSection[]; }

export const TERMS: Doc = {
  slug: "terms",
  kicker: "Legal",
  title: "Terms of Service.",
  intro: "The rules for using NexStudio. Written plainly because you should actually be able to read them.",
  updated: "September 2026",
  sections: [
    {
      id: "agreement",
      title: "The agreement",
      body: [
        "These terms are a contract between you and NexStudio. By creating an account, requesting a video, or using any part of the service, you accept them. If you use NexStudio on behalf of a company or another person, you confirm you have the authority to bind them, and they accept these terms through you.",
        "If you do not agree, do not use the service. That is the whole point of terms.",
      ],
    },
    {
      id: "account",
      title: "Your account",
      body: [
        "NexStudio uses email sign-in links instead of passwords. Anyone who can open your inbox can sign in, so protect your email account. Every active sign-in session is listed in your account settings, and you can revoke any of them, including the current one.",
        "You are responsible for what happens on your account. If you think someone else has access, sign out other sessions from account settings and tell us.",
        "One account per person. You must be at least 16 years old.",
      ],
    },
    {
      id: "service",
      title: "What NexStudio does",
      body: [
        "You give NexMind a brief or a script. NexMind turns a brief into a written narration, then a production direction, which you approve before anything renders. NexStudio then produces a finished video for widescreen, vertical, and square formats in the same run.",
        "You can review the result, request revisions, download the files, or take them to platforms yourself. NexStudio does not publish anything on your behalf.",
        "We may improve, change, or retire parts of the service. If a change removes something you paid for, you get a reasonable adjustment or a credit for the difference.",
      ],
    },
    {
      id: "billing",
      title: "Credits and payment",
      body: [
        "NexStudio runs on credits. You buy a pack, the balance lands in your account, and renders draw from it. Credits can show as pending while a render is in progress, then settle when it finishes.",
        "You can pay with a credit or debit card, or with USDC, where both methods are available at checkout. Prices, packs, and any promotions are shown before you pay. Payment processing is handled by our providers; we never see or store your full card number.",
        "Credits you have not spent can be refunded to the original payment method within 30 days of purchase, unless a law gives you longer. Credits already spent on completed or in-progress renders are final. If a render fails on our side, its credits come back to your balance automatically.",
        "You are responsible for any taxes that apply where you live.",
      ],
    },
    {
      id: "your-content",
      title: "What is yours",
      body: [
        "What you bring stays yours: briefs, scripts, uploads, brand material, and references. You keep every right you had.",
        "The videos NexStudio produces for you are yours too, once paid for. You can download them, publish them, sell them, or archive them. No extra license from us, no revenue share, no watermark requirement.",
        "To make the service work you grant us a limited license to store, process, and display your content and your productions, only for running and improving the service and only while your account is active.",
      ],
    },
    {
      id: "acceptable-use",
      title: "What we will not make",
      body: [
        "NexStudio refuses certain content before it is ever rendered. This is not optional and it is not negotiable. The service will not produce, and you will not ask it to produce:",
        "Content that is vulgar or obscene for the audience it could reach. Content that attacks, threatens, or defames government officials, public figures, or private individuals. Content that promotes, instructs, or assists crime, fraud, or violence.",
        "Hate or harassment of any group. Sexual content of any kind, and anything sexual involving minors under any circumstances. Content that encourages self-harm. Praise or recruitment material for extremist or violent movements.",
        "Content that reproduces copyrighted text or media you do not have rights to. False or guaranteed claims about health, law, finance, or elections. Impersonation of real people, companies, or institutions. Anything designed to deceive viewers about who made it or why.",
        "We apply this list to briefs, scripts, uploads, and generated narration, before and after writing. We can refuse a production, remove content, or suspend an account that breaks it. Where a law requires reporting, we report.",
      ],
    },
    {
      id: "ai-output",
      title: "Made by machines",
      body: [
        "NexMind writes, plans, and directs with artificial intelligence. Output can contain errors: a wrong fact, a mispronounced name, a visual that reads wrong for your audience.",
        "You approve the direction and you review the finished video. What you publish is your responsibility. Where a law or a platform requires AI-generated content to be labeled, the label is your responsibility too.",
      ],
    },
    {
      id: "memory",
      title: "NexMind memory",
      body: [
        "To keep your productions consistent, NexMind remembers things: your brand, your series continuity, your stated preferences. Everything it remembers is visible to you in Brand and Series views, and you can delete any remembered fact permanently.",
        "Memory exists to serve your productions. It is not used to profile you for advertising, and it is deleted when your account is.",
      ],
    },
    {
      id: "termination",
      title: "Leaving",
      body: [
        "You can request account deletion from your account settings at any time. We send a confirmation link to your email, and nothing is deleted until you confirm. Once confirmed, your productions, memory, sessions, and billing history are removed. Export your data first if you want a copy.",
        "We can suspend or close accounts that break the acceptable use section, fail to pay, or create risk for other users or for us. If we close your account for a breach of these terms, unspent credits are forfeited. Otherwise unspent credits are returned to the original payment method.",
      ],
    },
    {
      id: "disclaimers",
      title: "What we do not promise",
      body: [
        "The service is provided as is. We work hard to keep it fast, accurate, and available, but we do not guarantee uninterrupted operation, error-free output, or that a video will achieve any particular result for you.",
        "Nothing in the service constitutes legal, medical, financial, or professional advice.",
      ],
    },
    {
      id: "liability",
      title: "Liability",
      body: [
        "To the extent the law allows, NexStudio is not liable for indirect, incidental, or consequential losses: lost profits, lost audience, lost data that could have been exported, or the cost of a video that underperformed.",
        "Our total liability for any claim is capped at the amount you paid us in the 12 months before the claim, or 100 US dollars if you paid nothing. Some jurisdictions do not allow these limits; where they do not, they do not apply to you.",
      ],
    },
    {
      id: "changes",
      title: "Changes to these terms",
      body: [
        "We may update these terms at any time, at our discretion. The version on this page is the current one and applies from the date shown. Continued use of NexStudio after an update means you accept it.",
      ],
    },
    {
      id: "contact",
      title: "Contact",
      body: [
        "Questions about these terms: legal@nexmarkets.xyz. For anything about your account, use the account drawer in the studio first; most issues are solved there.",
      ],
    },
  ],
};

export const PRIVACY: Doc = {
  slug: "privacy",
  kicker: "Legal",
  title: "Privacy Policy.",
  intro: "What we collect, why, and how you take it back. Short enough to read, specific enough to mean something.",
  updated: "September 2026",
  sections: [
    {
      id: "collected",
      title: "What we collect",
      body: [
        "Account data: your email address and display name. There is no password; sign-in works through emailed links.",
        "Production data: briefs, scripts, uploads, generated narration, direction choices, and the finished video files.",
        "Memory: facts NexMind stores to keep your brand, series, and preferences consistent across productions. All of it is inspectable inside the studio.",
        "Session data: each active sign-in session stores a hashed token, a device description, a hashed IP, and timestamps. You can see every session and revoke any of them.",
        "Billing data: ledger entries, pack purchases, and payment status. Card numbers never touch our servers; they go straight to the payment processor.",
      ],
    },
    {
      id: "use",
      title: "How we use it",
      body: [
        "To run the service: writing your narration, resolving direction, rendering, storing your work, and keeping your sessions signed in.",
        "To keep you informed: sign-in links, receipts, export notices, and, only if you turn it on in Preferences, an email when a render finishes or when something meaningful changes in the product.",
        "To keep the service honest: rate limits, abuse detection, fraud prevention, and the content rules in our Terms.",
      ],
    },
    {
      id: "memory",
      title: "What NexMind remembers",
      body: [
        "NexMind keeps an append-only production memory: brand voice, palette, series continuity, cast notes, and things you explicitly tell it. Nothing enters memory silently; remembered facts appear in Brand and Series where you can read and tombstone them.",
        "Tombstoning a fact removes it from every future production. Deleting your account removes all of it.",
      ],
    },
    {
      id: "sharing",
      title: "Who sees it",
      body: [
        "Infrastructure providers that host the application and store your files. Payment processors that run checkout for card or USDC. The AI provider that helps NexMind write and plan, which receives the brief and context needed for the job and nothing more.",
        "Each processor receives only what its job requires and only while we use them. We do not sell, rent, or trade your data, and there are no third-party advertising cookies on NexStudio.",
        "We disclose data when the law genuinely requires it, and to you whenever you ask for it.",
      ],
    },
    {
      id: "cookies",
      title: "Cookies",
      body: [
        "One cookie keeps you signed in. It is a random token, hashed on our side, revocable from your account settings. There are no analytics cookies, ad cookies, or fingerprinting.",
      ],
    },
    {
      id: "retention",
      title: "Keeping and deleting",
      body: [
        "We keep your data while your account is active. When you request deletion, a confirmation link goes to your email; once confirmed, your productions, memory, sessions, and ledger history are deleted. Backup copies follow the normal backup cycle and disappear with it.",
        "You can export a full archive of your data from account settings before deleting, or at any time.",
      ],
    },
    {
      id: "security",
      title: "How it is protected",
      body: [
        "No passwords means nothing to phish or leak. Session tokens are stored hashed, traffic is encrypted in transit, payment webhooks are verified by signature, and account mutations are rate-limited.",
        "No system is perfect. If we ever have a breach that affects you, we tell you what happened, what it touched, and what we did about it.",
      ],
    },
    {
      id: "children",
      title: "Children",
      body: [
        "NexStudio is not for anyone under 16. If we learn an account belongs to a child, we close it and delete its data.",
      ],
    },
    {
      id: "changes",
      title: "Changes and contact",
      body: [
        "We may update this policy at any time, at our discretion. The version on this page is the current one and applies from the date shown. Continued use after an update means you accept it.",
        "Privacy questions and requests: privacy@nexmarkets.xyz.",
      ],
    },
  ],
};

export const FAQ: Doc = {
  slug: "faq",
  kicker: "Answers",
  title: "Questions, answered.",
  intro: "The things people actually ask before their first video, and after it.",
  updated: "September 2026",
  sections: [
    {
      id: "what",
      title: "What is NexStudio?",
      body: [
        "A production studio you talk to. You describe the video you want, NexMind writes the narration and the direction, you approve it, and the studio renders the finished video. No timeline, no editing software, no production skills required.",
      ],
    },
    {
      id: "how",
      title: "How does making a video actually work?",
      body: [
        "Four steps. You write a brief or paste a script. NexMind shapes it into a story and a direction you can inspect and change. You pick the style, voice, and length. Then the studio renders it while you watch the journey, stage by stage.",
        "You get the finished video in widescreen, vertical, and square in the same render. Three files, one direction.",
      ],
    },
    {
      id: "brief-vs-script",
      title: "What is the difference between a brief and a script?",
      body: [
        "A brief is the idea in your own words, and NexMind writes the narration for you. A script is finished narration you wrote, voiced and illustrated exactly as written. Toggle between them above the text box.",
      ],
    },
    {
      id: "families",
      title: "What kinds of videos can I make?",
      body: [
        "Two production families today. Explainer turns complex systems, products, and ideas into clear staged videos in five visual styles. Whiteboard draws the reasoning live, either as kinetic typography or as a hand that draws labeled diagrams in front of you.",
        "Character and Illustrated Stories are in development and marked as such. What you see in the picker is what actually renders.",
      ],
    },
    {
      id: "time",
      title: "How long does a render take?",
      body: [
        "Plan for a few minutes depending on length and style. The production view shows each stage as it happens, and your Work list updates live. If you turned on the email preference, you also get a note the moment it is ready.",
      ],
    },
    {
      id: "voices",
      title: "How do voices work?",
      body: [
        "Six neural voices across US, UK, and AU accents, each with a playable sample before you pick. Speed and length are adjustable per video. A default voice can be set once in Preferences.",
      ],
    },
    {
      id: "ownership",
      title: "Do I own the videos?",
      body: [
        "Yes, once paid for. Your briefs, scripts, and uploads remain yours, and the rendered videos are yours to download, publish, and sell. There is no revenue share and no forced watermark. Details are in the Terms.",
      ],
    },
    {
      id: "credits",
      title: "How do credits and payment work?",
      body: [
        "You buy a credit pack, renders draw from the balance, and the ledger records every movement including pending and settled amounts. Checkout accepts credit and debit cards, or USDC where that method is available.",
        "Unspent credits can be refunded within 30 days. Credits for completed or in-progress renders are final, and a failed render returns its credits automatically.",
      ],
    },
    {
      id: "limits",
      title: "What can I not make?",
      body: [
        "The Terms list it exactly, and the service enforces it before anything renders: no vulgarity, no attacks on officials or individuals, no crime promotion, no hate, no sexual content, no extremist material, no copyrighted text you do not own, no false health or financial claims, no deception.",
        "If NexMind refuses a brief, it tells you what was flagged so you can rework it.",
      ],
    },
    {
      id: "mistakes",
      title: "Does NexMind make mistakes?",
      body: [
        "Yes. It writes quickly and confidently, which is exactly why the direction stage exists: you inspect the story, the beats, and the narration before paying to render. Review the finished video the same way before you publish it.",
      ],
    },
    {
      id: "training",
      title: "Is my content used to train models?",
      body: [
        "No. Your productions, uploads, and brand material are not used to train models. NexMind memory exists only to keep your own work consistent, and you can inspect and delete every fact it stores.",
      ],
    },
    {
      id: "signin",
      title: "How do I sign in?",
      body: [
        "Enter your email and we send a link that opens your Studio directly. No password exists to forget or leak. Every active session is listed in your account, and you can revoke any device from there.",
      ],
    },
    {
      id: "data",
      title: "Can I take my data or delete my account?",
      body: [
        "Both, without asking anyone. Request a full archive from Your data in the account drawer, and request deletion from Privacy. Deletion emails a confirmation link first, then removes productions, memory, sessions, and billing history permanently.",
      ],
    },
    {
      id: "labeling",
      title: "Do I have to tell people a video is AI-made?",
      body: [
        "That depends on where you publish and which laws apply to you. Some platforms and jurisdictions require synthetic media to be labeled. The video is yours, so the decision and the responsibility sit with you.",
      ],
    },
  ],
};

export const DOCS = { terms: TERMS, privacy: PRIVACY, faq: FAQ };
