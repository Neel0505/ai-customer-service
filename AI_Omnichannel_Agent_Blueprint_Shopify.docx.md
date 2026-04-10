

**AI-POWERED OMNICHANNEL**

**CUSTOMER SERVICE & SALES AGENT**

*WhatsApp  •  Email  •  Instagram  •  Voice Calls (ElevenLabs)*

**PRODUCT BLUEPRINT**

Version 1.0  |  Confidential

*Client: \[CLIENT\_NAME\]  |  Prepared by: \[AGENCY\_NAME\]*

# **Table of Contents**

**1  Executive Summary**3

**2  Product Overview & Core Capabilities**4

**3  System Architecture**5

**4  Shopify Integration — Product & Customer Data Layer**7

  4.1  Shopify API Access Setup7

  4.2  Shopify Configuration Variables8

  4.3  Product Data Sync — RAG Knowledge Base from Shopify9

  4.4  Real-Time Shopify Tools (LLM Function Calls)10

  4.5  Order Lookup & Customer Service Flows11

  4.6  Customer Identity Resolution12

**5  Channel Deep-Dives**13

  5.1  WhatsApp Integration13

  5.2  Email Integration15

  5.3  Instagram Integration17

  5.4  Voice Calls via ElevenLabs19

**6  AI Brain: LLM Core Engine**21

**7  Sales Workflow Engine**23

**8  Customer Service Workflow Engine**24

**9  CRM & Data Layer**26

**10  Handoff & Escalation Logic**27

**11  Analytics & Reporting Dashboard**28

**12  Security, Compliance & Data Privacy**29

**13  Full Tech Stack Reference**30

**14  Client Configuration Guide**31

**15  Deployment & DevOps Blueprint**33

**16  Cost Estimation & Pricing Model**34

**17  Customization Checklist Per Client**35

# **1\. Executive Summary**

This document is a complete product blueprint for an AI-powered Omnichannel Customer Service and Sales Agent — a production-ready, white-label system that can be deployed for any business within hours. The system replaces or augments traditional customer service teams with an intelligent, always-on agent that communicates across WhatsApp, Email, Instagram Direct Messages, and inbound/outbound phone calls powered by ElevenLabs' voice synthesis.

The agent is built on a modular architecture, meaning each component — the AI brain, channel connectors, CRM sync, escalation rules, and analytics — can be independently configured per client by updating a central environment configuration file. No code changes are required between client deployments.

| 🎯  Core Business Value This product reduces customer response time from hours to seconds, handles unlimited concurrent conversations, qualifies sales leads 24/7, books appointments, answers FAQs, processes orders, escalates edge cases to humans — and does all of this across every major communication channel your clients' customers already use. |
| :---- |

## **Key Metrics This System Targets**

| Metric | Target Performance |
| :---- | :---- |
| First Response Time | \< 3 seconds on all channels |
| Resolution Rate (AI only) | 75–85% of tickets resolved without human |
| Lead Qualification Rate | Up to 3x improvement vs. unassisted |
| Availability | 24/7/365, no downtime windows |
| Concurrent Conversations | Unlimited (scales horizontally) |
| Channel Coverage | WhatsApp, Email, Instagram, Voice |
| Deployment Time Per Client | 2–4 hours with this blueprint |
| Human Escalation Accuracy | \> 90% correct escalation routing |

# **2\. Product Overview & Core Capabilities**

The AI Omnichannel Agent is a multi-channel, multi-modal AI system. At its core sits a Large Language Model (LLM) orchestration layer — the 'brain' — that maintains conversation state, understands intent, executes business logic, and generates contextually appropriate responses. Wrapped around this brain are four channel adapters (WhatsApp, Email, Instagram, Voice), a CRM integration layer, a knowledge base retrieval system (RAG), and a human handoff module.

## **Capability Matrix**

| Capability | Customer Service Mode | Sales Mode |
| :---- | :---- | :---- |
| FAQ Answering | ✅ Full | ✅ Product-focused |
| Order Status Lookup | ✅ Real-time via API | ✅ Post-sale |
| Appointment Booking | ✅ Calendar integration | ✅ Demo booking |
| Lead Qualification | Partial | ✅ Full BANT/MEDDIC |
| Price Quoting | ✅ Standard pricing | ✅ Dynamic \+ upsell |
| Complaint Handling | ✅ Primary function | Limited |
| Follow-up Sequencing | Ticketing follow-ups | ✅ Full sales cadence |
| Human Escalation | ✅ Priority routing | ✅ Hot lead routing |
| Multilingual Support | ✅ 50+ languages | ✅ 50+ languages |
| Voice (Calls) | ✅ IVR \+ live agent | ✅ Outbound SDR |
| Sentiment Analysis | ✅ Live mood detection | ✅ Buying signal detect |
| Document Sending | ✅ via Email/WhatsApp | ✅ Proposals, brochures |

## **Operational Modes**

* **Fully Autonomous Mode:** AI handles 100% of conversations until a hard escalation trigger fires.

* **Assisted Mode:** AI drafts responses and a human approves before sending.

* **Monitoring Mode:** Human handles all conversations, AI watches and suggests in real-time.

* **Hybrid Mode:** AI handles defined intent categories (FAQs, status checks) and humans handle the rest.

# **3\. System Architecture**

The system follows a microservices-inspired, event-driven architecture. Each channel adapter is a standalone service. All services communicate via a central Message Bus (Redis Pub/Sub or a queue service). The Orchestration Engine is the only service that touches the LLM and the CRM simultaneously.

## **High-Level Architecture Diagram (Text Representation)**

| 📐  Architecture Overview INBOUND LAYER (Channel Adapters)  \[WhatsApp Cloud API\] → Webhook → WhatsApp Adapter Service  \[Gmail / SMTP/IMAP\]  → Poller → Email Adapter Service  \[Instagram Graph API\]→ Webhook → Instagram Adapter Service  \[Twilio Voice / SIP\] → Stream → Voice Adapter Service (ElevenLabs STT)MESSAGE BUS (Redis / BullMQ)  All adapters publish normalized NLPMessage objects to a central queue.CORE ORCHESTRATION ENGINE  ├── Intent Classifier (LLM call \#1 — lightweight, fast)  ├── State Manager (Redis — conversation history, context window)  ├── RAG Retrieval (Pinecone / Chroma — knowledge base search)  ├── LLM Response Generator (primary model — Claude / GPT-4o / Gemini)  ├── Tool Execution Layer (CRM read/write, calendar, order API, etc.)  └── Response Router (routes back to correct channel adapter)OUTBOUND LAYER  WhatsApp Adapter → Cloud API → User's WhatsApp  Email Adapter    → SMTP     → User's Email  Instagram Adapter→ Graph API→ User's Instagram DM  Voice Adapter    → ElevenLabs TTS → Twilio → User's PhoneINTEGRATIONS  CRM (HubSpot / Salesforce / custom)  Calendar (Google Calendar / Calendly)  Order Management System  Analytics / BI (internal dashboard \+ Mixpanel / GA)  Human Handoff (Slack alert / Intercom / Zendesk ticket) |
| :---- |

## **Data Flow: Inbound Message Lifecycle**

1. User sends a message on any channel.

2. Channel Adapter receives the webhook/event, validates the signature, and normalizes the payload into a standard NLPMessage object (fields: channel, user\_id, session\_id, text, media\_urls, timestamp, raw\_payload).

3. The NLPMessage is published to the Message Bus with a channel-specific topic key.

4. The Orchestration Engine consumes the message, loads the conversation history from Redis, and runs the Intent Classifier.

5. Based on intent, the engine either: retrieves from RAG and generates a response (most common), OR executes a Tool (API call to CRM, calendar, etc.) and includes the result in context.

6. The response is formatted for the target channel (e.g., WhatsApp requires 160-char chunks, email requires HTML), published back to the Message Bus.

7. The Channel Adapter picks up the response and delivers it via the appropriate API.

8. The full conversation turn is persisted to the database and analytics events are emitted.

## **Core Data Structures**

### **NLPMessage Object**

| NLPMessage Schema {  "session\_id":     "string — unique per conversation",  "channel":        "whatsapp | email | instagram | voice",  "user\_id":        "string — platform user ID",  "contact\_id":     "string — CRM contact ID (if resolved)",  "message\_id":     "string — platform message ID",  "text":           "string — transcribed or typed content",  "media":          "\[{type, url, mime\_type}\]",  "timestamp":      "ISO 8601",  "direction":      "inbound | outbound",  "intent":         "string — classified intent label",  "sentiment":      "positive | neutral | negative | frustrated",  "escalate":       "boolean",  "tool\_calls":     "\[{name, arguments, result}\]",  "metadata":       "{} — channel-specific extra fields"} |
| :---- |

# **4\. Shopify Integration — Product & Customer Data Layer**

Shopify serves as the single source of truth for all product catalog data and customer service context. Rather than maintaining a separate product database or relying on manually curated FAQs for inventory and order information, the AI agent queries Shopify directly and in real time. This keeps the agent's knowledge perfectly synchronized with the store without any manual re-ingestion.

| 🛍️  Why Shopify as Primary Data Source Product Data: All product titles, descriptions, variants, pricing, inventory levels, tags, and metafields are pulled live from Shopify. The RAG knowledge base is seeded from Shopify product exports and kept fresh via webhooks — no manual uploads needed.Customer Service Data: Order history, fulfillment status, tracking numbers, refunds, and customer account information are fetched in real time via the Shopify Admin API. The agent can look up any order the moment a customer asks, without any separate order management system.Webhooks: Shopify pushes events (new orders, fulfillment updates, refunds, inventory changes) to the agent in real time, enabling proactive notifications and always-current context. |
| :---- |

## **4.1 Shopify API Access Setup**

The agent connects to Shopify via a Custom App installed directly in the client's Shopify Admin. This provides a stable, long-lived access token scoped to only the permissions the agent needs — no OAuth redirects or session tokens required.

### **Step-by-Step Shopify App Setup**

9. Log in to the client's Shopify Admin and go to Settings → Apps and Sales Channels → Develop Apps.

10. Click Create an App. Name it something identifiable, e.g. 'AI Agent Integration'.

11. Under API Credentials → Admin API, click Configure Admin API Scopes and grant the permissions listed in the table below.

12. Click Install App. Shopify will generate an Admin API Access Token — copy it immediately (it is shown only once).

13. Note the Store Domain (mystore.myshopify.com) and the API Version to use (always pin to a specific version, e.g. 2025-01).

14. Add these credentials to the client .env file under the SHOPIFY\_ variables.

### **Required Shopify API Scopes**

| API Scope | Why It's Needed |
| :---- | :---- |
| read\_products | Fetch product titles, descriptions, variants, pricing, images |
| read\_inventory | Real-time stock levels per variant and location |
| read\_orders | Full order details: line items, status, addresses, notes |
| write\_orders | Update order notes, tags (e.g. flag as AI-handled) |
| read\_customers | Customer profiles, order history, addresses, tags |
| write\_customers | Add notes or tags to customer records |
| read\_fulfillments | Fulfillment status and tracking information |
| write\_fulfillments | Initiate fulfillment requests if enabled |
| read\_draft\_orders | Access draft orders (quotes) |
| write\_draft\_orders | Create draft orders for custom quotes |
| read\_price\_rules | Discount codes and promotional rules |
| read\_shipping | Shipping zones, rates, policies |
| read\_returns | Return requests and their status |
| write\_returns | Create return requests on behalf of customers |
| read\_metaobjects | Custom metafields for extended product/store data |

## **4.2 Shopify Configuration Variables**

| Variable | Description |
| :---- | :---- |
| SHOPIFY\_STORE\_DOMAIN | The .myshopify.com domain (e.g. acmecorp.myshopify.com) |
| SHOPIFY\_ADMIN\_API\_TOKEN | Admin API Access Token generated from the Custom App |
| SHOPIFY\_API\_VERSION | Pinned Shopify API version (e.g. 2025-01) |
| SHOPIFY\_WEBHOOK\_SECRET | HMAC secret for validating Shopify webhook payloads |
| SHOPIFY\_STOREFRONT\_TOKEN | Storefront API token (for public product browsing, optional) |
| SHOPIFY\_LOCATION\_ID | Default location ID for inventory queries |
| SHOPIFY\_CURRENCY | Store default currency (e.g. INR, USD, AED) |
| SHOPIFY\_RETURN\_POLICY\_URL | URL to return policy page — included in refund responses |
| SHOPIFY\_TRACKING\_URL\_TEMPLATE | Carrier tracking URL template for order status responses |
| SHOPIFY\_AUTO\_TAG\_AI\_ORDERS | true | false — auto-tag AI-handled orders with 'ai-agent' |
| SHOPIFY\_DRAFT\_ORDER\_EXPIRY\_DAYS | Days before auto-expiring draft orders (default: 7\) |

## **4.3 Product Data Sync — RAG Knowledge Base from Shopify**

On initial setup, the ingestion pipeline pulls all product data from Shopify and embeds it into the vector knowledge base. This replaces the need for manually curated product FAQs. Ongoing sync is handled by webhooks.

### **Initial Ingestion Pipeline**

| Shopify → Vector DB Ingestion Flow 1\. Run: npm run shopify:ingest \-- \--store acmecorp.myshopify.com2. The ingestion script calls Shopify Admin API:   GET /admin/api/2025-01/products.json?limit=250 (paginated)3. For each product, a structured document is created:   {     "id": "shopify\_product\_7823456",     "title": "Wireless Earbuds Pro Max",     "description": "...",  // HTML-stripped     "price\_range": "₹2,499 – ₹3,299",     "variants": \[{"title": "Black / 1-pack", "sku": "WEP-BLK-1", "price": 2499, "inventory": 47}\],     "tags": \["electronics", "audio", "best-seller"\],     "vendor": "SoundCo",     "collections": \["New Arrivals", "Electronics"\],     "metafields": {"warranty": "1 year", "compatibility": "iOS, Android"}   }4. Each product is chunked (title \+ description \+ variants) and embedded using   the configured embedding model → stored in Pinecone/pgvector.5. Estimated time: \~2 minutes per 1,000 products. |
| :---- |

### **Ongoing Sync via Shopify Webhooks**

Register the following Shopify webhooks pointing to your agent's webhook ingestion endpoint. Shopify will push real-time events whenever store data changes, keeping the knowledge base and agent context always current.

| Webhook Topic | Trigger | Agent Action |
| :---- | :---- | :---- |
| products/create | New product published | Embed new product in vector DB |
| products/update | Product edited (price, description, stock) | Re-embed updated product |
| products/delete | Product deleted or unpublished | Remove from vector DB |
| inventory\_levels/update | Stock level changes | Update inventory context cache |
| orders/create | New order placed | Proactive WhatsApp/email order confirmation (if enabled) |
| orders/updated | Order modified | Update cached order context |
| orders/fulfilled | Order shipped | Send proactive tracking notification |
| orders/cancelled | Order cancelled | Update context, notify customer if needed |
| refunds/create | Refund processed | Notify customer via preferred channel |
| customers/create | New customer account | Create/sync CRM contact |
| customers/update | Customer profile updated | Sync CRM contact fields |
| price\_rules/create | New discount code | Update promotions context in RAG |

## **4.4 Real-Time Shopify Tools (LLM Function Calls)**

The following Shopify-specific tools replace the generic order/product tools in the original architecture. Each tool makes a direct Shopify Admin API call and returns structured data to the LLM context.

| Tool Name | Shopify API Call | Sample Use Case |
| :---- | :---- | :---- |
| shopify\_get\_order | GET /orders/{id}.json or search by name (\#1234) | Customer asks 'where is my order?' |
| shopify\_search\_orders\_by\_customer | GET /orders.json?email={email} | Look up all orders for a customer |
| shopify\_get\_fulfillment | GET /orders/{id}/fulfillments.json | Fetch tracking number and carrier |
| shopify\_get\_product | GET /products/{id}.json | Detailed product info, variants, pricing |
| shopify\_search\_products | GET /products.json?title={query} | Customer asks about a product by name |
| shopify\_check\_inventory | GET /inventory\_levels.json?inventory\_item\_ids={ids} | Is this item in stock? |
| shopify\_get\_customer | GET /customers/search.json?query=email:{email} | Fetch customer profile \+ history |
| shopify\_create\_draft\_order | POST /draft\_orders.json | Build a custom quote for the customer |
| shopify\_apply\_discount | GET /price\_rules.json \+ validate code | Validate discount code before checkout |
| shopify\_initiate\_return | POST /returns.json | Start a return request for an order |
| shopify\_get\_refund\_status | GET /orders/{id}/refunds.json | Check refund processing status |
| shopify\_get\_collections | GET /collections.json | Help customer browse by category |
| shopify\_get\_metafields | GET /products/{id}/metafields.json | Fetch warranty, specs, extended data |

## **4.5 Order Lookup & Customer Service Flows (Shopify-Specific)**

### **Order Status Lookup Flow**

| Order Status Conversation Flow Customer: "Where is my order?"Agent: \[calls shopify\_get\_customer to resolve identity from phone/email\]Agent: \[calls shopify\_search\_orders\_by\_customer → finds recent order \#1042\]Agent: \[calls shopify\_get\_fulfillment → gets tracking: Delhivery \#789456\]Agent: "Your order \#1042 was shipped on Feb 24th via Delhivery.        Track it here: https://delhivery.com/track/789456        Estimated delivery: Feb 27–28th. Is there anything else I can help with?"If unfulfilled:Agent: \[checks order.fulfillment\_status \= 'unfulfilled'\]Agent: "Your order \#1042 was placed on Feb 23rd and is currently being        processed in our warehouse. You'll receive a tracking link via        \[WhatsApp/email\] as soon as it ships — usually within 1 business day." |
| :---- |

### **Return & Refund Flow**

| Return Request Flow Customer: "I want to return my order"Agent: \[calls shopify\_get\_order → verifies order exists and is within return window\]IF within return policy window:Agent: \[calls shopify\_initiate\_return with line items\]Agent: "I've initiated a return for your order \#1042. You'll receive a        return shipping label at \[email\] within 2 hours. Once we receive        the item, your refund of ₹2,499 will be processed in 5–7 business days."IF outside return window:Agent: "Your order \#1042 was delivered on Feb 10th, which is outside our        \[RETURN\_POLICY\_DAYS\]-day return window. I'd like to escalate this        to our team — they may be able to assist as a goodwill exception."Agent: \[calls escalate\_to\_human with reason: 'return\_window\_exceeded'\] |
| :---- |

### **Product Recommendation Flow**

| Sales — Product Discovery Flow Customer: "I'm looking for wireless earbuds under 3000 rupees"Agent: \[calls shopify\_search\_products with query: "wireless earbuds"\]Agent: \[filters results by price \<= 3000 from returned variants\]Agent: "We have a few great options in that range:  1\. SoundWave Lite — ₹1,999 | 20hr battery, IPX4 water resistant  2\. Wireless Earbuds Pro — ₹2,499 | ANC, 30hr total, comes in 3 colors  3\. BudPro Air — ₹2,999 | Hi-Fi audio, premium case, 1yr warrantyWhich of these interests you most? I can share more details, images,or help you place an order directly."\[On WhatsApp: renders as interactive list message with product names as options\]\[On Instagram: renders as conversational text with image links\]\[On Email: renders as HTML product cards with 'Add to Cart' buttons\] |
| :---- |

## **4.6 Shopify Customer Identity Resolution**

Before the agent can look up orders or personalize responses, it must resolve the customer's identity — mapping the platform user (WhatsApp number, email, Instagram user) to a Shopify customer record and CRM contact. This happens automatically on every conversation via the following lookup chain:

15. Extract identifier from the channel (phone number from WhatsApp, email from email channel, or ask the user on Instagram/Voice).

16. Call shopify\_get\_customer with the phone or email → returns Shopify customer ID and full profile.

17. If no Shopify customer found: check CRM for a matching contact. If found in CRM, use CRM data. If not found in either, create a new CRM lead.

18. Cache the resolved identity in Redis for the duration of the session (SESSION\_IDENTITY\_TTL, default: 24 hours).

19. On subsequent turns in the same session, skip lookup and use cached identity.

| 🔐  Privacy Note on Identity Resolution WhatsApp provides the user's phone number automatically. For Instagram and Voice, the agent must ask the user for their email or order number to look up their account. Never ask for passwords or payment details. The resolved identity is stored in Redis with TTL — it is not persisted to a permanent log file. Full Shopify customer data (addresses, payment methods) is fetched fresh per request and not cached. |
| :---- |

# **5\. Channel Deep-Dives**

## **5.1 WhatsApp Integration**

WhatsApp is typically the highest-volume channel for B2C businesses in most markets. The integration uses the official Meta WhatsApp Business Cloud API (no third-party middleware required, avoiding per-message fees).

### **Technical Setup**

* **Meta Developer Account:** Create a Meta Business App at developers.facebook.com. The app must be verified for WhatsApp access.

* **WhatsApp Business Account (WABA):** Linked to a dedicated phone number. One phone number per client.

* **Webhook Registration:** Register a HTTPS webhook URL pointing to your WhatsApp Adapter Service. Meta will send all messages and status updates here.

* **Webhook Verification:** Implement the GET challenge-response verification endpoint using the WEBHOOK\_VERIFY\_TOKEN environment variable.

* **Message Signature Validation:** Every inbound webhook must have its X-Hub-Signature-256 header validated using the APP\_SECRET to prevent spoofing.

### **API Configuration Variables (per client)**

| Variable | Description |
| :---- | :---- |
| WHATSAPP\_PHONE\_NUMBER\_ID | The unique phone number ID from Meta Business dashboard |
| WHATSAPP\_ACCESS\_TOKEN | Permanent System User token — generate in Meta Business Manager |
| WHATSAPP\_WEBHOOK\_VERIFY\_TOKEN | A random secret string you define for webhook verification |
| WHATSAPP\_APP\_SECRET | App secret from Meta App Settings for signature validation |
| WHATSAPP\_BUSINESS\_ACCOUNT\_ID | WABA ID for template message access |

### **Message Types Handled**

* **Text Messages:** Standard plain text — most conversations.

* **Interactive Messages (sent by bot):** Button messages (up to 3 buttons), List messages (up to 10 options) for menu-driven flows.

* **Template Messages:** Pre-approved message templates for proactive outreach (sales follow-ups, appointment reminders). Templates must be submitted to Meta for approval before use.

* **Media Messages:** Inbound: images, documents, voice notes (transcribed via Whisper). Outbound: images, PDFs (brochures, invoices).

* **Reaction Messages:** Received and logged but not actioned unless business logic requires it.

### **WhatsApp-Specific Agent Behaviors**

* Always send a typing indicator (POST to /messages with type: 'reaction' or use read receipts) before generating a response to create a natural feel.

* Chunk long responses: WhatsApp messages over 4096 characters will fail. The adapter automatically splits at sentence boundaries.

* 24-hour rule: WhatsApp restricts businesses to only send template messages to users who haven't messaged in 24 hours. The system tracks the last inbound timestamp per user and automatically switches to template mode when needed.

* Opt-out handling: Monitor for keywords like STOP, Unsubscribe, and immediately tag user as opted\_out in CRM and stop all outbound messaging.

## **5.2 Email Integration**

Email provides rich formatting capabilities and is the primary channel for B2B interactions and formal communications. The email agent handles both inbound triage and outbound sales sequences.

### **Technical Setup Options**

| Approach | Best For |
| :---- | :---- |
| Gmail API (OAuth2) | Google Workspace clients — easiest setup |
| Microsoft Graph API (Outlook) | Microsoft 365 clients |
| IMAP/SMTP (universal) | Any email provider — most flexible |
| SendGrid Inbound Parse | High-volume routing, good for shared inboxes |
| Postmark Inbound | Reliable parsing with spam filtering |

### **Email API Configuration Variables (per client)**

| Variable | Description |
| :---- | :---- |
| EMAIL\_PROVIDER | gmail | outlook | smtp | sendgrid | postmark |
| EMAIL\_INBOUND\_ADDRESS | The address the AI monitors (e.g., support@client.com) |
| GMAIL\_CLIENT\_ID | OAuth2 client ID from Google Cloud Console |
| GMAIL\_CLIENT\_SECRET | OAuth2 client secret |
| GMAIL\_REFRESH\_TOKEN | Long-lived refresh token from OAuth flow |
| SMTP\_HOST | SMTP server hostname for sending |
| SMTP\_PORT | Usually 587 (TLS) or 465 (SSL) |
| SMTP\_USER | SMTP authentication username |
| SMTP\_PASS | SMTP authentication password |
| EMAIL\_FROM\_NAME | Display name for outbound emails (e.g., 'Sarah from Acme Support') |
| SENDGRID\_API\_KEY | If using SendGrid for outbound sending |
| SENDGRID\_INBOUND\_WEBHOOK\_SECRET | For validating inbound parse webhooks |

### **Email Agent Behaviors**

* **Thread Management:** All replies are sent within the same email thread using the correct Message-ID and In-Reply-To headers to maintain conversation grouping in email clients.

* **HTML Email Generation:** Responses are formatted as HTML emails with the client's branding (logo, colors, footer). A plain text fallback is always included.

* **Email Signature:** Dynamic signature block includes agent name (can be a human-sounding name), company name, and unsubscribe link.

* **Attachment Handling:** Inbound attachments (PDFs, images) are extracted, uploaded to storage, and their content/URLs passed to the LLM context.

* **Spam & Classification:** Auto-classify inbound emails with labels: support\_request, sales\_inquiry, complaint, invoice\_query, spam. Spam is archived automatically.

* **Out-of-Office Detection:** Detect OOO auto-replies and suppress further follow-up messages.

* **Outbound Sales Sequences:** Multi-step email drip campaigns triggered by CRM events (new lead, demo no-show, trial expiry). Each step waits for a reply; if reply received, sequence stops.

## **5.3 Instagram Integration**

Instagram Direct Messages are critical for DTC (direct-to-consumer) brands, influencer-adjacent businesses, and any client with a visual product. The integration uses the Instagram Graph API via a connected Facebook Business account.

### **Technical Setup**

* **Requirements:** Instagram Professional Account (Business or Creator) connected to a Facebook Page. The Page must be connected to a Meta Business App.

* **Permissions Required:** instagram\_basic, instagram\_manage\_messages, pages\_manage\_metadata, pages\_read\_engagement — all requested during app review.

* **Webhook Events:** Subscribe to messages, messaging\_seen, messaging\_reactions events on the Instagram-connected Page.

### **Instagram API Configuration Variables (per client)**

| Variable | Description |
| :---- | :---- |
| INSTAGRAM\_ACCESS\_TOKEN | Long-lived Page Access Token (from Meta Business Manager) |
| INSTAGRAM\_PAGE\_ID | Facebook Page ID connected to the Instagram account |
| INSTAGRAM\_APP\_SECRET | App secret for webhook signature validation |
| INSTAGRAM\_WEBHOOK\_VERIFY\_TOKEN | Random secret for webhook challenge verification |
| INSTAGRAM\_ACCOUNT\_ID | Instagram Business Account ID |

### **Instagram-Specific Considerations**

* **Story Mentions:** When a user mentions the business account in their Story, the system receives a webhook event. The AI can auto-reply with a DM acknowledging the mention.

* **Post Comment DMs:** Users who comment on posts with trigger keywords (e.g., 'price?', 'interested', 'info') can be automatically DMed with a product link or menu.

* **Human Agent Indicator:** The Instagram API has a human\_agent message tag that allows 7-day reply windows (vs. 24 hours normally). Tag escalated conversations with this.

* **Image Context:** If a user sends an image in DM, pass it to the vision-capable LLM for context (useful for product identification, returns, etc.).

* **Emoji-First Tone:** Instagram users expect casual, emoji-rich responses. The agent's system prompt for Instagram should include tone instructions reflecting this.

| ⚠️  Instagram Limitation Note Instagram does not support template messages like WhatsApp. All proactive DMs must be replies to a user-initiated interaction within the messaging window. Plan your engagement flows accordingly — use Comments automation to trigger DM conversations rather than cold outbound DMs. |
| :---- |

## **5.4 Voice Calls via ElevenLabs**

The voice channel transforms the AI agent into a fully conversational phone agent. Using ElevenLabs for text-to-speech synthesis and a speech-to-text model for transcription, the agent can conduct natural-sounding phone conversations for inbound support, outbound sales calls, and appointment reminders.

### **Technical Stack for Voice**

| Component | Technology |
| :---- | :---- |
| Phone Number & Call Routing | Twilio Voice (or Vonage) |
| Speech-to-Text (STT) | OpenAI Whisper (via Twilio Media Streams) or Deepgram |
| Text-to-Speech (TTS) | ElevenLabs API — custom voice cloning supported |
| Real-time Audio Streaming | Twilio Media Streams (WebSocket bidirectional audio) |
| Conversation AI | Same Orchestration Engine — voice-optimized prompts |
| Call Recording & Transcription | Twilio Call Recording \+ async Whisper transcription |
| DTMF / IVR Menu | Twilio TwiML for menu routing before agent handoff |

### **Voice API Configuration Variables (per client)**

| Variable | Description |
| :---- | :---- |
| ELEVENLABS\_API\_KEY | ElevenLabs API key from the dashboard |
| ELEVENLABS\_VOICE\_ID | ID of the selected or cloned voice for the agent |
| ELEVENLABS\_MODEL\_ID | eleven\_turbo\_v2 (lowest latency) or eleven\_multilingual\_v2 |
| ELEVENLABS\_STABILITY | Voice stability (0.0–1.0, recommend 0.5) |
| ELEVENLABS\_SIMILARITY\_BOOST | Voice similarity boost (0.0–1.0, recommend 0.75) |
| TWILIO\_ACCOUNT\_SID | Twilio account SID |
| TWILIO\_AUTH\_TOKEN | Twilio auth token |
| TWILIO\_PHONE\_NUMBER | The purchased Twilio phone number for inbound/outbound |
| DEEPGRAM\_API\_KEY | If using Deepgram instead of Whisper for real-time STT |
| CALL\_RECORDING\_ENABLED | true | false — enable/disable call recording |
| OUTBOUND\_CALLS\_ENABLED | true | false — toggle outbound dialer |

### **Voice Agent Architecture (Real-time)**

| 🎙️  Real-time Voice Call Flow 1\. Inbound call hits Twilio number.2. Twilio executes a TwiML app: plays greeting, optionally presents IVR menu.3. Based on menu selection (or direct), Twilio opens a Media Stream WebSocket to the Voice Adapter.4. Voice Adapter receives raw audio (mulaw 8kHz) in 200ms chunks.5. Audio chunks are buffered and sent to Deepgram/Whisper for real-time STT.6. Transcription results (with end-of-utterance detection) are passed to the Orchestration Engine.7. The Orchestration Engine processes the text, generates a response (shorter, conversational).8. Response text is sent to ElevenLabs TTS API → returns audio stream.9. Audio is converted to mulaw 8kHz and sent back through the WebSocket to Twilio.10. Twilio plays the audio to the caller — latency target: \< 1.5 seconds end-to-end.11. If escalation triggers, Twilio call is transferred to a human agent number via Dial verb. |
| :---- |

### **Voice-Specific Agent Design Rules**

* **Response Length:** Voice responses must be under 50 words per turn. The LLM system prompt for voice enforces this explicitly.

* **Filler Words:** Include 'Mhm', 'Got it', 'Sure, let me check that' etc. in response generation to sound natural during processing pauses.

* **Barge-In Handling:** Implement voice activity detection (VAD) to allow callers to interrupt the agent mid-sentence — stop TTS playback immediately.

* **Silence Detection:** After 5 seconds of silence, prompt: 'Are you still there?' After 10 seconds, gracefully close the call.

* **PII Handling:** Never speak sensitive data like full credit card numbers or passwords aloud. Use masking.

# **6\. AI Brain: LLM Core Engine**

The LLM Core Engine is the most critical component of the system. It manages all aspects of natural language understanding, response generation, tool use, and conversation quality. The architecture is model-agnostic — it can work with OpenAI GPT-4o, Anthropic Claude, Google Gemini, or any OpenAI-compatible API. The client-specific model is set via environment variable.

## **LLM Configuration Variables**

| Variable | Description |
| :---- | :---- |
| LLM\_PROVIDER | openai | anthropic | google | groq | custom |
| LLM\_MODEL | e.g., gpt-4o, claude-3-5-sonnet-20241022, gemini-2.0-flash |
| LLM\_API\_KEY | API key for the chosen LLM provider |
| LLM\_API\_BASE\_URL | Override for custom or proxy endpoints |
| LLM\_MAX\_TOKENS | Max tokens per response (recommend 1024–2048) |
| LLM\_TEMPERATURE | Creativity — 0.2 for support, 0.5 for sales |
| LLM\_FAST\_MODEL | Lightweight model for intent classification |
| LLM\_FAST\_MODEL\_API\_KEY | API key for the fast model (can be same as above) |
| EMBEDDING\_MODEL | text-embedding-3-small or equivalent for RAG |
| EMBEDDING\_API\_KEY | API key for embedding model |

## **Prompt Architecture**

Every LLM call is composed of three prompt layers that are assembled dynamically at runtime:

### **Layer 1 — System Prompt (Static, Per Client)**

| System Prompt Template You are \[AGENT\_NAME\], an AI assistant for \[COMPANY\_NAME\].\[COMPANY\_DESCRIPTION\]Your role: \[customer service | sales | both\]Channel: \[whatsapp | email | instagram | voice\] — adapt your tone accordingly.Language: Respond in the same language the user writes in unless instructed otherwise.Tone: \[TONE\_DESCRIPTION — e.g., professional and warm / casual and friendly\]Critical rules:- Never claim to be human unless directly and sincerely asked.- Never make up information. If unsure, say so and offer to connect the user with a team member.- Do not discuss competitors.- All pricing must come from the product catalog tool — never quote from memory.- If the user is angry or upset, acknowledge their frustration before attempting to resolve.- If a conversation requires human intervention, trigger the escalation tool immediately.\[BUSINESS\_SPECIFIC\_RULES\] |
| :---- |

### **Layer 2 — RAG Context (Dynamic, Per Message)**

Before each LLM call, the system performs a semantic search against the client's knowledge base vector store. The top-3 to top-5 most relevant chunks are injected into the prompt as context. The knowledge base is built from:

* FAQ documents (Word, PDF, Google Docs)

* Product/service catalog (JSON, CSV, or scraped from website)

* Company policies (return policy, shipping, warranties)

* Past resolved tickets (anonymized, used to demonstrate resolution patterns)

* Pricing tables

### **Layer 3 — Conversation History (Dynamic)**

The last N turns of the conversation are injected as the messages array. N is determined by available context window space after the system prompt and RAG context are filled. A summarization step compresses very long conversations: if history exceeds 8000 tokens, older turns are summarized into a single paragraph.

## **Tool/Function Calling**

The LLM is given a set of tools (OpenAI function calling format) that it can invoke to take real-world actions:

| Tool Name | Function | Required Config |
| :---- | :---- | :---- |
| search\_knowledge\_base | Semantic search of RAG store (seeded from Shopify) | VECTOR\_DB\_URL, VECTOR\_DB\_API\_KEY |
| shopify\_get\_order | Fetch order from Shopify Admin API by ID or number | SHOPIFY\_ADMIN\_API\_TOKEN, SHOPIFY\_STORE\_DOMAIN |
| shopify\_search\_orders\_by\_customer | Find all orders for a customer by email/phone | SHOPIFY\_ADMIN\_API\_TOKEN |
| shopify\_get\_fulfillment | Get tracking info for an order's shipment | SHOPIFY\_ADMIN\_API\_TOKEN |
| shopify\_search\_products | Query Shopify product catalog with filters | SHOPIFY\_ADMIN\_API\_TOKEN |
| shopify\_check\_inventory | Real-time stock check per variant | SHOPIFY\_ADMIN\_API\_TOKEN, SHOPIFY\_LOCATION\_ID |
| shopify\_initiate\_return | Create a Shopify return request for a customer | SHOPIFY\_ADMIN\_API\_TOKEN |
| shopify\_create\_draft\_order | Build a draft order / custom quote in Shopify | SHOPIFY\_ADMIN\_API\_TOKEN |
| shopify\_get\_customer | Fetch Shopify customer profile and order history | SHOPIFY\_ADMIN\_API\_TOKEN |
| create\_crm\_contact | Create/update CRM contact | CRM\_PROVIDER, CRM\_API\_KEY |
| log\_crm\_activity | Log conversation to CRM deal/contact | CRM\_PROVIDER, CRM\_API\_KEY |
| book\_appointment | Create calendar event via API | CALENDAR\_PROVIDER, CALENDAR\_API\_KEY |
| escalate\_to\_human | Trigger human handoff workflow | ESCALATION\_CHANNEL, SLACK\_WEBHOOK |
| send\_payment\_link | Send Stripe/Razorpay payment link | PAYMENT\_PROVIDER, PAYMENT\_API\_KEY |
| qualify\_lead | Score lead and update CRM pipeline | CRM\_PROVIDER, CRM\_API\_KEY |

# **7\. Sales Workflow Engine**

The Sales Workflow Engine turns the AI agent into an active revenue generator. It handles lead capture, qualification, nurturing, and handoff to human sales reps for high-value deals.

## **Lead Qualification Framework**

The agent uses a configurable qualification framework. The default is BANT (Budget, Authority, Need, Timeline) but it can be swapped for MEDDIC, GPCTBA, or a custom framework by updating the qualification\_framework setting in client config.

| BANT Dimension | How the Agent Extracts It |
| :---- | :---- |
| Budget | Directly asks or infers from product interest. Slots into CRM field deal.budget\_range |
| Authority | Asks role/title. Cross-checks if they have decision-making language ('our team', 'I decide', 'need approval') |
| Need | Identifies pain points through open-ended questions. Maps to CRM field deal.pain\_points |
| Timeline | Extracts urgency signals ('ASAP', 'next quarter', 'just exploring'). Maps to deal.close\_date\_estimate |

## **Sales Conversation Flow**

20. Greeting & Opener — personalized based on entry point (which ad, post, or page triggered the conversation).

21. Rapport Building — 1–2 conversational exchanges before pitching.

22. Discovery — structured questions to extract BANT data, recorded as CRM fields via the qualify\_lead tool.

23. Solution Presentation — personalized based on discovery answers. Links to relevant product pages or sends brochure.

24. Objection Handling — LLM is given a list of common objections and proven responses in the system prompt.

25. CTA (Call to Action) — books a demo, sends a proposal, or initiates a payment link depending on deal stage.

26. Nurture / Follow-Up — if no decision, enters an automated follow-up sequence (email \+ WhatsApp) over the configured number of days.

27. Hot Lead Escalation — if lead score exceeds threshold, immediately alerts a human sales rep via Slack with full conversation summary.

## **Lead Scoring Model**

| Lead Score Calculation Score \= Σ(weighted signals)Budget confirmed:        \+25 pointsDecision maker:          \+20 pointsClear need identified:   \+15 pointsTimeline \< 30 days:      \+20 pointsDemo requested:          \+30 pointsPricing page visited:    \+10 pointsMultiple messages:       \+5 per message (cap 20)Frustrated/negative:     \-10 pointsTHRESHOLD: Score ≥ 70 → Escalate to human sales rep immediately.           Score 40–69 → Enter nurture sequence.           Score \< 40 → FAQ/informational handling only. |
| :---- |

# **8\. Customer Service Workflow Engine**

The Customer Service engine handles inbound support requests, complaints, and general queries. It is optimized for resolution rate, customer satisfaction, and escalation accuracy.

## **Intent Classification Taxonomy**

Every inbound message is classified into one of the following intent categories by the fast classification model before the full LLM processes it:

| Intent Category | Sub-Intents | Action |
| :---- | :---- | :---- |
| Order Inquiry | Status, Tracking, Delay | Call get\_order\_status tool |
| Returns & Refunds | Initiate, Status, Policy | Check policy, initiate workflow |
| Product Info | Specs, Availability, Comparison | RAG retrieval |
| Technical Support | Setup, Error, Troubleshooting | RAG \+ escalation if unresolved |
| Billing & Payments | Invoice, Dispute, Payment method | CRM lookup \+ human if dispute |
| Complaints | Service, Product, Staff | Empathy first \+ escalation |
| Appointments | Book, Reschedule, Cancel | Calendar tool integration |
| General FAQ | Hours, Location, Contact | RAG retrieval |
| Human Request | 'Talk to a person' | Immediate escalation |
| Spam / Gibberish | N/A | Soft redirect or ignore |

## **Complaint Handling Protocol**

Complaints require special treatment to avoid escalation and protect brand reputation:

28. Acknowledge immediately with empathy — never argue or defend.

29. Thank the user for bringing the issue to attention.

30. Ask clarifying questions to fully understand the issue — do not jump to solutions.

31. Offer a concrete resolution (refund, replacement, credit, follow-up call).

32. If resolution cannot be offered autonomously, escalate to human with full context and a recommended resolution.

33. Log everything to CRM under a 'Complaint' activity type.

34. Follow up 24–48 hours later (via the configured follow-up channel) to confirm satisfaction.

## **SLA Configuration**

| SLA Parameter | Config Variable |
| :---- | :---- |
| First Response Target (seconds) | SLA\_FIRST\_RESPONSE\_SECONDS (default: 5\) |
| Resolution Target (hours) | SLA\_RESOLUTION\_HOURS (default: 24\) |
| Escalation Timeout (minutes) | SLA\_ESCALATION\_TIMEOUT\_MINS (default: 30\) |
| Follow-up Delay (hours) | SLA\_FOLLOWUP\_HOURS (default: 24\) |
| Max AI Retry Attempts | SLA\_MAX\_RETRIES (default: 3\) |
| Satisfaction Survey Delay | SLA\_SURVEY\_DELAY\_MINS (default: 60\) |

# **9\. CRM & Data Layer**

Shopify acts as the primary product and order data source. The CRM layer sits alongside it, managing lead data, conversation history, and sales pipeline. Every customer interaction — whether resolved via Shopify data or escalated — is logged to the CRM for a full 360-degree customer view.

| 📊  Data Responsibility Split Shopify owns:      Products, inventory, orders, fulfillments, refunds, customer purchase historyCRM owns:          Leads, deals, sales pipeline, conversation logs, agent notes, escalation recordsRedis owns:        Active session state, conversation history (TTL), identity cacheVector DB owns:    Shopify product embeddings, policy docs, FAQ embeddings for RAG |
| :---- |

## **CRM Configuration Variables**

| Variable | Description |
| :---- | :---- |
| CRM\_PROVIDER | hubspot | salesforce | pipedrive | zoho | airtable | custom |
| CRM\_API\_KEY | CRM API key or private app token |
| CRM\_BASE\_URL | Base URL for custom CRM REST API |
| CRM\_CONTACT\_LOOKUP\_FIELD | Field to match users to contacts (phone | email) |
| CRM\_DEAL\_PIPELINE\_ID | Pipeline ID for new deals (CRM-specific) |
| CRM\_DEAL\_STAGE\_NEW | Stage ID for newly created deals |
| CRM\_DEAL\_STAGE\_QUALIFIED | Stage ID for qualified leads |
| CRM\_DEAL\_STAGE\_CLOSED\_WON | Stage ID for closed won |
| CRM\_ACTIVITY\_LOG\_ENABLED | true | false |
| CRM\_AUTO\_CREATE\_CONTACTS | true | false — create CRM contact on first message |

## **Data Stored Per Conversation**

* Full message transcript (all turns, both directions)

* Intent classification history

* Sentiment scores per turn and overall conversation sentiment

* Tools called and their results

* Lead score (if sales mode)

* Escalation events with trigger reason

* Channel, timestamps, duration (for voice)

* Agent version and LLM model used (for audit trail)

## **Knowledge Base Management**

The vector knowledge base is primarily seeded from Shopify product data via the automated ingestion pipeline (see Section 4.3). Additional documents — return policies, brand guidelines, warranty terms, and shipping FAQs — are ingested separately. Supported additional input formats: PDF, Word (.docx), Google Docs URL, plain text. Shopify product data is kept fresh automatically via webhooks; non-Shopify documents must be manually re-ingested when updated.

# **10\. Handoff & Escalation Logic**

The escalation system is the safety net of the entire product. It ensures that no conversation that requires human judgment gets stuck with the AI. Escalations must be fast, context-rich, and routed to the right person.

## **Escalation Triggers**

| Trigger | Threshold / Logic |
| :---- | :---- |
| User requests human | Any of: 'human', 'agent', 'person', 'talk to someone', 'real person' |
| Negative sentiment | Sentiment \= 'frustrated' for 2+ consecutive turns |
| High lead score | Score ≥ ESCALATION\_LEAD\_SCORE\_THRESHOLD |
| Unresolved after retries | AI failed to resolve intent after SLA\_MAX\_RETRIES attempts |
| Legal / compliance keyword | Mentions of 'lawyer', 'lawsuit', 'sue', 'fraud', 'report' |
| Safety concern | Any content suggesting self-harm or danger to others |
| High-value transaction | Deal value \> ESCALATION\_DEAL\_VALUE\_THRESHOLD |
| VIP customer | Contact tagged as VIP in CRM |
| Unknown intent | Confidence score \< ESCALATION\_CONFIDENCE\_THRESHOLD |

## **Escalation Configuration Variables**

| Variable | Description |
| :---- | :---- |
| ESCALATION\_CHANNEL | slack | email | sms | webhook | intercom | zendesk |
| ESCALATION\_SLACK\_WEBHOOK | Slack incoming webhook URL for alert channel |
| ESCALATION\_EMAIL\_TO | Email address(es) for escalation notifications |
| ESCALATION\_SMS\_NUMBER | Phone number for SMS escalation alerts |
| ESCALATION\_LEAD\_SCORE\_THRESHOLD | Lead score that triggers hot-lead escalation (default: 70\) |
| ESCALATION\_DEAL\_VALUE\_THRESHOLD | Deal value ($) that triggers VIP escalation |
| ESCALATION\_CONFIDENCE\_THRESHOLD | Intent confidence below which to escalate (default: 0.4) |
| ESCALATION\_MESSAGE\_TEMPLATE | Template for the escalation notification message |
| ESCALATION\_HOLD\_MESSAGE | Message sent to user when handing off to human |

## **Escalation Notification Format**

| Sample Slack Escalation Alert 🚨 ESCALATION REQUIRED━━━━━━━━━━━━━━━━━━━━━━━━Customer: John Doe (+91 9876543210)Channel: WhatsAppReason: User requested human agentLead Score: 82 / 100Sentiment: FrustratedSession ID: sess\_abc123xyz━━━━━━━━━━━━━━━━━━━━━━━━Last 3 turns:\[User\]: I've been waiting for 3 days and no one is helping me\[AI\]: I completely understand your frustration...\[User\]: Just get me a real person please━━━━━━━━━━━━━━━━━━━━━━━━\[👀 View Full Chat\] \[✅ Mark Resolved\] \[📞 Call Now\] |
| :---- |

# **11\. Analytics & Reporting Dashboard**

The built-in analytics layer tracks all key performance indicators in real time. A dashboard is generated using a lightweight web UI (React \+ Recharts) that clients can access via a secure URL. All data is exportable to CSV and can be pushed to external BI tools (Google Looker Studio, Power BI, Metabase) via webhooks or Postgres direct access.

## **Dashboard Metrics**

| Metric Category | Specific Metrics | Update Frequency |
| :---- | :---- | :---- |
| Volume | Total conversations, messages/day, by channel | Real-time |
| Performance | First response time, resolution rate, CSAT score | Real-time |
| AI Quality | Intent accuracy, escalation rate, retry rate | Per conversation |
| Sales | Lead volume, qualification rate, pipeline value added | Real-time |
| Channel | Volume breakdown by WhatsApp/Email/Instagram/Voice | Real-time |
| Escalation | Escalation count, reasons, resolution time post-escalation | Per event |
| Sentiment | Average sentiment, negative conversation trends | Rolling 24h |
| Knowledge Base | RAG hit rate, unanswered questions log | Per conversation |
| Shopify Orders | Orders looked up, return requests initiated, fulfillment queries | Real-time |
| Shopify Products | Most queried products, out-of-stock deflection rate | Daily |
| Shopify Revenue | Draft orders created, discount codes applied, AI-assisted order value | Real-time |

## **Analytics Configuration Variables**

| Variable | Description |
| :---- | :---- |
| ANALYTICS\_DB\_URL | PostgreSQL connection string for analytics data |
| DASHBOARD\_PORT | Port for the analytics web UI (default: 3001\) |
| DASHBOARD\_USERNAME | Basic auth username for dashboard access |
| DASHBOARD\_PASSWORD | Basic auth password for dashboard access |
| ANALYTICS\_WEBHOOK\_URL | Webhook to push events to external BI tools |
| MIXPANEL\_TOKEN | If using Mixpanel for product analytics |

# **12\. Security, Compliance & Data Privacy**

## **Security Architecture**

* **API Key Management:** All API keys stored in environment variables or a secrets manager (AWS Secrets Manager, HashiCorp Vault, Doppler). Never hardcoded.

* **Webhook Signature Validation:** All inbound webhooks (WhatsApp, Instagram, SendGrid, etc.) are validated using HMAC-SHA256 signature verification before processing.

* **Transport Security:** All services communicate over HTTPS/TLS 1.3. Internal service-to-service communication uses mutual TLS or JWT-signed requests.

* **Data Encryption:** All conversation data encrypted at rest using AES-256. Database encrypted at the volume level.

* **PII Handling:** Phone numbers and email addresses are hashed in logs. Full PII only accessible via the CRM integration with proper access controls.

* **Rate Limiting:** All API endpoints rate-limited. Inbound webhook endpoints have IP allowlisting for known platform IP ranges.

* **Audit Logging:** Every tool call, LLM response, and escalation event is logged with timestamp, user ID, and session ID.

## **Compliance Considerations**

| Regulation | Implementation |
| :---- | :---- |
| GDPR (EU) | Data deletion API, consent tracking, data portability export, DPA agreement |
| CCPA (California) | Opt-out handling, data sale prohibition flag, deletion requests |
| DPDP Act (India) | Consent collection before first message, data localization option |
| WhatsApp Policy | Opt-in required before first message, opt-out handling, no spam |
| TCPA (US calling) | Express written consent before automated calls, do-not-call list integration |
| HIPAA (if healthcare) | BAA with all vendors, PHI cannot be sent via SMS/WhatsApp |

# **13\. Full Tech Stack Reference**

| Layer | Technology | Purpose |
| :---- | :---- | :---- |
| Runtime | Node.js 20 / Python 3.12 | API services and data pipelines |
| Framework | Fastify (Node) / FastAPI (Python) | High-performance HTTP servers |
| Message Queue | Redis (BullMQ) or RabbitMQ | Async message bus between services |
| Database | PostgreSQL 16 | Primary persistence layer |
| Cache / State | Redis 7 | Session state, conversation history |
| Vector DB | Pinecone or pgvector | RAG knowledge base embeddings |
| Orchestration | Docker Compose (dev) / K8s (prod) | Service orchestration |
| LLM Access | OpenAI SDK / Anthropic SDK / LangChain | LLM abstraction layer |
| Voice STT | OpenAI Whisper / Deepgram | Speech to text transcription |
| Voice TTS | ElevenLabs API | Text to speech synthesis |
| Telephony | Twilio Voice \+ Media Streams | Phone call handling |
| WhatsApp | Meta Cloud API (direct) | WhatsApp channel |
| Instagram | Meta Graph API | Instagram DM channel |
| Email Send | SendGrid / Resend / SMTP | Outbound email delivery |
| Email Receive | Gmail API / IMAP poller | Inbound email parsing |
| Shopify | Shopify Admin API 2025-01 (REST \+ GraphQL) | Product catalog, orders, customers, returns |
| Shopify Webhooks | Shopify Webhook Subscriptions | Real-time product/order/customer sync |
| Shopify SDK | @shopify/shopify-api (Node.js) | Admin API client with rate limit handling |
| CRM | HubSpot / Salesforce SDK | Customer data management |
| Calendar | Google Calendar API / Calendly | Appointment booking |
| Payments | Stripe / Razorpay API | Payment link generation |
| Auth | JWT \+ API key middleware | Service authentication |
| Observability | OpenTelemetry \+ Grafana | Metrics, traces, logs |
| Dashboard UI | React \+ Recharts \+ Tailwind | Analytics front-end |
| Deployment | Railway / Render / AWS ECS | Cloud hosting |
| Secrets | Doppler / AWS Secrets Manager | Environment variable management |
| CI/CD | GitHub Actions | Automated testing and deployment |

# **14\. Client Configuration Guide**

All client-specific settings are defined in a single .env file (or Doppler project). No code changes are needed between client deployments. Below is the complete annotated configuration template.

| 📄  Master .env Configuration Template \# ═══════════════════════════════════════\# CORE IDENTITY\# ═══════════════════════════════════════CLIENT\_NAME="Acme Corp"AGENT\_NAME="Alex"COMPANY\_DESCRIPTION="We sell premium home appliances online."AGENT\_TONE="professional and friendly"AGENT\_MODE="both"   \# customer\_service | sales | both\# ═══════════════════════════════════════\# LLM CONFIGURATION\# ═══════════════════════════════════════LLM\_PROVIDER="openai"LLM\_MODEL="gpt-4o"LLM\_API\_KEY="sk-..."LLM\_TEMPERATURE="0.3"LLM\_MAX\_TOKENS="1024"LLM\_FAST\_MODEL="gpt-4o-mini"\# ═══════════════════════════════════════\# SHOPIFY\# ═══════════════════════════════════════SHOPIFY\_STORE\_DOMAIN="acmecorp.myshopify.com"SHOPIFY\_ADMIN\_API\_TOKEN="shpat\_..."SHOPIFY\_API\_VERSION="2025-01"SHOPIFY\_WEBHOOK\_SECRET="wh\_secret\_xyz..."SHOPIFY\_STOREFRONT\_TOKEN="abc123..."       \# OptionalSHOPIFY\_LOCATION\_ID="12345678"SHOPIFY\_CURRENCY="INR"SHOPIFY\_RETURN\_POLICY\_URL="https://acmecorp.com/returns"SHOPIFY\_TRACKING\_URL\_TEMPLATE="https://track.delhivery.com/{tracking\_number}"SHOPIFY\_AUTO\_TAG\_AI\_ORDERS="true"SHOPIFY\_DRAFT\_ORDER\_EXPIRY\_DAYS="7"SHOPIFY\_PRODUCT\_SYNC\_BATCH\_SIZE="250"     \# Products per ingestion page\# ═══════════════════════════════════════\# WHATSAPP\# ═══════════════════════════════════════WHATSAPP\_PHONE\_NUMBER\_ID="XXXXXX"WHATSAPP\_ACCESS\_TOKEN="EAA..."WHATSAPP\_WEBHOOK\_VERIFY\_TOKEN="my\_secure\_token\_123"WHATSAPP\_APP\_SECRET="abc123..."WHATSAPP\_BUSINESS\_ACCOUNT\_ID="YYYYYY"\# ═══════════════════════════════════════\# EMAIL\# ═══════════════════════════════════════EMAIL\_PROVIDER="gmail"EMAIL\_INBOUND\_ADDRESS="support@acmecorp.com"GMAIL\_CLIENT\_ID="xxx.apps.googleusercontent.com"GMAIL\_CLIENT\_SECRET="GOCSPX-..."GMAIL\_REFRESH\_TOKEN="1//..."EMAIL\_FROM\_NAME="Alex from Acme Support"SENDGRID\_API\_KEY="SG...."\# ═══════════════════════════════════════\# INSTAGRAM\# ═══════════════════════════════════════INSTAGRAM\_ACCESS\_TOKEN="EAA..."INSTAGRAM\_PAGE\_ID="123456789"INSTAGRAM\_APP\_SECRET="abc..."INSTAGRAM\_WEBHOOK\_VERIFY\_TOKEN="insta\_token\_xyz"\# ═══════════════════════════════════════\# VOICE (ELEVENLABS \+ TWILIO)\# ═══════════════════════════════════════ELEVENLABS\_API\_KEY="el\_..."ELEVENLABS\_VOICE\_ID="21m00Tcm4TlvDq8ikWAM"ELEVENLABS\_MODEL\_ID="eleven\_turbo\_v2"ELEVENLABS\_STABILITY="0.5"ELEVENLABS\_SIMILARITY\_BOOST="0.75"TWILIO\_ACCOUNT\_SID="ACxxx"TWILIO\_AUTH\_TOKEN="xxx"TWILIO\_PHONE\_NUMBER="+14155551234"\# ═══════════════════════════════════════\# CRM\# ═══════════════════════════════════════CRM\_PROVIDER="hubspot"CRM\_API\_KEY="pat-na1-..."CRM\_CONTACT\_LOOKUP\_FIELD="phone"CRM\_DEAL\_PIPELINE\_ID="default"\# ═══════════════════════════════════════\# ESCALATION\# ═══════════════════════════════════════ESCALATION\_CHANNEL="slack"ESCALATION\_SLACK\_WEBHOOK="https://hooks.slack.com/..."ESCALATION\_LEAD\_SCORE\_THRESHOLD="70"\# ═══════════════════════════════════════\# DATABASE\# ═══════════════════════════════════════DATABASE\_URL="postgresql://user:pass@host:5432/dbname"REDIS\_URL="redis://host:6379"VECTOR\_DB\_PROVIDER="pinecone"VECTOR\_DB\_API\_KEY="pc-..."VECTOR\_DB\_INDEX="client-knowledge-base" |
| :---- |

# **15\. Deployment & DevOps Blueprint**

## **Recommended Infrastructure**

| Component | Recommended Setup |
| :---- | :---- |
| App Hosting | Railway.app or Render.com (easy) / AWS ECS Fargate (enterprise) |
| Database | Supabase (PostgreSQL) or AWS RDS |
| Redis | Upstash Redis (serverless) or AWS ElastiCache |
| Vector DB | Pinecone Serverless (simplest) or pgvector on Supabase |
| Media Storage | AWS S3 or Cloudflare R2 |
| DNS & SSL | Cloudflare (automatic SSL, DDoS protection) |
| Monitoring | Grafana Cloud (free tier) \+ Sentry for error tracking |
| Secrets | Doppler (recommended) or Railway native env vars |

## **Deployment Steps (New Client)**

35. Clone the base repository to a new branch named after the client.

36. Create a new environment in Doppler (or copy the .env template) and fill in all client-specific variables including all SHOPIFY\_ variables.

37. Set up Shopify Custom App in the client's admin panel, grant required scopes, and copy the Admin API Access Token.

38. Run the Shopify knowledge base ingestion: npm run shopify:ingest \-- this pulls all products, embeds them, and loads them into the vector DB.

39. Register Shopify webhooks for products, orders, customers, fulfillments, and refunds pointing to the agent's webhook endpoint.

40. Configure channel webhooks: register the WhatsApp and Instagram webhook URLs with Meta; configure email forwarding or IMAP credentials.

41. Run integration tests: npm run test:integration — validates Shopify API connection, all channel connections, and CRM sync.

42. Deploy to Railway/Render by pushing the branch. Set environment variables from Doppler.

43. Perform end-to-end smoke test: trigger an order status query, a product search, a return request, and an escalation on each channel.

44. Hand off the analytics dashboard URL and credentials to the client.

## **Estimated Deployment Time**

| Task | Time Estimate |
| :---- | :---- |
| Environment setup & variable configuration | 30–45 minutes |
| Shopify Custom App setup & API token generation | 15–20 minutes |
| Shopify product ingestion (knowledge base build) | 15–30 minutes (depends on catalog size) |
| Shopify webhook registration (9 webhook topics) | 15 minutes |
| Meta app & channel webhook configuration | 45–60 minutes |
| ElevenLabs voice \+ Twilio setup | 30–45 minutes |
| CRM integration & field mapping | 30–45 minutes |
| Testing & smoke test (all channels \+ Shopify flows) | 45 minutes |
| Total | \~3.5–4.5 hours for a new client |

# **16\. Cost Estimation & Pricing Model**

The following cost estimates are for a typical mid-sized client handling 5,000 conversations per month across all channels. Actual costs will vary based on message volume, voice call duration, and chosen LLM model.

## **Monthly Infrastructure Cost Estimate (5,000 conversations/month)**

| Service | Estimated Monthly Cost (USD) |
| :---- | :---- |
| LLM API (GPT-4o, avg 1500 tokens/conv) | $35–60 |
| ElevenLabs TTS (500 voice minutes/mo) | $22–40 |
| Deepgram STT (500 minutes/mo) | $9–15 |
| Twilio Voice (500 minutes outbound/inbound) | $25–40 |
| Twilio SMS (if used for notifications) | $5–15 |
| SendGrid (5000 outbound emails) | $15–20 |
| Pinecone Serverless (vector DB) | $0–25 |
| Supabase Pro (DB \+ storage) | $25 |
| Upstash Redis | $0–10 |
| Railway / Render (hosting) | $20–50 |
| Cloudflare (DNS \+ CDN) | $0–5 |
| Shopify API | $0 (included in client's Shopify plan — no extra API cost) |
| Total Estimated Infrastructure | $156–305 / month |

## **Suggested Client Pricing Tiers**

| Tier | Suggested Retainer |
| :---- | :---- |
| Starter (1 channel, \< 1,000 conv/mo) | $500–800/month |
| Growth (all 4 channels, \< 5,000 conv/mo) | $1,200–2,000/month |
| Scale (all channels, 5,000–20,000 conv/mo) | $2,500–4,000/month |
| Enterprise (custom volume, SLA, white-label) | $5,000+/month |
| One-time Setup Fee (per client) | $500–2,000 (configuration \+ onboarding) |

| 💡  Margin Note At 5,000 conversations/month with \~$230 infrastructure cost and a $1,500/month retainer, your gross margin is approximately 85%. The primary cost driver is LLM API usage — switching from GPT-4o to GPT-4o-mini or Claude Haiku for simple intents (FAQ, order status) can reduce LLM costs by 70–80% with minimal quality impact. |
| :---- |

# **17\. Customization Checklist Per Client**

Use this checklist at the start of every new client deployment to ensure nothing is missed:

## **Identity & Tone**

* Define agent name (human name recommended: Alex, Sarah, etc.)

* Write company description for system prompt (2–3 sentences)

* Define tone guidelines (formal / casual / regional language preferences)

* Decide agent operational mode (sales / support / both)

* Collect brand colors and logo for email HTML template

## **Shopify Integration Setup**

* Log into client Shopify Admin → Settings → Apps → Develop Apps → Create App

* Name the app (e.g. 'AI Agent Integration') and configure all required API scopes from Section 4.1

* Click Install App and securely copy the Admin API Access Token (shown once only)

* Note and record the Store Domain (.myshopify.com) and pin the API version

* Generate Storefront API token if product browsing via storefront is needed

* Note the default Location ID for inventory queries

* Set up Shopify Webhook subscriptions for all 12 topics (products, orders, customers, fulfillments, refunds, price rules)

* Add and verify the SHOPIFY\_WEBHOOK\_SECRET in the .env

* Run the product ingestion script: npm run shopify:ingest and verify top-5 semantic search results

* Upload non-Shopify documents: return policy, shipping FAQ, warranty terms (PDF/Word)

* Configure SHOPIFY\_RETURN\_POLICY\_URL and SHOPIFY\_TRACKING\_URL\_TEMPLATE

## **Channel Setup**

* WhatsApp: Create Meta App, get phone number, generate System User token, register webhook

* Email: Set up inbound address, configure OAuth or IMAP, test inbound parsing

* Instagram: Connect Instagram to Meta Business App, subscribe to DM webhooks

* Voice: Purchase Twilio number, configure TwiML app, select ElevenLabs voice

## **Integrations**

* CRM: Generate API key, map custom fields, define deal pipeline stages

* Calendar: Connect Google Calendar or Calendly for appointment booking

* Payments: Configure Stripe/Razorpay for payment link generation

* Escalation: Set up Slack webhook or email for human handoff alerts

## **Sales & Service Configuration**

* Define lead qualification framework (BANT / MEDDIC / custom)

* Set lead score escalation threshold

* Write objection-handling guide for system prompt

* Configure follow-up sequence timing and templates

* Define which intent categories auto-escalate vs. AI-handled

* Configure Shopify-specific intents: order\_status, return\_request, product\_inquiry, discount\_query

* Set SLA targets (response time, resolution time)

## **Testing & QA**

* Test order status lookup: send 'where is my order \#XXXX' on WhatsApp — verify Shopify API call and correct tracking response

* Test product search: 'do you have \[product\] under \[price\]?' — verify Shopify product query and correct results

* Test return initiation: verify Shopify return API call and customer notification

* Test out-of-stock response: verify agent checks inventory and suggests alternatives

* Test discount code validation: verify agent checks Shopify price\_rules before confirming validity

* Test escalation trigger on all configured conditions

* Test CRM contact creation and deal logging

* Test appointment booking flow end-to-end

* Test Shopify webhook events: trigger a product update in Shopify and verify vector DB updates

* Load test voice channel with concurrent calls (if high volume expected)

* Verify analytics dashboard Shopify metrics are populating correctly

## **Handoff & Go-Live**

* Provide client with analytics dashboard URL and login

* Train client team on how to handle escalations and respond in the handoff interface

* Document all credentials and store securely in password manager

* Schedule 2-week post-launch check-in to review performance and tune prompts

**End of Document**

*This document is a confidential product blueprint. Replace all \[PLACEHOLDER\] values before sharing with clients.*